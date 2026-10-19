"""Deterministic native PartDesign history for the A1 two-hole PlateSpec.

Run inside FreeCAD's Python interpreter. Inputs are validated before creating a
document. Subsequent native spreadsheet edits are ordinary FreeCAD operations;
callers must validate their edited specification before publishing a result.
"""
import FreeCAD as App
import Part
import Sketcher

from schemas import validate


CELLS = {"L": "B1", "W": "B2", "T": "B3", "D": "B4", "e": "B5"}
ALIASES = {"L": "plate_length", "W": "plate_width", "T": "plate_thickness",
           "D": "hole_diameter", "e": "edge_offset"}


def _dimension(sketch, constraint, name, expression):
    index = sketch.addConstraint(constraint)
    sketch.renameConstraint(index, name)
    sketch.setExpression("Constraints." + name, expression)


def _xy_sketch(body, name):
    sketch = body.newObject("Sketcher::SketchObject", name)
    xy_plane = next(feature for feature in body.Origin.OriginFeatures if feature.Name == "XY_Plane")
    sketch.AttachmentSupport = (xy_plane, [""])
    sketch.MapMode = "FlatFace"
    return sketch


def compile_plate(spec, document_name="Plate"):
    """Return a new document, with Params -> Sketch/Pad/Sketch/Pocket history."""
    spec = validate("PlateSpec", spec)
    values = {key: float(value[:-3]) for key, value in spec["dimensions"].items()}
    doc = App.newDocument(document_name)
    params = doc.addObject("Spreadsheet::Sheet", "Params")
    for key, cell in CELLS.items():
        params.set("A" + cell[1:], ALIASES[key])
        params.set(cell, spec["dimensions"][key])
        params.setAlias(cell, ALIASES[key])
    params.set("A6", "hole_pitch")
    params.set("B6", "=plate_length - 2 * edge_offset")
    params.setAlias("B6", "hole_pitch")
    doc.recompute()

    body = doc.addObject("PartDesign::Body", "Body")
    body.addProperty("App::PropertyString", "SemanticId").SemanticId = spec["id"]
    for name, sign in (("MountLeft", "-"), ("MountRight", "")):
        mount = body.newObject("PartDesign::CoordinateSystem", name)
        mount.setExpression("Placement.Base.x", sign + "Params.hole_pitch / 2")
        mount.setExpression("Placement.Base.y", "0 mm")
        mount.setExpression("Placement.Base.z", "0 mm")

    length, width = values["L"], values["W"]
    base = _xy_sketch(body, "BaseSketch")
    points = [(-length/2, -width/2), (length/2, -width/2),
              (length/2, width/2), (-length/2, width/2)]
    for index, (x, y) in enumerate(points):
        nx, ny = points[(index + 1) % 4]
        base.addGeometry(Part.LineSegment(App.Vector(x, y, 0), App.Vector(nx, ny, 0)), False)
    for index in range(4):
        base.addConstraint(Sketcher.Constraint("Coincident", index, 2, (index + 1) % 4, 1))
        base.addConstraint(Sketcher.Constraint("Horizontal" if index % 2 == 0 else "Vertical", index))
    base.addConstraint(Sketcher.Constraint("Symmetric", 0, 1, 2, 1, -1, 1))
    _dimension(base, Sketcher.Constraint("Distance", 0, length), "PlateLength", "Params.plate_length")
    _dimension(base, Sketcher.Constraint("Distance", 1, width), "PlateWidth", "Params.plate_width")
    doc.recompute()
    pad = body.newObject("PartDesign::Pad", "BasePad")
    pad.Profile = base
    pad.setExpression("Length", "Params.plate_thickness")
    pad.Reversed = False
    doc.recompute()

    holes = _xy_sketch(body, "HoleSketch")
    pitch = length - 2 * values["e"]
    for x in (-pitch/2, pitch/2):
        holes.addGeometry(Part.Circle(App.Vector(x, 0, 0), App.Vector(0, 0, 1), values["D"]/2), False)
    holes.addConstraint(Sketcher.Constraint("Symmetric", 0, 3, 1, 3, -1, 1))
    holes.addConstraint(Sketcher.Constraint("Equal", 0, 1))
    holes.addConstraint(Sketcher.Constraint("DistanceY", 0, 3, 0.0))
    _dimension(holes, Sketcher.Constraint("DistanceX", 0, 3, -pitch/2), "LeftCenterX", "-Params.hole_pitch / 2")
    _dimension(holes, Sketcher.Constraint("Diameter", 0, values["D"]), "HoleDiameter", "Params.hole_diameter")
    doc.recompute()
    pocket = body.newObject("PartDesign::Pocket", "HolesCut")
    pocket.Profile = holes
    pocket.Type = "ThroughAll"
    pocket.Reversed = True  # XY at z=0: remove material in +Z.
    body.Tip = pocket
    doc.recompute()
    for sketch in (base, holes):
        if sketch.solve() != 0 or not sketch.FullyConstrained:
            raise RuntimeError(sketch.Name + ": expected fully constrained sketch")
    for obj in (base, pad, holes, pocket):
        if "Invalid" in obj.State or "Error" in obj.State:
            raise RuntimeError(obj.Name + ": " + obj.getStatusString())
    if pocket.Shape.isNull() or not pocket.Shape.isValid():
        raise RuntimeError("Pocket did not produce a valid shape")
    return doc
