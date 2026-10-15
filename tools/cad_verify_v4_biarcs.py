"""Deterministic, source-certified pixel or physical-unit boundary fitting.

Historical v1 retains hard corners and its pixel budget. Explicit v2 uses
physical-unit periodic cubic fits and shared-tangent biarcs. Bounded analytic
line/circle normal proposals precede source certification. Branch-order-only
curvature proposals precede stronger material-facing thickness constraints;
fine disk-opening measurements reject inaccessible proposals, never construct
output. These producer guards do not certify independent actual-output checks.
No mask repair, polygon-buffer output or post-score change is performed.
"""
import bisect
import math

MAX_SEGMENTS = 8192


def _add(a,b): return (a[0]+b[0],a[1]+b[1])
def _sub(a,b): return (a[0]-b[0],a[1]-b[1])
def _mul(a,k): return (a[0]*k,a[1]*k)
def _dot(a,b): return a[0]*b[0]+a[1]*b[1]
def _cross(a,b): return a[0]*b[1]-a[1]*b[0]


def _unit(v):
    length=math.hypot(*v)
    if length==0: raise ValueError('contour_curve_fit_zero_tangent')
    return _mul(v,1/length)


def _arc(a,b,tangent):
    chord=_sub(b,a);length=math.hypot(*chord)
    if length==0: raise ValueError('contour_curve_fit_zero_chord')
    normal=(-tangent[1],tangent[0]);den=2*_dot(normal,chord)
    if abs(den)<=128*math.ulp(max(1.,length)):
        if _dot(chord,tangent)<=0: raise ValueError('contour_curve_fit_reversed_line')
        return (dict(kind='line',p0=list(a),p1=list(b)),None,0.,0.,0.)
    offset=_dot(chord,chord)/den
    center=_add(a,_mul(normal,offset));radius=abs(offset)
    start=math.atan2(a[1]-center[1],a[0]-center[0])
    sweep=2*math.atan2(_cross(tangent,chord),_dot(tangent,chord))
    sagitta=2*radius*math.sin(sweep/4)**2
    middle=_mul(_add(a,b),.5)
    left=(-chord[1]/length,chord[0]/length)
    p=_sub(middle,_mul(left,math.copysign(sagitta,sweep)))
    return (dict(kind='arc',p0=list(a),pm=list(p),p1=list(b)),center,radius,start,sweep)


def _reverse(arc):
    segment,center,radius,start,sweep=arc
    result=dict(segment,p0=segment['p1'],p1=segment['p0'])
    return result,center,radius,start+sweep,-sweep


def _biarc(a,b,ta,tb):
    v=_sub(b,a);length2=_dot(v,v)
    along=_dot(v,_add(ta,tb));coefficient=2*(1-max(-1.,min(1.,_dot(ta,tb))))
    denominator=along+math.sqrt(max(0.,along*along+coefficient*length2))
    if denominator<=0: raise ValueError('contour_curve_fit_no_forward_biarc')
    distance=length2/denominator
    middle=_mul(_add(_add(a,b),_mul(_sub(ta,tb),distance)),.5)
    return [_arc(a,middle,ta),_reverse(_arc(b,middle,_mul(tb,-1)))]


def _flatten(arcs,tolerance):
    points=[];error=0.
    for segment,center,radius,start,sweep in arcs:
        if center is None:
            current=[segment['p0'],segment['p1']]
        else:
            angle=4*math.asin(math.sqrt(min(tolerance/(2*radius),.5)))
            if angle==0: raise ValueError('contour_curve_fit_resolution')
            count=max(1,math.ceil(abs(sweep)/angle))
            if count>1000000: raise ValueError('contour_curve_fit_resource_limit')
            radial=_sub(segment['p0'],center)
            current=[]
            for i in range(count+1):
                delta=sweep*i/count
                cm1=-2*math.sin(delta/2)**2
                sine=math.sin(delta)
                current.append((segment['p0'][0]+radial[0]*cm1-radial[1]*sine,
                                segment['p0'][1]+radial[1]*cm1+radial[0]*sine))
            current[0],current[-1]=segment['p0'],segment['p1']
            error=max(error,2*radius*math.sin(abs(sweep)/count/4)**2)
        points.extend(current if not points else current[1:])
    return points,error


def _samples(points,step):
    result=[];cover=0.
    for a,b in zip(points,points[1:]):
        length=math.dist(a,b);count=max(1,math.ceil(length/step))
        if len(result)+count>1000000: raise ValueError('contour_curve_fit_resource_limit')
        cover=max(cover,length/count/2)
        result.extend((a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count))
    result.append(points[-1])
    return result,cover


def _error(source,arcs,limit):
    import numpy as np
    import shapely
    from shapely.geometry import LineString
    output,curve_error=_flatten(arcs,limit/64)
    maximum=cover=0.
    for a,b in ((source,output),(output,source)):
        samples,gap=_samples(a,limit/4)
        distances=shapely.distance(shapely.points(samples),LineString(b))
        maximum=max(maximum,float(np.max(distances)));cover=max(cover,gap)
    magnitude=max(1.,*(abs(v) for p in source+output for v in p))
    return maximum+cover+curve_error+128*math.ulp(magnitude)


