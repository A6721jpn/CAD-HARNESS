"""C5 immutable-reference freeform patch reconstruction, native c-s3 only.

A finite, oriented tensor grid is joined in an explicit affine chart, then OCCT
knot removal enforces parametric C2. Geometric regularity and actual deviation
remain independent C6 proof obligations. No fitter estimate is an acceptance
verdict. The source boundary is retained and the region is sewn into its solid.
"""
import hashlib
import json
import math
from pathlib import Path
import tempfile


class UnsupportedDomain(NotImplementedError):
    """A missing numerical-domain capability is not a verified rejection."""


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '') + name)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def validate_plan(plan, manifest_path=None, prepared=None):
    return _module('cad_verify_v4_s3_contracts').validate_plan(plan, manifest_path, prepared)


def _solid(shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError('surface_rebuild_single_valid_solid_required')
    solid = shape.Solids[0]
    if any(len(getattr(shape, key)) != len(getattr(solid, key)) for key in ('Faces', 'Edges', 'Vertexes')):
        raise ValueError('surface_rebuild_loose_geometry')
    if not solid.Shells or any(not shell.isClosed() for shell in solid.Shells):
        raise ValueError('surface_rebuild_closed_boundary_required')
    return shape


def _from_brep(value):
    import Part
    shape = Part.Shape()
    shape.importBrepFromString(value, False)
    return shape


def _bounds(shape):
    b = shape.BoundBox
    return [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax]


def _native_selection(shape, record, selection):
    """Recompute signatures and actual shared-edge adjacency, never guess FaceN."""
    inputs = _module('cad_verify_v4_inputs')
    precision = record['signature_precision_mm']
    signatures = []
    for face in shape.Faces:
        normal = None
        try:
            u0, u1, v0, v1 = face.ParameterRange
            n = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            if n.Length > 0 and math.isfinite(n.Length):
                normal = [n.x / n.Length, n.y / n.Length, n.z / n.Length]
        except (RuntimeError, ValueError, AttributeError, OverflowError):
            pass
        signatures.append(inputs.canonical_sha(dict(
            surface_type=type(face.Surface).__name__, area_quantized=round(face.Area / precision**2),
            center_quantized=[round(x / precision) for x in face.CenterOfMass],
            bounds_quantized=[round(x / precision) for x in _bounds(face)],
            normal_quantized=None if normal is None else [0.0 if round(x, 12) == 0 else round(x, 12) for x in normal])))
    indices = [i for i, signature in enumerate(signatures) if signature == selection['signature']]
    if len(indices) != 1 or selection['face_id'] != 'Face' + str(indices[0] + 1):
        raise ValueError('surface_rebuild_stale_or_ambiguous_selection')
    index = indices[0]
    face = shape.Faces[index]
    adjacent = ['Face' + str(i + 1) for i, other in enumerate(shape.Faces) if i != index and
                any(a.isSame(b) for a in face.Edges for b in other.Edges)]
    if adjacent != selection['adjacent_face_ids']:
        raise ValueError('surface_rebuild_native_adjacency_mismatch')
    return index


def _surface_data(surface):
    return dict(poles=[[list(point) for point in row] for row in surface.getPoles()],
                weights=[list(row) for row in surface.getWeights()],
                u_knots=list(surface.getUKnots()), v_knots=list(surface.getVKnots()),
                u_mults=list(surface.getUMultiplicities()), v_mults=list(surface.getVMultiplicities()),
                degree_u=surface.UDegree, degree_v=surface.VDegree)


def _surface(data, max_poles):
    import FreeCAD as App
    import Part
    poles, weights = data['poles'], data['weights']
    if not poles or not poles[0] or len(poles) * len(poles[0]) > max_poles:
        raise ValueError('surface_rebuild_pole_resource_limit')
    if any(len(row) != len(poles[0]) for row in poles) or len(weights) != len(poles):
        raise ValueError('surface_rebuild_control_grid')
    if any(len(row) != len(poles[0]) for row in weights):
        raise ValueError('surface_rebuild_weight_grid')
    if any(len(p) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) for x in p)
           for row in poles for p in row):
        raise ValueError('surface_rebuild_nonfinite_poles')
    if any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for row in weights for w in row):
        raise ValueError('surface_rebuild_positive_weights_required')
    surface = Part.BSplineSurface()
    surface.buildFromPolesMultsKnots([[App.Vector(*p) for p in row] for row in poles],
        data['u_mults'], data['v_mults'], data['u_knots'], data['v_knots'], False, False,
        data['degree_u'], data['degree_v'], weights)
    return surface


