"""Independent S1 oracles. No imports of the candidate compiler or contour preprocessor.

Planar certificates use exact line/circle definitions, bounded chord approximation,
and a 1-Lipschitz distance sampling bound. Tool access certifies only a planar disk
center model, not CAM, dynamics, six-DOF clearance, or machining feasibility.
Declared v2 raster topology is independently labeled fg4/bg8 from the original
decoded mask. Source point contacts are immutable references; canonical/native
boundaries must be separated, and contact clearance is certified to material.
"""
import math

SCHEMA = 'cad-harness.judgement.v4c'


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '') + name)


def _number(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('judge_nonfinite_' + name)
    if minimum is not None and value < minimum:
        raise ValueError('judge_range_' + name)
    return float(value)


def _vector(value, size, name):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ValueError('judge_vector_' + name)
    return tuple(_number(x, name) for x in value)


def validate_card(card):
    """Use the one shared strict public schema; no acceptance defaults."""
    return _module('cad_verify_v4_plans').validate_judge_card(card)


def _required(c, *keys):
    missing = [k for k in keys if k not in c or c[k] is None]
    if missing:
        raise Unknown('missing_required:' + ','.join(missing))


class Unknown(ValueError):
    """Evidence or an acceptance quantity is unavailable; never an acceptance."""


class _NativeLoop(dict):
    """Private witness for a closed native wire, never reconstructed from JSON.

    Curves remain native: no endpoint snapping or three-point circle refitting.
    The certified vertex tolerance is carried into every measurement enclosure.
    """
    def __init__(self, segments, curves, error_mm):
        super().__init__(role='outer', segments=segments)
        self.curves = tuple(curves)
        self.error_mm = error_mm

    def points(self, index, tolerance):
        edge, first, last = self.curves[index]
        if self['segments'][index]['kind'] == 'line':
            return [tuple(self['segments'][index][k]) for k in ('p0', 'p1')], 0.
        radius = _number(edge.Curve.Radius, 'native_circle_radius', 0)
        if radius == 0:
            raise Unknown('native_circle_radius_zero')
        angle = 4*math.asin(math.sqrt(min(tolerance/(2*radius), .5)))
        count = max(1, math.ceil(abs(last-first)/angle))
        if count > 1000000:
            raise Unknown('curve_resolution_excessive')
        points = []
        for i in range(count+1):
            point = edge.valueAt(first+(last-first)*i/count)
            points.append((point.x, point.y))
        return points, 2*radius*math.sin(abs(last-first)/count/4)**2

    def tangent(self, index, at_end):
        edge, first, last = self.curves[index]
        tangent = edge.tangentAt(last if at_end else first)
        length = math.hypot(tangent.x, tangent.y)
        if length == 0:
            raise Unknown('native_projection_tangent_zero')
        sign = 1 if last > first else -1
        return sign*tangent.x/length, sign*tangent.y/length

    def radius(self, index):
        if self['segments'][index]['kind'] == 'line':
            return math.inf
        return _number(self.curves[index][0].Curve.Radius, 'native_circle_radius', 0)


def _check(c, status, measured=None, target=None, tolerance=None, uncertainty=None, **evidence):
    return dict(id=c['id'], metric=c['metric'], status=status, measured=measured,
                target=target, tolerance=tolerance, uncertainty=uncertainty, evidence=evidence)


def _interval_status(lower, upper, limit, minimum=False):
    if minimum:
        return 'PASS' if lower >= limit else 'FAIL' if upper < limit else 'UNVERIFIED'
    return 'PASS' if upper <= limit else 'FAIL' if lower > limit else 'UNVERIFIED'


def _arc(segment):
    a, m, b = (_vector(segment[k], 2, k) for k in ('p0', 'pm', 'p1'))
    ax, ay = a; mx, my = m; bx, by = b
    d = 2 * (ax*(my-by) + mx*(by-ay) + bx*(ay-my))
    if abs(d) <= 1e-14 * max(1., math.dist(a, m)*math.dist(m, b)):
        raise ValueError('judge_degenerate_arc')
    aa, mm, bb = ax*ax+ay*ay, mx*mx+my*my, bx*bx+by*by
    center = ((aa*(my-by)+mm*(by-ay)+bb*(ay-my))/d,
              (aa*(bx-mx)+mm*(ax-bx)+bb*(mx-ax))/d)
    r = math.dist(a, center)
    start, middle, end = (math.atan2(p[1]-center[1], p[0]-center[0]) for p in (a,m,b))
    sweep = (end-start) % (2*math.pi)
    if (middle-start) % (2*math.pi) > sweep:
        sweep -= 2*math.pi
    if sweep == 0:
        raise ValueError('judge_zero_arc')
    return center, r, start, sweep


def _segment_points(segment, tolerance):
    kind = segment.get('kind')
    if kind == 'line':
        return [_vector(segment['p0'], 2, 'p0'), _vector(segment['p1'], 2, 'p1')], 0.
    if kind != 'arc':
        raise Unknown('uncertified_curve_kind:' + str(kind))
    center, radius, start, sweep = _arc(segment)
    angle = 2*math.acos(max(-1., 1-min(tolerance/radius, 1.)))
    count = max(1, math.ceil(abs(sweep)/angle))
    if count > 1000000:
        raise Unknown('curve_resolution_excessive')
    points = [(center[0]+radius*math.cos(start+sweep*i/count),
               center[1]+radius*math.sin(start+sweep*i/count)) for i in range(count+1)]
    points[0], points[-1] = tuple(segment['p0']), tuple(segment['p1'])
    return points, radius*(1-math.cos(abs(sweep)/count/2))


def _loop_points(loop, tolerance):
    points = []
    error = join_error = 0.
    native = type(loop) is _NativeLoop
    closure_limit = max(1e-8, loop.error_mm) if native else 1e-8
    for index, segment in enumerate(loop['segments']):
        part, bound = loop.points(index, tolerance) if native else _segment_points(segment, tolerance)
        if points:
            gap = math.dist(points[-1], part[0])
            if gap > closure_limit:
                raise ValueError('judge_open_segment_chain')
            join_error = max(join_error, gap)
        points.extend(part if not points else part[1:])
        error = max(error, bound)
    if not points:
        raise ValueError('judge_open_loop')
    gap = math.dist(points[0], points[-1])
    if gap > closure_limit:
        raise ValueError('judge_open_loop')
    # A native closed wire can evaluate its shared vertex a few ulps apart.
    # Represent the ALREADY accepted closure exactly, not as a tiny extra edge;
    # retain its displacement in the symmetric approximation error enclosure.
    points[-1] = points[0]
    return points, error + max(join_error, gap, loop.error_mm if native else 0.)


def planar_geometry(record, tolerance_mm):
    """Return polygon and symmetric boundary approximation bound, independent of reports."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    tolerance = _number(tolerance_mm, 'curve_tolerance_mm', 0)
    if tolerance == 0:
        raise ValueError('judge_curve_tolerance_zero')
    if record.get('units') != 'mm' or not record.get('loops'):
        raise ValueError('judge_contour_units_or_empty')
    outer, holes, epsilon = [], [], 0.
    for loop in record['loops']:
        points, error = _loop_points(loop, tolerance)
        epsilon = max(epsilon, error)
        poly = Polygon(points)
        if not poly.is_valid or poly.area == 0:
            raise ValueError('judge_invalid_planar_loop')
        if loop['role'] == 'outer':
            outer.append(poly)
        elif loop['role'] == 'hole':
            holes.append(poly)
        else:
            raise ValueError('judge_loop_role')
    assigned = [[] for _ in outer]
    for hole in holes:
        owners = [(p.area, i) for i, p in enumerate(outer) if p.contains(hole)]
        if not owners:
            raise ValueError('judge_orphan_hole')
        assigned[min(owners)[1]].append(hole)
    region = unary_union([p.difference(unary_union(assigned[i]))
                          for i, p in enumerate(outer)])
    if not region.is_valid or region.is_empty:
        raise ValueError('judge_invalid_region')
    return region, epsilon


def _boundary_lines(region):
    boundary = region.boundary
    return list(boundary.geoms) if hasattr(boundary, 'geoms') else [boundary]


def hausdorff_bounds(a, b, step_mm, error_a_mm=0., error_b_mm=0.):
    """Symmetric Hausdorff interval, not nearest-shape distance.

    Distance to a fixed closed set is 1-Lipschitz. Every point of each source
    polygon boundary is within step/2 of a sampled endpoint. Approximation
    uncertainty enters both directions by the Hausdorff triangle inequality.
    """
    from shapely.geometry import Point
    step = _number(step_mm, 'sampling_step_mm', 0)
    if step == 0:
        raise ValueError('judge_sampling_step_zero')
    maximum, covering = 0., 0.
    coordinate_scale=max(1.,*(abs(x) for region in (a,b) for x in region.bounds))
    numerical_error=128*math.ulp(coordinate_scale)
    for source, target in ((a,b), (b,a)):
        target_boundary = target.boundary
        for line in _boundary_lines(source):
            coords = list(line.coords)
            for p, q in zip(coords, coords[1:]):
                length = math.dist(p, q)
                n = max(1, math.ceil(length/step))
                covering = max(covering, length/n/2)
                for i in range(n+1):
                    point = Point(p[0]+(q[0]-p[0])*i/n, p[1]+(q[1]-p[1])*i/n)
                    maximum = max(maximum, point.distance(target_boundary))
    error = error_a_mm+error_b_mm+numerical_error
    return dict(lower_mm=max(0., maximum-error), upper_mm=maximum+covering+error,
                sampled_max_mm=maximum, lipschitz_cover_mm=covering,
                curve_error_mm=error_a_mm+error_b_mm,numerical_error_mm=numerical_error,
                method='symmetric_boundary_1_lipschitz')


def _topology(region):
    polygons=list(region.geoms) if hasattr(region,'geoms') else [region]
    return dict(components=len(polygons),holes=sum(len(p.interiors) for p in polygons))


def _overlap_correspondence(source, target):
    """A fixed-frame bijection; no component translation or bbox fitting."""
    if len(source) != len(target):
        return None
    mapping = []
    for piece in source:
        overlaps = [(piece.intersection(other).area, j) for j, other in enumerate(target)]
        if not overlaps:
            return None
        overlaps.sort(reverse=True)
        if overlaps[0][0] <= 0 or len(overlaps) > 1 and overlaps[0][0] == overlaps[1][0]:
            return None
        mapping.append(overlaps[0][1])
    return mapping if len(set(mapping)) == len(mapping) else None


def _nesting_matches(a, b):
    """Match material pieces and their holes, then verify containment relations."""
    from shapely.geometry import Polygon
    source = list(a.geoms) if hasattr(a, 'geoms') else [a]
    target = list(b.geoms) if hasattr(b, 'geoms') else [b]
    mapping = _overlap_correspondence(source, target)
    if mapping is None:
        return False
    holes_a = [[Polygon(ring) for ring in piece.interiors] for piece in source]
    holes_b = [[Polygon(ring) for ring in piece.interiors] for piece in target]
    hole_maps = []
    for i, j in enumerate(mapping):
        matches = _overlap_correspondence(holes_a[i], holes_b[j])
        if matches is None:
            return False
        hole_maps.append(matches)
    def owner(piece, holes):
        candidates = [(hole.area, i, j) for i, group in enumerate(holes)
                      for j, hole in enumerate(group) if hole.contains(piece)]
        return min(candidates)[1:] if candidates else None
    for i, j in enumerate(mapping):
        old, new = owner(source[i], holes_a), owner(target[j], holes_b)
        expected = (mapping[old[0]], hole_maps[old[0]][old[1]]) if old is not None else None
        if new != expected:
            return False
    return True


def _digital_v2(record):
    """Only the explicitly declared complementary v2 connectivity is authority."""
    recipe = record.get('recipe', {})
    if recipe.get('curve_fit', {}).get('method') != 'source_bounded_biarc_v2':
        return False
    connectivity = recipe.get('topology', {}).get('connectivity')
    if (connectivity != dict(foreground=4, background=8, pinch='remove_locally')
            or type(connectivity['foreground']) is not int
            or type(connectivity['background']) is not int):
        raise ValueError('judge_v2_connectivity_missing_or_invalid')
    return True


def _digital_mask_analysis(mask, registration):
    """Independent fg4/bg8 labels, exposed-edge forest, and immutable cell sets.

    GEOS interiors are deliberately NOT used to count source holes: a bg8
    region can consist of several closed cell polygons touching at a vertex.
    No source boundary walk, fitter report, or repaired polygon is consulted.
    """
    from collections import deque
    import numpy as np
    from shapely.geometry import box
    from shapely.ops import unary_union

    def labels(binary, offsets):
        height, width = binary.shape
        result = np.zeros(binary.shape, dtype=np.int32)
        count = 0
        for row in range(height):
            for col in range(width):
                if not binary[row, col] or result[row, col]:
                    continue
                count += 1
                result[row, col] = count
                queue = deque([(row, col)])
                while queue:
                    y, x = queue.popleft()
                    for dy, dx in offsets:
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < height and 0 <= nx < width
                                and binary[ny, nx] and not result[ny, nx]):
                            result[ny, nx] = count
                            queue.append((ny, nx))
        return result, count

    height, width = mask.shape
    cross = ((-1, 0), (0, -1), (0, 1), (1, 0))
    foreground, components = labels(mask, cross)
    if not components:
        raise ValueError('judge_empty_mask')
    padded = np.pad(mask, 1, constant_values=False)
    background, background_count = labels(
        ~padded, tuple((dy, dx) for dy in (-1, 0, 1)
                       for dx in (-1, 0, 1) if dy or dx))
    # The padded first cell is exterior. Its raster label is one; remap to zero.
    background -= 1
    adjacency = {('background', 0): set()}
    for row in range(height):
        for col in range(width):
            label = int(foreground[row, col])
            if not label:
                continue
            material = ('foreground', label)
            adjacency.setdefault(material, set())
            for dy, dx in cross:
                y, x = row + 1 + dy, col + 1 + dx
                if not padded[y, x]:
                    void = ('background', int(background[y, x]))
                    adjacency.setdefault(void, set()).add(material)
                    adjacency[material].add(void)
    root = ('background', 0)
    parents = {root: None}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for neighbor in sorted(adjacency[node]):
            if neighbor == parents[node]:
                continue
            if neighbor in parents:
                raise ValueError('judge_digital_nesting_not_a_forest')
            parents[neighbor] = node
            queue.append(neighbor)
    holes = background_count - 1
    if len(parents) != components + holes + 1:
        raise ValueError('judge_digital_nesting_incomplete')

    origin = registration['origin_mm']
    sx, sy = registration['pixel_size_mm']
    direction = registration['y_direction']

    def cell_regions(raster, count, first):
        runs = [[] for _ in range(count)]
        for row in range(height):
            col = 0
            while col < width:
                label = int(raster[row, col])
                end = col + 1
                while end < width and int(raster[row, end]) == label:
                    end += 1
                if first <= label < first + count:
                    x0, x1 = origin[0] + col*sx, origin[0] + end*sx
                    y0 = origin[1] + row*sy*direction
                    y1 = origin[1] + (row+1)*sy*direction
                    runs[label-first].append(box(x0, min(y0, y1), x1, max(y0, y1)))
                col = end
        return [unary_union(group) for group in runs]

    contacts = []
    for row in range(height-1):
        for col in range(width-1):
            a, b = bool(mask[row, col]), bool(mask[row, col+1])
            c, d = bool(mask[row+1, col]), bool(mask[row+1, col+1])
            if a == d and b == c and a != b:
                incident = sorted({int(foreground[y, x])
                                   for y, x in ((row, col), (row, col+1),
                                                (row+1, col), (row+1, col+1))
                                   if foreground[y, x]})
                contacts.append(dict(vertex_pixels=[col+1, height-row-1],
                                     incident_components=incident))
    contacts.sort(key=lambda contact: contact['vertex_pixels'])
    return dict(topology=dict(components=components, holes=holes),
                components=cell_regions(foreground, components, 1),
                holes=cell_regions(background[1:-1, 1:-1], holes, 1),
                component_parents=[parents[('foreground', i)][1]
                                   for i in range(1, components+1)],
                hole_parents=[parents[('background', i)][1]
                              for i in range(1, holes+1)],
                contacts=contacts, height=height, width=width, registration=registration)


def _positive_overlap_matching(weights):
    """Deterministic maximum-weight perfect matching; zero edges are forbidden.

    A shortest augmenting-path assignment avoids either greedy rejection when
    a tiny piece also overlaps a large neighbor, or exponential enumeration.
    Equal costs retain ascending raster/target order as the deterministic tie.
    """
    count = len(weights)
    if any(len(row) != count for row in weights):
        return None
    u, v = [0.]*(count+1), [0.]*(count+1)
    assigned, previous = [0]*(count+1), [0]*(count+1)
    for source in range(1, count+1):
        assigned[0] = source
        minimum, used = [math.inf]*(count+1), [False]*(count+1)
        column = 0
        while True:
            used[column] = True
            row = assigned[column]
            delta, next_column = math.inf, 0
            for target in range(1, count+1):
                if used[target]:
                    continue
                weight = weights[row-1][target-1]
                if weight > 0:
                    cost = -weight-u[row]-v[target]
                    if cost < minimum[target]:
                        minimum[target], previous[target] = cost, column
                if minimum[target] < delta:
                    delta, next_column = minimum[target], target
            if not math.isfinite(delta):
                return None
            for target in range(count+1):
                if used[target]:
                    u[assigned[target]] += delta
                    v[target] -= delta
                else:
                    minimum[target] -= delta
            column = next_column
            if not assigned[column]:
                break
        while column:
            predecessor = previous[column]
            assigned[column] = assigned[predecessor]
            column = predecessor
    result = [None]*count
    for target in range(1, count+1):
        result[assigned[target]-1] = target-1
    return result


def _digital_nesting_matches(source, target, factor=1., origin=(0., 0.)):
    """Match the alternating forest by positive fixed-frame region overlaps.

    Every fg4 piece and bg8 hole has its own target. Extra overlaps caused by
    bounded outward growth are allowed, but merging, dropping, or changing
    nesting cannot supply a complete forest-constrained perfect matching.
    """
    from shapely.affinity import scale, translate
    from shapely.geometry import Polygon
    if source['topology'] != _topology(target):
        return False

    def registered(region):
        return translate(scale(region, xfact=factor, yfact=factor, origin=(0, 0)),
                         xoff=origin[0], yoff=origin[1])

    pieces = list(target.geoms) if hasattr(target, 'geoms') else [target]
    holes = [(i, Polygon(ring)) for i, piece in enumerate(pieces)
             for ring in piece.interiors]
    target_parents = []
    for piece in pieces:
        owners = [(hole.area, k) for k, (_, hole) in enumerate(holes) if hole.contains(piece)]
        target_parents.append(min(owners)[1] if owners else None)
    source_regions = ([registered(piece) for piece in source['components']],
                      [registered(hole) for hole in source['holes']])
    target_regions = (pieces, [hole for _, hole in holes])
    source_children = (
        [[k for k, parent in enumerate(source['hole_parents']) if parent == i+1]
         for i in range(len(source_regions[0]))],
        [[k for k, parent in enumerate(source['component_parents']) if parent == i+1]
         for i in range(len(source_regions[1]))])
    target_children = (
        [[k for k, (owner, _) in enumerate(holes) if owner == i] for i in range(len(pieces))],
        [[k for k, owner in enumerate(target_parents) if owner == i] for i in range(len(holes))])
    memo = {}

    def pair_score(kind, old, new):
        key = (kind, old, new)
        if key not in memo:
            overlap = source_regions[kind][old].intersection(target_regions[kind][new]).area
            if not math.isfinite(overlap):
                raise Unknown('digital_overlap_nonfinite')
            children = (group_score(1-kind, source_children[kind][old], target_children[kind][new])
                        if overlap > 0 else None)
            memo[key] = overlap+children if children is not None else 0.
        return memo[key]

    def group_score(kind, old, new):
        if len(old) != len(new):
            return None
        weights = [[pair_score(kind, i, j) for j in new] for i in old]
        mapping = _positive_overlap_matching(weights)
        return (sum(weights[i][j] for i, j in enumerate(mapping))
                if mapping is not None else None)

    return group_score(0, [i for i, parent in enumerate(source['component_parents']) if not parent],
                       [i for i, parent in enumerate(target_parents) if parent is None]) is not None


def _candidate_separated(record, tolerance):
    """Certify simple, role-correct, strictly disjoint candidate boundaries."""
    from shapely.geometry import Polygon
    polygons, errors = [], []
    for loop in record['loops']:
        points, error = _loop_points(loop, tolerance)
        polygon = Polygon(points)
        if not polygon.is_valid or polygon.area <= 0:
            return False
        polygons.append(polygon)
        errors.append(error)
    coordinate_scale = max(1., *(abs(x) for p in polygons for x in p.bounds))
    numerical_error = 128*math.ulp(coordinate_scale)
    for i, polygon in enumerate(polygons):
        depth = sum(other.contains(polygon) for j, other in enumerate(polygons) if i != j)
        if record['loops'][i]['role'] != ('hole' if depth % 2 else 'outer'):
            return False
        for j in range(i):
            if polygon.boundary.distance(polygons[j].boundary) <= (
                    errors[i]+errors[j]+numerical_error):
                return False
    return True


def _pinch_openings(record, source, material, error, factor=1., origin=(0., 0.)):
    """Recompute cleared MATERIAL neighborhoods; declared distances are not proof."""
    from shapely.geometry import Point
    declared = record.get('reports', {}).get('pinch_openings')
    listing_matches = isinstance(declared, list)
    observed = {}
    if listing_matches:
        for entry in declared:
            if not isinstance(entry, dict) or set(entry) != {
                    'vertex_pixels', 'incident_components', 'clearance_mm_lower'}:
                listing_matches = False
                break
            vertex, incident = entry['vertex_pixels'], entry['incident_components']
            if (not isinstance(vertex, list) or len(vertex) != 2
                    or any(type(x) is not int for x in vertex)
                    or not isinstance(incident, list) or not incident
                    or any(type(x) is not int or x <= 0 for x in incident)
                    or incident != sorted(set(incident))
                    or tuple(vertex) in observed):
                listing_matches = False
                break
            try:
                if _number(entry['clearance_mm_lower'], 'pinch_clearance') <= 0:
                    listing_matches = False
                    break
            except ValueError:
                listing_matches = False
                break
            observed[tuple(vertex)] = incident
        listing_matches = listing_matches and observed == {
            tuple(c['vertex_pixels']): c['incident_components'] for c in source['contacts']}
    reg = source['registration']
    coordinate_scale = max(1., *(abs(x) for x in material.bounds), abs(factor),
                           *(abs(x) for x in origin),
                           abs(factor)*(abs(reg['origin_mm'][0])+
                                        source['width']*reg['pixel_size_mm'][0]),
                           abs(factor)*(abs(reg['origin_mm'][1])+
                                        source['height']*reg['pixel_size_mm'][1]))
    numerical_error = 128*math.ulp(coordinate_scale)
    measured = []
    for contact in source['contacts']:
        x, y = contact['vertex_pixels']
        point = Point(origin[0]+factor*(reg['origin_mm'][0]+x*reg['pixel_size_mm'][0]),
                      origin[1]+factor*(reg['origin_mm'][1]+
                      (source['height']-y)*reg['pixel_size_mm'][1]*reg['y_direction']))
        distance = material.distance(point)
        lower = max(0., distance-error-numerical_error)
        measured.append(dict(contact, clearance_mm_lower=lower,
                             material_distance_mm=distance))
    return dict(listing_matches=listing_matches,
                cleared=all(entry['clearance_mm_lower'] > 0 for entry in measured),
                openings=measured, curve_error_mm=error,
                numerical_error_mm=numerical_error,
                definition='positive_distance_to_material_with_boundary_error_enclosure')


def _source_mask_criterion(record):
    transform = record['pixel_to_mm']
    factor = transform['scale_mm_per_pixel']
    recipe = record['recipe']
    alpha = recipe['alpha']
    alpha_min = (alpha['threshold'] if alpha['policy'] == 'threshold' else
                 255 if alpha['policy'] == 'require-opaque' else 0)
    return dict(mask_asset_id=record.get('source_image_asset_id', record.get('asset_id')),
                registration=dict(
                    origin_mm=[transform['origin_mm'][0],
                               transform['origin_mm'][1]+transform['image_height_pixels']*factor],
                    pixel_size_mm=[factor, factor], y_direction=-1),
                foreground=dict(recipe['foreground'], alpha_min=alpha_min))


def _mask_commitment_matches(record, evidence):
    return (evidence['source_sha256'] == record.get('source_image_sha256')
            and ('mask_sha256' not in record or evidence['mask_sha256'] == record['mask_sha256'])
            and ('decoded_rgba_sha256' not in record
                 or evidence['decoded_rgba_sha256'] == record['decoded_rgba_sha256']))


def _piece_records(record, tolerance):
    """Partition exact native loops independently by immediate geometric owner."""
    from shapely.geometry import Polygon
    outers, holes = [], []
    for loop in record['loops']:
        points, _ = _loop_points(loop, tolerance)
        polygon = Polygon(points)
        (outers if loop['role'] == 'outer' else holes).append((loop, polygon))
    assigned = [[] for _ in outers]
    for loop, polygon in holes:
        owners = [(outer.area, i) for i, (_, outer) in enumerate(outers) if outer.contains(polygon)]
        if not owners:
            raise ValueError('judge_orphan_hole')
        assigned[min(owners)[1]].append(loop)
    return [dict(units='mm', loops=[outer] + assigned[i]) for i, (outer, _) in enumerate(outers)]


def _tangent(segment, at_end):
    if segment['kind'] == 'line':
        a, b = segment['p0'], segment['p1']
        dx, dy = b[0]-a[0], b[1]-a[1]
    elif segment['kind'] == 'arc':
        center, _, _, sweep = _arc(segment)
        p = segment['p1'] if at_end else segment['p0']
        sign = 1 if sweep > 0 else -1
        dx, dy = -sign*(p[1]-center[1]), sign*(p[0]-center[0])
    else:
        raise Unknown('uncertified_curvature:' + str(segment['kind']))
    length = math.hypot(dx, dy)
    if length == 0:
        raise ValueError('judge_zero_segment')
    return dx/length, dy/length


def minimum_radius(record, angular_tolerance_rad):
    """Actual circle radii and tangent discontinuities; straight lines have infinite radius."""
    angular = _number(angular_tolerance_rad, 'angular_tolerance_rad', 0)
    if angular > 0.01:
        raise ValueError('judge_angular_tolerance_excessive')
    radii, corners, native_error = [], 0, 0.
    for loop in record['loops']:
        native = type(loop) is _NativeLoop
        if native:
            native_error = max(native_error, loop.error_mm)
        segments = loop['segments']
        if not segments:
            raise ValueError('judge_empty_loop')
        for i, s in enumerate(segments):
            if s['kind'] == 'arc':
                radii.append(loop.radius(i) if native else _arc(s)[1])
            elif s['kind'] != 'line':
                raise Unknown('uncertified_curvature:' + str(s['kind']))
            previous = segments[i-1]
            if math.dist(previous['p1'], s['p0']) > (max(1e-8, loop.error_mm) if native else 1e-8):
                raise ValueError('judge_open_loop')
            u, v = ((loop.tangent(i-1, True), loop.tangent(i, False)) if native
                    else (_tangent(previous, True), _tangent(s, False)))
            angle = math.atan2(abs(u[0]*v[1]-u[1]*v[0]), u[0]*v[0]+u[1]*v[1])
            # Vertex tolerance bounds position, not a change to the native
            # curve parameter or its fixed unit derivative. Only floating-point
            # direction evaluation uncertainty belongs in the angular interval.
            angle_error = 256*math.ulp(1.) if native else 0.
            if angle_error and angle-angle_error <= angular < angle+angle_error:
                raise Unknown('native_tangent_interval_inconclusive')
            if angle-angle_error > angular:
                corners += 1
    return dict(minimum_mm=0. if corners else min(radii) if radii else None,
                unbounded=not corners and not radii, sharp_corners=corners,
                circle_radii_mm=radii, native_error_mm=native_error,
                source='independent_segment_geometry')


def _convex_certificate(record):
    """Exact signed turning certificate for a single line/circle loop."""
    if len(record['loops']) != 1 or record['loops'][0]['role'] != 'outer':
        return False
    loop = record['loops'][0]
    native = type(loop) is _NativeLoop
    segments = loop['segments']
    turns = []
    for i, segment in enumerate(segments):
        u, v = ((loop.tangent(i-1, True), loop.tangent(i, False)) if native
                else (_tangent(segments[i-1], True), _tangent(segment, False)))
        turns.append(math.atan2(u[0]*v[1]-u[1]*v[0], u[0]*v[0]+u[1]*v[1]))
        if segment['kind'] == 'arc':
            if native:
                edge, first, last = loop.curves[i]
                turns.append((last-first)*(1 if edge.Curve.Axis.z > 0 else -1))
            else:
                turns.append(_arc(segment)[3])
    return (abs(abs(sum(turns))-2*math.pi) < 1e-7 and
            (all(t >= -1e-10 for t in turns) or all(t <= 1e-10 for t in turns)))


def _envelope(region, error, segments=64):
    if error == 0:
        return region, region
    # Inflating the radius compensates for GEOS's inscribed circular buffer
    # chords, so the positive buffer contains the full uncertainty disk.
    radius = error/math.cos(math.pi/(4*segments))
    return region.buffer(-radius, quad_segs=segments), region.buffer(radius, quad_segs=segments)


def tool_access(record, criterion):
    """Disk-center erosion/reachability and coverage, with conservative area envelope."""
    _required(criterion, 'tool_radius_mm','maximum_uncovered_mm2','area_uncertainty_mm2',
              'curve_tolerance_mm','buffer_segments','require_connected')
    radius = _number(criterion['tool_radius_mm'], 'tool_radius_mm', 0)
    if radius == 0:
        raise ValueError('judge_tool_radius_zero')
    n = criterion['buffer_segments']
    if isinstance(n, bool) or not isinstance(n, int) or n < 8 or n > 4096:
        raise ValueError('judge_buffer_segments')
    if not isinstance(criterion['require_connected'], bool):
        raise ValueError('judge_require_connected')
    region, epsilon = planar_geometry(record, criterion['curve_tolerance_mm'])
    sagitta = radius*(1-math.cos(math.pi/(4*n)))
    delta = epsilon+sagitta
    # Shrink uncertainty for certainly reachable coverage; enlarge for possibly reachable.
    safe, possible = _envelope(region, delta, n)
    cosine = math.cos(math.pi/(4*n))
    safe_centers = safe.buffer(-(radius+sagitta)/cosine, quad_segs=n)
    possible_centers = possible.buffer(-max(0.,radius-sagitta)*cosine, quad_segs=n)
    safe_cover = safe_centers.buffer(radius, quad_segs=n)
    possible_cover = possible_centers.buffer((radius+sagitta)/cosine, quad_segs=n)
    nominal = region.buffer(-radius, quad_segs=n)
    components = len(nominal.geoms) if hasattr(nominal, 'geoms') else (0 if nominal.is_empty else 1)
    lower = max(0., safe.area-possible_cover.intersection(safe).area)
    upper = max(0., possible.area-safe_cover.intersection(possible).area)
    margin = _number(criterion['area_uncertainty_mm2'], 'area_uncertainty_mm2', 0)
    lower, upper = max(0.,lower-margin), upper+margin
    status = _interval_status(lower,upper,_number(criterion['maximum_uncovered_mm2'],'maximum_uncovered_mm2',0))
    # Equal component counts of sampled offsets are not a topology proof.
    # Convexity certifies connected erosion; disjoint possible components with
    # nonempty safe subsets certify failure. Other numerical topology is unknown.
    convex = _convex_certificate(record)
    topology_stable = convex and not safe_centers.is_empty
    possible_parts = list(possible_centers.geoms) if hasattr(possible_centers, 'geoms') else [possible_centers]
    certainly_occupied = sum(not p.intersection(safe_centers).is_empty for p in possible_parts if not p.is_empty)
    if criterion['require_connected']:
        if _topology(region)['components'] > 1:
            pieces = [tool_access(piece, criterion) for piece in _piece_records(record, criterion['curve_tolerance_mm'])]
            topology_stable = all(piece['topology_stable'] for piece in pieces)
            if any(piece['status'] == 'FAIL' for piece in pieces):
                status = 'FAIL'
            elif status != 'FAIL' and any(piece['status'] != 'PASS' for piece in pieces):
                status = 'UNVERIFIED'
        elif possible_centers.is_empty or certainly_occupied > 1:
            status = 'FAIL'
        elif not topology_stable and status != 'FAIL':
            status = 'UNVERIFIED'
    return dict(status=status, uncovered_lower_mm2=lower,uncovered_upper_mm2=upper,
                center_components=components, topology_stable=topology_stable,
                curve_error_mm=epsilon,buffer_sagitta_mm=sagitta,
                model='planar_disk_center_only')


def _mask_region(manifest, c, digital=False):
    from PIL import Image
    import numpy as np
    from shapely.geometry import box
    from shapely.ops import unary_union
    _required(c,'mask_asset_id','registration','foreground')
    reg, fg = c['registration'], c['foreground']
    _required(reg,'origin_mm','pixel_size_mm','y_direction')
    _required(fg,'channel','threshold','polarity','alpha_min')
    origin = _vector(reg['origin_mm'],2,'origin_mm')
    sx, sy = _vector(reg['pixel_size_mm'],2,'pixel_size_mm')
    if sx <= 0 or sy <= 0 or reg['y_direction'] not in (-1,1):
        raise ValueError('judge_mask_registration')
    threshold, alpha = _number(fg['threshold'],'threshold',0), _number(fg['alpha_min'],'alpha_min',0)
    if threshold > 255 or alpha > 255 or fg['polarity'] not in ('dark','light'):
        raise ValueError('judge_foreground')
    asset = _module('cad_verify_v4_inputs').resolve_asset(manifest,c['mask_asset_id'],'image')
    with Image.open(asset['path']) as image:
        rgba = np.asarray(image.convert('RGBA'))
    # Explicit byte-valued luminance definition; no hidden antialias threshold.
    if fg['channel']=='luminance':
        rgb = rgba[:,:,:3].astype(np.uint32)
        values = (299*rgb[:,:,0]+587*rgb[:,:,1]+114*rgb[:,:,2]+500)//1000
    else:
        values = rgba[:,:,{'red':0,'green':1,'blue':2,'alpha':3}[fg['channel']]]
    mask = (values <= threshold if fg['polarity']=='dark' else values >= threshold) & (rgba[:,:,3] >= alpha)
    runs = []
    encoded_rows=[[] for _ in range(mask.shape[0])]
    for row in range(mask.shape[0]):
        indices = np.flatnonzero(mask[row])
        if not len(indices):
            continue
        start, last = int(indices[0]), int(indices[0])
        for col in [*map(int,indices[1:]), None]:
            if col is not None and col == last+1:
                last=col; continue
            x0,x1=origin[0]+start*sx,origin[0]+(last+1)*sx
            y0,y1=origin[1]+row*sy*reg['y_direction'],origin[1]+(row+1)*sy*reg['y_direction']
            runs.append(box(x0,min(y0,y1),x1,max(y0,y1)))
            encoded_rows[row].append([start,last+1])
            start=last=col
    if not runs:
        raise ValueError('judge_empty_mask')
    mask_record=dict(width=int(mask.shape[1]),height=int(mask.shape[0]),encoding='row-runs',rows=encoded_rows)
    inputs=_module('cad_verify_v4_inputs')
    evidence = dict(source_sha256=asset['digest'],registration=reg,
                    mask_sha256=inputs.canonical_sha(mask_record),
                    decoded_rgba_sha256=_module('cad_verify_v4_ledger').sha(rgba.tobytes(order='C')),
                    pixel_convention='pixel_cells_corner_origin',foreground=fg)
    region = unary_union(runs)
    return (region, evidence, _digital_mask_analysis(mask, reg)) if digital else (region, evidence)


def _bounds(shape):
    b=shape.BoundBox
    return [b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax]


def _shape_record(shape, z):
    import FreeCAD as App
    loops=[]
    for wire in shape.slice(App.Vector(0,0,1),_number(z,'projection_z_mm')):
        if not wire.isClosed() or not wire.isValid():
            raise Unknown('output_projection_wire_not_closed_valid')
        segments, curves, joins = [], [], []
        error = 0.
        for edge in wire.OrderedEdges:
            first, last = edge.FirstParameter, edge.LastParameter
            if edge.Orientation == 'Reversed':
                first, last = last, first
            p0=edge.valueAt(first); p1=edge.valueAt(last)
            vertices = edge.Vertexes
            if not vertices:
                raise Unknown('output_projection_vertex_missing')
            start_vertex = min(vertices, key=lambda vertex: (vertex.Point-p0).Length)
            end_vertex = min(vertices, key=lambda vertex: (vertex.Point-p1).Length)
            for point, vertex in ((p0, start_vertex), (p1, end_vertex)):
                numerical = 256*math.ulp(max(1., abs(point.x), abs(point.y), abs(point.z)))
                bound = max(edge.getTolerance(1), vertex.getTolerance(1)) + numerical
                if (point-vertex.Point).Length > bound:
                    raise Unknown('output_projection_vertex_curve_inconsistent')
                error = max(error, bound)
            joins.append((start_vertex, end_vertex, p0, p1))
            curve=type(edge.Curve).__name__
            if curve in ('Line','LineSegment'):
                segments.append(dict(kind='line',p0=[p0.x,p0.y],p1=[p1.x,p1.y]))
                curves.append((edge, first, last))
            elif curve=='Circle':
                # Full circle is split to avoid coincident three-point arc endpoints.
                parts=2 if math.dist((p0.x,p0.y),(p1.x,p1.y)) < 1e-8 else 1
                for i in range(parts):
                    params=[first+(last-first)*(i+t)/parts for t in (0,.5,1)]
                    pts=[edge.valueAt(t) for t in params]
                    segments.append(dict(kind='arc',p0=[pts[0].x,pts[0].y],pm=[pts[1].x,pts[1].y],p1=[pts[2].x,pts[2].y]))
                    curves.append((edge, params[0], params[-1]))
            else:
                raise Unknown('output_projection_curve:'+curve)
        for previous, current in zip(joins[-1:]+joins[:-1], joins):
            if not previous[1].isSame(current[0]):
                raise Unknown('output_projection_shared_vertex_missing')
            error = max(error, (previous[3]-current[2]).Length)
        loops.append(_NativeLoop(segments, curves, error))
    if not loops:
        raise Unknown('output_projection_empty')
    # Classify by geometric containment independently, not by wire order/orientation.
    from shapely.geometry import Polygon
    polys=[]
    for loop in loops:
        points, _ = _loop_points(loop, 1e-5)
        polys.append(Polygon(points))
    for i,loop in enumerate(loops):
        depth=sum(p.contains(polys[i]) for j,p in enumerate(polys) if j!=i)
        loop['role']='hole' if depth%2 else 'outer'
    return dict(units='mm',loops=loops)


def _reference(manifest, prepared, c):
    import FreeCAD as App
    import Part
    _required(c,'asset_id','translation_mm','rotation_axis','rotation_deg')
    asset=_module('cad_verify_v4_inputs').resolve_asset(manifest,c['asset_id'],'step')
    shape=Part.Shape();shape.read(str(asset['path']))
    translation=_vector(c['translation_mm'],3,'translation_mm')
    axis=_vector(c['rotation_axis'],3,'rotation_axis')
    angle=_number(c['rotation_deg'],'rotation_deg')
    if math.sqrt(sum(x*x for x in axis))==0:
        raise ValueError('judge_zero_rotation_axis')
    shape.Placement=App.Placement(App.Vector(*translation),App.Rotation(App.Vector(*axis),angle)).multiply(shape.Placement)
    facts=prepared['assets'].get(c['asset_id'])
    if not facts or facts.get('source_sha256')!=asset['digest']:
        raise Unknown('reference_facts_digest_missing_or_changed')
    return shape, facts, asset['digest']


def _selected_reference_face(ref, facts, face_id, tolerance):
    import re
    match=re.fullmatch(r'Face([1-9][0-9]*)',str(face_id))
    selected=[f for f in facts['faces'] if f['id']==face_id]
    if not match or len(selected)!=1 or selected[0].get('ambiguous'):
        raise Unknown('reference_face_ambiguous_or_unknown')
    index=int(match.group(1))-1
    if index>=len(ref.Faces):
        raise Unknown('reference_face_unknown')
    face=ref.Faces[index]
    for j,other in enumerate(ref.Faces):
        if j==index or type(other.Surface).__name__!=type(face.Surface).__name__:
            continue
        if (abs(other.Area-face.Area)<=tolerance*max(1.,math.sqrt(face.Area))
                and (other.CenterOfMass-face.CenterOfMass).Length<=tolerance
                and max(abs(a-b) for a,b in zip(_bounds(other),_bounds(face)))<=tolerance):
            overlap=face.common(other).Area
            if overlap>=face.Area-tolerance*max(1.,math.sqrt(face.Area)):
                raise Unknown('reference_face_duplicate_native_geometry')
    return face


def _reference_region(shape, manifest, prepared, criterion, tolerance):
    """Whole selected-face coverage, including nonplanar original STEP faces."""
    _required(criterion,'face_ids')
    ref,facts,digest=_reference(manifest,prepared,criterion)
    identifiers=criterion['face_ids']
    if not identifiers or len(set(identifiers))!=len(identifiers):
        raise ValueError('judge_region_face_ids')
    faces=[_selected_reference_face(ref,facts,name,tolerance) for name in identifiers]
    gaps=[face.distToShape(shape)[0] for face in faces]
    contact=sum(face.common(shape).Area for face in faces)
    if any(not math.isfinite(value) or value<0 for value in gaps) or not math.isfinite(contact):
        raise Unknown('native_region_measurement_invalid')
    measured=dict(minimum_gap_mm=min(gaps),exact_contact_area_mm2=contact,
                  face_gaps_mm=dict(zip(identifiers,gaps)),selected_area_mm2=sum(face.Area for face in faces))
    evidence=dict(source_sha256=digest,original_face_ids=identifiers,coverage='complete_selected_faces',
                  contact_definition='exact_original_face_common_candidate_area_not_offset_neighborhood')
    if criterion['metric']=='reference_clearance':
        _required(criterion,'minimum_gap_mm','strict_separation')
        target=_number(criterion['minimum_gap_mm'],'minimum_gap_mm',0)
        lower=max(0.,min(gaps)-tolerance);upper=min(gaps)+tolerance
        measured.update(lower_gap_mm=lower,upper_gap_mm=upper)
        if criterion['strict_separation']:
            status='PASS' if lower>target else 'FAIL' if upper<=target else 'UNVERIFIED'
        else:
            status=_interval_status(lower,upper,target,minimum=True)
        return status,measured,target,tolerance,evidence
    _required(criterion,'maximum_contact_area_mm2','area_uncertainty_mm2')
    target=_number(criterion['maximum_contact_area_mm2'],'maximum_contact_area_mm2',0)
    uncertainty=_number(criterion['area_uncertainty_mm2'],'area_uncertainty_mm2',0)
    lower=max(0.,contact-uncertainty);upper=contact+uncertainty
    measured.update(lower_contact_mm2=lower,upper_contact_mm2=upper)
    return _interval_status(lower,upper,target),measured,target,uncertainty,evidence


def _reference_gap(shape,manifest,prepared,c,tol):
    import FreeCAD as App
    _required(c,'face_id','candidate_face_index','expected_gap_mm','normal','contact_area_min_mm2','contact_tolerance_mm')
    ref,facts,digest=_reference(manifest,prepared,c)
    face=_selected_reference_face(ref,facts,c['face_id'],tol)
    ci=c['candidate_face_index']
    if isinstance(ci,bool) or not isinstance(ci,int) or not 1<=ci<=len(shape.Faces):
        raise ValueError('judge_candidate_face_index')
    candidate=shape.Faces[ci-1]
    normal=_vector(c['normal'],3,'normal')
    length=math.sqrt(sum(x*x for x in normal))
    if abs(length-1)>1e-8:
        raise ValueError('judge_gap_normal_not_unit')
    n=App.Vector(*normal)
    if type(face.Surface).__name__!='Plane' or type(candidate.Surface).__name__!='Plane':
        raise Unknown('selected_face_not_planar')
    # Maximum vertex plane residual and parallel normals reject a minimum-distance shortcut.
    refn=face.normalAt(0,0);candn=candidate.normalAt(0,0)
    if abs(abs(refn.dot(n))-1)>1e-8 or abs(abs(candn.dot(n))-1)>1e-8:
        return 'FAIL',None,dict(reason='face_normal_mismatch',source_sha256=digest)
    signed=[(v.Point-face.CenterOfMass).dot(n) for v in candidate.Vertexes]
    gap=sum(signed)/len(signed)
    spread=max(signed)-min(signed)
    moved=candidate.copy();moved.translate(n.multiply(-gap))
    area=face.common(moved).Area
    target=_number(c['expected_gap_mm'],'expected_gap_mm')
    contact_tol=_number(c['contact_tolerance_mm'],'contact_tolerance_mm',0)
    minimum=_number(c['contact_area_min_mm2'],'contact_area_min_mm2',0)
    passed=abs(gap-target)<=tol and spread<=tol and area>=minimum
    if abs(target)<=contact_tol:
        passed=passed and abs(gap)<=contact_tol
    return 'PASS' if passed else 'FAIL',dict(signed_gap_mm=gap,face_gap_spread_mm=spread,projected_contact_mm2=area),dict(source_sha256=digest,original_face_id=c['face_id'],normal=list(normal))


def _translation_clearance(shape,manifest,prepared,c):
    import FreeCAD as App
    _required(c,'direction','interval_mm','samples','penetration_tolerance_mm3')
    ref,_,digest=_reference(manifest,prepared,c)
    direction=_vector(c['direction'],3,'direction');length=math.sqrt(sum(x*x for x in direction))
    if abs(length-1)>1e-8:
        raise ValueError('judge_play_direction_not_unit')
    lo,hi=_vector(c['interval_mm'],2,'interval_mm')
    n=c['samples']
    if lo>hi or isinstance(n,bool) or not isinstance(n,int) or n<2:
        raise ValueError('judge_play_interval_or_samples')
    limit=_number(c['penetration_tolerance_mm3'],'penetration_tolerance_mm3',0)
    maximum=0.
    for i in range(n):
        moved=ref.copy();moved.translate(App.Vector(*direction).multiply(lo+(hi-lo)*i/(n-1)))
        maximum=max(maximum,shape.common(moved).Volume)
    # Translating a finite-perimeter solid changes its volume of overlap by at
    # most surface area times translation distance (BV translation inequality).
    uncertainty=ref.Area*(hi-lo)/(n-1)/2
    status=_interval_status(maximum,maximum+uncertainty,limit)
    return status,dict(sampled_max_penetration_mm3=maximum,upper_penetration_mm3=maximum+uncertainty),dict(volume_lipschitz_mm2=ref.Area,covering_mm=(hi-lo)/(n-1)/2,source_sha256=digest,claim='declared_translation_interval_only')


def _reference_play(shape,manifest,prepared,c,tolerance):
    """Bound the connected translation component using actual collision barriers."""
    import FreeCAD as App
    _required(c,'direction','interval_mm','samples','penetration_tolerance_mm3',
              'volume_uncertainty_mm3','position_tolerance_mm','maximum_play_mm','convention')
    ref,_,digest=_reference(manifest,prepared,c)
    if not ref.Solids or ref.Volume<=0:
        raise Unknown('play_requires_solid_reference')
    direction=_vector(c['direction'],3,'direction')
    if abs(math.sqrt(sum(x*x for x in direction))-1)>1e-8:
        raise ValueError('judge_play_direction_not_unit')
    lo,hi=_vector(c['interval_mm'],2,'interval_mm')
    count=c['samples']
    if lo>0 or hi<0 or lo==hi or isinstance(count,bool) or not isinstance(count,int) or count<2:
        raise ValueError('judge_play_search_must_contain_datum')
    limit=_number(c['penetration_tolerance_mm3'],'penetration_tolerance_mm3',0)
    volume_error=_number(c['volume_uncertainty_mm3'],'volume_uncertainty_mm3',0)
    resolution=_number(c['position_tolerance_mm'],'position_tolerance_mm',0)
    target=_number(c['maximum_play_mm'],'maximum_play_mm',0)
    if resolution==0 or c['convention'] not in ('total','positive','negative'):
        raise ValueError('judge_play_resolution_or_convention')
    evaluations=0
    def measure(distance,sign):
        nonlocal evaluations
        moved=ref.copy()
        moved.translate(App.Vector(*direction).multiply(sign*distance))
        overlap=shape.common(moved).Volume
        gap=shape.distToShape(moved)[0]
        evaluations+=1
        if not math.isfinite(overlap) or not math.isfinite(gap):
            raise Unknown('play_native_measurement_invalid')
        return overlap,gap
    nominal,gap=measure(0.,1)
    if nominal-volume_error>limit:
        return 'FAIL',dict(nominal_penetration_mm3=nominal,lower_play_mm=0.,upper_play_mm=0.),dict(
            source_sha256=digest,reason='datum_interpenetrates',convention=c['convention'])
    if nominal+volume_error>limit:
        raise Unknown('play_datum_penetration_uncertain')
    def side(extent,sign):
        reachable=min(extent,max(0.,gap-tolerance))
        barrier=None
        previous=0.
        for index in range(1,count):
            distance=extent*index/(count-1)
            overlap,clearance=measure(distance,sign)
            if overlap-volume_error>limit:
                a,b=previous,distance
                while b-a>resolution:
                    middle=(a+b)/2
                    if middle==a or middle==b:
                        raise Unknown('play_position_resolution_not_representable')
                    middle_overlap,_=measure(middle,sign)
                    if middle_overlap-volume_error>limit:
                        b=middle
                    else:
                        a=middle
                barrier=b
                break
            if overlap+volume_error<=limit:
                margin=max(0.,clearance-tolerance)
                # Distance is 1-Lipschitz under a unit translation. Joining
                # overlapping positive-clearance intervals certifies a path;
                # isolated free samples do not prove traversability.
                if distance-margin<=reachable:
                    reachable=max(reachable,min(extent,distance+margin))
            previous=distance
        return dict(free_mm=reachable,blocked_mm=barrier,search_extent_mm=extent)
    positive=side(hi,1)
    negative=side(-lo,-1)
    selected=[positive,negative] if c['convention']=='total' else [positive if c['convention']=='positive' else negative]
    lower=sum(item['free_mm'] for item in selected)
    upper=None if any(item['blocked_mm'] is None for item in selected) else sum(item['blocked_mm'] for item in selected)
    status='PASS' if upper is not None and upper<=target else 'FAIL' if lower>target else 'UNVERIFIED'
    return status,dict(lower_play_mm=lower,upper_play_mm=upper,positive=positive,negative=negative,
                       nominal_penetration_mm3=nominal,volume_uncertainty_mm3=volume_error),dict(
        source_sha256=digest,convention=c['convention'],evaluations=evaluations,
        claim='connected_collision_free_translation_component_about_registered_datum',
        no_claim='rotation_friction_compliance_or_six_DOF_fit')


def _engravings(shape,body,plan,manifest,c,tol,context):
    import FreeCAD as App
    import Part
    _required(c,'index','minimum_removed_mm3','depth_tolerance_mm')
    index=c['index']
    if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(plan.get('engravings',[])):
        raise ValueError('judge_engraving_index')
    engraving=plan['engravings'][index]
    outline=_module('cad_verify_v4_text').text_outline(manifest,engraving['font_id'],engraving['text'],engraving['height_mm'])
    wires=[]
    for loop in outline['loops']:
        edges=[]
        for s in loop['segments']:
            if s['kind']=='line':
                edges.append(Part.makeLine(App.Vector(*s['p0'],0),App.Vector(*s['p1'],0)))
            elif s['kind']=='bezier':
                curve=Part.BezierCurve();curve.setPoles([App.Vector(*p,0) for p in s['poles']]);edges.append(curve.toShape())
            elif s['kind']=='arc':
                edges.append(Part.Arc(App.Vector(*s['p0'],0),App.Vector(*s['pm'],0),App.Vector(*s['p1'],0)).toShape())
            else:
                raise Unknown('engraving_curve_unsupported')
        wires.append(Part.Wire(edges))
    # Native face maker handles nesting/counters; independent from compiler's cut path.
    face=Part.makeFace(wires,'Part::FaceMakerBullseye')
    depth=_number(engraving['depth_mm'],'depth_mm',0)
    depth_tol=_number(c['depth_tolerance_mm'],'depth_tolerance_mm',0)
    if depth<=depth_tol:
        raise Unknown('engraving_depth_not_resolved')
    placement=App.Placement(App.Vector(*engraving['origin_mm']),App.Rotation(App.Vector(*engraving['rotation_axis']),engraving['rotation_deg']))
    cutter=face.extrude(App.Vector(0,0,-depth));cutter.Placement=placement
    baseline=context.get('baseline_shapes', {}).get(index, context.get('baseline_shape'))
    if baseline is None and context.get('allow_history_baseline', True) and hasattr(body, 'Group'):
        feature = next((o for o in body.Group if o.Name == 'Engraving' + str(index)), None)
        if feature is not None and hasattr(feature, 'Base'):
            baseline = feature.Base.Shape
    if baseline is None and context.get('allow_history_baseline', True) and hasattr(body,'Group'):
        group=[o for o in body.Group if hasattr(o,'Shape') and not o.Shape.isNull()]
        for obj in group:
            if getattr(obj,'Name','').lower().startswith(('base','stock','contourextrude')):
                baseline=obj.Shape;break
    if baseline is None:
        raise Unknown('engraving_baseline_missing')
    expected=baseline.common(cutter)
    removed=expected.Volume-shape.common(expected).Volume
    remaining=shape.common(expected).Volume
    # Ink counters are retained stock, not merely absent expected cutter volume.
    # Without measuring them, an O-shaped recess and a filled square recess
    # would receive the same glyph score. Use the same card-derived volume bound.
    counter_stock = None
    for loop, wire in zip(outline['loops'], wires):
        if loop['role'] == 'hole':
            counter = Part.Face(wire).extrude(App.Vector(0,0,-depth))
            counter.Placement = placement
            stock = baseline.common(counter).cut(cutter)
            counter_stock = stock if counter_stock is None else counter_stock.fuse(stock)
    counter_lost = (0. if counter_stock is None else
                    max(0., counter_stock.Volume-shape.common(counter_stock).Volume))
    vol_tol=max(tol,depth_tol)*face.Area
    minimum=_number(c['minimum_removed_mm3'],'minimum_removed_mm3',0)
    # A slab just below the declared depth must remain; this distinguishes a
    # real declared-depth recess from a through-cut or over-deep pocket.
    guard=face.extrude(App.Vector(0,0,-(depth+depth_tol)))
    deeper=face.extrude(App.Vector(0,0,-(depth+2*depth_tol)))
    guard.Placement=placement;deeper.Placement=placement
    below=baseline.common(deeper).cut(guard)
    lost_below=below.Volume-shape.common(below).Volume
    depth_volume_tol=tol*face.Area
    status='PASS' if removed>=minimum and expected.Volume>=minimum and remaining<=vol_tol and counter_lost<=vol_tol and lost_below<=depth_volume_tol else 'FAIL'
    return status,dict(expected_cut_mm3=expected.Volume,removed_mm3=removed,remaining_in_glyph_mm3=remaining,lost_counter_stock_mm3=counter_lost,lost_below_depth_mm3=lost_below),dict(font_sha256=outline['font_sha256'],text=engraving['text'],depth_mm=depth,volume_uncertainty_mm3=vol_tol,claim='recessed_font_geometry_with_counters')


def _contour_registration(data, prepared=None):
    """One fixed-frame metrology registration for owned and neutral inputs."""
    if data.get('schema') == 'cad-harness.artifact-context.v4':
        registration = data.get('contour')
        if not registration:
            raise Unknown('contour_measurement_registration_missing')
        return registration
    if data.get('family') != 'contour_extrude':
        raise Unknown('output_section_requires_matching_contour_family')
    registration = dict(contour_id=data['contour_id'], origin_mm=data['origin_mm'],
                        thickness_mm=data['thickness_mm'])
    if prepared is not None:
        record = prepared['assets'][data['contour_id']]
        registration['scale'] = data['width_mm'] / record['nominal_width_mm']
    return registration


def _output_section(plan, shape, criterion):
    """Remeasure the handed-over extrusion, including operative size changes."""
    registration = _contour_registration(plan)
    if criterion['contour_id'] != registration['contour_id']:
        raise Unknown('output_section_requires_matching_contour_family')
    origin = _vector(registration['origin_mm'], 3, 'origin_mm')
    thickness = _number(registration['thickness_mm'], 'thickness_mm', 0)
    z = criterion.get('projection_z_mm', origin[2] + thickness / 2)
    return _shape_record(shape, z), z


def _expected_solid_count(data, prepared):
    c2 = data.get('profile') == 'c-s1' and (
        data.get('schema') == 'cad-harness.artifact-context.v4' and data.get('family') == 'C2'
        or data.get('family') == 'contour_extrude')
    if not c2:
        return 1
    registration = _contour_registration(data)
    record = prepared['assets'].get(registration['contour_id'])
    # Missing multi-piece authority cannot relax the default one-solid gate.
    if not record:
        return 1
    if record.get('recipe', {}).get('topology', {}).get('components') != 'preserve':
        return 1
    return _module('cad_verify_v4_inputs').contour_solid_count(record)


def judge(plan, manifest_path, prepared, body_or_shape, card, **context):
    """Judge actual candidate against original assets and explicit independent card.

    native_evidence is optional external reopen evidence. baseline_shape can be
    supplied for engraving; otherwise the native base/stock feature is used.
    No acceptance value is inferred from compiler/preprocessor reports.
    """
    validate_card(card)
    shape=getattr(body_or_shape,'Shape',body_or_shape)
    checks=[]
    for c in card['criteria']:
        metric=c['metric']
        try:
            if 'linear_tolerance_mm' not in card:
                raise Unknown('missing_required:linear_tolerance_mm')
            tol=_number(card['linear_tolerance_mm'],'linear_tolerance_mm',0)
            if metric=='solid_valid':
                expected = _expected_solid_count(plan, prepared)
                valid=not shape.isNull() and shape.isValid() and len(shape.Solids)==expected and shape.Volume>0
                checks.append(_check(c,'PASS' if valid else 'FAIL',dict(valid=shape.isValid(),solids=len(shape.Solids),volume_mm3=shape.Volume),dict(valid=True,solids=expected),0,0,source='actual_native_brep'))
            elif metric=='bounds':
                _required(c,'expected_mm');target=_vector(c['expected_mm'],6,'expected_mm');actual=_bounds(shape)
                error=max(abs(a-b) for a,b in zip(actual,target))
                checks.append(_check(c,'PASS' if error<=tol else 'FAIL',actual,list(target),tol,0,maximum_absolute_error_mm=error))
            elif metric=='volume':
                _required(c,'expected_mm3','tolerance_mm3');target=_number(c['expected_mm3'],'expected_mm3',0);vt=_number(c['tolerance_mm3'],'tolerance_mm3',0)
                checks.append(_check(c,'PASS' if abs(shape.Volume-target)<=vt else 'FAIL',shape.Volume,target,vt,0,source='native_volume'))
            elif metric=='unchanged_dimension':
                _required(c,'axis','expected_mm')
                if c['axis'] not in ('X','Y','Z'):raise ValueError('judge_dimension_axis')
                i={'X':0,'Y':2,'Z':4}[c['axis']];b=_bounds(shape);actual=b[i+1]-b[i];target=_number(c['expected_mm'],'expected_mm',0)
                checks.append(_check(c,'PASS' if abs(actual-target)<=tol else 'FAIL',actual,target,tol,0,axis=c['axis'],definition='source_axis_extent_not_thickness'))
            elif metric=='reference_gap':
                status,actual,evidence=_reference_gap(shape,manifest_path,prepared,c,tol)
                checks.append(_check(c,status,actual,c['expected_gap_mm'],tol,0,**evidence))
            elif metric in ('reference_clearance','reference_contact'):
                status,actual,target,uncertainty,evidence=_reference_region(shape,manifest_path,prepared,c,tol)
                checks.append(_check(c,status,actual,target,None,uncertainty,**evidence))
            elif metric=='translation_clearance':
                status,actual,evidence=_translation_clearance(shape,manifest_path,prepared,c)
                checks.append(_check(c,status,actual,c['interval_mm'],c['penetration_tolerance_mm3'],actual['upper_penetration_mm3']-actual['sampled_max_penetration_mm3'],**evidence))
            elif metric=='reference_play':
                status,actual,evidence=_reference_play(shape,manifest_path,prepared,c,tol)
                upper=actual['upper_play_mm']
                checks.append(_check(c,status,actual,c['maximum_play_mm'],c['position_tolerance_mm'],
                                     None if upper is None else upper-actual['lower_play_mm'],**evidence))
            elif metric=='engraving':
                status,actual,evidence=_engravings(shape,body_or_shape,plan,manifest_path,c,tol,context)
                checks.append(_check(c,status,actual,dict(index=c['index'],minimum_removed_mm3=c['minimum_removed_mm3']),c['depth_tolerance_mm'],evidence['volume_uncertainty_mm3'],**evidence))
            elif metric=='native_roundtrip':
                _required(c,'maximum_bounds_difference_mm','maximum_volume_difference_mm3','require_editable')
                ev=context.get('native_evidence')
                if not isinstance(ev,dict):raise Unknown('native_reopen_evidence_missing')
                _required(ev,'fcstd_reopened','step_reopened','editable','bounds_difference_mm','volume_difference_mm3')
                for flag in ('fcstd_reopened','step_reopened','editable'):
                    if not isinstance(ev[flag],bool):
                        raise ValueError('judge_native_evidence_boolean')
                _number(ev['bounds_difference_mm'],'bounds_difference_mm',0)
                _number(ev['volume_difference_mm3'],'volume_difference_mm3',0)
                passed=ev['fcstd_reopened'] is True and ev['step_reopened'] is True and (not c['require_editable'] or ev['editable'] is True) and ev['bounds_difference_mm']<=c['maximum_bounds_difference_mm'] and ev['volume_difference_mm3']<=c['maximum_volume_difference_mm3']
                checks.append(_check(c,'PASS' if passed else 'FAIL',ev,c,None,0,source='independent_native_reopen'))
            else:
                _required(c,'contour_id')
                record=prepared['assets'].get(c['contour_id'])
                if not record:raise Unknown('contour_missing')
                if metric=='min_radius':
                    _required(c,'minimum_mm','angular_tolerance_rad')
                    output, z = _output_section(plan, shape, c)
                    r=minimum_radius(output,c['angular_tolerance_rad']);target=_number(c['minimum_mm'],'minimum_mm',0)
                    if r['unbounded']:
                        status = 'PASS'
                    else:
                        radius_error = tol+r['native_error_mm']
                        lower, upper = max(0., r['minimum_mm']-radius_error), r['minimum_mm']+radius_error
                        status = _interval_status(lower, upper, target, minimum=True)
                        r.update(lower_mm=lower, upper_mm=upper)
                    checks.append(_check(c,status,r,target,None,tol+r['native_error_mm'],
                                         source='actual_native_section_line_arc_geometry',projection_z_mm=z))
                elif metric=='tool_access':
                    output, z = _output_section(plan, shape, c)
                    result=tool_access(output,c);checks.append(_check(c,result['status'],result,c['maximum_uncovered_mm2'],c['area_uncertainty_mm2'],result['uncovered_upper_mm2']-result['uncovered_lower_mm2'],claim='actual_output_planar_disk_center_only',projection_z_mm=z))
                else:
                    _required(c,'leg','curve_tolerance_mm')
                    if c['leg'] not in ('image_to_contour','contour_to_output'):raise ValueError('judge_fidelity_leg')
                    a,ea=planar_geometry(record,c['curve_tolerance_mm'])
                    evidence=dict(leg=c['leg'],contour_id=c['contour_id'])
                    digital_v2 = _digital_v2(record)
                    canonical_separated = (_candidate_separated(record, c['curve_tolerance_mm'])
                                           if digital_v2 else True)
                    if c['leg']=='image_to_contour':
                        expected_image=record.get('source_image_asset_id',record.get('asset_id'))
                        transform=record['pixel_to_mm'];scale=transform['scale_mm_per_pixel']
                        registered=dict(origin_mm=[transform['origin_mm'][0],transform['origin_mm'][1]+transform['image_height_pixels']*scale],
                                        pixel_size_mm=[scale,scale],y_direction=-1)
                        if c.get('mask_asset_id')!=expected_image or c.get('registration')!=registered:
                            checks.append(_check(c,'FAIL',reason='source_image_or_registration_not_bound_to_contour'))
                            continue
                        if digital_v2:
                            if c['foreground'] != _source_mask_criterion(record)['foreground']:
                                checks.append(_check(c,'FAIL',reason='source_foreground_not_bound_to_recipe'))
                                continue
                            b,mask_evidence,digital_source=_mask_region(manifest_path,c,digital=True)
                        else:
                            b,mask_evidence=_mask_region(manifest_path,c)
                        eb=0.;evidence.update(mask_evidence)
                        if not _mask_commitment_matches(record,mask_evidence):
                            checks.append(_check(c,'FAIL',reason='decoded_image_or_mask_commitment_mismatch'))
                            continue
                    else:
                        _required(c,'projection_z_mm')
                        output_record=_shape_record(shape,c['projection_z_mm'])
                        b,eb=planar_geometry(output_record,c['curve_tolerance_mm'])
                        if digital_v2:
                            _,mask_evidence,digital_source=_mask_region(
                                manifest_path,_source_mask_criterion(record),digital=True)
                            if not _mask_commitment_matches(record,mask_evidence):
                                checks.append(_check(c,'FAIL',reason='decoded_image_or_mask_commitment_mismatch'))
                                continue
                            canonical_matches=_digital_nesting_matches(digital_source,a)
                            canonical_openings=_pinch_openings(record,digital_source,a,ea)
                            output_separated=_candidate_separated(output_record,c['curve_tolerance_mm'])
                        # Fixed preregistered scale/origin, never candidate bbox fitting.
                        registration = _contour_registration(plan, prepared)
                        if c['contour_id'] != registration['contour_id']:
                            raise Unknown('contour_output_registration_mismatch')
                        from shapely.affinity import scale,translate
                        factor = _number(registration['scale'], 'scale', 0)
                        origin = _vector(registration['origin_mm'], 3, 'origin_mm')
                        a=translate(scale(a,xfact=factor,yfact=factor,origin=(0,0)),xoff=origin[0],yoff=origin[1]);ea*=factor
                        evidence['registration']=dict(scale=factor,origin_mm=list(origin),projection_z_mm=c['projection_z_mm'])
                    if digital_v2:
                        source_topology=digital_source['topology']
                        target_topology=_topology(a if c['leg']=='image_to_contour' else b)
                        if c['leg']=='image_to_contour':
                            openings=_pinch_openings(record,digital_source,a,ea)
                            topology_matches=(canonical_separated
                                and _digital_nesting_matches(digital_source,a)
                                and openings['listing_matches'] and openings['cleared'])
                        else:
                            openings=_pinch_openings(record,digital_source,b,eb,factor,origin[:2])
                            topology_matches=(canonical_separated and output_separated
                                and canonical_matches and canonical_openings['listing_matches']
                                and canonical_openings['cleared']
                                and _digital_nesting_matches(digital_source,b,factor,origin[:2])
                                and openings['listing_matches'] and openings['cleared'])
                            evidence['canonical_pinch_openings']=canonical_openings
                        evidence.update(connectivity=dict(foreground=4,background=8,pinch='remove_locally'),
                                        pinch_openings=openings,canonical_separated=canonical_separated)
                    else:
                        source_topology,target_topology=_topology(a),_topology(b)
                        topology_matches=source_topology==target_topology and _nesting_matches(a,b)
                    evidence.update(source_topology=source_topology,target_topology=target_topology,
                                    topology_matches=topology_matches)
                    if metric=='boundary_hausdorff':
                        _required(c,'maximum_mm','sampling_step_mm');bound=hausdorff_bounds(a,b,c['sampling_step_mm'],ea,eb);limit=_number(c['maximum_mm'],'maximum_mm',0)
                        status=_interval_status(bound['lower_mm'],bound['upper_mm'],limit) if topology_matches else 'FAIL'
                        checks.append(_check(c,status,bound,limit,None,bound['upper_mm']-bound['lower_mm'],**evidence))
                    elif metric=='image_iou':
                        _required(c,'minimum_iou');limit=_number(c['minimum_iou'],'minimum_iou',0)
                        if limit>1:raise ValueError('judge_iou_range')
                        # Morphological envelopes bound area under boundary uncertainty.
                        ai,ao=_envelope(a,ea);bi,bo=_envelope(b,eb)
                        lower=ai.intersection(bi).area/ao.union(bo).area
                        upper=min(1.,ao.intersection(bo).area/max(ai.union(bi).area,1e-300))
                        actual=dict(nominal=a.intersection(b).area/a.union(b).area,lower=lower,upper=upper)
                        status=_interval_status(lower,upper,limit,minimum=True) if topology_matches else 'FAIL'
                        checks.append(_check(c,status,actual,limit,None,upper-lower,**evidence))
                    else:raise ValueError('judge_unhandled_metric')
        except Unknown as exc:
            checks.append(_check(c,'UNVERIFIED',reason=str(exc)))
        except (ValueError,KeyError,TypeError,IndexError,AttributeError,RuntimeError,OSError,OverflowError) as exc:
            checks.append(_check(c,'UNVERIFIED',reason='invalid_or_missing_input:'+str(exc)))
    status='FAIL' if any(x['status']=='FAIL' for x in checks) else 'UNVERIFIED' if any(x['status']!='PASS' for x in checks) else 'PASS'
    return dict(schema=SCHEMA,profile='c-s1',status=status,checks=checks)
