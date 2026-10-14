"""Phase 1–2 tests: deterministic mocks/records only, no Sol or CAD launch."""
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_agent, cad_verify_v3_agent as v3_agent, eval_verify_v3 as v3
from tools import cad_verify_v4_agent as agent, cad_verify_v4_ledger as ledger, eval_verify_v4 as evaluation
from tools.cad_verify_v3_diagnostics import finalize
from tools.test_support import start_tempdirs, stop_tempdirs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "design/cad-harness-verify-v3/test"
SOURCE = 'import FreeCAD\nimport Part\nimport Sketcher\ndef build(doc):\n    return doc.addObject("PartDesign::Body", "Body")\n'
OVERLOAD = json.dumps(dict(type="turn.failed", error=dict(codex_error_info="server_overloaded"))).encode()+b"\n"


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def spec():
    gold = ledger.read_json(BASE/"G6/gold.json")
    return dict(schema="cad-harness.build-spec.v1", family="rect_prism", units="mm", frame="world",
                regions=[dict(bounds=gold["bbox"])],
                holes=[{k: v for k, v in h.items() if k != "through"} for h in gold["holes"]],
                pockets=[{k: v for k, v in p.items() if k != "sharp"} for p in gold["pockets"]],
                finish=gold["finish"])


class MockRuntime:
    """Artificial unit responses, explicitly not measured CAD/model performance."""
    def __init__(self, outputs, *, fail_cad=False, quota=None):
        self.outputs = iter(outputs)
        self.clock = agent.ReplayClock()
        self.models, self.cads = [], []
        self.fail_cad, self.quota_values, self.quota_calls = fail_cad, quota, 0

    def quota(self):
        self.quota_calls += 1
        value = self.quota_values(self.quota_calls) if self.quota_values else 0
        return dict(decision="quota_snapshot_missing_or_invalid" if value is None else
                    "quota_hard_stop" if value >= 60 else "quota_soft_stop" if value >= 55 else "allow",
                    evidence_mode="unit_mock")

    def sleep(self, seconds):
        self.clock.advance(seconds)

    def execute(self, operation, argv, **kwargs):
        if operation == "model":
            self.models.append(list(argv))
            self.clock.advance(10)
            value = next(self.outputs)
            if isinstance(value, Exception):
                raise value
            if isinstance(value, dict):
                return value
            usage = dict(input_tokens=10, cached_input_tokens=0, cache_write_input_tokens=0,
                         output_tokens=3, reasoning_output_tokens=1)
            return dict(returncode=0, final=value.encode("utf-8"), stderr=b"",
                        stdout=json.dumps(dict(type="turn.completed", usage=usage)).encode()+b"\n")
        self.cads.append(list(argv))
        self.clock.advance(20)
        source, out, gold = [Path(argv[argv.index(key)+1]) for key in ("--script", "--out-dir", "--gold")]
        out.mkdir()
        (out/"input.py").write_bytes(source.read_bytes())
        (out/"gold.json").write_bytes(gold.read_bytes())
        result = dict(schema="cad-harness.cad_run.v0", task_id=ledger.read_json(gold)["case_id"],
                      probe_profile="verify-v3", script_sha256=ledger.sha(source.read_bytes()), gold_sha256=ledger.sha(gold.read_bytes()),
                      status="ok", geometry_ok=True, editability_ok=True, probe_pass=True, probe_status="pass", script_completed=True,
                      verification_pass=True, document_closed=True, cleanup_status="exited", cad_exit_code=0,
                      verification_cleanup_status="exited", verification_exit_code=0, owned_pid=100, verification_pid=200,
                      verification=dict(verification_pass=True, document_closed=True), failed_phase=None, next_actor=None,
                      generator=argv[argv.index("--generator")+1], measurements={"volume_mm3": 123},
                      stage_statuses=dict.fromkeys(("build", "geometry", "editability", "export", "reimport"), "pass"),
                      stage_measurements=dict.fromkeys(("build", "geometry", "editability", "export", "reimport")))
        if self.fail_cad and len(self.cads) == 1:
            result.update(status="failed", editability_ok=False, probe_pass=False, probe_status="predicate_fail",
                          failed_phase="probe", next_actor="sol", code_owner="script", predicate_diff=["editability"],
                          verification=None, verification_pid=None, verification_pass=False)
            result["stage_statuses"].update(editability="fail", export="not_reached", reimport="not_reached")
        finalize(result)
        (out/"result.json").write_text(json.dumps(result), encoding="utf-8")
        return dict(returncode=0 if result["status"] == "ok" else 1,
                    stdout=json.dumps(result).encode(), stderr=b"", final=None)