def _rectangular_trim(face):
    """Reject holes/notches from actual complete p-curves, including tiny ones."""
    import Part
    if len(face.Wires) != 1:
        raise UnsupportedDomain('surface_rebuild_nonrectangular_trim')
    u0, u1, v0, v1 = face.ParameterRange
    numerical = 128 * math.ulp(max(1., *(abs(x) for x in (u0, u1, v0, v1))))
    sides = [[], [], [], []]
    for edge in face.Edges:
        item = face.curveOnSurface(edge)
        if item is None:
            raise UnsupportedDomain('surface_rebuild_trim_curve_unavailable')
        curve, first, last = item
        try:
            if isinstance(curve, Part.Geom2d.Line2d):
                points = [curve.value(first), curve.value(last)]
                weights = [1., 1.]
            elif isinstance(curve, (Part.Geom2d.BSplineCurve2d, Part.Geom2d.BezierCurve2d)):
                spline = curve.copy()
                spline.segment(first, last)
                points = list(spline.getPoles())
                weights = list(spline.getWeights())
            else:
                raise UnsupportedDomain('surface_rebuild_trim_curve_uncertified')
        except (RuntimeError, ValueError, AttributeError, TypeError) as exc:
            raise UnsupportedDomain('surface_rebuild_trim_curve_uncertified') from exc
        if not points or any(w <= 0 or not math.isfinite(w) for w in weights):
            raise UnsupportedDomain('surface_rebuild_trim_weights_unresolved')
        if any(not math.isfinite(x) for point in points for x in (point.x, point.y)):
            raise ValueError('surface_rebuild_nonfinite_trim')
        endpoints = [curve.value(first), curve.value(last)]
        matched = False
        for side, axis, boundary in ((0, 'x', u0), (1, 'x', u1), (2, 'y', v0), (3, 'y', v1)):
            if all(abs(getattr(p, axis) - boundary) <= numerical for p in points):
                other = 'y' if axis == 'x' else 'x'
                low, high = (v0, v1) if axis == 'x' else (u0, u1)
                if any(not low - numerical <= getattr(p, other) <= high + numerical for p in points):
                    raise UnsupportedDomain('surface_rebuild_trim_outside_rectangle')
                sides[side].append(sorted(getattr(p, other) for p in endpoints))
                matched = True
                break
        if not matched:
            raise UnsupportedDomain('surface_rebuild_nonrectangular_trim')
    for side, (low, high) in zip(sides, ((v0, v1), (v0, v1), (u0, u1), (u0, u1))):
        reached = low
        for start, end in sorted(side):
            if start > reached + numerical:
                raise UnsupportedDomain('surface_rebuild_trim_boundary_gap')
            reached = max(reached, end)
        if reached < high - numerical:
            raise UnsupportedDomain('surface_rebuild_trim_boundary_incomplete')


