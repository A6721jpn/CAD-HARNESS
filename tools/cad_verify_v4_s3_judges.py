"""Independent C6 polynomial surface certificates; host admission imports no CAD.

Supported numerical domain: finite, rectangularly trimmed, nonperiodic,
nonrational B-spline/Bezier faces, affine signed/permuted UV charts. Actual
stored native poles/knots are converted by outward-rounded Boehm insertion;
Bernstein and interval operations retain conservative coordinate enclosures.
The explicit native_full card method measures the entire actual UV domain.
Clamped polynomial endpoint continuation is composed by Bernstein blossoms;
no thin strip is clipped. Jets are differentiated before composition.
Every actual native interior knot is judged at its exact native coordinate,
in addition to preregistered grid/face seams; rounded virtual seams cannot hide
one-sided jumps. Trim roundoff is charged via full physical derivative bounds.
Selected rational/periodic surfaces, nonrectangular trims, ambiguous ROI maps,
singular jets and exhausted resources are UNVERIFIED, never sampled certificates.
Every unselected face is separately registered: full rectangular polynomial
supports, or certified planar/polynomial-extrusion supports with complete
polynomial trim-wire homotopies. Unsupported outside geometry also prevents PASS.
No fitter imports/oracles. Exact same-face Ck uses actual knots AND full regularity;
separate-face G2 always uses invariant physical second forms, not raw jet equality.
"""
import copy
import math
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/schemas'


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '') + name)


class Unknown(ValueError):
    """A required continuous proof is unavailable."""


class Changed(Unknown):
    """A certified actual closest-point lower witness defeats preservation."""
    def __init__(self,reason,lower):
        super().__init__(reason)
        self.lower = lower


def _ordered(a):
    return all(a[k] < a[k+1] for k in range(0, len(a), 2))


