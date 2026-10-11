"""Trusted MVP measurements of actual BRep/native history; no builder or LLM imports."""
import hashlib
import json
import math
from pathlib import Path
import re

GOLD_SCHEMA = Path(__file__).resolve().parents[1] / "design/cad-harness-mvp/eval-v1/schema.json"
BOX_KEYS = ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max")


def read_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_gold_key")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("nonfinite_gold")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject)


def gold_check(value, node, schema):
    if "$ref" in node:
        target = schema
        for part in node["$ref"].split("/")[1:]:
            target = target[part]
        return gold_check(value, target, schema)
    if "oneOf" in node:
        accepted = 0
        for choice in node["oneOf"]:
            try:
                gold_check(value, choice, schema)
                accepted += 1
            except ValueError:
                pass
        if accepted != 1:
            raise ValueError("gold_oneOf")
    types = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "number": type(value) in (int, float) and math.isfinite(value),
             "null": value is None, "boolean": type(value) is bool}
    if "type" in node and not types.get(node["type"], False):
        raise ValueError("gold_type")
    if "const" in node and (value != node["const"] or type(value) is not type(node["const"])):
        raise ValueError("gold_const")
    if "enum" in node and value not in node["enum"]:
        raise ValueError("gold_enum")
    if isinstance(value, dict):
        props = node.get("properties", {})
        if set(node.get("required", [])) - set(value):
            raise ValueError("gold_required")
        if node.get("additionalProperties") is False and set(value) - set(props):
            raise ValueError("gold_unknown_field")
        for key in value.keys() & props.keys():
            gold_check(value[key], props[key], schema)
    if isinstance(value, list):
        if not node.get("minItems", 0) <= len(value) <= node.get("maxItems", math.inf):
            raise ValueError("gold_array_length")
        for item in value:
            if "items" in node:
                gold_check(item, node["items"], schema)
    if type(value) in (int, float) and not math.isfinite(value):
        raise ValueError("nonfinite_gold")


def load_gold(path):
    gold = read_json(Path(path).read_text(encoding="utf-8"))
    schema = read_json(GOLD_SCHEMA.read_text(encoding="utf-8"))
    gold_check(gold, schema, schema)
    provenance = gold["provenance"]
    if provenance["confirmed"] is not (provenance["authority"] == "human"):
        raise ValueError("gold_provenance")
    if (not re.fullmatch(r"[A-Za-z0-9_-]+", gold["case_id"]) or
            hashlib.sha256(gold["description"].encode("utf-8")).hexdigest() != gold["description_sha256"]):
        raise ValueError("gold_identity")
    if gold["volume"]["target_mm3"] <= 0 or any(gold["bbox"][i] >= gold["bbox"][i + 1] for i in (0, 2, 4)):
        raise ValueError("gold_dimensions")
    return gold


def make_details(task_id, records):
    """Bounded records from the same comparisons that determine pass/fail."""
    failed = []
    for row in records:
        if row.get("passed") is True:
            continue
        item = {k: v for k, v in row.items() if k != "passed"}
        for key in ("expected", "actual"):
            if len(json.dumps(item.get(key), ensure_ascii=False, allow_nan=False).encode("utf-8")) > 256:
                item[key] = None
                item["reason"] = key + "_omitted_size_limit"
        failed.append(item)
    first, rest, seen = [], [], set()
    for item in failed:
        target = first if item["predicate"] not in seen else rest
        target.append(item)
        seen.add(item["predicate"])
    output = {"version": 1, "task_id": task_id, "checks": [], "truncated": False, "omitted": 0}
    for item in first + rest:
        output["checks"].append(item)
        if len(output["checks"]) > 32 or len(json.dumps(output, ensure_ascii=False, allow_nan=False).encode("utf-8")) > 8100:
            output["checks"].pop()
            output["omitted"] += 1
    output["truncated"] = output["omitted"] > 0
    return output


