def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth):
        sketch = body.newObject("Sketcher::SketchObject", name)
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
        return sketch

    def one_sided(feature, length):
        feature.Type = 0
        feature.Length = length
        feature.Reversed = False
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False

    base_sketch = rectangle("BaseSketch", 40, 30)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    one_sided(pad, 20)
    doc.recompute()

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(index)
        for index, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20) < tolerance
        and abs(face.BoundBox.ZMax - 20) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face on the pad.")

    pocket_sketch = rectangle("PocketSketch", 20, 15)
    support_property = (
        "AttachmentSupport"
        if "AttachmentSupport" in pocket_sketch.PropertiesList
        else "Support"
    )
    setattr(pocket_sketch, support_property, (pad, top_faces))
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    desired_placement = App.Placement(
        App.Vector(0, 0, 20), App.Rotation()
    )
    pocket_sketch.AttachmentOffset = (
        pocket_sketch.Placement.inverse().multiply(desired_placement)
    )
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    one_sided(pocket, 5)
    pocket.TaperAngle = 0
    doc.recompute()

    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in points):
            continue
        on_x_boundary = any(
            all(abs(point.x - x) < tolerance for point in points)
            for x in (-20, 20)
        )
        on_y_boundary = any(
            all(abs(point.y - y) < tolerance for point in points)
            for y in (-15, 15)
        )
        if on_x_boundary or on_y_boundary:
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("Expected one valid solid after filleting.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
