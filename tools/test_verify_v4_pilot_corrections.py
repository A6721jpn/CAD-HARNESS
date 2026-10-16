"""Independent human-correction fixtures with real neutral dispatch and injected workers.

No model, FreeCAD process, private input, pilot attachment, or provider is used.
The mock native worker derives its answer from independent submitted numeric data;
artifact admission, job construction, stream capture and closed-ledger proof run normally.
"""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_pilot_live as pilot, cad_verify_v4_artifacts as artifacts
from tools import cad_verify_v4_ledger as ledger, cad_verify_v4_s1 as s1
from tools import cad_verify_v4_artifact_judges as metrics
from tools.test_verify_v4_pilot_live import PilotFixture, passing_record, user_verdict
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class FixtureClock:
    boot_id = "independent-dev-boot"
    implementation = "independent-dev-system-monotonic"
    def __init__(self):
        self.value, self.utc_offset = 1000.0, 0.0
    def __call__(self):
        return self.value
    def utc(self):
        return (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.value + self.utc_offset)).isoformat()
    def advance(self, seconds):
        self.value += seconds


class PilotCorrectionTests(PilotFixture):
    def setUp(self):
        super().setUp()
        self.clock = FixtureClock()
        self.native_calls, self.sessions = [], []
        self.worker_duration = 5.0
        self.add_file("U1-card", dict(required_width_mm=10.0))
        self.add_file("U1-context", dict(independent_dev=True))
        self.preregister()
        self.lock = self.root / "DEV-integrated-lock.json"
        self.lock.write_text('{"independent_dev_lock": true}', encoding="utf-8")
        self.authorization = self.root / "DEV-authorization.json"
        self.authorization.write_text('{"independent_dev_authorization": true}', encoding="utf-8")
        self.manifest.write_text(json.dumps(dict(registration_data=self.registration, integrated_lock=pilot._file(self.lock))), encoding="utf-8")
        self.run_dir = self.root / "original-pilot"
        self.run_dir.mkdir()
        self.original_bundle = self.make_bundle("original-handover", width=9.0)
        self.original = passing_record()
        self.original.update(worker_status="FAIL", artifact_bundle=str(self.original_bundle),
            artifact_verdict=dict(status="FAIL", result=dict(checks=[dict(id="width", status="FAIL")])),
            first_handover=dict(status="FAIL", attempt=1, critical_dimension_error=None, fabrication=None,
                                artifact_bundle_sha256=ledger.file_sha(self.original_bundle)))
        self.original["judge"]["status"] = "FAIL"
        self.original["judge"]["verdict"]["items"][0]["status"] = "FAIL"
        self.summary = dict(schema="cad-harness.pilot-trial.v1", trial_id=self.registration["trial_id"],
            cycle_id=self.registration["cycle_id"], manifest_sha256=ledger.file_sha(self.manifest),
            roster=list(pilot.ROSTER), denominator=5, records=[self.original] + [passing_record(key) for key in pilot.ROSTER[1:]],
            status="FAIL", evidence_mode="unit_mock")
        self.save_summary()
        # Only independent admission dependencies are substituted. artifacts.check,
        # s1.native_work, bundle admission, job writing, raw streams and ledgers remain real.
        admission = patch.object(s1, "_manifest_inputs", side_effect=lambda manifest, prepared, **kwargs:
                                 (Path(manifest), dict(evidence_mode="independent_dev"), {}))
        context = patch.object(metrics, "validate_context", return_value=dict(independent_dev=True))
        bindings = patch.object(s1, "implementation_bindings", return_value={"independent-checker": "a" * 64})
        capture = patch.object(s1.runtime_binding, "capture", return_value=dict(schema="DEV-runtime", files={}))
        verify = patch.object(s1.runtime_binding, "verify", return_value=None)
        for item in (admission, context, bindings, capture, verify):
            item.start()
            self.addCleanup(item.stop)
        from tools import cad_verify_v4_trials as trials
        session = patch.object(trials, "TrialSession", side_effect=self.session_factory)
        session.start()
        self.addCleanup(session.stop)

    def save_summary(self):
        (self.run_dir / "summary.json").write_text(json.dumps(self.summary), encoding="utf-8")

    def make_bundle(self, name, *, width, critical=False, fabrication=False):
        folder = self.root / name
        folder.mkdir()
        native, step = folder / "result.FCStd", folder / "result.step"
        native.write_bytes(b"Independent DEV native admission bytes; injected native worker only")
        step.write_text(json.dumps(dict(width_mm=width, critical_dimension_error=critical, fabrication=fabrication)), encoding="utf-8")
        bundle = folder / "bundle.json"
        ledger.write_json(bundle, dict(schema="cad-harness.artifact-bundle.v4", profile="c-s1",
            evidence_mode="independent_dev", native=pilot._file(native), step=pilot._file(step),
            output_object="IndependentDEV", extensions=[], probes=[]))
        return bundle

    def native_process(self, argv, captures, *, cwd, timeout):
        job = ledger.read_json(Path(argv[argv.index("--job") + 1]))
        self.assertEqual(job["operation"], "artifact-verify")
        self.assertNotIn("plan", job)
        self.assertEqual(Path(job["card"]), self.paths["U1-card"])
        self.assertEqual(Path(job["context"]), self.paths["U1-context"])
        bundle, files, _ = artifacts.load_bundle(job["bundle"], profile="c-s1")
        submitted = ledger.read_json(files["step"])
        required = ledger.read_json(job["card"])["required_width_mm"]
        status = "PASS" if submitted["width_mm"] == required else "FAIL"
        self.native_calls.append(dict(job=job, timeout=timeout, submitted=submitted, status=status))
        self.clock.advance(self.worker_duration)
        captures["stdout"].feed(("independent native numeric width check: " + status + "\n").encode("ascii"))
        captures["stderr"].feed(b"")
        result = dict(schema="cad-harness.artifact-check-result.v4", profile="c-s1", status=status,
            bindings={key + "_sha256": ledger.file_sha(job[key]) for key in ("manifest", "prepared", "card", "context", "bundle")},
            artifacts={key: pilot._file(files[key]) for key in ("native", "step")},
            checks=[dict(id="width", status=status, measured=submitted["width_mm"], expected=required)],
            critical_dimension_error=submitted["critical_dimension_error"], fabrication=submitted["fabrication"],
            runtime_binding=pilot._file(job["runtime_binding"]), gui_up=0, document_closed=True, live_calls=0)
        ledger.write_json(Path(job["out"]) / "result.json", result)
        return 0 if status == "PASS" else 1

    def session_factory(self, manifest, authorization, out, **kwargs):
        fixture = self
        self.assertEqual(Path(kwargs["validation_of"]), self.run_dir)
        self.assertEqual(kwargs["phase"], "pilot")
        self.assertEqual(Path(manifest), self.manifest)
        self.assertEqual(Path(authorization), self.authorization)
        class ValidationSession:
            def __init__(self):
                self.out = ledger.new_directory(out)
                self.registration = copy.deepcopy(fixture.registration)
                self.manifest = ledger.read_json(fixture.manifest)
                self.manifest_path = fixture.manifest
                self.mode = "unit_mock"
                self.journal = ledger.Journal(self.out / "ledger.jsonl", self.out.name, "pilot-validation", clock=fixture.clock)
            def __enter__(self):
                self.journal.append("run_started", live_calls=0)
                return self
            def __exit__(self, *args):
                self.journal.append("run_finished", **self.summary())
                self.journal.close()
            def check(self):
                return None
            def event(self, kind, **fields):
                return self.journal.append(kind, **fields)
            def summary(self):
                return dict(logical_calls=0, physical_attempts=0, live_calls=0, charged_calls=dict(pilot=0))
            def call(self, *args, **kwargs):
                raise AssertionError("correction path must never call a model")
            def check_artifacts(self, entry, bundle, out, *, timeout):
                self.check()
                self.assert_entry(entry)
                return artifacts.check(fixture.paths[entry["input_manifest"]], fixture.paths[entry["prepared"]],
                    fixture.paths[entry["card"]], fixture.paths[entry["context"]], bundle, out,
                    profile=entry["profile"], timeout=timeout, process=kwargs["native_process"])
            def assert_entry(self, entry):
                fixture.assertEqual(entry, fixture.registration["entries"][0])
        session = ValidationSession()
        self.sessions.append(session)
        return session

    def begin(self):
        return pilot.begin_correction(self.manifest, self.authorization, self.run_dir, "U1",
            process=lambda *args, **kwargs: self.fail("model process forbidden"), wall=self.clock,
            verifier=lambda path: self.fail("verification is owned by validation session"))

    def check(self, bundle, name="check-output"):
        return pilot.check_correction(self.manifest, self.authorization, self.run_dir, "U1", bundle, self.root / name,
            process=lambda *args, **kwargs: self.fail("model process forbidden"), native_process=self.native_process,
            wall=self.clock, verifier=lambda path: self.fail("verification is owned by validation session"))

    def external(self, *, correction=None, seconds=0, visual="PASS"):
        evidence = self.root / "external-user-evidence.txt"
        evidence.write_bytes(b"Independent DEV external user evidence fixture, not actual adoption")
        verdict = dict(schema="cad-harness.pilot-user-verdict.v1", authority="user", source_id="DEV-message",
            evidence_sha256=ledger.file_sha(evidence), trial_id=self.summary["trial_id"], cycle_id=self.summary["cycle_id"],
            manifest_sha256=self.summary["manifest_sha256"], record_id="U1", handover_sha256=pilot.handover_sha256(self.original),
            visual_status=visual, first_handover_accepted=True, correction_elapsed_s=seconds,
            correction_proof=correction, critical_dimension_error=False, fabrication=False)
        path = self.root / "external-verdict.json"
        path.write_text(json.dumps(verdict), encoding="utf-8")
        return path, evidence

    def test_timer_is_exclusive_and_records_actual_clock_identity(self):
        started = self.begin()
        self.assertEqual(started["timer"]["live_calls"], 0)
        self.assertEqual(started["timer"]["started"]["boot_id"], self.clock.boot_id)
        with self.assertRaisesRegex(ValueError, "timer_already_started"):
            self.begin()
        self.assertEqual(self.native_calls, [])

    def test_failed_worker_without_actual_handover_has_no_correction_entry(self):
        self.original.update(first_handover=None, artifact_bundle=None)
        self.save_summary()
        with self.assertRaisesRegex(ValueError, "actual_handover_required"):
            self.begin()
        self.assertEqual(self.sessions, [])
        self.assertEqual(self.native_calls, [])

    def test_missing_native_verification_cannot_accept_claimed_1_to_300_second_edits(self):
        for seconds in (1, 30, 300):
            with self.subTest(seconds=seconds), self.assertRaisesRegex(ValueError, "requires_native_proof"):
                pilot.record_user_verdict(self.run_dir, *self.external(seconds=seconds))
        self.assertFalse((self.run_dir / "user-verdicts/U1").exists())

    def test_native_numeric_failure_stays_failed_despite_human_visual_pass(self):
        self.begin()
        self.clock.advance(250)
        corrected = self.make_bundle("still-wrong", width=9.5)
        self.worker_duration = 10
        checked = self.check(corrected)
        self.assertEqual(self.native_calls[0]["timeout"], 50)
        self.assertEqual(checked["proof"]["elapsed_s"], 260)
        self.assertEqual(checked["proof"]["status"], "FAIL")
        result = pilot.record_user_verdict(self.run_dir, *self.external(correction=checked["proof_file"], seconds=260))
        self.assertEqual(result["receipt"]["status"], "FAIL")
        self.assertEqual(self.native_calls[0]["job"]["operation"], "artifact-verify")

    def test_real_native_dispatch_corrects_noncritical_fail_and_human_is_final_visually(self):
        historical = (self.run_dir / "summary.json").read_bytes()
        self.begin()
        self.clock.advance(100)
        corrected = self.make_bundle("correct-width", width=10)
        self.worker_duration = 20
        checked = self.check(corrected)
        proof = checked["proof"]
        self.assertEqual((proof["status"], proof["elapsed_s"]), ("PASS", 120))
        self.assertIn("native.stdout.bin", proof["native_evidence"])
        self.assertEqual(proof["native_verdict"]["result"]["checks"][0]["measured"], 10)
        result = pilot.record_user_verdict(self.run_dir, *self.external(correction=checked["proof_file"], seconds=120))
        self.assertEqual(result["receipt"]["status"], "PASS")
        self.assertEqual(result["cycle"]["records"][0]["judge"]["status"], "FAIL")
        self.assertEqual(len(result["receipt"]["handover_history"]), 2)
        self.assertEqual((self.run_dir / "summary.json").read_bytes(), historical)
        self.assertEqual(len(self.native_calls), 1)
        self.assertTrue(all(session.summary()["logical_calls"] == 0 for session in self.sessions))

    def test_elapsed_includes_prior_checks_and_waits_never_resets(self):
        self.begin()
        self.clock.advance(20)
        self.worker_duration = 10
        self.check(self.make_bundle("first-noncritical-check", width=9), "first-check")
        self.clock.advance(200)
        self.worker_duration = 15
        checked = self.check(self.make_bundle("final-correct-check", width=10), "second-check")
        self.assertEqual(self.native_calls[1]["timeout"], 70)
        self.assertEqual(checked["proof"]["elapsed_s"], 245)
        result = pilot.record_user_verdict(self.run_dir, *self.external(correction=checked["proof_file"], seconds=245))
        self.assertEqual(result["receipt"]["status"], "PASS")
        self.assertEqual(len(result["receipt"]["handover_history"]), 3)

    def test_native_work_finishing_after_300_seconds_never_passes(self):
        self.begin()
        self.clock.advance(290)
        self.worker_duration = 11
        checked = self.check(self.make_bundle("too-late", width=10))
        self.assertEqual(checked["proof"]["status"], "EXPIRED")
        self.assertEqual(self.native_calls[0]["timeout"], 10)
        with self.assertRaisesRegex(ValueError, "proof_expired"):
            pilot.record_user_verdict(self.run_dir, *self.external(correction=checked["proof_file"], seconds=299))

    def test_already_expired_timer_never_dispatches_native_work(self):
        self.begin()
        self.clock.advance(301)
        with self.assertRaisesRegex(ValueError, "elapsed_expired"):
            self.check(self.make_bundle("expired-before-native", width=10))
        self.assertEqual(self.native_calls, [])

    def test_clock_reboot_backward_and_inconsistent_utc_are_refused(self):
        self.begin()
        self.clock.value = 999
        with self.assertRaisesRegex(ValueError, "clock_backward"):
            self.check(self.make_bundle("backward-clock", width=10), "backward-output")
        self.clock.value = 1010
        self.clock.boot_id = "different-boot"
        with self.assertRaisesRegex(ValueError, "clock_identity_changed"):
            self.check(self.make_bundle("new-boot", width=10), "new-boot-output")
        self.clock.boot_id = "independent-dev-boot"
        self.clock.utc_offset = 100
        with self.assertRaisesRegex(ValueError, "clock_inconsistent"):
            self.check(self.make_bundle("utc-jump", width=10), "utc-jump-output")
        self.assertEqual(self.native_calls, [])

    def test_historical_native_fatal_cannot_be_erased_by_later_pass(self):
        self.begin()
        first = self.check(self.make_bundle("fatal-first-correction", width=9, critical=True), "fatal-check")
        self.assertEqual(first["proof"]["status"], "FAIL")
        final = self.check(self.make_bundle("later-native-pass", width=10), "later-check")
        result = pilot.record_user_verdict(self.run_dir, *self.external(correction=final["proof_file"], seconds=10))
        self.assertEqual(result["receipt"]["status"], "FAIL")
        self.assertTrue(result["receipt"]["handover_history"][1]["native_verdict"]["result"]["critical_dimension_error"])

    def test_original_fatal_and_missing_model_verdict_are_never_corrected_into_pass(self):
        for key in ("critical_dimension_error", "fabrication"):
            record = passing_record()
            record["first_handover"][key] = True
            self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=5),
                dict(status="PASS", elapsed_s=5, native_verdict=dict(status="PASS"))), "FAIL")
        record = passing_record()
        record["judge"] = dict(status="UNVERIFIED", verdict=None, reason="malformed_or_missing_verdict")
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=5),
            dict(status="PASS", elapsed_s=5, native_verdict=dict(status="PASS"))), "UNVERIFIED")
        record["first_handover"] = None
        record["worker_status"] = "FAIL"
        self.assertEqual(pilot.evaluate_record(record, user_verdict()), "FAIL")
        record = passing_record()
        del record["judge"]["verdict"]["schema"]
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=5),
            dict(status="PASS", elapsed_s=5, native_verdict=dict(status="PASS"))), "UNVERIFIED")

    def test_altered_native_stream_invalidates_proof_before_user_receipt(self):
        self.begin()
        checked = self.check(self.make_bundle("bound-final", width=10))
        stream = Path(checked["proof"]["native_evidence"]["native.stdout.bin"]["path"])
        stream.write_bytes(b"altered native evidence")
        with self.assertRaisesRegex(ValueError, "bound_file_changed"):
            pilot.record_user_verdict(self.run_dir, *self.external(correction=checked["proof_file"], seconds=5))
        self.assertFalse((self.run_dir / "user-verdicts/U1").exists())

    def test_altered_proof_and_old_favorable_proof_cannot_replace_latest_check(self):
        self.begin()
        first = self.check(self.make_bundle("earlier-pass", width=10), "earlier-output")
        latest = self.check(self.make_bundle("latest-pass", width=10), "latest-output")
        with self.assertRaisesRegex(ValueError, "proof_not_latest"):
            pilot.record_user_verdict(self.run_dir, *self.external(correction=first["proof_file"], seconds=5))
        proof_path = Path(latest["proof_file"]["path"])
        proof_path.write_bytes(proof_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "bound_file_changed"):
            pilot.record_user_verdict(self.run_dir, *self.external(correction=latest["proof_file"], seconds=10))

    def test_no_edit_claim_cannot_hide_an_actual_correction_check(self):
        self.begin()
        self.check(self.make_bundle("actual-edit", width=10))
        with self.assertRaisesRegex(ValueError, "no_edit_path_cannot_hide_checks"):
            pilot.record_user_verdict(self.run_dir, *self.external(seconds=0))

    def test_editing_same_source_files_preserves_first_and_all_checked_artifact_bytes(self):
        self.begin()
        bundle = ledger.read_json(self.original_bundle)
        step = Path(bundle["step"]["path"])
        step.write_text(json.dumps(dict(width_mm=10, critical_dimension_error=False, fabrication=False)), encoding="utf-8")
        bundle["step"] = pilot._file(step)
        self.original_bundle.write_text(json.dumps(bundle), encoding="utf-8")
        checked = self.check(self.original_bundle)
        first_snapshot = checked["proof"]["first_handover_snapshot"]["artifact_bundle"]
        _, first_files, _ = artifacts.load_bundle(first_snapshot["path"], profile="c-s1")
        _, final_files, _ = artifacts.load_bundle(checked["proof"]["artifact_bundle"]["path"], profile="c-s1")
        self.assertEqual(ledger.read_json(first_files["step"])["width_mm"], 9)
        self.assertEqual(ledger.read_json(final_files["step"])["width_mm"], 10)
        result = pilot.record_user_verdict(self.run_dir, *self.external(correction=checked["proof_file"], seconds=5))
        self.assertEqual(result["receipt"]["status"], "PASS")
        with self.assertRaisesRegex(ValueError, "user_verdict_already_final"):
            self.check(self.original_bundle, "after-final-verdict")


class HumanFinalVisualTests(unittest.TestCase):
    def test_ordinary_valid_astra_visual_fail_can_be_overridden_without_model_rescore(self):
        record = passing_record()
        record["judge"]["status"] = "FAIL"
        record["judge"]["verdict"]["items"][0]["status"] = "FAIL"
        original = copy.deepcopy(record["judge"])
        self.assertEqual(pilot.evaluate_record(record, user_verdict()), "PASS")
        self.assertEqual(record["judge"], original)
        record["judge"]["verdict"]["fabrication"] = True
        self.assertEqual(pilot.evaluate_record(record, user_verdict()), "FAIL")

    def test_budget_stopped_record_keeps_incomplete_even_with_later_human_claim(self):
        record = passing_record()
        record.update(worker_status="INCOMPLETE", stop_reason="quota_stop")
        proof = dict(status="PASS", elapsed_s=5, native_verdict=dict(status="PASS"))
        self.assertEqual(pilot.evaluate_record(record, user_verdict(seconds=5), proof), "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
