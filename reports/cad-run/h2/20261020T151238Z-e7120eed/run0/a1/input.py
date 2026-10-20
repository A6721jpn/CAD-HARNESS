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
                Sketcher.Constraint(
                    "Horizontal" if i % 2 == 0 else "Vertical", i
                )
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

    base = rectangle_sketch("BaseSketch", 40.0, 30.0, 0.0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Length = 20.0
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    doc.recompute()
    base.Visibility = False

    pocket_sketch = rectangle_sketch("PocketSketch", 20.0, 15.0, 20.0)
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5.0
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    pocket.TaperAngle = 0.0
    doc.recompute()
    pad.Visibility = False
    pocket_sketch.Visibility = False

    tolerance = 1e-7
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [vertex.Point for vertex in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in vertices):
            continue
        on_outer_boundary = any(
            all(abs(getattr(point, axis) - value) < tolerance
                for point in vertices)
            for axis, value in (
                ("x", -20.0), ("x", 20.0),
                ("y", -15.0), ("y", 15.0),
            )
        )
        if on_outer_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3.0
    doc.recompute()
    pocket.Visibility = False
    body.Tip = fillet
    fillet.Visibility = True

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Fillet did not produce a valid shape.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected one solid.")

    return body
