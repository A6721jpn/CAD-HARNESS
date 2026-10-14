"""Deterministic, explicit-policy PNG contours; numerical dependencies are lazy.

Pixels occupy closed unit cells, not an interpolated marching-squares isovalue.
No foreground, alpha, scale, smoothing or acceptance policy is inferred.  Circular
fillets replace corners geometrically; radius reports never certify topology.

Supported inputs are single-frame, 1-/8-bit PNGs, at most 16,777,216 pixels,
1,000,000 exposed cell edges and 8192 canonical segments. Resource and
floating-point resolution failures are refusals, never topology repair.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

try:
    from .cad_verify_v4_ledger import file_sha, new_directory, write_json
except ImportError:
    from cad_verify_v4_ledger import file_sha, new_directory, write_json

SCHEMA = "cad-harness.contour.v4c"
RECIPE_SCHEMA = "cad-harness.contour-recipe.v4c"
TAU = 2 * math.pi

MAX_PIXELS = 16_777_216
MAX_BOUNDARY_SEGMENTS = 8192
MAX_CELL_EDGES = 1_000_000
DEVIATION_METHOD = "two-sided polygonal distance samples plus half maximum sample gap plus curve approximation bound and floating-point allowance; distance is 1-Lipschitz"

def _fail(reason):
    raise ValueError("contour_" + reason)


def _hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _fields(value, required, optional=()):
    if not isinstance(value, dict) or set(required) - value.keys() or set(value) - set(required) - set(optional):
        _fail("missing_or_unknown_fields")


def _number(value, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail("nonfinite_number")
    if positive and value <= 0 or nonnegative and value < 0:
        _fail("number_out_of_range")
    return float(value)


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        _fail("invalid_point")
    return [_number(value[0]), _number(value[1])]


def _add(a, b):
    return [a[0] + b[0], a[1] + b[1]]


def _sub(a, b):
    return [a[0] - b[0], a[1] - b[1]]


def _mul(a, t):
    return [a[0] * t, a[1] * t]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _unit(a):
    length = math.hypot(*a)
    if not length:
        _fail("zero_length_segment")
    return _mul(a, 1 / length)


def validate_recipe(recipe):
    _fields(recipe, ("schema", "profile", "foreground", "alpha", "scale", "simplify", "rounding", "limits", "topology"))
    if recipe["schema"] != RECIPE_SCHEMA or recipe["profile"] != "c-s1":
        _fail("recipe_schema")
    fg = recipe["foreground"]
    _fields(fg, ("channel", "polarity", "threshold"))
    if fg["channel"] not in ("luminance", "red", "green", "blue", "alpha") or fg["polarity"] not in ("dark", "light"):
        _fail("foreground_policy")
    if not 0 <= _number(fg["threshold"]) <= 255:
        _fail("threshold_range")
    alpha = recipe["alpha"]
    _fields(alpha, ("policy",), ("threshold",))
    if alpha["policy"] not in ("ignore", "require-opaque", "threshold"):
        _fail("alpha_policy")
    if alpha["policy"] == "threshold":
        if "threshold" not in alpha or not 0 <= _number(alpha["threshold"]) <= 255:
            _fail("alpha_threshold")
    elif "threshold" in alpha:
        _fail("unused_alpha_threshold")
    _fields(recipe["scale"], ("mm_per_pixel", "origin_mm"))
    _number(recipe["scale"]["mm_per_pixel"], positive=True)
    _point(recipe["scale"]["origin_mm"])
    for name, quantity in (("simplify", "tolerance_mm"), ("rounding", "radius_mm")):
        section = recipe[name]
        _fields(section, ("allowed",), (quantity,))
        if not isinstance(section["allowed"], bool):
            _fail("permission_not_boolean")
        if section["allowed"]:
            if quantity not in section:
                _fail("missing_" + quantity)
            _number(section[quantity], positive=True)
        elif quantity in section:
            _fail("unapproved_" + name)
    _fields(recipe["limits"], ("max_deviation_mm", "approximation_tolerance_mm"))
    _number(recipe["limits"]["max_deviation_mm"], nonnegative=True)
    _number(recipe["limits"]["approximation_tolerance_mm"], positive=True)
    _fields(recipe["topology"], ("components", "holes", "islands"))
    if type(recipe["topology"]["components"]) is not int or recipe["topology"] != {"components": 1, "holes": "preserve", "islands": "reject"}:
        _fail("one_solid_policy_incompatible")
    return recipe


def segment_endpoints(segment):
    if not isinstance(segment, dict):
        _fail("invalid_segment")
    kind = segment.get("kind")
    if kind == "line":
        _fields(segment, ("kind", "p0", "p1"))
    elif kind == "arc":
        _fields(segment, ("kind", "p0", "pm", "p1"))
        _point(segment["pm"])
    elif kind == "bezier":
        _fields(segment, ("kind", "poles"))
        poles = segment["poles"]
        if not isinstance(poles, list) or len(poles) not in (3, 4):
            _fail("unsupported_bezier_degree")
        for p in poles:
            _point(p)
        return _point(poles[0]), _point(poles[-1])
    else:
        _fail("unsupported_segment")
    return _point(segment["p0"]), _point(segment["p1"])


def arc_geometry(segment):
    """Circumcircle and directed sweep passing through the supplied midpoint."""
    p0, p1 = segment_endpoints(segment)
    if segment["kind"] != "arc":
        _fail("not_arc")
    pm = _point(segment["pm"])
    u, v = _sub(pm, p0), _sub(p1, p0)
    determinant = 2 * _cross(u, v)
    scale = max(math.hypot(*u), math.hypot(*v))
    if not scale or abs(determinant) <= 1e-14 * scale * scale:
        _fail("degenerate_arc")
    uu, vv = _dot(u, u), _dot(v, v)
    center = _add(p0, [(uu * v[1] - vv * u[1]) / determinant,
                       (u[0] * vv - v[0] * uu) / determinant])
    radius = _distance(center, p0)
    a0 = math.atan2(p0[1] - center[1], p0[0] - center[0])
    am = math.atan2(pm[1] - center[1], pm[0] - center[0])
    a1 = math.atan2(p1[1] - center[1], p1[0] - center[0])
    positive = (a1 - a0) % TAU
    sweep = positive if (am - a0) % TAU < positive else positive - TAU
    if not radius or not sweep or not math.isfinite(radius):
        _fail("degenerate_arc")
    return {"center": center, "radius": radius, "start_angle": a0, "sweep": sweep}


def _segment_flatten(segment, tolerance):
    p0, p1 = segment_endpoints(segment)
    if segment["kind"] == "line":
        if p0 == p1:
            _fail("zero_length_segment")
        return [p0, p1], 0.0
    if segment["kind"] == "arc":
        g = arc_geometry(segment)
        u, v = _sub(segment["pm"], p0), _sub(p1, p0)
        condition = max(1.0, max(_dot(u, u), _dot(v, v)) / abs(2 * _cross(u, v)))
        magnitude = max(abs(c) for c in (*g["center"], g["radius"]))
        numeric = 128 * math.ulp(magnitude) * condition
        if tolerance <= numeric:
            _fail("approximation_below_numeric_resolution")
        # 1-cos(theta/2) <= theta**2/8. Reserve a conservative floating-point
        # allowance for the circumcircle solve and trig coordinates.
        angle = min(math.pi / 2, math.sqrt(8 * (tolerance - numeric) / g["radius"]))
        if angle <= 0:
            _fail("approximation_underflow")
        count = max(1, math.ceil(abs(g["sweep"]) / angle))
        if count > 1000000:
            _fail("approximation_limit")
        step = g["sweep"] / count
        pts = [p0]
        for i in range(1, count):
            a = g["start_angle"] + i * step
            pts.append(_add(g["center"], [g["radius"] * math.cos(a), g["radius"] * math.sin(a)]))
        pts.append(p1)
        return pts, g["radius"] * step * step / 8 + numeric
    # Bezier lies in its control hull. Linear interpolation with the same
    # parameter differs from the curve by at most the largest pole-to-
    # corresponding-chord-control displacement. De Casteljau subdivision
    # gives a two-sided parameterwise bound, including reversing curves.
    result, largest = [p0], 0.0
    magnitude = max(abs(c) for p in segment["poles"] for c in p)
    numeric = 128 * math.ulp(magnitude)
    if tolerance <= numeric:
        _fail("approximation_below_numeric_resolution")
    stack = [(segment["poles"], 0)]
    leaves = 0
    while stack:
        poles, depth = stack.pop()
        n = len(poles) - 1
        error = max(_distance(poles[i], _add(poles[0], _mul(_sub(poles[-1], poles[0]), i / n))) for i in range(n + 1)) + numeric * (depth + 1)
        if error <= tolerance:
            result.append(list(poles[-1]))
            largest = max(largest, error)
            leaves += 1
            if leaves > 1000000:
                _fail("approximation_limit")
            continue
        if depth >= 48:
            _fail("approximation_limit")
        levels = [poles]
        while len(levels[-1]) > 1:
            prev = levels[-1]
            levels.append([_mul(_add(prev[i], prev[i + 1]), .5) for i in range(len(prev) - 1)])
        left = [level[0] for level in levels]
        right = [level[-1] for level in reversed(levels)]
        stack.append((right, depth + 1))
        stack.append((left, depth + 1))
    return result, largest


def flatten_loops(record, tolerance_mm):
    """Return (closed XY rings, maximum two-sided chord error in millimetres).

    Ordering matches record['loops']; the function also accepts text-outline
    records containing quadratic/cubic Beziers. It never imports FreeCAD.
    """
    tolerance = _number(tolerance_mm, positive=True)
    loops = record.get("loops") if isinstance(record, dict) else None
    if not isinstance(loops, list) or not loops:
        _fail("missing_loops")
    rings, bound = [], 0.0
    for loop in loops:
        segments = loop.get("segments")
        if not isinstance(segments, list) or not segments:
            _fail("empty_loop")
        points = []
        for segment in segments:
            pts, error = _segment_flatten(segment, tolerance)
            if points and points[-1] != pts[0]:
                _fail("disconnected_segments")
            points.extend(pts if not points else pts[1:])
            bound = max(bound, error)
        if points[-1] != points[0]:
            _fail("open_loop")
        rings.append(points)
    return rings, bound


def _tangent(segment, end):
    p0, p1 = segment_endpoints(segment)
    if segment["kind"] == "line":
        return _unit(_sub(p1, p0))
    if segment["kind"] != "arc":
        _fail("minimum_radius_bezier_requires_curvature_solver")
    g = arc_geometry(segment)
    v = _sub(p1 if end else p0, g["center"])
    sign = 1 if g["sweep"] > 0 else -1
    return _unit([-sign * v[1], sign * v[0]])


def _tangent_numeric_allowance(segment):
    p0, p1 = segment_endpoints(segment)
    magnitude = max(abs(c) for p in (p0, p1) for c in p)
    length = _distance(p0, p1)
    condition = 1.0
    if segment["kind"] == "arc":
        g = arc_geometry(segment)
        u, v = _sub(segment["pm"], p0), _sub(p1, p0)
        condition = max(1.0, max(_dot(u, u), _dot(v, v)) / abs(2 * _cross(u, v)))
        magnitude = max(magnitude, *(abs(c) for c in g["center"]), g["radius"])
        length = min(length, g["radius"])
    if not length:
        _fail("zero_length_segment")
    allowance = 256 * math.ulp(magnitude) * condition / length
    if not math.isfinite(allowance) or allowance >= 1e-4:
        _fail("radius_below_numeric_resolution")
    return allowance


def minimum_radius(record):
    """Actual circular radii plus every join; a non-tangent corner has radius 0.

    Infinity denotes exclusively tangent straight segments, not a finite
    certificate. Join comparisons use a coordinate/circle-conditioning-derived
    floating-point allowance, not an acceptance angle. No report is consulted.
    """
    result = math.inf
    for loop in record["loops"]:
        segments = loop["segments"]
        for i, segment in enumerate(segments):
            if segment["kind"] == "arc":
                result = min(result, arc_geometry(segment)["radius"])
            before, after = _tangent(segments[i - 1], True), _tangent(segment, False)
            allowance = _tangent_numeric_allowance(segments[i - 1]) + _tangent_numeric_allowance(segment)
            if abs(_cross(before, after)) > allowance or _dot(before, after) <= 0:
                return 0.0
    return result


def _area(points):
    return sum(_cross(a, b) for a, b in zip(points, points[1:])) / 2


def _line_loop(points, role, parent=None):
    result = {"role": role, "segments": [{"kind": "line", "p0": a, "p1": b} for a, b in zip(points, points[1:])]}
    if role == "hole":
        result["parent"] = parent
    return result


def _mask_loops(mask, scale, origin):
    """Trace the exact cell union. Degree != 2 refuses diagonal contacts."""
    height, width = mask.shape
    successors = {}
    def edge(a, b):
        if a in successors:
            _fail("nonmanifold_pixel_contact")
        successors[a] = b
        if len(successors) > MAX_CELL_EDGES:
            _fail("exposed_cell_edge_limit")
    ys, xs = mask.nonzero()
    for y, x in zip(ys.tolist(), xs.tolist()):
        bottom, top = height - y - 1, height - y
        if y == 0 or not mask[y - 1, x]:
            edge((x + 1, top), (x, top))
        if x == 0 or not mask[y, x - 1]:
            edge((x, top), (x, bottom))
        if y == height - 1 or not mask[y + 1, x]:
            edge((x, bottom), (x + 1, bottom))
        if x == width - 1 or not mask[y, x + 1]:
            edge((x + 1, bottom), (x + 1, top))
    if not successors:
        _fail("empty_mask")
    if set(successors) != set(successors.values()):
        _fail("nonmanifold_mask")
    rings = []
    while successors:
        start = min(successors)
        pts, current = [], start
        while True:
            pts.append(current)
            current = successors.pop(current)
            if current == start:
                break
            if current not in successors:
                _fail("nonmanifold_mask")
        keep = [p for i, p in enumerate(pts) if _cross(_sub(p, pts[i - 1]), _sub(pts[(i + 1) % len(pts)], p)) != 0]
        # Canonical start is lexicographically smallest geometric vertex.
        index = min(range(len(keep)), key=lambda i: keep[i])
        keep = keep[index:] + keep[:index]
        ring = [[origin[0] + p[0] * scale, origin[1] + p[1] * scale] for p in keep]
        ring.append(ring[0])
        rings.append(ring)
    outer = sorted((r for r in rings if _area(r) > 0), key=lambda r: r[0])
    holes = sorted((r for r in rings if _area(r) < 0), key=lambda r: r[0])
    if len(outer) != 1:
        _fail("multiple_islands_one_solid_refused")
    return [_line_loop(outer[0], "outer")] + [_line_loop(r, "hole", 0) for r in holes]


def _polygon(rings):
    from shapely.geometry import Polygon
    polygon = Polygon(rings[0], rings[1:])
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
        _fail("invalid_or_changed_topology")
    return polygon


def _round_loop(loop, radius):
    vertices = [segment["p0"] for segment in loop["segments"]]
    entry, exit_, arcs = [], [], []
    for i, v in enumerate(vertices):
        incoming = _unit(_sub(v, vertices[i - 1]))
        outgoing = _unit(_sub(vertices[(i + 1) % len(vertices)], v))
        turn = math.atan2(_cross(incoming, outgoing), _dot(incoming, outgoing))
        if abs(turn) < 1e-12 or math.pi - abs(turn) < 1e-12:
            _fail("unsupported_rounding_corner")
        trim = radius * math.tan(abs(turn) / 2)
        q0, q1 = _sub(v, _mul(incoming, trim)), _add(v, _mul(outgoing, trim))
        sign = 1 if turn > 0 else -1
        center = _add(q0, [-sign * incoming[1] * radius, sign * incoming[0] * radius])
        a0 = math.atan2(q0[1] - center[1], q0[0] - center[0])
        pm = _add(center, [radius * math.cos(a0 + turn / 2), radius * math.sin(a0 + turn / 2)])
        entry.append(q0)
        exit_.append(q1)
        arcs.append({"kind": "arc", "p0": q0, "pm": pm, "p1": q1})
    segments = []
    for i in range(len(vertices)):
        nxt = (i + 1) % len(vertices)
        direction = _unit(_sub(vertices[nxt], vertices[i]))
        remaining = _dot(_sub(entry[nxt], exit_[i]), direction)
        if remaining <= max(radius, _distance(vertices[i], vertices[nxt])) * 1e-12:
            _fail("rounding_radius_does_not_fit")
        segments.append(arcs[i])
        segments.append({"kind": "line", "p0": exit_[i], "p1": entry[nxt]})
    return dict(loop, segments=segments)


def _bezier_at(poles, t):
    level = [list(p) for p in poles]
    while len(level) > 1:
        level = [_add(_mul(a, 1 - t), _mul(b, t)) for a, b in zip(level, level[1:])]
    return level[0]


def _quadratic_roots(a, b, c):
    if a == 0:
        return [] if b == 0 else [-c / b]
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return []
    q = -.5 * (b + math.copysign(math.sqrt(discriminant), b))
    return [-b / (2 * a)] if q == 0 else [q / a, c / q]


def _geometry_bounds(loops):
    points = []
    for loop in loops:
        for segment in loop["segments"]:
            p0, p1 = segment_endpoints(segment)
            points.extend((p0, p1))
            if segment["kind"] == "arc":
                g = arc_geometry(segment)
                for angle in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
                    distance = ((angle - g["start_angle"]) % TAU if g["sweep"] > 0 else (g["start_angle"] - angle) % TAU)
                    if distance <= abs(g["sweep"]):
                        points.append(_add(g["center"], [g["radius"] * math.cos(angle), g["radius"] * math.sin(angle)]))
            elif segment["kind"] == "bezier":
                poles = segment["poles"]
                for axis in (0, 1):
                    values = [p[axis] for p in poles]
                    if len(values) == 3:
                        a = 2 * (values[0] - 2 * values[1] + values[2])
                        roots = [] if a == 0 else [-2 * (values[1] - values[0]) / a]
                    else:
                        roots = _quadratic_roots(
                            3 * (-values[0] + 3 * values[1] - 3 * values[2] + values[3]),
                            6 * (values[0] - 2 * values[1] + values[2]),
                            3 * (values[1] - values[0]))
                    points.extend(_bezier_at(poles, t) for t in roots if 0 < t < 1)
    return [min(p[0] for p in points), max(p[0] for p in points), min(p[1] for p in points), max(p[1] for p in points)]


def _boundary_bound(a, b, step):
    """Certified two-sided polygonal Hausdorff upper bound via 1-Lipschitz distance."""
    from shapely.geometry import MultiLineString, Point
    aa = MultiLineString(a)
    bb = MultiLineString(b)
    def direction(rings, target):
        maximum, gap = 0.0, 0.0
        count_total = 0
        for ring in rings:
            for p, q in zip(ring, ring[1:]):
                length = _distance(p, q)
                count = max(1, math.ceil(length / step))
                count_total += count
                if count_total > 2000000:
                    _fail("boundary_evidence_limit")
                gap = max(gap, length / count)
                for i in range(count + 1):
                    sample = _add(p, _mul(_sub(q, p), i / count))
                    maximum = max(maximum, target.distance(Point(sample)))
        return maximum + gap / 2
    magnitude = max(abs(c) for rings in (a, b) for ring in rings for p in ring for c in p)
    return max(direction(a, bb), direction(b, aa)) + 128 * math.ulp(magnitude)


def _topology(loops):
    return {"components": sum(l["role"] == "outer" for l in loops),
            "holes": sum(l["role"] == "hole" for l in loops),
            "euler_characteristic": sum(1 if l["role"] == "outer" else -1 for l in loops)}


def _curve_projection_range(segment, origin, normal):
    p0, p1 = segment_endpoints(segment)
    points = [p0, p1]
    if segment["kind"] == "bezier":
        # A linear functional on the Bezier is bounded by its control hull.
        points = segment["poles"]
    elif segment["kind"] == "arc":
        g = arc_geometry(segment)
        angle = math.atan2(normal[1], normal[0])
        for a in (angle, angle + math.pi):
            offset = (a - g["start_angle"]) % TAU if g["sweep"] > 0 else (g["start_angle"] - a) % TAU
            if offset <= abs(g["sweep"]):
                points.append(_add(g["center"], [g["radius"] * math.cos(a), g["radius"] * math.sin(a)]))
    values = [_dot(_sub(p, origin), normal) for p in points]
    return min(values), max(values)


def _curve_midpoint(segment):
    p0, p1 = segment_endpoints(segment)
    if segment["kind"] == "bezier":
        return _bezier_at(segment["poles"], .5)
    if segment["kind"] == "arc":
        g = arc_geometry(segment)
        angle = g["start_angle"] + g["sweep"] / 2
        return _add(g["center"], [g["radius"] * math.cos(angle), g["radius"] * math.sin(angle)])
    return _mul(_add(p0, p1), .5)


def _certify_adjacent(a, b):
    """Separate incident curves by a supporting half-plane at their join.

    This is conservative: pathological valid curves may be refused rather
    than have unproved topology inferred from a fine-looking chord polygon.
    Bezier control hulls and exact circular extrema bound the whole curves.
    """
    a0, join = segment_endpoints(a)
    b0, b1 = segment_endpoints(b)
    if b0 != join:
        _fail("disconnected_segments")
    da, db = _sub(join, a0), _sub(b1, join)
    candidates = [_sub(_curve_midpoint(b), _curve_midpoint(a)), _add(_unit(da), _unit(db)),
                  [-da[1], da[0]], [-db[1], db[0]], da, db]
    magnitude = max(abs(c) for p in (a0, join, b1) for c in p)
    numeric = 256 * math.ulp(magnitude)
    for candidate in candidates:
        if math.hypot(*candidate) == 0:
            continue
        normal = _unit(candidate)
        amin, amax = _curve_projection_range(a, join, normal)
        bmin, bmax = _curve_projection_range(b, join, normal)
        if max(amax - amin, bmax - bmin) <= numeric:
            continue
        if amax <= numeric and bmin >= -numeric or bmax <= numeric and amin >= -numeric:
            return
    _fail("adjacent_curve_topology_not_certified")


def _certify_bezier_simple(segment):
    poles = segment["poles"]
    chord = _unit(_sub(poles[-1], poles[0]))
    derivatives = [_dot(_sub(b, a), chord) for a, b in zip(poles, poles[1:])]
    # Positive Bernstein derivative on the open interval => injectivity.
    if min(derivatives) < 0 or max(derivatives) <= 0:
        _fail("bezier_topology_not_certified")


def _check_geometry(loops, tolerance):
    from shapely.geometry import LineString
    from shapely.strtree import STRtree
    if sum(len(loop["segments"]) for loop in loops) > MAX_BOUNDARY_SEGMENTS:
        _fail("boundary_complexity_limit")
    if not loops or loops[0]["role"] != "outer" or any(l["role"] != "hole" or l.get("parent") != 0 for l in loops[1:]):
        _fail("unsupported_loop_nesting")
    rings, error = flatten_loops({"loops": loops}, tolerance)
    for loop, ring in zip(loops, rings):
        if (_area(ring) > 0) != (loop["role"] == "outer"):
            _fail("loop_orientation")
    _polygon(rings)
    # Distinct boundaries must be separated by their full chord-error
    # envelopes; approximation validity alone is not a topology certificate.
    lines = [LineString(r) for r in rings]
    ring_tree = STRtree(lines)
    for i, line in enumerate(lines):
        for j in ring_tree.query(line, predicate="dwithin", distance=2 * error):
            if j > i:
                _fail("topology_approximation_not_separated")
    for loop in loops:
        for i, segment in enumerate(loop["segments"]):
            if segment["kind"] == "bezier":
                _certify_bezier_simple(segment)
            _certify_adjacent(segment, loop["segments"][(i + 1) % len(loop["segments"])])
        parts = [_segment_flatten(s, tolerance) for s in loop["segments"]]
        segment_lines = [LineString(p) for p, _ in parts]
        maximum_error = max(e for _, e in parts)
        tree = STRtree(segment_lines)
        for i, (line, (_, ep)) in enumerate(zip(segment_lines, parts)):
            for index in tree.query(line, predicate="dwithin", distance=ep + maximum_error):
                j = int(index)
                if j <= i or j == i + 1 or i == 0 and j == len(parts) - 1:
                    continue
                if line.distance(segment_lines[j]) <= ep + parts[j][1]:
                    _fail("self_contact_or_uncertain_topology")
    return rings, error


def _decode(path, recipe):
    import numpy as np
    from PIL import Image
    with Image.open(path) as image:
        if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
            _fail("unsupported_image_format")
        if image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA"):
            _fail("unsupported_image_sample_depth")
        if image.width * image.height > MAX_PIXELS:
            _fail("image_pixel_limit")
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    # Integer Rec.601 luma, specified here and in provenance (not gamma-linear).
    channel = recipe["foreground"]["channel"]
    if channel == "luminance":
        rgb = rgba[:, :, :3].astype(np.uint32)
        values = (299 * rgb[:, :, 0] + 587 * rgb[:, :, 1] + 114 * rgb[:, :, 2] + 500) // 1000
    else:
        values = rgba[:, :, {"red": 0, "green": 1, "blue": 2, "alpha": 3}[channel]]
    threshold = recipe["foreground"]["threshold"]
    mask = values <= threshold if recipe["foreground"]["polarity"] == "dark" else values >= threshold
    alpha = recipe["alpha"]
    if alpha["policy"] == "require-opaque" and not np.all(rgba[:, :, 3] == 255):
        _fail("nonopaque_image")
    if alpha["policy"] == "threshold":
        mask &= rgba[:, :, 3] >= alpha["threshold"]
    return mask, hashlib.sha256(rgba.tobytes(order="C")).hexdigest()


def _mask_record(mask):
    rows = []
    for row in mask:
        runs, start = [], None
        for i, value in enumerate(row.tolist()):
            if value and start is None:
                start = i
            elif not value and start is not None:
                runs.append([start, i])
                start = None
        if start is not None:
            runs.append([start, len(row)])
        rows.append(runs)
    return {"width": int(mask.shape[1]), "height": int(mask.shape[0]), "encoding": "row-runs", "rows": rows}


def _processed_loops(source, recipe):
    """Single deterministic reconstruction used by preparation and admission."""
    loops = source
    if recipe["simplify"]["allowed"]:
        rings, _ = flatten_loops({"loops": source}, recipe["limits"]["approximation_tolerance_mm"])
        poly = _polygon(rings)
        reduced = poly.simplify(recipe["simplify"]["tolerance_mm"], preserve_topology=True)
        if reduced.geom_type != "Polygon" or len(reduced.interiors) != len(poly.interiors):
            _fail("simplification_topology_changed")
        from shapely.geometry.polygon import orient
        reduced = orient(reduced, sign=1.0)
        rings = [list(map(list, reduced.exterior.coords))] + [list(map(list, r.coords)) for r in reduced.interiors]
        canonical = []
        for ring in rings:
            vertices = ring[:-1]
            vertices = [v for i, v in enumerate(vertices)
                        if _cross(_sub(v, vertices[i - 1]), _sub(vertices[(i + 1) % len(vertices)], v)) != 0]
            if len(vertices) < 3:
                _fail("simplification_degenerate")
            start = min(range(len(vertices)), key=lambda i: vertices[i])
            vertices = vertices[start:] + vertices[:start]
            canonical.append(vertices + [vertices[0]])
        canonical[1:] = sorted(canonical[1:], key=lambda r: r[0])
        loops = [_line_loop(r, "outer" if i == 0 else "hole", 0) for i, r in enumerate(canonical)]
    if recipe["rounding"]["allowed"]:
        loops = [_round_loop(loop, recipe["rounding"]["radius_mm"]) for loop in loops]
    return loops


def _deviation(source, loops, tolerance):
    source_rings, _ = _check_geometry(source, tolerance)
    output_rings, error = _check_geometry(loops, tolerance)
    deviation = 0.0 if loops == source else _boundary_bound(source_rings, output_rings, tolerance) + error
    return deviation, error


def _output_directory(out):
    """Accept a new directory or supervisor-created empty directory, no links."""
    try:
        from .cad_verify_v4_inputs import guarded_path
    except ImportError:
        from cad_verify_v4_inputs import guarded_path
    text = str(out).replace("\\", "/")
    parts = text.split("/")
    if any(p.casefold().rstrip(" .") in {"pilot-user", "v4-holdout-private"} for p in parts):
        _fail("private_output_path_forbidden")
    if any(p in (".", "..") for p in parts):
        _fail("output_path_traversal")
    path = Path(out).absolute()
    parent = guarded_path(path.parent, regular=False)
    if not parent.is_dir():
        _fail("output_parent_not_directory")
    try:
        path.lstat()  # Never follow a leaf symlink even for an existence check.
    except FileNotFoundError:
        return new_directory(path)
    path = guarded_path(path, regular=False)
    if not path.is_dir() or any(path.iterdir()):
        _fail("output_not_empty_directory")
    return path

def _record_hash(record):
    return _hash({key: value for key, value in record.items() if key != "record_sha256"})


def _provenance(recipe):
    import PIL
    import numpy
    import shapely
    return {
        "decoder": f"Pillow {PIL.__version__} PNG RGBA8; NumPy {numpy.__version__}; Shapely {shapely.__version__}",
        "luminance": "integer Rec.601: (299R+587G+114B+500)//1000; no gamma linearization",
        "threshold_comparison": "dark <=; light >=; alpha >=",
        "extraction": f"cell-union-fillet-v1: exact foreground closed-cell union; diagonal contacts refused; resource caps {MAX_PIXELS} pixels / {MAX_CELL_EDGES} exposed cell edges / {MAX_BOUNDARY_SEGMENTS} segments",
        "simplification": "Shapely topology-preserving polygon simplification" if recipe["simplify"]["allowed"] else "none",
        "rounding": "exact tangent circular fillets; infeasible trim refused" if recipe["rounding"]["allowed"] else "none",
        "hash_encoding": "sorted-key compact UTF-8 JSON, no NaN",
        "source_checks": "raw image and manifest SHA256 before/after",
    }

def geometry_bounds(record):
    """Exact line/circle bounds and analytic quadratic/cubic Bezier extrema."""
    return _geometry_bounds(record["loops"])


def _validate_analytic(record):
    """Validate genuine independent analytic-source records, not raster claims."""
    _fields(record, ("schema", "profile", "asset_id", "source_sha256",
                     "source_image_asset_id", "source_image_sha256", "provenance",
                     "units", "bounds_mm", "nominal_width_mm", "loops", "topology",
                     "pixel_to_mm"))
    if record["schema"] != SCHEMA or record["profile"] != "c-s1" or record["units"] != "mm":
        _fail("analytic_schema")
    for name in ("asset_id", "source_image_asset_id"):
        if not isinstance(record[name], str) or not record[name]:
            _fail("analytic_asset_id")
    for name in ("source_sha256", "source_image_sha256"):
        value = record[name]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            _fail("analytic_hash")
    transform = record["pixel_to_mm"]
    _fields(transform, ("scale_mm_per_pixel", "origin_mm", "image_height_pixels", "y_axis", "pixel_convention"))
    _number(transform["scale_mm_per_pixel"], positive=True)
    _point(transform["origin_mm"])
    if type(transform["image_height_pixels"]) is not int or transform["image_height_pixels"] <= 0 or transform["y_axis"] != "up" or transform["pixel_convention"] != "closed unit cells; centers at (col+0.5,row+0.5)":
        _fail("analytic_transform")
    loops = record["loops"]
    if not isinstance(loops, list) or not loops:
        _fail("missing_loops")
    canonical = []
    for i, loop in enumerate(loops):
        _fields(loop, ("role", "segments"), ("parent",))
        role = "outer" if i == 0 else "hole"
        if loop["role"] != role or "parent" in loop and (i == 0 or type(loop["parent"]) is not int or loop["parent"] != 0):
            _fail("analytic_loop_nesting")
        if not isinstance(loop["segments"], list) or not loop["segments"]:
            _fail("empty_loop")
        for segment in loop["segments"]:
            segment_endpoints(segment)
        canonical.append(dict(loop, **({"parent": 0} if i else {})))
    topology = record["topology"]
    _fields(topology, ("components", "holes"))
    if type(topology["components"]) is not int or type(topology["holes"]) is not int or topology != {"components": 1, "holes": len(loops) - 1}:
        _fail("analytic_topology")
    declared = record["bounds_mm"]
    if not isinstance(declared, list) or len(declared) != 4:
        _fail("analytic_bounds")
    for value in declared:
        _number(value)
    width = _number(record["nominal_width_mm"], positive=True)
    actual = _geometry_bounds(canonical)
    extent = max(actual[1] - actual[0], actual[3] - actual[2])
    if extent <= 0 or not math.isfinite(extent):
        _fail("analytic_extent")
    # This is numerical resolution, not a user acceptance threshold. The
    # exact analytic source and image are digest-bound by Inputs admission.
    numeric = 256 * math.ulp(max(abs(c) for c in actual))
    if any(abs(a - b) > numeric for a, b in zip(actual, declared)) or abs(actual[1] - actual[0] - width) > 2 * numeric:
        _fail("analytic_bounds_mismatch")
    _check_geometry(canonical, extent * 1e-6)
    return record


def validate_contour(record):
    """Validate hash closure, policies, exact segments and conservative topology."""
    if isinstance(record, dict) and record.get("provenance") == {"kind": "independent_analytic_source"}:
        return _validate_analytic(record)
    required = ("schema", "profile", "asset_id", "source_image_sha256", "source_manifest_sha256", "decoded_rgba_sha256", "mask_sha256", "recipe_sha256", "record_sha256", "units", "pixel_to_mm", "bounds_mm", "nominal_width_mm", "loops", "source_loops", "source_mask", "recipe", "topology", "reports", "provenance", "approximation")
    _fields(record, required)
    if record["schema"] != SCHEMA or record["profile"] != "c-s1" or record["units"] != "mm":
        _fail("record_schema")
    if not isinstance(record["asset_id"], str) or not record["asset_id"]:
        _fail("asset_id")
    for name in ("source_image_sha256", "source_manifest_sha256", "decoded_rgba_sha256", "mask_sha256", "recipe_sha256", "record_sha256"):
        value = record[name]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            _fail("invalid_hash")
    recipe = validate_recipe(record["recipe"])
    if _hash(recipe) != record["recipe_sha256"] or _hash(record["source_mask"]) != record["mask_sha256"] or _record_hash(record) != record["record_sha256"]:
        _fail("hash_closure")
    mask_record = record["source_mask"]
    _fields(mask_record, ("width", "height", "encoding", "rows"))
    width, height = mask_record["width"], mask_record["height"]
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0 or width * height > MAX_PIXELS or mask_record["encoding"] != "row-runs" or not isinstance(mask_record["rows"], list) or len(mask_record["rows"]) != height:
        _fail("mask_encoding")
    import numpy as np
    mask = np.zeros((height, width), dtype=bool)
    for y, runs in enumerate(mask_record["rows"]):
        if not isinstance(runs, list):
            _fail("mask_runs")
        previous = -1
        for run in runs:
            if not isinstance(run, list) or len(run) != 2 or any(type(v) is not int for v in run) or not 0 <= run[0] < run[1] <= width or run[0] <= previous:
                _fail("mask_runs")
            mask[y, run[0]:run[1]] = True
            previous = run[1]
    scale = recipe["scale"]
    expected_transform = {"scale_mm_per_pixel": scale["mm_per_pixel"], "origin_mm": scale["origin_mm"], "image_height_pixels": height, "y_axis": "up", "pixel_convention": "closed unit cells; centers at (col+0.5,row+0.5)"}
    if record["pixel_to_mm"] != expected_transform:
        _fail("transform_mismatch")
    source = _mask_loops(mask, scale["mm_per_pixel"], scale["origin_mm"])
    if source != record["source_loops"]:
        _fail("source_mask_geometry_mismatch")
    if _processed_loops(source, recipe) != record["loops"]:
        _fail("geometry_not_derived_from_recipe")
    for loop in record["loops"]:
        _fields(loop, ("role", "segments"), ("parent",))
        for segment in loop["segments"]:
            if segment.get("kind") not in ("line", "arc"):
                _fail("unapproved_contour_segment")
    if record["topology"] != {"source": _topology(source), "output": _topology(record["loops"])} or record["topology"]["source"] != record["topology"]["output"]:
        _fail("topology_changed")
    tolerance = recipe["limits"]["approximation_tolerance_mm"]
    deviation, error = _deviation(source, record["loops"], tolerance)
    if deviation > recipe["limits"]["max_deviation_mm"]:
        _fail("source_deviation_budget_exceeded")
    _fields(record["reports"], ("minimum_radius_mm", "source_boundary_hausdorff_upper_mm"))
    _fields(record["approximation"], ("flatten_tolerance_mm", "flatten_error_bound_mm", "source_deviation_upper_mm", "deviation_method"))
    _fields(record["provenance"], ("decoder", "luminance", "threshold_comparison", "extraction", "simplification", "rounding", "hash_encoding", "source_checks"))
    if any(not isinstance(v, str) or not v for v in record["provenance"].values()):
        _fail("provenance_value")
    if record["approximation"]["deviation_method"] != DEVIATION_METHOD:
        _fail("approximation_method")
    if record["reports"]["source_boundary_hausdorff_upper_mm"] != deviation or record["approximation"]["source_deviation_upper_mm"] != deviation or record["approximation"]["flatten_error_bound_mm"] != error or record["approximation"]["flatten_tolerance_mm"] != tolerance:
        _fail("approximation_report_mismatch")
    bounds = _geometry_bounds(record["loops"])
    if bounds != record["bounds_mm"] or bounds[1] - bounds[0] != record["nominal_width_mm"]:
        _fail("bounds_mismatch")
    _number(record["nominal_width_mm"], positive=True)
    actual_radius = minimum_radius(record)
    reported = record["reports"].get("minimum_radius_mm")
    if reported != (actual_radius if math.isfinite(actual_radius) else None):
        _fail("radius_report_mismatch")
    return record


def prepare_contour(manifest_path, asset_id, recipe, out):
    """Resolve independent input, extract/round real curves, write out/contour.json.

    out must be new or an existing empty supervisor-owned directory. Evidence
    embeds the unchanged source mask and exact pre-processing cell boundaries;
    no original input path enters the record.
    """
    try:
        from .cad_verify_v4_inputs import resolve_asset
    except ImportError:
        from cad_verify_v4_inputs import resolve_asset
    recipe = json.loads(json.dumps(validate_recipe(recipe), allow_nan=False))
    asset = resolve_asset(manifest_path, asset_id, expected_kind="image")
    manifest_digest = file_sha(manifest_path)
    mask, rgba_digest = _decode(asset["path"], recipe)
    source_mask = _mask_record(mask)
    scale = recipe["scale"]
    source = _mask_loops(mask, scale["mm_per_pixel"], scale["origin_mm"])
    loops = _processed_loops(source, recipe)
    tolerance = recipe["limits"]["approximation_tolerance_mm"]
    deviation, error = _deviation(source, loops, tolerance)
    if deviation > recipe["limits"]["max_deviation_mm"]:
        _fail("source_deviation_budget_exceeded")
    if _topology(source) != _topology(loops):
        _fail("topology_changed")
    bounds = _geometry_bounds(loops)
    radius = minimum_radius({"loops": loops})
    record = {"schema": SCHEMA, "profile": "c-s1", "asset_id": asset_id,
              "source_image_sha256": asset["digest"], "source_manifest_sha256": manifest_digest,
              "decoded_rgba_sha256": rgba_digest, "mask_sha256": _hash(source_mask),
              "recipe_sha256": _hash(recipe), "units": "mm",
              "pixel_to_mm": {"scale_mm_per_pixel": scale["mm_per_pixel"], "origin_mm": scale["origin_mm"], "image_height_pixels": int(mask.shape[0]), "y_axis": "up", "pixel_convention": "closed unit cells; centers at (col+0.5,row+0.5)"},
              "bounds_mm": bounds, "nominal_width_mm": bounds[1] - bounds[0],
              "loops": loops, "source_loops": source, "source_mask": source_mask, "recipe": recipe,
              "topology": {"source": _topology(source), "output": _topology(loops)},
              "reports": {"minimum_radius_mm": radius if math.isfinite(radius) else None,
                          "source_boundary_hausdorff_upper_mm": deviation},
              "provenance": _provenance(recipe),
              "approximation": {"flatten_tolerance_mm": tolerance, "flatten_error_bound_mm": error, "source_deviation_upper_mm": deviation, "deviation_method": DEVIATION_METHOD}}
    record["record_sha256"] = _record_hash(record)
    validate_contour(record)
    if file_sha(asset["path"]) != asset["digest"] or file_sha(manifest_path) != manifest_digest:
        _fail("input_changed")
    # Re-resolve to recheck links, sizes, registry and digest, not just bytes.
    if resolve_asset(manifest_path, asset_id, expected_kind="image")["digest"] != asset["digest"]:
        _fail("input_changed")
    directory = _output_directory(out)
    write_json(directory / "contour.json", record)
    return record
