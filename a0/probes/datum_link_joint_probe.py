"""Run with FreeCADCmd.exe. Artifacts default to a unique temporary directory.

A0_DATUM_PROBE_DIR selects the artifact directory. A0_DATUM_PROBE_MODE=reopen
is reserved for the fresh FreeCADCmd child process. No GUI fallback is used.
"""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

import FreeCAD as App
import Part


OUT = Path(os.environ.get("A0_DATUM_PROBE_DIR") or tempfile.mkdtemp(prefix="a0-datum-"))
OUT.mkdir(parents=True, exist_ok=True)
RESULT = {"probe": "datum-link-joint-headless", "mode": os.environ.get("A0_DATUM_PROBE_MODE", "create"),
          "pid": os.getpid(), "python": sys.version, "freecad": App.Version(),
          "gui_up": App.GuiUp, "artifact_dir": str(OUT), "stages": {}}
CTX = {}


class Unsupported(RuntimeError):
    pass


class Unknown(RuntimeError):
    pass


def stage(key, action):
    entry = {"status": "unknown", "data": {}}
    RESULT["stages"][key] = entry
    try:
        action(entry["data"])
        entry["status"] = "pass"
    except Exception as exc:
        gui_required = (not App.GuiUp and isinstance(exc, NameError)
                        and ("'Gui'" in str(exc) or "'FreeCADGui'" in str(exc)))
        entry.update(status="unsupported" if isinstance(exc, Unsupported) or gui_required else
                     "unknown" if isinstance(exc, Unknown) else "fail",
                     exception_type=type(exc).__name__, exception=str(exc),
                     traceback=traceback.format_exc())
        if gui_required:
            entry["reason"] = "Installed workbench API requires GUI; no GUI fallback attempted"
    print("A0_STAGE " + json.dumps({key: entry}, ensure_ascii=True), flush=True)


def require(*keys):
    for key in keys:
        if RESULT["stages"][key]["status"] != "pass":
            raise Unknown("Dependency did not pass: " + key)


def xyz(vector):
    return [vector.x, vector.y, vector.z]


def close_to(actual, expected):
    assert len(actual) == len(expected)
    assert all(abs(a - b) < 1e-6 for a, b in zip(actual, expected)), (actual, expected)


def healthy(doc):
    bad = {o.Name: list(o.State) for o in doc.Objects if "Invalid" in o.State}
    assert not bad, bad


def measure():
    records = []
    for doc, part, body, sheet, hole in CTX["parts"]:
        datum = doc.getObject("HoleLCS")
        records.append({"document": doc.Name, "L_mm": str(sheet.get("A1")),
                        "length_mm": doc.Box.Length.Value, "volume_mm3": hole.Shape.Volume,
                        "datum_mm": xyz(datum.Placement.Base) if datum else None})
    data = {"parts": records}
    if "links" in CTX:
        data["link_datums_mm"] = [xyz(link.getSubObject("Body.HoleLCS.").Placement.Base)
                                  for link in CTX["links"]]
        data["world_datums_mm"] = [xyz(link.Placement.multVec(doc.HoleLCS.Placement.Base))
                                   for link, (doc, *_) in zip(CTX["links"], CTX["parts"])]
        data["link_placements_mm"] = [xyz(link.Placement.Base) for link in CTX["links"]]
    return data


def create_parts(data):
    CTX["parts"] = []
    for index in (1, 2):
        doc = App.newDocument("ProbePart" + str(index))
        part = doc.addObject("App::Part", "Part")
        sheet = doc.addObject("Spreadsheet::Sheet", "Dimensions")
        part.addObject(sheet)
        # Single-letter L is rejected as an alias (unit name); parameter L
        # lives in A1 and uses the unambiguous expression alias param_L.
        for cell, alias, value in (("A1", "param_L", "40 mm"), ("A2", "param_W", "20 mm"),
                                   ("A3", "param_H", "8 mm")):
            sheet.set(cell, value)
            sheet.setAlias(cell, alias)
        body = doc.addObject("PartDesign::Body", "Body")
        part.addObject(body)
        box = body.newObject("PartDesign::AdditiveBox", "Box")
        for prop, alias in (("Length", "L"), ("Width", "W"), ("Height", "H")):
            box.setExpression(prop, "Dimensions.param_" + alias)
        hole = body.newObject("PartDesign::SubtractiveCylinder", "Hole")
        hole.Radius = 2
        hole.setExpression("Height", "Dimensions.param_H")
        hole.setExpression("Placement.Base.x", "Dimensions.param_L / 2")
        hole.setExpression("Placement.Base.y", "Dimensions.param_W / 2")
        doc.recompute()
        assert hole.Shape.isValid() and len(hole.Shape.Solids) == 1
        assert abs(hole.Shape.Volume - (40 * 20 * 8 - math.pi * 4 * 8)) < 1e-6
        healthy(doc)
        CTX["parts"].append((doc, part, body, sheet, hole))
    data.update(measure())
    data["expressions"] = list(CTX["parts"][0][0].Box.ExpressionEngine)


