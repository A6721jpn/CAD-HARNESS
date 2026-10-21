def build(doc):
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject("PartDesign::Body", "Body")

    def rectangle(name, width, depth, z):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(App.Vector(0, 0, z), App.Rotation())
        points = [
            App.Vector(-width / 2, -depth / 2, 0),
            App.Vector(width / 2, -depth / 2, 0),
            App.Vector(width / 2, depth / 2, 0),
            App.Vector(-width / 2, depth / 2, 0),
        ]
        for i in range(4):
            g = sketch.addGeometry(
                Part.LineSegment(points[i], points[(i + 1) % 4]), False
            )
            sketch.addConstraint(Sketcher.Constraint("Block", g))
        return sketch

    def one_side(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = 0
        else:
            feature.Midplane = False
        feature.Reversed = False

    base_sketch = rectangle("BaseSketch", 40, 30, 0)
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Type = 0
    pad.Length = 20
    one_side(pad)
    body.Tip = pad
    doc.recompute()

    pocket_sketch = rectangle("PocketSketch", 20, 15, 20)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5
    pocket.TaperAngle = 0
    one_side(pocket)
    body.Tip = pocket
    doc.recompute()

    outer_edges = []
    tolerance = 1e-7
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        vertices = [v.Point for v in edge.Vertexes]
        if len(vertices) != 2:
            continue
        if not all(abs(p.z - 20) < tolerance for p in vertices):
            continue
        on_x_boundary = (
            abs(vertices[0].x - vertices[1].x) < tolerance
            and all(abs(abs(p.x) - 20) < tolerance for p in vertices)
        )
        on_y_boundary = (
            abs(vertices[0].y - vertices[1].y) < tolerance
            and all(abs(abs(p.y) - 15) < tolerance for p in vertices)
        )
        if on_x_boundary or on_y_boundary:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    def linked_object(value):
        return value[0] if isinstance(value, (tuple, list)) else value

    if not pad.isDerivedFrom("PartDesign::Pad"):
        raise RuntimeError("Missing sketch-based Pad.")
    if not pocket.isDerivedFrom("PartDesign::Pocket"):
        raise RuntimeError("Missing sketch-based Pocket.")
    if not fillet.isDerivedFrom("PartDesign::Fillet"):
        raise RuntimeError("Missing Fillet.")
    if linked_object(pad.Profile) != base_sketch:
        raise RuntimeError("Invalid Pad profile.")
    if linked_object(pocket.Profile) != pocket_sketch:
        raise RuntimeError("Invalid Pocket profile.")
    if pocket.BaseFeature != pad:
        raise RuntimeError("Pocket predecessor must be Pad.")
    if linked_object(fillet.Base) != pocket:
        raise RuntimeError("Fillet must reference Pocket.")
    if fillet.BaseFeature != pocket or body.Tip != fillet:
        raise RuntimeError("Invalid final feature chain.")

    for obj in (base_sketch, pad, pocket_sketch, pocket, fillet):
        if obj not in body.Group:
            raise RuntimeError("Feature is outside the returned Body.")

    for feature in (pad, pocket, fillet):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError("Feature must contain one valid solid.")

    if body.Shape.isNull() or len(body.Shape.Solids) != 1:
        raise RuntimeError("Body must contain one solid.")

    for obj in (base_sketch, pad, pocket_sketch, pocket):
        obj.Visibility = False
    fillet.Visibility = True
    return body
