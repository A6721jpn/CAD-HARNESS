"""Independent mocked judge boundaries; never invoke a model, renderer or provider."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_model_judge as judge
from tools import cad_verify_v4_ledger as ledger
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def rubric(*, visual=True):
    return dict(schema=judge.RUBRIC_SCHEMA, id="independent-dev", items=[
        dict(id="appearance", criterion="Independent fixture feature is visible", visual=visual),
        dict(id="correct", criterion="Compare against independent deterministic evidence", visual=False)])


def verdict(*, status="PASS", critical=False, fabrication=False):
    return dict(schema=judge.VERDICT_SCHEMA, rubric_id="independent-dev",
                items=[dict(id=key, status=status, reason="Independent fixture evidence")
                       for key in ("appearance", "correct")],
                critical_dimension_error=critical, fabrication=fabrication)


class FakeSession:
    def __init__(self, response=None, *, phase="pilot"):
        self.mode = "unit_mock"
        self.registration = dict(phase=phase)
        self.response = json.dumps(verdict()) if response is None else response
        self.calls, self.events = [], []

    def call(self, record_id, request, runtime_data, **kwargs):
        self.calls.append(dict(record_id=record_id, request=request, runtime_data=runtime_data, **kwargs))
        return self.response

    def event(self, kind, **fields):
        self.events.append((kind, fields))


class AstraJudgeBoundaryTests(unittest.TestCase):
    def setUp(self):
        for target in ("subprocess.run", "subprocess.Popen"):
            item = patch(target, side_effect=AssertionError("live provider calls prohibited"))
            item.start()
            self.addCleanup(item.stop)

    def adjudicate(self, session=None, *, deterministic=None, images=(Path("independent-generated-view.png"),), record_id="DEV-1"):
        session = session or FakeSession()
        result = judge.adjudicate(session, record_id, "Independent DEV request", deterministic or dict(status="PASS"),
                                  rubric(), pool="pilot", images=images)
        return session, result

    def test_actual_images_forwarded_with_exact_identity_one_call_and_same_model_caveat(self):
        image = Path("independent-output-view.png")
        session, result = self.adjudicate(images=(image,))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(session.calls), 1)
        call = session.calls[0]
        self.assertEqual(call["images"], (image,))
        self.assertEqual((call["model"], call["thinking"], call["pool"], call["max_calls"], call["purpose"]),
                         ("openai-codex/gpt-6-astra", "max", "pilot", 1, "judge"))
        self.assertIn("same model", result["same_model_caveat"])
        self.assertEqual(call["runtime_data"]["rubric"], rubric())

    def test_malformed_missing_and_incomplete_verdicts_never_rescore(self):
        missing_item = verdict()
        missing_item["items"].pop()
        duplicate = verdict()
        duplicate["items"][1] = duplicate["items"][0]
        extra = dict(verdict(), status="PASS")
        boolean_string = dict(verdict(), critical_dimension_error="false")
        for response in ("", "PASS", "```json\n{}\n```", "{}", "null", "{", json.dumps(missing_item),
                         json.dumps(duplicate), json.dumps(extra), json.dumps(boolean_string)):
            with self.subTest(response=response):
                session, result = self.adjudicate(FakeSession(response))
                self.assertEqual(result["status"], "UNVERIFIED")
                self.assertEqual(len(session.calls), 1)
                with self.assertRaisesRegex(ValueError, "already_adjudicated"):
                    self.adjudicate(session)
                self.assertEqual(len(session.calls), 1)

    def test_missing_image_evidence_is_unverified_not_path_prose_or_a_guess(self):
        session, result = self.adjudicate(images=())
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(result["reason"], "approved_visual_evidence_missing")
        self.assertEqual(session.calls, [])
        with self.assertRaisesRegex(ValueError, "already_adjudicated"):
            self.adjudicate(session)

    def test_deterministic_numeric_and_critical_failures_override_favorable_astra(self):
        for deterministic in (dict(status="FAIL"), dict(status="PASS", checks=[dict(status="FAIL", metric="thickness")]),
                              dict(status="PASS", critical_dimension_error=True), dict(status="PASS", fabrication=True)):
            with self.subTest(deterministic=deterministic):
                _, result = self.adjudicate(deterministic=deterministic)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["reason"], "deterministic_failure_precedence")
        _, result = self.adjudicate(FakeSession("{"), deterministic=dict(status="FAIL"))
        self.assertEqual(result["status"], "FAIL")

    def test_model_fatal_flags_fail_and_missing_native_evidence_cannot_pass(self):
        for kwargs in (dict(critical=True), dict(fabrication=True), dict(status="FAIL")):
            _, result = self.adjudicate(FakeSession(json.dumps(verdict(**kwargs))))
            self.assertEqual(result["status"], "FAIL")
        for deterministic in (dict(status="UNVERIFIED"), dict(status="PASS", judges=[dict(status="UNVERIFIED")])):
            _, result = self.adjudicate(deterministic=deterministic)
            self.assertEqual(result["status"], "UNVERIFIED")

    def test_once_only_key_is_record_not_pool_and_failed_call_is_not_retried(self):
        session, _ = self.adjudicate()
        with self.assertRaisesRegex(ValueError, "already_adjudicated"):
            judge.adjudicate(session, "DEV-1", "request", dict(status="PASS"), rubric(), pool="another", images=(Path("x.png"),))
        failing = FakeSession()
        with patch.object(failing, "call", side_effect=OSError("independent transport failure")) as call:
            with self.assertRaises(OSError):
                self.adjudicate(failing)
            with self.assertRaisesRegex(ValueError, "already_adjudicated"):
                self.adjudicate(failing)
            self.assertEqual(call.call_count, 1)

    def test_missing_transport_response_is_unverified_once_with_actual_error_retained(self):
        session = FakeSession()
        with patch.object(session, "call", side_effect=judge.Stop("trial_model_response_failed")) as call:
            _, result = self.adjudicate(session)
            self.assertEqual(result["status"], "UNVERIFIED")
            self.assertEqual(result["call_error"], "trial_model_response_failed")
            with self.assertRaisesRegex(ValueError, "already_adjudicated"):
                self.adjudicate(session)
            self.assertEqual(call.call_count, 1)

    def test_structured_verdict_event_remains_a_valid_durable_ledger_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ledger.jsonl"
            session = FakeSession()
            with ledger.Journal(path, "DEV-run", "pilot") as journal:
                session.event = journal.append
                _, result = self.adjudicate(session)
            rows = list(ledger.rows(path))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["event"], "model_judged")
            self.assertEqual(rows[0]["record_id"], "DEV-1")
            self.assertEqual(rows[0]["result"], result)


class StandaloneJudgeRegistrationTests(unittest.TestCase):
    def registration(self):
        return dict(schema="cad-harness.live-registration.v1", phase="judge", trial_id="DEV-judge", cycle_id="DEV-cycle",
            files={key: dict(path=key + ".json", sha256="a" * 64, bytes=1,
                            role="judge_image" if key == "image" else "input")
                   for key in ("request", "deterministic", "rubric", "image")},
            judge=dict(judge.MODEL), budget=dict(judge=2), order=["DEV-1", "DEV-2"],
            entries=[dict(id=key, request="request", deterministic="deterministic", rubric="rubric", images=["image"])
                     for key in ("DEV-1", "DEV-2")])

    def test_freeze_denies_duplicate_roster_changed_budget_model_order_and_unapproved_images(self):
        base = self.registration()
        self.assertIs(judge.validate_registration(base), base)
        changes = [lambda value: value["entries"][1].update(id="DEV-1"),
                   lambda value: value.update(budget=dict(judge=3)),
                   lambda value: value["judge"].update(thinking="high"),
                   lambda value: value["order"].reverse(),
                   lambda value: value["files"]["image"].update(role="unapproved")]
        for change in changes:
            value = copy.deepcopy(base)
            change(value)
            with self.assertRaises(ValueError):
                judge.validate_registration(value)

    def test_bound_visual_rubric_cannot_freeze_without_image_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger.write_json(root / "rubric.json", rubric())
            ledger.write_json(root / "deterministic.json", dict(status="PASS"))
            value = self.registration()
            value["entries"][0]["images"] = []
            with self.assertRaisesRegex(ValueError, "visual_evidence_missing"):
                judge.validate_bound_inputs(value, lambda key: root / (key + ".json"))

    def test_standalone_run_keeps_full_frozen_roster_and_one_call_each(self):
        from tools import cad_verify_v4_trials as trials
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, content in (("rubric", rubric()), ("deterministic", dict(status="PASS"))):
                ledger.write_json(root / (name + ".json"), content)
            (root / "request.json").write_text("Independent DEV request", encoding="utf-8")
            session = FakeSession(phase="judge")
            session.registration = self.registration()
            session.out = root
            session.path = lambda key: root / (key + ".json")
            session.check = lambda: None
            session.summary = lambda: dict(charged_pools=dict(judge=len(session.calls)))
            with patch.object(trials, "TrialSession") as constructor:
                constructor.return_value.__enter__.return_value = session
                result = judge.run("DEV-manifest.json", "DEV-authorization.json", root,
                                   process=lambda *args, **kwargs: self.fail("real process forbidden"))
            self.assertEqual([row["record_id"] for row in result["records"]], ["DEV-1", "DEV-2"])
            self.assertEqual(len(session.calls), 2)
            self.assertTrue(all(call["pool"] == "judge" and call["max_calls"] == 1 for call in session.calls))
            self.assertEqual(result["status"], "PASS")
            self.assertIsNone(result["records"][0]["same_model_caveat"])
            self.assertEqual(constructor.call_args.kwargs["phase"], "judge")


if __name__ == "__main__":
    unittest.main()