def create_datums(data):
    require("a")
    data["datums"] = []
    for doc, part, body, sheet, hole in CTX["parts"]:
        # Select the actual bottom circular rim of the through-hole.
        candidates = [(i, e) for i, e in enumerate(hole.Shape.Edges, 1)
                      if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Center.z) < 1e-6]
        assert len(candidates) == 1, len(candidates)
        edge = "Edge" + str(candidates[0][0])
        datum = body.newObject("PartDesign::CoordinateSystem", "HoleLCS")
        datum.AttachmentSupport = [(hole, (edge,))]
        datum.MapMode = "Concentric"
        datum.setExpression("AttachmentOffset.Base.z", "Dimensions.param_H")
        # A datum must not replace the solid feature as Body Tip.
        body.Tip = hole
        doc.recompute()
        close_to(xyz(datum.Placement.Base), [20, 10, 8])
        healthy(doc)
        data["datums"].append({"type": datum.TypeId, "support": repr(datum.AttachmentSupport),
                               "map_mode": datum.MapMode,
                               "expressions": list(datum.ExpressionEngine),
                               "position_mm": xyz(datum.Placement.Base)})


def create_links(data):
    require("a")
    for doc, *_ in CTX["parts"]:
        doc.saveAs(str(OUT / (doc.Name + ".FCStd")))
    doc = App.newDocument("ProbeAssembly")
    # External XLinks require both owner and target to have file paths.
    doc.saveAs(str(OUT / "ProbeAssembly.FCStd"))
    CTX["assembly_doc"] = doc
    CTX["links"] = []
    for index, (source, part, *_) in enumerate(CTX["parts"], 1):
        link = doc.addObject("App::Link", "Link" + str(index))
        link.setLink(part)
        CTX["links"].append(link)
    doc.recompute()
    data["links"] = [{"type": link.TypeId, "linked_document": link.LinkedObject.Document.Name,
                      "linked_object": link.LinkedObject.Name, "shape_valid": link.Shape.isValid(),
                      "volume_mm3": link.Shape.Volume} for link in CTX["links"]]
    assert all(item["shape_valid"] and item["volume_mm3"] > 0 for item in data["links"])
    healthy(doc)


def create_joint(data):
    require("b", "c")
    import JointObject
    doc = CTX["assembly_doc"]
    data["api"] = []
    assembly = doc.addObject("Assembly::AssemblyObject", "Assembly")
    CTX["assembly"] = assembly
    assembly.Type = "Assembly"
    data["api"].append({"call": 'doc.addObject("Assembly::AssemblyObject", "Assembly")', "return": repr(assembly)})
    group = assembly.newObject("Assembly::JointGroup", "Joints")
    data["api"].append({"call": 'assembly.newObject("Assembly::JointGroup", "Joints")', "return": repr(group)})
    for link in CTX["links"]:
        assembly.addObject(link)
    ground = group.newObject("App::FeaturePython", "Ground")
    proxy = JointObject.GroundedJoint(ground, CTX["links"][0])
    data["api"].append({"call": "JointObject.GroundedJoint(ground, Link1)", "return": repr(proxy)})
    joint = group.newObject("App::FeaturePython", "FixedJoint")
    proxy = JointObject.Joint(joint, 0)
    CTX["joint"] = joint
    data["api"].append({"call": "JointObject.Joint(joint, 0)", "return": repr(proxy), "joint_type": joint.JointType})
    refs = [[link, ["Body.HoleLCS.", "Body.HoleLCS."]] for link in CTX["links"]]
    ret = joint.Proxy.setJointConnectors(joint, refs)
    data["api"].append({"call": 'joint.Proxy.setJointConnectors(joint, [[Link1, ["Body.HoleLCS.", "Body.HoleLCS."]], [Link2, ["Body.HoleLCS.", "Body.HoleLCS."]]])', "return": repr(ret)})
    doc.recompute()
    ret = assembly.solve()
    data["api"].append({"call": "assembly.solve()", "return": repr(ret)})
    assert ret == 0, ret
    data["references"] = [repr(joint.Reference1), repr(joint.Reference2)]
    healthy(doc)
    data.update(measure())


