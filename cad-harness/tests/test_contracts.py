import copy
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schemas import ValidationError, apply_parameters, load, transition_job, validate


def fixture(name):
    return json.loads((ROOT / "fixtures" / (name + ".json")).read_text(encoding="utf-8"))


class ContractsTest(unittest.TestCase):
    def test_fixture_manifest(self):
        cases = fixture("manifest")
        self.assertEqual({c["file"] for c in cases}, {p.name for p in (ROOT / "fixtures").glob("*.json")} - {"manifest.json"})
        for case in cases:
            with self.subTest(file=case["file"], reason=case["reason"]):
                if case["accepted"]:
                    load(case["type"], ROOT / "fixtures" / case["file"])
                else:
                    with self.assertRaises(ValidationError):
                        load(case["type"], ROOT / "fixtures" / case["file"])

    def test_envelope_boundaries(self):
        limits = {"L": (80, 180), "W": (30, 80), "T": (4, 16), "D": (4, 12), "e": (12, 25)}
        for values in itertools.product(*limits.values()):
            with self.subTest(values=values):
                plate = fixture("plate_valid")
                plate["dimensions"] = {k: f"{v} mm" for k, v in zip(limits, values)}
                validate("PlateSpec", plate)
        for key, (low, high) in limits.items():
            for value in (low - 0.001, high + 0.001):
                with self.subTest(key=key, value=value):
                    plate = fixture("plate_valid")
                    plate["dimensions"][key] = f"{value} mm"
                    with self.assertRaises(ValidationError):
                        validate("PlateSpec", plate)

    def test_decimal_units_and_non_json_values(self):
        for value in [True, None, [], {}, "100", "100 cm", "100 m", "100 deg", "100 mm^2", "NaN mm",
                      "Infinity mm", "1e2 mm", "100 mm\n", "-100 mm"]:
            with self.subTest(value=value):
                plate = fixture("plate_valid")
                plate["dimensions"]["L"] = value
                with self.assertRaises(ValidationError):
                    validate("PlateSpec", plate)
        plate = fixture("plate_valid")
        plate["dimensions"]["L"] = "100.125 mm"
        validate("PlateSpec", plate)

    def test_unknown_keys_at_every_object_boundary(self):
        def objects(data, path=()):
            if isinstance(data, dict):
                yield path
                for key, value in data.items():
                    yield from objects(value, path + (key,))
            elif isinstance(data, list):
                for index, value in enumerate(data):
                    yield from objects(value, path + (index,))
        for kind, name in [("PlateSpec", "plate_valid"), ("Operation", "operation_valid"), ("Operation", "operation_create"),
                           ("Operation", "operation_holes"), ("Observation", "observation_valid"),
                           ("Revision", "revision_valid"), ("Job", "job_valid")]:
            original = fixture(name)
            for path in objects(original):
                with self.subTest(kind=kind, path=path):
                    bad = copy.deepcopy(original)
                    node = bad
                    for key in path:
                        node = node[key]
                    node["unexpected"] = "reject me"
                    with self.assertRaises(ValidationError):
                        validate(kind, bad)

    def test_required_fields(self):
        for kind, name in [("PlateSpec", "plate_valid"), ("Operation", "operation_valid"),
                           ("Observation", "observation_valid"), ("Revision", "revision_valid"), ("Job", "job_valid")]:
            for key in fixture(name):
                with self.subTest(kind=kind, key=key):
                    bad = fixture(name)
                    del bad[key]
                    with self.assertRaises(ValidationError):
                        validate(kind, bad)

    def test_semantic_ids_are_not_native_face_numbers(self):
        for bad_id in ["Face1", "plate.other", "plate.main\n", ""]:
            op = fixture("operation_valid")
            op["target"] = bad_id
            with self.subTest(id=bad_id), self.assertRaises(ValidationError):
                validate("Operation", op)

    def test_patch_preserves_human_length(self):
        base = fixture("plate_valid")
        base["dimensions"]["L"] = "140 mm"
        original = copy.deepcopy(base)
        candidate = apply_parameters(base, [fixture("operation_valid")])
        self.assertEqual(base, original)
        self.assertEqual(candidate["dimensions"], {"L": "140 mm", "W": "40 mm", "T": "10 mm", "D": "8 mm", "e": "15 mm"})

    def test_patch_rejects_invalid_or_extra_operations_atomically(self):
        base = fixture("plate_valid")
        original = copy.deepcopy(base)
        for ops in [[], {}, [fixture("operation_create")], [fixture("operation_valid"), {"op": "delete_body"}],
                    [{"op": "set_parameters", "target": "plate.main", "values": {}}],
                    [{"op": "set_parameters", "target": "plate.main", "values": {"hole_diameter": "13 mm"}}]]:
            with self.subTest(ops=ops), self.assertRaises(ValidationError):
                apply_parameters(base, ops)
            self.assertEqual(base, original)

    def test_every_job_transition(self):
        prefixes = {"queued": ["queued"], "running": ["queued", "running"], "validated": ["queued", "running", "validated"],
                    "committed": ["queued", "running", "validated", "committed"], "failed": ["queued", "failed"],
                    "cancelled": ["queued", "cancelled"], "unknown": ["queued", "unknown"]}
        allowed = {"queued": {"running", "failed", "cancelled", "unknown"},
                   "running": {"validated", "failed", "cancelled", "unknown"},
                   "validated": {"committed", "failed", "cancelled", "unknown"}}
        for before, history in prefixes.items():
            for after in prefixes:
                with self.subTest(before=before, after=after):
                    job = fixture("job_valid")
                    job.update(state=before, history=history)
                    if after in allowed.get(before, set()):
                        result = transition_job(job, after)
                        self.assertEqual(result["history"], history + [after])
                        self.assertEqual(job["state"], before)
                    else:
                        with self.assertRaises(ValidationError):
                            transition_job(job, after)

    def test_job_history_must_agree_with_state(self):
        for history in [["running"], ["queued", "running"], ["queued", "bogus"]]:
            job = fixture("job_valid")
            job["history"] = history
            with self.subTest(history=history), self.assertRaises(ValidationError):
                validate("Job", job)

    def test_revision_lineage_and_job_candidate(self):
        root = fixture("revision_valid")
        root.update(base_revision=None, candidate_id=None)
        validate("Revision", root)
        for updates in [{"base_revision": None}, {"candidate_id": None},
                        {"base_revision": "r2-human-L140"}, {"base_policy": "automatic"}]:
            revision = fixture("revision_valid")
            revision.update(updates)
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                validate("Revision", revision)
        job = fixture("job_valid")
        job["revision"] = root
        validate("Job", job)
        job.update(state="validated", history=["queued", "running", "validated"])
        with self.assertRaises(ValidationError):
            validate("Job", job)
        job = fixture("job_valid")
        job["document_id"] = "another-document"
        with self.assertRaises(ValidationError):
            validate("Job", job)

    def test_boolean_is_not_integer_or_hole_count(self):
        plate = fixture("plate_valid")
        plate["hole_count"] = True
        with self.assertRaises(ValidationError):
            validate("PlateSpec", plate)
        observation = fixture("observation_valid")
        observation["measurements"]["solid_count"] = True
        with self.assertRaises(ValidationError):
            validate("Observation", observation)

    def test_observation_reports_failed_shape_without_claiming_pass(self):
        observation = fixture("observation_valid")
        observation["measurements"].update(hole_count=1, through=False, solid_count=2)
        observation["validation"]["constraints"] = {"status": "fail", "evidence": ["Synthetic invalid solid observation"]}
        result = validate("Observation", observation)
        self.assertEqual(result["validation"]["constraints"]["status"], "fail")
        self.assertEqual(result["state"]["after"]["hole_count"], 2)

    def test_visual_identity_and_failure_are_separate(self):
        observation = fixture("observation_valid")
        observation["visual"] = {"status": "ready", "images": [
            {"revision_id": "r3", "view": "top", "artifact": "synthetic-top.png"},
            {"revision_id": "r3", "view": "isometric", "artifact": "synthetic-iso.png"}]}
        validate("Observation", observation)
        for key, value in [("revision_id", "r2"), ("view", "top")]:
            bad = copy.deepcopy(observation)
            bad["visual"]["images"][1][key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                validate("Observation", bad)
        observation["visual"] = {"status": "failed", "reason": "Synthetic renderer failure", "images": []}
        validate("Observation", observation)

    def test_strict_json_loader(self):
        for payload in ['{"id":"plate.main","id":"plate.other"}', '{"value":NaN}', '{"value":Infinity}']:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"
                path.write_text(payload, encoding="utf-8")
                with self.subTest(payload=payload), self.assertRaises(ValidationError):
                    load("PlateSpec", path)

    def test_validation_returns_independent_value(self):
        plate = fixture("plate_valid")
        result = validate("PlateSpec", plate)
        result["dimensions"]["L"] = "160 mm"
        self.assertEqual(plate["dimensions"]["L"], "100 mm")


if __name__ == "__main__":
    unittest.main()
