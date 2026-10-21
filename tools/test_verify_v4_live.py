"""Mocked transport regressions and opt-in independent native episode coverage."""
import copy
from contextlib import contextmanager
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_live as live, cad_verify_v4_agent as agent
from tools import cad_verify_v4_ledger as ledger, eval_verify_v4 as cli
from tools import eval_verify_v3 as v3, cad_run_probes
from tools.test_support import start_tempdirs, stop_tempdirs

ROOT = Path(__file__).resolve().parents[1]
OVERLOAD = json.dumps(dict(type="turn.failed", error=dict(codex_error_info="server_overloaded"))).encode()+b"\n"


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def response(text, *, model="gpt-6.1-sol", output=3):
    return json.dumps(dict(type="message_end", message=dict(role="assistant", provider="openai-codex",
        model=model, stopReason="stop", content=[dict(type="text", text=text)],
        usage=dict(input=10, cacheRead=0, cacheWrite=0, output=output)))).encode()+b"\n"


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.journals = []
        # Any missed boundary fails loudly instead of spending or launching CAD.
        self.patches = [patch("subprocess.run", side_effect=AssertionError("live process denied")),
                        patch("subprocess.Popen", side_effect=AssertionError("live process denied"))]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    @contextmanager
    def temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            try:
                yield directory
            finally:
                for journal in self.journals:
                    journal.close()

    def transport(self, base, outputs, *, quota=None, maximum=3):
        clock = agent.ReplayClock()
        manifest = dict(authorization=dict(charged_calls=163), files={}, quota_snapshot="unit-quota",
                        generator=dict(omp="unit-omp", version="unit-version",
                                       model="openai-codex/gpt-6.1-sol", thinking="xhigh"))
        journal = ledger.Journal(base/"ledger.jsonl", "unit", "holdout", clock=clock, now=clock.utc)
        self.journals.append(journal)
        observed = []
        replies = iter(outputs)
        def process(argv, captures, *, cwd, timeout):
            observed.append((list(argv), timeout))
            clock.advance(10)
            item = next(replies)
            if isinstance(item, Exception):
                captures["stdout"].feed(b"partial\xff")
                captures["stderr"].feed(b"error bytes")
                raise item
            captures["stdout"].feed(item)
            captures["stderr"].feed(b"raw stderr\r\n")
            return 0
        guard = live.LiveGuard(manifest, lambda: None, clock=clock)
        guard.check = quota or (lambda: dict(decision="allow"))
        guard.before_episode(maximum)
        transport = live.LiveTransport(manifest, journal, base, "original request", agent.bundle(), guard,
                                       wall=clock, process=process, sleep=clock.advance)
        transport.episode, transport.route = "episode", "spec"
        transport.driver_reserves = False
        work = base/"work"
        work.mkdir()
        last = work/"last.txt"
        argv = live.LiveSkillAdapter(agent.bundle(), "original request").exec_argv("unit", work, last, "original request", agent.bundle().decode())
        return transport, guard, clock, observed, argv, work, last, journal

    def test_many_overloads_at_last_budget_slot_are_exempt_and_preserve_active_time(self):
        with self.temporary() as directory:
            base = Path(directory)
            transport, guard, clock, calls, argv, work, last, journal = self.transport(base, [OVERLOAD]*7+[response("answer")])
            guard.calls, guard.episode_start = 162, 162
            transport(argv, cwd=work, timeout=420)
            self.assertEqual((guard.calls, last.read_text()), (163, "answer"))
            self.assertEqual(clock(), 7*610+10)
            self.assertEqual(transport.clock(), 10)
            events = list(ledger.rows(journal.path))
            finished = [e for e in events if e["event"] == "attempt_finished"]
            self.assertEqual([e["charged"] for e in finished], [False]*7+[True])
            self.assertEqual(sum(e["actual_s"] for e in events if e["event"] == "wait_finished"), 4200)
            submitted = [ledger.read_json(base/e["attempt_id"]/"submitted.json") for e in finished]
            self.assertTrue(all(value == submitted[0] for value in submitted))
            self.assertEqual(transport.recoveries, 1)
            with self.assertRaisesRegex(ValueError, "call_budget"):
                transport(argv, cwd=work, timeout=420)
            self.assertEqual(len(calls), 8)

    def test_output_bearing_overload_is_charged_without_resend(self):
        with self.temporary() as directory:
            base = Path(directory)
            partial = json.dumps(dict(type="message_update", assistantMessageEvent=dict(type="text_delta", delta="partial"))).encode()+b"\n"
            transport, guard, _, calls, argv, work, last, journal = self.transport(base, [partial+OVERLOAD])
            transport(argv, cwd=work, timeout=420)
            event = next(e for e in ledger.rows(journal.path) if e["event"] == "attempt_finished")
            self.assertEqual((guard.calls, len(calls), event["charged"], event["provider_rejected"]), (1, 1, True, False))
            self.assertFalse(last.exists())
            self.assertEqual(transport.recoveries, 0)

    def test_quota_interrupts_wait_and_releases_only_the_rejected_reservation(self):
        with self.temporary() as directory:
            base = Path(directory)
            counter = [0]
            def quota():
                counter[0] += 1
                if counter[0] >= 6:
                    raise live.Stop("quota_hard_stop")
                return dict(decision="allow")
            transport, guard, clock, calls, argv, work, _, journal = self.transport(base, [OVERLOAD], quota=quota)
            with self.assertRaisesRegex(ValueError, "quota_hard_stop"):
                transport(argv, cwd=work, timeout=420)
            self.assertEqual((len(calls), guard.calls, clock()), (1, 0, 70))
            wait = next(e for e in ledger.rows(journal.path) if e["event"] == "wait_finished")
            self.assertEqual((wait["actual_s"], wait["completed"]), (60, False))
            self.assertEqual(transport.clock(), 0)

    def test_transport_failure_preserves_partial_bytes_and_unknown_usage(self):
        with self.temporary() as directory:
            base = Path(directory)
            transport, guard, _, calls, argv, work, _, journal = self.transport(base, [subprocess.TimeoutExpired("unit", 10)])
            with self.assertRaisesRegex(OSError, "interrupted"):
                transport(argv, cwd=work, timeout=420)
            event = next(e for e in ledger.rows(journal.path) if e["event"] == "attempt_finished")
            self.assertEqual((guard.calls, len(calls), event["charged"]), (1, 1, True))
            self.assertEqual(Path(event["streams"]["stdout"]["path"]).read_bytes(), b"partial\xff")
            self.assertFalse(event["streams"]["stdout"]["complete"])
            self.assertIsNone(event["usage"]["values"]["input_tokens"])

    def test_wrong_generator_or_hidden_retry_cannot_return_a_success(self):
        for stdout, reason in ((response("answer", model="different"), "generator_identity"),
                               (response("one")+response("two"), "hidden_model_retry")):
            with self.subTest(reason=reason), self.temporary() as directory:
                transport, _, _, _, argv, work, last, _ = self.transport(Path(directory), [stdout])
                with self.assertRaisesRegex(OSError, reason):
                    transport(argv, cwd=work, timeout=420)
                self.assertFalse(last.exists())

    def test_missing_or_offline_manifest_never_reads_sealed_inputs(self):
        with self.temporary() as directory:
            base = Path(directory)
            with patch.object(live.freezing, "verify", return_value=dict(authorization=None)), patch.object(live, "load_cohort", side_effect=AssertionError("private input denied")):
                with self.assertRaisesRegex(ValueError, "authorization_required"):
                    live.run_holdout(base/"manifest.json", base/"private-not-read", base/"out")
            self.assertFalse((base/"out").exists())
            with patch("sys.stdout", new_callable=io.StringIO):
                code = cli.main(["run", "--phase", "holdout", "--sealed-input", "private-not-read", "--run-dir", str(base/"out")])
            self.assertEqual(code, 1)
            self.assertFalse((base/"out").exists())

    def test_soft_hard_and_stale_quota_admit_no_calls(self):
        for used, age, reason in ((55, 0, "quota_soft_stop"), (60, 0, "quota_hard_stop"), (0, 301, "quota_snapshot_stale")):
            with self.subTest(reason=reason), self.temporary() as directory:
                base = Path(directory)
                clock = agent.ReplayClock()
                snapshot = base/"quota.json"
                ledger.write_json(snapshot, dict(snapshot_id="unit", observed_at=clock.utc(), used_percent=used))
                clock.advance(age)
                guard = live.LiveGuard(dict(authorization=dict(charged_calls=163), quota_snapshot=str(snapshot)), lambda: None, clock=clock)
                with self.assertRaisesRegex(ValueError, reason):
                    guard.before_episode(3)
                self.assertEqual(guard.calls, 0)

    def test_unstructured_or_malformed_overload_never_gets_exemption(self):
        for raw in (b"server_overloaded\n", b"invalid json\n"+OVERLOAD, b"x"*1048577+b"\n"+OVERLOAD):
            with self.subTest(length=len(raw)), self.temporary() as directory:
                path = Path(directory)/"stdout.bin"
                path.write_bytes(raw)
                result = live.omp_result(path)
                self.assertFalse(result["summary"]["provider_rejected"])

    def test_malformed_assistant_content_cannot_hide_output_or_become_a_final(self):
        for content in (None, "not blocks", [None], [dict(type="text", text=4)]):
            with self.subTest(content=content), self.temporary() as directory:
                path = Path(directory)/"stdout.bin"
                raw = json.dumps(dict(type="message_end", message=dict(role="assistant", content=content))).encode()+b"\n"
                path.write_bytes(raw+OVERLOAD)
                result = live.omp_result(path)
                self.assertIsNone(result["final"])
                self.assertFalse(result["summary"]["provider_rejected"])

    def test_changed_cohort_order_and_scored_denominator_are_rejected_before_cards(self):
        order = ledger.read_json(ROOT/"design/cad-harness-verify-v3/run-order.json")
        for change in ("order", "denominator"):
            with self.subTest(change=change), self.temporary() as directory:
                base = Path(directory)
                (base/"bound.txt").write_bytes(b"unit bound input")
                entries = copy.deepcopy(order["entries"])
                if change == "order":
                    entries[0], entries[1] = entries[1], entries[0]
                else:
                    entries[3]["scored"] = False
                cohort = base/"cohort.json"
                ledger.write_json(cohort, dict(schema="cad-harness.holdout.v4",
                    files={"bound.txt": ledger.file_sha(base/"bound.txt")}, entries=entries))
                commitment = base/"commitment.json"
                ledger.write_json(commitment, dict(schema="cad-harness.holdout-commitment.v4",
                                                   cohort_sha256=ledger.file_sha(cohort)))
                with self.assertRaisesRegex(ValueError, "order|class_contract"):
                    live.load_cohort(cohort, dict(commitment=dict(path=str(commitment))))

    def test_episode_time_exhaustion_is_incomplete_not_a_false_pass(self):
        order = ledger.read_json(ROOT/"design/cad-harness-verify-v3/run-order.json")
        entry = next(e for e in order["entries"] if e["route"] == "spec")
        row = live.score_episode(entry, dict(status="failed", message_code="episode_stage_deadline_exceeded", calls=[], attempts=[]), "unit", wall_s=2000, active_s=450)
        self.assertFalse(row["passed"])
        self.assertFalse(row["completed"])
        self.assertEqual(row["episode_stop_reason"], "episode_stage_deadline_exceeded")

    def test_live_request_reuses_clarification_gate_and_stream_ledger(self):
        with self.temporary() as directory:
            base = Path(directory)
            rubric = ledger.read_json(ROOT/"design/cad-harness-verify-v3/test/A5/rubric.json")
            raw = (ROOT/"design/cad-harness-verify-v3/test/A5/description.txt").read_bytes()
            request = base/"request.txt"
            request.write_bytes(raw)
            transport, guard, clock, calls, _, _, _, journal = self.transport(base, [response(json.dumps(rubric["positive"]))], maximum=1)
            entry = dict(id="q-A5-r1", sequence=1, case="A5", group="q", round=1, route="ask", min_calls=1, max_calls=1, scored=True, bar_class="Q2", request="request.txt")
            card = dict(schema="cad-harness.acceptance.v4", route="ask", request_sha256=ledger.sha(raw), rubric=rubric)
            report, code = live.execute_episode(entry, card, base, base/"episode", transport)
            live.validate_report(entry, card, base, base/"episode", report)
            report["_rubric"] = rubric
            row = live.score_episode(entry, report, "unit", wall_s=clock(), active_s=transport.clock())
            self.assertEqual((code, guard.calls, row["passed"], row["q_score"]), (0, 1, True, 1))
            self.assertEqual(len(calls), 1)
            event = next(e for e in ledger.rows(journal.path) if e["event"] == "attempt_finished")
            self.assertEqual(event["usage"]["values"]["input_tokens"], 10)
            self.assertIsNone(event["usage"]["values"]["reasoning_output_tokens"])
            self.assertEqual(event["streams"]["stderr"]["bytes"], len(b"raw stderr\r\n"))