class Checks:
    def __init__(self, task_id):
        self.task_id, self.records, self.predicates = task_id, [], {}

    def add(self, predicate, sub_id, expected, actual, passed, tolerance=None, reason=None):
        passed = passed is True
        self.predicates[predicate] = self.predicates.get(predicate, True) and passed
        row = {"predicate": predicate, "sub_check_id": sub_id, "expected": expected,
               "actual": actual, "passed": passed}
        if tolerance is not None:
            row["tolerance"] = tolerance
        if reason:
            row["reason"] = reason
        self.records.append(row)

    def details(self):
        return make_details(self.task_id, self.records)


def bounds(shape, offset=(0, 0, 0)):
    b = shape.BoundBox
    return [b.XMin - offset[0], b.XMax - offset[0], b.YMin - offset[1],
            b.YMax - offset[1], b.ZMin - offset[2], b.ZMax - offset[2]]


def close(a, b, tol):
    return a is not None and type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= tol


def same_bounds(actual, expected, tol):
    return actual is not None and len(actual) == len(expected) and all(close(a, b, tol) for a, b in zip(actual, expected))


def union_bounds(items):
    return ([min(b[i] for b in items) if i % 2 == 0 else max(b[i] for b in items) for i in range(6)]
            if items else None)


def vector(v):
    return [v.x, v.y, v.z]


def axis(v):
    values = vector(v)
    length = math.sqrt(sum(a * a for a in values))
    if length == 0:
        raise ValueError("zero_axis")
    values = [a / length for a in values]
    first = next((a for a in values if abs(a) > 1e-9), 1)
    return [-a for a in values] if first < 0 else values


def rectangle_segments(b, z):
    x0, x1, y0, y1 = b
    points = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    return [(points[i], points[(i + 1) % 4]) for i in range(4)]


def covers_segment(edges, segment, tol, sharp=False, shape=None):
    import Part
    a, b = segment
    direction = next(i for i in range(3) if abs(a[i] - b[i]) > tol)
    lo, hi = sorted((a[direction], b[direction]))
    intervals = []
    for edge, points in edges:
        if not isinstance(edge.Curve, Part.Line) or len(points) != 2:
            continue
        if not all(abs(p[k] - a[k]) <= tol for p in points for k in range(3) if k != direction):
            continue
        first, last = sorted(p[direction] for p in points)
        if first < lo - tol or last > hi + tol:
            continue
        if sharp:
            adjacent = [f for f in shape.Faces if any(edge.isSame(e) for e in f.Edges)]
            if len(adjacent) != 2 or any(not isinstance(f.Surface, Part.Plane) for f in adjacent):
                continue
            normals = [f.normalAt(0, 0) for f in adjacent]
            if abs(normals[0].dot(normals[1])) > 1e-6:
                continue
        intervals.append((first, last))
    end = lo
    for first, last in sorted(intervals):
        if first > end + tol:
            return False
        end = max(end, last)
    return end >= hi - tol


