"""Trusted artifact-only FreeCAD worker; never imports or executes the generator."""
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
if __package__:
    from .cad_spec_probe import load_gold, probe, Checks, BOX_KEYS, same_bounds
else:
    from cad_spec_probe import load_gold, probe, Checks, BOX_KEYS, same_bounds


def verify(app, part, request, directory):
    gold_reader, artifact_probe = load_gold, probe
    if request.get("probe_profile") == "verify-v3":
        if __package__:
            from .cad_verify_v3_probe import load_gold as gold_reader, probe as artifact_probe
        else:
            from cad_verify_v3_probe import load_gold as gold_reader, probe as artifact_probe
    elif request.get("probe_profile") == "verify-v2":
        if __package__:
            from .cad_verify_v2_probe import load_gold as gold_reader, probe as artifact_probe
        else:
            from cad_verify_v2_probe import load_gold as gold_reader, probe as artifact_probe
    elif request.get("probe_profile") == "verify-v1":
        if __package__:
            from .cad_verify_probe import load_gold as gold_reader, probe as artifact_probe
        else:
            from cad_verify_probe import load_gold as gold_reader, probe as artifact_probe
    result = {"schema": "cad-harness.verify.v1", "owned_pid": os.getpid(),
              "verification_pass": False, "document_closed": False, "artifacts": {}}
    result.update({key: request.get(key) for key in
                   ("task_id", "attempt_id", "script_sha256", "probe_profile", "gold_sha256", "spec_sha256")})
    checks = Checks(request["task_id"])
    try:
        if getattr(app, "GuiUp", None) != 0 or list(app.Version())[:3] != ["1", "1", "4"] or app.listDocuments():
            raise ValueError("unsupported_verify_runtime")
        gold_path = directory / "gold.json"
        if hashlib.sha256(gold_path.read_bytes()).hexdigest() != request["gold_sha256"]:
            raise ValueError("verify_gold_hash")
        gold = gold_reader(gold_path)
        if gold["case_id"] != request["task_id"]:
            raise ValueError("verify_gold_task")
        hashes = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                  for name in ("model.FCStd", "model.step")}
        if hashes != request["artifact_sha256"]:
            raise ValueError("verify_artifact_hash")
        result["artifact_sha256"] = hashes
        for name in ("model.FCStd", "model.step"):
            doc = None
            try:
                if name.endswith("FCStd"):
                    doc = app.openDocument(str(directory / name))
                    doc.recompute()
                    bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
                    if len(bodies) != 1:
                        raise ValueError("reimport_body_count")
                    body = bodies[0]
                else:
                    doc = app.newDocument("StepVerify")
                    imported = doc.addObject("Part::Feature", "ImportedSolid")
                    imported.Shape = part.read(str(directory / name))
                    doc.recompute()
                    body = SimpleNamespace(Shape=imported.Shape)
                observed = artifact_probe(doc, body, gold, require_editability=name.endswith("FCStd"))
                result["artifacts"][name] = observed
                checks.add("reimport", name + ".gold_geometry", True, observed["probe_pass"], observed["probe_pass"])
                m, built = observed["measurements"], request["built"]
                actual = [m["bound_box_mm"][k] for k in BOX_KEYS]
                expected = [built["bound_box_mm"][k] for k in BOX_KEYS]
                checks.add("reimport", name + ".world_bbox", expected, actual,
                           same_bounds(actual, expected, .01), .01)
                target = built["volume_mm3"]
                checks.add("reimport", name + ".volume", target, m["volume_mm3"],
                           abs(m["volume_mm3"] / target - 1) <= 1e-4, 1e-4)
            finally:
                if doc is not None:
                    app.closeDocument(doc.Name)
        result["verification_pass"] = all(checks.predicates.values())
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_code"] = str(exc) if str(exc).startswith(("verify_", "reimport_", "unsupported_")) else "verify_exception"
    finally:
        for name in list(app.listDocuments()):
            try:
                app.closeDocument(name)
            except Exception as exc:
                result["close_error_type"] = type(exc).__name__
        result["document_closed"] = not app.listDocuments()
        result["verification_pass"] &= result["document_closed"]
        records = list(checks.records)
        for name, observed in result["artifacts"].items():
            records.extend(dict(row, sub_check_id=name + "." + row["sub_check_id"], passed=False)
                           for row in observed["predicate_details"]["checks"])
        if __package__:
            from .cad_spec_probe import make_details
        else:
            from cad_spec_probe import make_details
        result["predicate_details"] = make_details(request["task_id"], records)
    return result


def main():
    import FreeCAD as App
    import Part
    directory = Path.cwd()
    request = json.loads((directory / "verify-request.json").read_text(encoding="utf-8"))
    with (directory / "verify-events.jsonl").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"owned_pid": os.getpid(), "gui_up": getattr(App, "GuiUp", None)}) + "\n")
    result = verify(App, Part, request, directory)
    with (directory / "verify-result.json").open("x", encoding="utf-8") as output:
        json.dump(result, output, allow_nan=False)


if __name__ == "__main__" or ("FreeCAD" in sys.modules and (Path.cwd() / "verify-request.json").is_file()):
    main()
