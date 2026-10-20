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
        doc.recompute()
        return sketch

    def single_sided(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False

    def check_solid(feature):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError("Expected one valid solid: " + feature.Name)

    base_sketch = rectangle("BaseSketch", 40.0, 30.0, 0.0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    single_sided(pad)
    pad.TaperAngle = 0.0
    doc.recompute()
    check_solid(pad)

    # Preserve normal Body insertion order so PartDesign manages predecessors.
    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0, 20.0)
    pocket_sketch.setExpression("Placement.Base.z", "Pad.Length")
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = 0
    pocket.Length = 5.0
    single_sided(pocket)
    pocket.TaperAngle = 0.0
    doc.recompute()
    check_solid(pocket)

    tolerance = 1e-7
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
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        )
        if on_outer_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()
    check_solid(fillet)

    history = (
        (base_sketch, "Sketcher::SketchObject"),
        (pad, "PartDesign::Pad"),
        (pocket_sketch, "Sketcher::SketchObject"),
        (pocket, "PartDesign::Pocket"),
        (fillet, "PartDesign::Fillet"),
    )
    for feature, expected_type in history:
        if feature.TypeId != expected_type or feature not in body.Group:
            raise RuntimeError("Incorrect feature history: " + feature.Name)

    if pad.Profile != base_sketch or pocket.Profile != pocket_sketch:
        raise RuntimeError("Incorrect profile reference.")
    if pocket.BaseFeature != pad or fillet.BaseFeature != pocket:
        raise RuntimeError("Incorrect PartDesign predecessor.")
    if fillet.Base[0] != pocket or set(fillet.Base[1]) != set(outer_edges):
        raise RuntimeError("Incorrect fillet references.")
    if body.Tip != fillet:
        raise RuntimeError("Incorrect Body tip.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
