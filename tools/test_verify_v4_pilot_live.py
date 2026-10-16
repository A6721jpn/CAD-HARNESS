"""Independent DEV pilot cycles only; no sealed data, model or native calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_pilot_live as pilot, cad_verify_v4_model_judge as judge
from tools import cad_verify_v4_ledger as ledger
from tools.cad_verify_guard import Stop
from tools.test_support import start_tempdirs, stop_tempdirs
from tools.test_verify_v4_family_live import dev_card


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def passing_record(record_id="U1"):
    return dict(id=record_id, worker_status="PASS", status="UNVERIFIED",
                artifact_verdict=dict(status="PASS", result=dict(judges=[dict(status="PASS", metric="validity")])),
                first_handover=dict(status="PASS", attempt=1, critical_dimension_error=False, fabrication=False),
                artifact_bundle=dict(native=dict(sha256="a" * 64), step=dict(sha256="b" * 64)),
                judge=dict(status="PASS", verdict=dict(schema=judge.VERDICT_SCHEMA, rubric_id=record_id,
                    items=[dict(id="visual", status="PASS", reason="Independent DEV")],
                    critical_dimension_error=False, fabrication=False)), user_verdict=None)


def user_verdict(*, seconds=0, **kwargs):
    return dict(visual_status="PASS", first_handover_accepted=True, correction_elapsed_s=seconds,
                correction_proof=None, critical_dimension_error=False, fabrication=False, **kwargs)


class PilotFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).absolute()
        self.paths, self.files = {}, {}
        for target in ("subprocess.run", "subprocess.Popen", "socket.socket.connect"):
            item = patch(target, side_effect=AssertionError("live/native/provider access prohibited"))
            item.start()
            self.addCleanup(item.stop)
        self.rubric = dict(schema="cad-harness.pilot-rubric.v4", status="draft", preregistered=False,
            tasks=[dict(id=key, **{"pass": [dict(item="Independent DEV numerical gate")],
                                  "astra_user_visual": [dict(item="Independent DEV visual gate")]}) for key in pilot.ROSTER])
        self.add_file("rubric", self.rubric)
        self.add_file("authority", "Independent DEV external authority evidence, not an actual user approval")
        self.originals = {}
        for name in ("requests.md", "U1.step", "U2.step", "U3.step", "U4.step", "U5_logo.png"):
            key = "original-" + name
            self.add_file(key, "Independent DEV original " + name + "; not real pilot material")
            self.originals[name] = key
        contour = dict(schema="cad-harness.contour.v4c", asset_id="logo", units="mm", profile="c-s1",
                       loops=[dict(role="outer", segments=[dict(kind="line", p0=[0, 0], p1=[2, 0]),
                                                         dict(kind="line", p0=[2, 0], p1=[0, 2]),
                                                         dict(kind="line", p0=[0, 2], p1=[0, 0])])])
        # Intake-only synthetic typed data; no geometric/native PASS is claimed.
        self.add_file("contour", contour)
        self.add_file("u5-prepared", dict(schema="cad-harness.prepared.v4c", profile="c-s1", assets=dict(logo=contour)))
        self.commitment()
        entries = []
        for record_id in pilot.ROSTER:
            refs = {}
            for kind in ("request", "input_manifest", "prepared", "card", "context"):
                if record_id == "U5" and kind == "prepared":
                    refs[kind] = "u5-prepared"
                else:
                    key = record_id + "-" + kind
                    if kind == "card":
                        value = dev_card(dict(family=pilot.PRIMARY_FAMILIES[record_id], profile=pilot.PROFILES[record_id]))
                    elif kind == "input_manifest":
                        assets = {}
                        if record_id != "U5":
                            original = self.files[self.originals[record_id+".step"]]
                            assets["reference"] = dict(kind="step", role="reference",
                                **{field: original[field] for field in ("path", "sha256", "bytes")})
                        value = dict(schema="cad-harness.inputs.v4c", profile=pilot.PROFILES[record_id], assets=assets)
                    else:
                        value = "Independent DEV " + record_id + " " + kind
                    self.add_file(key, value)
                    refs[kind] = key
            entries.append(dict(id=record_id, family=pilot.PRIMARY_FAMILIES[record_id],
                                profile=pilot.PROFILES[record_id], stratum="DEV", images=[], **refs))
        self.registration = dict(schema="cad-harness.live-registration.v1", phase="pilot", trial_id="DEV-pilot",
            cycle_id="DEV-cycle", source_root=str(self.root), files=self.files, entries=entries,
            order=list(pilot.ROSTER), budget=dict(pilot.RESERVATIONS), generator=dict(pilot.MODEL), judge=dict(pilot.MODEL),
            rubric=dict(file="rubric", preregistration="preregistration"),
            cycle=dict(kind="initial", previous_manifest_sha256=None, retry_authorization=None),
            custody=dict(bundle="pilot-v4", contour="contour", prepared="u5-prepared", commitment="commitment", asset_id="logo"))
        self.preregister()
        self.manifest = self.root / "DEV-manifest.json"
        ledger.write_json(self.manifest, dict(independent_dev=True))
        self.reads = []

    def add_file(self, key, value):
        path = self.root / (key + (".json" if isinstance(value, (dict, list)) else ".txt"))
        raw = (json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
               if isinstance(value, (dict, list)) else value.encode("utf-8"))
        path.write_bytes(raw)
        self.paths[key] = path
        self.files[key] = dict(path=path.name, sha256=ledger.sha(raw), bytes=len(raw), role="independent_dev")
        return path

    def commitment(self):
        text = "# Independent DEV custody commitment\n\n## Pilot inputs\n\n| File | Bytes | SHA-256 |\n| --- | ---: | --- |\n"
        for name, key in self.originals.items():
            text += f"| {name} | {self.files[key]['bytes']} | `{self.files[key]['sha256']}` |\n"
        text += "\n## Pilot v4 (synthetic DEV)\n\n| File | Bytes | SHA-256 |\n| --- | ---: | --- |\n"
        for name, key in (("native/contour.json", "contour"), ("native/prepared.json", "u5-prepared")):
            text += f"| {name} | {self.files[key]['bytes']} | `{self.files[key]['sha256']}` |\n"
        self.add_file("commitment", text)

    def preregister(self, **overrides):
        value = dict(schema="cad-harness.pilot-preregistration.v1", status="approved", authority="authorized_custodian",
                     authority_evidence="authority", trial_id=self.registration["trial_id"], cycle_id=self.registration["cycle_id"],
                     rubric_sha256=self.files["rubric"]["sha256"], input_sha256=pilot._bindings(self.registration),
                     acknowledges_draft_rubric=True, previous_manifest_sha256=self.registration["cycle"]["previous_manifest_sha256"])
        value.update(overrides)
        self.add_file("preregistration", value)
        return value

    def path(self, key):
        self.reads.append(key)
        return self.paths[key]

    def fake_session(self, *, stop_at=None, stop_reason="budget_exhausted", failures=None, images=True):
        fixture = self
        class Session:
            def __init__(self):
                self.registration = copy.deepcopy(fixture.registration)
                self.out = fixture.root / "run"
                self.out.mkdir()
                self.mode = "unit_mock"
                self.generated, self.judgments, self.calls, self.events = [], [], [], []
            def path(self, key):
                return fixture.path(key)
            def check(self):
                return None
            def execute_plan(self, entry, out, **kwargs):
                if stop_at == entry["id"]:
                    raise Stop(stop_reason)
                if entry["id"] in self.generated:
                    raise AssertionError("task retake")
                self.generated.append(entry["id"])
                fixture.assertEqual(kwargs["pool"], "pilot")
                fixture.assertIs(kwargs["one_attempt"], True)
                fixture.assertEqual(kwargs["max_calls"], 3)
                fixture.assertEqual((kwargs["model"], kwargs["thinking"]), ("openai-codex/gpt-6-astra", "max"))
                row = passing_record(entry["id"])
                if failures and entry["id"] in failures:
                    row.update(failures[entry["id"]])
                return dict(status=row["worker_status"], artifact_verdict=row["artifact_verdict"],
                            first_handover=row["first_handover"], artifact_bundle=row["artifact_bundle"],
                            images=[fixture.root / (entry["id"] + "-actual-generated-view.png")] if images else [],
                            error=row.get("error"), stop_reason=row.get("stop_reason"), native_cad_intervals=[], driver_result={})
            def judge(self, record_id, request, deterministic, rubric, **kwargs):
                self.judgments.append(record_id)
                return judge.adjudicate(self, record_id, request, deterministic, rubric, **kwargs)
            def call(self, record_id, request, data, **kwargs):
                self.calls.append(dict(record_id=record_id, **kwargs))
                return json.dumps(dict(schema=judge.VERDICT_SCHEMA, rubric_id=record_id,
                    items=[dict(id=item["id"], status="PASS", reason="Independent fixture only") for item in data["rubric"]["items"]],
                    critical_dimension_error=False, fabrication=False))
            def event(self, kind, **fields):
                self.events.append((kind, fields))
            def summary(self):
                return dict(charged_pools=dict(pilot=len(self.generated) + len(self.calls)))
        return Session()

    def run_mock(self, session):
        from tools import cad_verify_v4_trials as trials
        with patch.object(trials, "TrialSession") as constructor:
            constructor.return_value.__enter__.return_value = session
            result = pilot.run(self.manifest, self.root / "external-authorization.json", session.out,
                               process=lambda *args, **kwargs: self.fail("provider process forbidden"))
        self.assertEqual(constructor.call_args.kwargs["phase"], "pilot")
        return result


class PilotRegistrationTests(PilotFixture):
    def test_full_roster_is_immutable_and_never_drops_unsupported_tasks(self):
        pilot.validate_registration(self.registration)
        for mutate in (lambda value: value["entries"].pop(2), lambda value: value["entries"][2].update(id="U1"),
                       lambda value: value["order"].remove("U4"), lambda value: value["entries"].reverse(),
                       lambda value: value["entries"][2].update(excluded=True)):
            value = copy.deepcopy(self.registration)
            mutate(value)
            with self.assertRaises(ValueError):
                pilot.validate_registration(value)
        self.assertEqual(self.reads, [])

    def test_user_tasks_cannot_be_reclassified_into_weaker_stage_profiles(self):
        value = copy.deepcopy(self.registration)
        value["entries"][2]["profile"] = "c-s1"
        with self.assertRaisesRegex(ValueError, "entry_structure"):
            pilot.validate_registration(value)

    def test_committed_user_step_cannot_be_substituted_even_with_new_preregistration(self):
        manifest = ledger.read_json(self.paths["U1-input_manifest"])
        wrong = self.files[self.originals["U4.step"]]
        manifest["assets"]["reference"].update({key:wrong[key] for key in ("path","sha256","bytes")})
        self.add_file("U1-input_manifest", manifest)
        self.preregister()
        with self.assertRaisesRegex(ValueError, "committed_original_step_mismatch:U1"):
            pilot.validate_bound_inputs(self.registration, self.path)

    def test_c5_continuity_card_cannot_be_omitted_from_the_real_pilot(self):
        card = ledger.read_json(self.paths["U3-card"])
        card["criteria"] = [item for item in card["criteria"] if item["metric"] != "g2_continuity"]
        self.add_file("U3-card", card)
        self.preregister()
        with self.assertRaisesRegex(ValueError, "family_c5_g2_deviation"):
            pilot.validate_bound_inputs(self.registration, self.path)

    def test_original_custody_evidence_cannot_disappear_from_a_new_preregistration(self):
        self.files.pop(self.originals["U2.step"])
        self.preregister()
        with self.assertRaisesRegex(ValueError, "committed_original_input_missing:U2.step"):
            pilot.validate_bound_inputs(self.registration, self.path)

    def test_pilot_pool_is_shared_40_with_no_borrowing_and_exact_astra_max(self):
        for mutate in (lambda value: value.update(budget=dict(pilot=41)),
                       lambda value: value.update(budget=dict(pilot=40, holdout=163)),
                       lambda value: value["generator"].update(model="openai-codex/gpt-6.1-sol"),
                       lambda value: value["judge"].update(thinking="high")):
            value = copy.deepcopy(self.registration)
            mutate(value)
            with self.assertRaisesRegex(ValueError, "model_or_shared_40"):
                pilot.validate_registration(value)

    def test_draft_rubric_requires_bound_authoritative_external_preregistration(self):
        before = self.paths["rubric"].read_bytes()
        pilot.validate_bound_inputs(self.registration, self.path)
        self.assertEqual(self.paths["rubric"].read_bytes(), before)
        self.assertFalse(ledger.read_json(self.paths["rubric"])["preregistered"])
        for overrides in (dict(status="draft"), dict(authority="generator"), dict(acknowledges_draft_rubric=False),
                          dict(rubric_sha256="0" * 64), dict(input_sha256={}), dict(authority_evidence="missing")):
            with self.subTest(overrides=overrides):
                self.preregister(**overrides)
                with self.assertRaisesRegex(ValueError, "external_preregistration_binding"):
                    pilot.validate_bound_inputs(self.registration, self.path)
        self.preregister()

    def test_retry_cycle_needs_separate_40_authorization_and_fresh_quota(self):
        self.registration["cycle"] = dict(kind="retry", previous_manifest_sha256="c" * 64, retry_authorization="retry")
        self.registration["cycle_id"] = "DEV-retry"
        with self.assertRaisesRegex(ValueError, "separate_retry_authorization"):
            pilot.validate_registration(self.registration)
        approval = dict(schema="cad-harness.pilot-retry-authorization.v1", status="approved", trial_id="DEV-pilot",
            cycle_id="DEV-retry", previous_manifest_sha256="c" * 64, budget=dict(pilot=40), fresh_quota_required=True,
            authority_evidence="authority")
        self.add_file("retry", approval)
        self.preregister()
        pilot.validate_bound_inputs(self.registration, self.path)
        for key, value in (("fresh_quota_required", False), ("cycle_id", "DEV-cycle"), ("budget", dict(pilot=80)),
                           ("previous_manifest_sha256", "d" * 64)):
            self.add_file("retry", dict(approval, **{key: value}))
            with self.assertRaisesRegex(ValueError, "separate_retry_authorization_binding"):
                pilot.validate_bound_inputs(self.registration, self.path)

    def test_u5_intake_consumes_only_bound_pilot_v4_typed_contour_never_png(self):
        self.files["original-png"] = dict(path="not-released.png", sha256="d" * 64, bytes=10, role="checker_only")
        self.preregister()
        pilot.validate_bound_inputs(self.registration, self.path)
        self.assertIn("contour", self.reads)
        self.assertIn("u5-prepared", self.reads)
        self.assertNotIn("original-png", self.reads)
        self.registration["custody"]["bundle"] = "pilot-v3"
        with self.assertRaisesRegex(ValueError, "u5_bound_pilot_v4"):
            pilot.validate_bound_inputs(self.registration, self.path)

    def test_u5_changed_contour_or_unbound_prepared_packet_is_refused(self):
        self.add_file("contour", dict(schema="cad-harness.contour.v4c", asset_id="logo", units="mm", loops=[]))
        self.preregister()
        with self.assertRaisesRegex(ValueError, "u5_pilot_v4_contour_binding"):
            pilot.validate_bound_inputs(self.registration, self.path)
        self.commitment()
        self.preregister()
        with self.assertRaisesRegex(ValueError, "u5_typed_contour_intake"):
            pilot.validate_bound_inputs(self.registration, self.path)


class PilotCycleTests(PilotFixture):
    def test_run_attempts_each_task_once_same_cycle_and_keeps_missing_user_verdict_unverified(self):
        session = self.fake_session()
        result = self.run_mock(session)
        self.assertEqual(session.generated, list(pilot.ROSTER))
        self.assertEqual(session.judgments, list(pilot.ROSTER))
        self.assertEqual(result["denominator"], 5)
        self.assertEqual([row["id"] for row in result["records"]], list(pilot.ROSTER))
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertTrue(all(row["status"] == "UNVERIFIED" and row["user_verdict"] is None for row in result["records"]))
        self.assertFalse(result["final_v4_ready"])
        self.assertTrue(all(call["pool"] == "pilot" and call["max_calls"] == 1 and call["images"] for call in session.calls))
        self.assertIn("same model", result["same_model_caveat"])

    def test_budget_or_quota_stop_keeps_full_denominator_without_retry_or_borrowing(self):
        for stop in ("budget_exhausted", "quota_hard_stop", "quota_soft_stop"):
            with self.subTest(stop=stop):
                session = self.fake_session(stop_at="U3", stop_reason=stop)
                result = self.run_mock(session)
                self.assertEqual(session.generated, ["U1", "U2"])
                self.assertEqual(result["status"], "INCOMPLETE")
                self.assertEqual(len(result["records"]), 5)
                self.assertTrue(all(row["status"] == "INCOMPLETE" for row in result["records"][2:]))
                # Keep independent result trees between subcases, without rerunning any completed cycle.
                self.root = self.root / "next"
                self.root.mkdir()
                self.manifest = self.root / "DEV-manifest.json"
                ledger.write_json(self.manifest, dict(independent_dev=True))

    def test_worker_errors_remain_actual_status_not_incomplete_and_no_retakes(self):
        session = self.fake_session(failures={"U3": dict(worker_status="FAIL", error="native_specific_failure",
                                                       first_handover=None, artifact_bundle=None),
                                              "U4": dict(worker_status="ERROR", error="worker_specific_error",
                                                         first_handover=None, artifact_bundle=None)})
        result = self.run_mock(session)
        rows = {row["id"]: row for row in result["records"]}
        self.assertEqual((rows["U3"]["status"], rows["U3"]["error"]), ("FAIL", "native_specific_failure"))
        self.assertEqual((rows["U4"]["status"], rows["U4"]["error"]), ("ERROR", "worker_specific_error"))
        self.assertEqual(session.generated, list(pilot.ROSTER))
        self.assertNotIn("U3", session.judgments)
        self.assertNotIn("U4", session.judgments)

    def test_postprocessing_exception_keeps_previous_records_and_unstarted_denominator(self):
        session = self.fake_session()
        execute = session.execute_plan
        def interrupted(entry, out, **kwargs):
            if entry["id"] == "U2":
                session.generated.append(entry["id"])
                raise OSError("Independent DEV rendering timeout")
            return execute(entry, out, **kwargs)
        session.execute_plan = interrupted
        result = self.run_mock(session)
        self.assertEqual([row["status"] for row in result["records"]],
                         ["UNVERIFIED", "ERROR", "NOT_RUN", "NOT_RUN", "NOT_RUN"])
        self.assertEqual(session.generated, ["U1", "U2"])
        self.assertEqual(session.judgments, ["U1"])
        self.assertIsNotNone(result["records"][0]["first_handover"])
        self.assertEqual(result["records"][1]["error"]["type"], "OSError")
        self.assertEqual(ledger.read_json(session.out / "summary.json")["denominator"], 5)

    def test_every_actual_handover_receives_one_astra_judgment_even_noncritical_native_fail(self):
        session = self.fake_session(failures={"U3": dict(worker_status="FAIL",
            artifact_verdict=dict(status="FAIL", checks=[dict(id="noncritical", status="FAIL")]),
            first_handover=dict(status="FAIL", attempt=1, critical_dimension_error=None, fabrication=None))})
        result = self.run_mock(session)
        self.assertEqual(session.judgments, list(pilot.ROSTER))
        self.assertEqual(session.generated, list(pilot.ROSTER))
        record = result["records"][2]
        self.assertEqual(record["worker_status"], "FAIL")
        self.assertIsNotNone(record["judge"]["verdict"])
        self.assertEqual(sum(call["record_id"] == "U3" for call in session.calls), 1)

    def test_missing_actual_output_views_never_uses_input_paths_as_visual_substitute(self):
        self.add_file("reference-image", "Independent fixture image admission bytes")
        self.files["reference-image"]["role"] = "judge_image"
        for entry in self.registration["entries"]:
            entry["images"] = ["reference-image"]
        self.preregister()
        session = self.fake_session(images=False)
        result = self.run_mock(session)
        self.assertEqual(session.calls, [])
        self.assertTrue(all(row["judge"]["reason"] == "approved_visual_evidence_missing" for row in result["records"]))
        self.assertEqual(result["status"], "UNVERIFIED")

    def test_explicit_retry_cycle_reexecutes_full_roster_with_fresh_isolated_accounting(self):
        initial = self.fake_session(failures={"U3": dict(worker_status="FAIL", error="independent failure")})
        previous = self.run_mock(initial)
        old_summary_path = initial.out / "summary.json"
        old_summary = old_summary_path.read_bytes()
        self.registration["cycle_id"] = "DEV-authorized-retry"
        self.registration["cycle"] = dict(kind="retry", previous_manifest_sha256=previous["manifest_sha256"],
                                          retry_authorization="retry")
        # A different output tree and external authorization are mandatory; no
        # successful U1/U2/U4/U5 record from the failed cycle enters this cycle.
        self.root = self.root / "authorized-retry"
        self.root.mkdir()
        self.add_file("retry", dict(schema="cad-harness.pilot-retry-authorization.v1", status="approved",
            trial_id=self.registration["trial_id"], cycle_id=self.registration["cycle_id"],
            previous_manifest_sha256=previous["manifest_sha256"], budget=dict(pilot=40),
            fresh_quota_required=True, authority_evidence="authority"))
        self.preregister()
        self.manifest = self.root / "DEV-manifest.json"
        ledger.write_json(self.manifest, dict(independent_dev=True, cycle="retry"))
        retry = self.fake_session()
        result = self.run_mock(retry)
        self.assertEqual(retry.generated, list(pilot.ROSTER))
        self.assertEqual(result["cycle_id"], "DEV-authorized-retry")
        self.assertEqual(result["accounting"]["charged_pools"], dict(pilot=10))
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(old_summary_path.read_bytes(), old_summary)


class FirstHandoverGateTests(unittest.TestCase):
    def test_first_handover_five_minute_boundary_and_missing_user_verdict(self):
        record = passing_record()
        self.assertEqual(pilot.evaluate_record(record), "UNVERIFIED")
        proof = dict(status="PASS", elapsed_s=300, native_verdict=dict(status="PASS"))
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=300)), "UNVERIFIED")
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=300), proof), "PASS")
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=300.0001)), "FAIL")
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=0)), "PASS")
        for key in ("critical_dimension_error", "fabrication"):
            actual = user_verdict()
            actual[key] = True
            self.assertEqual(pilot.evaluate_record(record, actual), "FAIL")
        actual = user_verdict()
        actual["first_handover_accepted"] = False
        self.assertEqual(pilot.evaluate_record(record, actual), "FAIL")

    def test_fatal_first_handover_cannot_be_repaired_into_a_pass(self):
        for first in (dict(status="FAIL"), dict(status="PASS", critical_dimension_error=True),
                      dict(status="PASS", fabrication=True)):
            record = passing_record()
            record["first_handover"] = first
            self.assertEqual(pilot.evaluate_record(record, user_verdict()), "FAIL")
        record = passing_record()
        record["artifact_verdict"]["result"]["judges"][0]["status"] = "FAIL"
        self.assertEqual(pilot.evaluate_record(record, user_verdict()), "FAIL")


class UserVerdictIntakeTests(PilotFixture):
    def make_summary(self):
        out = self.root / "completed"
        out.mkdir()
        value = dict(schema="cad-harness.pilot-trial.v1", trial_id="DEV-pilot", cycle_id="DEV-cycle",
                     manifest_sha256="f" * 64, roster=list(pilot.ROSTER), denominator=5,
                     records=[passing_record(record_id) for record_id in pilot.ROSTER], status="UNVERIFIED", evidence_mode="unit_mock")
        ledger.write_json(out / "summary.json", value)
        return out, value

    def external(self, summary, record, **overrides):
        evidence = self.root / (record["id"] + "-external-user-message.txt")
        evidence.write_bytes(b"Independent DEV evidence fixture, not a real user's verdict")
        value = dict(schema="cad-harness.pilot-user-verdict.v1", authority="user", source_id="DEV-external-message",
            evidence_sha256=ledger.file_sha(evidence), trial_id=summary["trial_id"], cycle_id=summary["cycle_id"],
            manifest_sha256=summary["manifest_sha256"], record_id=record["id"], handover_sha256=pilot.handover_sha256(record),
            **user_verdict())
        value.update(overrides)
        path = self.root / (record["id"] + "-external-verdict.json")
        path.write_text(json.dumps(value, allow_nan=True), encoding="utf-8")
        return path, evidence

    def test_intake_append_only_preserves_history_and_all_five_same_cycle_are_required(self):
        out, summary = self.make_summary()
        original = (out / "summary.json").read_bytes()
        first_paths = None
        for index, record in enumerate(summary["records"]):
            paths = self.external(summary, record)
            first_paths = first_paths or paths
            result = pilot.record_user_verdict(out, *paths)
            self.assertEqual(result["receipt"]["status"], "PASS")
            self.assertEqual(result["cycle"]["status"], "PASS" if index == 4 else "UNVERIFIED")
        self.assertEqual((out / "summary.json").read_bytes(), original)
        with self.assertRaises(FileExistsError):
            pilot.record_user_verdict(out, *first_paths)
        self.assertEqual(pilot.user_results(out)["status"], "PASS")
        self.assertFalse(pilot.user_results(out)["final_v4_ready"])

    def test_wrong_cycle_manifest_handover_or_absent_numeric_elapsed_is_not_user_acceptance(self):
        out, summary = self.make_summary()
        for overrides in (dict(cycle_id="another-cycle"), dict(manifest_sha256="0" * 64),
                          dict(handover_sha256="0" * 64), dict(correction_elapsed_s=None),
                          dict(correction_elapsed_s=float("nan")), dict(authority="assistant"),
                          dict(evidence_sha256="0" * 64)):
            with self.subTest(overrides=overrides):
                paths = self.external(summary, summary["records"][0], **overrides)
                with self.assertRaises(ValueError):
                    pilot.record_user_verdict(out, *paths)
        self.assertEqual(pilot.user_results(out)["status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
