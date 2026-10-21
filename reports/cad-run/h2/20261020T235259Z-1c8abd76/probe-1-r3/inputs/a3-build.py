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

    def require(condition, message):
        if not condition:
            raise RuntimeError(message)

    base_sketch = rectangle("BaseSketch", 40.0, 30.0, 0.0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    pad.Midplane = False
    pad.Reversed = False
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0, 20.0)
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5.0
    pocket.Midplane = False
    pocket.Reversed = False
    pocket.TaperAngle = 0.0
    doc.recompute()

    require(not pocket.Shape.isNull(), "Pocket has no shape.")
    require(len(pocket.Shape.Solids) == 1, "Pocket must produce one solid.")

    tolerance = 1e-6
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        on_outer_boundary = any(
            all(abs(getattr(point, axis) - value) < tolerance
                for point in points)
            for axis, value in (
                ("x", -20.0), ("x", 20.0),
                ("y", -15.0), ("y", 15.0),
            )
        )
        if on_outer_boundary:
            outer_edges.append("Edge{}".format(index))

    require(len(outer_edges) == 4, "Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    require(pad.Profile == base_sketch, "Invalid Pad profile link.")
    require(pocket.Profile == pocket_sketch, "Invalid Pocket profile link.")
    require(pocket.BaseFeature == pad, "Invalid Pocket predecessor.")
    require(fillet.Base[0] == pocket, "Invalid Fillet base link.")
    require(fillet.BaseFeature == pocket, "Invalid Fillet predecessor.")
    require(body.Tip == fillet, "Invalid Body tip.")

    for feature in (base_sketch, pad, pocket_sketch, pocket, fillet):
        require(feature in body.Group, "Feature is outside the Body.")

    for feature in (pad, pocket, fillet):
        require(not feature.Shape.isNull(), "Feature has no shape.")
        require(feature.Shape.isValid(), "Feature shape is invalid.")
        require(len(feature.Shape.Solids) == 1, "Expected one solid.")

    require(len(body.Shape.Solids) == 1, "Body must contain one solid.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