def _tangents(points,span,corner_degrees):
    n=len(points);closed=points+[points[0]];distances=[0.]
    for a,b in zip(closed,closed[1:]):distances.append(distances[-1]+math.dist(a,b))
    perimeter=distances[-1];window=min(span,perimeter/8)
    def at(s):
        s%=perimeter;i=min(n-1,bisect.bisect_right(distances,s)-1)
        f=(s-distances[i])/(distances[i+1]-distances[i])
        return _add(closed[i],_mul(_sub(closed[i+1],closed[i]),f))
    incoming=[];outgoing=[];corners=[]
    threshold=math.cos(math.radians(corner_degrees))
    for i,p in enumerate(points):
        back,forward=at(distances[i]-window),at(distances[i]+window)
        before,after=_unit(_sub(p,back)),_unit(_sub(forward,p))
        hard=_dot(before,after)<threshold
        if hard:
            incoming.append(_unit(_sub(p,points[i-1])))
            outgoing.append(_unit(_sub(points[(i+1)%n],p)));corners.append(i)
        else:
            tangent=_unit(_sub(forward,back));incoming.append(tangent);outgoing.append(tangent)
    return incoming,outgoing,corners


def _spline_data(points, spacing, rms):
    import numpy as np
    from scipy.interpolate import splprep
    closed=np.asarray(points+[points[0]],dtype=float)
    lengths=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(closed,axis=0),axis=1))))
    count=max(8,math.ceil(float(lengths[-1])/spacing))
    if count>1000000:raise ValueError('contour_curve_fit_resource_limit')
    parameters=np.arange(count+1,dtype=float)/count
    samples=[np.interp(parameters*lengths[-1],lengths,closed[:,axis]) for axis in (0,1)]
    (tck,_),_,status,_=splprep(samples,u=parameters,k=3,per=True,
        s=count*rms**2,full_output=1)
    if status>0:raise ValueError('contour_curve_fit_spline_not_converged')
    return tck, parameters, samples, float(lengths[-1])


def _smooth(points,config,rms):
    """Frozen FITPACK proposal; only the final boundary enclosure certifies it."""
    from scipy.interpolate import splev
    tck, parameters, _, _ = _spline_data(points, config['sample_spacing_pixels'], rms)
    xy=splev(parameters[:-1],tck)
    derivative=splev(parameters[:-1],tck,der=1)
    fitted=list(zip(xy[0].tolist(),xy[1].tolist()))
    tangents=[_unit(v) for v in zip(derivative[0].tolist(),derivative[1].tolist())]
    def evaluate(parameter):
        xy=splev(parameter,tck)
        derivative=splev(parameter,tck,der=1)
        return (float(xy[0]),float(xy[1])),_unit((float(derivative[0]),float(derivative[1])))
    return fitted,tangents,evaluate


