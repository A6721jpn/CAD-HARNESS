"""Independent S2 BREP judges; host-safe admission, no editor/compiler imports.

Continuous thickness certificates deliberately cover only convex, line-edged
planar material within the full declared ray-domain prism, with projected
opposed-face coverage. Unsupported geometry retains sampled observations. Preserved
ROIs compare material occupancy in mm^3, not maximum surface displacement.
"""
import copy
import math
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/schemas'


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '') + name)


class Unknown(ValueError):
    """Unavailable or uncertified evidence, never acceptance."""


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _xyz(p):
    return [float(p.x), float(p.y), float(p.z)]


def _unit(v):
    length = math.hypot(*v)
    if length == 0:
        raise ValueError('zero_direction')
    return [x/length for x in v]


def _box_valid(b):
    if any(b[i] >= b[i+1] for i in (0, 2, 4)):
        raise ValueError('region_requires_positive_extents')


def validate_card(card):
    """Strict data-only admission; every acceptance quantity is explicit."""
    plans = _module('cad_verify_v4_plans')
    schema = _module('cad_verify_v4_ledger').read_json(SCHEMAS / 's2-judge-card.schema.json')
    plans._check(card, schema, schema, 's2-judge-card')
    ids = [c['id'] for c in card['criteria']]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_criterion_id')
    for c in card['criteria']:
        for field in ('region_mm',):
            if field in c:
                _box_valid(c[field])
        if c['metric'] == 'thickness_distribution':
            d, u, v = (_unit(x) for x in (c['direction'], c['domain']['u'], c['domain']['v']))
            if any(abs(_dot(a, b)) > 1e-12 for a, b in ((d,u),(d,v),(u,v))):
                raise ValueError('domain_requires_orthogonal_direction_and_basis')
            if any(abs(math.hypot(*x)-1) > 1e-12 for x in (c['direction'],c['domain']['u'],c['domain']['v'])):
                raise ValueError('domain_basis_and_direction_require_unit_vectors')
            if c['expected_range_mm'][0] > c['expected_range_mm'][1]:
                raise ValueError('thickness_range_reversed')
            if math.prod(c['samples']) > 100000:
                raise ValueError('thickness_sample_count_excessive')
            for side in c['opposed_sets'].values():
                _box_valid(side['output_region_mm'])
            if set(c['opposed_sets']['a']['source_face_ids']) & set(c['opposed_sets']['b']['source_face_ids']):
                raise ValueError('opposed_source_sets_overlap')
        if c['metric'] == 'unchanged_dimension' and c['definition'] == 'landmark_distance':
            if math.dist(*c['landmarks_mm']) == 0:
                raise ValueError('landmarks_must_be_distinct')
    return copy.deepcopy(card)


def _bounds(shape):
    b = shape.BoundBox
    return [float(b.XMin),float(b.XMax),float(b.YMin),float(b.YMax),float(b.ZMin),float(b.ZMax)]


def _trimmed_bounds(shape):
    """Measure finite trimmed geometry, not its possibly extended support.

    _bounds deliberately retains the existing STEP face-fact/signature convention.
    """
    b = shape.optimalBoundingBox(False,False)
    if not b.isValid():
        raise Unknown('trimmed_geometry_has_invalid_bounds')
    return [float(b.XMin),float(b.XMax),float(b.YMin),float(b.YMax),float(b.ZMin),float(b.ZMax)]


def _roi(bounds):
    import FreeCAD as App
    import Part
    return Part.makeBox(bounds[1]-bounds[0],bounds[3]-bounds[2],bounds[5]-bounds[4],
                        App.Vector(bounds[0],bounds[2],bounds[4]))