@unittest.skipUnless(
    os.environ.get("CAD_VERIFY_ARTIFACT_NATIVE") == "1"
    and sys.version_info[:3] == (3, 11, 14)
    and importlib.util.find_spec("FreeCAD") is not None,
    "set CAD_VERIFY_ARTIFACT_NATIVE=1 under pinned native FreeCAD Python")
class NativeEpisodeTests(unittest.TestCase):
    def test_isolated_offline_episode_measures_independent_fixture(self):
        from tools import cad_spec
        from tools.fixtures.cad_mvp_build import held_out_specs

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            episode = base / "episode"
            live.setup_episode(episode, agent.bundle(), ROOT)
            source = base / "fixture.py"
            source.write_text(cad_spec.compile_spec(held_out_specs()["H_RECT_CHAMFER"]),
                              encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(episode / "tools/cad_run.py"),
                 "--script", str(source), "--out-dir", str(episode / "reports/cad-run/dev-mvp1"),
                 "--task", "H_RECT_CHAMFER", "--recipe", "freecadcmd",
                 "--gold", str(ROOT / "tools/fixtures/mvp/H_RECT_CHAMFER.gold.json"),
                 "--probe-profile", "mvp-v1", "--timeout-s", "60",
                 "--end-to-end-s", "90"],
                cwd=str(episode), stdin=subprocess.DEVNULL, capture_output=True,
                text=True, encoding="utf-8", timeout=120)
            result = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 0, result)
            self.assertEqual(
                (completed.returncode, result["probe_pass"], result["geometry_ok"],
                 result["editability_ok"], result["document_closed"], result["cleanup_status"]),
                (0, True, True, True, True, "exited"), completed.stderr)


if __name__ == "__main__":
    unittest.main()
