def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def add_rectangle(sketch, width, depth, z):
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
            a, b = points[i], points[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a.x, a.y, 0),
                    App.Vector(b.x, b.y, 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))

    def one_side(feature, length):
        feature.Type = 0
        feature.Length = length
        feature.Reversed = False
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False

    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    add_rectangle(base_sketch, 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    one_side(pad, 20)
    doc.recompute()

    if pad.Shape.isNull() or len(pad.Shape.Solids) != 1:
        raise RuntimeError("Pad did not produce one solid.")

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20) < tolerance
        and abs(face.BoundBox.ZMax - 20) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Could not identify the Pad top face.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    if "AttachmentSupport" in pocket_sketch.PropertiesList:
        pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    else:
        pocket_sketch.Support = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()
    add_rectangle(pocket_sketch, 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    one_side(pocket, 5)
    pocket.TaperAngle = 0
    doc.recompute()

    if pocket.Shape.isNull() or len(pocket.Shape.Solids) != 1:
        raise RuntimeError("Pocket did not produce one solid.")

    outer_edges = []
    for i, edge in enumerate(pocket.Shape.Edges, 1):
        points = [v.Point for v in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(p.z - 20) < tolerance for p in points):
            continue
        if any(
            all(abs(getattr(p, axis) - coordinate) < tolerance for p in points)
            for axis, coordinate in (
                ("x", -20),
                ("x", 20),
                ("y", -15),
                ("y", 15),
            )
        ):
            outer_edges.append("Edge{}".format(i))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four exterior top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    def linked_object(value):
        return value[0] if isinstance(value, (tuple, list)) else value

    support_property = (
        "AttachmentSupport"
        if "AttachmentSupport" in pocket_sketch.PropertiesList
        else "Support"
    )
    support = getattr(pocket_sketch, support_property)

    if linked_object(pad.Profile) != base_sketch:
        raise RuntimeError("Invalid Pad profile.")
    if linked_object(pocket.Profile) != pocket_sketch:
        raise RuntimeError("Invalid Pocket profile.")
    if linked_object(support) != pad:
        raise RuntimeError("Pocket sketch must be attached to Pad.")
    if pocket.BaseFeature != pad:
        raise RuntimeError("Pocket must follow Pad.")
    if fillet.BaseFeature != pocket or fillet.Base[0] != pocket:
        raise RuntimeError("Fillet must follow Pocket.")
    if set(fillet.Base[1]) != set(outer_edges):
        raise RuntimeError("Incorrect Fillet edges.")
    if body.Tip != fillet:
        raise RuntimeError("Incorrect Body tip.")

    for feature in (base_sketch, pad, pocket_sketch, pocket, fillet):
        if feature not in body.Group:
            raise RuntimeError("Feature is outside the Body.")

    for feature in (pad, pocket, fillet):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError("Invalid solid in " + feature.Name)

    if body.Shape.isNull() or len(body.Shape.Solids) != 1:
        raise RuntimeError("Final Body must contain one solid.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
