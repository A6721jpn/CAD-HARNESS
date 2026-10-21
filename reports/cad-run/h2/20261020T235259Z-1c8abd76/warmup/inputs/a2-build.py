def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(sketch, width, depth):
        corners = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            n = sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
            sketch.addConstraint(Sketcher.Constraint("Block", n))

    base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    rectangle(base, 40, 30)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base
    pad.Type = 0
    pad.Length = 20
    pad.SideType = "One side"
    pad.Reversed = False
    doc.recompute()

    if pad.Shape.isNull() or len(pad.Shape.Solids) != 1:
        raise RuntimeError("Pad did not produce one solid.")

    tol = 1e-7
    top_faces = [
        "Face{}".format(i)
        for i, face in enumerate(pad.Shape.Faces, 1)
        if abs(face.BoundBox.ZMin - 20) < tol
        and abs(face.BoundBox.ZMax - 20) < tol
    ]
    if len(top_faces) != 1:
        raise RuntimeError("Could not identify the Pad top face.")

    pocket_sketch = body.newObject("Sketcher::SketchObject", "PocketSketch")
    pocket_sketch.AttachmentSupport = (pad, [top_faces[0]])
    pocket_sketch.MapMode = "FlatFace"
    doc.recompute()

    inverse = pocket_sketch.Placement.inverse()
    corners = [
        inverse.multVec(App.Vector(x, y, 20))
        for x, y in [(-10, -7.5), (10, -7.5), (10, 7.5), (-10, 7.5)]
    ]
    for i in range(4):
        a = corners[i]
        b = corners[(i + 1) % 4]
        n = pocket_sketch.addGeometry(
            Part.LineSegment(
                App.Vector(a.x, a.y, 0),
                App.Vector(b.x, b.y, 0),
            ),
            False,
        )
        pocket_sketch.addConstraint(Sketcher.Constraint("Block", n))
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
        raise RuntimeError("Pocket did not produce one solid.")

    edges = []
    for i, edge in enumerate(pocket.Shape.Edges, 1):
        box = edge.BoundBox
        on_top = (
            abs(box.ZMin - 20) < tol
            and abs(box.ZMax - 20) < tol
        )
        outer = (
            (abs(box.XMin - 20) < tol and abs(box.XMax - 20) < tol)
            or (abs(box.XMin + 20) < tol and abs(box.XMax + 20) < tol)
            or (abs(box.YMin - 15) < tol and abs(box.YMax - 15) < tol)
            or (abs(box.YMin + 15) < tol and abs(box.YMax + 15) < tol)
        )
        if on_top and outer:
            edges.append("Edge{}".format(i))

    if len(edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, edges)
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    if (
        fillet.Shape.isNull()
        or not fillet.Shape.isValid()
        or len(fillet.Shape.Solids) != 1
    ):
        raise RuntimeError("Fillet did not produce one valid solid.")

    base.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
