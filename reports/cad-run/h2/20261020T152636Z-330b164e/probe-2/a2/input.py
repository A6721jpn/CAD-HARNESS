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

    def one_side(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False

    base_sketch = rectangle("BaseSketch", 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    one_side(pad)
    body.Tip = pad
    doc.recompute()

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20.0) < tolerance
        and abs(face.BoundBox.ZMax - 20.0) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face.")

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0)
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    desired_placement = App.Placement(
        App.Vector(0, 0, 20.0), App.Rotation()
    )
    pocket_sketch.AttachmentOffset = (
        pocket_sketch.Placement.inverse().multiply(desired_placement)
    )
    doc.recompute()

    body.Tip = pad
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5.0
    one_side(pocket)
    pocket.TaperAngle = 0.0
    body.Tip = pocket
    doc.recompute()

    outer_top_edges = []
    for number, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(
                abs(getattr(point, axis) - coordinate) < tolerance
                for point in points
            )
            for axis, coordinate in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        ):
            outer_top_edges.append("Edge{}".format(number))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3.0
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
