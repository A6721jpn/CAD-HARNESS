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

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base_sketch, 40, 30)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    pad.Type = 0
    pad.Reversed = False
    doc.recompute()
    base_sketch.Visibility = False

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.Placement = App.Placement(
        App.Vector(0, 0, 20), App.Rotation()
    )
    rectangle(pocket_sketch, 20, 15)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5
    pocket.Type = 0
    pocket.Reversed = False
    pocket.TaperAngle = 0
    doc.recompute()
    pad.Visibility = False
    pocket_sketch.Visibility = False

    outer_edges = []
    tolerance = 1e-7
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [vertex.Point for vertex in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in vertices):
            continue
        on_x_boundary = all(
            abs(abs(point.x) - 20) < tolerance for point in vertices
        ) and abs(vertices[0].x - vertices[1].x) < tolerance
        on_y_boundary = all(
            abs(abs(point.y) - 15) < tolerance for point in vertices
        ) and abs(vertices[0].y - vertices[1].y) < tolerance
        if on_x_boundary or on_y_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()
    pocket.Visibility = False
    fillet.Visibility = True

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Invalid fillet geometry.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected one solid.")

    return body
