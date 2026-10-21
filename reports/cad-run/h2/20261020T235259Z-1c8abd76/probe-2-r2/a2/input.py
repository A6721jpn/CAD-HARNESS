def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(sketch, width, depth, z):
        inverse = sketch.Placement.inverse()
        points = [
            inverse.multVec(App.Vector(x, y, z))
            for x, y in (
                (-width / 2, -depth / 2),
                (width / 2, -depth / 2),
                (width / 2, depth / 2),
                (-width / 2, depth / 2),
            )
        ]
        for i in range(4):
            index = sketch.addGeometry(
                Part.LineSegment(points[i], points[(i + 1) % 4]), False
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base_sketch, 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    body.Tip = pad
    doc.recompute()

    top_faces = []
    for index, face in enumerate(pad.Shape.Faces, 1):
        if all(abs(v.Point.z - 20) < 1e-7 for v in face.Vertexes):
            top_faces.append("Face{}".format(index))
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    rectangle(pocket_sketch, 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Length = 5
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    pocket.TaperAngle = 0
    body.Tip = pocket
    doc.recompute()

    outer_edges = []
    tolerance = 1e-7
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in points):
            continue
        on_x_boundary = (
            all(abs(abs(point.x) - 20) < tolerance for point in points)
            and abs(points[0].x - points[1].x) < tolerance
        )
        on_y_boundary = (
            all(abs(abs(point.y) - 15) < tolerance for point in points)
            and abs(points[0].y - points[1].y) < tolerance
        )
        if on_x_boundary or on_y_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Invalid fillet geometry.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected one solid.")

    return body
