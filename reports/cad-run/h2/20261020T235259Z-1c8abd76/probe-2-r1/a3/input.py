def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, height):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(
            App.Vector(0, 0, height), App.Rotation()
        )
        vertices = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a = vertices[i]
            b = vertices[(i + 1) % 4]
            index = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", index))
        doc.recompute()
        return sketch

    base_sketch = rectangle("BaseSketch", 40, 30, 0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20
    pad.Midplane = False
    pad.Reversed = False
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20, 15, 20)
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5
    pocket.Midplane = False
    pocket.Reversed = False
    pocket.TaperAngle = 0
    doc.recompute()

    tolerance = 1e-6
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        bounds = edge.BoundBox
        on_top = (
            abs(bounds.ZMin - 20) < tolerance
            and abs(bounds.ZMax - 20) < tolerance
        )
        on_boundary = any(
            abs(low - value) < tolerance
            and abs(high - value) < tolerance
            for low, high, value in (
                (bounds.XMin, bounds.XMax, -20),
                (bounds.XMin, bounds.XMax, 20),
                (bounds.YMin, bounds.YMax, -15),
                (bounds.YMin, bounds.YMax, 15),
            )
        )
        if on_top and on_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected exactly four exterior top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("Invalid final geometry.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected one solid.")

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
