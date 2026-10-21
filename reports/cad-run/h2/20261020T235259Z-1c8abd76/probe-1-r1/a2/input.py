def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, z):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(App.Vector(0, 0, z), App.Rotation())
        corners = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(App.Vector(*a, 0), App.Vector(*b, 0)),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))
        return sketch

    def one_side(feature):
        feature.Type = 0
        feature.Reversed = False
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False

    base_sketch = rectangle("BaseSketch", 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    one_side(pad)
    body.Tip = pad
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20, 15, 20)
    doc.recompute()

    # Restore the solid predecessor after adding the profile sketch.
    body.Tip = pad
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Length = 5
    pocket.TaperAngle = 0
    one_side(pocket)
    body.Tip = pocket
    doc.recompute()

    tolerance = 1e-7
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
        raise RuntimeError("Expected exactly four outer top edges.")

    body.Tip = pocket
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    def profile_of(feature):
        value = feature.Profile
        return value[0] if isinstance(value, (tuple, list)) else value

    if profile_of(pad) != base_sketch:
        raise RuntimeError("Invalid Pad profile link.")
    if profile_of(pocket) != pocket_sketch:
        raise RuntimeError("Invalid Pocket profile link.")
    if pocket.BaseFeature != pad:
        raise RuntimeError("Pocket predecessor must be Pad.")
    if fillet.BaseFeature != pocket or fillet.Base[0] != pocket:
        raise RuntimeError("Fillet predecessor must be Pocket.")
    if set(fillet.Base[1]) != set(outer_edges):
        raise RuntimeError("Invalid Fillet edge selection.")
    if body.Tip != fillet:
        raise RuntimeError("Invalid Body tip.")

    for obj in (base_sketch, pad, pocket_sketch, pocket, fillet):
        if obj not in body.Group:
            raise RuntimeError("Feature is outside the Body: " + obj.Name)

    for feature in (pad, pocket, fillet):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError("Expected one valid solid: " + feature.Name)

    if body.Shape.isNull() or len(body.Shape.Solids) != 1:
        raise RuntimeError("Final Body must contain one solid.")

    for obj in (base_sketch, pad, pocket_sketch, pocket):
        obj.Visibility = False
    fillet.Visibility = True
    return body
