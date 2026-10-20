def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, z):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(
            App.Vector(0, 0, z), App.Rotation()
        )
        corners = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))
        doc.recompute()
        return sketch

    base_sketch = rectangle("BaseSketch", 40.0, 30.0, 0.0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    pad.Midplane = False
    pad.Reversed = False
    pad.TaperAngle = 0.0
    body.Tip = pad
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0, 20.0)

    # Explicitly retain the preceding solid when inserting the pocket sketch.
    body.Tip = pad
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5.0
    pocket.Midplane = False
    pocket.Reversed = False
    pocket.TaperAngle = 0.0
    body.Tip = pocket
    doc.recompute()

    for feature in (pad, pocket):
        if (
            feature.Shape.isNull()
            or not feature.Shape.isValid()
            or len(feature.Shape.Solids) != 1
        ):
            raise RuntimeError("Invalid solid from " + feature.Name)

    tolerance = 1e-7
    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
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
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.BaseFeature = pocket
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    expected_history = (
        (base_sketch, "Sketcher::SketchObject"),
        (pad, "PartDesign::Pad"),
        (pocket_sketch, "Sketcher::SketchObject"),
        (pocket, "PartDesign::Pocket"),
        (fillet, "PartDesign::Fillet"),
    )
    for feature, expected_type in expected_history:
        if feature.TypeId != expected_type or feature not in body.Group:
            raise RuntimeError("Incorrect feature history: " + feature.Name)

    if pad.Profile != base_sketch or pocket.Profile != pocket_sketch:
        raise RuntimeError("Incorrect profile reference.")
    if pocket.BaseFeature != pad or fillet.BaseFeature != pocket:
        raise RuntimeError("Incorrect solid predecessor.")
    if fillet.Base[0] != pocket or set(fillet.Base[1]) != set(outer_top_edges):
        raise RuntimeError("Incorrect fillet edge references.")
    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
        or body.Tip != fillet
    ):
        raise RuntimeError("Final body must contain one valid solid.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