def _source(plan, manifest_path, prepared):
    """Reload exact admitted STEP; reconstruct identities without candidate reports."""
    import Part
    inputs = _module('cad_verify_v4_inputs')
    ledger = _module('cad_verify_v4_ledger')
    manifest = inputs.load_manifest(manifest_path)
    if manifest.get('profile') != 'c-s2' or prepared.get('profile') != 'c-s2':
        raise Unknown('source_profile_mismatch')
    _module('cad_verify_v4_plans').validate_document(prepared,'prepared',profile='c-s2')
    path = inputs.guarded_path(manifest_path)
    manifest_hash = ledger.file_sha(path)
    if prepared.get('source_manifest_sha256') != manifest_hash:
        raise Unknown('prepared_manifest_hash_mismatch')
    resolved = inputs.resolve_asset(path, plan['asset_id'], 'step')
    record = resolved['record']
    facts = prepared['assets'][plan['asset_id']]
    inputs._validate_facts(facts)
    if record.get('role') != 'reference' or resolved['digest'] != plan['source_sha256'] or facts.get('source_sha256') != resolved['digest']:
        raise Unknown('source_hash_or_role_mismatch')
    if facts.get('units') != 'mm' or facts.get('frame',{}).get('axis_transform') != 'identity':
        raise Unknown('source_frame_not_fixed_mm_identity')
    provenance = facts.get('provenance',{})
    for field in ('manifest_sha256_before','manifest_sha256_after'):
        if provenance.get(field) != manifest_hash:
            raise Unknown('source_manifest_provenance_mismatch')
    for field in ('asset_sha256_before','asset_sha256_after'):
        if provenance.get(field) != resolved['digest']:
            raise Unknown('source_asset_provenance_mismatch')
    shape = Part.Shape()
    shape.read(str(resolved['path']))
    if shape.isNull() or not shape.isValid():
        raise Unknown('original_step_invalid')
    # Independent exact identity checks use actual area/COM/bounds/surface/adjacency,
    # not the selected FaceN or compiler-provided correspondence alone.
    rows = facts.get('faces',[])
    if len(rows) != len(shape.Faces):
        raise Unknown('source_face_count_mismatch')
    for i, face in enumerate(shape.Faces):
        row = rows[i]
        if row.get('id') != 'Face'+str(i+1) or row.get('surface_type') != type(face.Surface).__name__:
            raise Unknown('source_face_identity_mismatch')
        numeric = [abs(row['area_mm2']-face.Area), math.dist(row['center_mm'],_xyz(face.CenterOfMass))]
        numeric.extend(abs(a-b) for a,b in zip(row['bounds_mm'],_bounds(face)))
        if max(numeric) > 1e-8 * max(1.,face.Area):
            raise Unknown('source_face_geometry_mismatch')
        adjacent = ['Face'+str(j+1) for j,other in enumerate(shape.Faces) if i != j and
                    any(e.isSame(f) for e in face.Edges for f in other.Edges)]
        if row.get('adjacent_face_ids') != adjacent:
            raise Unknown('source_face_adjacency_mismatch')
    if inputs.resolve_asset(path,plan['asset_id'],'step')['digest'] != resolved['digest'] or ledger.file_sha(path) != manifest_hash:
        raise Unknown('source_changed_during_judgement')
    return shape, facts, dict(asset_id=plan['asset_id'],source_sha256=resolved['digest'],
                              manifest_sha256=manifest_hash,frame='identity_source_axes',source_units='mm')


def _epsilon(shapes, budget):
    # An empty Boolean result can be a non-null compound. Its void BoundBox
    # stores DBL_MAX sentinels, not physical coordinates or numerical error.
    shapes = tuple(s for s in shapes if not s.isNull() and (s.Faces or s.Edges or s.Vertexes))
    if not shapes:
        raise Unknown('numerical_uncertainty_requires_nonempty_geometry')
    if any(not s.BoundBox.isValid() for s in shapes):
        raise Unknown('nonempty_geometry_has_invalid_bounds')
    scale = max(1.,*(abs(x) for shape in shapes for x in _bounds(shape)))
    actual = max(float(s.getTolerance(1)) for s in shapes) + 128*math.ulp(scale)
    if actual > budget:
        raise Unknown('native_tolerance_exceeds_declared_numerical_uncertainty')
    return actual


def _maximum_status(value, limit, error):
    return 'PASS' if value+error <= limit else 'FAIL' if max(0.,value-error) > limit else 'UNVERIFIED'


def _range_status(low, high, expected, tolerance, error):
    a,b = expected[0]-tolerance, expected[1]+tolerance
    if low+error < a or high-error > b:
        return 'FAIL'
    if low-error >= a and high+error <= b:
        return 'PASS'
    return 'UNVERIFIED'


