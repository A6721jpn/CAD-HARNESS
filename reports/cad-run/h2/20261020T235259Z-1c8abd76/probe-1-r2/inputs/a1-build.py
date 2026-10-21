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
        points = [
            App.Vector(-width / 2, -depth / 2, 0),
            App.Vector(width / 2, -depth / 2, 0),
            App.Vector(width / 2, depth / 2, 0),
            App.Vector(-width / 2, depth / 2, 0),
        ]
        for i in range(4):
            index = sketch.addGeometry(
                Part.LineSegment(points[i], points[(i + 1) % 4]), False
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))
        return sketch

    base_sketch = rectangle("BaseSketch", 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    pad.Type = 0
    pad.Reversed = False
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5
    pocket.Type = 0
    pocket.Reversed = False
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

    def linked_object(value):
        return value[0] if isinstance(value, (tuple, list)) else value

    if linked_object(pad.Profile) != base_sketch:
        raise RuntimeError("Invalid Pad profile.")
    if linked_object(pocket.Profile) != pocket_sketch:
        raise RuntimeError("Invalid Pocket profile.")
    if pocket.BaseFeature != pad:
        raise RuntimeError("Pocket must follow Pad.")
    if linked_object(fillet.Base) != pocket:
        raise RuntimeError("Fillet must reference Pocket.")
    if fillet.BaseFeature != pocket or body.Tip != fillet:
        raise RuntimeError("Invalid final feature chain.")

    for feature in (pad, pocket, fillet):
        if (
            feature.Shape.isNull()
            or not feature.Shape.isValid()
            or len(feature.Shape.Solids) != 1
        ):
            raise RuntimeError("Each feature must produce one valid solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