def _finite_patch(face, cell, i, j, plan):
    import Part
    tolerance = plan['kernel_tolerance_mm']
    _rectangular_trim(face)
    surface = face.Surface
    domain = face.ParameterRange
    if isinstance(surface, Part.BezierSurface):
        surface = _surface(dict(
            poles=[[list(point) for point in row] for row in surface.getPoles()],
            weights=[list(row) for row in surface.getWeights()],
            u_knots=[0., 1.], v_knots=[0., 1.],
            u_mults=[surface.UDegree + 1] * 2, v_mults=[surface.VDegree + 1] * 2,
            degree_u=surface.UDegree, degree_v=surface.VDegree), plan['max_poles'])
    elif isinstance(surface, Part.Plane):
        u0, u1, v0, v1 = domain
        surface = _surface(dict(
            poles=[[list(face.valueAt(u, v)) for v in (v0, v1)] for u in (u0, u1)],
            weights=[[1., 1.], [1., 1.]], u_knots=[u0, u1], v_knots=[v0, v1],
            u_mults=[2, 2], v_mults=[2, 2], degree_u=1, degree_v=1), plan['max_poles'])
    elif not isinstance(surface, Part.BSplineSurface):
        raise UnsupportedDomain('surface_rebuild_exact_spline_representation_unavailable')
    if not isinstance(surface, Part.BSplineSurface) or surface.isUPeriodic() or surface.isVPeriodic():
        raise UnsupportedDomain('surface_rebuild_nonperiodic_spline_required')
    surface = surface.copy()
    u0, u1, v0, v1 = domain
    if not all(math.isfinite(x) for x in domain) or u0 >= u1 or v0 >= v1:
        raise ValueError('surface_rebuild_invalid_patch_domain')
    surface.segment(u0, u1, v0, v1)
    finite = surface.toShape()
    # This is construction admission only; C6 independently proves trimmed-domain
    # coverage before using any corresponding-point global-error certificate.
    area_error = tolerance * (face.Length + finite.Length) + tolerance**2 * math.pi * 16
    if face.cut(finite).Area + finite.cut(face).Area > area_error:
        raise UnsupportedDomain('surface_rebuild_nonrectangular_trim')
    data = _surface_data(surface)
    if cell['swap_uv']:
        data['poles'] = [list(row) for row in zip(*data['poles'])]
        data['weights'] = [list(row) for row in zip(*data['weights'])]
        for a, b in (('u_knots', 'v_knots'), ('u_mults', 'v_mults'), ('degree_u', 'degree_v')):
            data[a], data[b] = data[b], data[a]
    for axis, reverse in (('u', cell['reverse_u']), ('v', cell['reverse_v'])):
        if not reverse:
            continue
        if axis == 'u':
            data['poles'].reverse()
            data['weights'].reverse()
        else:
            data['poles'] = [list(reversed(row)) for row in data['poles']]
            data['weights'] = [list(reversed(row)) for row in data['weights']]
        knots = data[axis + '_knots']
        data[axis + '_knots'] = [knots[0] + knots[-1] - value for value in reversed(knots)]
        data[axis + '_mults'].reverse()
    for axis, start in (('u', i), ('v', j)):
        knots = data[axis + '_knots']
        width = knots[-1] - knots[0]
        data[axis + '_knots'] = [start + (k - knots[0]) / width for k in knots]
    if max(data['degree_u'], data['degree_v']) > plan['max_degree']:
        raise ValueError('surface_rebuild_degree_resource_limit')
    return _surface(data, plan['max_poles'])


def _partition(values):
    result = sorted(set(values))
    if any(b - a <= 128 * math.ulp(max(1.0, abs(a), abs(b))) for a, b in zip(result, result[1:])):
        raise UnsupportedDomain('surface_rebuild_unresolved_knot_partition')
    return result


def _insert(surface, axis, knots, multiplicities):
    current = dict(zip(getattr(surface, 'get' + axis.upper() + 'Knots')(),
                       getattr(surface, 'get' + axis.upper() + 'Multiplicities')()))
    for knot, count in zip(knots, multiplicities):
        if current.get(knot, 0) < count:
            getattr(surface, 'insert' + axis.upper() + 'Knot')(knot, count, 0.)


def _shared(a, b, axis):
    if axis == 'u':
        return list(zip(a['poles'][-1], b['poles'][0])), list(zip(a['weights'][-1], b['weights'][0]))
    return list(zip([row[-1] for row in a['poles']], [row[0] for row in b['poles']])), list(zip(
        [row[-1] for row in a['weights']], [row[0] for row in b['weights']]))


