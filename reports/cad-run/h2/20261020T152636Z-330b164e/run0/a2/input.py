def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def add_rectangle(sketch, width, depth):
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

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    add_rectangle(base_sketch, 40, 30)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20
    pad.SideType = "One side"
    pad.Reversed = False
    pad.TaperAngle = 0
    doc.recompute()

    if pad.Shape.isNull():
        raise RuntimeError("Pad failed.")

    tolerance = 1e-7
    top_faces = [
        index
        for index, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20) < tolerance
        and abs(face.BoundBox.ZMax - 20) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.AttachmentSupport = (
        pad, ["Face{}".format(top_faces[0])]
    )
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    desired_placement = App.Placement(
        App.Vector(0, 0, 20), App.Rotation()
    )
    pocket_sketch.AttachmentOffset = (
        pocket_sketch.Placement.inverse().multiply(desired_placement)
    )
    add_rectangle(pocket_sketch, 20, 15)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Type = 0
    pocket.Length = 5
    pocket.SideType = "One side"
    pocket.Reversed = False
    pocket.TaperAngle = 0
    doc.recompute()

    if pocket.Shape.isNull() or len(pocket.Shape.Solids) != 1:
        raise RuntimeError("Pocket failed.")

    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance
                for point in points)
            for axis, value in (
                ("x", -20), ("x", 20), ("y", -15), ("y", 15)
            )
        ):
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

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
        raise RuntimeError("Expected a valid single solid after filleting.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
