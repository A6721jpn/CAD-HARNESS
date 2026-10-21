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

    base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base, 40.0, 30.0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Length = 20.0
    pad.Type = 0
    pad.Reversed = False
    pad.Midplane = False
    doc.recompute()
    base.Visibility = False

    opening = body.newObject("Sketcher::SketchObject", "PocketSketch")
    opening.Placement = App.Placement(
        App.Vector(0, 0, 20), App.Rotation()
    )
    rectangle(opening, 20.0, 15.0)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = opening
    pocket.Length = 5.0
    pocket.Type = 0
    pocket.Reversed = False
    pocket.Midplane = False
    pocket.TaperAngle = 0.0
    doc.recompute()
    opening.Visibility = False
    pad.Visibility = False

    tolerance = 1e-7
    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [vertex.Point for vertex in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in vertices):
            continue
        on_outer_boundary = any(
            all(abs(getattr(point, axis) - value) < tolerance
                for point in vertices)
            for axis, value in (
                ("x", -20.0), ("x", 20.0),
                ("y", -15.0), ("y", 15.0),
            )
        )
        if on_outer_boundary:
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Could not identify the four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "TopOuterFillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3.0
    doc.recompute()

    if fillet.Shape.isNull() or len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Fillet did not produce a single solid.")

    pocket.Visibility = False
    fillet.Visibility = True
    body.Tip = fillet
    return body