def _count(shape, criterion, eps):
    if criterion['scope'] == 'full':
        return len(shape.Faces)
    clip = _roi(criterion['region_mm'])
    count = 0
    for face in shape.Faces:
        area = face.common(clip).Area
        if 0 < area <= eps*eps:
            raise Unknown('region_face_intersection_numerically_unresolved')
        count += area > eps*eps
    return count


def _dimension(source, output, c, eps):
    if c['definition'] == 'axis_extent':
        i = {'X':0,'Y':2,'Z':4}[c['axis']]
        a,b = _trimmed_bounds(source),_trimmed_bounds(output)
        before, after = a[i+1]-a[i], b[i+1]-b[i]
        evidence = dict(definition='source_axis_extent',axis=c['axis'],coverage='global_axis_extent',
                        bounds_method='optimal_trimmed_brep_without_triangulation_or_shape_tolerance')
    else:
        original, candidate = [],[]
        # Spatial correspondence is explicit and ambiguity is not nearest guessing.
        for point in c['landmarks_mm']:
            originals = [v.Point for v in source.Vertexes if math.dist(point,_xyz(v.Point)) <= eps]
            candidates = [v.Point for v in output.Vertexes if math.dist(point,_xyz(v.Point)) <= c['search_radius_mm']]
            if len(originals) != 1 or len(candidates) != 1:
                raise Unknown('landmark_spatial_correspondence_missing_or_ambiguous')
            original.append(_xyz(originals[0]));candidate.append(_xyz(candidates[0]))
        before,after = math.dist(*original),math.dist(*candidate)
        evidence = dict(definition='source_vertex_landmark_distance',source_landmarks_mm=original,
                        output_landmarks_mm=candidate,correspondence='unique_fixed_frame_search_ball',coverage='declared_landmarks_only')
    delta = abs(after-before)
    return _maximum_status(delta,c['tolerance_mm'],4*eps),dict(source_mm=before,output_mm=after,absolute_difference_mm=delta),4*eps,evidence


def _normal(face, point=None):
    if point is None:
        u0,u1,v0,v1 = face.ParameterRange
        u,v = (u0+u1)/2,(v0+v1)/2
    else:
        u,v = face.Surface.parameter(point)
    return _unit(_xyz(face.normalAt(u,v)))


def _output_faces(shape, side, eps):
    clip = _roi(side['output_region_mm'])
    return [patch for face in shape.Faces for patch in face.common(clip).Faces if patch.Area > eps*eps]


def _original_faces(shape, facts, side):
    rows = {f['id']:f for f in facts['faces']}
    faces = []
    for name in side['source_face_ids']:
        if name not in rows or rows[name].get('ambiguous'):
            raise Unknown('opposed_source_face_missing_or_ambiguous')
        faces.append(shape.Faces[int(name[4:])-1])
    return faces


def _point(domain, x, y):
    return [o+x*u+y*v for o,u,v in zip(domain['origin_mm'],domain['u'],domain['v'])]


def _ray(shape, groups, p, direction, length, eps):
    import FreeCAD as App
    import Part
    start = App.Vector(*(x-length*d for x,d in zip(p,direction)))
    end = App.Vector(*(x+length*d for x,d in zip(p,direction)))
    line = Part.makeLine(start,end)
    results = []
    for side, sign in zip(groups,(-1,1)):
        hits = []
        for face in side:
            section = face.section(line)
            if section.Edges:
                return None,'ray_overlaps_opposed_face'
            for vertex in section.Vertexes:
                t = _dot([x-y for x,y in zip(_xyz(vertex.Point),p)],direction)
                normal = _dot(_normal(face,vertex.Point),direction)
                if sign*normal <= 1e-10:
                    return None,'wrong_opposed_face_orientation'
                if not any(abs(t-old) <= eps for old in hits):
                    hits.append(t)
        if len(hits) != 1:
            return None,'missing_opposed_hit' if not hits else 'multiple_opposed_hits'
        results.append(hits[0])
    if results[1]-results[0] <= eps:
        return None,'wrong_opposed_order_or_zero_chord'
    material = shape.common(line)
    if len(material.Edges) != 1:
        return None,'missing_or_multiple_material_intervals'
    ends = sorted(_dot([x-y for x,y in zip(_xyz(v.Point),p)],direction) for v in material.Edges[0].Vertexes)
    if len(ends) != 2 or any(abs(a-b) > 2*eps for a,b in zip(ends,results)):
        return None,'opposed_faces_not_actual_material_endpoints'
    return results[1]-results[0],None