def _joined_surface(patches, plan):
    """Construct an actual C0 tensor net, preserving compatible positive weights."""
    nu, nv = len(patches), len(patches[0])
    degree_u = max(3, *(surface.UDegree for row in patches for surface in row))
    degree_v = max(3, *(surface.VDegree for row in patches for surface in row))
    if max(degree_u, degree_v) > plan['max_degree']:
        raise ValueError('surface_rebuild_degree_resource_limit')
    u_parts = [_partition(k for surface in patches[i] for k in surface.getUKnots()) for i in range(nu)]
    v_parts = [_partition(k for row in patches for k in row[j].getVKnots()) for j in range(nv)]
    projected_u = 1 + degree_u * sum(len(knots) - 1 for knots in u_parts)
    projected_v = 1 + degree_v * sum(len(knots) - 1 for knots in v_parts)
    if projected_u * projected_v > plan['max_poles']:
        raise ValueError('surface_rebuild_pole_resource_limit')
    for row in patches:
        for surface in row:
            surface.increaseDegree(degree_u, degree_v)
    for i, row in enumerate(patches):
        for j, surface in enumerate(row):
            _insert(surface, 'u', u_parts[i], [degree_u + 1] + [degree_u] * (len(u_parts[i]) - 2) + [degree_u + 1])
            _insert(surface, 'v', v_parts[j], [degree_v + 1] + [degree_v] * (len(v_parts[j]) - 2) + [degree_v + 1])
    data = [[_surface_data(surface) for surface in row] for row in patches]
    tolerance = plan['kernel_tolerance_mm']
    scales = {(0, 0): 1.0 / data[0][0]['weights'][0][0]}
    for i in range(nu):
        for j in range(nv):
            for a, b, axis in (((i - 1, j), (i, j), 'u'), ((i, j - 1), (i, j), 'v')):
                if min(a) < 0:
                    continue
                pairs, weights = _shared(data[a[0]][a[1]], data[b[0]][b[1]], axis)
                if any(math.dist(x, y) > tolerance for x, y in pairs):
                    raise ValueError('surface_rebuild_grid_boundary_not_coincident')
                ratios = [x * scales[a] / y for x, y in weights]
                factor = sum(ratios) / len(ratios)
                if any(abs(x - factor) > 1e-11 * max(abs(x), abs(factor)) for x in ratios):
                    raise UnsupportedDomain('surface_rebuild_rational_boundary_parameterization')
                if b in scales and abs(scales[b] - factor) > 1e-10 * max(abs(factor), abs(scales[b])):
                    raise ValueError('surface_rebuild_rational_grid_inconsistent')
                scales[b] = factor
    u_sizes = [len(data[i][0]['poles']) for i in range(nu)]
    v_sizes = [len(data[0][j]['poles'][0]) for j in range(nv)]
    u_total, v_total = 1 + sum(n - 1 for n in u_sizes), 1 + sum(n - 1 for n in v_sizes)
    if u_total * v_total > plan['max_poles']:
        raise ValueError('surface_rebuild_pole_resource_limit')
    poles = [[None for _ in range(v_total)] for _ in range(u_total)]
    weights = [[None for _ in range(v_total)] for _ in range(u_total)]
    u_offset = 0
    for i in range(nu):
        v_offset = 0
        for j in range(nv):
            piece = data[i][j]
            if len(piece['poles']) != u_sizes[i] or len(piece['poles'][0]) != v_sizes[j]:
                raise ValueError('surface_rebuild_tensor_partition_mismatch')
            for u, row in enumerate(piece['poles']):
                for v, point in enumerate(row):
                    a, b = u_offset + u, v_offset + v
                    weight = piece['weights'][u][v] * scales[i, j]
                    if not math.isfinite(weight) or weight <= 0:
                        raise ValueError('surface_rebuild_weight_scale')
                    if poles[a][b] is not None:
                        if math.dist(poles[a][b], point) > tolerance:
                            raise ValueError('surface_rebuild_tensor_boundary_mismatch')
                        if abs(weights[a][b] - weight) > 1e-10 * max(weights[a][b], weight):
                            raise ValueError('surface_rebuild_tensor_weight_mismatch')
                        poles[a][b] = [(x + y) / 2 for x, y in zip(poles[a][b], point)]
                        weights[a][b] = (weights[a][b] + weight) / 2
                    else:
                        poles[a][b] = list(point)
                        weights[a][b] = weight
            v_offset += v_sizes[j] - 1
        u_offset += u_sizes[i] - 1
    u_knots = [k for i, knots in enumerate(u_parts) for k in (knots if i == 0 else knots[1:])]
    v_knots = [k for j, knots in enumerate(v_parts) for k in (knots if j == 0 else knots[1:])]
    result = dict(poles=poles, weights=weights, degree_u=degree_u, degree_v=degree_v,
        u_knots=u_knots, v_knots=v_knots,
        u_mults=[degree_u + 1] + [degree_u] * (len(u_knots) - 2) + [degree_u + 1],
        v_mults=[degree_v + 1] + [degree_v] * (len(v_knots) - 2) + [degree_v + 1])
    return _surface(result, plan['max_poles'])