def measure_shape(shape, gold, checks):
    import FreeCAD as App
    import Part
    tol, at = gold["tolerances"]["linear_mm"], gold["tolerances"]["axis"]
    world = bounds(shape)
    offset = ((world[0] + world[1]) / 2, (world[2] + world[3]) / 2, world[4]) if gold["frame"] == "bbox_relative" else (0, 0, 0)
    actual_box = bounds(shape, offset)
    m = {"bound_box_mm": dict(zip(BOX_KEYS, world)), "volume_mm3": shape.Volume,
         "area_mm2": shape.Area, "face_count": len(shape.Faces), "solid_count": len(shape.Solids),
         "is_valid": shape.isValid(), "offset_mm": list(offset)}
    checks.add("valid_solid", "shape.solid_count", 1, len(shape.Solids), len(shape.Solids) == 1)
    checks.add("valid_solid", "shape.valid", True, m["is_valid"], m["is_valid"] is True)
    for i, key in enumerate(BOX_KEYS):
        checks.add("bbox", "bbox." + key, gold["bbox"][i], actual_box[i], close(actual_box[i], gold["bbox"][i], tol), tol)
    volume = gold["volume"]
    passed = abs(shape.Volume / volume["target_mm3"] - 1) <= volume["relative"]
    if "upper_exclusive" in volume:
        passed = passed and shape.Volume < volume["upper_exclusive"]
    checks.add("volume", "volume.target", volume, shape.Volume, passed, volume["relative"])
    edges = [(e, [[v.Point.x - offset[0], v.Point.y - offset[1], v.Point.z - offset[2]] for v in e.Vertexes])
             for e in shape.Edges]
    planes, cylinders, extras = [], [], []
    for face in shape.Faces:
        surface, b = face.Surface, bounds(face, offset)
        if isinstance(surface, Part.Plane):
            planes.append({"face": face, "bounds": b, "normal": vector(face.normalAt(0, 0)), "area": face.Area})
        elif isinstance(surface, Part.Cylinder):
            u0, u1, v0, v1 = face.ParameterRange
            u, v = (u0 + u1) / 2, (v0 + v1) / 2
            point, normal = face.valueAt(u, v), face.normalAt(u, v)
            radial = point - surface.Center
            radial -= surface.Axis * radial.dot(surface.Axis)
            cylinders.append({"center": [surface.Center.x - offset[0], surface.Center.y - offset[1], surface.Center.z - offset[2]],
                              "axis": axis(surface.Axis), "radius": surface.Radius, "bounds": b,
                              "inside": normal.dot(radial) < 0})
        else:
            extras.append({"surface": type(surface).__name__, "bounds": b})
    groups = []
    for c in cylinders:
        if not same_bounds(c["axis"], [0, 0, 1], at):
            continue
        found = next((r for r in groups if r["inside"] == c["inside"] and close(r["radius"], c["radius"], tol)
                      and same_bounds(r["center_xy"], c["center"][:2], tol)), None)
        if found is None:
            found = {"center_xy": c["center"][:2], "radius": c["radius"], "axis": c["axis"],
                     "z": c["bounds"][4:6], "inside": c["inside"]}
            groups.append(found)
        found["z"] = [min(found["z"][0], c["bounds"][4]), max(found["z"][1], c["bounds"][5])]
    holes, steps = [r for r in groups if r["inside"]], [r for r in groups if not r["inside"]]
    for h in holes:
        x, y = h["center_xy"]
        h["axis_empty"] = all(not shape.isInside(App.Vector(x + offset[0], y + offset[1], z + offset[2]), 1e-7, True)
                              for z in (h["z"][0], (h["z"][0] + h["z"][1]) / 2, h["z"][1]))
        for z, key in zip(h["z"], ("bottom_open", "top_open")):
            rims = [e for e in shape.Edges if isinstance(e.Curve, Part.Circle)
                    and same_bounds([e.Curve.Center.x - offset[0], e.Curve.Center.y - offset[1]], h["center_xy"], tol)
                    and close(e.Curve.Radius, h["radius"], tol) and same_bounds(axis(e.Curve.Axis), [0, 0, 1], at)
                    and same_bounds(bounds(e, offset)[4:6], [z, z], tol)]
            h[key] = abs(sum(e.Length for e in rims) - 2 * math.pi * h["radius"]) <= tol
    m["holes"], m["steps"] = holes, steps
    checks.add("holes", "holes.count", len(gold["holes"]), len(holes), len(holes) == len(gold["holes"]))
    for index, expected in enumerate(gold["holes"]):
        h = next((h for h in holes if same_bounds(h["center_xy"], expected["center_xy"], tol)), None)
        prefix = "holes.%d." % index
        checks.add("holes", prefix + "center", expected["center_xy"], h["center_xy"] if h else None, h is not None)
        for key, value in (("radius", expected["diameter"] / 2), ("z", expected["z"]), ("axis", [0, 0, 1]),
                           ("top_open", True), ("bottom_open", True), ("axis_empty", True)):
            actual = h.get(key) if h else None
            ok = (same_bounds(actual, value, at if key == "axis" else tol) if isinstance(value, list)
                  else actual is True if value is True else close(actual, value, tol))
            checks.add("holes", prefix + key, value, actual, ok)
    checks.add("steps", "steps.count", len(gold["steps"]), len(steps), len(steps) == len(gold["steps"]))
    for index, expected in enumerate(gold["steps"]):
        found = next((r for r in steps if same_bounds(r["center_xy"], expected["center_xy"], tol)
                      and same_bounds(r["z"], expected["z"], tol)), None)
        checks.add("steps", "steps.%d.cylinder" % index, expected, found,
                   found is not None and close(found["radius"], expected["diameter"] / 2, tol))
        cx, cy = expected["center_xy"]
        checks.add("steps", "steps.%d.solid_axis" % index, True, None if found is None else
                   shape.isInside(App.Vector(cx + offset[0], cy + offset[1], sum(expected["z"]) / 2 + offset[2]), 1e-7, True),
                   found is not None and shape.isInside(App.Vector(cx + offset[0], cy + offset[1], sum(expected["z"]) / 2 + offset[2]), 1e-7, True))
    for i in range(1, len(gold["steps"])):
        lower, upper = gold["steps"][i - 1], gold["steps"][i]
        z, r = upper["z"][0], max(lower["diameter"], upper["diameter"]) / 2
        x, y = upper["center_xy"]
        faces = [p for p in planes if same_bounds(p["bounds"], [x-r, x+r, y-r, y+r, z, z], tol)]
        area = sum(p["area"] for p in faces)
        expected = math.pi * abs(lower["diameter"] ** 2 - upper["diameter"] ** 2) / 4
        checks.add("steps", "steps.%d.shoulder" % i, expected, area, abs(area - expected) <= tol * 2 * math.pi * r)
    for index, section in enumerate(gold["sections"]):
        z = section["z"] + offset[2]
        width, depth = world[1] - world[0] + 20, world[3] - world[2] + 20
        cut = shape.section(Part.makePlane(width, depth, App.Vector(world[0] - 10, world[2] - 10, z)))
        observed = bounds(cut, offset) if not cut.isNull() else None
        expected = section["bounds"] + [section["z"], section["z"]]
        checks.add("sections", "sections.%d.bounds" % index, expected, observed, same_bounds(observed, expected, tol))
        section_edges = [(e, [[v.Point.x-offset[0], v.Point.y-offset[1], v.Point.z-offset[2]] for v in e.Vertexes]) for e in cut.Edges]
        for j, segment in enumerate(rectangle_segments(section["bounds"], section["z"])):
            checks.add("sections", "sections.%d.side.%d" % (index, j), list(segment), None,
                       covers_segment(section_edges, segment, tol))
    for index, pocket in enumerate(gold["pockets"]):
        b, top, floor = pocket["bounds"], pocket["top_z"], pocket["top_z"] - pocket["depth"]
        target_floor = b + [floor, floor]
        selected = [p for p in planes if same_bounds(p["bounds"], target_floor, tol)
                    and close(abs(p["normal"][2]), 1, at)]
        checks.add("pockets", "pockets.%d.floor" % index, target_floor, union_bounds([p["bounds"] for p in selected]),
                   bool(selected) and abs(sum(p["area"] for p in selected) - (b[1]-b[0])*(b[3]-b[2])) <= tol*(b[1]-b[0]+b[3]-b[2]))
        for j, target in enumerate(([b[0], b[0], b[2], b[3], floor, top], [b[1], b[1], b[2], b[3], floor, top],
                                   [b[0], b[1], b[2], b[2], floor, top], [b[0], b[1], b[3], b[3], floor, top])):
            chosen = [p for p in planes if same_bounds(p["bounds"], target, tol) and close(p["normal"][2], 0, at)]
            checks.add("pockets", "pockets.%d.wall.%d" % (index,j), target, union_bounds([p["bounds"] for p in chosen]), bool(chosen))
        segments = rectangle_segments(b, top) + rectangle_segments(b, floor)
        segments += [((x,y,floor),(x,y,top)) for x in b[:2] for y in b[2:4]]
        checks.add("pockets", "pockets.%d.sharp" % index, True, None,
                   all(covers_segment(edges, segment, tol, True, shape) for segment in segments))
    finish = gold["finish"]
    horizontal = [c for c in cylinders if not same_bounds(c["axis"], [0,0,1], at)]
    oblique = [p for p in planes if sum(abs(v) > at for v in p["normal"]) > 1]
    m["finish_surfaces"] = horizontal + [{"normal": p["normal"], "bounds": p["bounds"]} for p in oblique] + extras
    if finish is None:
        checks.add("finish", "finish.unrequested", [], m["finish_surfaces"], not m["finish_surfaces"])
    else:
        base, size = gold["bbox"], finish["size"]
        checks.add("finish", "finish.unsupported_surfaces", [], extras, not extras)
        for j, (coord, side, boundary) in enumerate(((0,-1,base[0]),(0,1,base[1]),(1,-1,base[2]),(1,1,base[3]))):
            if finish["kind"] == "fillet":
                expected_axis = [0,1,0] if coord == 0 else [1,0,0]
                chosen = [c for c in horizontal if same_bounds(c["axis"], expected_axis, at)
                          and close(c["center"][coord], boundary-side*size, tol)
                          and close(c["center"][2], base[5]-size, tol)
                          and close(c["radius"], size, tol)]
                expected = {"radius": size, "axis": expected_axis, "center_normal": boundary-side*size, "center_z":base[5]-size}
                checks.add("finish", "finish.fillet.%d" % j, expected, chosen[0] if chosen else None, bool(chosen))
            else:
                chosen = []
                for p in oblique:
                    n = p["normal"]
                    if not (close(n[2], math.sqrt(.5), at) and close(n[coord], side*math.sqrt(.5), at)
                            and close(n[1-coord], 0, at)):
                        continue
                    if all(close(side * (vector(v.Point)[coord]-offset[coord]) + v.Point.z-offset[2],
                                 side*boundary+base[5]-size, tol) for v in p["face"].Vertexes):
                        chosen.append(p)
                checks.add("finish", "finish.chamfer.%d" % j, {"leg":size,"angle_degrees":45},
                           union_bounds([p["bounds"] for p in chosen]), bool(chosen))
        checks.add("finish", "finish.kind", finish["kind"], {"cylinders":len(horizontal),"oblique_planes":len(oblique)},
                   (bool(horizontal) and not oblique) if finish["kind"] == "fillet" else (bool(oblique) and not horizontal))
        top = [p["bounds"] for p in planes if same_bounds(p["bounds"][4:6], [base[5],base[5]], tol)]
        expected = [base[0]+size,base[1]-size,base[2]+size,base[3]-size,base[5],base[5]]
        checks.add("finish", "finish.top_bounds", expected, union_bounds(top), same_bounds(union_bounds(top), expected, tol))
    return m


