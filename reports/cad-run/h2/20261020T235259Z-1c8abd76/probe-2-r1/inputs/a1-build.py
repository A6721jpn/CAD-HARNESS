def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, z):
        sketch = doc.addObject("Sketcher::SketchObject", name)
        body.addObject(sketch)
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

    base_sketch = rectangle("BaseSketch", 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = 20
    pad.Type = 0
    pad.Reversed = False
    pad.SideType = "One side"
    doc.recompute()
    base_sketch.Visibility = False

    pocket_sketch = rectangle("PocketSketch", 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.Length = 5
    pocket.Type = 0
    pocket.Reversed = False
    pocket.SideType = "One side"
    pocket.TaperAngle = 0
    doc.recompute()
    pocket_sketch.Visibility = False
    pad.Visibility = False

    outer_top_edges = []
    tolerance = 1e-7
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        bounds = edge.BoundBox
        on_top = (
            abs(bounds.ZMin - 20) < tolerance
            and abs(bounds.ZMax - 20) < tolerance
        )
        on_outer_boundary = (
            (abs(bounds.XMin - 20) < tolerance
             and abs(bounds.XMax - 20) < tolerance)
            or (abs(bounds.XMin + 20) < tolerance
                and abs(bounds.XMax + 20) < tolerance)
            or (abs(bounds.YMin - 15) < tolerance
                and abs(bounds.YMax - 15) < tolerance)
            or (abs(bounds.YMin + 15) < tolerance
                and abs(bounds.YMax + 15) < tolerance)
        )
        if on_top and on_outer_boundary:
            outer_top_edges.append("Edge{}".format(index))

    if len(outer_top_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_top_edges)
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()
    pocket.Visibility = False
    fillet.Visibility = True

    if fillet.Shape.isNull() or not fillet.Shape.isValid():
        raise RuntimeError("The final fillet geometry is invalid.")
    if len(fillet.Shape.Solids) != 1:
        raise RuntimeError("Expected a single solid.")

    return body
