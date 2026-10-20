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
        corners = [
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        ]
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            sketch.addGeometry(
                Part.LineSegment(
                    App.Vector(a[0], a[1], 0),
                    App.Vector(b[0], b[1], 0),
                ),
                False,
            )
        for i in range(4):
            sketch.addConstraint(
                Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1)
            )
            sketch.addConstraint(
                Sketcher.Constraint(
                    "Horizontal" if i % 2 == 0 else "Vertical", i
                )
            )
        sketch.addConstraint(Sketcher.Constraint("Distance", 0, width))
        sketch.addConstraint(Sketcher.Constraint("Distance", 1, depth))
        sketch.addConstraint(
            Sketcher.Constraint("DistanceX", 0, 1, -width / 2)
        )
        sketch.addConstraint(
            Sketcher.Constraint("DistanceY", 0, 1, -depth / 2)
        )
        doc.recompute()
        return sketch

    def configure_extrusion(feature, length):
        feature.Type = 0
        feature.Length = length
        if "SideType" in feature.PropertiesList:
            feature.SideType = "One side"
        else:
            feature.Midplane = False
        feature.Reversed = False
        feature.TaperAngle = 0.0
        if "AlongSketchNormal" in feature.PropertiesList:
            feature.AlongSketchNormal = True

    def validate(feature):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError(
                "{} must contain one valid solid.".format(feature.Name)
            )

    base_sketch = rectangle("BaseSketch", 40.0, 30.0, 0.0)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    configure_extrusion(pad, 20.0)
    doc.recompute()
    validate(pad)

    pocket_sketch = rectangle("PocketSketch", 20.0, 15.0, 20.0)
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = pocket_sketch
    configure_extrusion(pocket, 5.0)
    doc.recompute()
    validate(pocket)

    tolerance = 1e-7
    outer_edges = []
    for index, edge in enumerate(pocket.Shape.Edges, 1):
        points = [vertex.Point for vertex in edge.Vertexes]
        if len(points) != 2:
            continue
        if not all(abs(point.z - 20.0) < tolerance for point in points):
            continue
        if any(
            all(
                abs(getattr(point, axis) - coordinate) < tolerance
                for point in points
            )
            for axis, coordinate in (
                ("x", -20.0),
                ("x", 20.0),
                ("y", -15.0),
                ("y", 15.0),
            )
        ):
            outer_edges.append("Edge{}".format(index))

    if len(outer_edges) != 4:
        raise RuntimeError("Expected four outer perimeter edges at the top.")

    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pocket, outer_edges)
    fillet.Radius = 3.0
    body.Tip = fillet
    doc.recompute()
    validate(fillet)

    for feature in (base_sketch, pad, pocket_sketch, pocket):
        feature.Visibility = False
    fillet.Visibility = True
    return body
