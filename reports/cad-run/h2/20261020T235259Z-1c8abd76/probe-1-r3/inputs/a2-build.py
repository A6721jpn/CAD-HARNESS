def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, height):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(
            App.Vector(0, 0, height), App.Rotation()
        )
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
        return sketch

    def one_side(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False

    base_sketch = rectangle("BaseSketch", 40.0, 30.0, 0.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    one_side(pad)
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0, 20.0)
    doc.recompute()
    body.Tip = pad

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = 0
    pocket.Length = 5.0
    one_side(pocket)
    pocket.TaperAngle = 0.0
    doc.recompute()

    if pocket.Shape.isNull() or len(pocket.Shape.Solids) != 1:
        raise RuntimeError("Pocket did not produce one solid.")

    outer_edges = []
    tolerance = 1e-6
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance
                for point in points)
            for axis, value in (
                ("x", -20.0), ("x", 20.0),
                ("y", -15.0), ("y", 15.0),
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    body.Tip = pocket
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    def require(condition, message):
        if not condition:
            raise RuntimeError(message)

    require(pad.Profile == base_sketch, "Disconnected pad profile.")
    require(pocket.Profile == pocket_sketch, "Disconnected pocket profile.")
    require(pocket.BaseFeature == pad, "Disconnected pocket predecessor.")
    require(fillet.Base[0] == pocket, "Disconnected fillet base.")
    require(fillet.BaseFeature == pocket, "Disconnected fillet predecessor.")
    require(body.Tip == fillet, "Incorrect Body tip.")

    for feature in (base_sketch, pad, pocket_sketch, pocket, fillet):
        require(feature in body.Group, "Feature outside Body.")

    for feature in (pad, pocket, fillet):
        require(not feature.Shape.isNull(), "Empty feature shape.")
        require(feature.Shape.isValid(), "Invalid feature shape.")
        require(len(feature.Shape.Solids) == 1, "Expected one solid.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
