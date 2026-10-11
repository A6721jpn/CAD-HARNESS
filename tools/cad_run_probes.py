"""Fixed task specifications and trusted probes; CAD imports are lazy."""
from math import pi, sqrt

TOL = 1e-6  # run04-script.py; bbox tolerance is separately runbook +/-0.1 mm.
GOAL_VOLUME = 22239.9556819442  # run02/run04/run05-cad.json measurements.
BOX_KEYS = ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max",
            "x_length", "y_length", "z_length")


def near(a, b):
    return abs(a - b) < TOL


def bbox(shape):
    box = shape.BoundBox
    return dict(zip(BOX_KEYS, (box.XMin, box.XMax, box.YMin, box.YMax,
                              box.ZMin, box.ZMax, box.XLength, box.YLength, box.ZLength)))


def numeric_predicates(m):
    b = m["bound_box_mm"]
    return {
        "bbox": all(abs(b[k] - v) <= 0.1 for k, v in
                    zip(("x_length", "y_length", "z_length"), (40, 30, 20))),
        "volume": m["volume_mm3"] < 22500 and abs(m["volume_mm3"] / GOAL_VOLUME - 1) <= 0.01,
        "faces": m["face_count"] == 15,
        "valid_solid": m["solid_count"] == 1 and m["is_valid"] is True,
    }


def matches(points, ends):
    def ordered(a, b):
        return all(near(x, y) for p, q in zip(a, b) for x, y in zip(p, q))
    return len(points) == 2 and (ordered(points, ends) or ordered(points[::-1], ends))


