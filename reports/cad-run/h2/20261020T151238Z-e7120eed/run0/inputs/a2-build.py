def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, z):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(App.Vector(0, 0, z), App.Rotation())
        points = [
            App.Vector(-width / 2, -depth / 2, 0),
            App.Vector(width / 2, -depth / 2, 0),
            App.Vector(width / 2, depth / 2, 0),
            App.Vector(-width / 2, depth / 2, 0),
        ]
        for i in range(4):
            sketch.addGeometry(
                Part.LineSegment(points[i], points[(i + 1) % 4]), False
            )
        for i in range(4):
            sketch.addConstraint(
                Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1)
            )
            sketch.addConstraint(
                Sketcher.Constraint("Horizontal" if i % 2 == 0 else "Vertical", i)
            )
        sketch.addConstraint(Sketcher.Constraint("Distance", 0, width))
        sketch.addConstraint(Sketcher.Constraint("Distance", 1, depth))
        sketch.addConstraint(
            Sketcher.Constraint("DistanceX", 0, 1, -width / 2)
        )
        sketch.addConstraint(
            Sketcher.Constraint("DistanceY", 0, 1, -depth / 2)
        )
        doc.recompute()
        return sketch

    def one_side(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False

    base_sketch = rectangle("BaseSketch", 40.0, 30.0, 0.0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    one_side(pad)
    body.Tip = pad
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0, 20.0)
    body.Tip = pad
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5.0
    pocket.TaperAngle = 0.0
    one_side(pocket)
    body.Tip = pocket
    doc.recompute()

    if pocket.Shape.isNull() or not pocket.Shape.isValid():
        raise RuntimeError("Pocket did not produce a valid shape.")

    tolerance = 1e-7
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance for point in points)
            for axis, value in (
                ("x", -20.0), ("x", 20.0),
                ("y", -15.0), ("y", 15.0),
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Fillet did not produce a valid shape.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected exactly one solid.")

    for obj in (base_sketch, pad, pocket_sketch, pocket):
        obj.Visibility = False
    fillet.Visibility = True
    return body