def world_shape(obj):
    shape = obj.Shape
    if hasattr(obj, "getGlobalPlacement"):
        # Feature.Shape includes its local placement; replace it with the global
        # placement so a translated/rotated owning Body cannot evade world gold.
        shape = shape.copy()  # FreeCAD 1.1.4 document Shape properties are immutable.
        shape.Placement = obj.getGlobalPlacement()
    return shape


def editability(doc, body, shape, gold, checks, native_shape=None):
    tol = gold["tolerances"]["linear_mm"]
    bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    tip = body.Tip
    allowed = {"PartDesign::Pad","PartDesign::Pocket","PartDesign::Revolution","PartDesign::Fillet",
               "PartDesign::Chamfer","PartDesign::LinearPattern","PartDesign::MultiTransform"}
    checks.add("editability", "edit.body_count", 1, len(bodies), len(bodies) == 1 and bodies[0] == body)
    checks.add("editability", "edit.tip_native", True, getattr(tip,"TypeId",None),
               tip is not None and tip.TypeId in allowed and tip in body.Group)
    tip_shape = tip.Shape if tip is not None else None
    native_shape = native_shape if native_shape is not None else shape
    checks.add("editability", "edit.tip_solid", True, None if tip_shape is None else len(tip_shape.Solids),
               tip_shape is not None and tip_shape.isValid() and len(tip_shape.Solids) == 1
               and len(native_shape.Solids) == 1 and tip_shape.Solids[0].isSame(native_shape.Solids[0]))
    seen, native, sketches, pending = set(), [], [], [tip] if tip else []
    def links(value):
        if isinstance(value,(list,tuple)):
            for item in value:
                yield from links(item)
        elif hasattr(value,"TypeId"):
            yield value
    while pending:
        obj = pending.pop()
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        if obj.TypeId == "Sketcher::SketchObject":
            sketches.append(obj)
        elif obj.TypeId in allowed:
            native.append(obj)
            for key in ("Profile","BaseFeature","Base","Originals"):
                pending.extend(links(getattr(obj,key,None)))
        else:
            checks.add("editability","edit.native_dependency", True, obj.TypeId, False)
    checks.add("editability","edit.sketch_profiles",True,len(sketches),bool(sketches) and all(s in body.Group for s in sketches))
    for index,obj in enumerate(native):
        if obj.TypeId in ("PartDesign::Pad","PartDesign::Pocket","PartDesign::Revolution"):
            profile = next(links(getattr(obj,"Profile",None)),None)
            checks.add("editability","edit.profile.%d"%index,True,None if profile is None else profile.TypeId,
                       profile is not None and profile in sketches and not profile.Shape.isNull())
    errors = [i for i,o in enumerate(doc.Objects) if any("invalid" in str(s).lower() or "error" in str(s).lower() for s in o.State)]
    checks.add("editability","edit.recompute",[],errors,not errors)
    values = []
    for obj in native:
        for key in ("Length","Radius","Size","Size2"):
            if key in obj.PropertiesList:
                value = getattr(obj,key)
                values.append(abs(float(getattr(value,"Value",value))))
    for sketch in sketches:
        for index,constraint in enumerate(sketch.Constraints):
            if constraint.Type not in ("Distance","DistanceX","DistanceY","Radius","Diameter") or not sketch.getDriving(index):
                continue
            first = constraint.First
            if first >= 0 and first < sketch.GeometryCount and not sketch.getConstruction(first):
                values.append(abs(constraint.Value))
    for index,dimension in enumerate(gold["editability"]["key_dimensions_mm"]):
        matches = [v for v in values if close(v,abs(dimension),tol) or close(v,abs(dimension)/2,tol)]
        checks.add("editability","edit.dimension.%d"%index,{"mm":dimension,"half_allowed":True},
                   matches[0] if matches else None,bool(matches))
    warnings = ["flatface_advice"] if any(str(s.MapMode) != "FlatFace" for s in sketches[1:]) else []
    return {"native_features":len(native),"used_sketches":len(sketches),"driving_dimensions_mm":values},warnings