def change_and_solve(data):
    require("d")
    data["before"] = measure()
    CTX["parts"][0][3].set("A1", "60 mm")
    for doc, *_ in CTX["parts"]:
        doc.recompute()
        healthy(doc)
    CTX["assembly_doc"].recompute()
    data["solve_return"] = repr(CTX["assembly"].solve())
    assert data["solve_return"] == "0", data["solve_return"]
    CTX["assembly_doc"].recompute()
    data["after"] = measure()
    close_to(data["after"]["parts"][0]["datum_mm"], [30, 10, 8])
    close_to(data["after"]["world_datums_mm"][0], data["after"]["world_datums_mm"][1])
    close_to(data["after"]["link_placements_mm"][1], [10, 0, 0])
    healthy(CTX["assembly_doc"])


def save_and_reopen(data):
    require("c")
    for doc, *_ in CTX["parts"]:
        doc.recompute()
        doc.save()
    CTX["assembly_doc"].recompute()
    CTX["assembly_doc"].saveAs(str(OUT / "ProbeAssembly.FCStd"))
    (OUT / "expected.json").write_text(json.dumps(measure()), encoding="utf-8")
    env = dict(os.environ, A0_DATUM_PROBE_DIR=str(OUT), A0_DATUM_PROBE_MODE="reopen")
    command = [sys.executable, str(Path(__file__).resolve())]
    data["command"] = command
    completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120)
    data.update(exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    child_path = OUT / "reopen-result.json"
    assert child_path.exists(), "Child did not write result JSON"
    child = json.loads(child_path.read_text(encoding="utf-8"))
    data["child_result"] = child
    assert child["pid"] != os.getpid()
    assert completed.returncode == 0
    status = child["stages"]["f"]["status"]
    if status == "unsupported":
        raise Unsupported("Child requires GUI; see child_result")
    if status == "unknown":
        raise Unknown("Child could not verify complete path; see child_result")
    assert status == "pass", "Child measurement failed; see child_result"


def reopen(data):
    # Import installed proxy classes before restoring FeaturePython objects.
    import JointObject
    CTX["parts"] = []
    for index in (1, 2):
        doc = App.openDocument(str(OUT / ("ProbePart" + str(index) + ".FCStd")))
        CTX["parts"].append((doc, doc.Part, doc.Body, doc.Dimensions, doc.Hole))
    doc = App.openDocument(str(OUT / "ProbeAssembly.FCStd"))
    CTX["assembly_doc"] = doc
    CTX["links"] = [doc.Link1, doc.Link2]
    for source, *_ in CTX["parts"]:
        source.recompute(None, True, True)
        healthy(source)
    doc.recompute(None, True, True)
    data["measurement"] = measure()
    expected = json.loads((OUT / "expected.json").read_text(encoding="utf-8"))
    for actual, saved in zip(data["measurement"]["parts"], expected["parts"]):
        close_to(actual["datum_mm"], saved["datum_mm"])
        close_to([actual["length_mm"], actual["volume_mm3"]], [saved["length_mm"], saved["volume_mm3"]])
    for actual, saved in zip(data["measurement"]["world_datums_mm"], expected["world_datums_mm"]):
        close_to(actual, saved)
    for link, (source, part, *_) in zip(CTX["links"], CTX["parts"]):
        assert link.LinkedObject == part
    assembly = doc.getObject("Assembly")
    joint = doc.getObject("FixedJoint")
    if not assembly or not joint or not joint.Reference1 or not joint.Reference2:
        raise Unknown("Documents/links reopened, but complete joint reference path is absent")
    data["solve_return"] = repr(assembly.solve())
    assert data["solve_return"] == "0", data["solve_return"]
    doc.recompute()
    healthy(doc)
    data["after_solve"] = measure()
    for actual, saved in zip(data["after_solve"]["world_datums_mm"], expected["world_datums_mm"]):
        close_to(actual, saved)
    close_to(data["after_solve"]["world_datums_mm"][0], data["after_solve"]["world_datums_mm"][1])


if RESULT["mode"] == "reopen":
    stage("f", reopen)
else:
    for key, action in (("a", create_parts), ("b", create_datums), ("c", create_links),
                        ("d", create_joint), ("e", change_and_solve), ("f", save_and_reopen)):
        stage(key, action)
filename = "reopen-result.json" if RESULT["mode"] == "reopen" else "result.json"
(OUT / filename).write_text(json.dumps(RESULT, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print("A0_DATUM_RESULT " + json.dumps(RESULT, ensure_ascii=True), flush=True)
