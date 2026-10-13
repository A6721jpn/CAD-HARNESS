"""verify-v2: v1 BRep gates plus proven sketch construction reachability.

No compiler, generator, fixture, case-name or description-SHA lookup.
"""
from collections import deque
import re

if __package__:
    from . import cad_verify_probe as v1
else:
    import cad_verify_probe as v1

load_gold = v1.load_gold
Checks = v1.Checks
RELATIONS = frozenset(("Coincident", "PointOnObject", "Tangent", "Symmetric", "Equal",
    "Distance", "DistanceX", "DistanceY", "Angle", "Perpendicular", "Parallel", "Horizontal", "Vertical"))
DIMENSIONS = frozenset(("Distance", "DistanceX", "DistanceY", "Radius", "Diameter"))
NATIVE = frozenset(("Pad", "Pocket", "Revolution", "Groove", "AdditiveLoft", "SubtractiveLoft",
    "AdditivePipe", "SubtractivePipe", "Fillet", "Chamfer", "Thickness", "LinearPattern",
    "PolarPattern", "MultiTransform", "Mirrored"))
PROFILES = frozenset(("Pad", "Pocket", "Revolution", "Groove", "AdditiveLoft", "SubtractiveLoft",
    "AdditivePipe", "SubtractivePipe"))


def link_items(value):
    if hasattr(value, "TypeId"):
        yield value, ()
    elif isinstance(value, (tuple, list)):
        if (len(value) == 2 and hasattr(value[0], "TypeId")
                and isinstance(value[1], (tuple, list)) and all(isinstance(s, str) for s in value[1])):
            yield value[0], tuple(value[1])
        else:
            for item in value:
                yield from link_items(item)


def selected_geometry(sketch, subnames):
    real = [i for i in range(sketch.GeometryCount) if not sketch.getConstruction(i)]
    if not subnames or all(s == "" for s in subnames):
        return real
    selected = set()
    for sub in subnames:
        if not re.fullmatch(r"Edge[1-9][0-9]*", sub):
            raise ValueError("unsupported_verify_v2_sketch_selection")
        edge = sketch.getSubObject(sub, transform=False)
        matches = []
        for i in real:
            candidate = sketch.Geometry[i].toShape()
            if (len(candidate.Edges) == 1 and len(edge.Edges) == 1
                    and candidate.Edges[0].Curve.isSame(edge.Edges[0].Curve, 1e-7, 1e-7)
                    and abs(candidate.Length-edge.Length) < 1e-7
                    and v1.same_bounds(v1.bounds(candidate), v1.bounds(edge), 1e-7)):
                matches.append(i)
        if len(matches) != 1:
            raise ValueError("unsupported_verify_v2_ambiguous_geometry")
        selected.add(matches[0])
    return sorted(selected)


def references(constraint, count):
    return sorted({i for name in ("First", "Second", "Third")
                   if type(i := getattr(constraint, name, -1)) is int and 0 <= i < count})


def reachable(sketch, seeds):
    """Negative axes/origins never become shared graph hubs."""
    graph = {i: [] for i in range(sketch.GeometryCount)}
    for index, constraint in enumerate(sketch.Constraints):
        if (constraint.Type not in RELATIONS or not sketch.getActive(index)
                or not constraint.Driving):
            continue
        ids = references(constraint, sketch.GeometryCount)
        for first in ids:
            for second in ids:
                if first != second:
                    graph[first].append((second, index, constraint.Type))
    paths = {i: path for i, path in seeds.items()}
    todo = deque(sorted(paths))
    while todo:
        first = todo.popleft()
        for second, index, kind in graph[first]:
            if second not in paths:
                paths[second] = paths[first] + [{"constraint": index, "type": kind, "geometry": second}]
                todo.append(second)
    return paths


