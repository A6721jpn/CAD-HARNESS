def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(sketch, width, depth):
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

    def one_side(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base_sketch, 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20.0
    one_side(pad)
    body.Tip = pad
    doc.recompute()

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20.0) < tolerance
        and abs(face.BoundBox.ZMax - 20.0) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Expected one planar top face on the pad.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    support_property = (
        "AttachmentSupport"
        if "AttachmentSupport" in pocket_sketch.PropertiesList
        else "Support"
    )
    setattr(pocket_sketch, support_property, (pad, top_faces))
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    inverse = pocket_sketch.Placement.inverse()
    world_points = [
        App.Vector(-10.0, -7.5, 20.0),
        App.Vector(10.0, -7.5, 20.0),
        App.Vector(10.0, 7.5, 20.0),
        App.Vector(-10.0, 7.5, 20.0),
    ]
    local_points = [inverse.multVec(point) for point in world_points]
    for i in range(4):
        a = local_points[i]
        b = local_points[(i + 1) % 4]
        index = pocket_sketch.addGeometry(
            Part.LineSegment(
                App.Vector(a.x, a.y, 0),
                App.Vector(b.x, b.y, 0),
            ),
            False,
        )
        pocket_sketch.addConstraint(Sketcher.Constraint("Block", index))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5.0
    pocket.TaperAngle = 0.0
    one_side(pocket)
    body.Tip = pocket
    doc.recompute()

    if pocket.Shape.isNull() or len(pocket.Shape.Solids) != 1:
        raise RuntimeError("Pocket did not produce one solid.")

    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        bounds = edge.BoundBox
        at_top = (
            abs(bounds.ZMin - 20.0) < tolerance
            and abs(bounds.ZMax - 20.0) < tolerance
        )
        on_outer_boundary = any(
            abs(lower - coordinate) < tolerance
            and abs(upper - coordinate) < tolerance
            for lower, upper, coordinate in (
                (bounds.XMin, bounds.XMax, -20.0),
                (bounds.XMin, bounds.XMax, 20.0),
                (bounds.YMin, bounds.YMax, -15.0),
                (bounds.YMin, bounds.YMax, 15.0),
            )
        )
        if at_top and on_outer_boundary:
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("The final feature must be one valid solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
