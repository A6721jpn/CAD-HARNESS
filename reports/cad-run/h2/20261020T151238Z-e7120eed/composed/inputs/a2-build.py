def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth):
        sketch = body.newObject("Sketcher::SketchObject", name)
        points = [
            App.Vector(-width / 2, -depth / 2, 0),
            App.Vector(width / 2, -depth / 2, 0),
            App.Vector(width / 2, depth / 2, 0),
            App.Vector(-width / 2, depth / 2, 0),
        ]
        for i in range(4):
            index = sketch.addGeometry(
                Part.LineSegment(points[i], points[(i + 1) % 4]), False
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
        raise RuntimeError("Expected one planar top face on the pad.")

    pocket_sketch = rectangle("PocketSketch", 20, 15)
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    # Preserve the specified global rectangle orientation while retaining
    # the explicit attachment dependency on the preceding pad.
    target = App.Placement(App.Vector(0, 0, 20), App.Rotation())
    pocket_sketch.AttachmentOffset = (
        pocket_sketch.Placement.inverse().multiply(target)
    )
    doc.recompute()

    body.Tip = pad
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
                ("x", -20), ("x", 20), ("y", -15), ("y", 15)
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four top outer perimeter edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    for feature in (pad, pocket, fillet):
        if feature.Shape.isNull() or not feature.Shape.isValid():
            raise RuntimeError("Invalid geometry in " + feature.Name)
        if len(feature.Shape.Solids) != 1:
            raise RuntimeError("Expected one solid in " + feature.Name)

    if any(
        obj not in body.Group
        for obj in (base_sketch, pad, pocket_sketch, pocket, fillet)
    ):
        raise RuntimeError("Incomplete Body membership.")
    if pocket.BaseFeature != pad or fillet.BaseFeature != pocket:
        raise RuntimeError("Disconnected PartDesign feature history.")
    if fillet.Base[0] != pocket or body.Tip != fillet:
        raise RuntimeError("Incorrect final feature dependency or Body tip.")

    for obj in (base_sketch, pad, pocket_sketch, pocket):
        obj.Visibility = False
    fillet.Visibility = True
    return body
