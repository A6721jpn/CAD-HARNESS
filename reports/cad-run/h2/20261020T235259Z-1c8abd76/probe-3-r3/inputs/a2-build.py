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

    def one_sided(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False

    base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base, 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Type = 0
    pad.Length = 20.0
    one_sided(pad)
    doc.recompute()

    if pad.Shape.isNull() or len(pad.Shape.Solids) != 1:
        raise RuntimeError("Pad did not produce a single solid.")

    tolerance = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20.0) < tolerance
        and abs(face.BoundBox.ZMax - 20.0) < tolerance
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Could not identify the pad top face.")

    opening = body.newObject("Sketcher::SketchObject", "PocketSketch")
    support = (pad, [top_faces[0]])
    if "AttachmentSupport" in opening.PropertiesList:
        opening.AttachmentSupport = support
    else:
        opening.Support = support
    opening.MapMode = "FlatFace"
    doc.recompute()

    # Keep the attached sketch aligned with the document X and Y axes.
    target = App.Placement(App.Vector(0, 0, 20), App.Rotation())
    opening.AttachmentOffset = opening.Placement.inverse().multiply(target)
    rectangle(opening, 20.0, 15.0)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = opening
    pocket.Type = 0
    pocket.Length = 5.0
    one_sided(pocket)
    pocket.TaperAngle = 0.0
    doc.recompute()

    if pocket.Shape.isNull() or len(pocket.Shape.Solids) != 1:
        raise RuntimeError("Pocket did not produce a single solid.")

    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(abs(getattr(point, axis) - value) < tolerance for point in points)
            for axis, value in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        ):
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Could not identify the four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "TopOuterFillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3.0
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("Fillet did not produce a valid single solid.")

    base.Visibility = False
    pad.Visibility = False
    opening.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    body.Tip = fillet
    return body
