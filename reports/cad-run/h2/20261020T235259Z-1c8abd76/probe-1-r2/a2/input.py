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
        return sketch

    def one_side(feature):
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
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

    body.Tip = pad
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    pocket.BaseFeature = pad
    pocket.Type = 0
    pocket.Length = 5
    one_side(pocket)
    pocket.TaperAngle = 0
    body.Tip = pocket
    doc.recompute()

    tolerance = 1e-7
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20) < tolerance for point in points):
            continue
        on_x = (
            all(abs(abs(point.x) - 20) < tolerance for point in points)
            and abs(points[0].x - points[1].x) < tolerance
        )
        on_y = (
            all(abs(abs(point.y) - 15) < tolerance for point in points)
            and abs(points[0].y - points[1].y) < tolerance
        )
        if on_x or on_y:
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected exactly four outer top edges.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.BaseFeature = pocket
    fillet.Radius = 3
    body.Tip = fillet
    doc.recompute()

    def linked_object(value):
        return value[0] if isinstance(value, (tuple, list)) else value

    if not pad.isDerivedFrom("PartDesign::FeatureAdditive"):
        raise RuntimeError("The additive feature must be sketch based.")
    if linked_object(pad.Profile) != base_sketch:
        raise RuntimeError("Invalid Pad profile.")
    if linked_object(pocket.Profile) != pocket_sketch:
        raise RuntimeError("Invalid Pocket profile.")
    if pocket.BaseFeature != pad:
        raise RuntimeError("Pocket must directly follow Pad.")
    if linked_object(fillet.Base) != pocket:
        raise RuntimeError("Fillet must reference Pocket.")
    if fillet.BaseFeature != pocket or body.Tip != fillet:
        raise RuntimeError("Invalid final feature chain.")
    if any(obj not in body.Group for obj in (
        base_sketch, pad, pocket_sketch, pocket, fillet
    )):
        raise RuntimeError("All features must belong to the returned Body.")

    for feature in (pad, pocket, fillet):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError("Each feature must produce one valid solid.")

    base_sketch.Visibility = False
    pad.Visibility = False
    pocket_sketch.Visibility = False
    pocket.Visibility = False
    fillet.Visibility = True
    return body