def validate_card(card):
    plans = _module('cad_verify_v4_plans')
    schema = _module('cad_verify_v4_ledger').read_json(SCHEMAS / 's3-judge-card.schema.json')
    plans._check(card, schema, schema, 's3-judge-card')
    ids = [c['id'] for c in card['criteria']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate_criterion_id')
    for c in card['criteria']:
        if 'output_patches' not in c:
            continue
        if not _ordered(c['output_region_mm']):
            raise ValueError('output_region_requires_positive_extents')
        if c.get('maximum_normal_sin', 0) > 1:
            raise ValueError('normal_sin_limit_exceeds_one')
        if any(p in c['output_patches'][:i] for i,p in enumerate(c['output_patches'])):
            raise ValueError('duplicate_output_patch')
        seams = c.get('seams', [])
        if any(s in seams[:i] for i,s in enumerate(seams)):
            raise ValueError('duplicate_seam')
        for p in c['output_patches']:
            if (p['domain_uv']!='native_full' and not _ordered(p['domain_uv'])) or not _ordered(p['chart_uv']):
                raise ValueError('patch_domain_or_chart_reversed')
            if any(p['bounds_mm'][k] > p['bounds_mm'][k+1] for k in (0, 2, 4)):
                raise ValueError('patch_bounds_reversed')
        for seam in c.get('seams', []):
            for side in seam.values():
                if side['patch'] >= len(c['output_patches']) or not _ordered(side['range']):
                    raise ValueError('seam_patch_or_range_invalid')
                p = c['output_patches'][side['patch']]['chart_uv']
                axis = 0 if side['axis'] == 'u' else 2
                other = 2-axis
                if not p[axis] <= side['value'] <= p[axis+1] or not (p[other] <= side['range'][0] < side['range'][1] <= p[other+1]):
                    raise ValueError('seam_outside_full_chart')
                if side['range'] != p[other:other+2]:
                    raise ValueError('seam_requires_complete_transverse_domain')
    return copy.deepcopy(card)


def _xyz(p):
    return [float(p.x), float(p.y), float(p.z)]


def _bounds(shape):
    b = shape.BoundBox
    return [float(b.XMin), float(b.XMax), float(b.YMin), float(b.YMax), float(b.ZMin), float(b.ZMax)]


def _source(plan, manifest_path, prepared):
    """Reopen and independently reconstruct every immutable native face identity."""
    import Part
    inputs = _module('cad_verify_v4_inputs')
    ledger = _module('cad_verify_v4_ledger')
    plans = _module('cad_verify_v4_plans')
    manifest = inputs.load_manifest(manifest_path)
    if manifest.get('profile') != 'c-s3' or prepared.get('profile') != 'c-s3':
        raise Unknown('source_profile_mismatch')
    plans.validate_document(prepared, 'prepared', profile='c-s3')
    path = inputs.guarded_path(manifest_path)
    digest = ledger.file_sha(path)
    if prepared.get('source_manifest_sha256') != digest:
        raise Unknown('prepared_manifest_hash_mismatch')
    asset = inputs.resolve_asset(path, plan['asset_id'], 'step')
    facts = prepared['assets'][plan['asset_id']]
    inputs._validate_facts(facts)
    if asset['record'].get('role') != 'reference' or asset['digest'] != plan['source_sha256'] or facts['source_sha256'] != asset['digest']:
        raise Unknown('source_hash_or_role_mismatch')
    if facts['units'] != 'mm' or facts['frame']['axis_transform'] != 'identity':
        raise Unknown('source_frame_not_fixed_mm_identity')
    for key in ('manifest_sha256_before', 'manifest_sha256_after'):
        if facts['provenance'].get(key) != digest:
            raise Unknown('source_manifest_provenance_mismatch')
    for key in ('asset_sha256_before', 'asset_sha256_after'):
        if facts['provenance'].get(key) != asset['digest']:
            raise Unknown('source_asset_provenance_mismatch')
    shape = Part.Shape()
    shape.read(str(asset['path']))
    if shape.isNull() or not shape.isValid() or len(shape.Faces) != len(facts['faces']):
        raise Unknown('original_step_invalid_or_face_count_mismatch')
    precision = facts['signature_precision_mm']
    for i, (face, row) in enumerate(zip(shape.Faces, facts['faces'])):
        u0, u1, v0, v1 = face.ParameterRange
        try:
            n = face.normalAt((u0+u1)/2, (v0+v1)/2)
            normal = [x/n.Length for x in _xyz(n)]
        except (ValueError, RuntimeError, ZeroDivisionError):
            normal = None
        signature = dict(surface_type=type(face.Surface).__name__,
                         area_quantized=round(face.Area/(precision*precision)),
                         center_quantized=[round(x/precision) for x in _xyz(face.CenterOfMass)],
                         bounds_quantized=[round(x/precision) for x in _bounds(face)],
                         normal_quantized=None if normal is None else [0.0 if round(x,12)==0 else round(x,12) for x in normal])
        actual_signature = inputs.canonical_sha(signature)
        if row['id'] != 'Face'+str(i+1) or row['signature'] != actual_signature:
            raise Unknown('source_face_signature_mismatch')
        numeric = [abs(row['area_mm2']-face.Area), math.dist(row['center_mm'], _xyz(face.CenterOfMass))]
        numeric.extend(abs(x-y) for x,y in zip(row['bounds_mm'], _bounds(face)))
        if max(numeric) > 1e-8*max(1.,face.Area):
            raise Unknown('source_face_geometry_mismatch')
        adjacent = ['Face'+str(j+1) for j,other in enumerate(shape.Faces) if i != j and any(e.isSame(f) for e in face.Edges for f in other.Edges)]
        if row['adjacent_face_ids'] != adjacent:
            raise Unknown('source_face_adjacency_mismatch')
        parameterization = row['parameterization']
        corners = [_xyz(face.Surface.value(u,v)) for u,v in ((u0,v0),(u1,v0),(u0,v1),(u1,v1))]
        if max(abs(x-y) for x,y in zip(parameterization['domain_uv'], (u0,u1,v0,v1))) > 1e-10 or max(math.dist(x,y) for x,y in zip(parameterization['corner_points_mm'],corners)) > 1e-8:
            raise Unknown('source_parameterization_mismatch')
        spline = isinstance(face.Surface,(Part.BSplineSurface,Part.BezierSurface))
        actual_degrees = (face.Surface.UDegree,face.Surface.VDegree) if spline else (None,None)
        if (parameterization['degree_u'],parameterization['degree_v']) != actual_degrees:
            raise Unknown('source_polynomial_degree_mismatch')
    rows = {r['id']:r for r in facts['faces']}
    selected_ids = [cell['face_id'] for row in plan['grid'] for cell in row]
    if len(selected_ids) != len(set(selected_ids)):
        raise Unknown('duplicate_immutable_source_face_registration')
    for row in plan['grid']:
        for cell in row:
            fact = rows[cell['face_id']]
            if fact['ambiguous'] or cell['signature'] != fact['signature'] or cell['adjacent_face_ids'] != fact['adjacent_face_ids']:
                raise Unknown('grid_source_selector_mismatch')
    if inputs.resolve_asset(path,plan['asset_id'],'step')['digest'] != asset['digest'] or ledger.file_sha(path) != digest:
        raise Unknown('source_changed_during_judgement')
    return shape, dict(asset_id=plan['asset_id'], source_sha256=asset['digest'], manifest_sha256=digest, frame='identity_source_axes',source_units='mm')


# Outward-rounded binary64 intervals. Zero-width inputs represent stored doubles,
# not imaginary exact decimal data. Native coordinate uncertainty is added once.
def _down(x):
    return math.nextafter(x, -math.inf)


def _up(x):
    return math.nextafter(x, math.inf)


class I:
    __slots__ = ('lo','hi')
    def __init__(self, lo, hi=None):
        self.lo = float(lo)
        self.hi = float(lo if hi is None else hi)
        if not math.isfinite(self.lo) or not math.isfinite(self.hi) or self.lo > self.hi:
            raise Unknown('nonfinite_interval')
    def __add__(self, other):
        other = _i(other)
        return I(_down(self.lo+other.lo), _up(self.hi+other.hi))
    __radd__ = __add__
    def __neg__(self):
        return I(-self.hi, -self.lo)
    def __sub__(self, other):
        return self + -_i(other)
    def __rsub__(self, other):
        return _i(other) + -self
    def __mul__(self, other):
        other = _i(other)
        products = [a*b for a in (self.lo,self.hi) for b in (other.lo,other.hi)]
        return I(_down(min(products)), _up(max(products)))
    __rmul__ = __mul__
    def __truediv__(self, other):
        other = _i(other)
        if other.lo <= 0 <= other.hi:
            raise Unknown('singular_or_unresolved_denominator')
        return self * I(_down(1/other.hi), _up(1/other.lo))


def _i(x):
    return x if isinstance(x,I) else I(x)


def _square(x):
    x = _i(x)
    low = 0. if x.lo <= 0 <= x.hi else min(x.lo*x.lo,x.hi*x.hi)
    return I(max(0.,_down(low)), _up(max(x.lo*x.lo,x.hi*x.hi)))


def _sqrt(x):
    if x.lo < 0:
        raise Unknown('negative_interval_radicand')
    return I(max(0.,_down(math.sqrt(x.lo))), _up(math.sqrt(x.hi)))


def _dot(a,b):
    return sum((x*y for x,y in zip(a,b)), I(0))


def _cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def _norm(a):
    squared = sum((_square(x) for x in a), I(0))
    return _sqrt(I(max(0.,squared.lo),squared.hi))


def _mix(a,b,t):
    return [x*(1-t)+y*t for x,y in zip(a,b)]


def _curve_split(p,t=.5):
    layers = [p]
    while len(layers[-1]) > 1:
        layers.append([_mix(a,b,t) for a,b in zip(layers[-1],layers[-1][1:])])
    return [x[0] for x in layers], [x[-1] for x in reversed(layers)]


def _curve_at(p,t):
    return _curve_split(p,t)[0][-1]


def _curve_restrict(p,a,b):
    if not 0 <= a < b <= 1:
        raise Unknown('invalid_bernstein_restriction')
    if b < 1:
        p = _curve_split(p,b)[0]
    if a > 0:
        p = _curve_split(p,a/b)[1]
    return p


def _transpose(net):
    return [list(row) for row in zip(*net)]


def _split_net(net,axis):
    if axis == 0:
        a,b = _split_net(_transpose(net),1)
        return _transpose(a),_transpose(b)
    split = [_curve_split(row) for row in net]
    return [a for a,b in split],[b for a,b in split]


def _restrict_net(net,box):
    a,b,c,d = box
    net = [_curve_restrict(row,c,d) for row in net]
    return _transpose([_curve_restrict(row,a,b) for row in _transpose(net)])


def _elevate_curve(p):
    n = len(p)-1
    return [p[0]]+[_mix(p[k],p[k-1],I(k)/I(n+1)) for k in range(1,n+1)]+[p[-1]]


def _same_degree(a,b):
    for axis in (0,1):
        if axis == 0:
            a,b = _transpose(a),_transpose(b)
        while len(a[0]) < len(b[0]):
            a = [_elevate_curve(row) for row in a]
        while len(b[0]) < len(a[0]):
            b = [_elevate_curve(row) for row in b]
        if axis == 0:
            a,b = _transpose(a),_transpose(b)
    return a,b


def _hull(curve):
    return [I(min(p[k].lo for p in curve),max(p[k].hi for p in curve)) for k in range(3)]


def _rect_trim(face,eps):
    """Prove the single trimming wire traces the entire UV rectangle.

    Lines or nonrational collinear monotone B-spline pcurves only. This excludes
    holes, oblique trims, hidden curve bows and partial rectangular coverage.
    """
    if len(face.Wires) != 1:
        raise Unknown('unsupported_nonrectangular_trim_or_hole')
    domain = list(map(float,face.ParameterRange))
    sides = {k:[] for k in range(4)}
    # Parameter-space tolerance is dimensionless native roundoff, never mm.
    eps = 256*math.ulp(max(1.,*(abs(x) for x in domain)))
    for edge in face.Edges:
        result = face.curveOnSurface(edge)
        if result is None:
            raise Unknown('unsupported_trim_missing_pcurve')
        curve,first,last = result
        name = type(curve).__name__
        p,q = curve.value(first),curve.value(last)
        ends = [[float(p.x),float(p.y)],[float(q.x),float(q.y)]]
        if name == 'Line2d':
            poles = ends
        elif name == 'BSplineCurve2d' and not curve.isRational() and not curve.isPeriodic():
            poles = [[float(v.x),float(v.y)] for v in curve.getPoles()]
        else:
            raise Unknown('unsupported_trim_pcurve')
        matches = []
        for side in range(4):
            axis = 0 if side < 2 else 1
            value = domain[side]
            if all(abs(p[axis]-value) <= eps for p in poles):
                vals = [p[1-axis] for p in poles]
                if all(y >= x-eps for x,y in zip(vals,vals[1:])) or all(y <= x+eps for x,y in zip(vals,vals[1:])):
                    matches.append(side)
        if len(matches) != 1:
            raise Unknown('unsupported_nonrectangular_trim')
        side = matches[0]
        axis = 1 if side < 2 else 0
        sides[side].append(sorted([ends[0][axis],ends[1][axis]]))
    for side,segments in sides.items():
        axis = 2 if side < 2 else 0
        cursor = domain[axis]
        for a,b in sorted(segments):
            if abs(a-cursor) > eps or b <= a:
                raise Unknown('trim_boundary_gap_or_overlap')
            cursor = b
        if abs(cursor-domain[axis+1]) > eps:
            raise Unknown('incomplete_trim_coverage')
    return domain


def _chart_uv(mapping,u,v):
    domain,chart = mapping['domain_uv'],mapping['chart_uv']
    x,y = (u-domain[0])/(domain[1]-domain[0]),(v-domain[2])/(domain[3]-domain[2])
    if mapping['swap_uv']:
        x,y = y,x
    if mapping['reverse_u']:
        x = 1-x
    if mapping['reverse_v']:
        y = 1-y
    a = chart[0] if x==0 else chart[1] if x==1 else chart[0]+x*(chart[1]-chart[0])
    b = chart[2] if y==0 else chart[3] if y==1 else chart[2]+y*(chart[3]-chart[2])
    return a,b


def _native_uv(mapping,x,y):
    domain,chart = mapping['domain_uv'],mapping['chart_uv']
    x,y = (x-chart[0])/(chart[1]-chart[0]),(y-chart[2])/(chart[3]-chart[2])
    if mapping['reverse_u']:
        x = 1-x
    if mapping['reverse_v']:
        y = 1-y
    if mapping['swap_uv']:
        x,y = y,x
    a = domain[0] if x==0 else domain[1] if x==1 else domain[0]+x*(domain[1]-domain[0])
    b = domain[2] if y==0 else domain[3] if y==1 else domain[2]+y*(domain[3]-domain[2])
    return a,b


def _bezier_curve_core(poles,knots,degree,low,high):
    """Boehm insertion with outward interval coefficients, not native fitting."""
    from bisect import bisect_right
    poles,knots = list(poles),list(knots)
    if not knots[degree] <= low < high <= knots[-degree-1]:
        raise Unknown('trim_outside_finite_spline_support')
    for value in (low,high):
        while knots.count(value) < degree:
            n = len(poles)-1
            k = min(n,bisect_right(knots,value)-1)
            multiplicity = knots.count(value)
            result = [None]*(n+2)
            for i in range(k-degree+1):
                result[i] = poles[i]
            for i in range(k-multiplicity+1,n+2):
                result[i] = poles[i-1]
            for i in range(k-degree+1,k-multiplicity+1):
                alpha = (I(value)-I(knots[i]))/(I(knots[i+degree])-I(knots[i]))
                alpha = I(max(0.,alpha.lo),min(1.,alpha.hi))
                result[i] = _mix(poles[i-1],poles[i],alpha)
            if any(p is None for p in result):
                raise Unknown('incomplete_interval_knot_insertion')
            poles = result
            knots.insert(k+1,value)
    k = bisect_right(knots,low)-1
    if knots[k+1] != high:
        raise Unknown('requested_span_contains_unregistered_knots')
    result = poles[k-degree:k+1]
    if len(result) != degree+1:
        raise Unknown('bezier_extraction_degree_mismatch')
    return result


def _curve_affine(poles,low,high):
    """Bernstein blossom composition, INCLUDING extrapolation outside [0,1]."""
    degree = len(poles)-1
    result = []
    for k in range(degree+1):
        work = poles
        for t in [low]*(degree-k)+[high]*k:
            work = [_mix(a,b,t) for a,b in zip(work,work[1:])]
        result.append(work[0])
    return result


def _affine_net(net,box):
    u0,u1,v0,v1 = box
    return _transpose([_curve_affine(row,u0,u1) for row in _transpose([_curve_affine(row,v0,v1) for row in net])])


def _core_span(knots,degree,low,high):
    start,end = knots[degree],knots[-degree-1]
    values = sorted(set([start,end]+[k for k in knots if start<k<end]))
    if low < start or high > end:
        if knots.count(start)!=degree+1 or knots.count(end)!=degree+1:
            raise Unknown('unsupported_unclamped_spline_extrapolation')
    if len(values)==2:
        return values
    if low<start and high<=values[1]:
        return values[:2]
    if high>end and low>=values[-2]:
        return values[-2:]
    if high<=start:
        return values[:2]
    if low>=end:
        return values[-2:]
    for a,b in zip(values,values[1:]):
        if a<=low<high<=b:
            return [a,b]
    raise Unknown('requested_polynomial_piece_crosses_actual_knot')


def _fraction(value,low,high):
    return (I(value)-I(low))/(I(high)-I(low))


def _bezier_curve(poles,knots,degree,low,high):
    base = _core_span(knots,degree,low,high)
    net = _bezier_curve_core(poles,knots,degree,*base)
    return _curve_affine(net,_fraction(low,*base),_fraction(high,*base))


def _patch(face,mapping,eps):
    import Part
    surface = face.Surface
    if not isinstance(surface,(Part.BSplineSurface,Part.BezierSurface)):
        raise Unknown('unsupported_non_spline_surface')
    bezier = isinstance(surface,Part.BezierSurface)
    if surface.isURational() or surface.isVRational():
        raise Unknown('unsupported_rational_surface')
    weights = [float(w) for row in surface.getWeights() for w in row]
    if not weights or any(not math.isfinite(w) or w<=0 for w in weights):
        raise Unknown('invalid_native_surface_weights')
    if any(w!=weights[0] for w in weights):
        raise Unknown('unsupported_rational_surface')
    if surface.isUPeriodic() or surface.isVPeriodic():
        raise Unknown('unsupported_periodic_surface')
    domain = _rect_trim(face,eps)
    domain_method = 'native_full' if mapping['domain_uv']=='native_full' else 'explicit_full'
    if domain_method=='native_full':
        mapping = copy.deepcopy(mapping)
        mapping['domain_uv']=domain
    elif any(a != b for a,b in zip(domain,mapping['domain_uv'])):
        raise Unknown('map_does_not_cover_complete_trimmed_face')
    uvalues = [0.,1.] if bezier else list(surface.getUKnots())
    vvalues = [0.,1.] if bezier else list(surface.getVKnots())
    umults = [surface.UDegree+1]*2 if bezier else surface.getUMultiplicities()
    vmults = [surface.VDegree+1]*2 if bezier else surface.getVMultiplicities()
    if surface.UDegree > 12 or surface.VDegree > 12:
        raise Unknown('polynomial_degree_resource_bound')
    uknots = [float(k) for k,m in zip(uvalues,umults) for _ in range(m)]
    vknots = [float(k) for k,m in zip(vvalues,vmults) for _ in range(m)]
    ustart,uend = uknots[surface.UDegree],uknots[-surface.UDegree-1]
    vstart,vend = vknots[surface.VDegree],vknots[-surface.VDegree-1]
    # Endpoint continuation is the SAME adjacent polynomial. Coalescing it is
    # exact affine composition over an extended interval, not omitted strips.
    uk = sorted(set([domain[0],domain[1]]+[float(k) for k in uvalues if ustart < k < uend and domain[0] < k < domain[1]]))
    vk = sorted(set([domain[2],domain[3]]+[float(k) for k in vvalues if vstart < k < vend and domain[2] < k < domain[3]]))
    if surface.UDegree > 12 or surface.VDegree > 12 or (len(uk)-1)*(len(vk)-1) > 4096:
        raise Unknown('polynomial_degree_or_span_resource_bound')
    native_poles = surface.getPoles()
    if len(native_poles)*len(native_poles[0]) > 4096:
        raise Unknown('native_controlnet_resource_bound')
    poles = [[[I(_down(x-eps),_up(x+eps)) for x in _xyz(p)] for p in row] for row in native_poles]
    spans,core_cache = [],{}
    for u0,u1 in zip(uk,uk[1:]):
        base_u = _core_span(uknots,surface.UDegree,u0,u1)
        for v0,v1 in zip(vk,vk[1:]):
            base_v = _core_span(vknots,surface.VDegree,v0,v1)
            key = tuple(base_u+base_v)
            if key not in core_cache:
                strip = _transpose([_bezier_curve_core(row,uknots,surface.UDegree,*base_u) for row in _transpose(poles)])
                core = [_bezier_curve_core(row,vknots,surface.VDegree,*base_v) for row in strip]
                if mapping['swap_uv']:
                    core = _transpose(core)
                if mapping['reverse_u']:
                    core = list(reversed(core))
                if mapping['reverse_v']:
                    core = [list(reversed(row)) for row in core]
                widths = [I(base_u[1])-I(base_u[0]),I(base_v[1])-I(base_v[0])]
                domains = [I(domain[1])-I(domain[0]),I(domain[3])-I(domain[2])]
                if mapping['swap_uv']:
                    widths,domains = list(reversed(widths)),list(reversed(domains))
                widths = [widths[k]*(I(mapping['chart_uv'][2*k+1])-I(mapping['chart_uv'][2*k]))/domains[k] for k in (0,1)]
                du,dv = _differentiate(core,0,widths[0]),_differentiate(core,1,widths[1])
                core_cache[key] = [core,du,dv,_differentiate(du,0,widths[0]),_differentiate(du,1,widths[1]),_differentiate(dv,1,widths[1])]
            relative = [_fraction(u0,*base_u),_fraction(u1,*base_u),_fraction(v0,*base_v),_fraction(v1,*base_v)]
            if mapping['swap_uv']:
                relative = relative[2:]+relative[:2]
            if mapping['reverse_u']:
                relative[:2] = [1-relative[1],1-relative[0]]
            if mapping['reverse_v']:
                relative[2:] = [1-relative[3],1-relative[2]]
            # Differentiate on the REAL knot span before composition. Dividing
            # independently inflated tiny-strip poles by strip width is unsound
            # and would invent an enormous derivative uncertainty.
            jets = [_affine_net(net,relative) for net in core_cache[key]]
            rates = [max(_norm(p).hi for row in jets[k] for p in row) for k in (1,2)]
            scales = [(I(mapping['chart_uv'][2*k+1])-I(mapping['chart_uv'][2*k]))/(I(domain[(1-k if mapping['swap_uv'] else k)*2+1])-I(domain[(1-k if mapping['swap_uv'] else k)*2])) for k in (0,1)]
            native_rates = [(I(rate)*scale).hi for rate,scale in zip(rates,scales)]
            if mapping['swap_uv']:
                native_rates.reverse()
            uv_roundoff = 256*math.ulp(max(1.,*(abs(x) for x in domain)))
            trim_bound = _up(uv_roundoff*sum(native_rates))
            if trim_bound > eps/2:
                raise Unknown('trim_physical_lipschitz_bound_exceeds_coordinate_enclosure')
            corners = [_chart_uv(mapping,u,v) for u,v in ((u0,v0),(u1,v1))]
            box = [min(p[0] for p in corners),max(p[0] for p in corners),min(p[1] for p in corners),max(p[1] for p in corners)]
            if not _ordered(box):
                raise Unknown('actual_native_strip_unresolvable_in_chart')
            spans.append(dict(box=box,net=jets[0],jets=jets,native_box=[u0,u1,v0,v1],trim_physical_bound_mm=trim_bound))
    orientation = (-1 if face.Orientation == 'Reversed' else 1)*(-1 if mapping['swap_uv'] else 1)*(-1 if mapping['reverse_u'] else 1)*(-1 if mapping['reverse_v'] else 1)
    return dict(face=face,mapping=mapping,spans=spans,orientation=orientation,domain_method=domain_method)


def _tile(boxes,domain):
    """Exact affine-chart partition, independently checked without fit metadata."""
    if any(b[0] < domain[0] or b[1] > domain[1] or b[2] < domain[2] or b[3] > domain[3] or not _ordered(b) for b in boxes):
        raise Unknown('chart_tile_outside_domain')
    us = sorted(set([domain[0],domain[1]]+[v for b in boxes for v in b[:2]]))
    vs = sorted(set([domain[2],domain[3]]+[v for b in boxes for v in b[2:]]))
    if (len(us)-1)*(len(vs)-1) > 200000:
        raise Unknown('chart_coverage_resource_bound')
    for u0,u1 in zip(us,us[1:]):
        for v0,v1 in zip(vs,vs[1:]):
            count = sum(b[0] <= u0 and u1 <= b[1] and b[2] <= v0 and v1 <= b[3] for b in boxes)
            if count != 1:
                raise Unknown('incomplete_or_overlapping_full_chart_coverage')


def _output(shape,c,eps):
    region = c['output_region_mm']
    tolerance = c['selection_tolerance_mm']
    eligible = []
    for face in shape.Faces:
        bounds = _bounds(face)
        inside = all(region[k]-tolerance <= bounds[k] and bounds[k+1] <= region[k+1]+tolerance for k in (0,2,4))
        # Unmapped/crossing/inside-ROI faces are ALL checked by the global
        # complement bijection; unchanged oblique walls are not ROI omissions.
        if inside:
            eligible.append(face)
    patches,used = [],[]
    for mapping in c['output_patches']:
        matches = [i for i,f in enumerate(eligible) if max(abs(a-b) for a,b in zip(_bounds(f),mapping['bounds_mm'])) <= tolerance]
        if len(matches) != 1 or matches[0] in used:
            raise Unknown('output_selector_missing_ambiguous_or_repeated')
        used.append(matches[0])
        patches.append(_patch(eligible[matches[0]],mapping,eps))
    return patches


def _original(source,plan,eps):
    patches = []
    nu,nv = len(plan['grid']),len(plan['grid'][0])
    for i,row in enumerate(plan['grid']):
        if len(row) != nv:
            raise Unknown('nonrectangular_source_grid')
        for j,cell in enumerate(row):
            face = source.Faces[int(cell['face_id'][4:])-1]
            mapping = dict(domain_uv=list(map(float,face.ParameterRange)),chart_uv=[i,i+1,j,j+1],**{k:cell[k] for k in ('swap_uv','reverse_u','reverse_v')})
            patches.append(_patch(face,mapping,eps))
    return patches,[0,nu,0,nv]


def _seam_coverage(patches,c,domain):
    """Preregistered source joins and output FACE boundaries must be complete."""
    required = {}
    for axis in (0,1):
        other = 1-axis
        for value in range(int(domain[2*axis])+1,int(domain[2*axis+1])):
            required.setdefault((axis,float(value)),[]).append(domain[2*other:2*other+2])
        for patch in patches:
            box = patch['mapping']['chart_uv']
            for value in box[2*axis:2*axis+2]:
                if domain[2*axis] < value < domain[2*axis+1]:
                    required.setdefault((axis,value),[]).append(box[2*other:2*other+2])
    registered = {}
    for seam in c['seams']:
        a,b = seam['a'],seam['b']
        if any(a[k] != b[k] for k in ('axis','value','range','reverse')):
            raise Unknown('seam_must_follow_registered_global_chart_correspondence')
        axis = 0 if a['axis']=='u' else 1
        left = patches[a['patch']]['mapping']['chart_uv']
        right = patches[b['patch']]['mapping']['chart_uv']
        if not left[2*axis] < a['value'] <= left[2*axis+1] or not right[2*axis] <= b['value'] < right[2*axis+1]:
            raise Unknown('seam_sides_do_not_register_actual_left_and_right_faces')
        registered.setdefault((axis,a['value']),[]).append(a['range'])
    for key,ranges in required.items():
        available = sorted(registered.get(key,[]))
        for low,high in ranges:
            cursor = low
            for a,b in available:
                if b <= cursor:
                    continue
                if a > cursor:
                    break
                cursor = max(cursor,b)
            if cursor < high:
                raise Unknown('omitted_source_grid_or_output_face_boundary_seam')


def _common_cells(a,b,domain,max_cells):
    _tile([p['mapping']['chart_uv'] for p in a],domain)
    _tile([p['mapping']['chart_uv'] for p in b],domain)
    _tile([s['box'] for p in a for s in p['spans']],domain)
    _tile([s['box'] for p in b for s in p['spans']],domain)
    aa = [s for p in a for s in p['spans']]
    bb = [s for p in b for s in p['spans']]
    if len(aa)*len(bb) > max_cells:
        raise Unknown('knot_grid_pair_search_exceeds_resource_bound')
    for x in aa:
        for y in bb:
            box = [max(x['box'][0],y['box'][0]),min(x['box'][1],y['box'][1]),max(x['box'][2],y['box'][2]),min(x['box'][3],y['box'][3])]
            if not _ordered(box):
                continue
            nets = []
            for s in (x,y):
                r = s['box']
                nets.append(_restrict_net(s['net'],[(box[0]-r[0])/(r[1]-r[0]),(box[1]-r[0])/(r[1]-r[0]),(box[2]-r[2])/(r[3]-r[2]),(box[3]-r[2])/(r[3]-r[2])]))
            yield box,*_same_degree(*nets)


def _native_distance(point,shape):
    import Part
    value = float(Part.Vertex(point).distToShape(shape)[0])
    if not math.isfinite(value) or value<0:
        raise Unknown('native_closestpoint_unavailable_or_nonfinite')
    return value


def _point(patch,u,v):
    a,b = _native_uv(patch['mapping'],u,v)
    return patch['face'].Surface.value(a,b)


def _closest_lower(a,b,box,eps):
    import Part
    # BOTH directed distances use actual closest-point kernels on full trimmed
    # compounds. Correspondence distance is never a Hausdorff lower witness.
    aa = Part.makeCompound([p['face'] for p in a])
    bb = Part.makeCompound([p['face'] for p in b])
    lower = 0.
    for patches,other in ((a,bb),(b,aa)):
        for u,v in ((box[0],box[2]),(box[1],box[3]),((box[0]+box[1])/2,(box[2]+box[3])/2)):
            matches = [p for p in patches if p['mapping']['chart_uv'][0] <= u <= p['mapping']['chart_uv'][1] and p['mapping']['chart_uv'][2] <= v <= p['mapping']['chart_uv'][3]]
            for patch in matches:
                distance = _native_distance(_point(patch,u,v),other)
                lower = max(lower,max(0.,distance-2*eps))
    return lower


def certify_deviation(a,b,domain,target,resources,eps):
    """Continuous bidirectional Hausdorff [L,U], given complete chart coverage."""
    stack = [(box,x,y,0) for box,x,y in _common_cells(a,b,domain,resources['max_cells'])]
    if len(stack) > resources['max_cells']:
        raise Unknown('initial_knot_grid_exceeds_resource_bound')
    lower,upper,visited,unresolved = 0.,0.,0,False
    while stack:
        box,x,y,depth = stack.pop()
        visited += 1
        bound = max(_norm([q-r for q,r in zip(px,py)]).hi for rx,ry in zip(x,y) for px,py in zip(rx,ry))
        lower = max(lower,_closest_lower(a,b,box,eps))
        if lower > target:
            # Other pending cells must still contribute to the reported upper.
            pending = [max(_norm([q-r for q,r in zip(px,py)]).hi for rx,ry in zip(nx,ny) for px,py in zip(rx,ry)) for _,nx,ny,_ in stack]
            return 'FAIL',dict(lower_mm=lower,upper_mm=max(lower,bound,upper,*pending)),dict(cells=visited,coverage='full_bidirectional_trimmed_regions',method='bernstein_correspondence_upper_native_closestpoint_lower')
        if bound <= target:
            upper = max(upper,bound)
            continue
        if depth >= resources['max_depth'] or visited+len(stack)+2 > resources['max_cells']:
            upper = max(upper,bound)
            unresolved = True
            continue
        axis = depth%2
        xs,ys = _split_net(x,axis),_split_net(y,axis)
        mid = (box[axis*2]+box[axis*2+1])/2
        for k in (0,1):
            child = list(box)
            child[axis*2+(1-k)] = mid
            stack.append((child,xs[k],ys[k],depth+1))
    upper = max(lower,upper)
    status = 'PASS' if upper <= target else 'UNVERIFIED'
    return status,dict(lower_mm=lower,upper_mm=upper),dict(cells=visited,resource_exhausted=unresolved,coverage='full_bidirectional_trimmed_regions',method='bernstein_correspondence_upper_native_closestpoint_lower')


def _differentiate(net,axis,width):
    if axis == 0:
        return _transpose(_differentiate(_transpose(net),1,width))
    degree = len(net[0])-1
    if degree == 0:
        return [[[I(0) for _ in range(3)]] for row in net]
    return [[[degree*(b-a)/width for a,b in zip(p,q)] for p,q in zip(row,row[1:])] for row in net]


def _jet_nets(span):
    if 'jets' in span:
        return span['jets']
    n,box = span['net'],span['box']
    u = _differentiate(n,0,box[1]-box[0])
    v = _differentiate(n,1,box[3]-box[2])
    return [n,u,v,_differentiate(u,0,box[1]-box[0]),_differentiate(u,1,box[3]-box[2]),_differentiate(v,1,box[3]-box[2])]


def _seam_segments(patch,side,one_side):
    axis = 0 if side['axis']=='u' else 1
    along = 1-axis
    override = side.get('_native_fixed')
    mapping = patch['mapping']
    native_axis = 1-axis if mapping['swap_uv'] else axis
    if override is not None and override['axis']!=native_axis:
        raise Unknown('invalid_automatic_native_seam_axis')
    coordinate_axis = native_axis if override is not None else axis
    key = 'native_box' if override is not None else 'box'
    value = override['value'] if override is not None else side['value']
    reversed_axis = mapping['reverse_u' if axis==0 else 'reverse_v']
    physical_side = -one_side if override is not None and reversed_axis else one_side
    segments = []
    for span in patch['spans']:
        box = span['box']
        low,high = span[key][2*coordinate_axis:2*coordinate_axis+2]
        if not low <= value <= high:
            continue
        # Automatic seams use the EXACT actual native knot coordinate. A
        # rounded global chart value must never sample away from a real jump.
        if value == low and physical_side < 0 and any(s[key][2*coordinate_axis+1] == value for s in patch['spans']):
            continue
        if value == high and physical_side > 0 and any(s[key][2*coordinate_axis] == value for s in patch['spans']):
            continue
        lo,hi = max(box[2*along],side['range'][0]),min(box[2*along+1],side['range'][1])
        if lo >= hi:
            continue
        t = (value-low)/(high-low)
        if override is not None and reversed_axis:
            t = 1-t
        curves = []
        for net in _jet_nets(span):
            curve = [_curve_at(row,t) for row in _transpose(net)] if axis==0 else [_curve_at(row,t) for row in net]
            curve = _curve_restrict(curve,(lo-box[2*along])/(box[2*along+1]-box[2*along]),(hi-box[2*along])/(box[2*along+1]-box[2*along]))
            if side['reverse']:
                curve = list(reversed(curve))
            curves.append(curve)
        a,b = (lo-side['range'][0])/(side['range'][1]-side['range'][0]),(hi-side['range'][0])/(side['range'][1]-side['range'][0])
        segments.append((([1-b,1-a] if side['reverse'] else [a,b]),curves))
    cursor = 0.
    for bounds,_ in sorted(segments,key=lambda s:s[0][0]):
        if abs(bounds[0]-cursor) > 1e-12:
            raise Unknown('seam_knot_coverage_gap_or_overlap')
        cursor = bounds[1]
    if abs(cursor-1) > 1e-12:
        raise Unknown('incomplete_seam_coverage')
    return segments


def _matmul(a,b):
    return [[sum((a[i][k]*b[k][h] for k in range(len(b))),I(0)) for h in range(len(b[0]))] for i in range(len(a))]


def _matadd(a,b):
    return [[x+y for x,y in zip(ra,rb)] for ra,rb in zip(a,b)]


def _chain(*matrices):
    result = matrices[0]
    for matrix in matrices[1:]:
        result = _matmul(result,matrix)
    return result


def _geometry_parts(jets,orientation):
    p,u,v,uu,uv,vv = jets
    cross = [orientation*x for x in _cross(u,v)]
    length = _norm(cross)
    if length.lo <= 0:
        raise Unknown('singular_or_unresolved_surface_jacobian')
    normal = [x/length for x in cross]
    e,f,g = _dot(u,u),_dot(u,v),_dot(v,v)
    det = e*g-f*f
    if det.lo <= 0:
        raise Unknown('singular_or_unresolved_metric_tensor')
    inverse = [[g/det,-f/det],[-f/det,e/det]]
    second = [[_dot(normal,uu),_dot(normal,uv)],[_dot(normal,uv),_dot(normal,vv)]]
    j = [[u[k],v[k]] for k in range(3)]
    return normal,inverse,second,j,cross,length


def _geometry(jets,orientation):
    normal,inverse,second,j,_,_ = _geometry_parts(jets,orientation)
    # Ambient, parameterization-invariant physical shape operator, 1/mm.
    return jets[0],normal,_chain(j,inverse,second,inverse,_transpose(j))


def _curve_difference(a,b):
    while len(a) < len(b):
        a = _elevate_curve(a)
    while len(b) < len(a):
        b = _elevate_curve(b)
    return _hull([[x-y for x,y in zip(p,q)] for p,q in zip(a,b)])


def _residuals(ca,cb,oa,ob):
    ja,jb = [_hull(c) for c in ca],[_hull(c) for c in cb]
    delta = [_curve_difference(a,b) for a,b in zip(ca,cb)]
    na,ia,ba,a,xa,la = _geometry_parts(ja,oa)
    nb,ib,bb,b,xb,lb = _geometry_parts(jb,ob)
    position = _norm(delta[0])
    # Correlated Bernstein differences are taken BEFORE hulling. Telescoping
    # identities retain cancellation for identical jets without assuming raw
    # UV equality is the definition of geometric continuity.
    if oa == ob:
        dx = [oa*(x+y) for x,y in zip(_cross(delta[1],ja[2]),_cross(jb[1],delta[2]))]
    else:
        dx = [x-y for x,y in zip(xa,xb)]
    length_difference = _dot(dx,[x+y for x,y in zip(xa,xb)])/(la+lb)
    dn = [x/la-y*length_difference/(la*lb) for x,y in zip(dx,xb)]
    # sin(angle) alone accepts opposite normals: oriented dot is mandatory.
    dot = _dot(na,nb)
    cross_residual = _norm(_cross(na,nb))
    normal = I(cross_residual.lo,min(cross_residual.hi,_norm(dn).hi))
    dj = [[delta[1][k],delta[2][k]] for k in range(3)]
    dg = _matadd(_matmul(_transpose(dj),a),_matmul(_transpose(b),dj))
    di = [[-x for x in row] for row in _chain(ia,dg,ib)]
    dsecond = [[_dot(na,delta[3])+_dot(dn,jb[3]),_dot(na,delta[4])+_dot(dn,jb[4])],
               [_dot(na,delta[4])+_dot(dn,jb[4]),_dot(na,delta[5])+_dot(dn,jb[5])]]
    # A IA B_A IA A^T - B IB B_B IB B^T, five-factor telescoping.
    terms = [_chain(dj,ia,ba,ia,_transpose(a)),
             _chain(b,di,ba,ia,_transpose(a)),
             _chain(b,ib,dsecond,ia,_transpose(a)),
             _chain(b,ib,bb,di,_transpose(a)),
             _chain(b,ib,bb,ib,_transpose(dj))]
    difference = terms[0]
    for term in terms[1:]:
        difference = _matadd(difference,term)
    curvature = _norm([x for row in difference for x in row])
    return position,normal,curvature,dot


def _automatic_native_seams(patches,max_cells):
    """Complete actual interior-knot lines, independently of card roundoff."""
    seams = []
    for index,patch in enumerate(patches):
        surface,mapping = patch['face'].Surface,patch['mapping']
        if not hasattr(surface,'getUKnots'):
            continue
        domain,chart = mapping['domain_uv'],mapping['chart_uv']
        for native_axis in (0,1):
            values = surface.getUKnots() if native_axis==0 else surface.getVKnots()
            mults = surface.getUMultiplicities() if native_axis==0 else surface.getVMultiplicities()
            degree = surface.UDegree if native_axis==0 else surface.VDegree
            expanded = [float(k) for k,m in zip(values,mults) for _ in range(m)]
            start,end = expanded[degree],expanded[-degree-1]
            axis = 1-native_axis if mapping['swap_uv'] else native_axis
            other = 1-axis
            for knot in values:
                if not (start<knot<end and domain[2*native_axis]<knot<domain[2*native_axis+1]):
                    continue
                uv = [(domain[0]+domain[1])/2,(domain[2]+domain[3])/2]
                uv[native_axis]=float(knot)
                value = _chart_uv(mapping,*uv)[axis]
                side = dict(patch=index,axis='u' if axis==0 else 'v',value=value,range=chart[2*other:2*other+2],reverse=False,
                            _native_fixed=dict(axis=native_axis,value=float(knot)))
                seams.append(dict(a=side,b=copy.deepcopy(side)))
                if len(seams)>max_cells:
                    raise Unknown('automatic_native_seam_resource_bound')
    return seams


def _structural_seam(patch,a,b,order,resources):
    """Exact Ck of ONE actual spline plus continuous Jacobian regularity."""
    if any(a[k] != b[k] for k in ('patch','axis','value','range','reverse')):
        return False,0
    chart = patch['mapping']['chart_uv']
    axis = 0 if a['axis']=='u' else 1
    if not chart[2*axis] < a['value'] < chart[2*axis+1]:
        return False,0
    mapping = patch['mapping']
    t = (I(a['value'])-I(chart[2*axis]))/(I(chart[2*axis+1])-I(chart[2*axis]))
    if mapping['reverse_u' if axis==0 else 'reverse_v']:
        t = 1-t
    native_axis = 1-axis if mapping['swap_uv'] else axis
    domain = mapping['domain_uv']
    fixed = I(domain[2*native_axis])+t*(I(domain[2*native_axis+1])-I(domain[2*native_axis]))
    if a.get('_native_fixed') != b.get('_native_fixed'):
        return False,0
    if '_native_fixed' in a:
        if a['_native_fixed']['axis']!=native_axis:
            return False,0
        fixed = I(a['_native_fixed']['value'])
    surface = patch['face'].Surface
    if hasattr(surface,'getUKnots'):
        for direction in (0,1):
            knots = surface.getUKnots() if direction==0 else surface.getVKnots()
            mults = surface.getUMultiplicities() if direction==0 else surface.getVMultiplicities()
            degree = surface.UDegree if direction==0 else surface.VDegree
            expanded = [float(k) for k,m in zip(knots,mults) for _ in range(m)]
            start,end = expanded[degree],expanded[-degree-1]
            for knot,multiplicity in zip(knots,mults):
                crosses = direction!=native_axis or fixed.lo <= knot <= fixed.hi
                if start < knot < end and domain[2*direction] < knot < domain[2*direction+1] and crosses and degree-multiplicity < order:
                    return False,0
    segments = _seam_segments(patch,a,-1)
    work = [(curves[1],curves[2],0) for _,curves in segments]
    if len(work) > resources['max_cells']:
        raise Unknown('structural_regular_seam_resource_bound')
    cells = 0
    while work:
        u,v,depth = work.pop()
        cells += 1
        if _norm(_cross(_hull(u),_hull(v))).lo > 0:
            continue
        if depth >= resources['max_depth'] or cells+len(work)+2 > resources['max_cells']:
            raise Unknown('structural_seam_jacobian_singular_or_unresolved')
        uu,vv = _curve_split(u),_curve_split(v)
        work.extend((uu[k],vv[k],depth+1) for k in (0,1))
    return True,cells


def certify_continuity(patches,c):
    limits = [c['maximum_position_mm'],c['maximum_normal_sin']]
    if c['metric']=='g2_continuity':
        limits.append(c['maximum_curvature_per_mm'])
    work = []
    structural_cells,structural_seams = 0,0
    native_seams = _automatic_native_seams(patches,c['resources']['max_cells'])
    all_seams = c['seams']+native_seams
    if len(all_seams)>c['resources']['max_cells']:
        raise Unknown('full_native_and_registered_seam_resource_bound')
    for seam in all_seams:
        a,b = seam['a'],seam['b']
        pa,pb = patches[a['patch']],patches[b['patch']]
        if a['patch']==b['patch']:
            structural,count = _structural_seam(pa,a,b,2 if c['metric']=='g2_continuity' else 1,c['resources'])
            if structural:
                structural_cells += count
                structural_seams += 1
                if structural_cells > c['resources']['max_cells']:
                    raise Unknown('structural_seam_total_resource_bound')
                continue
        sa,sb = _seam_segments(pa,a,-1),_seam_segments(pb,b,1)
        if len(sa)*len(sb)+len(work) > c['resources']['max_cells']:
            raise Unknown('seam_pair_search_exceeds_resource_bound')
        for (ba,ca) in sa:
            for (bb,cb) in sb:
                lo,hi = max(ba[0],bb[0]),min(ba[1],bb[1])
                if lo >= hi:
                    continue
                xa = [_curve_restrict(p,(lo-ba[0])/(ba[1]-ba[0]),(hi-ba[0])/(ba[1]-ba[0])) for p in ca]
                xb = [_curve_restrict(p,(lo-bb[0])/(bb[1]-bb[0]),(hi-bb[0])/(bb[1]-bb[0])) for p in cb]
                work.append((xa,xb,pa['orientation'],pb['orientation'],0))
                if len(work) > c['resources']['max_cells']:
                    raise Unknown('initial_seam_grid_exceeds_resource_bound')
    if len(work) > c['resources']['max_cells']:
        raise Unknown('initial_seam_grid_exceeds_resource_bound')
    upper,lower = [0.]*len(limits),[0.]*len(limits)
    visited,unknown = structural_cells,False
    while work:
        ca,cb,oa,ob,depth = work.pop()
        visited += 1
        try:
            residuals = _residuals(ca,cb,oa,ob)
            point = _residuals([[_curve_at(p,.5)] for p in ca],[[_curve_at(p,.5)] for p in cb],oa,ob)
            for i in range(len(limits)):
                lower[i] = max(lower[i],point[i].lo)
            if point[3].hi < 0 or any(x > t for x,t in zip(lower,limits)):
                return 'FAIL',dict(lower=lower,upper=None),dict(cells=visited,coverage='all_registered_and_automatic_exact_native_seams',automatic_native_seams=len(native_seams),method='oriented_normal_and_ambient_shape_operator_intervals')
            good = residuals[3].lo > 0 and all(residuals[i].hi <= limits[i] for i in range(len(limits)))
        except Unknown:
            residuals,good = None,False
        if good:
            for i in range(len(limits)):
                if upper[i] is not None:
                    upper[i] = max(upper[i],residuals[i].hi)
            continue
        if depth >= c['resources']['max_depth'] or visited+len(work)+2 > c['resources']['max_cells']:
            unknown = True
            for i in range(len(limits)):
                upper[i] = None if residuals is None or upper[i] is None else max(upper[i],residuals[i].hi)
            continue
        split_a = [_curve_split(p) for p in ca]
        split_b = [_curve_split(p) for p in cb]
        for k in (0,1):
            work.append(([p[k] for p in split_a],[p[k] for p in split_b],oa,ob,depth+1))
    return ('UNVERIFIED' if unknown else 'PASS'),dict(lower=lower,upper=upper),dict(cells=visited,resource_exhausted=unknown,coverage='all_registered_grid_face_boundaries_and_actual_native_knot_seams',method='physical_interval_residuals_or_exact_single_spline_Ck_with_regular_jacobian',structural_exact_seams=structural_seams,automatic_native_seams=len(native_seams),continuous_interval_seams=len(all_seams)-structural_seams,units=['mm','sin_angle','1/mm'][:len(limits)])


def _edge_ends(edge):
    low,high = edge.ParameterRange
    return [_xyz(edge.valueAt(low)),_xyz(edge.valueAt(high))]


def _edge_orientation(a,b,eps):
    aa,bb = _edge_ends(a),_edge_ends(b)
    forward = all(math.dist(x,y) <= eps for x,y in zip(aa,bb))
    backward = all(math.dist(x,y) <= eps for x,y in zip(aa,reversed(bb)))
    if forward == backward:
        return None
    return backward


def _curve_polynomials(curve,low,high):
    import Part
    if isinstance(curve,Part.Line):
        location,direction = [I(x) for x in _xyz(curve.Location)],[I(x) for x in _xyz(curve.Direction)]
        spans = [([0.,1.],[[p+d*I(t) for p,d in zip(location,direction)] for t in (low,high)])]
    else:
        bezier = isinstance(curve,Part.BezierCurve)
        if not isinstance(curve,(Part.BSplineCurve,Part.BezierCurve)) or curve.isRational() or curve.isPeriodic():
            raise Unknown('unsupported_outside_trim_curve_domain')
        weights = list(map(float,curve.getWeights()))
        if not weights or any(not math.isfinite(w) or w<=0 for w in weights):
            raise Unknown('invalid_native_trim_curve_weights')
        if any(w!=weights[0] for w in weights):
            raise Unknown('unsupported_rational_trim_curve')
        if curve.Degree > 12 or len(curve.getPoles()) > 4096:
            raise Unknown('outside_trim_polynomial_resource_bound')
        poles = [[I(x) for x in _xyz(p)] for p in curve.getPoles()]
        values = [0.,1.] if bezier else list(curve.getKnots())
        multiplicities = [curve.Degree+1]*2 if bezier else curve.getMultiplicities()
        knots = [float(k) for k,m in zip(values,multiplicities) for _ in range(m)]
        start,end = knots[curve.Degree],knots[-curve.Degree-1]
        partitions = sorted(set([low,high]+[float(k) for k in values if start<k<end and low < k < high]))
        spans = [([(a-low)/(high-low),(b-low)/(high-low)],_bezier_curve(poles,knots,curve.Degree,a,b)) for a,b in zip(partitions,partitions[1:])]
    return spans


def _edge_polynomials(edge,reverse):
    spans = _curve_polynomials(edge.Curve,*map(float,edge.ParameterRange))
    if reverse:
        spans = [([1-b,1-a],list(reversed(net))) for (a,b),net in spans]
    return spans


def _edge_upper(a,b,reverse,target,resources,face_a,face_b):
    import FreeCAD as App
    aa,bb = _edge_polynomials(a,False),_edge_polynomials(b,reverse)
    if len(aa)*len(bb) > resources['max_cells']:
        raise Unknown('outside_trim_pair_search_resource_bound')
    work = []
    for ba,ca in aa:
        for bbounds,cb in bb:
            low,high = max(ba[0],bbounds[0]),min(ba[1],bbounds[1])
            if low < high:
                x = _curve_restrict(ca,(low-ba[0])/(ba[1]-ba[0]),(high-ba[0])/(ba[1]-ba[0]))
                y = _curve_restrict(cb,(low-bbounds[0])/(bbounds[1]-bbounds[0]),(high-bbounds[0])/(bbounds[1]-bbounds[0]))
                while len(x) < len(y):
                    x = _elevate_curve(x)
                while len(y) < len(x):
                    y = _elevate_curve(y)
                work.append((x,y,0))
    if not work:
        raise Unknown('outside_trim_incomplete_parameter_coverage')
    upper,visited = 0.,0
    while work:
        x,y,depth = work.pop()
        visited += 1
        for curve,other in ((x,face_b),(y,face_a)):
            point = _curve_at(curve,.5)
            center = [(p.lo+p.hi)/2 for p in point]
            radius = _norm([I(-max(c-p.lo,p.hi-c),max(c-p.lo,p.hi-c)) for p,c in zip(point,center)]).hi
            distance = _native_distance(App.Vector(*center),other)
            lower = max(0.,distance-radius-2*target)
            if lower > target:
                raise Changed('outside_trim_actual_closestpoint_lower',lower)
        bound = max(_norm([a-b for a,b in zip(p,q)]).hi for p,q in zip(x,y))
        if bound <= target:
            upper = max(upper,bound)
        elif depth >= resources['max_depth'] or visited+len(work)+2 > resources['max_cells']:
            raise Unknown('outside_trim_bound_unresolved_or_resource_exhausted')
        else:
            xx,yy = _curve_split(x),_curve_split(y)
            work.extend((xx[k],yy[k],depth+1) for k in (0,1))
    return upper,visited


def _support_plane(face,eps,reference=None):
    """Find an initial native plane, then certify actual polynomial support."""
    import Part
    surface = face.Surface
    if isinstance(surface,Part.Plane):
        return surface,0.
    polynomial = isinstance(surface,(Part.BSplineSurface,Part.BezierSurface))
    extrusion = type(surface).__name__=='SurfaceOfExtrusion'
    if not polynomial and not extrusion:
        return None
    plane = reference if reference is not None else face.findPlane()
    if plane is None:
        return None
    normal = [I(x) for x in _xyz(plane.Axis)]
    length = _norm(normal)
    normal = [x/length for x in normal]
    point = [I(x) for x in _xyz(plane.Position)]
    upper = 0.
    signs = set()
    if extrusion:
        u0,u1,v0,v1 = face.ParameterRange
        direction = [I(x) for x in _xyz(surface.Direction)]
        along = _dot(normal,direction)*I(v0,v1)
        for box,curve in _curve_polynomials(surface.BasisCurve,u0,u1):
            for pole in curve:
                height = _dot(normal,[p-q for p,q in zip(pole,point)])+along
                upper = max(upper,abs(height.lo),abs(height.hi))
            degree = len(curve)-1
            tangent = _hull([[degree*(q-p)/(box[1]-box[0]) for p,q in zip(a,b)] for a,b in zip(curve,curve[1:])])
            regular = _dot(normal,_cross(tangent,direction))
            if not (regular.lo>0 or regular.hi<0):
                raise Unknown('outside_extrusion_planar_projection_singular')
            signs.add(1 if regular.lo>0 else -1)
    else:
        mapping = dict(domain_uv=list(map(float,face.ParameterRange)),chart_uv=[0.,1.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        patch = _patch(face,mapping,eps/128)
        for span in patch['spans']:
            for row in span['net']:
                for pole in row:
                    height = _dot(normal,[p-q for p,q in zip(pole,point)])
                    upper = max(upper,abs(height.lo),abs(height.hi))
            jets = _jet_nets(span)
            regular = _dot(normal,_cross(_hull([p for row in jets[1] for p in row]),_hull([p for row in jets[2] for p in row])))
            if not (regular.lo>0 or regular.hi<0):
                raise Unknown('outside_polynomial_planar_projection_singular')
            signs.add(1 if regular.lo>0 else -1)
    if len(signs)!=1:
        raise Unknown('outside_projection_orientation_changes')
    if upper > eps/32:
        raise Unknown('outside_actual_support_not_certified_planar')
    return plane,upper


def _planar_trim_identity(a,b,eps,resources):
    """Full boundary homotopy + coplanar support bounds the filled face.

    Under an orthogonal planar projection, a continuous pointwise boundary
    homotopy of size h cannot change winding number for points farther than h
    from the boundary. All outer/hole wires are registered bijectively. This
    proves the FULL filled domains, not an edge-sample or area certificate.
    """
    if len(a.Edges) != len(b.Edges) or len(a.Wires) != len(b.Wires):
        raise Unknown('outside_planar_trim_topology_changed')
    used,pairs = set(),{}
    upper,cells = 0.,0
    for i,edge in enumerate(a.Edges):
        matches = [(j,_edge_orientation(edge,other,eps)) for j,other in enumerate(b.Edges)]
        matches = [(j,reverse) for j,reverse in matches if reverse is not None]
        if len(matches) != 1 or matches[0][0] in used:
            raise Unknown('outside_trim_edge_identity_missing_or_ambiguous')
        j,reverse = matches[0]
        used.add(j)
        pairs[i] = j
        bound,count = _edge_upper(edge,b.Edges[j],reverse,eps,resources,a,b)
        upper,cells = max(upper,bound),cells+count
        if cells > resources['max_cells']:
            raise Unknown('outside_trim_total_resource_bound')
    used_wires = set()
    for wire in a.Wires:
        indexes = [pairs[i] for i,edge in enumerate(a.Edges) if any(edge.isSame(e) for e in wire.Edges)]
        matches = [j for j,w in enumerate(b.Wires) if len(w.Edges)==len(indexes) and all(any(b.Edges[i].isSame(e) for e in w.Edges) for i in indexes)]
        if len(matches) != 1 or matches[0] in used_wires:
            raise Unknown('outside_trim_wire_identity_missing_or_ambiguous')
        j = matches[0]
        used_wires.add(j)
        if wire.isSame(a.OuterWire) != b.Wires[j].isSame(b.OuterWire):
            raise Unknown('outside_trim_outer_or_hole_role_changed')
    support_a,support_b = _support_plane(a,eps),_support_plane(b,eps)
    if support_a is None or support_b is None:
        raise Unknown('outside_support_planarity_not_certified')
    plane_a,error_a = support_a
    plane_b,error_b = support_b
    # Certify the candidate's actual projection into the ORIGINAL frame, not
    # merely regularity in its own independently found plane.
    _support_plane(b,eps,plane_a)
    na = [I(x) for x in _xyz(plane_a.Axis)]
    nb = [I(x) for x in _xyz(plane_b.Axis)]
    na = [x/_norm(na) for x in na]
    nb = [x/_norm(nb) for x in nb]
    alignment = _dot(na,nb)
    if not (alignment.lo > .5 or alignment.hi < -.5):
        raise Unknown('outside_planar_projection_not_regular')
    if alignment.hi < 0:
        nb = [-x for x in nb]
    position = [I(x) for x in _xyz(plane_a.Position)]
    position_b = [I(x) for x in _xyz(plane_b.Position)]
    bounds = _bounds(b)
    height = _dot([a-b for a,b in zip(na,nb)],[I(bounds[2*k],bounds[2*k+1])-position_b[k] for k in range(3)])+_dot(na,[b-a for a,b in zip(position,position_b)])
    height = max(abs(height.lo),abs(height.hi))
    # Projection boundary error and lifting the projected filled domain each
    # contribute at most this continuous support-plane height.
    upper = _up(upper+2*(height+error_a+error_b))
    if upper > eps:
        raise Unknown('outside_planar_support_or_trim_bound_unresolved')
    return upper,cells


def _outside_witness_lower(a,b,eps):
    import Part
    lower = 0.
    if not a or not b:
        return lower
    for faces,other in ((a,Part.makeCompound(b)),(b,Part.makeCompound(a))):
        for face in faces:
            points = [v.Point for v in face.Vertexes]
            points.extend(e.valueAt(sum(e.ParameterRange)/2) for e in face.Edges)
            u0,u1,v0,v1 = face.ParameterRange
            u,v = (u0+u1)/2,(v0+v1)/2
            if face.isPartOfDomain(u,v):
                points.append(face.valueAt(u,v))
            for point in points:
                lower = max(lower,max(0.,_native_distance(point,other)-2*eps))
    return lower


def _outside_preservation(source,shape,plan,output,eps,resources):
    """Register EVERY unselected face; no outside-ROI outlier is excused."""
    import Part
    selected = {int(cell['face_id'][4:])-1 for row in plan['grid'] for cell in row}
    original = [f for i,f in enumerate(source.Faces) if i not in selected]
    candidate = [f for f in shape.Faces if not any(f.isSame(p['face']) for p in output)]
    detail = dict(coverage='all_original_unselected_and_all_unmapped_candidate_faces',
                  tolerance_mm=eps,source_faces=len(original),output_faces=len(candidate))
    if len(original) != len(candidate):
        return 'FAIL',dict(detail,reason='outside_face_bijection_cardinality_changed')
    lower = _outside_witness_lower(original,candidate,eps)
    detail['lower_mm'] = lower
    if lower > eps:
        return 'FAIL',dict(detail,reason='actual_bidirectional_native_closestpoint_outside_witness')
    supports = [_support_plane(f,eps) for f in candidate]
    used,upper,cells = set(),0.,0
    for face in original:
        if not face.isValid():
            raise Unknown('outside_original_face_invalid')
        support = _support_plane(face,eps)
        if support is not None:
            matches = []
            for i,other in enumerate(candidate):
                if supports[i] is None or len(face.Edges)!=len(other.Edges):
                    continue
                if all(sum(_edge_orientation(edge,e,eps) is not None for e in other.Edges)==1 for edge in face.Edges):
                    matches.append(i)
            if len(matches) != 1 or matches[0] in used:
                raise Unknown('outside_planar_face_trim_identity_missing_or_ambiguous')
            index = matches[0]
            try:
                bound,count = _planar_trim_identity(face,candidate[index],eps,resources)
            except Changed as exc:
                return 'FAIL',dict(detail,reason=str(exc),face_lower_mm=exc.lower)
        elif isinstance(face.Surface,(Part.BSplineSurface,Part.BezierSurface)):
            domain = list(map(float,face.ParameterRange))
            mapping = dict(domain_uv=domain,chart_uv=[0.,1.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
            corners = [_xyz(face.valueAt(u,v)) for u,v in ((domain[0],domain[2]),(domain[1],domain[2]),(domain[0],domain[3]),(domain[1],domain[3]))]
            matches = []
            for i,other in enumerate(candidate):
                if not isinstance(other.Surface,(Part.BSplineSurface,Part.BezierSurface)):
                    continue
                other_domain = list(map(float,other.ParameterRange))
                for swap in (False,True):
                    for ru in (False,True):
                        for rv in (False,True):
                            other_map = dict(domain_uv=other_domain,chart_uv=[0.,1.,0.,1.],swap_uv=swap,reverse_u=ru,reverse_v=rv)
                            points = [_xyz(other.valueAt(*_native_uv(other_map,u,v))) for u,v in ((0.,0.),(1.,0.),(0.,1.),(1.,1.))]
                            if all(math.dist(p,q) <= eps for p,q in zip(corners,points)):
                                matches.append((i,other_map))
            if len(matches) != 1 or matches[0][0] in used:
                raise Unknown('outside_polynomial_full_corner_identity_missing_or_ambiguous')
            index,other_map = matches[0]
            scale = max(1.,*(abs(x) for f in (face,candidate[index]) for x in _bounds(f)))
            arithmetic = max(512*math.ulp(scale),eps/16)
            a,b = _patch(face,mapping,arithmetic),_patch(candidate[index],other_map,arithmetic)
            state,measured,ev = certify_deviation([a],[b],[0.,1.,0.,1.],eps,resources,eps)
            if state=='FAIL':
                return 'FAIL',dict(detail,reason='outside_polynomial_continuous_identity_changed',face_lower_mm=measured['lower_mm'])
            if state!='PASS':
                raise Unknown('outside_polynomial_identity_bound_unresolved')
            bound,count = measured['upper_mm'],ev['cells']
        else:
            raise Unknown('unsupported_outside_support_or_trim_domain')
        if not candidate[index].isValid():
            raise Unknown('outside_candidate_face_invalid')
        used.add(index)
        upper,cells = max(upper,bound),cells+count
        if cells > resources['max_cells']:
            raise Unknown('outside_preservation_total_resource_bound')
    return 'PASS',dict(detail,upper_mm=upper,cells=cells,method='bijective_native_support_full_trim_continuous_correspondence')


def _epsilon(source,shape,budget):
    scale = max(1.,*(abs(x) for s in (source,shape) for x in _bounds(s)))
    native = max(float(s.getTolerance(1)) for s in (source,shape))+128*math.ulp(scale)
    if not math.isfinite(native) or native > budget:
        raise Unknown('native_tolerance_exceeds_declared_numerical_uncertainty')
    # The explicit budget covers native closestpoint/trim tolerance. Polynomial
    # knot insertion itself is performed with directed interval arithmetic.
    return budget


def _maximum(value,target,error):
    return 'PASS' if value+error <= target else 'FAIL' if max(0.,value-error)>target else 'UNVERIFIED'


def judge(plan,manifest_path,prepared,body_or_shape,card,**context):
    card = validate_card(card)
    shape = getattr(body_or_shape,'Shape',body_or_shape)
    source_error = None
    try:
        source,provenance = _source(plan,manifest_path,prepared)
        eps = _epsilon(source,shape,card['numerical_uncertainty_mm'])
    except (Unknown,ValueError,KeyError,TypeError,IndexError,AttributeError,RuntimeError,OSError,OverflowError,ZeroDivisionError) as exc:
        source_error = str(exc)
    checks = []
    outside_cache = {}
    for c in card['criteria']:
        metric = c['metric']
        target = {k:v for k,v in c.items() if k not in ('id','metric','output_patches','resources','seams','output_region_mm','selection_tolerance_mm')}
        measured,error = None,None
        evidence = dict(numerical_uncertainty_budget_mm=card['numerical_uncertainty_mm'])
        try:
            if source_error:
                invalid = metric=='solid_valid' and (shape.isNull() or not shape.isValid() or not shape.isClosed() or len(shape.Solids)!=c['expected_solids'] or shape.Volume<=0)
                if not invalid:
                    raise Unknown(source_error)
                evidence['source_uncertified_reason'] = source_error
            else:
                evidence.update(provenance)
            if metric == 'solid_valid':
                measured = (dict(null=True,valid=False,closed=False,solids=0,volume_mm3=0.) if shape.isNull() else
                            dict(null=False,valid=shape.isValid(),closed=shape.isClosed(),solids=len(shape.Solids),volume_mm3=float(shape.Volume)))
                status = 'PASS' if not measured['null'] and measured['valid'] and measured['closed'] and measured['solids']==c['expected_solids'] and measured['volume_mm3']>0 else 'FAIL'
                error = 0
                evidence.update(coverage='entire_actual_brep',method='native_valid_closed_solid_count_positive_volume')
            elif metric == 'face_count':
                old,new = len(source.Faces),len(shape.Faces)
                measured = dict(source_count=old,output_count=new,delta=new-old)
                value = new if c['relation']=='equal' else new-old
                status = 'PASS' if value==c.get('expected_count',c.get('expected_delta')) else 'FAIL'
                error = 0
                evidence.update(coverage='entire_actual_brep',units='integer_faces')
            elif metric == 'native_roundtrip':
                ev = context.get('native_evidence')
                flags = ('fcstd_reopened','step_reopened','editable')
                values = ('bounds_difference_mm','volume_difference_mm3')
                if not isinstance(ev,dict) or any(type(ev.get(k)) is not bool for k in flags) or any(type(ev.get(k)) not in (int,float) or not math.isfinite(ev[k]) or ev[k]<0 for k in values):
                    raise Unknown('native_reopen_evidence_missing_or_invalid')
                measured = {k:ev[k] for k in flags+values}
                error = dict(mm=2*eps,mm3=eps*(source.Area+shape.Area)+128*math.ulp(max(1.,shape.Volume)))
                states = [_maximum(ev['bounds_difference_mm'],c['maximum_bounds_difference_mm'],error['mm']),_maximum(ev['volume_difference_mm3'],c['maximum_volume_difference_mm3'],error['mm3'])]
                if not ev['fcstd_reopened'] or not ev['step_reopened'] or (c['require_editable'] and not ev['editable']):
                    status = 'FAIL'
                else:
                    status = 'FAIL' if 'FAIL' in states else 'UNVERIFIED' if 'UNVERIFIED' in states else 'PASS'
                evidence.update(coverage='actual_independent_fcstd_and_step_reopen',method='shared_worker_reopen_not_fitted_self_report')
            else:
                original,domain = _original(source,plan,eps)
                output = _output(shape,c,eps)
                _tile([p['mapping']['chart_uv'] for p in output],domain)
                _tile([s['box'] for p in output for s in p['spans']],domain)
                key = repr((c['output_region_mm'],c['output_patches'],c['selection_tolerance_mm'],c['resources']))
                if key not in outside_cache:
                    try:
                        outside_cache[key] = _outside_preservation(source,shape,plan,output,eps,c['resources'])
                    except Unknown as exc:
                        outside_cache[key] = str(exc)
                preserved = outside_cache[key]
                if isinstance(preserved,str):
                    raise Unknown(preserved)
                outside_state,outside_evidence = preserved
                evidence['outside_preservation'] = outside_evidence
                if outside_state!='PASS':
                    status = outside_state
                    extra = dict(reason='complete_original_unselected_region_preservation_failed',coverage='entire_actual_candidate_and_immutable_source')
                elif metric=='surface_deviation':
                    status,measured,extra = certify_deviation(original,output,domain,c['maximum_mm'],c['resources'],eps)
                    error = eps
                else:
                    _seam_coverage(output,c,domain)
                    status,measured,extra = certify_continuity(output,c)
                    error = dict(coordinate_mm=eps,arithmetic='binary64_outward_rounded_interval_operations')
                evidence.update(extra,domain='nonrational_nonperiodic_rectangular_polynomial_spline',native_control_enclosure_mm=eps,correspondence='independently_validated_full_chart_tiling_unique_spatial_roi_and_all_unselected_faces')
                evidence['observed_output_domains_uv'] = [dict(patch=i,method=p['domain_method'],domain_uv=p['mapping']['domain_uv'],chart_uv=p['mapping']['chart_uv'],maximum_trim_physical_bound_mm=max(s['trim_physical_bound_mm'] for s in p['spans'])) for i,p in enumerate(output)]
        except (Unknown,ValueError,KeyError,TypeError,IndexError,AttributeError,RuntimeError,OSError,OverflowError,ZeroDivisionError) as exc:
            status = 'UNVERIFIED'
            evidence.update(reason=str(exc),coverage='uncertified')
        checks.append(dict(id=c['id'],metric=metric,status=status,measured=measured,target=target,tolerance=target,uncertainty=error,evidence=evidence))
    status = 'FAIL' if any(c['status']=='FAIL' for c in checks) else 'UNVERIFIED' if any(c['status']=='UNVERIFIED' for c in checks) else 'PASS'
    return dict(schema='cad-harness.judgement.v4c',profile='c-s3',status=status,checks=checks)