def probe(doc, body, gold, require_editability=True):
    checks = Checks(gold["case_id"])
    # Body.Shape is a distinct BRep copy in FreeCAD 1.1.4. Probe the native Tip
    # itself: the editability gate binds this exact solid to the one owning Body.
    tip = getattr(body, "Tip", None) if require_editability else None
    shape = world_shape(tip) if tip is not None else body.Shape
    if shape.isNull():
        checks.add("valid_solid","shape.null",False,True,False)
        return {"measurements":{"volume_mm3":None}, "predicates":checks.predicates, "probe_pass":False,
                "geometry_ok":False, "editability_ok":False, "skill_warnings":[], "predicate_details":checks.details()}
    measured = measure_shape(shape,gold,checks)
    geometry_ok = all(checks.predicates.values())
    warnings = []
    if require_editability:
        measured["editability"],warnings = editability(doc,body,shape,gold,checks,
                                                      native_shape=tip.Shape if tip is not None else shape)
    return {"measurements":measured,"predicates":checks.predicates,"probe_pass":all(checks.predicates.values()),
            "geometry_ok":geometry_ok,"editability_ok":checks.predicates.get("editability") if require_editability else None,
            "skill_warnings":warnings,"predicate_details":checks.details(),
            "reference":{"gold_schema":gold["schema"],"volume_mm3":gold["volume"]["target_mm3"]}}
