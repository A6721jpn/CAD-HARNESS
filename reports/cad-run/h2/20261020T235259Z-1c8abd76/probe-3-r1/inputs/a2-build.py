def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def add_rectangle(sketch, width, depth, z):
        inverse = sketch.Placement.inverse()
        points = [
            inverse.multVec(App.Vector(x, y, z))
            for x, y in (
                (-width / 2, -depth / 2),
                (width / 2, -depth / 2),
                (width / 2, depth / 2),
                (-width / 2, depth / 2),
            )
        ]
        for i in range(4):
            a, b = points[i], points[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a.x, a.y, 0),
                    App.Vector(b.x, b.y, 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))

    base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    add_rectangle(base, 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Type = 0
    pad.Length = 20
    pad.SideType = "One side"
    pad.Reversed = False
    doc.recompute()

    if pad.Shape.isNull() or not pad.Shape.isValid():
        raise RuntimeError("Pad creation failed.")

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20) < tolerance
        and abs(face.BoundBox.ZMax - 20) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    add_rectangle(pocket_sketch, 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = 0
    pocket.Length = 5
    pocket.SideType = "One side"
    pocket.Reversed = False
    pocket.TaperAngle = 0
    doc.recompute()

    if pocket.Shape.isNull() or not pocket.Shape.isValid():
        raise RuntimeError("Pocket creation failed.")

    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance for point in points)
            for axis, value in (
                ("x", -20),
                ("x", 20),
                ("y", -15),
                ("y", 15),
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Fillet creation failed.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected one final solid.")

    base.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True

    return body