def _align(a, b):
    a, b = a.copy(), b.copy()
    p, q = max(a.UDegree, b.UDegree), max(a.VDegree, b.VDegree)
    a.increaseDegree(p, q)
    b.increaseDegree(p, q)
    for axis in ('u', 'v'):
        ak = getattr(a, 'get' + axis.upper() + 'Knots')()
        bk = getattr(b, 'get' + axis.upper() + 'Knots')()
        am = getattr(a, 'get' + axis.upper() + 'Multiplicities')()
        bm = getattr(b, 'get' + axis.upper() + 'Multiplicities')()
        counts = {}
        for k, m in list(zip(ak, am)) + list(zip(bk, bm)):
            counts[k] = max(m, counts.get(k, 0))
        knots = _partition(counts)
        for surface in (a, b):
            _insert(surface, axis, knots, [counts[k] for k in knots])
    return _surface_data(a), _surface_data(b)


def _pointwise_bound(a, b):
    """Positive-weight partition-of-unity bound in one common spline basis."""
    if not a or len(a) != len(b):
        raise ValueError('surface_rebuild_bound_basis_mismatch')
    origin = a[0][0]
    wa, wb = min(w for _, w in a), min(w for _, w in b)
    numerator_difference = max(math.dist([(x - o) * w for x, o in zip(p, origin)],
                                         [(x - o) * v for x, o in zip(q, origin)])
                               for (p, w), (q, v) in zip(a, b))
    denominator_difference = max(abs(w - v) for (_, w), (_, v) in zip(a, b))
    b_numerator = max(math.dist(q, origin) * v for q, v in b)
    return numerator_difference / wa + b_numerator * denominator_difference / (wa * wb)


def _boundary_bound(before, after):
    a, b = _align(before, after)
    pairs = []
    for row in (0, len(a['poles']) - 1):
        pairs.append((list(zip(a['poles'][row], a['weights'][row])), list(zip(b['poles'][row], b['weights'][row]))))
    for col in (0, len(a['poles'][0]) - 1):
        pairs.append(([(p[col], w[col]) for p, w in zip(a['poles'], a['weights'])],
                      [(p[col], w[col]) for p, w in zip(b['poles'], b['weights'])]))
    return max(_pointwise_bound(x, y) for x, y in pairs)


def _fit(original, facts, plan):
    indices = [[_native_selection(original, facts, cell) for cell in row] for row in plan['grid']]
    if len({i for row in indices for i in row}) != sum(len(row) for row in indices):
        raise ValueError('surface_rebuild_duplicate_native_patch')
    patches = [[_finite_patch(original.Faces[indices[i][j]], cell, i, j, plan)
                for j, cell in enumerate(row)] for i, row in enumerate(plan['grid'])]
    before = _joined_surface(patches, plan)
    fitted = before.copy()
    removed = []
    for axis, degree in (('u', fitted.UDegree), ('v', fitted.VDegree)):
        knots = list(getattr(fitted, 'get' + axis.upper() + 'Knots')())
        for index in range(len(knots) - 1, 1, -1):
            old = getattr(fitted, 'get' + axis.upper() + 'Multiplicity')(index)
            target = degree - 2
            if old > target:
                if not getattr(fitted, 'remove' + axis.upper() + 'Knot')(index, target, plan['fit_tolerance_mm']):
                    raise ValueError('surface_rebuild_g2_knot_reduction_failed')
                removed.append(dict(axis=axis, knot=knots[index - 1], old_multiplicity=old, new_multiplicity=target))
    for axis, degree in (('u', fitted.UDegree), ('v', fitted.VDegree)):
        if any(m > degree - 2 for m in getattr(fitted, 'get' + axis.upper() + 'Multiplicities')()[1:-1]):
            raise ValueError('surface_rebuild_g2_representation_not_established')
    boundary_error = _boundary_bound(before, fitted)
    if boundary_error > plan['kernel_tolerance_mm']:
        raise ValueError('surface_rebuild_changes_preserved_boundary')
    data = _surface_data(fitted)
    if len(data['poles']) * len(data['poles'][0]) > plan['max_poles']:
        raise ValueError('surface_rebuild_pole_resource_limit')
    report = dict(schema='cad-harness.surface-rebuild-report.v4c', profile='c-s3',
        source_sha256=plan['source_sha256'], selected_face_ids=[cell['face_id'] for row in plan['grid'] for cell in row],
        chart_domain_uv=[0., float(len(plan['grid'])), 0., float(len(plan['grid'][0]))],
        kernel='OCCT spline knot insertion/degree elevation/C2 knot reduction + bounded sewing',
        continuity='parametric_C2_by_native_knot_multiplicity_requires_independent_regular_geometric_G2_check',
        knots_reduced=removed, construction_boundary_correspondence_upper_mm=boundary_error,
        input_poles=before.NbUPoles * before.NbVPoles, fitted_poles=fitted.NbUPoles * fitted.NbVPoles,
        degree_u=fitted.UDegree, degree_v=fitted.VDegree,
        fit_tolerance_mm=plan['fit_tolerance_mm'], acceptance_status='not_judged')
    return data, indices, report