def editability(doc, body, shape, gold, checks, native_shape=None):
    allowed = {"PartDesign::"+name for name in NATIVE}
    profiles = {"PartDesign::"+name for name in PROFILES}
    tip = getattr(body, "Tip", None)
    bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    checks.add("editability", "edit.body", 1, len(bodies), len(bodies) == 1 and bodies[0] == body)
    checks.add("editability", "edit.native_tip", True, getattr(tip, "TypeId", None),
               tip is not None and tip.TypeId in allowed and tip in body.Group)
    ts = getattr(tip, "Shape", None)
    ns = native_shape if native_shape is not None else shape
    same = ts is not None and ts.isValid() and len(ts.Solids) == 1 and len(ns.Solids) == 1 and ts.Solids[0].isSame(ns.Solids[0])
    checks.add("editability", "edit.tip_solid", True, same, same)
    todo, seen, native, sketches, seeds = ([tip] if tip else []), set(), [], [], {}
    while todo:
        obj = todo.pop()
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        checks.add("editability", "edit.used_member."+str(len(seen)), True, obj in body.Group, obj in body.Group)
        if obj.TypeId == "Sketcher::SketchObject":
            sketches.append(obj)
            continue
        if obj.TypeId not in allowed:
            checks.add("editability", "edit.unsupported_dependency", True, obj.TypeId, False)
            continue
        native.append(obj)
        if obj.TypeId in profiles:
            used = list(link_items(getattr(obj, "Profile", None)))
            ok = len(used) == 1 and used[0][0].TypeId == "Sketcher::SketchObject" and not used[0][0].Shape.isNull()
            checks.add("editability", "edit.used_profile."+str(len(native)), True, ok, ok)
        for key in ("Profile", "BaseFeature", "Base", "Originals", "Sections", "Spine", "AuxiliarySpine"):
            for linked, subnames in link_items(getattr(obj, key, None)):
                todo.append(linked)
                if linked.TypeId == "Sketcher::SketchObject":
                    found = seeds.setdefault(linked.Name, {})
                    for i in selected_geometry(linked, subnames):
                        found.setdefault(i, [{"feature": obj.Name, "link": key, "subnames": list(subnames),
                                              "sketch": linked.Name, "geometry": i}])
        ref = getattr(obj, "ReferenceAxis", None)
        if ref and isinstance(ref, (tuple, list)) and len(ref) == 2 and getattr(ref[0], "TypeId", None) == "Sketcher::SketchObject":
            s = ref[0]
            todo.append(s)
            construction = [i for i in range(s.GeometryCount) if s.getConstruction(i)]
            for sub in ref[1]:
                axis = 0 if sub == "Axis" and len(construction) == 1 else (
                    int(sub[4:]) if sub.startswith("Axis") and sub[4:].isdigit() else -1)
                if 0 <= axis < len(construction):
                    i = construction[axis]
                    seeds.setdefault(s.Name, {}).setdefault(i, [{"feature": obj.Name, "link": "ReferenceAxis",
                        "subnames": [sub], "sketch": s.Name, "geometry": i}])
    checks.add("editability", "edit.consumed_sketch", True, len(sketches), bool(sketches))
    errors = [i for i, o in enumerate(doc.Objects) if any("error" in str(v).lower() or "invalid" in str(v).lower() for v in o.State)]
    checks.add("editability", "edit.clean_recompute", [], errors, not errors)
    native_valid = checks.predicates.get("editability") is True
    values, evidence = [], []
    for obj in native:
        for key in ("Length", "Length2", "Radius", "Size", "Size2"):
            if key in obj.PropertiesList:
                value = getattr(obj, key)
                value = abs(float(value.Value if hasattr(value, "Value") else value))
                values.append(value)
                evidence.append({"value_mm": value, "feature": obj.Name, "property": key})
    for s in sketches:
        values.extend(abs(v) for v in v1.vector(s.Placement.Base))
        paths = reachable(s, seeds.get(s.Name, {}))
        for i, c in enumerate(s.Constraints):
            ids = references(c, s.GeometryCount)
            if (c.Type in DIMENSIONS and s.getActive(i) and s.getDriving(i)
                    and ids and all(geo in paths for geo in ids)):
                value = abs(float(c.Value))
                values.append(value)
                evidence.append({"value_mm": value, "sketch": s.Name, "constraint": i, "type": c.Type,
                                 "geometry": ids, "paths": [paths[geo] for geo in ids]})
    for i, dimension in enumerate(gold["editability"]["key_dimensions_mm"]):
        found = next((v for v in values if v1.close(v, dimension, .01) or v1.close(v, dimension/2, .01)), None)
        checks.add("editability", "edit.driving_dimension.%d" % i, dimension, found, found is not None)
    return {"native_features": len(native), "used_sketches": len(sketches), "native_valid": native_valid,
            "driving_dimensions_mm": values, "dimension_evidence": evidence}, [
                "flatface_advice"] if any(str(s.MapMode) != "FlatFace" for s in sketches[1:]) else []


def probe(doc, body, gold, require_editability=True):
    checks = Checks(gold["case_id"])
    tip = getattr(body, "Tip", None) if require_editability else None
    shape = v1.world_shape(tip) if tip is not None else body.Shape
    if shape.isNull():
        checks.add("valid_solid", "shape.null", False, True, False)
        return dict(measurements={"volume_mm3": None}, predicates=checks.predicates, probe_pass=False,
                    geometry_ok=False, editability_ok=False, skill_warnings=[], predicate_details=checks.details())
    measured = v1.measure_shape(shape, gold, checks)
    geometry, warnings = all(checks.predicates.values()), []
    if require_editability:
        measured["editability"], warnings = editability(doc, body, shape, gold, checks, native_shape=tip.Shape if tip else shape)
    return dict(measurements=measured, predicates=checks.predicates, probe_pass=all(checks.predicates.values()),
                geometry_ok=geometry, editability_ok=checks.predicates.get("editability") if require_editability else None,
                skill_warnings=warnings, predicate_details=checks.details(),
                reference={"gold_schema": gold["schema"], "volume_mm3": gold["volume"]["target_mm3"],
                           "volume_scope": gold.get("volume_scope"), "probe_profile": "verify-v2"})
