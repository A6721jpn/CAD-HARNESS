"""Typed geometry validation and deterministic native FreeCAD recipes; no eval data."""
import argparse
import copy
import hashlib
import inspect
import json
import math
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "design/cad-harness-mvp/build-schema.json"
VERSION = "cad-harness.build-spec.v1"
RECIPE_FAMILIES = ("rect_prism", "rect_stack", "stepped_shaft", "top_fillet", "top_chamfer")


def read_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_key:" + key)
            result[key] = value
        return result
    def reject(value):
        raise ValueError("nonfinite_json")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject)


def canonical(spec):
    return json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False)


def schema_check(value, node, schema, path="spec"):
    """Only the JSON-schema keywords used by the shipped build/gold contracts."""
    if "$ref" in node:
        target = schema
        for part in node["$ref"].split("/")[1:]:
            target = target[part]
        schema_check(value, target, schema, path)
        return
    if "oneOf" in node:
        count = 0
        for alternative in node["oneOf"]:
            try:
                schema_check(value, alternative, schema, path)
                count += 1
            except ValueError:
                pass
        if count != 1:
            raise ValueError(path + ":oneOf")
    types = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "number": type(value) in (int, float) and math.isfinite(value),
             "string": isinstance(value, str), "boolean": type(value) is bool,
             "null": value is None}
    if "type" in node and not types.get(node["type"], False):
        raise ValueError(path + ":type")
    if "const" in node and value != node["const"]:
        raise ValueError(path + ":const")
    if "enum" in node and value not in node["enum"]:
        raise ValueError(path + ":enum")
    if isinstance(value, dict):
        properties = node.get("properties", {})
        if any(key not in value for key in node.get("required", [])):
            raise ValueError(path + ":required")
        if node.get("additionalProperties") is False and set(value) - set(properties):
            raise ValueError(path + ":unknown_field")
        for key in value.keys() & properties.keys():
            schema_check(value[key], properties[key], schema, path + "." + key)
    if isinstance(value, list):
        if not node.get("minItems", 0) <= len(value) <= node.get("maxItems", math.inf):
            raise ValueError(path + ":count")
        for index, item in enumerate(value):
            if "items" in node:
                schema_check(item, node["items"], schema, path + "." + str(index))
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError(path + ":finite")
        if "exclusiveMinimum" in node and value <= node["exclusiveMinimum"]:
            raise ValueError(path + ":positive")
        if "minimum" in node and value < node["minimum"]:
            raise ValueError(path + ":minimum")
    for clause in node.get("allOf", []):
        if "if" in clause:
            try:
                schema_check(value, clause["if"], schema, path)
            except ValueError:
                continue
            schema_check(value, clause["then"], schema, path)
        else:
            schema_check(value, clause, schema, path)