def _reconnect(original, indices, surface, tolerance):
    import FreeCAD as App
    import Part
    from OCC.Core.BRep import BRep_Builder
    from OCC.Core.BRepTools import breptools
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SHELL
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopoDS import TopoDS_Shape, topods
    from OCC.Core.BRepLib import breplib
    removed = {i for row in indices for i in row}
    face = surface.toShape()
    reference = original.Faces[indices[0][0]]
    u0, u1, v0, v1 = reference.ParameterRange
    old_normal = reference.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
    new_normal = face.normalAt(.5, .5)
    if old_normal.Length == 0 or new_normal.Length == 0:
        raise UnsupportedDomain('surface_rebuild_singular_orientation')
    if old_normal.dot(new_normal) < 0:
        face.reverse()
    if face.isNull() or not face.isValid():
        raise ValueError('surface_rebuild_invalid_fitted_face')
    faces = [f for i, f in enumerate(original.Faces) if i not in removed] + [face]
    with tempfile.TemporaryDirectory(prefix='cad-s3-sew-') as directory:
        path = str(Path(directory) / 'surface.brep')
        Part.makeCompound(faces).exportBrep(path)
        occ = TopoDS_Shape()
        if not breptools.Read(occ, path, BRep_Builder()):
            raise ValueError('surface_rebuild_brep_read')
        sewing = BRepBuilderAPI_Sewing(tolerance, True, True, True, False)
        explorer = TopExp_Explorer(occ, TopAbs_FACE)
        while explorer.More():
            sewing.Add(topods.Face(explorer.Current()))
            explorer.Next()
        sewing.Perform()
        sewn = sewing.SewedShape()
        if sewn.IsNull() or sewing.NbFreeEdges() or sewing.NbMultipleEdges():
            raise ValueError('surface_rebuild_boundary_not_closed')
        maker = BRepBuilderAPI_MakeSolid()
        explorer = TopExp_Explorer(sewn, TopAbs_SHELL)
        shells = 0
        while explorer.More():
            maker.Add(topods.Shell(explorer.Current()))
            shells += 1
            explorer.Next()
        if not shells or not maker.IsDone():
            raise ValueError('surface_rebuild_solid_sewing_failed')
        solid = maker.Solid()
        if not breplib.OrientClosedSolid(solid):
            raise ValueError('surface_rebuild_solid_orientation')
        if not breptools.Write(solid, path):
            raise ValueError('surface_rebuild_brep_write')
        output = Part.Shape()
        output.importBrep(path)
    _solid(output)
    if len(output.Faces) > len(original.Faces) - len(removed) + 1:
        raise ValueError('surface_rebuild_unexpected_face_split')
    return output


