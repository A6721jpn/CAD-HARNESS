"""Hand-authored standalone native control; no compiler or gold access."""

def build_fixture(doc, p):
    import FreeCAD as App
    import Part
    import Sketcher
    import math

    body = doc.addObject("PartDesign::Body", "FixtureBody")
    last = None

    def sketch(name, origin=(0, 0, 0), rotation=None):
        obj = body.newObject("Sketcher::SketchObject", name)
        obj.Placement = App.Placement(App.Vector(*origin), rotation or App.Rotation())
        return obj

    def position(s, i, point, axis, value):
        if abs(value) < 1e-10:
            s.addConstraint(Sketcher.Constraint("PointOnObject", i, point, -2 if axis == "X" else -1))
        else:
            s.addConstraint(Sketcher.Constraint("Distance" + axis, i, point, value))

    def rectangle(s, b):
        x0, x1, y0, y1 = b
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        first = s.GeometryCount
        for i in range(4):
            s.addGeometry(Part.LineSegment(App.Vector(*pts[i], 0), App.Vector(*pts[(i + 1) % 4], 0)), False)
        for i in range(4):
            s.addConstraint(Sketcher.Constraint("Coincident", first + i, 2, first + (i + 1) % 4, 1))
            s.addConstraint(Sketcher.Constraint("Horizontal" if i % 2 == 0 else "Vertical", first + i))
        s.addConstraint(Sketcher.Constraint("Distance", first, x1 - x0))
        s.addConstraint(Sketcher.Constraint("Distance", first + 1, y1 - y0))
        position(s, first, 1, "X", x0)
        position(s, first, 1, "Y", y0)

    def circle(s, x, y, radius):
        i = s.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), radius), False)
        s.addConstraint(Sketcher.Constraint("Radius", i, radius))
        position(s, i, 3, "X", x)
        position(s, i, 3, "Y", y)

    def extrude(s, kind, length, name):
        nonlocal last
        doc.recompute()
        f = body.newObject("PartDesign::" + kind, name)
        f.Profile = s
        f.Length = length
        f.Length2 = 0
        f.Type = 0
        f.Reversed = False
        if last is not None:
            f.BaseFeature = last
        body.Tip = f
        doc.recompute()
        last = f
        return f

    def rect_pad(b, name):
        s = sketch(name + "Sketch", (0, 0, b[4]))
        rectangle(s, b[:4])
        return extrude(s, "Pad", b[5] - b[4], name)

    def rect_cut(b, top, depth, name):
        s = sketch(name + "Sketch", (0, 0, top))
        rectangle(s, b)
        return extrude(s, "Pocket", depth, name)

    kind = p["profile"]
    if kind == "roller":
        r, bore, length = p["radius"], p["bore_radius"], p["length"]
        s = sketch("Annulus")
        circle(s, 0, 0, r)
        circle(s, 0, 0, bore)
        extrude(s, "Pad", length, "Roller")
        if not p.get("omit_groove", False):
            low, high = p["groove_z"]
            s = sketch("GrooveRing", (0, 0, high))
            circle(s, 0, 0, r)
            circle(s, 0, 0, r - p["groove_depth"])
            extrude(s, "Pocket", high - low, "CircumferentialGroove")
    elif kind == "taper":
        w, d = p["bottom"]
        wt, dt = p["top"]
        low = sketch("BottomRectangle")
        rectangle(low, [-w / 2, w / 2, -d / 2, d / 2])
        high = sketch("TopRectangle", (0, 0, p["height"]))
        rectangle(high, [-wt / 2, wt / 2, -dt / 2, dt / 2])
        doc.recompute()
        f = body.newObject("PartDesign::AdditiveLoft", "Taper")
        f.Profile = low
        f.Sections = [high]
        f.Ruled = True
        body.Tip = f
        doc.recompute()
        last = f
    elif kind == "elbow":
        r = p["path_radius"]
        s = sketch("TubeSection", rotation=App.Rotation(App.Vector(0, 0, 1), App.Vector(1, 0, 0)))
        circle(s, 0, 0, p["outer_radius"])
        circle(s, 0, 0, p["inner_radius"])
        i = s.addGeometry(Part.LineSegment(App.Vector(-10, r, 0), App.Vector(10, r, 0)), True)
        s.addConstraint(Sketcher.Constraint("Horizontal", i))
        s.addConstraint(Sketcher.Constraint("DistanceY", i, 1, r))
        doc.recompute()
        f = body.newObject("PartDesign::Revolution", "BentTube")
        f.Profile = s
        f.ReferenceAxis = (s, ["Axis0"])
        f.Angle = 90
        f.Reversed = True
        body.Tip = f
        doc.recompute()
        last = f
    elif kind == "ribbed_box":
        b, wall = p["bbox"], p["wall"]
        rect_pad(b, "BoxStock")
        inner = [b[0] + wall, b[1] - wall, b[2] + wall, b[3] - wall]
        rect_cut(inner, b[5], b[5] - wall, "OpenCavity")
        if not p.get("omit_rib", False):
            s = sketch("RibTriangle", (0, p["rib_thickness"] / 2, 0), App.Rotation(App.Vector(1, 0, 0), 90))
            x0, x1 = inner[:2]
            z0, z1 = wall, p["rib_top"]
            pts = [(x0, z0), (x1, z0), (x1, z1)]
            for i in range(3):
                s.addGeometry(Part.LineSegment(App.Vector(*pts[i], 0), App.Vector(*pts[(i + 1) % 3], 0)), False)
                s.addConstraint(Sketcher.Constraint("Block", i))
            s.delConstraint(2)
            s.delConstraint(1)
            s.delConstraint(0)
            for i in range(3):
                s.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 3, 1))
            s.addConstraint(Sketcher.Constraint("Horizontal", 0))
            s.addConstraint(Sketcher.Constraint("Vertical", 1))
            s.addConstraint(Sketcher.Constraint("Distance", 0, x1 - x0))
            s.addConstraint(Sketcher.Constraint("Distance", 1, z1 - z0))
            position(s, 0, 1, "X", x0)
            position(s, 0, 1, "Y", z0)
            extrude(s, "Pad", p["rib_thickness"], "ConnectedRib")
    elif kind == "flange":
        s = sketch("FlangeAnnulus")
        circle(s, 0, 0, p["radius"])
        circle(s, 0, 0, p["bore_radius"])
        extrude(s, "Pad", p["thickness"], "FlangeStock")
        s = sketch("BoltCircle", (0, 0, p["thickness"]))
        pitch = s.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), p["pcd_radius"]), True)
        datum = s.addConstraint(Sketcher.Constraint("Diameter", pitch, 2 * p["pcd_radius"]))
        s.addConstraint(Sketcher.Constraint("Coincident", pitch, 3, -1, 1))
        mode = p.get("fixture_pcd_state", "linked")
        for i in range(p["pcd_count"]):
            if i == 0 and p.get("omit_pcd_hole", False):
                continue
            a = 2 * math.pi * i / p["pcd_count"]
            x, y = p["pcd_radius"] * math.cos(a), p["pcd_radius"] * math.sin(a)
            if mode == "decoy":
                if abs(y) < 1e-8:
                    h = s.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), p["hole_radius"]), False)
                    s.addConstraint(Sketcher.Constraint("Block", h))
                else:
                    circle(s, x, y, p["hole_radius"])
                continue
            h = s.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), p["hole_radius"]), False)
            s.addConstraint(Sketcher.Constraint("Radius", h, p["hole_radius"]))
            ray = s.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(x, y, 0)), True)
            s.addConstraint(Sketcher.Constraint("Coincident", ray, 1, -1, 1))
            s.addConstraint(Sketcher.Constraint("Horizontal", ray) if abs(y) < 1e-8 else
                            Sketcher.Constraint("Angle", ray, math.atan2(y, x)))
            s.addConstraint(Sketcher.Constraint("PointOnObject", ray, 2, pitch))
            s.addConstraint(Sketcher.Constraint("Coincident", h, 3, ray, 2))
        if mode == "reference":
            s.setDriving(datum, False)
        if mode == "inactive":
            s.setActive(datum, False)
        extrude(s, "Pocket", p["thickness"], "BoltHoles")
        for i, pocket in enumerate(p["pockets"]):
            rect_cut(pocket["bounds"], pocket["top_z"], pocket["depth"], "Slot%d" % i)
    elif kind == "rect_prism":
        rect_pad(p["bbox"], "PlateStock")
        for i, pocket in enumerate(p["pockets"]):
            rect_cut(pocket["bounds"], pocket["top_z"], pocket["depth"], "Pocket%d" % i)
        if p["holes"]:
            s = sketch("HoleCenters", (0, 0, p["bbox"][5]))
            for i, h in enumerate(p["holes"]):
                radius = h["diameter"] / 2 + (p.get("wrong_hole_delta", 1) if i == 0 and p.get("wrong_hole", False) else 0)
                circle(s, *h["center_xy"], radius)
            extrude(s, "Pocket", p["bbox"][5] - p["bbox"][4], "ThroughHoles")
    else:
        raise ValueError("unknown_fixture_profile")

    finish = p.get("finish")
    if finish and not p.get("omit_finish", False):
        b = p["bbox"]
        selected = []
        for i, e in enumerate(last.Shape.Edges, 1):
            pts = [v.Point for v in e.Vertexes]
            if (isinstance(e.Curve, Part.Line) and len(pts) == 2 and all(abs(v.z - b[5]) < 1e-7 for v in pts)
                    and (any(all(abs(v.x - x) < 1e-7 for v in pts) for x in b[:2])
                         or any(all(abs(v.y - y) < 1e-7 for v in pts) for y in b[2:4]))):
                selected.append("Edge%d" % i)
        if len(selected) != 4:
            raise ValueError("fixture_outer_top_edges")
        f = body.newObject("PartDesign::Fillet" if finish["kind"] == "fillet" else "PartDesign::Chamfer", "OuterFinish")
        f.Base = (last, selected)
        if finish["kind"] == "fillet":
            f.Radius = finish["size"]
        else:
            f.Size = finish["size"]
        f.UseAllEdges = False
        body.Tip = f
    doc.recompute()
    return body

_PARAMETERS = {'profile': 'rect_prism', 'bbox': [-52.0, 52.0, -35.0, 35.0, 0.0, 16.0], 'pockets': [{'bounds': [-37.0, -13.0, -8.0, 8.0], 'top_z': 16.0, 'depth': 5.0}, {'bounds': [13.0, 37.0, -8.0, 8.0], 'top_z': 16.0, 'depth': 5.0}], 'holes': [{'center_xy': [-34, -25], 'diameter': 6.0}, {'center_xy': [-34, 25], 'diameter': 6.0}, {'center_xy': [0, -25], 'diameter': 6.0}, {'center_xy': [0, 25], 'diameter': 6.0}, {'center_xy': [34, -25], 'diameter': 6.0}, {'center_xy': [34, 25], 'diameter': 6.0}], 'wrong_hole': True, 'wrong_hole_delta': 1.5, 'finish': {'kind': 'chamfer', 'size': 1.2}}

def build(doc):
    return build_fixture(doc, _PARAMETERS)
