"""VERIFY v4 freeze tests: temporary public fixtures and mocked --version only."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tools import cad_verify_v4_freeze as frozen, cad_verify_v4_ledger as ledger
from tools.cad_verify_guard import Stop
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class FreezeV4(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "repo"
        self.root.mkdir()
        for name in frozen.FIXED_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
        self.policy = self.root / frozen.DESIGN / "policy.json"
        self.policy_value = ledger.read_json(frozen.ROOT / frozen.DESIGN / "policy.json")
        self.policy.write_text(json.dumps(self.policy_value), encoding="utf-8")
        skill = self.root / "skills/cad-harness-v4"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "Mock frozen instruction\n<!-- policy:start -->\n" + json.dumps(self.policy_value)
            + "\n<!-- policy:end -->\n", encoding="utf-8")
        (skill / "modeling.md").write_text("Mock modeling prose\n", encoding="utf-8")
        (self.root / "skills/freecad-modeling/SKILL.md").write_bytes((skill / "modeling.md").read_bytes())
        (skill / "contracts.md").write_text("Mock compiler contract\n", encoding="utf-8")
        (self.root / "tools/nested").mkdir(parents=True)
        for name in ("cad_verify_v4_freeze.py", "test_verify_v4_freeze.py", "nested/fixture.py"):
            (self.root / "tools" / name).write_text("# mock code\n", encoding="utf-8")
        self.commitment = self.base / "public-commitment.json"
        ledger.write_json(self.commitment, dict(arbitrary=True, files={
            "C:/dev/v4-holdout-private/not-read.json": "opaque-public-commitment",
            "absent/never-opened.json": "another-opaque-commitment"}))
        self.exe = self.base / "omp-mock.exe"
        self.exe.write_bytes(b"mock executable bytes; never launched")
        self.cad_dir = self.base / "freecad-mock"
        self.cadexe = self.cad_dir / "bin/freecadcmd.exe"
        self.cadexe.parent.mkdir(parents=True)
        self.cadexe.write_bytes(b"mock CAD executable; never launched")
        cad_location = patch.object(frozen.cad_run, "FREECAD_DIR", self.cad_dir)
        cad_version = patch.object(frozen, "_binary_version", return_value="1.1.4")
        cad_location.start()
        self.cad_version_mock = cad_version.start()
        self.addCleanup(cad_location.stop)
        self.addCleanup(cad_version.stop)
        self.host = patch.object(frozen.socket, "gethostname", return_value="MOCK-OFFLINE")
        self.which = patch.object(frozen.shutil, "which", return_value=str(self.exe))
        # Isolate the version stub from platform's use of the real subprocess module.
        self.runner = patch.object(frozen, "subprocess", SimpleNamespace(
            run=Mock(side_effect=self.version), DEVNULL=subprocess.DEVNULL,
            SubprocessError=subprocess.SubprocessError))
        self.host_mock = self.host.start()
        self.which_mock = self.which.start()
        self.run_mock = self.runner.start().run
        self.addCleanup(self.host.stop)
        self.addCleanup(self.which.stop)
        self.addCleanup(self.runner.stop)
        self.counter = 0

    def version(self, argv, **kwargs):
        self.assertEqual(argv, [str(self.exe), "--version"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertIs(kwargs["shell"], False)
        return subprocess.CompletedProcess(argv, 0, stdout="omp mock 1.0\n", stderr="")

    def freeze(self, **kwargs):
        self.counter += 1
        out = self.base / ("freeze-%d" % self.counter)
        value = frozen.freeze(self.policy, self.commitment, out, root=self.root, **kwargs)
        return out / "manifest.json", value

    def authorization(self, **updates):
        value = dict(schema="cad-harness.live-authorization.v4", phase="holdout", charged_calls=163,
                     clock_confirmation=True, model=frozen.MODEL, host="DPC-019",
                     quota_snapshot=str(self.base / "absent-quota.json"), independent_control_validation=True,
                     holdout_commitment_sha256=ledger.file_sha(self.commitment))
        value.update(updates)
        self.counter += 1
        path = self.base / ("authorization-%d.json" % self.counter)
        ledger.write_json(path, value)
        return path, value

    def rewrite(self, path, value, *, rebind=False):
        # Deliberate temporary tampering, never production overwrite/resume.
        if rebind:
            sha_path = path.parent / "SHA256.json"
            sha_path.write_text(json.dumps(frozen._sha_payload(value)), encoding="utf-8")
            value["sha256_file"] = ledger.file_sha(sha_path)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_offline_default_does_not_authorize_or_follow_commitment_paths(self):
        actual = ledger.file_sha
        reads = []

        def record(path):
            reads.append(Path(path))
            return actual(path)

        with patch.object(ledger, "file_sha", side_effect=record), patch.dict(os.environ, {
            "CAD_HARNESS_LIVE_AUTHORIZED": "1", "CAD_HARNESS_AUTHORIZED_CALLS": "163"}):
            path, manifest = self.freeze()
            checked = frozen.verify(path, root=self.root)
        self.assertIsNone(manifest["authorization"])
        self.assertIsNone(manifest["quota_snapshot"])
        self.assertEqual(checked, manifest)
        self.assertEqual(manifest["host"]["hostname"], "MOCK-OFFLINE")
        self.assertEqual(manifest["host"]["required_host"], "DPC-019")
        self.assertEqual(manifest["host"]["required_freecad"], "1.1.4")
        self.assertEqual(manifest["host"]["freecad"], dict(recipe="freecadcmd", executable=str(self.cadexe),
                                                         version="1.1.4", sha256=actual(self.cadexe)))
        self.assertEqual(manifest["generator"]["sha256"], actual(self.exe))
        self.assertEqual(manifest["generator"]["version"], "omp mock 1.0")
        self.assertEqual(ledger.read_json(self.policy)["live_authorized_calls"], 0)
        self.assertIn("tools/nested/fixture.py", manifest["files"])
        self.assertIn("tools/cad_verify_v4_freeze.py", manifest["files"])
        self.assertIn("tools/test_verify_v4_freeze.py", manifest["files"])
        self.assertEqual(self.run_mock.call_count, 2)
        self.assertTrue(all(p in (self.commitment, self.exe, self.cadexe) or p.is_relative_to(self.root)
                            or p.is_relative_to(path.parent) for p in reads))

    def test_changed_code_skill_modeling_policy_and_public_plans_rejected(self):
        names = ("tools/nested/fixture.py", "skills/cad-harness-v4/contracts.md",
                 "skills/cad-harness-v4/SKILL.md", "skills/cad-harness-v4/modeling.md",
                 "skills/freecad-modeling/SKILL.md", frozen.DESIGN + "/policy.json",
                 frozen.DESIGN + "/PLAN-V4-UPDATE-U1.md", frozen.DESIGN + "/DECISIONS.md",
                 "design/cad-harness-mvp/build-schema.json")
        for name in names:
            with self.subTest(name=name):
                path, unused = self.freeze()
                target = self.root / name
                original = target.read_bytes()
                try:
                    target.write_bytes(original + b"\n ")
                    with self.assertRaises(Stop):
                        frozen.verify(path, root=self.root)
                finally:
                    target.write_bytes(original)

    def test_added_and_deleted_code_cannot_escape_file_set_binding(self):
        path, unused = self.freeze()
        added = self.root / "tools/nested/new_module.py"
        added.write_text("# newly added code", encoding="utf-8")
        with self.assertRaisesRegex(Stop, "file_set_binding_mismatch"):
            frozen.verify(path, root=self.root)
        added.unlink()
        (self.root / "tools/nested/fixture.py").unlink()
        with self.assertRaisesRegex(Stop, "file_set_binding_mismatch"):
            frozen.verify(path, root=self.root)

    def test_host_changes_and_spoofed_host_input_rejected(self):
        path, unused = self.freeze()
        self.host_mock.return_value = "OTHER-HOST"
        with self.assertRaisesRegex(Stop, "host_binding_mismatch"):
            frozen.verify(path, root=self.root)
        self.assertIsNone(frozen.verify(path, root=self.root, check_host=False)["authorization"])
        with self.assertRaisesRegex(Stop, "host_override_not_actual"):
            self.freeze(host="DPC-019")

    def test_commitment_changed_and_missing_rejected_without_following_references(self):
        path, unused = self.freeze()
        original = self.commitment.read_bytes()
        self.commitment.write_bytes(original + b" ")
        with self.assertRaisesRegex(Stop, "commitment_binding_mismatch"):
            frozen.verify(path, root=self.root)
        self.commitment.unlink()
        with self.assertRaisesRegex(Stop, "freeze_file_unreadable"):
            frozen.verify(path, root=self.root)

    def test_empty_missing_invalid_maps_and_wrong_schema_rejected(self):
        path, original = self.freeze()
        malformed = [dict(original, files={}), dict(original, files=[]),
                     dict(original, schema="cad-harness.manifest.v3"),
                     dict(original, files={"tools/nested/fixture.py": "bad-digest"}),
                     {key: value for key, value in original.items() if key != "files"}, None]
        for value in malformed:
            with self.subTest(value=value):
                self.rewrite(path, value)
                with self.assertRaisesRegex(Stop, "manifest_contract"):
                    frozen.verify(path, root=self.root)

    def test_map_cannot_omit_or_add_bindings_even_with_recomputed_sha(self):
        for remove in (True, False):
            with self.subTest(remove=remove):
                path, manifest = self.freeze()
                if remove:
                    manifest["files"].pop("tools/nested/fixture.py")
                else:
                    manifest["files"]["../outside.py"] = "a" * 64
                self.rewrite(path, manifest, rebind=True)
                with self.assertRaisesRegex(Stop, "file_set_binding_mismatch"):
                    frozen.verify(path, root=self.root)

    def test_adjacent_sha_and_manifest_payload_tampering_rejected(self):
        path, manifest = self.freeze()
        sha_path = path.parent / "SHA256.json"
        sha_path.write_bytes(sha_path.read_bytes() + b" ")
        with self.assertRaisesRegex(Stop, "sha_manifest_mismatch"):
            frozen.verify(path, root=self.root)
        path, manifest = self.freeze()
        manifest["authorization"] = dict(schema="cad-harness.live-authorization.v4")
        self.rewrite(path, manifest)
        with self.assertRaisesRegex(Stop, "sha_manifest_mismatch"):
            frozen.verify(path, root=self.root)

    def test_executable_binary_version_and_resolution_drift_rejected(self):
        path, unused = self.freeze()
        original = self.exe.read_bytes()
        self.exe.write_bytes(b"changed mock binary")
        with self.assertRaisesRegex(Stop, "executable_binding_mismatch"):
            frozen.verify(path, root=self.root)
        self.exe.write_bytes(original)
        self.run_mock.side_effect = lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout="omp mock 2.0\n", stderr="")
        with self.assertRaisesRegex(Stop, "executable_binding_mismatch"):
            frozen.verify(path, root=self.root)
        self.run_mock.side_effect = self.version
        self.exe.unlink()
        self.which_mock.return_value = None
        with self.assertRaisesRegex(Stop, "executable_binding_mismatch"):
            frozen.verify(path, root=self.root)

    def test_unavailable_omp_still_permits_offline_freeze(self):
        self.which_mock.return_value = None
        path, manifest = self.freeze(omp="absent-fixture-omp")
        self.assertEqual(manifest["generator"], dict(model=frozen.MODEL, thinking="xhigh",
                                                   omp=None, version=None, sha256=None))
        self.assertEqual(frozen.verify(path, root=self.root), manifest)
        self.run_mock.assert_not_called()

    def test_explicit_authorization_freezes_but_never_invokes_model_or_cad(self):
        self.host_mock.return_value = "DPC-019"
        auth_path, auth = self.authorization()
        path, manifest = self.freeze(authorization_path=auth_path)
        self.assertEqual(manifest["authorization"], auth)
        self.assertEqual(manifest["quota_snapshot"], auth["quota_snapshot"])
        self.assertFalse(Path(auth["quota_snapshot"]).exists())
        auth_path.unlink()  # Frozen evidence, not a dependency on mutable authorization input.
        self.assertEqual(frozen.verify(path, root=self.root), manifest)
        self.assertEqual(self.run_mock.call_count, 2)
        self.assertEqual(ledger.read_json(self.policy)["live_authorized_calls"], 0)
        self.host_mock.return_value = "NOT-DPC-019"
        with self.assertRaises(Stop):
            frozen.verify(path, root=self.root, check_host=False)

    def test_freecad_binary_and_observed_version_are_bound_without_cad_calls(self):
        path, unused = self.freeze()
        original = self.cadexe.read_bytes()
        self.cadexe.write_bytes(b"changed mock CAD executable")
        with self.assertRaisesRegex(Stop, "host_binding_mismatch"):
            frozen.verify(path, root=self.root)
        self.cadexe.write_bytes(original)
        self.cad_version_mock.return_value = "1.1.5"
        with self.assertRaisesRegex(Stop, "host_binding_mismatch"):
            frozen.verify(path, root=self.root)
        self.host_mock.return_value = "DPC-019"
        auth_path, unused = self.authorization()
        with self.assertRaisesRegex(Stop, "live_freecad_identity_missing_or_wrong_version"):
            self.freeze(authorization_path=auth_path)
        self.cad_version_mock.return_value = None
        with self.assertRaisesRegex(Stop, "live_freecad_identity_missing_or_wrong_version"):
            self.freeze(authorization_path=auth_path)
        self.cadexe.unlink()
        path, manifest = self.freeze()
        self.assertEqual(manifest["host"]["freecad"], dict(recipe="freecadcmd", executable=None,
                                                         version=None, sha256=None))
        self.assertIsNone(frozen.verify(path, root=self.root)["authorization"])
        with self.assertRaisesRegex(Stop, "live_freecad_identity_missing_or_wrong_version"):
            self.freeze(authorization_path=auth_path)

    def test_authorization_requires_every_evidence_field(self):
        self.host_mock.return_value = "DPC-019"
        invalid = dict(schema="wrong", phase="pilot", charged_calls=40, clock_confirmation=False,
                       model="other-model", host="OTHER", quota_snapshot="relative.json",
                       independent_control_validation=False, holdout_commitment_sha256="0" * 64)
        for key, value in invalid.items():
            with self.subTest(key=key):
                auth_path, unused = self.authorization(**{key: value})
                with self.assertRaises((Stop, ValueError)):
                    self.freeze(authorization_path=auth_path)
        auth_path, unused = self.authorization()
        with self.assertRaisesRegex(Stop, "live_authorization_contract"):
            self.freeze(authorization_path=auth_path, quota_snapshot=str(self.base / "other-quota.json"))
        null_path = self.base / "null-authorization.json"
        ledger.write_json(null_path, None)
        with self.assertRaisesRegex(Stop, "live_authorization_contract"):
            self.freeze(authorization_path=null_path)
        self.host_mock.return_value = "MOCK-OFFLINE"
        with self.assertRaisesRegex(Stop, "live_host_mismatch"):
            self.freeze(authorization_path=auth_path)

    def test_live_authorization_rechecked_not_inferred_from_manifest_flags(self):
        self.host_mock.return_value = "DPC-019"
        auth_path, unused = self.authorization()
        path, original = self.freeze(authorization_path=auth_path)
        for key in original["authorization"]:
            with self.subTest(missing=key):
                manifest = copy.deepcopy(original)
                del manifest["authorization"][key]
                self.rewrite(path, manifest, rebind=True)
                with self.assertRaises((Stop, ValueError)):
                    frozen.verify(path, root=self.root)
        for key, value in (("model", "other"), ("thinking", "low")):
            manifest = copy.deepcopy(original)
            manifest["generator"][key] = value
            self.rewrite(path, manifest, rebind=True)
            with self.assertRaisesRegex(Stop, "generator_contract"):
                frozen.verify(path, root=self.root)
        manifest = copy.deepcopy(original)
        manifest["limits"]["proposed_reservations"]["holdout"] = 164
        self.rewrite(path, manifest, rebind=True)
        with self.assertRaisesRegex(Stop, "frozen_limits_mismatch"):
            frozen.verify(path, root=self.root)

    def test_fixed_policy_and_generator_settings_are_required_at_freeze(self):
        for updates in (dict(generator_model="other"), dict(thinking="low")):
            with self.assertRaisesRegex(Stop, "generator_settings_drift"):
                self.freeze(**updates)
        self.policy_value["live_authorized_calls"] = 163
        self.policy.write_text(json.dumps(self.policy_value), encoding="utf-8")
        with self.assertRaisesRegex(Stop, "freeze_policy_drift"):
            self.freeze()

    def test_exclusive_outputs_and_manifest_claim_never_overwrite(self):
        path, manifest = self.freeze()
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "output_exists_or_linked"):
            frozen.freeze(self.policy, self.commitment, path.parent, root=self.root)
        claimed = frozen.claim(path, self.base / "holdout-run")
        self.assertEqual(claimed["manifest_sha256"], ledger.sha(before))
        with self.assertRaisesRegex(Stop, "manifest_already_claimed"):
            frozen.claim(path, self.base / "different-run")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(frozen.verify(path, root=self.root), manifest)
        copied = self.base / "copied-freeze"
        copied.mkdir()
        (copied / "manifest.json").write_bytes(before)
        (copied / "SHA256.json").write_bytes((path.parent / "SHA256.json").read_bytes())
        with self.assertRaisesRegex(Stop, "manifest_original_directory_required"):
            frozen.verify(copied / "manifest.json", root=self.root)
        with self.assertRaisesRegex(Stop, "manifest_original_directory_required"):
            frozen.claim(copied / "manifest.json", self.base / "third-run")


if __name__ == "__main__":
    unittest.main()