def _approximate(points,incoming,outgoing,corners,limit,remaining,evaluate=None):
    n=len(points)
    anchors=corners or sorted({int(k*n/4) for k in range(4)})
    if len(anchors)==1:anchors=sorted(set(anchors+[int((anchors[0]+n//2)%n)]))
    anchors=anchors+[anchors[0]+n]
    segments=[];fitted_arcs=[];extra={}
    def sample(index):
        if int(index)==index:
            i=int(index)%n
            return points[i],incoming[i],outgoing[i]
        if index not in extra:
            point,tangent=evaluate(index/n)
            extra[index]=(point,tangent,tangent)
        return extra[index]
    def fit(i,j,depth=0):
        a,_,ta=sample(i);b,tb,_=sample(j)
        path=[a]+[points[k%n] for k in range(math.floor(i)+1,math.ceil(j))]+[b]
        try:
            arcs=_biarc(a,b,ta,tb)
        except ValueError:
            arcs=[]
        accepted=bool(arcs) and _error(path,arcs,limit)<=limit
        if accepted:
            if len(segments)+len(arcs)>remaining:raise ValueError('contour_curve_fit_segment_limit')
            segments.extend(arc[0] for arc in arcs);fitted_arcs.extend(arcs)
        elif depth<32 and (j-i>1 or evaluate is not None):
            middle=math.floor((i+j)/2) if j-i>1 else (i+j)/2
            fit(i,middle,depth+1);fit(middle,j,depth+1)
        else:
            raise ValueError('contour_curve_fit_error_budget_unattainable')
    for a,b in zip(anchors,anchors[1:]):fit(a,b)
    return segments,fitted_arcs


def _simple_candidate(raw, arcs, tolerance, *, contacts=(), role='outer'):
    """Proposal guard only; exact final topology/clearance is checked again."""
    from shapely.geometry import Point, Polygon
    points, error = _flatten(arcs, tolerance / 8)
    polygon = Polygon(points)
    before = sum(_cross(a, b) for a, b in zip(raw, raw[1:] + raw[:1]))
    after = sum(_cross(a, b) for a, b in zip(points, points[1:]))
    if not polygon.is_valid or polygon.area <= 0 or before * after <= 0:
        return False
    original = Polygon(raw)
    if original.is_valid and polygon.intersection(original).area <= 0:
        return False
    for contact in contacts:
        point = Point(contact['point'])
        distance = (polygon.distance(point) if role == 'outer' else
                    polygon.boundary.distance(point) if polygon.contains(point) else 0.)
        if distance <= error:
            return False
    return True


def _loop_contacts(raw, shared):
    lengths = [0.]
    for a, b in zip(raw, raw[1:] + raw[:1]):
        lengths.append(lengths[-1] + math.dist(a, b))
    result = []
    for i, point in enumerate(raw):
        if point not in shared:
            continue
        before = _unit(_sub(point, raw[i-1]))
        after = _unit(_sub(raw[(i+1) % len(raw)], point))
        normal = _unit((-before[1]-after[1], before[0]+after[0]))
        result.append(dict(point=point, normal=normal, parameter=lengths[i]/lengths[-1]))
    return result


def _circle_proposals(raw, radius, contacts, role, tolerance):
    """Try a bounded primitive for undersized loops; never drop a piece.

    A source-area threshold is deliberately NOT an admission predicate.
    The ordinary source/R/topology certificates decide every proposal.
    """
    bounds = (min(p[0] for p in raw), max(p[0] for p in raw),
              min(p[1] for p in raw), max(p[1] for p in raw))
    if math.hypot(bounds[1]-bounds[0], bounds[3]-bounds[2]) > 2*radius:
        return
    radius += 256 * math.ulp(max(1., radius))
    center = ((bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2)
    vertices = sorted({tuple(contact['point']) for contact in contacts})
    clearance = tolerance / 2
    contact_radius = radius + clearance if role == 'outer' else radius - clearance
    candidates = [center]
    for multiplier in (1, 2, 4, 8):
        current_radius = radius + clearance*multiplier if role == 'outer' else radius - clearance*multiplier
        if current_radius <= 0:
            continue
        for point in vertices:
            delta = _sub(center, point)
            if math.hypot(*delta):
                candidates.append(_add(point, _mul(_unit(delta), current_radius)))
            candidates.extend(_add(point, _mul((math.cos(i*math.pi/8), math.sin(i*math.pi/8)),
                                               current_radius)) for i in range(16))
        if len(vertices) <= 64:
            for i, a in enumerate(vertices):
                for b in vertices[i+1:]:
                    delta = _sub(b, a)
                    distance = math.hypot(*delta)
                    if not distance or distance > 2*current_radius:
                        continue
                    half = _mul(_add(a, b), .5)
                    normal = (-delta[1]/distance, delta[0]/distance)
                    offset = math.sqrt(max(0., current_radius**2-distance**2/4))
                    candidates.extend((_add(half, _mul(normal, offset)),
                                       _sub(half, _mul(normal, offset))))
    allowance = 256 * math.ulp(max(1., radius, *(abs(v) for p in candidates for v in p)))
    sign = 1 if role == 'outer' else -1
    directions = [(-1., 0.), (0., -sign), (1., 0.), (0., sign), (-1., 0.)]
    q = math.sqrt(.5)
    middles = [(-q, -sign*q), (q, -sign*q), (q, sign*q), (-q, sign*q)]
    for candidate in sorted(set(candidates), key=lambda p: (math.dist(p, center), p)):
        distances = [math.dist(candidate, point) for point in vertices]
        if any((distance < contact_radius-allowance if role == 'outer'
                else distance > contact_radius+allowance) for distance in distances):
            continue
        segments, arcs = [], []
        for i in range(4):
            segment = dict(kind='arc', p0=list(_add(candidate, _mul(directions[i], radius))),
                pm=list(_add(candidate, _mul(middles[i], radius))),
                p1=list(_add(candidate, _mul(directions[i+1], radius))))
            segments.append(segment)
            arcs.append((segment, candidate, radius, math.pi+sign*i*math.pi/2, sign*math.pi/2))
        yield segments, arcs


def _material_region(loops, rings):
    """Assemble the original forest, including islands, without altering it."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    return unary_union([Polygon(rings[i], [
        rings[j] for j, child in enumerate(loops)
        if child['role'] == 'hole' and child.get('parent') == i])
        for i, loop in enumerate(loops) if loop['role'] == 'outer'])


def _material_reachable(region, error, radius, tolerance, *, possible_void=None):
    """Reject proposals with material a disk cannot sweep.

    This intentionally is only a fine polygon measurement, NOT a certificate
    of the arcs or exported CAD. Radius is the nominal actual-tool radius,
    never the curvature construction reserve. Reduce it by chord uncertainty
    before erosion (an inscribed radius-R polygon otherwise has an empty
    radius-R erosion). Partial layouts may exclude a conservative envelope of
    still-unplaced holes from rejection; completed components exclude nothing.
    Inflate the measured opening only by its tessellation/chord uncertainty;
    remaining area must be below the squared representation tolerance.
    Neither the original mask nor the proposed boundary is replaced.
    """
    resolution = tolerance / 128
    tool = radius - 2 * error - resolution
    if tool <= 0 or region.is_empty or not region.is_valid:
        return False
    angle = math.acos(max(-1., min(1., 1-resolution/tool)))
    quadrants = max(8, math.ceil(math.pi/(4*angle))) if angle else 1024
    centers = region.buffer(-tool, quad_segs=quadrants)
    if centers.is_empty:
        return False
    swept = centers.buffer(tool, quad_segs=quadrants)
    numerical_band = 2 * error + 4 * resolution
    uncovered = region.difference(swept.buffer(numerical_band, quad_segs=quadrants))
    if possible_void is not None:
        uncovered = uncovered.difference(possible_void)
    return uncovered.area <= tolerance ** 2


def _material_pairs(target, neighbours, distances, perimeter, radius, maximum, material):
    """Select nearby nonlocal chords actually crossing original material.

    Void-facing branches must NOT be forced apart as material: doing so would
    destroy narrow holes/slots. Full-segment coverage, rather than a midpoint
    test, also avoids constraints spanning another intervening void.
    """
    import numpy as np
    import shapely
    pairs = set()
    for i, (near, lengths) in enumerate(zip(neighbours, distances)):
        for j, distance in zip(near, lengths):
            j = int(j)
            along = min(abs(i-j), len(target)-abs(i-j)) * perimeter / len(target)
            if along <= 4 * radius or distance <= 0 or distance >= 2 * maximum:
                continue
            pairs.add(tuple(sorted((i, j))))
    ordered = sorted(pairs)
    if not ordered:
        return set()
    chords = shapely.linestrings(np.asarray([[target[i], target[j]] for i, j in ordered]))
    covered = [pair for pair, inside in zip(ordered, shapely.covers(material, chords)) if inside]
    incident = [[] for _ in target]
    for i, j in covered:
        length = float(np.linalg.norm(target[i]-target[j]))
        incident[i].append((length, j))
        incident[j].append((length, i))
    return {tuple(sorted((i, j))) for i, near in enumerate(incident)
            for _, j in sorted(near)[:4]}


def _curvature_proposal(raw, config, radius, contacts=(), *, material=None, other_points=(),
                        tool_radius=None, enforce_material=True):
    """Constrained periodic-spline proposal, never a geometric certificate.

    Analytic sampled derivatives constrain curvature. Linear source-branch
    inequalities keep material-facing branches at least two tool radii
    apart; this reserve is separate from curvature construction slack.
    Void-facing branches only preserve ordering. Other loops share the
    required displacement equally about their original separating midpoint.
    Source coverage classifies sides, not a stress-case name or source area.
    Sampling and frozen source normals can miss contacts or be infeasible:
    final biarcs, original-source enclosure, forest and disk-opening rejection
    are still mandatory, and actual CAD remains independently checked.
    """
    import numpy as np
    from scipy.interpolate import BSpline
    from scipy.optimize import LinearConstraint, minimize
    from scipy.spatial import cKDTree
    perimeter_hint = sum(math.dist(a, b) for a, b in zip(raw, raw[1:] + raw[:1]))
    area_hint = abs(sum(_cross(a, b) for a, b in zip(raw, raw[1:] + raw[:1]))) / 2
    # A coarse initialization can collapse a narrow closed loop before the
    # solver starts. Keep its two source branches represented in the basis.
    # Width-constrained fitting needs local degrees of freedom: start at the
    # declared RMS rather than erasing detail at half a tool radius. The same
    # bounded doubling schedule still enforces the unchanged control budget.
    initial_rms = min(config['smoothing_rms_mm'] if enforce_material else
                      max(config['smoothing_rms_mm'], config['minimum_radius_mm'] / 2),
                      area_hint / (4 * perimeter_hint))
    # Complex loops may only reach the existing control budget at a later
    # frozen RMS doubling. Do not fail solely because the finest basis is
    # too large, and do not raise the control/iteration budgets. Coarsening
    # is a proposal only: material, source and topology guards still apply.
    for attempt in range(config['maximum_fit_passes']):
        tck, parameters, samples, perimeter = _spline_data(
            raw, config['sample_spacing_mm'], initial_rms * 2**attempt)
        knots, coefficients, degree = tck
        count = len(coefficients[0]) - degree
        if count <= 256:
            break
    else:
        raise ValueError('contour_curvature_fit_control_limit')
    initial = np.asarray(coefficients, dtype=float).T[:count]
    basis = BSpline(knots, np.eye(count + degree), degree)
    def reduced(values):
        result = values[:, :count].copy()
        result[:, :degree] += values[:, count:]
        return result
    positions = reduced(basis(parameters[:-1]))
    target = np.asarray(samples, dtype=float).T[:-1]
    construction_radius = radius + config['biarc_error_mm']
    thickness_radius = (config['minimum_radius_mm'] + config['biarc_error_mm']/128
                        if tool_radius is None else tool_radius)
    distances, neighbours = cKDTree(target).query(target, k=min(64, len(target)))
    # A numerical-only envelope makes interpolated points on the original
    # cell edges count as covered despite floating-point interpolation.
    numerical = 256 * math.ulp(max(1., *(abs(v) for p in raw for v in p)))
    material_pairs = set()
    if enforce_material:
        if material is None:
            from shapely.geometry import Polygon
            material = Polygon(raw)
        coverage = material.buffer(numerical)
        material_pairs = _material_pairs(target, neighbours, distances, perimeter,
            radius, config['maximum_error_mm'], coverage)
    pairs = set()
    for i, (near, lengths) in enumerate(zip(neighbours, distances)):
        used = 0
        for j, distance in zip(near, lengths):
            j = int(j)
            along = min(abs(i-j), len(target)-abs(i-j)) * perimeter / len(target)
            if along <= 4 * radius or distance <= 0 or distance >= 2 * config['maximum_error_mm']:
                continue
            pairs.add(tuple(sorted((i, j))))
            used += 1
            if used == 4:
                break
    pairs.update(material_pairs)
    separation, margins = [], []
    for i, j in sorted(pairs):
        delta = target[i] - target[j]
        length = float(np.linalg.norm(delta))
        normal = delta / length
        difference = positions[i] - positions[j]
        separation.append(np.concatenate((difference * normal[0], difference * normal[1])))
        margins.append(2 * thickness_radius if (i, j) in material_pairs else
                       min(length / 2, 2 * config['biarc_error_mm']))
    if enforce_material and len(other_points):
        import shapely
        other = np.asarray(other_points, dtype=float)
        lengths, near = cKDTree(other).query(target, k=min(64, len(other)))
        lengths, near = lengths.reshape(len(target), -1), near.reshape(len(target), -1)
        candidates = []
        for i, (indices, distances_to_other) in enumerate(zip(near, lengths)):
            for j, distance in zip(indices, distances_to_other):
                if distance <= numerical or distance >= 2 * config['maximum_error_mm']:
                    continue
                candidates.append((i, int(j), float(distance)))
        if candidates:
            chords = shapely.linestrings(np.asarray([
                [target[i], other[j]] for i, j, _ in candidates]))
            admitted = [0] * len(target)
            for (i, j, length), covered in zip(candidates, shapely.covers(coverage, chords)):
                if not covered or admitted[i] == 4:
                    continue
                admitted[i] += 1
                normal = (target[i] - other[j]) / length
                separation.append(np.concatenate((positions[i]*normal[0], positions[i]*normal[1])))
                margins.append(float((target[i]+other[j]) @ normal / 2) + thickness_radius)
    spans = np.unique(knots[degree:-degree])
    constraints_at = np.concatenate([
        a + (b-a) * np.arange(12) / 12 for a, b in zip(spans, spans[1:])])
    for contact in contacts:
        normal, point = np.asarray(contact['normal']), np.asarray(contact['point'])
        support = (np.asarray(raw) - point) @ normal
        numerical = 256 * math.ulp(max(1., *(abs(v) for p in raw for v in p)))
        if float(np.min(support)) >= -numerical:
            # B-spline basis functions are nonnegative: supporting every
            # control point also supports the entire proposed curve.
            local = np.eye(count)
        else:
            delta = np.abs(parameters[:-1] - contact['parameter'])
            delta = np.minimum(delta, 1-delta)
            selected = parameters[:-1][delta <= min(4*radius/perimeter, .125)]
            local = reduced(basis(np.concatenate((selected, [contact['parameter']]))))
        rows = np.concatenate((normal[0]*local, normal[1]*local), axis=1)
        separation.extend(rows)
        margins.extend([float(point @ normal) + 2*config['biarc_error_mm']] * len(rows))
    first = reduced(basis.derivative(1)(constraints_at))
    second = reduced(basis.derivative(2)(constraints_at))
    def unpack(value):
        return np.column_stack((value[:count], value[count:]))
    def objective(value):
        residual = positions @ unpack(value) - target
        return float(np.sum(residual * residual) / len(target))
    def gradient(value):
        residual = positions @ unpack(value) - target
        result = 2 * positions.T @ residual / len(target)
        return np.concatenate((result[:, 0], result[:, 1]))
    def state(value):
        velocity, acceleration = first @ unpack(value), second @ unpack(value)
        squared = np.maximum(np.sum(velocity * velocity, axis=1), 1e-24)
        cross = velocity[:, 0] * acceleration[:, 1] - velocity[:, 1] * acceleration[:, 0]
        return velocity, acceleration, squared, cross
    def constraints(value):
        _, _, squared, cross = state(value)
        curvature = 1 - construction_radius ** 2 * cross ** 2 / squared ** 3
        speed = squared / perimeter ** 2 - 1e-4
        return np.concatenate((curvature, speed))
    def jacobian(value):
        velocity, acceleration, squared, cross = state(value)
        dx = acceleration[:, 1, None] * first - velocity[:, 1, None] * second
        dy = velocity[:, 0, None] * second - acceleration[:, 0, None] * first
        sx, sy = 2 * velocity[:, 0, None] * first, 2 * velocity[:, 1, None] * first
        factor = 2 * cross / squared ** 3
        speed_factor = 3 * cross ** 2 / squared ** 4
        gx = -construction_radius ** 2 * (factor[:, None] * dx - speed_factor[:, None] * sx)
        gy = -construction_radius ** 2 * (factor[:, None] * dy - speed_factor[:, None] * sy)
        return np.concatenate((np.concatenate((gx, gy), axis=1),
                               np.concatenate((sx, sy), axis=1) / perimeter ** 2), axis=0)
    restrictions = [{'type': 'ineq', 'fun': constraints, 'jac': jacobian}]
    if separation:
        restrictions.append(LinearConstraint(np.asarray(separation), np.asarray(margins), np.inf))
    solved = minimize(objective, np.concatenate((initial[:, 0], initial[:, 1])),
        jac=gradient, method='SLSQP', constraints=restrictions,
        options={'maxiter': 200, 'ftol': 1e-9, 'disp': False})
    if not solved.success:
        raise ValueError('contour_curvature_fit_not_converged:' + str(solved.message))
    control = unpack(solved.x)
    curve = BSpline(knots, np.vstack((control, control[:degree])), degree)
    derivative = curve.derivative()
    xy, velocity = curve(parameters[:-1]), derivative(parameters[:-1])
    points = [tuple(row) for row in xy.tolist()]
    tangents = [_unit(tuple(row)) for row in velocity.tolist()]
    def evaluate(parameter):
        return tuple(curve(parameter).tolist()), _unit(tuple(derivative(parameter).tolist()))
    return points, tangents, evaluate


def _parallel_candidates(segments, arcs, config, minimum_radius, limit):
    """Exact line/circle normal proposals, before ANY source certification.

    Every ring keeps material on its left; a right-normal displacement grows
    material and shrinks holes. No polygon buffer becomes output geometry.
    Positive offsets never replace zero-offset candidates already certified.
    """
    yield segments, arcs
    maximum = min([limit] + [radius-minimum_radius
        for _, center, radius, _, sweep in arcs if center is not None and sweep < 0])
    if maximum <= 0:
        return
    maximum = math.nextafter(maximum, 0.)
    distances = {min(config['biarc_error_mm'] * 2**attempt / 2, maximum)
                 for attempt in range(config['maximum_fit_passes'])}
    distances.add(maximum/2)
    for distance in sorted(distances):
        shifted = []
        for segment, center, radius, start, sweep in arcs:
            if center is None:
                tangent = _unit(_sub(segment['p1'], segment['p0']))
                normal = (tangent[1], -tangent[0])
                value = dict(kind='line', p0=list(_add(segment['p0'], _mul(normal, distance))),
                             p1=list(_add(segment['p1'], _mul(normal, distance))))
                shifted.append((value, None, 0., 0., 0.))
            else:
                sign = math.copysign(1., sweep)
                value = dict(kind='arc')
                for key, angle in (('p0', start), ('pm', start+sweep/2), ('p1', start+sweep)):
                    normal = (sign*math.cos(angle), sign*math.sin(angle))
                    value[key] = list(_add(segment[key], _mul(normal, distance)))
                shifted.append((value, center, radius+sign*distance, start, sweep))
        yield [arc[0] for arc in shifted], shifted


def _bounded_candidates(loop, config, radius, limit, shared, *, material=None, other_points=(),
                        local_tool=None, material_radius=None, prefer_material=False):
    """Lazily source-certify proposals; no actual-output verdict is consumed."""
    if __package__:
        from .cad_verify_v4_contours import minimum_radius
    else:
        from cad_verify_v4_contours import minimum_radius
    from shapely.geometry import Polygon
    anchor = tuple(loop['segments'][0]['p0'])
    raw = [_sub(segment['p0'], anchor) for segment in loop['segments']]
    contacts = _loop_contacts(raw, {_sub(point, anchor) for point in shared})
    if material is not None:
        from shapely.affinity import translate
        material = translate(material, xoff=-anchor[0], yoff=-anchor[1])
    other_points = [_sub(point, anchor) for point in other_points]
    if local_tool is None:
        local_tool = config['minimum_radius_mm']
    def curvature(constrained):
        try:
            points, tangents, evaluate = _curvature_proposal(
                raw, config, radius, contacts, material=material, other_points=other_points,
                tool_radius=material_radius, enforce_material=constrained)
            for divisor in (1, 2, 4):
                yield _approximate(points, tangents, tangents, [],
                    config['biarc_error_mm']/divisor, MAX_SEGMENTS, evaluate)
        except ValueError as exc:
            if not str(exc).startswith('contour_'):
                raise
    def proposals():
        if prefer_material:
            # Independent RMS choices on opposite thin walls can force huge
            # compensating deformations. Fit their original shared midlines first.
            yield from curvature(True)
        yield from _circle_proposals(raw, radius, contacts, loop['role'], config['biarc_error_mm'])
        smooth = {'sample_spacing_pixels': config['sample_spacing_mm']}
        for attempt in range(config['maximum_fit_passes']):
            try:
                points, tangents, evaluate = _smooth(raw, smooth, config['smoothing_rms_mm']*2**attempt)
                yield _approximate(points, tangents, tangents, [],
                    config['biarc_error_mm'], MAX_SEGMENTS, evaluate)
            except ValueError as exc:
                if not str(exc).startswith('contour_'):
                    raise
        yield from curvature(False)
        if not prefer_material:
            yield from curvature(True)
    # The exact arc check needs the physical shrink reserve, not the larger
    # construction slack used while proposing/approximating a spline.
    admitted_radius = (radius * config['minimum_radius_mm'] /
                       (config['minimum_radius_mm'] + config['biarc_error_mm']) +
                       config['biarc_error_mm']/128)
    def ordered_candidates():
        # Preserve a compliant zero-offset fit before introducing additional
        # deformation. Cache finite geometric proposals, never admission trust.
        bases = []
        for segments, arcs in proposals():
            if _simple_candidate(raw, arcs, config['biarc_error_mm'],
                                 contacts=contacts, role=loop['role']):
                bases.append((segments, arcs))
                yield segments, arcs
        for segments, arcs in bases:
            shifted = _parallel_candidates(segments, arcs, config, admitted_radius, limit)
            next(shifted)  # Zero displacement was already considered.
            yield from shifted
    for segments, arcs in ordered_candidates():
        try:
            if not _simple_candidate(raw, arcs, config['biarc_error_mm'],
                                     contacts=contacts, role=loop['role']):
                continue
            if minimum_radius({'loops': [dict(loop, segments=segments)]}) < admitted_radius:
                continue
            source_error = _error(raw+[raw[0]], arcs, min(limit, config['biarc_error_mm']))
            if source_error > limit:
                continue
            points, error = _flatten(arcs, config['biarc_error_mm']/128)
            local_region = Polygon(points)
            if (loop['role'] == 'outer' and local_tool > 0 and not _material_reachable(
                    local_region, error, local_tool, config['biarc_error_mm'])):
                continue
            placed = [{key: (list(_add(value, anchor)) if key in ('p0', 'pm', 'p1') else value)
                       for key, value in segment.items()} for segment in segments]
            start = min(range(len(placed)), key=lambda i: placed[i]['p0'])
            region = Polygon([_add(point, anchor) for point in points])
            yield dict(loop, segments=placed[start:]+placed[:start]), region, error, source_error
        except ValueError as exc:
            if not str(exc).startswith('contour_'):
                raise


def _layout_compatible(loop, region, error, previous, regions, tolerance):
    ancestors = set()
    parent = loop.get('parent')
    while parent is not None:
        ancestors.add(parent)
        parent = previous[parent].get('parent')
    for i, (other, other_error) in enumerate(regions):
        if (not other.contains(region) if i in ancestors else not other.disjoint(region)):
            return False
        if region.boundary.distance(other.boundary) <= error + other_error + tolerance/2:
            return False
    return True


def _material_layout_compatible(source, placed, regions, tool, tolerance, future_voids,
                                *, all_components=False):
    """Prune material walls as soon as their loops are placed.

    Only an outer and its immediate holes form one material component.
    Same-parent holes bound material between them; child islands and distinct
    foreground pieces do not. Unplaced holes could remove inaccessible material,
    so partial-component rejection subtracts their original-source deviation
    envelopes, except collars that strict layout separation guarantees remain
    material beside already-placed boundaries. This prevents future-hole
    envelopes hiding an existing thin wall. Every candidate hole is contained
    by its envelope because its original-boundary enclosure has already passed.
    Completed components use no exclusion, even with nested islands unplaced.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    if tool <= 0:
        return True
    if all_components:
        components = [i for i, loop in enumerate(placed) if loop['role'] == 'outer']
    else:
        last = len(placed)-1
        components = [last if placed[last]['role'] == 'outer' else placed[last]['parent']]
    for index in components:
        children = [j for j, loop in enumerate(source)
                    if loop['role'] == 'hole' and loop.get('parent') == index]
        current = [j for j in children if j < len(placed)]
        pending = [j for j in children if j >= len(placed)]
        outer, outer_error = regions[index]
        enclosure = max([outer_error]+[regions[j][1] for j in current])
        if pending and not all_components:
            # A new hole can only create a material wall with its outer or a
            # same-parent hole. Avoid disk measurements for clearly wide gaps.
            last = len(placed)-1
            if placed[last]['role'] == 'hole' and all(
                    regions[last][0].boundary.distance(regions[j][0].boundary) >=
                    2*tool+enclosure+regions[j][1] for j in [index]+current if j != last):
                continue
        component = Polygon(outer.exterior.coords,
                            [regions[j][0].exterior.coords for j in current])
        possible_void = unary_union([future_voids[j] for j in pending]) if pending else None
        if pending:
            # Future hole chords must stay farther than tolerance/2 (plus
            # both chord enclosures) from each already-placed boundary.
            # This smaller collar therefore cannot become a future void.
            protected = unary_union([regions[j][0].boundary.buffer(tolerance/4)
                                     for j in [index]+current])
            possible_void = possible_void.difference(protected)
        if not _material_reachable(component, enclosure, tool, tolerance,
                                   possible_void=possible_void):
            return False
    return True


def _fit_source_bounded(source, config):
    """Fit in nominal mm; reserve for the one subsequent canonical scaling.

    For nominal source error e <= E and height H, fitted height is at most
    H+2E; the radius reserve therefore survives the final uniform scaling.
    Source error uses the actual complete-layout scale, not a worst-case
    enlargement reserve. Final original-mask/arc certificates remain the
    publication gate; proposal tolerances never relax acceptance.
    """
    from shapely.geometry import Polygon
    ys = [segment['p0'][1] for loop in source for segment in loop['segments']]
    height = max(ys) - min(ys)
    maximum = config['maximum_error_mm']
    limit = maximum
    radius = (config['minimum_radius_mm'] + config['biarc_error_mm']) * (1 + 2 * limit / height)
    # The actual tool has no biarc/curvature construction slack. Local
    # rejection must allow the largest possible final enlargement; proposals
    # reserve only for the opposite, worst final shrink, plus fine chord error.
    local_tool = config['minimum_radius_mm'] * max(0., 1-2*limit/height)
    material_radius = (config['minimum_radius_mm'] * (1+2*limit/height) +
                       config['biarc_error_mm']/128)
    occurrences = {}
    for loop in source:
        for segment in loop['segments']:
            point = tuple(segment['p0'])
            occurrences[point] = occurrences.get(point, 0) + 1
    shared = {point for point, count in occurrences.items() if count > 1}
    rings = [[tuple(segment['p0']) for segment in loop['segments']] for loop in source]
    material = _material_region(source, rings)
    from shapely.geometry import LineString
    boundaries = [LineString(ring+[ring[0]]) for ring in rings]
    prefer_material = [False] * len(source)
    for i, loop in enumerate(source):
        if loop['role'] != 'hole':
            continue
        parent = loop['parent']
        peers = [parent] + [j for j in range(i) if source[j]['role'] == 'hole'
                            and source[j].get('parent') == parent]
        for j in peers:
            if boundaries[i].distance(boundaries[j]) < 2*material_radius:
                prefer_material[i] = prefer_material[j] = True
    source_samples = [_samples(ring+[ring[0]], config['sample_spacing_mm'])[0][:-1]
                      for ring in rings]
    future_voids = [Polygon(ring).buffer(limit) if loop['role'] == 'hole' else None
                   for loop, ring in zip(source, rings)]
    root_indices = [i for i, loop in enumerate(source) if loop.get('parent') is None]
    generators = [iter(_bounded_candidates(loop, config, radius, limit, shared,
        material=material, local_tool=local_tool, material_radius=material_radius,
        prefer_material=prefer_material[i],
        other_points=[point for j, samples in enumerate(source_samples)
            if j != i for point in samples])) for i, loop in enumerate(source)]
    cached = [[] for _ in source]
    exhausted = [False] * len(source)
    positions = [0] * len(source)
    result, regions, errors, total, attempts = [], [], [], 0, 0
    reason = 'no_certified_source_radius_topology_layout'
    if __package__:
        from .cad_verify_v4_contours import _geometry_bounds
    else:
        from cad_verify_v4_contours import _geometry_bounds
    while True:
        if len(result) == len(source):
            bounds = _geometry_bounds(result)
            final_scale = height / (bounds[3] - bounds[2])
            candidate = _material_region(result, [list(region.exterior.coords)
                                                 for region, _ in regions])
            enclosure = max(error for _, error in regions)
            inner, outer = candidate.buffer(-enclosure), candidate.buffer(enclosure)
            source_iou = material.intersection(inner).area / material.union(outer).area
            if (max(errors) * final_scale <= maximum and
                    source_iou >= config['minimum_iou'] and
                    _material_reachable(candidate, enclosure,
                        config['minimum_radius_mm']/final_scale, config['biarc_error_mm'])):
                return result
            total -= len(result.pop()['segments'])
            regions.pop()
            errors.pop()
        depth = len(result)
        chosen = None
        while True:
            position = positions[depth]
            if position == len(cached[depth]) and not exhausted[depth]:
                try:
                    cached[depth].append(next(generators[depth]))
                except StopIteration:
                    exhausted[depth] = True
                except ValueError as exc:
                    if not str(exc).startswith('contour_'):
                        raise
                    reason, exhausted[depth] = str(exc), True
            if position == len(cached[depth]):
                break
            loop, region, error, source_error = cached[depth][position]
            positions[depth] += 1
            attempts += 1
            if attempts > MAX_SEGMENTS:
                raise ValueError('contour_layout_search_budget_exhausted')
            if (total + len(loop['segments']) <= MAX_SEGMENTS and
                    _layout_compatible(loop, region, error, result, regions, config['biarc_error_mm'])):
                proposed = result+[loop]
                proposed_regions = regions+[(region, error)]
                roots_fixed = max(root_indices) < len(proposed)
                tool = local_tool
                if roots_fixed:
                    # Descendants are strictly contained and cannot extend
                    # extrema: all roots fix the one final canonical scale.
                    root_bounds = _geometry_bounds([proposed[i] for i in root_indices])
                    tool = config['minimum_radius_mm'] * (root_bounds[3]-root_bounds[2])/height
                if not _material_layout_compatible(source, proposed, proposed_regions, tool,
                        config['biarc_error_mm'], future_voids, all_components=roots_fixed):
                    continue
                chosen = (loop, region, error, source_error)
                break
        if chosen is None:
            if not result:
                raise ValueError('contour_source_bounded_fit_unattainable:' + reason)
            total -= len(result.pop()['segments'])
            regions.pop()
            errors.pop()
            continue
        loop, region, error, source_error = chosen
        result.append(loop)
        regions.append((region, error))
        errors.append(source_error)
        total += len(loop['segments'])
        if len(result) < len(source):
            positions[len(result)] = 0


def fit_loops(source,config):
    """Dispatch the explicitly declared frozen source-fit policy."""
    if config['method'] == 'source_bounded_biarc_v2':
        return _fit_source_bounded(source, config)
    limit=config['maximum_error_pixels'];result=[];total=0
    for loop in source:
        anchor=tuple(loop['segments'][0]['p0'])
        # Integer source-local coordinates make padding irrelevant to FITPACK
        # conditioning, knot decisions and the approximation itself.
        raw=[_sub(segment['p0'],anchor) for segment in loop['segments']]
        incoming,outgoing,corners=_tangents(raw,config['tangent_span_pixels'],config['corner_angle_degrees'])
        passes=1 if corners else config['maximum_fit_passes']
        for attempt in range(passes):
            if corners:
                points=raw;fit_limit=limit;evaluate=None
            else:
                rms=config['smoothing_rms_pixels']/(2**attempt)
                points,incoming,evaluate=_smooth(raw,config,rms);outgoing=incoming
                fit_limit=config['biarc_error_pixels']
            segments,arcs=_approximate(points,incoming,outgoing,corners,fit_limit,MAX_SEGMENTS-total,evaluate)
            if _error(raw+[raw[0]],arcs,limit)<=limit:
                break
        else:
            raise ValueError('contour_curve_fit_source_error_budget_exceeded')
        total+=len(segments)
        segments=[{key:(list(_add(value,anchor)) if key in ('p0','pm','p1') else value)
                   for key,value in segment.items()} for segment in segments]
        start=min(range(len(segments)),key=lambda i:segments[i]['p0'])
        segments=segments[start:]+segments[:start]
        result.append(dict(loop,segments=segments))
    return result
