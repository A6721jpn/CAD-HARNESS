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
                Sketcher.Constraint("Horizontal" if i % 2 == 0 else "Vertical", i)
            )
        sketch.addConstraint(Sketcher.Constraint("Distance", 0, width))
        sketch.addConstraint(Sketcher.Constraint("Distance", 1, depth))
        sketch.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, -width / 2))
        sketch.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, -depth / 2))
        return sketch

    base_sketch = rectangle("BaseSketch", 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = "Length"
    pad.Length = 20.0
    pad.SideType = "One side"
    pad.Reversed = False
    doc.recompute()

    if pad.Shape.isNull():
        raise RuntimeError("Pad creation failed.")

    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20.0) < 1e-7
        and abs(face.BoundBox.ZMax - 20.0) < 1e-7
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face.")

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0)
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = "Length"
    pocket.Length = 5.0
    pocket.SideType = "One side"
    pocket.Reversed = False
    pocket.TaperAngle = 0.0
    doc.recompute()

    if pocket.Shape.isNull() or not pocket.Shape.isValid():
        raise RuntimeError("Pocket creation failed.")

    outer_top_edges = []
    tolerance = 1e-7
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance for point in points)
            for axis, value in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        ):
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3.0
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Fillet creation failed.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected a single solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    body.Tip = fillet
    fillet.Visibility = True
    doc.recompute()
    return body