def _projected_polygon(face, domain, direction):
    from shapely.geometry import Polygon
    if type(face.Surface).__name__ != 'Plane' or any(type(e.Curve).__name__ != 'Line' for e in face.Edges):
        raise Unknown('continuous_requires_planar_line_edged_opposed_faces')
    # Projection along the ray onto the fixed domain frame (u,v orthogonal to d).
    loops = []
    for wire in face.Wires:
        points = [_xyz(v.Point) for v in wire.OrderedVertexes]
        loops.append([(_dot([x-o for x,o in zip(p,domain['origin_mm'])],domain['u']),
                       _dot([x-o for x,o in zip(p,domain['origin_mm'])],domain['v'])) for p in points])
    outer = next((i for i,w in enumerate(face.Wires) if w.isSame(face.OuterWire)),None)
    if outer is None:
        raise Unknown('projected_outer_wire_unavailable')
    poly = Polygon(loops[outer],[loop for i,loop in enumerate(loops) if i != outer])
    if not poly.is_valid or poly.area == 0:
        raise Unknown('opposed_projection_invalid')
    return poly


def _convex_planar(shape, eps):
    if len(shape.Solids) != 1 or not shape.isValid() or not shape.isClosed():
        raise Unknown('continuous_requires_one_valid_closed_solid')
    vertices = [_xyz(v.Point) for v in shape.Vertexes]
    for face in shape.Faces:
        if type(face.Surface).__name__ != 'Plane' or any(type(e.Curve).__name__ != 'Line' for e in face.Edges):
            raise Unknown('continuous_domain_geometry_not_planar_line_edged')
        normal = _normal(face)
        center = _xyz(face.CenterOfMass)
        if any(_dot([x-y for x,y in zip(p,center)],normal) > eps for p in vertices):
            raise Unknown('continuous_domain_solid_not_convex_cavity_or_local_groove_possible')


