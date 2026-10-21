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

    def transport(self, base, outputs, *, quota=None, maximum=3, prior_counted_calls=0):
        clock = agent.ReplayClock()
        manifest = dict(authorization=dict(charged_calls=163, prior_counted_calls=prior_counted_calls), files={}, quota_snapshot="unit-quota",
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

    def test_prior_four_limits_new_calls_to_159_across_episodes(self):
        guard = live.LiveGuard(dict(authorization=dict(charged_calls=163, prior_counted_calls=4)), lambda: None)
        guard.check = lambda: dict(decision="allow")
        for _ in range(159):
            guard.before_episode(1)
            guard.before_call()
        self.assertEqual(guard.calls, 163)
        with self.assertRaisesRegex(ValueError, "insufficient_call_budget"):
            guard.before_episode(1)
        self.assertEqual(guard.calls, 163)

    def test_exhausted_prior_budget_admits_no_new_call(self):
        guard = live.LiveGuard(dict(authorization=dict(charged_calls=163, prior_counted_calls=163)), lambda: None)
        guard.check = lambda: dict(decision="allow")
        with self.assertRaisesRegex(ValueError, "insufficient_call_budget"):
            guard.before_call()
        self.assertEqual(guard.calls, 163)

    def test_invalid_or_missing_prior_count_is_not_a_fresh_budget(self):
        for prior in (-1, True, 4.0, 164, None):
            with self.subTest(prior=prior), self.assertRaisesRegex(ValueError, "authorization_required"):
                live.LiveGuard(dict(authorization=dict(charged_calls=163, prior_counted_calls=prior)), lambda: None)
        with self.assertRaisesRegex(ValueError, "authorization_required"):
            live.LiveGuard(dict(authorization=dict(charged_calls=163)), lambda: None)

    def test_exempt_overload_preserves_prior_four_and_charges_only_success(self):
        with self.temporary() as directory:
            transport, guard, clock, calls, argv, work, last, journal = self.transport(
                Path(directory), [OVERLOAD, response("answer")], maximum=1, prior_counted_calls=4)
            transport(argv, cwd=work, timeout=420)
            self.assertEqual((guard.calls, last.read_text(), len(calls)), (5, "answer", 2))
            events = list(ledger.rows(journal.path))
            self.assertEqual([e["charged"] for e in events if e["event"] == "attempt_finished"], [False, True])
            self.assertEqual(sum(e["actual_s"] for e in events if e["event"] == "wait_finished"), 600)
            self.assertEqual(transport.clock(), 10)

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
                guard = live.LiveGuard(dict(authorization=dict(charged_calls=163, prior_counted_calls=0), quota_snapshot=str(snapshot)), lambda: None, clock=clock)
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


class ContinuationTests(unittest.TestCase):
    """Independent DEV metadata/artifact bytes; no private or native fixtures."""
    def setUp(self):
        for target in ("subprocess.run", "subprocess.Popen"):
            denied = patch(target, side_effect=AssertionError("process denied"))
            denied.start()
            self.addCleanup(denied.stop)

    def fixture(self, base):
        sealed, prior = base/"sealed-dev", base/"prior-dev"
        sealed.mkdir()
        prior.mkdir()
        entries = copy.deepcopy(ledger.read_json(ROOT/"design/cad-harness-verify-v3/run-order.json")["entries"])
        files = {}
        for entry in entries:
            number = entry["sequence"]
            request = sealed/("request-%03d.txt" % number)
            request.write_text("Independent DEV request %d" % number, encoding="utf-8")
            gold = sealed/("gold-%03d.json" % number)
            ledger.write_json(gold, dict(schema="cad-harness.verify-gold.v3",
                                        case_id="DEV-SAVED-%03d" % number))
            card = sealed/("card-%03d.json" % number)
            value = dict(schema="cad-harness.acceptance.v4", route=entry["route"],
                         request_sha256=ledger.file_sha(request), gold=gold.name)
            if entry["group"] == "fault":
                fault = sealed/("fault-%03d.json" % number)
                candidate = sealed/("candidate-%03d.py" % number)
                candidate.write_bytes(b"# Independent DEV fault metadata; never executed\n")
                ledger.write_json(fault, dict(candidate=candidate.name))
                value["fault"] = fault.name
                files[fault.name], files[candidate.name] = ledger.file_sha(fault), ledger.file_sha(candidate)
            ledger.write_json(card, value)
            entry.update(request=request.name, acceptance=card.name)
            files.update({path.name: ledger.file_sha(path) for path in (request, gold, card)})
        cohort = dict(schema="cad-harness.holdout.v4", files=files, entries=entries)
        cohort_path = sealed/"cohort.json"
        ledger.write_json(cohort_path, cohort)
        (prior/"cohort.json").write_bytes(cohort_path.read_bytes())
        commitment = base/"commitment-dev.json"
        ledger.write_json(commitment, dict(schema="cad-harness.holdout-commitment.v4",
                                           cohort_sha256=ledger.file_sha(cohort_path)))
        episode = prior/"episode-018"
        source_files = {
            "tools/cad_spec.py": b"# independent historical DEV compiler\n",
            "tools/cad_verify_v3_probe.py": b"# independent historical DEV probe\n",
            "tools/cad_verify_probe.py": b"# independent historical DEV shared probe\n",
            "tools/eval_verify_v3.py": b"# historical checker identity differs from current implementation\n",
            "design/cad-harness-mvp/build-schema.json": b'{"dev_schema":true}\n',
            "design/cad-harness-mvp/eval-v1/schema.json": b'{"dev_result_schema":true}\n',
            "design/cad-harness-verify-v3/gold-schema.json": b'{"dev_gold_schema":true}\n',
        }
        skill = b"Independent DEV skill\n"
        for name, raw in {**source_files, "skills/freecad-modeling/SKILL.md": skill}.items():
            path = episode/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        manifest = dict(schema="cad-harness.manifest.v4",
                        authorization=dict(charged_calls=163, prior_counted_calls=4),
                        commitment=dict(path=str(commitment), sha256=ledger.file_sha(commitment)),
                        files={name: ledger.sha(raw) for name, raw in source_files.items()},
                        skill_sha256=ledger.sha(skill))
        ledger.write_json(prior/"manifest.json", manifest)
        entry = entries[17]
        request = (sealed/entry["request"]).read_bytes()
        where = episode/"reports/cad-run/request-mvp1"
        cad = where/"cad-1"
        cad.mkdir(parents=True)
        source = b"def build(doc):\n    return doc.addObject('PartDesign::Body', 'DEV')\n"
        (cad/"input.py").write_bytes(source)
        (cad/"gold.json").write_bytes((sealed/"gold-018.json").read_bytes())
        for name in ("model.FCStd", "model.step"):
            (cad/name).write_bytes(("Independent DEV artifact "+name).encode())
        verification = dict(verification_pass=True, document_closed=True, task_id="DEV-SAVED-018")
        ledger.write_json(cad/"verify-result.json", verification)
        stages = ("build", "geometry", "editability", "export", "reimport")
        result = dict(schema="cad-harness.cad_run.v0", task_id="DEV-SAVED-018",
            probe_profile="verify-v3", script_sha256=ledger.sha(source), source_sha256=None,
            gold_sha256=ledger.file_sha(cad/"gold.json"), status="ok",
            geometry_ok=True, editability_ok=True, probe_pass=True, probe_status="pass",
            script_completed=True, document_closed=True, cleanup_status="exited", cad_exit_code=0,
            verification_pass=True, verification_cleanup_status="exited", verification_exit_code=0,
            owned_pid=101, verification_pid=102, verification=verification, generator="agent",
            stage_statuses=dict.fromkeys(stages, "pass"), stage_measurements=dict.fromkeys(stages),
            artifact_sha256={name: ledger.file_sha(cad/name) for name in ("model.FCStd", "model.step")})
        ledger.write_json(cad/"result.json", result)
        calls = []
        for number, kind in enumerate(("spec", "source"), 1):
            prompt, context = where/("prompt-%d.txt" % number), where/("context-%d.txt" % number)
            prompt.write_bytes(request)
            context.write_bytes(b"Independent DEV context")
            calls.append(dict(call=number, kind=kind, purpose="interpretation" if number == 1 else "source",
                stage="initial", invoked=True, prompt_sha256=ledger.sha(request),
                context_sha256=ledger.file_sha(context), timeout_s=100, elapsed_s=1,
                quota_snapshot=dict(decision="allow", age_s=0, used_percent=1),
                context_artifacts={key: dict(path=str(path.relative_to(episode)), sha256=ledger.file_sha(path))
                                   for key, path in (("prompt", prompt), ("context", context))}))
            call = calls[-1]
            raw = response("Independent DEV response %d" % number)
            provider = dict(error_infos=[], assistant_output=True, event_shapes=[], source="stdout",
                            full_sha256=ledger.sha(raw), parse_complete=True, provider_rejected=False)
            provider_path = where/("provider-%d.json" % number)
            ledger.write_json(provider_path, provider)
            artifacts = {}
            for key, content in (("stdout", raw), ("stderr", b"DEV\n")):
                artifact = where/("transport-%d-%s.txt" % (number, key))
                artifact.write_bytes(content)
                artifacts[key] = dict(path=str(artifact.relative_to(episode)), sha256=ledger.file_sha(artifact),
                                      bytes=len(content), full_bytes=len(content), full_sha256=ledger.file_sha(artifact))
            call.update(logical_call=number, transport_attempt=1, slot_consumed=True, provider_rejected=False,
                        argv_sha256="a"*64, transport_artifacts=artifacts, provider_summary=provider,
                        provider_artifact=dict(path=str(provider_path.relative_to(episode)),
                                               sha256=ledger.file_sha(provider_path)))
        report = dict(schema="cad-harness.cad_agent.verify3", run_id="request-mvp1",
            task_id="DEV-SAVED-018", mode="description", probe_profile="verify-v3",
            description_sha256=ledger.sha(request), input_sha256=ledger.sha(request),
            gold_sha256=ledger.file_sha(cad/"gold.json"), route=entry["route"], preview=False,
            compiler_sha256=manifest["files"]["tools/cad_spec.py"],
            probe_sha256=manifest["files"]["tools/cad_verify_v3_probe.py"],
            shared_probe_sha256=manifest["files"]["tools/cad_verify_probe.py"],
            skill_sha256=ledger.sha(skill),
            schema_sha256=manifest["files"]["design/cad-harness-mvp/build-schema.json"],
            status="ok", message_code=None, calls=calls, llm_calls=2, cad_attempts=1,
            unsupported_to_source=True, parse_repairs=0, repair_calls=0, repair_eligible=False,
            budget_counts=dict(question=0, interpretation=1, source=1, parse_repair=0, repair=0),
            provider_policy=live.cad_verify_v3_agent.PROVIDER_POLICY, prior_provider_attempts=0,
            logical_calls=2, transport_attempts=2, provider_rejected_attempts=0, provider_wait_s=0,
            wall_ms=12000, attempts=[dict(attempt=1, stage="initial",
                out_dir=str(cad.relative_to(episode)), source_sha256=ledger.sha(source), result=result,
                started_elapsed_s=2, ended_elapsed_s=10, build_timeout_s=90, reimport_timeout_s=90)])
        ledger.write_json(where/"driver-run.json", report)
        clock = agent.ReplayClock()
        with ledger.Journal(prior/"ledger.jsonl", "independent-dev-prior", "holdout",
                            clock=clock, now=clock.utc) as journal:
            journal.append("run_started")
            for number in range(14):
                fields = dict(attempt_id="old-%02d" % number, episode_id=entries[number]["id"], operation="model")
                journal.append("attempt_started", **fields)
                journal.append("attempt_finished", **fields, charged=True,
                               usage=ledger.unknown_usage(), price=ledger.price(ledger.unknown_usage()))
            for number, operation in enumerate(("model", "model", "cad"), 1):
                attempt_id = "attempt-%04d" % number
                capture = prior/attempt_id
                capture.mkdir()
                payload = capture/"payload.json"
                payload.write_bytes(b'{"independent_dev":true}')
                submitted = dict(request_sha256=ledger.sha(request), skill_sha256=ledger.sha(skill),
                                 files={str(payload): ledger.file_sha(payload)})
                ledger.write_json(capture/"submitted.json", submitted)
                fields = dict(attempt_id=attempt_id, episode_id=entry["id"], operation=operation)
                journal.append("attempt_started", **fields,
                               submitted_sha256=ledger.file_sha(capture/"submitted.json"))
                streams = {}
                for name in ("stdout", "stderr"):
                    stream = capture/(name+".bin")
                    raw = (json.dumps(result).encode() if operation == "cad" and name == "stdout"
                           else response("Independent DEV response %d" % number)
                           if operation == "model" and name == "stdout" else b"DEV\n")
                    stream.write_bytes(raw)
                    streams[name] = dict(path=str(stream), sha256=ledger.file_sha(stream),
                                         bytes=len(raw), complete=True)
                usage = ledger.unknown_usage()
                usage["values"].update(input_tokens=10, output_tokens=3)
                journal.append("attempt_finished", **fields, charged=True if operation == "model" else None,
                    usage=usage if operation == "model" else None,
                    price=ledger.price(usage) if operation == "model" else None, streams=streams)
            for old_entry in entries[:18]:
                journal.append("episode_finished", episode_id=old_entry["id"], wall_s=23, active_s=12)
            journal.append("run_finished", wall_s=1000, active_s=900)
        costs = ledger.summarize(prior/"ledger.jsonl")
        rows = [v3.empty_row(old_entry, old_entry["id"]) for old_entry in entries]
        for row in rows[:17]:
            row.update(completed=True, passed=True, wall_s=5, sol_calls=1, cad_attempts=0, failure_class=None)
        rows[0].update(passed=False, failure_class="retained_preview", preview_kind="source")
        rows[1].update(completed=False, passed=False, failure_class="retained_timeout",
                       episode_stop_reason="episode_stage_deadline_exceeded", wall_s=451)
        rows[16].update(passed=False, failure_class="retained_failed_measurement")
        rows[17]["tokens"] = {key: value["total"] for key, value in costs["per_episode"][entry["id"]]["tokens"].items()}
        summary = dict(schema="cad-harness.holdout-results.v4",
                       groups={group: [row for row in rows if row["group"] == group] for group in reversed(v3.GROUPS)})
        ledger.write_json(prior/"summary.json", summary)
        references = {key: ledger.file_sha(prior/name) for key, name in (
            ("prior_manifest_sha256", "manifest.json"), ("prior_summary_sha256", "summary.json"),
            ("prior_ledger_sha256", "ledger.jsonl"), ("cohort_sha256", "cohort.json"))}
        return dict(sealed=cohort_path, prior=prior, entries=entries, rows=rows, report=report,
                    references=references, commitment=manifest["commitment"], driver=where/"driver-run.json")

    def recover(self, fixture, destination):
        return live.recover_prefix(fixture["sealed"], fixture["prior"], destination, **fixture["references"])

    def authorized(self, fixture, recovered):
        continuation = dict(schema="cad-harness.holdout-continuation.v4", prefix_count=18,
                            prefix_path=recovered["prefix_path"], prefix_sha256=recovered["prefix_sha256"],
                            **fixture["references"])
        return dict(authorization=dict(charged_calls=163, prior_counted_calls=20, continuation=continuation),
                    commitment=fixture["commitment"],
                    generator=dict(omp="DEV-NEVER-EXECUTED", version="DEV",
                                   model="openai-codex/gpt-6.1-sol", thinking="xhigh"))

    def test_recover_preserves_17_values_and_scores_only_saved_18(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            original = {name: (fixture["prior"]/name).read_bytes()
                        for name in ("manifest.json", "summary.json", "ledger.jsonl", "cohort.json")}
            with patch.object(live, "execute_episode", side_effect=AssertionError("execution denied")), \
                 patch.object(live.freezing, "claim", side_effect=AssertionError("claim denied")), \
                 patch.object(live.freezing, "freeze", side_effect=AssertionError("freeze denied")), \
                 patch.object(live, "score_episode", wraps=live.score_episode) as score:
                recovered = self.recover(fixture, base/"recovery")
                score.assert_called_once()
                self.assertEqual(score.call_args.args[0]["sequence"], 18)
                self.assertEqual(score.call_args.kwargs, dict(wall_s=23, active_s=12))
            prefix = ledger.read_json(recovered["prefix_path"])
            self.assertEqual(prefix["rows"][:17], fixture["rows"][:17])
            self.assertEqual(prefix["rows"][17]["tokens"], fixture["rows"][17]["tokens"])
            self.assertTrue(prefix["rows"][17]["passed"])
            self.assertEqual(prefix["prefix17_sha256"], ledger.sha(live._canonical(fixture["rows"][:17])))
            self.assertEqual(prefix["recovery"]["row_sha256"], ledger.sha(live._canonical(prefix["rows"][17])))
            self.assertEqual(prefix["prior_counted_calls"], 20)
            self.assertEqual(original, {name: (fixture["prior"]/name).read_bytes() for name in original})
            self.assertNotIn("rows", recovered)
            self.assertNotIn("summary", recovered)
            second = self.recover(fixture, base/"recovery-again")
            self.assertEqual(second["prefix_sha256"], recovered["prefix_sha256"])
            with self.assertRaisesRegex(ValueError, "output_exists"):
                self.recover(fixture, base/"recovery")
            with self.assertRaisesRegex(ValueError, "historical_input"):
                self.recover(fixture, fixture["prior"]/"nested-recovery")

    def test_recovery_cli_returns_only_nonlive_metadata_and_honest_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            argv = ["recover-prefix", "--sealed-input", str(fixture["sealed"]),
                    "--prior-run", str(fixture["prior"]), "--run-dir", str(base/"recovery")]
            for key, value in fixture["references"].items():
                argv.extend(["--"+key.replace("_", "-"), value])
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(argv), 0)
            value = json.loads(output.getvalue())
            self.assertEqual((value["status"], value["live_calls"], value["live_cad_runs"]), ("RECOVERED", 0, 0))
            self.assertNotIn("rows", value)
            fixture["driver"].unlink()
            argv[argv.index("--run-dir")+1] = str(base/"blocked")
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(argv), 1)
            self.assertEqual(json.loads(output.getvalue())["live_calls"], 0)
            self.assertFalse((base/"blocked").exists())

    def test_prefix_tampering_is_rejected_before_claim_output_or_calls(self):
        mutations = {
            "digest": lambda prefix: None,
            "retained_failure": lambda prefix: prefix["rows"][0].update(passed=True),
            "duplicate": lambda prefix: prefix["rows"].__setitem__(1, copy.deepcopy(prefix["rows"][0])),
            "reorder": lambda prefix: prefix["rows"].reverse(),
            "missing": lambda prefix: prefix["rows"].pop(),
            "time": lambda prefix: prefix["recovery"].update(active_s=0),
            "row18": lambda prefix: prefix["rows"][17].update(wall_s=0),
            "budget": lambda prefix: prefix.update(prior_counted_calls=16),
            "cohort": lambda prefix: prefix.update(cohort_sha256="f"*64),
            "extra": lambda prefix: prefix.update(skip=18),
            "bool_count": lambda prefix: prefix.update(prefix_count=True),
        }
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            recovered = self.recover(fixture, base/"recovery")
            original = ledger.read_json(recovered["prefix_path"])
            manifest_path = base/"new-manifest.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    prefix = copy.deepcopy(original)
                    mutate(prefix)
                    path = base/(label+"-prefix.json")
                    ledger.write_json(path, prefix)
                    manifest = self.authorized(fixture, recovered)
                    auth = manifest["authorization"]["continuation"]
                    auth.update(prefix_path=str(path), prefix_sha256="0"*64 if label == "digest" else ledger.file_sha(path))
                    with patch.object(live.freezing, "verify", return_value=manifest), \
                         patch.object(live.freezing, "claim") as claim, \
                         patch.object(live, "execute_episode") as execute:
                        with self.assertRaises(ValueError):
                            live.run_holdout(manifest_path, fixture["sealed"], base/("out-"+label))
                        claim.assert_not_called()
                        execute.assert_not_called()
                    self.assertFalse((base/("out-"+label)).exists())

    def test_auth_contract_cannot_be_loosened_by_live_admission(self):
        changes = [
            lambda auth: auth.update(prior_counted_calls=16),
            lambda auth: auth.update(charged_calls=143),
            lambda auth: auth.update(charged_calls=True),
            lambda auth: auth["continuation"].update(prefix_count=True),
            lambda auth: auth["continuation"].update(prefix_count=17),
            lambda auth: auth["continuation"].update(prefix_path="relative-prefix.json"),
            lambda auth: auth["continuation"].update(prefix_sha256="A"*64),
            lambda auth: auth["continuation"].update(extra=True),
            lambda auth: auth["continuation"].pop("prior_ledger_sha256"),
            lambda auth: auth.update(continuation=None),
        ]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            recovered = self.recover(fixture, base/"recovery")
            for change in changes:
                manifest = self.authorized(fixture, recovered)
                change(manifest["authorization"])
                with self.assertRaisesRegex(ValueError, "authorization_contract"):
                    live._admit_continuation(manifest, fixture["sealed"])

    def test_changed_original_source_gold_artifact_or_hash_cannot_be_admitted(self):
        for label in ("manifest", "summary", "ledger", "cohort", "source", "gold", "artifact", "driver"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                fixture = self.fixture(base)
                recovered = self.recover(fixture, base/"recovery")
                paths = {
                    "manifest": fixture["prior"]/"manifest.json",
                    "summary": fixture["prior"]/"summary.json",
                    "ledger": fixture["prior"]/"ledger.jsonl",
                    "cohort": fixture["prior"]/"cohort.json",
                    "source": fixture["prior"]/"episode-018/tools/cad_spec.py",
                    "gold": fixture["sealed"].parent/"gold-018.json",
                    "artifact": fixture["driver"].parent/"cad-1/model.step",
                    "driver": fixture["driver"],
                }
                path = paths[label]
                path.write_bytes(path.read_bytes()+b"\nchanged-independent-dev")
                manifest_path = base/"new-manifest.json"
                ledger.write_json(manifest_path, dict(independent_dev=True))
                with patch.object(live.freezing, "verify", return_value=self.authorized(fixture, recovered)), \
                     patch.object(live.freezing, "claim") as claim, \
                     patch.object(live, "execute_episode") as execute:
                    with self.assertRaises(ValueError):
                        live.run_holdout(manifest_path, fixture["sealed"], base/"out")
                    claim.assert_not_called()
                    execute.assert_not_called()
                self.assertFalse((base/"out").exists())

    def test_missing_timing_and_historical_refunds_block_recovery(self):
        for label in ("missing_wall", "missing_active", "nonfinite", "refund_four", "unsettled18"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                fixture = self.fixture(base)
                if label == "refund_four":
                    path = fixture["prior"]/"manifest.json"
                    manifest = ledger.read_json(path)
                    manifest["authorization"]["prior_counted_calls"] = 0
                    path.write_text(json.dumps(manifest), encoding="utf-8")
                    fixture["references"]["prior_manifest_sha256"] = ledger.file_sha(path)
                else:
                    path = fixture["prior"]/"ledger.jsonl"
                    events = list(ledger.rows(path))
                    event = next(item for item in events if item["event"] == "episode_finished"
                                 and item["episode_id"] == fixture["entries"][17]["id"])
                    if label == "missing_wall":
                        event.pop("wall_s")
                    elif label == "missing_active":
                        event.pop("active_s")
                    elif label == "nonfinite":
                        event["active_s"] = float("inf")
                    else:
                        events = [item for item in events if not (
                            item["event"] == "attempt_finished" and item.get("attempt_id") == "attempt-0003")]
                    path.write_text("".join(json.dumps(item)+"\n" for item in events), encoding="utf-8")
                    fixture["references"]["prior_ledger_sha256"] = ledger.file_sha(path)
                with self.assertRaises(ValueError):
                    self.recover(fixture, base/"blocked")
                self.assertFalse((base/"blocked").exists())

    def test_unfinished_old_model_is_conservatively_charged_not_refunded(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            path = fixture["prior"]/"ledger.jsonl"
            events = [event for event in ledger.rows(path) if not (
                event["event"] == "attempt_finished" and event.get("attempt_id") == "old-00")]
            path.write_text("".join(json.dumps(event)+"\n" for event in events), encoding="utf-8")
            fixture["references"]["prior_ledger_sha256"] = ledger.file_sha(path)
            recovered = self.recover(fixture, base/"recovery")
            prefix = ledger.read_json(recovered["prefix_path"])
            evidence = ledger.read_json(base/"recovery/evidence.json")
            self.assertEqual(prefix["prior_counted_calls"], 20)
            self.assertEqual(prefix["rows"][:17], fixture["rows"][:17])
            self.assertEqual(evidence["prior_costs"]["conservative_reserved_calls"], 16)
            self.assertEqual(evidence["prior_costs"]["unfinished_attempts"], 1)
            self.assertIsNone(evidence["prior_costs"]["all_work"]["charged_calls"]["total"])

    def test_remaining_segment_executes_only_19_to_60_and_retains_all_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            recovered = self.recover(fixture, base/"recovery")
            prefix = ledger.read_json(recovered["prefix_path"])
            manifest = self.authorized(fixture, recovered)
            manifest_path = base/"new-manifest.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            executed, scored = [], []
            real_score = live.score_episode
            def execute(entry, card, source, out, transport, **kwargs):
                executed.append(entry["sequence"])
                return dict(status="failed", message_code="independent_dev_failure", attempts=[]), 1
            def score(entry, report, name, **kwargs):
                scored.append(entry["sequence"])
                return real_score(entry, report, name, **kwargs)
            def validate(entry, *args):
                if entry["sequence"] == 18:
                    return live_validate(entry, *args)
            live_validate = live.validate_report
            with patch.object(live.freezing, "verify", return_value=manifest), \
                 patch.object(live.freezing, "claim") as claim, \
                 patch.object(live.LiveGuard, "check", return_value=dict(decision="allow")), \
                 patch.object(live, "execute_episode", side_effect=execute), \
                 patch.object(live, "validate_report", side_effect=validate), \
                 patch.object(live, "score_episode", side_effect=score):
                result = live.run_holdout(manifest_path, fixture["sealed"], base/"remaining",
                    process=lambda *args, **kwargs: self.fail("no model/CAD requested by DEV stub"),
                    wall=agent.ReplayClock())
            claim.assert_called_once()
            self.assertEqual(executed, list(range(19, 61)))
            self.assertEqual(scored, [18]+list(range(19, 61)))
            rows = sorted((row for group in result["groups"].values() for row in group), key=lambda row: row["sequence"])
            self.assertEqual(len(rows), 60)
            self.assertEqual([row["id"] for row in rows], [entry["id"] for entry in fixture["entries"]])
            self.assertEqual(rows[:18], prefix["rows"])
            self.assertFalse(result["summary"]["complete"])  # retained timeout is never normalized
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(result["continuation"]["cumulative_counted_calls"], 20)
            self.assertEqual(result["costs"]["physical_model_attempts"], 0)
            self.assertEqual(result["costs"]["cost_scope"], "current_segment_only")
            events = list(ledger.rows(base/"remaining/ledger.jsonl"))
            self.assertEqual([event["episode_id"] for event in events if event["event"] == "episode_started"],
                             [entry["id"] for entry in fixture["entries"][18:]])
            self.assertEqual(events[0]["continuation"]["prefix_sha256"], recovered["prefix_sha256"])
            self.assertEqual((base/"remaining/continuation/prefix.json").read_bytes(),
                             Path(recovered["prefix_path"]).read_bytes())
            self.assertFalse((base/"remaining/episode-018").exists())

    def test_without_continuation_runs_all_60_even_with_historical_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            manifest = dict(authorization=dict(charged_calls=163, prior_counted_calls=4),
                            commitment=fixture["commitment"],
                            generator=dict(omp="DEV", version="DEV",
                                           model="openai-codex/gpt-6.1-sol", thinking="xhigh"))
            manifest_path = base/"fresh-manifest.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            executed = []
            def execute(entry, *args, **kwargs):
                executed.append(entry["sequence"])
                return dict(status="failed", attempts=[], message_code="DEV-failed-measurement"), 1
            with patch.object(live.freezing, "verify", return_value=manifest), \
                 patch.object(live.freezing, "claim"), \
                 patch.object(live.LiveGuard, "check", return_value=dict(decision="allow")), \
                 patch.object(live, "_prefix_material", side_effect=AssertionError("no implicit recovery")), \
                 patch.object(live, "validate_report"), \
                 patch.object(live, "execute_episode", side_effect=execute):
                result = live.run_holdout(manifest_path, fixture["sealed"], base/"fresh",
                    process=lambda *args, **kwargs: self.fail("process denied"), wall=agent.ReplayClock())
            self.assertEqual(executed, list(range(1, 61)))
            self.assertNotIn("continuation", result)
            self.assertNotIn("cost_scope", result["costs"])
            self.assertFalse((base/"fresh/continuation").exists())

    def test_prior_twenty_allows_143_new_calls_and_no_144th(self):
        guard = live.LiveGuard(dict(authorization=dict(charged_calls=163, prior_counted_calls=20)), lambda: None)
        guard.check = lambda: dict(decision="allow")
        for _ in range(143):
            guard.before_episode(1)
            guard.before_call()
        self.assertEqual(guard.calls, 163)
        with self.assertRaisesRegex(ValueError, "insufficient_call_budget"):
            guard.before_episode(1)
        self.assertEqual(guard.calls, 163)

    def test_continuation_stop_is_incomplete_without_retry_or_historical_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.fixture(base)
            recovered = self.recover(fixture, base/"recovery")
            prefix = ledger.read_json(recovered["prefix_path"])
            manifest_path = base/"new-manifest.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            with patch.object(live.freezing, "verify", return_value=self.authorized(fixture, recovered)), \
                 patch.object(live.freezing, "claim"), \
                 patch.object(live.LiveGuard, "check", return_value=dict(decision="allow")), \
                 patch.object(live, "execute_episode", side_effect=live.Stop("DEV-explicit-stop")) as execute:
                result = live.run_holdout(manifest_path, fixture["sealed"], base/"remaining",
                    process=lambda *args, **kwargs: self.fail("process denied"), wall=agent.ReplayClock())
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(execute.call_args.args[0]["sequence"], 19)
            self.assertEqual((result["status"], result["stop_reason"]), ("INCOMPLETE", "DEV-explicit-stop"))
            rows = sorted((row for group in result["groups"].values() for row in group), key=lambda row: row["sequence"])
            self.assertEqual(rows[:18], prefix["rows"])
            self.assertEqual(len(rows), 60)
            self.assertTrue(all(not row["completed"] for row in rows[18:]))


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