class VerifyV4(unittest.TestCase):
    def setUp(self):
        # A missed offline boundary fails the test instead of launching anything.
        self.patches = [patch("subprocess.run", side_effect=AssertionError("live process denied")),
                        patch("subprocess.Popen", side_effect=AssertionError("live process denied"))]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def drive(self, directory, runtime, *, case="G6", route="spec", name="run", preview=False):
        base = Path(directory)
        request = base/(name+"-request.txt")
        request.write_bytes((BASE/case/"description.txt").read_bytes())
        card = dict(schema="cad-harness.acceptance.v4", request_sha256=ledger.sha(request.read_bytes()),
                    route=route, preview=preview,
                    gold=str(BASE/case/"gold.json") if (BASE/case/"gold.json").exists() else None)
        if (BASE/case/"rubric.json").exists():
            card["rubric"] = ledger.read_json(BASE/case/"rubric.json")
        if route == "completion":
            card["answer"] = (BASE/case/"answer.txt").read_text(encoding="utf-8")
        acceptance = base/(name+"-acceptance.json")
        ledger.write_json(acceptance, card)
        out = base/name
        summary, code = agent.request(request, acceptance, out, runtime=runtime)
        report = ledger.read_json(out/summary["driver_report"])
        return out, summary, report, code, request, acceptance

    def test_preflight_preserves_modeling_contracts_and_live_zero(self):
        value = evaluation.preflight()
        self.assertEqual((value["status"], value["live_calls"], value["live_cad_runs"]), ("offline_ready", 0, 0))
        self.assertEqual(value["manifest"], "not_frozen")
        self.assertEqual(value["pilot"], "not_run")

    def test_nullable_rollup_and_usage_deduplication(self):
        events = [dict(event_index=1, values=dict(input_tokens=0, output_tokens=2))]*2
        value = ledger.usage_totals(events)
        self.assertEqual(value["values"]["input_tokens"], 0)
        self.assertEqual(value["values"]["output_tokens"], 2)
        self.assertIsNone(value["values"]["reasoning_output_tokens"])
        events += [dict(event_index=2, mode="cumulative", values=dict(input_tokens=7, output_tokens=3)),
                   dict(event_index=3, mode="cumulative", values=dict(input_tokens=9, output_tokens=4))]
        self.assertEqual(ledger.usage_totals(events)["values"]["input_tokens"], 9)
        result = ledger.nullable_total([0, None, 3])
        self.assertEqual((result["total"], result["known_subtotal"], result["missing"]), (None, 3, 1))

    def test_user_rate_source_identity_and_billing_subsets(self):
        usage = ledger.usage_totals([dict(values=dict(input_tokens=1000, cached_input_tokens=400, output_tokens=100))])
        self.assertIsNone(ledger.price(usage)["amount"])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/"test-only-rate.json"
            card = dict(provided_by_user=True, source="unit fixture, not a real price", effective_date="2000-01-01",
                        currency="TEST", product="unit", model="unit", tier="unit", categories=[
                            dict(name="uncached", fields=dict(input_tokens=1, cached_input_tokens=-1), rate_per_million="2"),
                            dict(name="cached", fields=dict(cached_input_tokens=1), rate_per_million="1"),
                            dict(name="output_including_reasoning", fields=dict(output_tokens=1), rate_per_million="3")])
            ledger.write_json(source, card)
            identity = dict(product="unit", model="unit", tier="unit")
            self.assertEqual(ledger.price(usage, source, identity=identity)["amount"], "0.0019")
            self.assertIsNone(ledger.price(usage, source, identity=dict(identity, product="other"))["amount"])

    def test_complete_raw_capture_is_bounded_in_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"stdout.bin"
            raw = b"x"*100000+b"\xff\r\n"+OVERLOAD
            capture = ledger.StreamCapture(path, parse=True)
            for index in range(0, len(raw), 997):
                capture.feed(raw[index:index+997])
            artifact = capture.finish()
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual((artifact["sha256"], artifact["bytes"]), (ledger.sha(raw), len(raw)))
            self.assertLessEqual(len(capture.tail), 16384)
            self.assertFalse(capture.parser.summary()["provider_rejected"])

    def test_started_but_unfinished_attempt_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"ledger.jsonl"
            with ledger.Journal(path, "unit", "offline") as journal:
                journal.append("attempt_started", attempt_id="one", episode_id="ep", operation="model")
            value = ledger.summarize(path)
            self.assertEqual(value["unfinished_attempts"], 1)
            self.assertIsNone(value["all_work"]["charged_calls"]["total"])
            self.assertIsNone(value["operational_wall_s"])

    def test_backfill_keeps_archives_missing_capture_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/"reports/cad-run"
            snapshots = {}
            for name, count in (("host-verify-v3-current", 2), ("host-verify-v3-partial", 1), ("host-verify-v3-aborted", 1)):
                path = source/name/"driver-run.json"
                path.parent.mkdir(parents=True)
                report = dict(calls=[dict(invoked=True, session_id=name+str(i), usage=[dict(event_index=1, values=dict(input_tokens=0))])
                                     for i in range(count)], attempts=[], wall_ms=12, status="ok")
                ledger.write_json(path, report)
                snapshots[path] = path.read_bytes()
            aggregate = root/"aggregate.json"
            bound = root/"reports/base-aggregate.json"
            ledger.write_json(bound, dict(groups=dict(core=[dict(run="host-verify-v3-current")])))
            ledger.write_json(aggregate, dict(groups=dict(core=[]), real_calls=3, total_charged_calls=4,
                              original_partial=dict(run="host-verify-v3-partial"),
                              base_aggregate=dict(path=bound.relative_to(root).as_posix(), sha256=ledger.file_sha(bound))))
            value = ledger.backfill(source, root/"verify-v4-backfill", aggregate=aggregate)
            self.assertEqual(value["all_work"]["charged_calls"]["total"], 4)
            self.assertEqual(value["retained_segments"]["charged_calls"]["total"], 3)
            self.assertTrue(value["historical_reconciliation"]["total_matches"])
            self.assertIsNone(value["all_work"]["tokens"]["output_tokens"]["total"])
            self.assertIsNone(value["all_work"]["price"]["total"])
            for path, raw in snapshots.items():
                self.assertEqual(path.read_bytes(), raw)
            events = list(ledger.rows(root/"verify-v4-backfill/ledger.jsonl"))
            call = next(e for e in events if e["event"] == "attempt_finished")
            self.assertIsNone(call["streams"]["stdout"]["bytes"])
            with self.assertRaisesRegex(ValueError, "output_exists"):
                ledger.backfill(source, root/"verify-v4-backfill", aggregate=aggregate)

    def test_one_entry_completes_and_sends_only_request_and_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = MockRuntime([json.dumps(spec())])
            runtime.clock.advance(5)  # The request must exclude earlier clock history.
            original = v3_agent.agent
            out, summary, report, code, request, _ = self.drive(directory, runtime)
            self.assertEqual((code, report["status"], len(runtime.cads)), (0, "ok", 1))
            self.assertEqual(summary["all_work"]["charged_calls"]["total"], 1)
            self.assertEqual(summary["operational_wall_s"], 30)
            argv = runtime.models[0]
            context = json.loads(next(a.split("=", 1)[1] for a in argv if a.startswith("developer_instructions=")))
            self.assertEqual(context.encode(), agent.bundle())
            self.assertEqual(argv[-1].encode(), request.read_bytes())
            self.assertIs(v3_agent.agent, original)
            self.assertEqual(report["attempts"][0]["result"]["stage_statuses"]["reimport"], "pass")
            schema = ledger.read_json(ROOT/"design/cad-harness-verify-v4/ledger.schema.json")
            for event in ledger.rows(out/"ledger.jsonl"):
                self.assertTrue(set(schema["required"]) <= event.keys())

    def test_source_fallback_reuses_driver_and_captures_geometry_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = MockRuntime([json.dumps(dict(unsupported=["native source required"])), SOURCE])
            _, summary, report, code, _, _ = self.drive(directory, runtime, case="G1", route="source")
            self.assertEqual((code, report["unsupported_to_source"], len(runtime.models), len(runtime.cads)), (0, True, 2, 1))
            self.assertEqual(summary["all_work"]["tokens"]["input_tokens"]["total"], 20)
            context = next(a for a in runtime.models[1] if a.startswith("developer_instructions="))
            self.assertEqual(json.loads(json.loads(context.split("=", 1)[1]).split(agent.MARKER)[1])["target"], "source")

    def test_uncapped_overloads_preserve_bytes_slots_and_full_wall(self):
        with tempfile.TemporaryDirectory() as directory:
            rejected = dict(returncode=1, stdout=OVERLOAD, stderr=b"", final=None)
            runtime = MockRuntime([rejected]*6+[json.dumps(spec())])
            out, summary, report, code, _, _ = self.drive(directory, runtime)
            self.assertEqual((code, report["logical_calls"], report["parse_repairs"], report["repair_calls"]), (0, 1, 0, 0))
            self.assertEqual(summary["exempt_overload_attempts"], 6)
            self.assertEqual(summary["operational_wall_s"], 6*610+30)
            self.assertEqual(summary["active_s"], 30)
            self.assertEqual(summary["wait_s"]["total"], 3600)
            self.assertTrue(all(argv == runtime.models[0] for argv in runtime.models))
            self.assertEqual(summary["overload_robustness"], "UNVERIFIED")
            calls = [e for e in ledger.rows(out/"ledger.jsonl") if e["event"] == "attempt_finished" and e["operation"] == "model"]
            self.assertTrue(all(c["charged"] is False for c in calls[:-1]))
            self.assertTrue(all(c["logical_call_id"] == 1 for c in calls))

    def test_output_bearing_or_unstructured_error_is_charged_without_retry(self):
        for stdout, final in ((OVERLOAD, b"partial"), (b"server_overloaded", None)):
            with self.subTest(stdout=stdout), tempfile.TemporaryDirectory() as directory:
                runtime = MockRuntime([dict(returncode=1, stdout=stdout, stderr=b"", final=final)])
                _, summary, _, code, _, _ = self.drive(directory, runtime)
                self.assertEqual((code, len(runtime.models), summary["exempt_overload_attempts"]), (1, 1, 0))
                self.assertEqual(summary["all_work"]["charged_calls"]["total"], 1)

    def test_parse_slot_is_shared_and_no_extra_generation_is_added(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = MockRuntime(["invalid JSON", json.dumps(spec()), "invalid repair JSON"], fail_cad=True)
            _, _, report, code, _, _ = self.drive(directory, runtime)
            self.assertEqual((code, report["parse_repairs"], report["repair_calls"], len(runtime.models)), (1, 1, 1, 3))
            self.assertEqual(len(runtime.cads), 1)

    def test_single_cad_repair_uses_existing_measurement_feedback(self):
        with tempfile.TemporaryDirectory() as directory:
            revised = spec()
            revised["regions"][0]["bounds"][1] += 1  # Test-only distinct response; no changed gold/checker.
            runtime = MockRuntime([json.dumps(spec()), json.dumps(revised)], fail_cad=True)
            _, summary, report, code, _, _ = self.drive(directory, runtime)
            self.assertEqual((code, report["repair_calls"], len(runtime.cads)), (0, 1, 2))
            self.assertEqual(summary["all_work"]["charged_calls"]["total"], 2)
            context = json.loads(next(a.split("=", 1)[1] for a in runtime.models[1] if a.startswith("developer_instructions=")))
            data = json.loads(context.split(agent.MARKER)[1])
            self.assertEqual((data["stage"], data["observations"]["result"]["predicate_diff"]), ("repair", ["editability"]))
            self.assertNotIn("gold_sha256", json.dumps(data))

    def test_quota_limits_and_missing_quota_admit_no_call(self):
        for value, reason in ((55, "quota_soft_stop"), (60, "quota_hard_stop"), (None, "quota_snapshot_missing_or_invalid")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                runtime = MockRuntime([], quota=lambda unused: value)
                _, summary, report, code, _, _ = self.drive(directory, runtime)
                self.assertEqual((code, summary["physical_model_attempts"], report["message_code"]), (1, 0, reason))

    def test_quota_interrupts_backoff_without_claiming_full_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = MockRuntime([dict(returncode=1, stdout=OVERLOAD, stderr=b"", final=None)],
                                  quota=lambda n: 60 if n >= 3 else 0)
            _, summary, report, code, _, _ = self.drive(directory, runtime)
            self.assertEqual((code, len(runtime.models), report["message_code"]), (1, 1, "quota_hard_stop"))
            self.assertEqual(summary["wait_s"]["total"], 60)
            self.assertEqual(summary["all_work"]["charged_calls"]["total"], 0)

    def test_timeout_has_full_empty_streams_and_is_charged(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = MockRuntime([subprocess.TimeoutExpired("unit-mock", 10)])
            out, summary, _, code, _, _ = self.drive(directory, runtime)
            self.assertEqual((code, summary["all_work"]["charged_calls"]["total"]), (1, 1))
            event = next(e for e in ledger.rows(out/"ledger.jsonl") if e["event"] == "attempt_finished")
            self.assertEqual(event["streams"]["stdout"]["bytes"], 0)
            self.assertIsNone(event["usage"]["values"]["input_tokens"])

    def test_completion_preserves_original_request_and_types_genuine_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            rubric = ledger.read_json(BASE/"C4/rubric.json")
            runtime = MockRuntime([json.dumps(rubric["positive"]), json.dumps(dict(unsupported=["test stop"]))])
            _, _, report, _, request, _ = self.drive(directory, runtime, case="C4", route="completion")
            self.assertTrue(report["completion_reached"])
            self.assertEqual(len(runtime.models), 2)
            self.assertTrue(all(argv[-1].encode() == request.read_bytes() for argv in runtime.models))
            context = json.loads(next(a.split("=", 1)[1] for a in runtime.models[1] if a.startswith("developer_instructions=")))
            self.assertEqual(json.loads(context.split(agent.MARKER)[1])["answer"], (BASE/"C4/answer.txt").read_text(encoding="utf-8"))

    def test_recorded_cli_request_uses_same_entry_and_never_launches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = MockRuntime([json.dumps(spec())])
            seed, _, report, _, request, acceptance = self.drive(root, runtime, name="seed")
            (root/"final.txt").write_text(json.dumps(spec()), encoding="utf-8")
            (root/"empty.bin").write_bytes(b"")
            cad = seed/"reports/cad-run/request-mvp1/a1-mvp1"
            fixture = dict(schema="cad-harness.replay.v4", evidence_mode="recorded",
                           started_at="2000-01-01T00:00:00+00:00", quota_percent=0, steps=[
                               dict(operation="model", elapsed_s=10, returncode=0, stdout_path="seed/attempt-0001/stdout.bin", stderr_path="empty.bin", final_path="final.txt"),
                               dict(operation="cad", elapsed_s=20, returncode=0, stdout_path=cad.relative_to(root).as_posix()+"/result.json", stderr_path="empty.bin", artifacts_dir=cad.relative_to(root).as_posix())])
            ledger.write_json(root/"replay.json", fixture)
            out = root/"replayed"
            with patch("sys.stdout", new_callable=io.StringIO):
                code = evaluation.main(["request", "--request", str(request), "--acceptance", str(acceptance),
                                        "--replay", str(root/"replay.json"), "--run-dir", str(out)])
            self.assertEqual(code, 0)
            self.assertEqual(ledger.read_json(out/"summary.json")["driver_status"], "ok")
            self.assertTrue((out/"calls.csv").is_file())
            entry = dict(request=request.name, acceptance=acceptance.name, replay="replay.json")
            ledger.write_json(root/"roster.json", dict(schema="cad-harness.replay-roster.v4", entries=[entry, entry]))
            batch = evaluation.run_replay(root/"roster.json", root/"batch", "holdout")
            self.assertEqual(batch["costs"]["all_work"]["charged_calls"]["total"], 2)
            self.assertEqual(batch["costs"]["operational_wall_s"], 60)
            self.assertEqual(batch["fresh_holdout"], "not_run")

    def test_recorded_aggregate_keeps_all_eight_predicates_and_order(self):
        order = ledger.read_json(ROOT/"design/cad-harness-verify-v3/run-order.json")
        rows = [v3.empty_row(e, "unit-"+e["id"]) for e in order["entries"]]
        groups = {g: [r for r in rows if r["group"] == g] for g in v3.GROUPS}
        original = v3.summarize(rows, order)
        result = evaluation.replay_summary(dict(groups=groups, summary=original))
        self.assertEqual(result["summary"], original)
        self.assertTrue(result["identical_summary"])
        self.assertEqual(len(result["summary"]["thresholds"]), 8)
        changed = copy.deepcopy(groups)
        changed["dev"][0]["manifest_entry"]["route"] = "spec"
        with self.assertRaisesRegex(ValueError, "order_binding"):
            evaluation.replay_summary(dict(groups=changed, summary=original))

    def test_live_and_freeze_are_blocked_and_missing_pilot_is_not_run(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)/"never-created"
            with self.assertRaisesRegex(ValueError, "offline_only"):
                agent.request("not-read", "not-read", out)
            self.assertFalse(out.exists())
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(evaluation.main(["freeze"]), 1)
                self.assertEqual(evaluation.main(["run", "--phase", "holdout", "--sealed-input", "not-read", "--run-dir", str(out)]), 1)
            self.assertFalse(out.exists())
            value = evaluation.run_replay(None, out, "pilot")
            self.assertEqual(value["pilot"], "not_run")


if __name__ == "__main__":
    unittest.main()
