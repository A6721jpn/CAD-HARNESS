def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def add_rectangle(sketch, width, depth, world_z):
        doc.recompute()
        inverse = sketch.Placement.inverse()
        corners = [
            inverse.multVec(App.Vector(x, y, world_z))
            for x, y in [
                (-width / 2, -depth / 2),
                (width / 2, -depth / 2),
                (width / 2, depth / 2),
                (-width / 2, depth / 2),
            ]
        ]
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a.x, a.y, 0),
                    App.Vector(b.x, b.y, 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    add_rectangle(base_sketch, 40, 30, 0)
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

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    add_rectangle(pocket_sketch, 20, 15, 20)
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

    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance for point in points)
            for axis, value in [
                ("x", -20), ("x", 20), ("y", -15), ("y", 15)
            ]
        ):
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("The final feature must be one valid solid.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
