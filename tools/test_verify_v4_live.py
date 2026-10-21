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

    def test_model_timeout_preserves_raw_capture_and_charged_failure(self):
        with self.temporary() as directory:
            base = Path(directory)
            failure = subprocess.TimeoutExpired(["DEV-model"], 180, output=b"discarded preview")
            transport, guard, _, calls, argv, work, last, journal = self.transport(base, [failure])
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                transport(argv, cwd=work, timeout=180)
            self.assertIsNone(transport.fatal)
            event = next(e for e in ledger.rows(journal.path) if e["event"] == "attempt_finished")
            self.assertEqual((guard.calls, len(calls), event["charged"], event["provider_rejected"]),
                             (1, 1, True, False))
            self.assertEqual(event["error"], "TimeoutExpired")
            self.assertEqual(Path(event["streams"]["stdout"]["path"]).read_bytes(), b"partial\xff")
            self.assertTrue(all(stream["complete"] for stream in event["streams"].values()))
            self.assertTrue(all(value is None for value in event["usage"]["values"].values()))
            timeout = caught.exception
            self.assertEqual(timeout.transport_capture["stdout"]["full_sha256"],
                             event["streams"]["stdout"]["sha256"])
            self.assertEqual(timeout.transport_capture["stderr"]["tail"], b"error bytes")
            self.assertEqual(timeout.provider_summary, event["provider_summary"])
            self.assertTrue(all(value is None for value in timeout.exec_metadata[1][0]["values"].values()))
            self.assertFalse(last.exists())

    def test_capture_process_and_finish_failures_remain_fatal(self):
        for failure in (OSError("DEV disk failure"), subprocess.CalledProcessError(1, "DEV")):
            with self.subTest(failure=type(failure).__name__), self.temporary() as directory:
                transport, guard, _, _, argv, work, _, journal = self.transport(Path(directory), [failure])
                with self.assertRaisesRegex(OSError, "interrupted"):
                    transport(argv, cwd=work, timeout=180)
                self.assertEqual(transport.fatal, "transport_or_capture_interrupted")
                event = next(e for e in ledger.rows(journal.path) if e["event"] == "attempt_finished")
                self.assertEqual((guard.calls, event["charged"]), (1, True))
                self.assertFalse(event["streams"]["stdout"]["complete"])
        with self.temporary() as directory:
            transport, _, _, _, argv, work, _, _ = self.transport(
                Path(directory), [subprocess.TimeoutExpired("DEV", 180)])
            original = ledger.StreamCapture.finish
            def finish(capture):
                value = original(capture)
                if capture.path.name == "stdout.bin":
                    raise OSError("DEV flush failed")
                return value
            with patch.object(ledger.StreamCapture, "finish", finish):
                with self.assertRaisesRegex(OSError, "capture_finish_failed"):
                    transport(argv, cwd=work, timeout=180)
            self.assertEqual(transport.fatal, "transport_or_capture_interrupted")

    def test_owned_cleanup_timeout_remains_fatal_and_charged(self):
        class Process:
            pid, returncode = 123, None
            def __init__(self):
                self.stdout, self.stderr = io.BytesIO(b"DEV archive\n"), io.BytesIO()
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def kill(self):
                self.returncode = -1
            def wait(self, timeout=None):
                raise subprocess.TimeoutExpired(["DEV", "private harness deadline"], timeout)
        with self.temporary() as directory:
            transport, guard, _, _, argv, work, _, journal = self.transport(Path(directory), [])
            transport.process = live.stream_process
            with patch("subprocess.Popen", return_value=Process()), \
                 patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
                with self.assertRaises(OSError):
                    transport(argv, cwd=work, timeout=180)
            event = next(e for e in ledger.rows(journal.path) if e["event"] == "attempt_finished")
            self.assertEqual(transport.fatal, "transport_or_capture_interrupted")
            self.assertEqual((guard.calls, event["charged"]), (1, True))
            self.assertTrue(all(stream["complete"] is False for stream in event["streams"].values()))

    def test_timeout_does_not_hide_a_pipe_drain_error(self):
        class Process:
            pid, returncode = 123, None
            def __init__(self):
                self.stdout, self.stderr = io.BytesIO(b"DEV bytes"), io.BytesIO()
                self.waits = 0
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def kill(self):
                self.returncode = -1
            def wait(self, timeout=None):
                self.waits += 1
                if self.waits == 1:
                    raise subprocess.TimeoutExpired("DEV", timeout)
                return self.returncode
        class BrokenCapture:
            def feed(self, raw):
                raise OSError("DEV archive write failed")
        with patch("subprocess.Popen", return_value=Process()), \
             patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
            with self.assertRaisesRegex(OSError, "capture_stream_failed") as caught:
                live.stream_process(["DEV"], dict(stdout=BrokenCapture(), stderr=BrokenCapture()),
                                    cwd=ROOT, timeout=180)
        self.assertIsInstance(caught.exception.__cause__, OSError)

    def test_timed_out_episode_is_failed_and_the_next_episode_can_run(self):
        with self.temporary() as directory:
            base = Path(directory)
            (base/"request.txt").write_text("Independent DEV request: ask for plate thickness.", encoding="utf-8")
            answer = json.dumps(dict(needs_clarification=["plate_thickness"]))
            transport, guard, clock, calls, _, _, _, _ = self.transport(base,
                [subprocess.TimeoutExpired("DEV", 450), response(answer)], maximum=1)
            entry = dict(id="DEV-timeout", sequence=1, case="A5", group="q", round=1, route="ask",
                         min_calls=1, max_calls=1, scored=True, bar_class="Q2", request="request.txt")
            card = dict(schema="cad-harness.acceptance.v4", route="ask",
                        request_sha256=ledger.file_sha(base/"request.txt"),
                        rubric=dict(case_id="DEV-timeout-plate",
                                    description_sha256=ledger.file_sha(base/"request.txt"),
                                    required_fields=["plate_thickness"], critical_invention_field="plate_thickness"))
            first, _ = live.execute_episode(entry, card, base, base/"first", transport)
            first["_rubric"] = card["rubric"]
            row = live.score_episode(entry, first, entry["id"], wall_s=clock(), active_s=transport.clock())
            self.assertEqual((row["completed"], row["passed"], transport.fatal), (True, False, None))
            second = dict(entry, id="DEV-following", sequence=2)
            report, code = live.execute_episode(second, card, base, base/"second", transport)
            report["_rubric"] = card["rubric"]
            row = live.score_episode(second, report, second["id"], wall_s=clock(), active_s=transport.clock())
            self.assertEqual((code, row["passed"], guard.calls, len(calls)), (0, True, 2, 2))

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
            gold_data = dict(schema="cad-harness.verify-gold.v3", case_id="DEV-SAVED-%03d" % number)
            if number == 60:
                gold_data = ledger.read_json(ROOT/"design/cad-harness-verify-v3/test/F6/gold.json")
                gold_data.update(case_id="DEV-SAVED-060", description=request.read_text(encoding="utf-8"),
                                 description_sha256=ledger.file_sha(request))
            ledger.write_json(gold, gold_data)
            card = sealed/("card-%03d.json" % number)
            value = dict(schema="cad-harness.acceptance.v4", route=entry["route"],
                         request_sha256=ledger.file_sha(request), gold=gold.name)
            if entry["group"] == "fault":
                fault = sealed/("fault-%03d.json" % number)
                candidate = sealed/("candidate-%03d.py" % number)
                candidate.write_bytes(b"# Independent DEV fault metadata; never executed\n")
                rule = dict(candidate=candidate.name)
                if number == 60:
                    rule = ledger.read_json(ROOT/"design/cad-harness-verify-v3/test/F6/fault.json")
                    rule["candidate"] = candidate.name
                    candidate.write_bytes((ROOT/"design/cad-harness-verify-v3/test/F6/candidate.json").read_bytes())
                ledger.write_json(fault, rule)
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

    def final_fixture(self, base):
        """Reusable real DEV files for API/CLI smoke; no model, CAD or claim."""
        original = self.fixture(base)
        recovered18 = self.recover(original, base/"original18-recovery")
        prefix18 = ledger.read_json(recovered18["prefix_path"])
        prior = base/"final-prior-dev"
        prior.mkdir()
        (prior/"cohort.json").write_bytes(original["sealed"].read_bytes())
        audit = prior/"continuation"
        audit.mkdir()
        for name in ("manifest.json", "summary.json", "ledger.jsonl", "cohort.json"):
            (audit/("prior-"+name)).write_bytes((original["prior"]/name).read_bytes())
        (audit/"prefix.json").write_bytes(Path(recovered18["prefix_path"]).read_bytes())
        (audit/"evidence.json").write_bytes((base/"original18-recovery/evidence.json").read_bytes())
        (audit/"driver-run.json").write_bytes(original["driver"].read_bytes())
        historical = ledger.read_json(original["prior"]/"manifest.json")
        manifest = self.authorized(original, recovered18)
        policy_name = live.freezing.DESIGN+"/policy.json"
        manifest.update(schema="cad-harness.manifest.v4", files=dict(historical["files"]),
                        manifest_sha256=ledger.sha(b"independent DEV original freeze manifest"),
                        skill_sha256=historical["skill_sha256"],
                        policy_sha256=ledger.file_sha(ROOT/policy_name),
                        limits=copy.deepcopy(live.freezing.LIMITS))
        manifest["files"][policy_name] = manifest["policy_sha256"]
        ledger.write_json(prior/"manifest.json", manifest)
        entries = original["entries"]
        entry = entries[58]
        episode = prior/"episode-059"
        for name in (*historical["files"], "skills/freecad-modeling/SKILL.md"):
            target = episode/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((original["prior"]/"episode-018"/name).read_bytes())
        where = episode/"reports/cad-run/request-mvp1"
        cad = where/"cad-1"
        cad.mkdir(parents=True)
        source = (original["driver"].parent/"cad-1/input.py").read_bytes()
        (cad/"input.py").write_bytes(source)
        sealed = original["sealed"].parent
        request = (sealed/entry["request"]).read_bytes()
        card = ledger.read_json(sealed/entry["acceptance"])
        (cad/"gold.json").write_bytes((sealed/card["gold"]).read_bytes())
        result = copy.deepcopy(original["report"]["attempts"][0]["result"])
        result.update(task_id="DEV-SAVED-059", gold_sha256=ledger.file_sha(cad/"gold.json"),
                      status="failed", geometry_ok=False, editability_ok=None,
                      probe_pass=False, probe_status="fail", verification_pass=False, artifact_sha256={},
                      stage_statuses=dict(build="pass", geometry="fail", editability="not_reached",
                                          export="not_reached", reimport="not_reached"))
        ledger.write_json(cad/"result.json", result)
        rows = copy.deepcopy(original["rows"])
        rows[:18] = copy.deepcopy(prefix18["rows"])
        selected = entries[18:58]
        counts = {old["id"]: old["min_calls"] for old in selected}
        remaining = 65-sum(counts.values())
        if remaining < 0:
            raise AssertionError("DEV fixture minimum exceeds unchanged segment budget")
        for old in selected:
            extra = min(remaining, old["max_calls"]-counts[old["id"]])
            counts[old["id"]] += extra
            remaining -= extra
        if remaining:
            raise AssertionError("DEV fixture cannot satisfy unchanged segment budget")
        clock = agent.ReplayClock()
        number, model_number, final_events = 0, 0, []
        with ledger.Journal(prior/"ledger.jsonl", "independent-dev-final-prior", "holdout",
                            clock=clock, now=clock.utc) as journal:
            journal.append("run_started", continuation=manifest["authorization"]["continuation"],
                           prefix_count=18, prior_counted_calls=20, cost_scope="current_segment_only",
                           manifest_sha256=manifest["manifest_sha256"],
                           cohort_sha256=ledger.file_sha(prior/"cohort.json"))
            def attempt(old, operation="model", *, logical=1, stage="initial", failed=False):
                nonlocal number, model_number
                number += 1
                model_number += operation == "model"
                attempt_id = "attempt-%04d" % number
                folder = prior/attempt_id
                folder.mkdir()
                raw_request = (sealed/old["request"]).read_bytes()
                payload = folder/"payload.json"
                ledger.write_json(payload, dict(request=raw_request.decode(), runtime_data=dict(stage=stage)))
                configuration = folder/"config.json"
                ledger.write_json(configuration, live.OMP_CONFIG)
                submitted = dict(request_sha256=ledger.sha(raw_request), skill_sha256=manifest["skill_sha256"],
                                 model=manifest["generator"]["model"] if operation == "model" else None,
                                 argv=[manifest["generator"]["omp"], "--print", "--model", manifest["generator"]["model"],
                                       "--thinking", manifest["generator"]["thinking"], "--config", str(configuration),
                                       "@"+str(payload)],
                                 files={str(payload): ledger.file_sha(payload),
                                        str(configuration): ledger.file_sha(configuration)})
                if operation == "cad":
                    submitted.update(argv=["DEV-native", "--script", str(cad/"input.py"),
                        "--out-dir", str(cad), "--gold", str(sealed/card["gold"]), "--task", "DEV-SAVED-059"],
                        files={str(cad/"input.py"): ledger.file_sha(cad/"input.py")})
                ledger.write_json(folder/"submitted.json", submitted)
                fields = dict(attempt_id=attempt_id, episode_id=old["id"], operation=operation,
                              route=old["route"], stage=stage,
                              retained_segment=old["group"] not in ("dev", "completion"),
                              logical_call_id=model_number if operation == "model" else None,
                              retry_parent_id=None, evidence_mode="unit_mock",
                              manifest_sha256=manifest["manifest_sha256"])
                journal.append("attempt_started", **fields, submitted_sha256=ledger.file_sha(folder/"submitted.json"))
                raw = (json.dumps(result).encode() if operation == "cad" else
                       b'{"type":"DEV_timeout_progress"}\n'*700 if failed else
                       response("Independent DEV saved response %d" % logical))
                streams = {}
                for name, content in (("stdout", raw), ("stderr", b"" if failed else b"DEV\n")):
                    path = folder/(name+".bin")
                    path.write_bytes(content)
                    streams[name] = dict(path=str(path), sha256=ledger.file_sha(path), bytes=len(content),
                        complete=not failed, missing_reason="transport_or_capture_interrupted" if failed else None)
                parsed = live.omp_result(folder/"stdout.bin") if operation == "model" else None
                if parsed:
                    parsed["summary"]["full_sha256"] = streams["stdout"]["sha256"]
                usage = ledger.unknown_usage("transport_or_capture_incomplete") if failed else parsed["usage"] if parsed else None
                elapsed = 180.172 if failed else 1
                clock.advance(elapsed)
                return journal.append("attempt_finished", **fields, streams=streams, wall_s=elapsed, active_s=elapsed,
                    charged=True if operation == "model" else None, provider_rejected=False,
                    provider_summary=parsed["summary"] if parsed else None, usage=usage,
                    price=ledger.price(usage) if usage else None, exit_code=None if failed else 0,
                    error="TimeoutExpired" if failed else None)
            for old in selected:
                journal.append("episode_started", episode_id=old["id"], route=old["route"])
                for logical in range(1, counts[old["id"]]+1):
                    attempt(old, logical=logical)
                timing = 451.1 if old["sequence"] == 19 else 23
                journal.append("episode_finished", episode_id=old["id"], wall_s=timing, active_s=timing,
                               status="completed")
                row = rows[old["sequence"]-1]
                row.update(completed=True, passed=False, wall_s=timing-0.1, active_s=timing-0.1,
                           sol_calls=counts[old["id"]], cad_attempts=0, failure_class="DEV_failed_measurement")
                if old["sequence"] == 19:
                    row.update(completed=False, episode_stop_reason="episode_stage_deadline_exceeded",
                               failure_class="episode_stage_deadline_exceeded")
            journal.append("episode_started", episode_id=entry["id"], route=entry["route"])
            final_events.append(attempt(entry, logical=1))
            final_events.append(attempt(entry, logical=2))
            final_events.append(attempt(entry, "cad"))
            final_events.append(attempt(entry, logical=3, stage="repair", failed=True))
            journal.append("episode_finished", episode_id=entry["id"], wall_s=361.2, active_s=361.2, status="incomplete")
            journal.append("run_finished", wall_s=2000, active_s=1900, stop_reason="transport_or_capture_interrupted")
        calls = []
        model_events = [event for event in final_events if event["operation"] == "model"]
        for logical, event in enumerate(model_events, 1):
            failed = logical == 3
            artifacts = {}
            for name, stream in event["streams"].items():
                raw = b"" if failed else Path(stream["path"]).read_bytes()[-ledger.TAIL_BYTES:]
                tail = where/("transport-%d-%s.txt" % (logical, name))
                tail.write_bytes(raw)
                artifacts[name] = dict(path=tail.relative_to(episode).as_posix(), sha256=ledger.sha(raw),
                    bytes=len(raw), full_bytes=0 if failed else stream["bytes"],
                    full_sha256=ledger.sha(b"") if failed else stream["sha256"])
            provider = (live.cad_verify_v3_agent.provider_summary("") if failed else copy.deepcopy(event["provider_summary"]))
            if failed:
                provider.update(transport_error="OSError", provider_rejected=False)
            provider_path = where/("provider-%d.json" % logical)
            ledger.write_json(provider_path, provider)
            context = where/("context-%d.txt" % logical)
            prompt = where/("prompt-%d.txt" % logical)
            context.write_bytes(b"Independent DEV saved repair context")
            prompt.write_bytes(request)
            call = dict(call=logical, kind="spec" if logical == 1 else "source",
                purpose="interpretation" if logical == 1 else "source" if logical == 2 else "repair",
                stage="repair" if failed else "initial", invoked=True, prompt_sha256=ledger.sha(request),
                context_sha256=ledger.file_sha(context), timeout_s=180 if failed else 100,
                elapsed_s=177.625 if failed else logical, wall_ms=180172 if failed else 1000, usage=None,
                quota_snapshot=dict(decision="allow", age_s=0, used_percent=1),
                context_artifacts={key: dict(path=path.relative_to(episode).as_posix(), sha256=ledger.file_sha(path))
                                   for key, path in (("prompt", prompt), ("context", context))},
                logical_call=logical, transport_attempt=1, slot_consumed=True, provider_rejected=False,
                argv_sha256="a"*64, transport_artifacts=artifacts, provider_summary=provider,
                provider_artifact=dict(path=provider_path.relative_to(episode).as_posix(), sha256=ledger.file_sha(provider_path)))
            if failed:
                call["error_type"] = "OSError"
            calls.append(call)
        report = copy.deepcopy(original["report"])
        report.update(task_id="DEV-SAVED-059", route=entry["route"],
            description_sha256=ledger.sha(request), input_sha256=ledger.sha(request),
            gold_sha256=ledger.file_sha(cad/"gold.json"), status="failed", message_code="transport_or_capture_interrupted",
            calls=calls, llm_calls=3, logical_calls=3, transport_attempts=3,
            repair_calls=1, repair_eligible=True, repair_invoked=True, repair_success=False,
            budget_counts=dict(question=0, interpretation=1, source=1, parse_repair=0, repair=1),
            fault=dict(reached=True, injected=True, established=True, detected=True), wall_ms=360000,
            final_out_dir=cad.relative_to(episode).as_posix(), geometry_ok=False)
        report["settings"] = v3.Budget(entry["max_calls"]).settings()
        report["settings"].update(model=live.cad_agent.MODEL, effort=live.cad_agent.EFFORT,
            disabled=list(live.cad_agent.DISABLED), sandbox="read-only", skip_git_repo_check=True)
        report["cli_version"] = manifest["generator"]["version"]
        report["attempts"][0].update(out_dir=cad.relative_to(episode).as_posix(), result=result)
        ledger.write_json(where/"driver-run.json", report)
        costs = ledger.summarize(prior/"ledger.jsonl")
        for row in rows[18:59]:
            row["tokens"] = {key: value["total"] for key, value in costs["per_episode"][row["id"]]["tokens"].items()}
        original59 = live.score_episode(entry, report, entry["id"], wall_s=361.1, active_s=361.1)
        original59.update(completed=False, passed=False, stop_reason="transport_or_capture_interrupted",
                          tokens=rows[58]["tokens"])
        rows[58] = original59
        rows[59] = v3.empty_row(entries[59], entries[59]["id"], "transport_or_capture_interrupted")
        ledger.write_json(prior/"summary.json", dict(schema="cad-harness.holdout-results.v4",
            groups={group: [row for row in rows if row["group"] == group] for group in reversed(v3.GROUPS)}))
        references = {key: ledger.file_sha(prior/name) for key, name in (
            ("prior_manifest_sha256", "manifest.json"), ("prior_summary_sha256", "summary.json"),
            ("prior_ledger_sha256", "ledger.jsonl"), ("cohort_sha256", "cohort.json"))}
        ledger.write_json(base/"recover-final-args.json",
                          dict(sealed_input=str(original["sealed"]), prior_run=str(prior), **references))
        return dict(sealed=original["sealed"], prior=prior, entries=entries, rows=rows, report=report,
                    references=references, commitment=manifest["commitment"], driver=where/"driver-run.json",
                    manifest=manifest, original=original)

    def recover_final(self, fixture, destination):
        return live.recover_final_prefix(fixture["sealed"], fixture["prior"], destination, **fixture["references"])

    def final_authorized(self, fixture, recovered):
        manifest = copy.deepcopy(fixture["manifest"])
        manifest["authorization"].update(prior_counted_calls=88,
            continuation=dict(schema="cad-harness.holdout-continuation.v4", prefix_count=59,
                prefix_path=recovered["prefix_path"], prefix_sha256=recovered["prefix_sha256"], **fixture["references"]))
        return manifest

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

    def test_final_recovery_preserves_58_values_times_tokens_and_failed_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.final_fixture(base)
            paths = [fixture["prior"]/name for name in ("manifest.json", "summary.json", "ledger.jsonl", "cohort.json")]
            paths += [fixture["driver"]]
            timeout = next(event for event in ledger.rows(fixture["prior"]/"ledger.jsonl")
                           if event["event"] == "attempt_finished" and event.get("error") == "TimeoutExpired")
            paths.extend(Path(stream["path"]) for stream in timeout["streams"].values())
            historical = {str(path): path.read_bytes() for path in paths}
            with patch.object(live, "execute_episode", side_effect=AssertionError("execution denied")), \
                 patch.object(live.freezing, "claim", side_effect=AssertionError("claim denied")), \
                 patch.object(live.freezing, "freeze", side_effect=AssertionError("freeze denied")), \
                 patch.object(live, "score_episode", wraps=live.score_episode) as score:
                recovered = self.recover_final(fixture, base/"final-recovery")
            self.assertEqual([call.args[0]["sequence"] for call in score.call_args_list], [59])
            self.assertEqual(score.call_args.kwargs,
                             {key: fixture["rows"][58][key] for key in ("wall_s", "active_s")})
            prefix = ledger.read_json(recovered["prefix_path"])
            evidence = ledger.read_json(base/"final-recovery/evidence.json")
            self.assertEqual(prefix["rows"][:58], fixture["rows"][:58])
            self.assertFalse(prefix["rows"][1]["completed"])
            self.assertFalse(prefix["rows"][18]["completed"])
            self.assertEqual(prefix["rows"][58]["tokens"], fixture["rows"][58]["tokens"])
            self.assertEqual((prefix["rows"][58]["completed"], prefix["rows"][58]["passed"]), (True, False))
            changed = {key for key in fixture["rows"][58]
                       if fixture["rows"][58][key] != prefix["rows"][58][key]}
            self.assertEqual(changed, {"completed", "stop_reason"})
            self.assertEqual(prefix["recovery"]["original_row"], fixture["rows"][58])
            self.assertEqual(prefix["recovery"]["original_score_times"], dict(wall_s=361.1, active_s=361.1))
            self.assertEqual(prefix["recovery"]["episode_finished_times"], dict(wall_s=361.2, active_s=361.2))
            self.assertTrue(all(flags["complete"] is False for flags in prefix["recovery"]["raw_capture_flags"].values()))
            self.assertEqual(prefix["prefix58_sha256"], ledger.sha(live._canonical(fixture["rows"][:58])))
            self.assertEqual(prefix["recovery"]["evidence_sha256"], ledger.sha(live._canonical(evidence["files"])))
            self.assertEqual(prefix["recovery"]["original_row_sha256"], ledger.sha(live._canonical(fixture["rows"][58])))
            self.assertEqual(prefix["recovery"]["row_sha256"], ledger.sha(live._canonical(prefix["rows"][58])))
            self.assertEqual((prefix["prior_counted_calls"], evidence["prior_costs"]["conservative_reserved_calls"]), (88, 68))
            self.assertEqual(historical, {path: Path(path).read_bytes() for path in historical})
            self.assertEqual(set(recovered), {"status", "prefix_path", "prefix_sha256", "prefix_count",
                                             "prior_counted_calls", "live_calls", "live_cad_runs"})
            self.assertEqual((recovered["prefix_count"], recovered["live_calls"], recovered["live_cad_runs"]), (59, 0, 0))
            with self.assertRaisesRegex(ValueError, "output_exists"):
                self.recover_final(fixture, base/"final-recovery")
            with self.assertRaisesRegex(ValueError, "historical_input"):
                self.recover_final(fixture, fixture["original"]["prior"]/"nested")

    def test_final_cli_recovers_real_dev_history_without_live_output(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.final_fixture(base)
            argv = ["recover-final-prefix", "--sealed-input", str(fixture["sealed"]),
                    "--prior-run", str(fixture["prior"]), "--run-dir", str(base/"cli-final")]
            for key, value in fixture["references"].items():
                argv.extend(["--"+key.replace("_", "-"), value])
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                code = cli.main(argv)
            value = json.loads(output.getvalue())
            self.assertEqual((code, value["status"], value["prefix_count"], value["prior_counted_calls"],
                              value["live_calls"], value["live_cad_runs"]), (0, "RECOVERED", 59, 88, 0, 0))
            self.assertNotIn("rows", value)
            self.assertNotIn("summary", value)

    def test_final_prefix_and_entire_evidence_are_reauthenticated_before_claim(self):
        mutations = {
            "retained58": lambda value: value["rows"][57].update(passed=True),
            "retained_deadline": lambda value: value["rows"][18].update(completed=True),
            "failed59": lambda value: value["rows"][58].update(passed=True),
            "original59": lambda value: value["recovery"]["original_row"].update(active_s=0),
            "capture_flags": lambda value: value["recovery"]["raw_capture_flags"]["stdout"].update(complete=True),
            "time": lambda value: value["rows"][58].update(wall_s=361.2),
            "prefix58_hash": lambda value: value.update(prefix58_sha256="0"*64),
            "bool_count": lambda value: value.update(prefix_count=True),
            "extra": lambda value: value.update(start_at=60),
        }
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.final_fixture(base)
            recovered = self.recover_final(fixture, base/"recovered")
            original = ledger.read_json(recovered["prefix_path"])
            manifest_path = base/"authorized.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    folder = base/label
                    folder.mkdir()
                    prefix = copy.deepcopy(original)
                    mutate(prefix)
                    ledger.write_json(folder/"prefix.json", prefix)
                    (folder/"evidence.json").write_bytes((base/"recovered/evidence.json").read_bytes())
                    manifest = self.final_authorized(fixture, recovered)
                    manifest["authorization"]["continuation"].update(
                        prefix_path=str(folder/"prefix.json"), prefix_sha256=ledger.file_sha(folder/"prefix.json"))
                    with patch.object(live.freezing, "verify", return_value=manifest), \
                         patch.object(live.freezing, "claim") as claim, \
                         patch.object(live, "execute_episode") as execute:
                        with self.assertRaises(ValueError):
                            live.run_holdout(manifest_path, fixture["sealed"], base/("out-"+label))
                    claim.assert_not_called()
                    execute.assert_not_called()
                    self.assertFalse((base/("out-"+label)).exists())
            proof = ledger.read_json(base/"recovered/evidence.json")
            proof["prior_costs"]["conservative_reserved_calls"] = 0
            (base/"recovered/evidence.json").write_text(json.dumps(proof), encoding="utf-8")
            with patch.object(live.freezing, "verify", return_value=self.final_authorized(fixture, recovered)), \
                 patch.object(live.freezing, "claim") as claim:
                with self.assertRaisesRegex(ValueError, "prefix_evidence_binding"):
                    live.run_holdout(manifest_path, fixture["sealed"], base/"proof-tampered")
            claim.assert_not_called()
            self.assertFalse((base/"proof-tampered").exists())

    def test_final_authorization_rejects_invalid_pairs_without_reading_prefix_or_sealed(self):
        changes = [
            lambda auth: auth.update(prior_counted_calls=20),
            lambda auth: auth.update(prior_counted_calls=True),
            lambda auth: auth.update(charged_calls=True),
            lambda auth: auth["continuation"].update(prefix_count=58),
            lambda auth: auth["continuation"].update(prefix_count=True),
            lambda auth: auth["continuation"].update(prefix_path="relative.json"),
            lambda auth: auth["continuation"].update(cohort_sha256="A"*64),
            lambda auth: auth["continuation"].update(extra=True),
            lambda auth: auth["continuation"].pop("prior_ledger_sha256"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            manifest_path = base/"public-manifest.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            for change in changes:
                manifest = dict(authorization=dict(charged_calls=163, prior_counted_calls=88,
                    continuation=dict(schema="cad-harness.holdout-continuation.v4", prefix_count=59,
                        prefix_path=str(base/"never-opened-prefix.json"), prefix_sha256="a"*64,
                        prior_manifest_sha256="b"*64, prior_summary_sha256="c"*64,
                        prior_ledger_sha256="d"*64, cohort_sha256="e"*64)))
                change(manifest["authorization"])
                with self.subTest(change=change), \
                     patch.object(live.freezing, "verify", return_value=manifest), \
                     patch.object(live, "_bound_file", side_effect=AssertionError("prefix denied")), \
                     patch.object(live, "load_cohort", side_effect=AssertionError("sealed denied")), \
                     patch.object(live.freezing, "claim") as claim:
                    with self.assertRaisesRegex(ValueError, "authorization_contract"):
                        live.run_holdout(manifest_path, base/"never-opened-sealed", base/"never-created")
                claim.assert_not_called()
            self.assertFalse((base/"never-created").exists())

    def test_final_recovery_rejects_unproven_timeout_budget_usage_chain_or_other_failure(self):
        for label in ("timeout", "wrong_type", "unfinished", "capture_promoted", "capture_missing",
                      "unknown_usage_filled", "refund", "prior58_tokens", "prior58_unstarted",
                      "original59_time", "original59_tokens", "other_error", "old_prefix", "after59",
                      "already60", "submission", "deadline59", "settings59"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                fixture = self.final_fixture(base)
                ledger_path = fixture["prior"]/"ledger.jsonl"
                events = list(ledger.rows(ledger_path))
                failed = next(event for event in events if event.get("error") == "TimeoutExpired")
                if label in ("timeout", "deadline59", "settings59"):
                    report = copy.deepcopy(fixture["report"])
                    if label == "timeout":
                        report["calls"][-1]["timeout_s"] = 179
                    elif label == "deadline59":
                        report["message_code"] = "episode_deadline_exceeded"
                    else:
                        report["settings"]["repair_sol_s"] = 181
                    fixture["driver"].write_text(json.dumps(report), encoding="utf-8")
                elif label == "submission":
                    path = fixture["prior"]/failed["attempt_id"]/"submitted.json"
                    submitted = ledger.read_json(path)
                    payload = Path(next(value[1:] for value in submitted["argv"] if value.startswith("@")))
                    value = ledger.read_json(payload)
                    value["request"] = "unbound DEV request"
                    payload.write_text(json.dumps(value), encoding="utf-8")
                    submitted["files"][str(payload)] = ledger.file_sha(payload)
                    path.write_text(json.dumps(submitted), encoding="utf-8")
                    next(event for event in events if event["event"] == "attempt_started"
                         and event["attempt_id"] == failed["attempt_id"])["submitted_sha256"] = ledger.file_sha(path)
                elif label == "wrong_type":
                    failed["error"] = "OSError"
                elif label == "unfinished":
                    events.remove(failed)
                elif label == "capture_promoted":
                    failed["streams"]["stdout"]["complete"] = True
                elif label == "capture_missing":
                    Path(failed["streams"]["stdout"]["path"]).unlink()
                elif label == "unknown_usage_filled":
                    failed["usage"]["values"]["input_tokens"] = 0
                elif label == "refund":
                    failed["charged"] = False
                elif label in ("prior58_tokens", "prior58_unstarted", "original59_time", "original59_tokens", "already60"):
                    summary_path = fixture["prior"]/"summary.json"
                    summary = ledger.read_json(summary_path)
                    rows = [row for group in summary["groups"].values() for row in group]
                    sequence = 60 if label == "already60" else 58 if label.startswith("prior58") else 59
                    row = next(row for row in rows if row["sequence"] == sequence)
                    if label.endswith("tokens"):
                        row["tokens"]["input_tokens"] = 0
                    elif label == "prior58_unstarted":
                        row.update(completed=False, failure_class="not_started", episode_stop_reason=None)
                    elif label == "already60":
                        row.update(completed=True, stop_reason=None, failure_class="DEV_already_finished")
                    else:
                        row["active_s"] = row["wall_s"]+1
                    summary_path.write_text(json.dumps(summary), encoding="utf-8")
                    fixture["references"]["prior_summary_sha256"] = ledger.file_sha(summary_path)
                elif label == "other_error":
                    next(event for event in events if event["event"] == "attempt_finished")["error"] = "OSError"
                elif label == "old_prefix":
                    path = fixture["prior"]/"continuation/prefix.json"
                    path.write_bytes(path.read_bytes()+b" ")
                elif label == "after59":
                    event = copy.deepcopy(next(event for event in events if event["event"] == "episode_started"))
                    event.update(event_id=len(events)+1, episode_id=fixture["entries"][59]["id"])
                    events.append(event)
                ledger_path.write_text("".join(json.dumps(event)+"\n" for event in events), encoding="utf-8")
                fixture["references"]["prior_ledger_sha256"] = ledger.file_sha(ledger_path)
                with self.assertRaises(ValueError):
                    self.recover_final(fixture, base/"blocked")
                self.assertFalse((base/"blocked").exists())

    def test_final_continuation_runs_only_60_and_keeps_segment_costs_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fixture = self.final_fixture(base)
            recovered = self.recover_final(fixture, base/"recovered")
            prefix = ledger.read_json(recovered["prefix_path"])
            manifest_path = base/"new-manifest.json"
            ledger.write_json(manifest_path, dict(independent_dev=True))
            clock, requested = agent.ReplayClock(), []
            def process(argv, captures, *, cwd, timeout):
                requested.append(tuple(argv))
                captures["stdout"].feed(b'{"type":"independent_DEV_progress"}\n')
                clock.advance(timeout)
                raise subprocess.TimeoutExpired(argv, timeout)
            with patch.object(live.freezing, "verify", return_value=self.final_authorized(fixture, recovered)), \
                 patch.object(live.freezing, "claim"), \
                 patch.object(live.LiveGuard, "check", return_value=dict(decision="allow", age_s=0, used_percent=1)):
                result = live.run_holdout(manifest_path, fixture["sealed"], base/"final-live-dev",
                                          process=process, wall=clock)
            rows = sorted((row for group in result["groups"].values() for row in group), key=lambda row: row["sequence"])
            self.assertEqual(rows[:59], prefix["rows"])
            self.assertEqual((rows[59]["completed"], rows[59]["passed"]), (True, False))
            self.assertEqual((result["continuation"]["prefix_count"], result["continuation"]["remaining_count"]), (59, 1))
            self.assertEqual((result["costs"]["prior_counted_calls"], result["costs"]["new_counted_calls"],
                              result["costs"]["cumulative_counted_calls"]), (88, 1, 89))
            self.assertEqual((result["costs"]["cad_attempts"], len(requested)), (0, 1))
            self.assertEqual(result["costs"]["cost_scope"], "current_segment_only")
            self.assertEqual(result["status"], "INCOMPLETE")  # unchanged earlier deadline remains
            events = list(ledger.rows(base/"final-live-dev/ledger.jsonl"))
            self.assertEqual([event["episode_id"] for event in events if event["event"] == "episode_started"],
                             [fixture["entries"][59]["id"]])
            self.assertEqual((base/"final-live-dev/continuation/driver-run.json").read_bytes(), fixture["driver"].read_bytes())
            self.assertEqual((base/"final-live-dev/continuation/original18/prefix.json").read_bytes(),
                             (fixture["prior"]/"continuation/prefix.json").read_bytes())

    def test_prior_88_leaves_exactly_75_new_reservations_not_163(self):
        guard = live.LiveGuard(dict(authorization=dict(charged_calls=163, prior_counted_calls=88)), lambda: None)
        guard.check = lambda: dict(decision="allow")
        for _ in range(75):
            guard.before_episode(1)
            guard.before_call()
        self.assertEqual(guard.calls, 163)
        with self.assertRaisesRegex(ValueError, "insufficient_call_budget"):
            guard.before_episode(1)


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
