"""Fixed A probe and worker; imported on ordinary Python without loading CAD."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

TOL = 1e-6  # run04-script.py; bbox tolerance is separately runbook +/-0.1 mm.
GOAL_VOLUME = 22239.9556819442  # run02/run04/run05-cad.json measurements.
BOX_KEYS = ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max",
            "x_length", "y_length", "z_length")


def near(a, b):
    return abs(a - b) < TOL


def bbox(shape):
    box = shape.BoundBox
    return dict(zip(BOX_KEYS, (box.XMin, box.XMax, box.YMin, box.YMax,
                              box.ZMin, box.ZMax, box.XLength, box.YLength, box.ZLength)))


def numeric_predicates(m):
    b = m["bound_box_mm"]
    return {
        "bbox": all(abs(b[k] - v) <= 0.1 for k, v in
                    zip(("x_length", "y_length", "z_length"), (40, 30, 20))),
        "volume": m["volume_mm3"] < 22500 and abs(m["volume_mm3"] / GOAL_VOLUME - 1) <= 0.01,
        "faces": m["face_count"] == 15,
        "valid_solid": m["solid_count"] == 1 and m["is_valid"] is True,
    }


def matches(points, ends):
    def ordered(a, b):
        return all(near(x, y) for p, q in zip(a, b) for x, y in zip(p, q))
    return len(points) == 2 and (ordered(points, ends) or ordered(points[::-1], ends))


def rectangle_segments(x, y, z):
    points = [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    return [(points[i], points[(i + 1) % 4]) for i in range(4)]


def covers(records, segments):
    return (len(records) == len(segments) and all(r["line"] for r in records)
            and all(sum(matches(r["endpoints_mm"], s) for r in records) == 1 for s in segments))


def inner_predicate(records):
    segments = rectangle_segments(10, 7.5, 20) + rectangle_segments(10, 7.5, 15)
    segments += [((x, y, 15), (x, y, 20)) for x in (-10, 10) for y in (-7.5, 7.5)]
    return covers(records, segments) and all(
        r["adjacent_face_count"] == 2 and r["adjacent_normal_dot"] is not None
        and near(r["adjacent_normal_dot"], 0) for r in records)


def link(value):
    while isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return value


def edge_record(edge, part):
    return {"endpoints_mm": [[v.Point.x, v.Point.y, v.Point.z] for v in edge.Vertexes],
            "line": isinstance(edge.Curve, part.Line), "length_mm": edge.Length}


def probe(doc, body):
    import Part
    shape = body.Shape
    measured = {"bound_box_mm": bbox(shape), "volume_mm3": shape.Volume,
                "area_mm2": shape.Area, "face_count": len(shape.Faces),
                "solid_count": len(shape.Solids), "is_valid": shape.isValid()}
    checks = numeric_predicates(measured)
    floor, walls, inner = [], [], []
    for face in shape.Faces:
        if not isinstance(face.Surface, Part.Plane):
            continue
        b, n = bbox(face), face.normalAt(0, 0)
        if all(near(b[k], v) for k, v in zip(
                ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max"),
                (-10, 10, -7.5, 7.5, 15, 15))) and near(abs(n.z), 1):
            floor.append(face)
        xwall = near(b["x_min"], b["x_max"]) and near(abs(b["x_min"]), 10)
        ywall = near(b["y_min"], b["y_max"]) and near(abs(b["y_min"]), 7.5)
        span = ((xwall and near(b["y_min"], -7.5) and near(b["y_max"], 7.5))
                or (ywall and near(b["x_min"], -10) and near(b["x_max"], 10)))
        if span and near(b["z_min"], 15) and near(b["z_max"], 20) and near(n.z, 0):
            walls.append(face)
    for edge in shape.Edges:
        record = edge_record(edge, Part)
        points = record["endpoints_mm"]
        if len(points) != 2 or not all(
                -10 - TOL <= x <= 10 + TOL and -7.5 - TOL <= y <= 7.5 + TOL
                and 15 - TOL <= z <= 20 + TOL for x, y, z in points):
            continue
        if not (any(all(near(p[0], x) for p in points) for x in (-10, 10))
                or any(all(near(p[1], y) for p in points) for y in (-7.5, 7.5))):
            continue
        adjacent = [f for f in shape.Faces if any(edge.isSame(e) for e in f.Edges)]
        normals = [f.normalAt(0, 0) for f in adjacent if isinstance(f.Surface, Part.Plane)]
        record.update(adjacent_face_count=len(adjacent), adjacent_normal_dot=
                      normals[0].dot(normals[1]) if len(adjacent) == len(normals) == 2 else None)
        inner.append(record)
    checks.update(pocket_floor=len(floor) == 1, pocket_walls=len(walls) == 4,
                  pocket_inner_sharp=inner_predicate(inner))
    types = ("PartDesign::Body", "Sketcher::SketchObject", "PartDesign::Pad",
             "PartDesign::Pocket", "PartDesign::Fillet")
    groups = {t: [o for o in doc.Objects if o.TypeId == t] for t in types}
    checks["feature_counts"] = [len(groups[t]) for t in types] == [1, 2, 1, 1, 1]
    origin = body.Origin
    auxiliaries = [o for o in doc.Objects if o.TypeId not in types]
    checks["standard_auxiliaries"] = all(
        o.TypeId in ("App::Origin", "App::Line", "App::Plane", "App::Point")
        and (o == origin or (o in origin.OriginFeatures and origin in o.InList))
        for o in auxiliaries)
    checks["feature_chain"] = False
    checks["outer_fillet"] = False
    if checks["feature_counts"]:
        pad, pocket, fillet = (groups[t][0] for t in types[2:])
        base, top = link(pad.Profile), link(pocket.Profile)
        checks["feature_chain"] = (
            groups[types[0]][0] == body and base != top
            and base in groups[types[1]] and top in groups[types[1]]
            and all(o in body.Group for o in (base, pad, top, pocket, fillet))
            and body.Tip == fillet and fillet.Base[0] == pocket
            and link(top.AttachmentSupport) == pad and str(top.MapMode) == "FlatFace")
        checks["sketches"] = all(
            near(bbox(s.Shape)[k], v) for s, expected in (
                (base, (-20, 20, -15, 15, 0, 0)),
                (top, (-10, 10, -7.5, 7.5, 20, 20)))
            for k, v in zip(BOX_KEYS[:6], expected))
        checks["pad_pocket_lengths"] = all(
            near(o.Length.Value, length) and str(o.Type) in ("Length", "0")
            and not o.Reversed and (
                str(o.SideType) == o.getEnumerationsOfProperty("SideType")[0]
                if "SideType" in o.PropertiesList else not o.Midplane)
            for o, length in ((pad, 20), (pocket, 5)))
        pb = bbox(pad.Shape)
        checks["pad_one_direction"] = near(pb["z_min"], 0) and near(pb["z_max"], 20)
        names = list(fillet.Base[1])
        selected = []
        for name in names:
            if not name.startswith("Edge") or not name[4:].isdigit():
                break
            index = int(name[4:]) - 1
            if not 0 <= index < len(pocket.Shape.Edges):
                break
            selected.append(edge_record(pocket.Shape.Edges[index], Part))
        checks["outer_fillet"] = (
            len(names) == 4 and len(set(names)) == 4 and len(selected) == 4
            and near(fillet.Radius.Value, 3) and not getattr(fillet, "UseAllEdges", False)
            and covers(selected, rectangle_segments(20, 15, 20)))
    return {"measurements": measured, "predicates": checks, "probe_pass": all(checks.values()),
            "reference": {"volume_mm3": GOAL_VOLUME, "volume_rule": "below_22500_and_within_1_percent",
                          "bbox_tolerance_mm": 0.1, "face_count": 15,
                          "source": "runbook section 6; run02/run04/run05-cad.json"}}


def execute(app, builder, model_path, emit, probe_fn=None):
    """The actual exception boundary, also exercised with a fake App in unit tests."""
    probe_fn = probe_fn or probe
    result = {"status": "failed", "failed_phase": None, "code_owner": None,
              "next_actor": None, "script_completed": False, "probe_pass": None,
              "probe_status": "not_run", "measurements": None, "predicate_diff": None,
              "document_closed": False, "owned_pid": os.getpid(),
              "gui_up": getattr(app, "GuiUp", None), "freecad_version": list(app.Version())}
    doc, phase, owner = None, "launch", "harness"
    emit("ready", {"owned_pid": result["owned_pid"], "gui_up": result["gui_up"]})
    try:
        if result["gui_up"] != 0 or result["freecad_version"][:3] != ["1", "1", "4"]:
            raise RuntimeError("unsupported_runtime")
        if app.listDocuments():
            raise RuntimeError("startup_documents")
        doc = app.newDocument("CadRunA")
        phase, owner = "build", "script"
        body = builder(doc)
        if body is None or body.Document != doc or body.TypeId != "PartDesign::Body":
            raise ValueError("build_contract")
        if set(app.listDocuments()) != {doc.Name}:
            raise ValueError("build_document_contract")
        owner = "harness"
        doc.recompute()
        emit("event", {"phase": "build", "event": "build_finished", "status": "ok"})
        phase, owner = "probe", "probe"
        observed = probe_fn(doc, body)
        result.update(probe_pass=observed["probe_pass"],
                      probe_status="pass" if observed["probe_pass"] else "predicate_fail",
                      measurements=observed["measurements"], reference=observed.get("reference"),
                      predicate_diff=[k for k, passed in observed["predicates"].items() if not passed])
        emit("event", {"phase": "probe", "event": "probe_finished",
                      "status": "ok" if observed["probe_pass"] else "failed",
                      "data": {"predicate": observed["predicates"]}})
        phase, owner = "build", "harness"
        doc.saveAs(str(model_path))
        if not Path(model_path).is_file():
            raise OSError("model_missing")
        result["script_completed"] = True
        result.update(status="ok" if result["probe_pass"] else "failed",
                      failed_phase=None if result["probe_pass"] else "probe",
                      code_owner=None if result["probe_pass"] else "script",
                      next_actor=None if result["probe_pass"] else "sol")
    except Exception as exc:
        result.update(status="failed", failed_phase=phase, code_owner=owner,
                      next_actor="sol" if owner == "script" else "human",
                      error_type=type(exc).__name__)
        if phase == "probe":
            result.update(probe_pass=None, probe_status="exception")
        emit("event", {"phase": phase, "event": phase + "_finished", "status": "failed"})
    finally:
        if doc is not None:
            try:
                app.closeDocument(doc.Name)
                result["document_closed"] = not app.listDocuments()
            except Exception as exc:
                result["close_error_type"] = type(exc).__name__
        if not result["document_closed"]:
            result["status"], result["next_actor"] = "failed", "human"
            if result["failed_phase"] is None:
                result.update(failed_phase="cleanup", code_owner="harness")
    return result


def main():
    request = json.loads((Path.cwd() / "request.json").read_text(encoding="utf-8"))
    with (Path.cwd() / "worker-events.jsonl").open("x", encoding="utf-8") as stream:
        def emit(kind, payload):
            stream.write(json.dumps({"kind": kind, **payload}, allow_nan=False) + "\n")
            stream.flush()
        try:
            import FreeCAD as App
            def builder(doc):
                source = Path.cwd() / "input.py"
                if hashlib.sha256(source.read_bytes()).hexdigest() != request["script_sha256"]:
                    raise ValueError("input_hash_mismatch")
                namespace = runpy.run_path(str(source))
                return namespace["build"](doc)
            result = execute(App, builder, Path.cwd() / "model.FCStd", emit)
        except Exception as exc:
            result = {"status": "failed", "failed_phase": "launch", "code_owner": "harness",
                      "next_actor": "human", "script_completed": False, "probe_status": "not_run",
                      "probe_pass": None, "document_closed": False, "owned_pid": os.getpid(),
                      "error_type": type(exc).__name__}
        result.update(schema="cad-harness.cad_run.worker.v0",
                      attempt_id=request["attempt_id"], script_sha256=request["script_sha256"])
        with (Path.cwd() / "worker-result.json").open("x", encoding="utf-8") as output:
            json.dump(result, output, allow_nan=False)
    # FreeCAD's console recipe consumes empty stdin and exits; raw CAD exit is host-owned.


if __name__ == "__main__" or ("FreeCAD" in sys.modules and (Path.cwd() / "request.json").is_file()):
    main()