def _continuous(shape, groups, c, eps, budget):
    """Support-plane convexity + exact polygon coverage certifies all ray chords."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    import FreeCAD as App
    import Part
    domain, d = c['domain'],c['direction']
    length = c['ray_length_mm']
    corners = [_point(domain,x,y) for x,y in ((0,0),(domain['size_mm'][0],0),
               tuple(domain['size_mm']),(0,domain['size_mm'][1]),(0,0))]
    base = [App.Vector(*(x-length*axis for x,axis in zip(p,d))) for p in corners]
    prism = Part.Face(Part.makePolygon(base)).extrude(App.Vector(*(2*length*axis for axis in d)))
    # Only boundary patches inside the full ray prism participate in coverage.
    # Remote circular holes/trim edges must not invalidate a planar local patch;
    # conversely, holes inside the prism remain real trim edges/material voids.
    groups = [[patch for face in faces for patch in face.common(prism).Faces
               if patch.Area > eps*eps] for faces in groups]
    local = shape.common(prism)
    if local.isNull():
        raise Unknown('continuous_domain_has_no_material')
    patches = [face for faces in groups for face in faces]
    eps = max(eps,_epsilon([shape,local,prism]+patches,budget))
    _convex_planar(local,eps)
    rectangle = box(0,0,*domain['size_mm'])
    sides = []
    conditioning = 1.
    for faces,sign in zip(groups,(-1,1)):
        usable = [f for f in faces if sign*_dot(_normal(f),d) > 1e-10]
        if not usable:
            raise Unknown('continuous_opposed_support_missing')
        # Multiple coplanar patches are supported. Differing planes imply piecewise
        # extrema whose arrangement is not certified here; preserve uncertainty.
        normal = _normal(usable[0]); center = _xyz(usable[0].CenterOfMass)
        nd = _dot(normal,d)
        if any(math.dist(_normal(f),normal)>1e-10 or abs(_dot([x-y for x,y in zip(_xyz(f.CenterOfMass),center)],normal))>eps for f in usable):
            raise Unknown('continuous_piecewise_opposed_planes_not_certified')
        projection = unary_union([_projected_polygon(f,domain,d) for f in usable])
        if not projection.covers(rectangle):
            raise Unknown('continuous_projected_domain_coverage_incomplete')
        conditioning = max(conditioning,1/abs(nd))
        sides.append((normal,center,nd))
    values = []
    for x,y in ((0,0),(domain['size_mm'][0],0),(0,domain['size_mm'][1]),tuple(domain['size_mm'])):
        p = _point(domain,x,y)
        ts = [_dot([a-b for a,b in zip(center,p)],normal)/nd for normal,center,nd in sides]
        values.append(ts[1]-ts[0])
    if min(values) <= 2*eps*conditioning:
        raise Unknown('continuous_chord_not_resolved_positive')
    return min(values),max(values),4*eps*conditioning,dict(method='convex_planar_support_planes_affine_corner_extrema',
        coverage='entire_declared_rectangle',domain_area_mm2=math.prod(domain['size_mm']),
        no_interior_cavity_certificate='all_actual_faces_in_full_ray_domain_prism_support_convex_material',
        opposed_projection_coverage='complete_polygon_union',global_extrema_scope='declared_domain_only')


def _thickness(source, output, facts, c, eps, budget):
    if output.isNull():
        return 'FAIL',None,0,dict(units='mm',coverage='no_output_geometry',reason='output_shape_null')
    domain,d = c['domain'],c['direction']
    # The finite ray must cover the entire actual bbox in the measurement direction.
    origin_projection = _dot(domain['origin_mm'],d)
    for shape in (source,output):
        b = _bounds(shape)
        projections = [_dot([x,y,z],d)-origin_projection for x in (b[0],b[1]) for y in (b[2],b[3]) for z in (b[4],b[5])]
        if max(abs(t) for t in projections)+eps >= c['ray_length_mm']:
            raise Unknown('ray_length_does_not_cover_actual_shape')
    source_groups = [_original_faces(source,facts,c['opposed_sets'][side]) for side in ('a','b')]
    output_groups = [_output_faces(output,c['opposed_sets'][side],eps) for side in ('a','b')]
    measured_shapes = [source,output] + [face for group in source_groups+output_groups for face in group]
    eps = max(eps,_epsilon(measured_shapes,budget))
    values,before,problems = [],[],[]
    nx,ny = c['samples']
    for i in range(nx):
        for j in range(ny):
            # Cell centres avoid trim-boundary duplicated hits; corners are covered
            # only by the analytic certificate, not upgraded from this sampling.
            p = _point(domain,(i+.5)*domain['size_mm'][0]/nx,(j+.5)*domain['size_mm'][1]/ny)
            old,source_problem = _ray(source,source_groups,p,d,c['ray_length_mm'],eps)
            if source_problem:
                raise Unknown('source_opposition_not_valid:'+source_problem)
            value,problem = _ray(output,output_groups,p,d,c['ray_length_mm'],eps)
            before.append(old)
            if problem:
                problems.append(dict(point_mm=p,reason=problem))
            else:
                values.append(value)
    evidence = dict(units='mm',convention=c['convention'],scope=c['scope'],domain=domain,direction=d,
                    sampled_count=nx*ny,valid_sample_count=len(values),ray_problems=problems,
                    output_selector='actual_face_patches_clipped_to_fixed_spatial_region',source_opposition='independently_loaded_original_faces')
    measured = dict(sampled_min_mm=min(values) if values else None,sampled_max_mm=max(values) if values else None,
                    source_sampled_min_mm=min(before),source_sampled_max_mm=max(before),
                    global_min_mm=None,global_max_mm=None)
    if problems:
        return 'FAIL',measured,2*eps,evidence
    sampled_status = _range_status(min(values),max(values),c['expected_range_mm'],c['tolerance_mm'],2*eps)
    if sampled_status == 'FAIL':
        return 'FAIL',measured,2*eps,evidence
    if c['scope'] == 'sampled':
        evidence.update(coverage='declared_cell_centres_only',continuous_certificate=False)
        return sampled_status,measured,2*eps,evidence
    try:
        # Original opposing patches must cover the whole domain as well, excluding
        # a plausible selector that only matches a tiny unaffected local decoy.
        _continuous(source,source_groups,c,eps,budget)
        low,high,error,certificate = _continuous(output,output_groups,c,eps,budget)
    except Unknown as exc:
        evidence.update(coverage='sampled_only_global_unknown',continuous_certificate=False,reason=str(exc))
        return 'UNVERIFIED',measured,None,evidence
    measured.update(global_min_mm=low,global_max_mm=high)
    evidence.update(certificate,continuous_certificate=True)
    return _range_status(low,high,c['expected_range_mm'],c['tolerance_mm'],error),measured,error,evidence


def _check(c, status, measured, target, tolerance, uncertainty, evidence):
    return dict(id=c['id'],metric=c['metric'],status=status,measured=measured,target=target,
                tolerance=tolerance,uncertainty=uncertainty,evidence=evidence)


def _target(c):
    metric = c['metric']
    if metric == 'solid_valid':
        return dict(valid=True,closed=True,solids=c['expected_solids'],positive_volume=True),0
    if metric == 'face_count':
        return {key:c[key] for key in ('scope','relation','expected_count','expected_delta','correspondence','region_mm','region_rule') if key in c},0
    if metric == 'unchanged_dimension':
        return dict(source_to_output_absolute_difference_mm=0,definition=c['definition']),c['tolerance_mm']
    if metric == 'preserved_region':
        return dict(maximum_symmetric_difference_mm3=c['maximum_symmetric_difference_mm3']),c['maximum_symmetric_difference_mm3']
    if metric == 'thickness_distribution':
        return dict(range_mm=c['expected_range_mm'],scope=c['scope'],convention=c['convention']),c['tolerance_mm']
    return {k:v for k,v in c.items() if k not in ('id','metric')},dict(mm=c['maximum_bounds_difference_mm'],mm3=c['maximum_volume_difference_mm3'])


def judge(plan, manifest_path, prepared, body_or_shape, card, **context):
    """One card judges actual native BREP or independent STEP-imported BREP."""
    card = validate_card(card)
    shape = getattr(body_or_shape,'Shape',body_or_shape)
    checks = []
    source_error = None
    try:
        source,facts,provenance = _source(plan,manifest_path,prepared)
        eps = _epsilon((source,shape),card['numerical_uncertainty_mm'])
    except (Unknown,ValueError,KeyError,TypeError,AttributeError,OSError,RuntimeError) as exc:
        source_error = str(exc)
    for c in card['criteria']:
        target,tolerance = _target(c)
        units = {'solid_valid':dict(volume='mm3',counts='integer'),'face_count':'integer_faces',
                 'preserved_region':'mm3','native_roundtrip':dict(bounds='mm',volume='mm3')}.get(c['metric'],'mm')
        evidence = dict(units=units,numerical_uncertainty_budget_mm=card['numerical_uncertainty_mm'])
        measured,error = None,None
        try:
            if source_error:
                raise Unknown(source_error)
            evidence.update(provenance,numerical_native_error_mm=eps)
            metric = c['metric']
            if metric == 'solid_valid':
                null = shape.isNull()
                measured = (dict(valid=False,closed=False,solids=0,volume_mm3=0.,null=True) if null else
                            dict(valid=shape.isValid(),closed=shape.isClosed(),solids=len(shape.Solids),volume_mm3=float(shape.Volume),null=False))
                passed = not measured['null'] and measured['valid'] and measured['closed'] and measured['solids']==c['expected_solids'] and measured['volume_mm3']>0
                status,error = ('PASS' if passed else 'FAIL'),0
                evidence.update(coverage='entire_actual_brep',units=dict(volume='mm3',counts='integer'),method='native_isValid_isClosed_actual_solid_count')
            elif metric == 'face_count':
                old,new = _count(source,c,eps),_count(shape,c,eps)
                actual = new if c['relation']=='equal' else new-old
                expected = c.get('expected_count',c.get('expected_delta'))
                measured = dict(source_count=old,output_count=new,delta=new-old)
                status,error = ('PASS' if actual == expected else 'FAIL'),0
                evidence.update(units='integer_faces',coverage=c['scope'],correspondence='spatial_fixed_frame_not_compiler_provenance')
            elif metric == 'unchanged_dimension':
                status,measured,error,extra = _dimension(source,shape,c,eps)
                evidence.update(extra)
            elif metric == 'preserved_region':
                clip = _roi(c['region_mm'])
                a,b = source.common(clip),shape.common(clip)
                if a.Volume <= eps**3:
                    raise Unknown('preserved_roi_has_no_resolved_source_material')
                removed,inserted = a.cut(b),b.cut(a)
                local_eps = max(eps,_epsilon((a,b,clip,removed,inserted),card['numerical_uncertainty_mm']))
                bound = local_eps*(a.Area+b.Area+clip.Area)+128*math.ulp(max(1.,a.Volume,b.Volume))
                error = c['volume_uncertainty_mm3']
                if bound > error:
                    raise Unknown('roi_native_error_exceeds_declared_volume_uncertainty')
                lost,added = float(removed.Volume),float(inserted.Volume)
                measured = dict(source_roi_volume_mm3=float(a.Volume),output_roi_volume_mm3=float(b.Volume),lost_material_mm3=lost,added_material_mm3=added,symmetric_difference_mm3=lost+added)
                status = _maximum_status(lost+added,c['maximum_symmetric_difference_mm3'],error)
                evidence.update(units='mm3',coverage='entire_declared_roi_material_occupancy',region_mm=c['region_mm'],
                    method='two_direction_native_boolean_symmetric_volume_difference',claim='bounded_material_volume_change_not_surface_deviation',computed_numerical_bound_mm3=bound)
            elif metric == 'thickness_distribution':
                status,measured,error,extra = _thickness(source,shape,facts,c,eps,card['numerical_uncertainty_mm'])
                evidence.update(extra)
            else:
                ev = context.get('native_evidence')
                keys = ('fcstd_reopened','step_reopened','editable','bounds_difference_mm','volume_difference_mm3')
                if not isinstance(ev,dict) or any(k not in ev for k in keys):
                    raise Unknown('native_reopen_evidence_missing')
                if any(type(ev[k]) is not bool for k in keys[:3]):
                    raise Unknown('native_reopen_flags_invalid')
                if any(type(ev[k]) not in (int,float) or not math.isfinite(ev[k]) or ev[k]<0 for k in keys[3:]):
                    raise Unknown('native_reopen_measurements_invalid')
                measured = {k:ev[k] for k in keys}
                error = dict(mm=2*eps,mm3=eps*(source.Area+shape.Area)+128*math.ulp(max(1.,shape.Volume)))
                states = [_maximum_status(ev['bounds_difference_mm'],c['maximum_bounds_difference_mm'],error['mm']),
                          _maximum_status(ev['volume_difference_mm3'],c['maximum_volume_difference_mm3'],error['mm3'])]
                if not ev['fcstd_reopened'] or not ev['step_reopened'] or (c['require_editable'] and not ev['editable']):
                    status = 'FAIL'
                else:
                    status = 'FAIL' if 'FAIL' in states else 'UNVERIFIED' if 'UNVERIFIED' in states else 'PASS'
                evidence.update(units=dict(bounds='mm',volume='mm3'),coverage='actual_shared_worker_native_and_step_reopen',
                    source='independent_reopen_evidence_not_operation_report')
        except (Unknown,ValueError,KeyError,TypeError,IndexError,AttributeError,RuntimeError,OSError) as exc:
            status = 'UNVERIFIED'
            evidence.update(reason=str(exc),coverage='uncertified')
        checks.append(_check(c,status,measured,target,tolerance,error,evidence))
    status = 'FAIL' if any(c['status']=='FAIL' for c in checks) else 'UNVERIFIED' if any(c['status']=='UNVERIFIED' for c in checks) else 'PASS'
    return dict(schema='cad-harness.judgement.v4c',profile='c-s2',status=status,checks=checks)
