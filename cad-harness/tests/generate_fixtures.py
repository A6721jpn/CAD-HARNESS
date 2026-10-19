"""Regenerate deterministic A1 examples, including deliberately invalid inputs."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate():
    plate = {"id": "plate.main", "dimensions": {"L": "100 mm", "W": "40 mm", "T": "8 mm", "D": "6 mm", "e": "15 mm"},
             "hole_count": 2, "symmetric": True, "through": True}
    patch = {"op": "set_parameters", "target": "plate.main", "values": {"hole_diameter": "8 mm", "plate_thickness": "10 mm"}}
    revision = {"revision_id": "r2-human-L140", "document_id": "plate-work-01", "base_revision": "r1",
                "candidate_id": "candidate-01", "base_policy": "require_current"}
    job = {"job_id": "job-01", "request_id": "request-01", "document_id": "plate-work-01", "revision": revision,
           "ops": [patch], "state": "queued", "history": ["queued"]}
    ids = ["plate.main", "Params.L", "Params.W", "Params.T", "Params.D", "Params.e", "Params.P",
           "Body.BaseSketch", "Body.Pad", "Body.HoleSketch", "Body.Pocket", "mount.left", "mount.right"]
    before = copy.deepcopy(plate)
    before["dimensions"]["L"] = "140 mm"
    after = copy.deepcopy(before)
    after["dimensions"].update(D="8 mm", T="10 mm")
    observation = {
        "identification": {"revision_id": "r3", "candidate_id": "candidate-01", "semantic_ids": ids,
                           "native_objects": {key: key.replace(".", "_") for key in ids}},
        "state": {"before": before, "after": after, "pitch_expression": "Params.L - 2 * Params.e",
                  "independent": ["Params.L", "Params.W", "Params.T", "Params.D", "Params.e"], "dependent": ["Params.P"]},
        "measurements": {"bounds": {"L": "140 mm", "W": "40 mm", "T": "10 mm"}, "hole_count": 2,
                         "hole_diameter": "8 mm", "hole_centers": [{"id": "mount.left", "x": "-55 mm", "y": "0 mm"},
                         {"id": "mount.right", "x": "55 mm", "y": "0 mm"}], "through": True, "solid_count": 1},
        "validation": {key: {"status": "unknown", "evidence": ["Synthetic contract fixture; CAD not executed (A2+)."]}
                       for key in ["constraints", "history", "preservation", "reload", "edit_tests"]},
        "visual": {"status": "unknown", "reason": "A1 fixture; no CAD images generated", "images": []}}
    cases = []

    def add(name, kind, data, accepted, reason):
        filename = name + ".json"
        (ROOT / "fixtures" / filename).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        cases.append({"file": filename, "type": kind, "accepted": accepted, "reason": reason})

    for name, kind, data in [("plate_valid", "PlateSpec", plate), ("operation_valid", "Operation", patch),
                             ("revision_valid", "Revision", revision), ("job_valid", "Job", job),
                             ("observation_valid", "Observation", observation)]:
        add(name, kind, data, True, "Valid A1 contract, not evidence of CAD execution")
    create = {"op": "create_body", "target": "plate.main", "values": {"length": "100 mm", "width": "40 mm",
              "plate_thickness": "8 mm", "profile": "centered_rectangle", "sketch_id": "Body.BaseSketch"}}
    holes = {"op": "add_hole_group", "target": "plate.main", "values": {"hole_diameter": "6 mm", "edge_margin": "15 mm",
             "count": 2, "symmetric": True, "through": True, "sketch_id": "Body.HoleSketch", "mount_ids": ["mount.left", "mount.right"]}}
    add("operation_create", "Operation", create, True, "M1 construction contract")
    add("operation_holes", "Operation", holes, True, "M1 construction contract")
    for name, value in [("unit_cm", "10 cm"), ("dimension_area", "100 mm2"), ("unit_missing", 100)]:
        bad = copy.deepcopy(plate)
        bad["dimensions"]["L"] = value
        add(name, "PlateSpec", bad, False, "Only explicit mm lengths accepted")
    bad = copy.deepcopy(patch)
    bad["values"]["length"] = "160 mm"
    add("operation_extra_parameter", "Operation", bad, False, "M2 may change D/T only")
    bad = copy.deepcopy(job)
    bad["ops"].append({"op": "treat_edges", "target": "plate.main", "values": {}})
    add("operation_extra", "Job", bad, False, "Unsupported M4 operation in M1/M2 job")
    bad = copy.deepcopy(plate)
    bad["hole_count"] = 3
    add("shape_three_holes", "PlateSpec", bad, False, "Fixed two-hole template")
    bad = copy.deepcopy(plate)
    bad["through"] = False
    add("shape_blind_holes", "PlateSpec", bad, False, "Through holes required")
    bad = copy.deepcopy(plate)
    bad["dimensions"].update(L="80 mm", e="38 mm", D="8 mm")
    add("shape_touching_holes", "PlateSpec", bad, False, "Outside e envelope and L-2e == D")
    bad = copy.deepcopy(plate)
    bad["dimensions"]["D"] = "13 mm"
    add("range_outside", "PlateSpec", bad, False, "D outside initial test envelope")
    bad = copy.deepcopy(plate)
    bad["dimensions"]["typo"] = "10 mm"
    add("unknown_key", "PlateSpec", bad, False, "Unknown nested key")
    bad = copy.deepcopy(job)
    bad.update(state="committed", history=["queued", "committed"])
    add("job_skipped_states", "Job", bad, False, "Cannot skip running/validated")
    (ROOT / "fixtures" / "manifest.json").write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()
