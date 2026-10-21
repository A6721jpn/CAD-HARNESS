def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(sketch, width, depth):
        points = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a = points[i]
            b = points[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base_sketch, 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20.0
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    body.Tip = pad
    doc.recompute()

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(index)
        for index, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20.0) < tolerance
        and abs(face.BoundBox.ZMax - 20.0) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Could not identify the pad's top face.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    if "AttachmentSupport" in pocket_sketch.PropertiesList:
        pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    else:
        pocket_sketch.Support = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    rectangle(pocket_sketch, 20.0, 15.0)
    doc.recompute()

    body.Tip = pad
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Length = 5.0
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    pocket.TaperAngle = 0.0
    body.Tip = pocket
    doc.recompute()

    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(
                abs(getattr(point, axis) - value) < tolerance
                for point in points
            )
            for axis, value in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Could not identify the four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("The final fillet geometry is invalid.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("The final body must contain exactly one solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
