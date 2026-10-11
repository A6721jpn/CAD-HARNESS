"""Task B PartDesign fixture. The negative fixture only omits the final Chamfer."""
def rectangle(sketch, x, y, z):
    import FreeCAD as App
    import Part
    import Sketcher
    inverse = sketch.Placement.inverse()
    corners = [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    for index, point in enumerate(corners):
        first = inverse.multVec(App.Vector(*point))
        second = inverse.multVec(App.Vector(*corners[(index + 1) % 4]))
        geometry = sketch.addGeometry(Part.LineSegment(first, second), False)
        sketch.addConstraint(Sketcher.Constraint("Block", geometry))


def top_face(feature):
    import Part
    selected = [index + 1 for index, face in enumerate(feature.Shape.Faces)
                if isinstance(face.Surface, Part.Plane)
                and abs(face.normalAt(0, 0).z) > 1 - 1e-6
                and all(abs(v.Point.z - 10) < 1e-6 for v in face.Vertexes)]
    if len(selected) != 1:
        raise ValueError("unique_top_face_required")
    return "Face%d" % selected[0]


def _build(doc, with_chamfer):
    import FreeCAD as App
    import Part
    import Sketcher
    body = doc.addObject("PartDesign::Body", "Plate")
    base = body.newObject("Sketcher::SketchObject", "PlateProfile")
    base.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    base.MapMode = "FlatFace"
    doc.recompute()
    rectangle(base, 40, 30, 0)
    pad = body.newObject("PartDesign::Pad", "PlatePad")
    pad.Profile = base
    pad.Length = 10
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    doc.recompute()
    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketProfile")
    pocket_sketch.AttachmentSupport = (pad, [top_face(pad)])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    rectangle(pocket_sketch, 15, 10, 10)
    pocket = body.newObject("PartDesign::Pocket", "CentralPocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 4
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    doc.recompute()
    hole_sketch = body.newObject("Sketcher::SketchObject", "HoleProfile")
    hole_sketch.AttachmentSupport = (pocket, [top_face(pocket)])
    hole_sketch.MapMode = "FlatFace"
    doc.recompute()
    center = hole_sketch.Placement.inverse().multVec(App.Vector(-20, -20, 10))
    geometry = hole_sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), 3), False)
    hole_sketch.addConstraint(Sketcher.Constraint("Block", geometry))
    hole = body.newObject("PartDesign::Pocket", "ThroughHole")
    hole.Profile = hole_sketch
    hole.Length = 10
    hole.Type = 0
    hole.Reversed = False
    hole.Midplane = False
    doc.recompute()
    pattern = body.newObject("PartDesign::LinearPattern", "HolePattern")
    pattern.Originals = [hole]
    pattern.Direction = (doc.getObject("X_Axis"), [""])
    pattern.Length = 40
    pattern.Occurrences = 3
    pattern.Reversed = False
    doc.recompute()
    body.Tip = pattern
    if not with_chamfer:
        return body
    edges = []
    for index, edge in enumerate(pattern.Shape.Edges):
        points = [v.Point for v in edge.Vertexes]
        if not isinstance(edge.Curve, Part.Line) or len(points) != 2:
            continue
        if not all(abs(p.z - 10) < 1e-6 for p in points):
            continue
        if (all(abs(p.x - 40) < 1e-6 for p in points)
                or all(abs(p.x + 40) < 1e-6 for p in points)
                or all(abs(p.y - 30) < 1e-6 for p in points)
                or all(abs(p.y + 30) < 1e-6 for p in points)):
            edges.append("Edge%d" % (index + 1))
    if len(edges) != 4:
        raise ValueError("outer_four_edges_required")
    chamfer = body.newObject("PartDesign::Chamfer", "OuterChamfer")
    chamfer.Base = (pattern, edges)
    chamfer.Size = 1
    doc.recompute()
    body.Tip = chamfer
    return body


def build(doc):
    return _build(doc, True)


def build_without_chamfer(doc):
    return _build(doc, False)
