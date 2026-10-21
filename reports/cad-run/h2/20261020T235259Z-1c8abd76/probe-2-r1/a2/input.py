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

    base_sketch = rectangle("BaseSketch", 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    pad.Type = 0
    pad.Reversed = False
    pad.SideType = "One side"
    body.Tip = pad
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Length = 5
    pocket.Type = 0
    pocket.Reversed = False
    pocket.SideType = "One side"
    pocket.TaperAngle = 0
    body.Tip = pocket
    doc.recompute()

    tolerance = 1e-7
    outer_top_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        bounds = edge.BoundBox
        on_top = (
            abs(bounds.ZMin - 20) < tolerance
            and abs(bounds.ZMax - 20) < tolerance
        )
        on_outer_boundary = (
            (
                abs(bounds.XMin - 20) < tolerance
                and abs(bounds.XMax - 20) < tolerance
            )
            or (
                abs(bounds.XMin + 20) < tolerance
                and abs(bounds.XMax + 20) < tolerance
            )
            or (
                abs(bounds.YMin - 15) < tolerance
                and abs(bounds.YMax - 15) < tolerance
            )
            or (
                abs(bounds.YMin + 15) < tolerance
                and abs(bounds.YMax + 15) < tolerance
            )
        )
        if on_top and on_outer_boundary:
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
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
        raise RuntimeError("The final fillet geometry is invalid.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected a single solid.")
    if pad.Profile != base_sketch or pocket.Profile != pocket_sketch:
        raise RuntimeError("Unexpected profile links.")
    if pocket.BaseFeature != pad or fillet.BaseFeature != pocket:
        raise RuntimeError("Unexpected predecessor links.")
    if body.Tip != fillet:
        raise RuntimeError("Unexpected Body tip.")
    for feature in (base_sketch, pad, pocket_sketch, pocket, fillet):
        if feature not in body.Group:
            raise RuntimeError("Feature is outside the Body.")

    return body
