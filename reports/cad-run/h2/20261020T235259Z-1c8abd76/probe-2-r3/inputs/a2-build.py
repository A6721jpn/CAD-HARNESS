def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(sketch, width, depth):
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

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base_sketch, 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20.0
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    body.Tip = pad
    doc.recompute()

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.Placement = App.Placement(
        App.Vector(0, 0, 20.0), App.Rotation()
    )
    rectangle(pocket_sketch, 20.0, 15.0)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Length = 5.0
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    pocket.TaperAngle = 0.0
    body.Tip = pocket
    doc.recompute()

    tolerance = 1e-7
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [vertex.Point for vertex in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in vertices):
            continue
        if any(
            all(
                abs(getattr(point, axis) - value) < tolerance
                for point in vertices
            )
            for axis, value in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Could not identify the four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("The final fillet geometry is invalid.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("The final body must contain exactly one solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
