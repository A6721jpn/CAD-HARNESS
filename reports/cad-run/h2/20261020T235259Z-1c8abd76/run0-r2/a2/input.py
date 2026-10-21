def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth):
        sketch = body.newObject("Sketcher::SketchObject", name)
        points = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a, b = points[i], points[(i + 1) % 4]
            sketch.addGeometry(
                Part.LineSegment(App.Vector(*a, 0), App.Vector(*b, 0)),
                False,
            )
        for i in range(4):
            sketch.addConstraint(
                Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1)
            )
            sketch.addConstraint(
                Sketcher.Constraint(
                    "Horizontal" if i % 2 == 0 else "Vertical", i
                )
            )
        sketch.addConstraint(Sketcher.Constraint("Distance", 0, width))
        sketch.addConstraint(Sketcher.Constraint("Distance", 1, depth))
        sketch.addConstraint(
            Sketcher.Constraint("DistanceX", 0, 1, -width / 2)
        )
        sketch.addConstraint(
            Sketcher.Constraint("DistanceY", 0, 1, -depth / 2)
        )
        return sketch

    base = rectangle("BaseSketch", 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Type = 0
    pad.Length = 20.0
    pad.SideType = "One side"
    pad.Reversed = False
    doc.recompute()

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20.0) < tolerance
        and abs(face.BoundBox.ZMax - 20.0) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Cannot identify the pad top face.")

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0)
    pocket_sketch.AttachmentSupport = (pad, top_faces)
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = 0
    pocket.Length = 5.0
    pocket.SideType = "One side"
    pocket.Reversed = False
    pocket.TaperAngle = 0.0
    doc.recompute()

    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(p.z - 20.0) < tolerance for p in points):
            continue
        if (
            all(abs(p.x - 20.0) < tolerance for p in points)
            or all(abs(p.x + 20.0) < tolerance for p in points)
            or all(abs(p.y - 15.0) < tolerance for p in points)
            or all(abs(p.y + 15.0) < tolerance for p in points)
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("Expected one valid solid after filleting.")

    base.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