def rectangle_segments(x, y, z):
    points = [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    return [(points[i], points[(i + 1) % 4]) for i in range(4)]


def covers(records, segments):
    return (len(records) == len(segments) and all(r["line"] for r in records)
            and all(sum(matches(r["endpoints_mm"], s) for r in records) == 1 for s in segments))


def inner_predicate(records):
    segments = rectangle_segments(10, 7.5, 20) + rectangle_segments(10, 7.5, 15)
    segments += [((x, y, 15), (x, y, 20)) for x in (-10, 10) for y in (-7.5, 7.5)]
    return covers(records, segments) and all(
        r["adjacent_face_count"] == 2 and r["adjacent_normal_dot"] is not None
        and near(r["adjacent_normal_dot"], 0) for r in records)


def link(value):
    while isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return value


def edge_record(edge, part):
    return {"endpoints_mm": [[v.Point.x, v.Point.y, v.Point.z] for v in edge.Vertexes],
            "line": isinstance(edge.Curve, part.Line), "length_mm": edge.Length}


def probe(doc, body):
    import Part
    shape = body.Shape
    measured = {"bound_box_mm": bbox(shape), "volume_mm3": shape.Volume,
                "area_mm2": shape.Area, "face_count": len(shape.Faces),
                "solid_count": len(shape.Solids), "is_valid": shape.isValid()}
    checks = numeric_predicates(measured)
    floor, walls, inner = [], [], []
    for face in shape.Faces:
        if not isinstance(face.Surface, Part.Plane):
            continue
        b, n = bbox(face), face.normalAt(0, 0)
        if all(near(b[k], v) for k, v in zip(
                ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max"),
                (-10, 10, -7.5, 7.5, 15, 15))) and near(abs(n.z), 1):
            floor.append(face)
        xwall = near(b["x_min"], b["x_max"]) and near(abs(b["x_min"]), 10)
        ywall = near(b["y_min"], b["y_max"]) and near(abs(b["y_min"]), 7.5)
        span = ((xwall and near(b["y_min"], -7.5) and near(b["y_max"], 7.5))
                or (ywall and near(b["x_min"], -10) and near(b["x_max"], 10)))
        if span and near(b["z_min"], 15) and near(b["z_max"], 20) and near(n.z, 0):
            walls.append(face)
    for edge in shape.Edges:
        record = edge_record(edge, Part)
        points = record["endpoints_mm"]
        if len(points) != 2 or not all(
                -10 - TOL <= x <= 10 + TOL and -7.5 - TOL <= y <= 7.5 + TOL
                and 15 - TOL <= z <= 20 + TOL for x, y, z in points):
            continue
        if not (any(all(near(p[0], x) for p in points) for x in (-10, 10))
                or any(all(near(p[1], y) for p in points) for y in (-7.5, 7.5))):
            continue
        adjacent = [f for f in shape.Faces if any(edge.isSame(e) for e in f.Edges)]
        normals = [f.normalAt(0, 0) for f in adjacent if isinstance(f.Surface, Part.Plane)]
        record.update(adjacent_face_count=len(adjacent), adjacent_normal_dot=
                      normals[0].dot(normals[1]) if len(adjacent) == len(normals) == 2 else None)
        inner.append(record)
    checks.update(pocket_floor=len(floor) == 1, pocket_walls=len(walls) == 4,
                  pocket_inner_sharp=inner_predicate(inner))
    types = ("PartDesign::Body", "Sketcher::SketchObject", "PartDesign::Pad",
             "PartDesign::Pocket", "PartDesign::Fillet")
    groups = {t: [o for o in doc.Objects if o.TypeId == t] for t in types}
    checks["feature_counts"] = [len(groups[t]) for t in types] == [1, 2, 1, 1, 1]
    origin = body.Origin
    auxiliaries = [o for o in doc.Objects if o.TypeId not in types]
    checks["standard_auxiliaries"] = all(
        o.TypeId in ("App::Origin", "App::Line", "App::Plane", "App::Point")
        and (o == origin or (o in origin.OriginFeatures and origin in o.InList))
        for o in auxiliaries)
    checks["feature_chain"] = False
    checks["outer_fillet"] = False
    if checks["feature_counts"]:
        pad, pocket, fillet = (groups[t][0] for t in types[2:])
        base, top = link(pad.Profile), link(pocket.Profile)
        checks["feature_chain"] = (
            groups[types[0]][0] == body and base != top
            and base in groups[types[1]] and top in groups[types[1]]
            and all(o in body.Group for o in (base, pad, top, pocket, fillet))
            and body.Tip == fillet and fillet.Base[0] == pocket
            and link(top.AttachmentSupport) == pad and str(top.MapMode) == "FlatFace")
        checks["sketches"] = all(
            near(bbox(s.Shape)[k], v) for s, expected in (
                (base, (-20, 20, -15, 15, 0, 0)),
                (top, (-10, 10, -7.5, 7.5, 20, 20)))
            for k, v in zip(BOX_KEYS[:6], expected))
        checks["pad_pocket_lengths"] = all(
            near(o.Length.Value, length) and str(o.Type) in ("Length", "0")
            and not o.Reversed and (
                str(o.SideType) == o.getEnumerationsOfProperty("SideType")[0]
                if "SideType" in o.PropertiesList else not o.Midplane)
            for o, length in ((pad, 20), (pocket, 5)))
        pb = bbox(pad.Shape)
        checks["pad_one_direction"] = near(pb["z_min"], 0) and near(pb["z_max"], 20)
        names = list(fillet.Base[1])
        selected = []
        for name in names:
            if not name.startswith("Edge") or not name[4:].isdigit():
                break
            index = int(name[4:]) - 1
            if not 0 <= index < len(pocket.Shape.Edges):
                break
            selected.append(edge_record(pocket.Shape.Edges[index], Part))
        checks["outer_fillet"] = (
            len(names) == 4 and len(set(names)) == 4 and len(selected) == 4
            and near(fillet.Radius.Value, 3) and not getattr(fillet, "UseAllEdges", False)
            and covers(selected, rectangle_segments(20, 15, 20)))
    return {"measurements": measured, "predicates": checks, "probe_pass": all(checks.values()),
            "predicate_details": legacy_details(TASK_A, measured, checks, {
                "pocket_floor": (1, len(floor)), "pocket_walls": (4, len(walls)),
                "feature_counts": ([1, 2, 1, 1, 1], [len(groups[t]) for t in types])}),
            "reference": {"volume_mm3": GOAL_VOLUME, "volume_rule": "below_22500_and_within_1_percent",
                          "bbox_tolerance_mm": 0.1, "face_count": 15,
                          "source": "runbook section 6; run02/run04/run05-cad.json"}}


TASK_A = "A-box-pocket-fillet"
TASK_B = "B-plate-pocket-hole-pattern-chamfer"
B_VOLUME = 45600 - 270 * pi - 416 / 3
B_COUNTS = {"PartDesign::Body": 1, "Sketcher::SketchObject": 3,
            "PartDesign::Pad": 1, "PartDesign::Pocket": 2,
            "PartDesign::LinearPattern": 1, "PartDesign::Chamfer": 1,
            "PartDesign::Fillet": 0}
B_BOX = (-40, 40, -30, 30, 0, 10, 80, 60, 10)
B_CENTERS = ((-20, -20), (0, -20), (20, -20))


def b_near(a, b):
    return a is not None and abs(a - b) <= TOL


def b_box(actual, expected):
    return all(b_near(actual[k], v) for k, v in zip(BOX_KEYS, expected))


def b_predicates(m):
    """Evaluate independently extracted measurements; no input-script assertions."""
    holes = m["holes"]
    centers = all(sum(b_near(h["x"], x) and b_near(h["y"], y)
                      for h in holes) == 1 for x, y in B_CENTERS)
    return {
        "solid_valid": m["body_count"] == 1 and m["body_identity"]
                       and m["solid_count"] == 1 and m["is_valid"] is True,
        "bbox": b_box(m["bound_box_mm"], B_BOX),
        "central_pocket": m["pocket_geometry"] and m["pocket_inner_sharp"]
                          and b_near(m["pocket_depth_mm"], 4)
                          and m["pocket_length_mode"]
                          and b_box(m["pocket_sketch_box"], (-15, 15, -10, 10, 10, 10)),
        "holes_pattern": len(holes) == 3 and centers
                         and all(b_near(h["radius"], 3) and b_near(abs(h["axis"][2]), 1)
                                 and b_near(h["axis"][0], 0) and b_near(h["axis"][1], 0)
                                 and b_near(h["z_min"], 0) and b_near(h["z_max"], 10)
                                 and h["top_open"] and h["bottom_open"] and h["axis_empty"]
                                 for h in holes),
        "feature_counts": m["feature_counts"] == B_COUNTS and m["standard_auxiliaries"],
        "feature_chain": m["feature_chain_ok"],
        "outer_chamfer": m["outer_chamfer_geometry"] and m["outer_chamfer_selection"]
                         and m["pocket_inner_sharp"],
        "volume": abs(m["volume_mm3"] - B_VOLUME) / abs(B_VOLUME) <= TOL,
    }


def legacy_details(task_id, measured, predicates, observations=None):
    """Diagnostics only: legacy predicates above remain the entire pass formula."""
    if __package__:
        from .cad_spec_probe import Checks
    else:
        from cad_spec_probe import Checks
    details = Checks(task_id)
    for name, passed in predicates.items():
        expected, actual = (observations or {}).get(name, (True, passed))
        if name == "volume":
            expected = ({"target": GOAL_VOLUME, "relative": .01, "upper_exclusive": 22500}
                        if task_id == TASK_A else {"target": B_VOLUME, "relative": TOL})
            actual = measured["volume_mm3"]
        elif name == "faces":
            expected, actual = 15, measured["face_count"]
        elif name == "feature_counts" and task_id == TASK_B:
            expected, actual = B_COUNTS, measured["feature_counts"]
        if name == "bbox":
            items = (zip(BOX_KEYS[6:], (40, 30, 20)) if task_id == TASK_A else zip(BOX_KEYS, B_BOX))
            for key, value in items:
                observed = measured["bound_box_mm"][key]
                tol = .1 if task_id == TASK_A else TOL
                details.add(name, "bbox." + key, value, observed,
                            observed is not None and abs(observed - value) <= tol, tol)
        elif name == "holes_pattern":
            holes = measured["holes"]
            details.add(name, "holes.count", 3, len(holes), len(holes) == 3)
            for i, (x, y) in enumerate(B_CENTERS):
                found = next((h for h in holes if b_near(h["x"], x) and b_near(h["y"], y)), None)
                details.add(name, "holes.%d.center" % i, [x, y],
                            [found["x"], found["y"]] if found else None, found is not None, TOL)
                if found:
                    for key, value in (("radius", 3), ("z_min", 0), ("z_max", 10),
                                       ("top_open", True), ("bottom_open", True), ("axis_empty", True)):
                        observed = found.get(key)
                        details.add(name, "holes.%d.%s" % (i, key), value, observed,
                                    observed is True if value is True else b_near(observed, value), TOL)
            details.add(name, name + ".aggregate", True, passed, passed)
        else:
            details.add(name, name + ".aggregate", expected, actual, passed)
    return details.details()


def combined_box(faces):
    boxes = [bbox(f) for f in faces]
    if not boxes:
        return None
    values = [min(b[k] for b in boxes) if i % 2 == 0 else max(b[k] for b in boxes)
              for i, k in enumerate(BOX_KEYS[:6])]
    return dict(zip(BOX_KEYS, values + [values[1] - values[0], values[3] - values[2],
                                      values[5] - values[4]]))


def sharp_edges(shape, segments, part):
    records = []
    for edge in shape.Edges:
        record = edge_record(edge, part)
        if not any(matches(record["endpoints_mm"], segment) for segment in segments):
            continue
        adjacent = [f for f in shape.Faces if any(edge.isSame(e) for e in f.Edges)]
        normals = [f.normalAt(0, 0) for f in adjacent if isinstance(f.Surface, part.Plane)]
        records.append(record)
        if len(adjacent) != 2 or len(normals) != 2 or not b_near(normals[0].dot(normals[1]), 0):
            return False
    return covers(records, segments)


def length_mode(feature, expected):
    return (feature is not None and b_near(feature.Length.Value, expected)
            and str(feature.Type) in ("Length", "0") and not feature.Reversed
            and (str(feature.SideType) == feature.getEnumerationsOfProperty("SideType")[0]
                 if "SideType" in feature.PropertiesList else not feature.Midplane))


def pattern_vector(pattern, app):
    """Resolve the selected direction geometrically, without axis-object identity."""
    selected = pattern.Direction
    reference = link(selected)
    vector = reference if all(hasattr(reference, k) for k in ("x", "y", "z")) else None
    if vector is None:
        names = selected[1] if isinstance(selected, (tuple, list)) and len(selected) == 2 else ()
        if names and names[0]:
            subshape = reference.getSubObject(names[0])
            vector = getattr(getattr(subshape, "Curve", None), "Direction", None)
        else:
            axes = {"X_Axis": (1, 0, 0), "Y_Axis": (0, 1, 0), "Z_Axis": (0, 0, 1)}
            values = axes.get(getattr(reference, "Role", None))
            if values and reference.TypeId == "App::Line":
                vector = reference.getGlobalPlacement().Rotation.multVec(app.Vector(*values))
    if vector is None:
        return None
    values = [vector.x, vector.y, vector.z]
    magnitude = sqrt(sum(v * v for v in values))
    return [v / magnitude for v in values] if magnitude else None


def b_probe(doc, body):
    import FreeCAD as App
    import Part
    shape = body.Shape
    groups = {t: [o for o in doc.Objects if o.TypeId == t] for t in B_COUNTS}
    m = {"bound_box_mm": bbox(shape), "volume_mm3": shape.Volume, "area_mm2": shape.Area,
         "face_count": len(shape.Faces), "solid_count": len(shape.Solids),
         "is_valid": shape.isValid(), "body_count": len(groups["PartDesign::Body"]),
         "body_identity": body.Placement.isIdentity(),
         "feature_counts": {t: len(objects) for t, objects in groups.items()}}
    origin = body.Origin
    extras = [o for o in doc.Objects if o.TypeId not in groups]
    m["standard_auxiliaries"] = all(
        o.TypeId in ("App::Origin", "App::Line", "App::Plane", "App::Point")
        and (o == origin or (o in origin.OriginFeatures and origin in o.InList)) for o in extras)
    planes = [f for f in shape.Faces if isinstance(f.Surface, Part.Plane)]
    floor = [f for f in planes if all(b_near(getattr(v.Point, "z"), 6) for v in f.Vertexes)
             and b_near(abs(f.normalAt(0, 0).z), 1)]
    floor_box = combined_box(floor)
    walls = []
    for axis, side, boundary, span in (("x", -1, 15, 10), ("x", 1, 15, 10),
                                      ("y", -1, 10, 15), ("y", 1, 10, 15)):
        selected = [f for f in planes if b_near(f.normalAt(0, 0).z, 0)
                    and all(b_near(getattr(v.Point, axis), side * boundary) for v in f.Vertexes)]
        actual = combined_box(selected)
        expected = ((side * boundary, side * boundary, -span, span, 6, 10) if axis == "x"
                    else (-span, span, side * boundary, side * boundary, 6, 10))
        walls.append(actual is not None and b_box(actual, expected))
    m["pocket_geometry"] = (floor_box is not None
                            and b_box(floor_box, (-15, 15, -10, 10, 6, 6)) and all(walls))
    segments = rectangle_segments(15, 10, 10) + rectangle_segments(15, 10, 6)
    segments += [((x, y, 6), (x, y, 10)) for x in (-15, 15) for y in (-10, 10)]
    m["pocket_inner_sharp"] = sharp_edges(shape, segments, Part)
    cylinders = []
    for face in shape.Faces:
        surface = face.Surface
        if not isinstance(surface, Part.Cylinder):
            continue
        center, axis, fb = surface.Center, surface.Axis, bbox(face)
        group = next((g for g in cylinders if b_near(g["x"], center.x)
                      and b_near(g["y"], center.y) and b_near(g["radius"], surface.Radius)
                      and all(b_near(abs(a), abs(b)) for a, b in zip(g["axis"], axis))), None)
        if group is None:
            group = {"x": center.x, "y": center.y, "radius": surface.Radius,
                     "axis": [axis.x, axis.y, axis.z], "z_min": fb["z_min"], "z_max": fb["z_max"]}
            cylinders.append(group)
        group["z_min"], group["z_max"] = min(group["z_min"], fb["z_min"]), max(group["z_max"], fb["z_max"])
    for group in cylinders:
        for z, label in ((10, "top_open"), (0, "bottom_open")):
            rims = [e for e in shape.Edges if isinstance(e.Curve, Part.Circle)
                    and b_near(e.Curve.Center.x, group["x"]) and b_near(e.Curve.Center.y, group["y"])
                    and b_near(e.Curve.Radius, group["radius"])
                    and b_near(abs(e.Curve.Axis.z), 1)
                    and b_near(bbox(e)["z_min"], z) and b_near(bbox(e)["z_max"], z)]
            group[label] = b_near(sum(e.Length for e in rims), 2 * pi * group["radius"])
        group["axis_empty"] = all(not shape.isInside(App.Vector(group["x"], group["y"], z), TOL, True)
                                  for z in (0, 5, 10))
    m["holes"] = cylinders
    # Collect all planar pieces of each of the four prescribed bevel planes.
    bevels = []
    for axis, side, half, span in (("x", -1, 40, 30), ("x", 1, 40, 30),
                                  ("y", -1, 30, 40), ("y", 1, 30, 40)):
        selected = [f for f in planes if b_near(abs(f.normalAt(0, 0).z), sqrt(0.5))
                    and b_near(abs(getattr(f.normalAt(0, 0), axis)), sqrt(0.5))
                    and all(b_near(side * getattr(v.Point, axis) + v.Point.z, half + 9)
                            for v in f.Vertexes)]
        actual = combined_box(selected)
        lo, hi = sorted((side * half, side * (half - 1)))
        expected = (lo, hi, -span, span, 9, 10) if axis == "x" else (-span, span, lo, hi, 9, 10)
        bevels.append(actual is not None and b_box(actual, expected))
    outer_top = rectangle_segments(39, 29, 10)
    top_edges = [edge_record(e, Part) for e in shape.Edges
                 if any(matches(edge_record(e, Part)["endpoints_mm"], s) for s in outer_top)]
    m["outer_chamfer_geometry"] = all(bevels) and covers(top_edges, outer_top)
    m.update(pocket_depth_mm=None, pocket_length_mode=False, pocket_sketch_box=dict.fromkeys(BOX_KEYS),
             hole_pattern_attributes=False, feature_chain_ok=False, outer_chamfer_selection=False,
             pattern_length_mm=None, pattern_occurrences=None, pattern_axis_role=None,
             pattern_direction=None, chamfer_size_mm=None)
    pads, pockets, patterns, chamfers = (groups[t] for t in (
        "PartDesign::Pad", "PartDesign::Pocket", "PartDesign::LinearPattern", "PartDesign::Chamfer"))
    if len(pads) == 1 and len(pockets) == 2 and len(patterns) == 1:
        pad, pattern = pads[0], patterns[0]
        central = next((p for p in pockets if getattr(p, "BaseFeature", None) == pad), None)
        hole = next((p for p in pockets if getattr(p, "BaseFeature", None) == central), None)
        if central is not None and hole is not None:
            base, ps, hs = link(pad.Profile), link(central.Profile), link(hole.Profile)
            axis = link(pattern.Direction)
            m.update(pocket_depth_mm=central.Length.Value, pocket_length_mode=length_mode(central, 4),
                     pocket_sketch_box=bbox(ps.Shape), pattern_length_mm=pattern.Length.Value,
                     pattern_occurrences=pattern.Occurrences, pattern_axis_role=getattr(axis, "Role", None))
            circles = [edge.Curve for edge in hs.Shape.Edges if isinstance(edge.Curve, Part.Circle)]
            direction = pattern_vector(pattern, App)
            m["pattern_direction"] = direction
            m["hole_pattern_attributes"] = (
                bool(circles) and all(b_near(circle.Center.x, -20) and b_near(circle.Center.y, -20)
                                     and b_near(circle.Center.z, 10) and b_near(circle.Radius, 3)
                                     and b_near(circle.Axis.x, 0) and b_near(circle.Axis.y, 0)
                                     and b_near(abs(circle.Axis.z), 1) for circle in circles)
                and length_mode(hole, 10) and b_box(bbox(hs.Shape), (-23, -17, -23, -17, 10, 10))
                and list(pattern.Originals) == [hole] and pattern.Occurrences == 3
                and direction is not None and all(b_near(v, expected) for v, expected in
                                                  zip(direction, (1, 0, 0)))
                and not pattern.Reversed)
            common_chain = (len({base, ps, hs}) == 3 and all(
                s in groups["Sketcher::SketchObject"] for s in (base, ps, hs))
                and length_mode(pad, 10) and b_box(bbox(base.Shape), (-40, 40, -30, 30, 0, 0))
                and m["hole_pattern_attributes"]
                and getattr(pattern, "BaseFeature", None) == hole
                and link(ps.AttachmentSupport) == pad and link(hs.AttachmentSupport) == central
                and str(ps.MapMode) == str(hs.MapMode) == "FlatFace"
                and all(o in body.Group for o in (base, pad, ps, central, hs, hole, pattern)))
            if len(chamfers) == 1:
                chamfer = chamfers[0]
                sequence = (base, pad, ps, central, hs, hole, pattern, chamfer)
                m["feature_chain_ok"] = (common_chain and chamfer in body.Group and body.Tip == chamfer
                                         and chamfer.Base[0] == pattern
                                         and [body.Group.index(o) for o in sequence]
                                         == sorted(body.Group.index(o) for o in sequence))
                names, selected = list(chamfer.Base[1]), []
                for name in names:
                    if name.startswith("Edge") and name[4:].isdigit():
                        index = int(name[4:]) - 1
                        if 0 <= index < len(pattern.Shape.Edges):
                            selected.append(edge_record(pattern.Shape.Edges[index], Part))
                m["chamfer_size_mm"] = chamfer.Size.Value
                m["outer_chamfer_selection"] = (
                    len(names) == len(set(names)) == len(selected) == 4
                    and b_near(chamfer.Size.Value, 1) and not getattr(chamfer, "UseAllEdges", False)
                    and covers(selected, rectangle_segments(40, 30, 10)))
    checks = b_predicates(m)
    return {"measurements": m, "predicates": checks, "probe_pass": all(checks.values()),
            "predicate_details": legacy_details(TASK_B, m, checks),
            "reference": {"volume_mm3": B_VOLUME, "volume_formula": "45600 - 270*pi - 416/3",
                          "unit": "mm^3", "provenance": "CONSENSUS section 2: geometric derivation",
                          "linear_tolerance_mm": TOL, "axis_tolerance": TOL,
                          "volume_relative_tolerance": TOL}}


A_PROMPT = """モデル / effort: gpt-6.1-sol / xhigh。
ホスト: DPC-019。CADはFreeCAD 1.1.4のみ。SolidWorksとFusionは起動しない。LPC-017ではCADを実行しない。
単位mm、新規ドキュメント、単一ソリッドボディで次を作る。
1) 直方体。幅40 mm（X）×奥行30 mm（Y）×高さ20 mm（Z）。PartDesignのBody上で、XYスケッチの中心矩形をPad長さ20 mmとする（片方向。貫通や対称の二重化はしない）。
2) 上面中央に20×15 mm、深さ5 mmの非貫通矩形ポケット。上面スケッチの中心矩形をPocket長さ5 mmとする。Through allではない。壁はスケッチ法線方向（垂直）。
3) 一定半径R=3 mmのフィレットを上面外周の4辺だけに適用する。ポケット内側のエッジには絶対にフィレットしない。
4) 追加フィーチャなし。最終も単一ソリッドボディ。
寸法・体積・表面積・面数はFreeCAD上で実際に読めた値だけ記録する。読めなければnull。理論値を実測として書かない。実在しないマクロは作ったことにしない。
返答はbuild(doc)を定義する完全なUTF-8 Pythonソースだけ。Markdownの説明や実行コマンドは返さない。
利用モジュールはFreeCAD、Part、Sketcher、math。必要な補助関数は定義してよい。
build(doc)は渡された文書に形状を作り、PartDesignのBodyを返す。作成中のrecomputeは使ってよい。
新規文書作成・Probe・保存・close・プロセス回収・CAD実行はdriver/cad_runが担当する。
シェル、調査、FreeCADの直接起動、ファイルやネットワーク操作を行わない。秘密や個人パスを書かない。
fixture、evidence、既存reports、他runの解答を参照・コピーしない。
"""

B_PROMPT = """モデル / effort: gpt-6.1-sol / xhigh。
ホスト: DPC-019のみでCADを実行する。CADはFreeCAD 1.1.4のみ。SolidWorksとFusionは起動しない。LPC-017ではCADを実行しない。
単位mm、新規文書、原点・回転なしのPartDesign::Bodyが1個、最終valid solidが1個。
1) XY中心矩形80×60のSketchを+Zへ片方向Pad長さ10。X=-40..40、Y=-30..30、Z=0..10。
2) Z=10の上面中央に30×20の矩形Sketch、Pocket長さ4で非貫通。X=-15..15、Y=-10..10、底Z=6、垂直壁。Through allではない。
3) 上面Z=10に中心(-20,-20)、半径3の円Sketch。穴Pocketを下向き長さ10でZ=0まで貫通し、上下で開口する。
4) 穴PocketだけをBodyの+X方向へLinearPattern。元を含め3個、中心XY=(-20,-20),(0,-20),(20,-20)。間隔20、最初から最後の総距離40。
5) 上面外周4直線辺だけ等脚1、45度のChamfer。中央Pocketの縁、穴の縁、縦稜、下面は面取りしない。最終TipはChamfer。
順序はPad→中央Pocket→穴Pocket→LinearPattern→Chamfer。Pad/Pocketは非対称・非Reversed。
標準Origin族以外はBody 1、Sketch 3、Pad 1、Pocket 2、LinearPattern 1、Chamfer 1、Fillet 0。追加Part::Feature、Hole、座ぐり、ねじは作らない。
返答はbuild(doc)を定義する完全なUTF-8 Pythonソースだけ。Markdownの説明や実行コマンドは返さない。
利用モジュールはFreeCAD、Part、Sketcher、math。必要な補助関数は定義してよい。
build(doc)は渡された文書に作成しBodyを返す。作成中のrecomputeは使ってよい。
新規文書作成・Probe・保存・close・プロセス回収・CAD実行はdriver/cad_runが担当する。
シェル、調査、FreeCADの直接起動、ファイルやネットワーク操作を行わない。秘密や個人パスを書かない。
fixture、evidence、既存reports、他runの解答、API例を参照・コピーしない。理論値を実測として書かない。
"""
SPECS = {TASK_A: {"prompt": A_PROMPT, "probe": probe},
         TASK_B: {"prompt": B_PROMPT, "probe": b_probe}}