def validate_spec(value):
    schema = read_json(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_check(value, schema, schema)
    spec = copy.deepcopy(value)
    scale = {"mm": 1, "cm": 10, "m": 1000}[spec.get("units", "mm")]
    spec.update(units="mm", frame="world")
    for key in ("pockets", "holes"):
        spec.setdefault(key, [])
    spec.setdefault("finish", None)
    for region in spec.get("regions", []):
        region["bounds"] = [n * scale for n in region["bounds"]]
    for step in spec.get("steps", []):
        step.update(diameter=step["diameter"] * scale, z=[n * scale for n in step["z"]])
    if "center_xy" in spec or spec["family"] == "stepped_shaft":
        spec["center_xy"] = [n * scale for n in spec.get("center_xy", [0, 0])]
    for pocket in spec["pockets"]:
        pocket.update(bounds=[n * scale for n in pocket["bounds"]],
                      top_z=pocket["top_z"] * scale, depth=pocket["depth"] * scale)
    for hole in spec["holes"]:
        hole.update(center_xy=[n * scale for n in hole["center_xy"]],
                    diameter=hole["diameter"] * scale, z=[n * scale for n in hole["z"]])
    if spec["finish"]:
        spec["finish"]["size"] *= scale
    schema_check(spec, schema, schema)  # Unit conversion must not overflow to infinity.
    if spec["family"] == "stepped_shaft":
        if "regions" in spec or spec["pockets"] or spec["holes"] or spec["finish"]:
            raise ValueError("unsupported_shaft_operation")
        steps = spec["steps"]
        for index, step in enumerate(steps):
            if step["z"][1] <= step["z"][0] or (index and step["z"][0] != steps[index - 1]["z"][1]):
                raise ValueError("step_interval_or_connection")
        return spec
    if "steps" in spec or "center_xy" in spec:
        raise ValueError("unsupported_rect_field")
    regions = [r["bounds"] for r in spec["regions"]]
    for index, b in enumerate(regions):
        if any(b[i + 1] <= b[i] for i in (0, 2, 4)):
            raise ValueError("region_bounds")
        if index and not any(abs(b[4] - p[5]) < 1e-9 and b[0] >= p[0] and b[1] <= p[1]
                             and b[2] >= p[2] and b[3] <= p[3] for p in regions[:index]):
            raise ValueError("unsupported_region_connection")
    if spec["finish"] and (len(regions) != 1 or spec["finish"]["size"] >=
                          min(regions[0][1] - regions[0][0], regions[0][3] - regions[0][2],
                              regions[0][5] - regions[0][4]) / 2):
        raise ValueError("unsupported_finish")
    for p in spec["pockets"]:
        b = p["bounds"]
        if b[1] <= b[0] or b[3] <= b[2] or not any(
                b[0] > r[0] and b[1] < r[1] and b[2] > r[2] and b[3] < r[3]
                and p["top_z"] == r[5] and p["top_z"] - p["depth"] > r[4] for r in regions):
            raise ValueError("pocket_region")
    for h in spec["holes"]:
        x, y = h["center_xy"]
        radius = h["diameter"] / 2
        if h["z"][1] <= h["z"][0] or not any(
                x - radius > r[0] and x + radius < r[1] and y - radius > r[2] and y + radius < r[3]
                and h["z"] == r[4:6] for r in regions):
            raise ValueError("through_hole_region")
        if any(max(b[0], x - radius) < min(b[1], x + radius)
               and max(b[2], y - radius) < min(b[3], y + radius) for b in [p["bounds"] for p in spec["pockets"]]):
            raise ValueError("unsupported_cut_intersection")
        for r in regions:
            if r[4] >= h["z"][1] and r[0] < x + radius and r[1] > x - radius and r[2] < y + radius and r[3] > y - radius:
                raise ValueError("blocked_hole_opening")
    for index, h in enumerate(spec["holes"]):
        for other in spec["holes"][:index]:
            if math.dist(h["center_xy"], other["center_xy"]) <= (h["diameter"] + other["diameter"]) / 2:
                raise ValueError("overlapping_holes")
    for index, p in enumerate(spec["pockets"]):
        for other in spec["pockets"][:index]:
            a, b = p["bounds"], other["bounds"]
            if max(a[0], b[0]) < min(a[1], b[1]) and max(a[2], b[2]) < min(a[3], b[3]):
                raise ValueError("overlapping_pockets")
    return spec


def loads_spec(text):
    return validate_spec(read_json(text))


def build_native(doc, spec):
    import FreeCAD as App
    import Part
    import Sketcher
    body = doc.addObject("PartDesign::Body", "Model")
    previous = None

    def position(sketch, geometry, point, axis, value):
        if abs(value) < 1e-12:
            sketch.addConstraint(Sketcher.Constraint("PointOnObject", geometry, point, -2 if axis == "X" else -1))
        else:
            sketch.addConstraint(Sketcher.Constraint("Distance" + axis, geometry, point, value))

    def profile(name, z):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.Placement = App.Placement(App.Vector(0, 0, z), App.Rotation())
        return sketch

    def rectangle(sketch, bounds):
        x0, x1, y0, y1 = bounds
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        start = sketch.GeometryCount
        for index, (x, y) in enumerate(corners):
            nx, ny = corners[(index + 1) % 4]
            sketch.addGeometry(Part.LineSegment(App.Vector(x, y, 0), App.Vector(nx, ny, 0)), False)
        for index in range(4):
            sketch.addConstraint(Sketcher.Constraint("Coincident", start + index, 2, start + (index + 1) % 4, 1))
            sketch.addConstraint(Sketcher.Constraint("Horizontal" if index % 2 == 0 else "Vertical", start + index))
        sketch.addConstraint(Sketcher.Constraint("Distance", start, x1 - x0))
        sketch.addConstraint(Sketcher.Constraint("Distance", start + 1, y1 - y0))
        position(sketch, start, 1, "X", x0)
        position(sketch, start, 1, "Y", y0)

    def circle(sketch, center, diameter):
        index = sketch.addGeometry(Part.Circle(App.Vector(center[0], center[1], 0), App.Vector(0, 0, 1), diameter / 2), False)
        sketch.addConstraint(Sketcher.Constraint("Radius", index, diameter / 2))
        position(sketch, index, 3, "X", center[0])
        position(sketch, index, 3, "Y", center[1])

    def extrude(sketch, kind, length, name):
        nonlocal previous
        doc.recompute()
        feature = body.newObject("PartDesign::" + kind, name)
        feature.Profile = sketch
        feature.Length = length
        feature.Type = 0
        feature.Reversed = False
        if "SideType" in feature.PropertiesList:
            feature.SideType = feature.getEnumerationsOfProperty("SideType")[0]
        else:
            feature.Midplane = False
        if previous is not None:
            feature.BaseFeature = previous
        body.Tip = feature
        doc.recompute()
        if feature.Shape.isNull() or not feature.Shape.isValid():
            raise ValueError("native_" + kind + "_failed")
        previous = feature

    if spec["family"] == "stepped_shaft":
        for index, step in enumerate(spec["steps"]):
            sketch = profile("ShaftProfile%d" % index, step["z"][0])
            circle(sketch, spec["center_xy"], step["diameter"])
            extrude(sketch, "Pad", step["z"][1] - step["z"][0], "ShaftPad%d" % index)
    else:
        for index, region in enumerate(spec["regions"]):
            b = region["bounds"]
            sketch = profile("RegionProfile%d" % index, b[4])
            rectangle(sketch, b[:4])
            extrude(sketch, "Pad", b[5] - b[4], "RegionPad%d" % index)
        for index, pocket in enumerate(spec["pockets"]):
            sketch = profile("PocketProfile%d" % index, pocket["top_z"])
            rectangle(sketch, pocket["bounds"])
            extrude(sketch, "Pocket", pocket["depth"], "RectPocket%d" % index)
        for index, hole in enumerate(spec["holes"]):
            sketch = profile("HoleProfile%d" % index, hole["z"][1])
            circle(sketch, hole["center_xy"], hole["diameter"])
            extrude(sketch, "Pocket", hole["z"][1] - hole["z"][0], "ThroughHole%d" % index)
        finish = spec["finish"]
        if finish:
            b = spec["regions"][0]["bounds"]
            selected = []
            for index, edge in enumerate(previous.Shape.Edges, 1):
                points = [v.Point for v in edge.Vertexes]
                if (isinstance(edge.Curve, Part.Line) and len(points) == 2
                        and all(abs(p.z - b[5]) < 1e-6 for p in points)
                        and (any(all(abs(p.x - x) < 1e-6 for p in points) for x in b[:2])
                             or any(all(abs(p.y - y) < 1e-6 for p in points) for y in b[2:4]))):
                    selected.append("Edge%d" % index)
            if len(selected) != 4:
                raise ValueError("four_outer_top_edges_required")
            kind = "Fillet" if finish["kind"] == "fillet" else "Chamfer"
            feature = body.newObject("PartDesign::" + kind, "Top" + kind)
            feature.Base = (previous, selected)
            if kind == "Fillet":
                feature.Radius = finish["size"]
            else:
                feature.Size = finish["size"]
            if "UseAllEdges" in feature.PropertiesList:
                feature.UseAllEdges = False
            body.Tip = feature
            doc.recompute()
            if feature.Shape.isNull() or not feature.Shape.isValid():
                raise ValueError("native_finish_failed")
    doc.recompute()
    return body


def compile_spec(value):
    spec = validate_spec(value)
    source = inspect.getsource(build_native)
    sha = hashlib.sha256(canonical(spec).encode("utf-8")).hexdigest()
    return ('BUILD_SPEC_SHA256 = "' + sha + '"\n' + source +
            "\n_BUILD_SPEC = " + repr(spec) + "\n\ndef build(doc):\n    return build_native(doc, _BUILD_SPEC)\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True, help="New source file; never overwrite")
    args = parser.parse_args(argv)
    spec = loads_spec(Path(args.spec).read_text(encoding="utf-8"))
    with Path(args.out).open("x", encoding="utf-8") as stream:
        stream.write(compile_spec(spec))
    print(canonical({"family": spec["family"], "spec_sha256": hashlib.sha256(canonical(spec).encode()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
