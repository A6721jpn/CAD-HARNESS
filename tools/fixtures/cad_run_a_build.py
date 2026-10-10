"""run05 construction adapted to build(doc); never writes original evidence.

Copy sha256 is recorded by cad_run in result.json. SOURCE_SHA256 hashes the
original bytes, not a normalized source. The bad smoke can export
build_without_fillet as build in a new input copy.
"""
SOURCE = "reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run05-script.py"
SOURCE_SHA256 = "55cb67233f611a806dc8d518a72c3a85a1219172d9d2584b35a7f0c189d1706b"
CONTRACT_CHANGES = (
    "Removed original try/except, self-checks, measurements and JSON/PID writes.",
    "Removed evidence path constants, saveAs, closeDocument and newDocument.",
    "The fixed worker owns document creation, probe, saving and close.",
    "Removed selected_geometry reporting only; native edge selection is unchanged.",
    "build_without_fillet omits Fillet and returns a Body whose Tip is Pocket.",
)
TOL = 1.0e-6


def close(a, b):
    return abs(a - b) < TOL


def rectangle(sketch, half_x, half_y, world_z):
    import FreeCAD as App
    import Part
    import Sketcher
    inverse = sketch.Placement.inverse()
    world = [App.Vector(-half_x, -half_y, world_z),
             App.Vector(half_x, -half_y, world_z),
             App.Vector(half_x, half_y, world_z),
             App.Vector(-half_x, half_y, world_z)]
    local = [inverse.multVec(point) for point in world]
    indices = sketch.addGeometry(
        [Part.LineSegment(local[i], local[(i + 1) % 4]) for i in range(4)], False)
    for index in indices:
        sketch.addConstraint(Sketcher.Constraint("Block", index))


def planar_at(face, z):
    import Part
    return isinstance(face.Surface, Part.Plane) and all(close(v.Point.z, z) for v in face.Vertexes)


def outer_top(edge):
    points = [v.Point for v in edge.Vertexes]
    if len(points) != 2 or not all(close(p.z, 20.0) for p in points):
        return False
    return (all(close(p.x, -20.0) for p in points) or
            all(close(p.x, 20.0) for p in points) or
            all(close(p.y, -15.0) for p in points) or
            all(close(p.y, 15.0) for p in points))


def _build(doc, with_fillet):
    body = doc.addObject("PartDesign::Body", "Body")
    base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    base.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    base.MapMode = "FlatFace"
    doc.recompute()
    rectangle(base, 20.0, 15.0, 0.0)
    doc.recompute()
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Length = 20.0
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    doc.recompute()
    if pad.Shape.isNull():
        raise RuntimeError("Pad produced no native shape")
    top = [i for i, face in enumerate(pad.Shape.Faces, 1) if planar_at(face, 20.0)]
    if len(top) != 1:
        raise RuntimeError("Pad top face was not unique")
    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.AttachmentSupport = (pad, ["Face%d" % top[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    rectangle(pocket_sketch, 10.0, 7.5, 20.0)
    doc.recompute()
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5.0
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    doc.recompute()
    if pocket.Shape.isNull():
        raise RuntimeError("Pocket produced no native shape")
    if not with_fillet:
        body.Tip = pocket
        doc.recompute()
        return body
    selected = ["Edge%d" % i for i, edge in enumerate(pocket.Shape.Edges, 1) if outer_top(edge)]
    if len(selected) != 4:
        raise RuntimeError("Expected four outer top edges, got %r" % selected)
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, selected)
    fillet.Radius = 3.0
    doc.recompute()
    if fillet.Shape.isNull():
        raise RuntimeError("Fillet produced no native shape")
    body.Tip = fillet
    return body


def build(doc):
    return _build(doc, True)


def build_without_fillet(doc):
    return _build(doc, False)
