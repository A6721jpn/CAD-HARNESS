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
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))
        return sketch

    base_sketch = rectangle("BaseSketch", 40, 30)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20
    pad.SideType = "One side"
    pad.Reversed = False
    body.Tip = pad
    doc.recompute()

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20) < tolerance
        and abs(face.BoundBox.ZMax - 20) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face.")

    pocket_sketch = rectangle("PocketSketch", 20, 15)
    support = (pad, [top_faces[0]])
    if "AttachmentSupport" in pocket_sketch.PropertiesList:
        pocket_sketch.AttachmentSupport = support
    else:
        pocket_sketch.Support = support
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5
    pocket.SideType = "One side"
    pocket.Reversed = False
    pocket.TaperAngle = 0
    body.Tip = pocket
    doc.recompute()

    if pocket.Shape.isNull() or not pocket.Shape.isValid():
        raise RuntimeError("Pocket did not produce valid geometry.")
    if len(pocket.Shape.Solids) != 1:
        raise RuntimeError("Expected one solid after the pocket.")
    if abs(pocket.Shape.Volume - (40 * 30 * 20 - 20 * 15 * 5)) > 1e-5:
        raise RuntimeError("Pocket dimensions or depth are incorrect.")

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
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Fillet did not produce valid geometry.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected a single final solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
