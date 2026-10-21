def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle_sketch(name, width, depth, z):
        sketch = doc.addObject("Sketcher::SketchObject", name)
        body.addObject(sketch)
        sketch.Placement = App.Placement(
            App.Vector(0, 0, z), App.Rotation()
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

    base_sketch = rectangle_sketch("BaseSketch", 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    pad.Type = 0
    pad.Reversed = False
    if "SideType" in pad.PropertiesList:
        pad.SideType = "One side"
    else:
        pad.Midplane = False
    doc.recompute()

    pocket_sketch = rectangle_sketch("PocketSketch", 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5
    pocket.Type = 0
    pocket.Reversed = False
    if "SideType" in pocket.PropertiesList:
        pocket.SideType = "One side"
    else:
        pocket.Midplane = False
    pocket.TaperAngle = 0
    doc.recompute()

    tolerance = 1e-7
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [vertex.Point for vertex in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in vertices):
            continue
        on_outer_boundary = any(
            all(abs(getattr(point, axis) - coordinate) < tolerance
                for point in vertices)
            for axis, coordinate in (
                ("x", -20), ("x", 20), ("y", -15), ("y", 15)
            )
        )
        if on_outer_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    def profile_object(feature):
        profile = feature.Profile
        return profile[0] if isinstance(profile, (tuple, list)) else profile

    if profile_object(pad) != base_sketch:
        raise RuntimeError("Invalid Pad profile.")
    if profile_object(pocket) != pocket_sketch:
        raise RuntimeError("Invalid Pocket profile.")
    if pocket.BaseFeature != pad:
        raise RuntimeError("Pocket must directly follow Pad.")
    if fillet.Base[0] != pocket:
        raise RuntimeError("Fillet must reference Pocket.")
    if body.Tip != fillet:
        raise RuntimeError("Invalid final Body tip.")

    for feature in (pad, pocket, fillet):
        if feature.Shape.isNull() or not feature.Shape.isValid():
            raise RuntimeError("Invalid shape: " + feature.Name)
        if len(feature.Shape.Solids) != 1:
            raise RuntimeError("Expected one connected solid: " + feature.Name)

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