class SurfaceRebuildProxy:
    """Only a version token is pickled. All construction inputs are frozen data."""
    TOKEN = 'cad-harness.surface-rebuild-proxy.v4c:1'

    def dumps(self):
        return self.TOKEN

    def loads(self, value):
        if value != self.TOKEN:
            raise ValueError('surface_rebuild_proxy_version')

    def __getstate__(self):
        return self.TOKEN

    def __setstate__(self, value):
        self.loads(value)

    def onDocumentRestored(self, obj):
        obj.touch()

    def execute(self, obj):
        import Part
        obj.Shape = Part.Shape()
        obj.OperationReport = ''
        obj.BuildStatus = 'computing'
        try:
            for field in ('OriginalBrep', 'FactsData', 'PlanData', 'SurfaceData', 'FitReport'):
                if _sha(getattr(obj, field)) != getattr(obj, field + 'Digest'):
                    raise ValueError('surface_rebuild_frozen_data_digest')
            plan = validate_plan(json.loads(obj.PlanData))
            original = _solid(_from_brep(obj.OriginalBrep))
            facts = json.loads(obj.FactsData)
            indices = [[_native_selection(original, facts, cell) for cell in row] for row in plan['grid']]
            data = json.loads(obj.SurfaceData)
            count = len(data['poles']) * len(data['poles'][0])
            offsets = list(obj.PoleOffsets)
            if len(offsets) != count:
                raise ValueError('surface_rebuild_pole_offset_count')
            for index, delta in enumerate(offsets):
                i, j = divmod(index, len(data['poles'][0]))
                if any(not math.isfinite(x) for x in delta):
                    raise ValueError('surface_rebuild_nonfinite_offset')
                if (i in (0, len(data['poles']) - 1) or j in (0, len(data['poles'][0]) - 1)) and delta.Length != 0:
                    raise ValueError('surface_rebuild_boundary_pole_locked')
                data['poles'][i][j] = [x + y for x, y in zip(data['poles'][i][j], delta)]
            surface = _surface(data, plan['max_poles'])
            for axis, degree in (('u', surface.UDegree), ('v', surface.VDegree)):
                if degree > plan['max_degree'] or any(m > degree - 2 for m in getattr(surface, 'get' + axis.upper() + 'Multiplicities')()[1:-1]):
                    raise ValueError('surface_rebuild_restored_continuity_invalid')
            obj.Shape = _reconnect(original, indices, surface, plan['kernel_tolerance_mm'])
            report = json.loads(obj.FitReport)
            report.update(original_faces=len(original.Faces), output_faces=len(obj.Shape.Faces),
                          original_volume_mm3=original.Volume, output_volume_mm3=obj.Shape.Volume,
                          edited_poles=sum(delta.Length != 0 for delta in offsets), valid=obj.Shape.isValid(), solids=len(obj.Shape.Solids))
            obj.OperationReport = _json(report)
            obj.BuildStatus = 'ok'
        except Exception as exc:
            obj.Shape = Part.Shape()
            obj.OperationReport = ''
            obj.BuildStatus = 'failed:' + str(exc)
            raise


def _property(obj, kind, name, value, frozen=False):
    obj.addProperty(kind, name, 'S3')
    setattr(obj, name, value)
    if frozen:
        obj.setEditorMode(name, 1)


def _load_source(manifest_path, asset_id):
    import Part
    inputs = _module('cad_verify_v4_inputs')
    asset = inputs.resolve_asset(manifest_path, asset_id, 'step')
    shape = Part.Shape()
    shape.read(str(asset['path']))
    if inputs.resolve_asset(manifest_path, asset_id, 'step')['digest'] != asset['digest']:
        raise ValueError('surface_rebuild_source_changed_during_build')
    return shape


def build_plan(doc, plan, manifest_path, prepared):
    import FreeCAD as App
    plan = validate_plan(plan, manifest_path, prepared)
    original = _solid(_load_source(manifest_path, plan['asset_id']))
    facts = prepared['assets'][plan['asset_id']]
    data, indices, report = _fit(original, facts, plan)
    body = doc.addObject('PartDesign::Body', 'Model')
    feature = body.newObject('PartDesign::FeaturePython', 'SurfaceRebuild')
    try:
        for name, value in (('PlanData', _json(plan)), ('FactsData', _json(facts)),
                ('OriginalBrep', original.exportBrepToString()), ('SurfaceData', _json(data)), ('FitReport', _json(report))):
            _property(feature, 'App::PropertyString', name, value, True)
            _property(feature, 'App::PropertyString', name + 'Digest', _sha(value), True)
        _property(feature, 'App::PropertyVectorList', 'PoleOffsets', [App.Vector() for row in data['poles'] for _ in row])
        _property(feature, 'App::PropertyString', 'BuildStatus', 'new', True)
        _property(feature, 'App::PropertyString', 'OperationReport', '', True)
        feature.Proxy = SurfaceRebuildProxy()
        body.Tip = feature
        doc.recompute()
        if feature.BuildStatus != 'ok':
            raise ValueError(feature.BuildStatus)
        _module('cad_verify_v4_compile').check_document(doc, body)
        check_model_inputs(body, plan, prepared, manifest_path)
        return body
    except Exception:
        doc.removeObject(feature.Name)
        doc.removeObject(body.Name)
        raise


