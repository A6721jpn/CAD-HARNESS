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
        corners = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))
        return sketch

    base_sketch = rectangle_sketch("BaseSketch", 40.0, 30.0, 0.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    pad.Reversed = False
    pad.Midplane = False
    doc.recompute()
    base_sketch.Visibility = False

    pocket_sketch = rectangle_sketch("PocketSketch", 20.0, 15.0, 20.0)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = 0
    pocket.Length = 5.0
    pocket.Reversed = False
    pocket.Midplane = False
    pocket.TaperAngle = 0.0
    doc.recompute()
    pocket_sketch.Visibility = False
    pad.Visibility = False

    tolerance = 1e-7
    outer_top_edges = []
    for number, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(p.z - 20.0) < tolerance for p in points):
            continue
        on_outer_boundary = any(
            all(abs(getattr(p, axis) - coordinate) < tolerance for p in points)
            for axis, coordinate in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        )
        if on_outer_boundary:
            outer_top_edges.append("Edge{}".format(number))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("The final feature must be one valid solid.")

    pocket.Visibility = False
    fillet.Visibility = True
    return body
