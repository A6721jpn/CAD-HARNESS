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
    pad.SideType = "One side"
    pad.Reversed = False
    doc.recompute()
    base_sketch.Visibility = False

    pocket_sketch = rectangle_sketch("PocketSketch", 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5
    pocket.Type = 0
    pocket.SideType = "One side"
    pocket.Reversed = False
    pocket.TaperAngle = 0
    doc.recompute()
    pocket_sketch.Visibility = False
    pad.Visibility = False

    tolerance = 1e-7
    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [vertex.Point for vertex in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in vertices):
            continue
        on_outer_boundary = any(
            all(abs(getattr(point, axis) - value) < tolerance
                for point in vertices)
            for axis, value in (
                ("x", -20), ("x", 20), ("y", -15), ("y", 15)
            )
        )
        if on_outer_boundary:
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Fillet did not produce a valid shape.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected a single solid.")

    pocket.Visibility = False
    fillet.Visibility = True
    body.Tip = fillet
    return body