def check_model_inputs(body, plan, prepared, manifest_path):
    plan = validate_plan(plan, manifest_path, prepared)
    feature = body.Tip
    if feature is None or type(feature.Proxy) is not SurfaceRebuildProxy or len(body.Group) != 1:
        raise ValueError('surface_rebuild_body_or_proxy')
    if feature.PlanData != _json(plan) or feature.FactsData != _json(prepared['assets'][plan['asset_id']]):
        raise ValueError('surface_rebuild_restored_plan_or_facts')
    if any(delta.Length != 0 for delta in feature.PoleOffsets):
        raise ValueError('surface_rebuild_restored_pole_offsets')
    original = _load_source(manifest_path, plan['asset_id'])
    if feature.OriginalBrep != original.exportBrepToString():
        raise ValueError('surface_rebuild_embedded_source_mismatch')
    for field in ('OriginalBrep', 'FactsData', 'PlanData', 'SurfaceData', 'FitReport'):
        if _sha(getattr(feature, field)) != getattr(feature, field + 'Digest'):
            raise ValueError('surface_rebuild_embedded_digest')
    for row in plan['grid']:
        for cell in row:
            _native_selection(original, prepared['assets'][plan['asset_id']], cell)
    if feature.BuildStatus != 'ok':
        raise ValueError('surface_rebuild_not_recomputed')
    _solid(feature.Shape)
    return True


def operation_report(body):
    feature = body.Tip
    if feature is None or type(feature.Proxy) is not SurfaceRebuildProxy or feature.BuildStatus != 'ok':
        raise ValueError('surface_rebuild_report_unavailable')
    return json.loads(feature.OperationReport)


def operative_evidence(doc, body):
    """A real interior pole moves, changes the solid, then restores exactly."""
    import FreeCAD as App
    feature = body.Tip
    if type(feature.Proxy) is not SurfaceRebuildProxy:
        raise ValueError('surface_rebuild_proxy_required')
    data = json.loads(feature.SurfaceData)
    nu, nv = len(data['poles']), len(data['poles'][0])
    if min(nu, nv) < 3:
        raise ValueError('surface_rebuild_no_interior_pole')
    index = (nu // 2) * nv + nv // 2
    offsets = [App.Vector(v) for v in feature.PoleOffsets]
    changed = [App.Vector(v) for v in offsets]
    before = _solid(feature.Shape).copy()
    surface = _surface(data, nu * nv)
    normal = surface.normal((data['u_knots'][0] + data['u_knots'][-1]) / 2,
                            (data['v_knots'][0] + data['v_knots'][-1]) / 2)
    if normal.Length == 0:
        raise ValueError('surface_rebuild_singular_edit_control')
    plan = json.loads(feature.PlanData)
    step = max(plan['kernel_tolerance_mm'] * 100, before.BoundBox.DiagonalLength * 1e-4)
    changed[index] = changed[index] + normal * (step / normal.Length)
    feature.PoleOffsets = changed
    try:
        doc.recompute()
        if feature.BuildStatus != 'ok':
            raise ValueError('surface_rebuild_operative_edit_failed')
        after = _solid(feature.Shape)
        difference = before.cut(after).Volume + after.cut(before).Volume
        if difference <= plan['kernel_tolerance_mm']**3:
            raise ValueError('surface_rebuild_pole_inert')
        evidence = dict(feature=feature.Name, parameter='PoleOffsets', index=index, step_mm=step,
                        operative=True, symmetric_difference_mm3=difference, restored=False,
                        artifact_probe=dict(kind='vector_list',object=feature.Name,property='PoleOffsets',
                                            index=index,delta_mm=list(changed[index]-offsets[index])))
    finally:
        feature.PoleOffsets = offsets
        feature.touch()
        doc.recompute()
        if feature.BuildStatus != 'ok':
            raise ValueError('surface_rebuild_operative_restore_failed')
        restored = _solid(feature.Shape)
        error = before.cut(restored).Volume + restored.cut(before).Volume
        if error > max(plan['kernel_tolerance_mm']**3, before.Volume * 1e-10):
            raise ValueError('surface_rebuild_operative_restore_mismatch')
    evidence.update(restored=True, restore_symmetric_difference_mm3=error)
    return [evidence]
