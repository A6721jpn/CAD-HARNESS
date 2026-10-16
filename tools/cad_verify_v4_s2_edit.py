"""S2 immutable STEP direct editing with OCCT per-face offset/reconnection.

Host admission is CAD-free. Native feature persistence contains data only and
rebuilds from embedded immutable BREP, never from recovered STEP history.
Replacement is deliberately bounded to planar supports; curved per-face offsets
use the actual OCCT offset engine. Kernel failure is an error, never a fallback.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile


def _modules():
    if __package__:
        from . import cad_verify_v4_inputs as inputs, cad_verify_v4_plans as plans, cad_verify_v4_ledger as ledger
    else:
        import cad_verify_v4_inputs as inputs
        import cad_verify_v4_plans as plans
        import cad_verify_v4_ledger as ledger
    return inputs, plans, ledger


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _selector(record, selection):
    if record.get('profile') != 'c-s2':
        raise ValueError('selector_profile_mismatch')
    matches = [f for f in record['faces'] if f['signature'] == selection['signature']]
    if len(matches) != 1 or matches[0]['ambiguous']:
        raise ValueError('selector_signature_not_unique')
    face = matches[0]
    if face['id'] != selection['face_id'] or face['adjacent_face_ids'] != selection['adjacent_face_ids']:
        raise ValueError('selector_identity_or_adjacency_mismatch')
    if selection['adjacent_face_ids'] != sorted(selection['adjacent_face_ids'], key=lambda s: int(s[4:])):
        raise ValueError('selector_adjacency_order')
    if face['id'] in selection['adjacent_face_ids']:
        raise ValueError('selector_self_adjacency')
    return face


def validate_plan(plan, manifest_path=None, prepared=None):
    inputs, plans, ledger = _modules()
    schema = ledger.read_json(plans.SCHEMAS / 's2-capability-plan.schema.json')
    plans._check(plan, schema, schema, 's2-plan')
    plan = copy.deepcopy(plan)
    operation = plan['operation']
    if operation['kind'] == 'offset' and operation['distance_mm'] == 0:
        raise ValueError('zero_offset')
    dependencies = [(plan['asset_id'], plan['source_sha256'], plan['selection'])]
    if operation['kind'] == 'replace':
        if operation['replacement_asset_id'] == plan['asset_id']:
            raise ValueError('replacement_requires_distinct_asset')
        dependencies.append((operation['replacement_asset_id'], operation['replacement_source_sha256'], operation['replacement_selection']))
    for _, _, selection in dependencies:
        adjacency = selection['adjacent_face_ids']
        if adjacency != sorted(adjacency,key=lambda s:int(s[4:])) or selection['face_id'] in adjacency:
            raise ValueError('selector_adjacency_order_or_self')
    if manifest_path is not None:
        manifest = inputs.load_manifest(manifest_path)
        if manifest['profile'] != 'c-s2':
            raise ValueError('manifest_profile_mismatch')
        for asset_id, digest, selection in dependencies:
            asset = inputs.resolve_asset(manifest_path, asset_id, 'step')
            if asset['record']['role'] != 'reference' or asset['digest'] != digest:
                raise ValueError('immutable_reference_binding')
        if prepared is not None:
            prepared = inputs.verify_prepared(prepared, manifest_path)
    if prepared is not None:
        if prepared['profile'] != 'c-s2':
            raise ValueError('prepared_profile_mismatch')
        for asset_id, digest, selection in dependencies:
            record = prepared['assets'].get(asset_id)
            if record is None or record.get('source_sha256') != digest:
                raise ValueError('prepared_source_binding')
            _selector(record, selection)
    return plan


def _solid(shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError('single_valid_solid_required')
    solid = shape.Solids[0]
    if any(len(getattr(shape,name)) != len(getattr(solid,name)) for name in ('Faces','Edges','Vertexes')):
        raise ValueError('loose_geometry_outside_solid')
    shells = solid.Shells
    if not shells or any(not shell.isClosed() for shell in shells) or sum(len(shell.Faces) for shell in shells)!=len(solid.Faces):
        raise ValueError('solid_requires_closed_complete_boundary')
    return shape


def _from_brep(text):
    import Part
    shape = Part.Shape()
    shape.importBrepFromString(text, False)
    return shape


def _bounds(shape):
    b = shape.BoundBox
    return [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax]


def _native_selector(shape, record, selection):
    """Recompute all geometric signatures and actual shared-edge adjacency."""
    import Part
    inputs, _, _ = _modules()
    precision = record['signature_precision_mm']
    if type(precision) not in (int, float) or not math.isfinite(precision) or precision <= 0:
        raise ValueError('signature_precision_invalid')
    signatures = []
    for face in shape.Faces:
        normal = None
        try:
            u0, u1, v0, v1 = face.ParameterRange
            vector = face.normalAt((u0+u1)/2, (v0+v1)/2)
            if vector.Length > 0 and math.isfinite(vector.Length):
                normal = [vector.x/vector.Length, vector.y/vector.Length, vector.z/vector.Length]
        except (RuntimeError, ValueError, AttributeError, OverflowError):
            pass
        signature_data = {'surface_type': type(face.Surface).__name__,
            'area_quantized': round(face.Area/(precision*precision)),
            'center_quantized': [round(v/precision) for v in face.CenterOfMass],
            'bounds_quantized': [round(v/precision) for v in _bounds(face)],
            'normal_quantized': None if normal is None else [0.0 if round(v,12)==0 else round(v,12) for v in normal]}
        signatures.append(inputs.canonical_sha(signature_data))
    matches = [i for i, signature in enumerate(signatures) if signature == selection['signature']]
    if len(matches) != 1 or 'Face'+str(matches[0]+1) != selection['face_id']:
        raise ValueError('native_signature_not_unique_or_stale')
    index = matches[0]
    face = shape.Faces[index]
    adjacency = ['Face'+str(i+1) for i, other in enumerate(shape.Faces) if i != index and
                 any(a.isSame(b) for a in face.Edges for b in other.Edges)]
    if adjacency != selection['adjacent_face_ids']:
        raise ValueError('native_adjacency_mismatch')
    _selector(record, selection)
    return index


class _Bridge:
    """Private native-only OCCT/FreeCAD interchange, preserving face order."""
    def __init__(self, directory):
        self.path = str(Path(directory)/'shape.brep')

    def to_occ(self, shape):
        from OCC.Core.TopoDS import TopoDS_Shape
        from OCC.Core.BRep import BRep_Builder
        from OCC.Core.BRepTools import breptools
        shape.exportBrep(self.path)
        result = TopoDS_Shape()
        if not breptools.Read(result, self.path, BRep_Builder()):
            raise ValueError('occt_brep_read')
        return result

    def to_freecad(self, shape):
        import Part
        from OCC.Core.BRepTools import breptools
        if not breptools.Write(shape, self.path):
            raise ValueError('occt_brep_write')
        result = Part.Shape()
        result.importBrep(self.path)
        return result


def _occ_faces(shape):
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE
    from OCC.Core.TopoDS import topods
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    result = []
    while explorer.More():
        result.append(topods.Face(explorer.Current()))
        explorer.Next()
    return result


def _offset(occ, face, distance, tolerance):
    from OCC.Core.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin
    from OCC.Core.GeomAbs import GeomAbs_Intersection
    builder = BRepOffset_MakeOffset()
    builder.Initialize(occ, 0., tolerance, BRepOffset_Skin, True, False, GeomAbs_Intersection, False, False)
    builder.SetOffsetOnFace(face, distance)
    builder.MakeOffsetShape()
    if not builder.IsDone():
        raise ValueError('per_face_offset_failed:'+str(builder.Error()))
    return builder


def _overlap(a, b, tolerance, dimension=2):
    """Geometric coincidence only; deliberately no nearest-face attribution."""
    if dimension == 2:
        common = a.common(b)
        return common.Area if not common.isNull() else 0.
    common = a.common(b)
    return common.Length if not common.isNull() else 0.


def _correspondence(original, output, tolerance):
    result = {'faces': [], 'edges': [], 'unmapped_output_faces': [], 'unmapped_output_edges': []}
    for name, source, target, dimension in [('faces', original.Faces, output.Faces, 2), ('edges', original.Edges, output.Edges, 1)]:
        prefix = 'Face' if dimension == 2 else 'Edge'
        mapped = set()
        rows = []
        inverse = {}
        for i, a in enumerate(source, 1):
            links = []
            for j, b in enumerate(target, 1):
                measure = _overlap(a, b, tolerance, dimension)
                if measure > (tolerance*tolerance if dimension == 2 else tolerance):
                    links.append({'output_id': prefix+str(j), 'coincident_measure': measure})
                    mapped.add(j)
                    inverse[j] = inverse.get(j, 0)+1
            rows.append({'source_id': prefix+str(i), 'outputs': links, 'relation': 'unmapped' if not links else 'split' if len(links)>1 else 'coincident_subset'})
        for row in rows:
            if any(inverse[int(link['output_id'][len(prefix):])] > 1 for link in row['outputs']):
                row['relation'] = 'merged_or_ambiguous'
        result[name] = rows
        result['unmapped_output_'+name] = [prefix+str(i) for i in range(1, len(target)+1) if i not in mapped]
    return result

def _area_error_bound(face, tolerance):
    """Construction-only mm² bound: boundary strips, vertex disks, roundoff."""
    scale_mm2 = max(face.Area, face.BoundBox.DiagonalLength**2)
    return (2*face.Length*tolerance + math.pi*len(face.Vertexes)*tolerance**2
            + 64*math.ulp(scale_mm2))


def _occ_map(shape, kind):
    from OCC.Core.TopExp import topexp
    from OCC.Core.TopTools import TopTools_IndexedMapOfShape
    result = TopTools_IndexedMapOfShape()
    topexp.MapShapes(shape,kind,result)
    return result


def _occ_list(shapes):
    from OCC.Core.TopTools import TopTools_ListIteratorOfListOfShape
    iterator = TopTools_ListIteratorOfListOfShape(shapes)
    result = []
    while iterator.More():
        result.append(iterator.Value())
        iterator.Next()
    return result


def _kernel_history(original_occ, final_occ, builder, clip=None, replacement_operand=None):
    """Exact OCCT topology identities, including offset->Boolean history chains.

    Empty history is explicitly unknown/deleted; no geometric or nearest-match
    inference is promoted to an OCCT provenance link.
    """
    from OCC.Core.TopAbs import TopAbs_FACE,TopAbs_EDGE
    from OCC.Core.TopTools import TopTools_ListOfShape
    result = {'faces':[],'edges':[],'replacement_operand_faces':[],
              'convention':'exact OCCT IsSame topology identity; offset LastImage/Modified/Generated chained through reconnect Modified/Generated'}
    for name, kind, prefix in [('faces',TopAbs_FACE,'Face'),('edges',TopAbs_EDGE,'Edge')]:
        source = _occ_map(original_occ,kind)
        target = _occ_map(final_occ,kind)
        image = builder.OffsetFacesFromShapes() if name=='faces' else builder.OffsetEdgesFromShapes()
        def output_links(candidates):
            links = {}
            for candidate,path in candidates:
                descendants = [(candidate,path)]
                if clip is not None:
                    descendants += [(s,path+' -> Common.Modified') for s in _occ_list(clip.Modified(candidate))]
                    descendants += [(s,path+' -> Common.Generated') for s in _occ_list(clip.Generated(candidate))]
                for descendant,method in descendants:
                    parts = _occ_map(descendant,kind)
                    for j in range(1,parts.Size()+1):
                        index = target.FindIndex(parts.FindKey(j))
                        if index:
                            links.setdefault(index,set()).add(method)
            return [{'output_id':prefix+str(index),'history_paths':sorted(methods)}
                    for index,methods in sorted(links.items())]
        rows = []
        for i in range(1,source.Size()+1):
            native = source.FindKey(i)
            candidates = [(native,'surviving_source_identity')]
            if image.HasImage(native):
                images = TopTools_ListOfShape()
                image.LastImage(native,images)
                candidates += [(s,'Offset.LastImage') for s in _occ_list(images)]
            candidates += [(s,'Offset.Modified') for s in _occ_list(builder.Modified(native))]
            candidates += [(s,'Offset.Generated') for s in _occ_list(builder.Generated(native))]
            links = output_links(candidates)
            rows.append({'source_id':prefix+str(i),'outputs':links,
                         'relation':'unknown_or_deleted' if not links else 'split' if len(links)>1 else 'kernel_link'})
        inverse = {}
        for row in rows:
            for link in row['outputs']:
                inverse[link['output_id']] = inverse.get(link['output_id'],0)+1
        for row in rows:
            if any(inverse[link['output_id']]>1 for link in row['outputs']):
                row['relation']='merged_or_shared_history'
        result[name]=rows
        result['unmapped_output_'+name]=[prefix+str(i) for i in range(1,target.Size()+1)
                                         if prefix+str(i) not in inverse]
        if name=='faces' and replacement_operand is not None:
            operand = _occ_map(replacement_operand,kind)
            for i in range(1,operand.Size()+1):
                native = operand.FindKey(i)
                result['replacement_operand_faces'].append({'operand_face_id':'Face'+str(i),
                    'outputs':output_links([(native,'replacement_halfspace_support_identity')])})
    return result


def _construct(original, record, plan, replacement=None, replacement_record=None, distance=None, replacement_shift=0.):
    import FreeCAD as App
    import Part
    tolerance = plan['kernel_tolerance_mm']
    index = _native_selector(original, record, plan['selection'])
    _solid(original)
    operation = plan['operation']
    with tempfile.TemporaryDirectory(prefix='cad-s2-occt-') as directory:
        bridge = _Bridge(directory)
        occ = bridge.to_occ(original)
        faces = _occ_faces(occ)
        # Verify topology interchange itself rather than assuming FaceN order.
        if len(faces) != len(original.Faces):
            raise ValueError('occt_face_interchange_count')
        selected = bridge.to_freecad(faces[index])
        if _overlap(selected, original.Faces[index], tolerance) < original.Faces[index].Area - _area_error_bound(original.Faces[index],tolerance):
            raise ValueError('occt_face_interchange_identity')
        replacement_outputs = []
        clip, halfspace = None, None
        if operation['kind'] == 'offset':
            amount = operation['distance_mm'] if distance is None else distance
            if not math.isfinite(amount) or amount == 0 or abs(amount)>1000:
                raise ValueError('offset_distance_invalid')
            builder = _offset(occ, faces[index], amount, tolerance)
            final_occ = builder.Shape()
            output = _solid(bridge.to_freecad(final_occ))
            kernel = 'BRepOffset_MakeOffset.SetOffsetOnFace'
        else:
            rindex = _native_selector(replacement, replacement_record, operation['replacement_selection'])
            old_face = original.Faces[index]
            replacement_face = replacement.Faces[rindex].copy()
            if not isinstance(old_face.Surface, Part.Plane) or not isinstance(replacement_face.Surface, Part.Plane):
                raise ValueError('replacement_requires_planar_supports')
            old_normal = old_face.normalAt(*[sum(old_face.ParameterRange[i:i+2])/2 for i in (0,2)])
            replacement_normal = replacement_face.normalAt(*[sum(replacement_face.ParameterRange[i:i+2])/2 for i in (0,2)])
            if abs(old_normal.dot(replacement_normal)) < .1:
                raise ValueError('replacement_orientation_infeasible')
            if replacement_normal.dot(old_normal)<0:
                replacement_normal = -replacement_normal
            if not math.isfinite(replacement_shift) or abs(replacement_shift)>1000:
                raise ValueError('replacement_shift_invalid')
            replacement_face.translate(replacement_normal*replacement_shift)
            builder = _offset(occ, faces[index], operation['extension_limit_mm'], tolerance)
            from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeHalfSpace
            from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
            from OCC.Core.gp import gp_Pnt,gp_Dir,gp_Pln
            # MakeHalfSpace on a finite trimmed face can retain its floating
            # patch without clipping the source solid. Intersect against the
            # actual unrestricted support, then verify finite asset coverage.
            center = replacement_face.CenterOfMass
            support = BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(*center),gp_Dir(*replacement_normal)))
            if not support.IsDone():
                raise ValueError('replacement_support_construction_failed')
            replacement_occ = support.Face()
            inside = center - replacement_normal
            halfspace = BRepPrimAPI_MakeHalfSpace(replacement_occ,gp_Pnt(*inside)).Solid()
            clip = BRepAlgoAPI_Common(builder.Shape(), halfspace)
            clip.SetFuzzyValue(tolerance)
            clip.Build()
            if not clip.IsDone():
                raise ValueError('replacement_reconnect_failed')
            final_occ = clip.Shape()
            output = _solid(bridge.to_freecad(final_occ))
            for i, face in enumerate(output.Faces, 1):
                if isinstance(face.Surface, Part.Plane):
                    u0,u1,v0,v1 = face.ParameterRange
                    normal = face.normalAt((u0+u1)/2,(v0+v1)/2)
                    gap = abs((face.CenterOfMass-replacement_face.CenterOfMass).dot(replacement_normal))
                    if abs(abs(normal.dot(replacement_normal))-1)<1e-8 and gap<=tolerance:
                        covered = _overlap(face, replacement_face, tolerance)
                        if covered < face.Area-_area_error_bound(face,tolerance):
                            raise ValueError('replacement_patch_not_covered')
                        replacement_outputs.append('Face'+str(i))
            if not replacement_outputs:
                raise ValueError('replacement_outside_extension_or_no_patch')
            # Replacement must not silently trim unrelated source faces.
            allowed = set(plan['selection']['adjacent_face_ids']+[plan['selection']['face_id']])
            for i, face in enumerate(original.Faces, 1):
                if 'Face'+str(i) not in allowed:
                    covered = sum(_overlap(face, other, tolerance) for other in output.Faces)
                    if abs(covered-face.Area)>_area_error_bound(face,tolerance):
                        raise ValueError('replacement_changes_nonadjacent_face')
            kernel = 'BRepOffset_MakeOffset extension + BRepPrimAPI_MakeHalfSpace + BRepAlgoAPI_Common reconnect'
        removed = original.cut(output).Volume
        added = output.cut(original).Volume
        if removed+added <= tolerance**3:
            raise ValueError('direct_edit_no_change')
        report = {'schema': 'cad-harness.direct-edit-report.v4c', 'profile': 'c-s2',
            'source_sha256': plan['source_sha256'], 'selection': copy.deepcopy(plan['selection']),
            'operation': copy.deepcopy(operation), 'kernel': kernel, 'reconnect': 'extend_intersect_trim',
            'signed_distance_mm': amount if operation['kind']=='offset' else None,
            'replacement_shift_mm': replacement_shift if operation['kind']=='replace' else None,
            'replacement_output_face_ids': replacement_outputs,
            'original_volume_mm3': original.Volume, 'output_volume_mm3': output.Volume,
            'removed_volume_mm3': removed, 'added_volume_mm3': added,
            'original_faces': len(original.Faces), 'output_faces': len(output.Faces),
            'correspondence': _correspondence(original,output,tolerance),
            'kernel_history': _kernel_history(occ,final_occ,builder,clip,halfspace),
            'construction_area_error_convention':'mm²: 2*perimeter_mm*tolerance_mm + pi*vertex_count*tolerance_mm² + 64*ulp(max(area_mm²,diagonal_mm²)); not judge acceptance',
            'correspondence_convention': 'exact coincident subsets only; changed/displaced support is unmapped, not guessed',
            'valid': output.isValid(), 'solids': len(output.Solids)}
        return output, report


class DirectEditProxy:
    TOKEN = 'cad-harness.direct-edit-proxy.v4c:1'

    def dumps(self):
        return self.TOKEN

    def loads(self, value):
        if value != self.TOKEN:
            raise ValueError('direct_edit_proxy_version')

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
            if _sha(obj.OriginalBrep) != obj.OriginalBrepDigest or _sha(obj.FactsData)!=obj.FactsDigest or _sha(obj.PlanData)!=obj.PlanDigest:
                raise ValueError('frozen_source_or_plan_digest')
            plan = validate_plan(json.loads(obj.PlanData))
            original = _from_brep(obj.OriginalBrep)
            replacement, replacement_record = None, None
            if plan['operation']['kind']=='replace':
                if _sha(obj.ReplacementBrep)!=obj.ReplacementBrepDigest or _sha(obj.ReplacementFactsData)!=obj.ReplacementFactsDigest:
                    raise ValueError('frozen_replacement_digest')
                replacement = _from_brep(obj.ReplacementBrep)
                replacement_record = json.loads(obj.ReplacementFactsData)
            shape, report = _construct(original,json.loads(obj.FactsData),plan,replacement,replacement_record,
                                       float(obj.OffsetDistance),float(obj.ReplacementShift))
            obj.Shape = shape
            obj.OperationReport = _json(report)
            obj.BuildStatus = 'ok'
        except Exception as exc:
            obj.Shape = Part.Shape()
            obj.OperationReport = ''
            obj.BuildStatus = 'failed:'+str(exc)
            raise


def _property(obj, kind, name, value, frozen=False):
    obj.addProperty(kind,name,'S2')
    setattr(obj,name,value)
    if frozen:
        obj.setEditorMode(name,1)


def _load_source(manifest_path, asset_id):
    import Part
    inputs, _, _ = _modules()
    asset = inputs.resolve_asset(manifest_path,asset_id,'step')
    shape = Part.Shape()
    shape.read(str(asset['path']))
    # Re-resolve after import: a concurrent replacement cannot be embedded silently.
    if inputs.resolve_asset(manifest_path,asset_id,'step')['digest'] != asset['digest']:
        raise ValueError('source_changed_during_build')
    return shape


def build_plan(doc, plan, manifest_path, prepared):
    plan = validate_plan(plan,manifest_path,prepared)
    original = _solid(_load_source(manifest_path,plan['asset_id']))
    record = prepared['assets'][plan['asset_id']]
    _native_selector(original,record,plan['selection'])
    body = doc.addObject('PartDesign::Body','Model')
    feature = body.newObject('PartDesign::FeaturePython','DirectEdit')
    try:
        for name, value in [('PlanData',_json(plan)),('FactsData',_json(record)),('OriginalBrep',original.exportBrepToString())]:
            _property(feature,'App::PropertyString',name,value,True)
            _property(feature,'App::PropertyString',{'PlanData':'PlanDigest','FactsData':'FactsDigest','OriginalBrep':'OriginalBrepDigest'}[name],_sha(value),True)
        operation = plan['operation']
        if operation['kind']=='replace':
            replacement = _load_source(manifest_path,operation['replacement_asset_id'])
            for name,value in [('ReplacementBrep',replacement.exportBrepToString()),('ReplacementFactsData',_json(prepared['assets'][operation['replacement_asset_id']]))]:
                _property(feature,'App::PropertyString',name,value,True)
                _property(feature,'App::PropertyString',{'ReplacementBrep':'ReplacementBrepDigest','ReplacementFactsData':'ReplacementFactsDigest'}[name],_sha(value),True)
        _property(feature,'App::PropertyFloat','OffsetDistance',operation.get('distance_mm',0.))
        _property(feature,'App::PropertyFloat','ReplacementShift',0.)
        feature.setEditorMode('ReplacementShift' if operation['kind']=='offset' else 'OffsetDistance',2)
        _property(feature,'App::PropertyString','BuildStatus','new',True)
        _property(feature,'App::PropertyString','OperationReport','',True)
        feature.Proxy = DirectEditProxy()
        body.Tip = feature
        doc.recompute()
        if feature.BuildStatus != 'ok':
            raise ValueError(feature.BuildStatus)
        _solid(feature.Shape)
        check_model_inputs(body,plan,prepared,manifest_path)
        return body
    except Exception:
        doc.removeObject(feature.Name)
        doc.removeObject(body.Name)
        raise


def check_model_inputs(body, plan, prepared, manifest_path):
    plan = validate_plan(plan,manifest_path,prepared)
    feature = body.Tip
    if feature is None or type(feature.Proxy) is not DirectEditProxy or len(body.Group)!=1:
        raise ValueError('direct_edit_body_or_proxy')
    if feature.PlanData != _json(plan) or feature.FactsData != _json(prepared['assets'][plan['asset_id']]):
        raise ValueError('restored_plan_or_facts_mismatch')
    if float(feature.OffsetDistance)!=plan['operation'].get('distance_mm',0.) or float(feature.ReplacementShift)!=0.:
        raise ValueError('restored_operative_parameters_mismatch')
    original = _load_source(manifest_path,plan['asset_id'])
    if feature.OriginalBrep != original.exportBrepToString():
        raise ValueError('embedded_original_mismatch')
    if _sha(feature.OriginalBrep)!=feature.OriginalBrepDigest or _sha(feature.PlanData)!=feature.PlanDigest or _sha(feature.FactsData)!=feature.FactsDigest:
        raise ValueError('embedded_source_digest_mismatch')
    _native_selector(_from_brep(feature.OriginalBrep),prepared['assets'][plan['asset_id']],plan['selection'])
    if plan['operation']['kind']=='replace':
        operation = plan['operation']
        replacement = _load_source(manifest_path,operation['replacement_asset_id'])
        if feature.ReplacementBrep!=replacement.exportBrepToString() or feature.ReplacementFactsData!=_json(prepared['assets'][operation['replacement_asset_id']]):
            raise ValueError('embedded_replacement_mismatch')
        if _sha(feature.ReplacementBrep)!=feature.ReplacementBrepDigest or _sha(feature.ReplacementFactsData)!=feature.ReplacementFactsDigest:
            raise ValueError('embedded_replacement_digest_mismatch')
    if feature.BuildStatus!='ok':
        raise ValueError('direct_edit_not_recomputed')
    _solid(feature.Shape)
    return True


def operation_report(body):
    feature = body.Tip
    if feature is None or type(feature.Proxy) is not DirectEditProxy or feature.BuildStatus!='ok':
        raise ValueError('direct_edit_report_unavailable')
    return json.loads(feature.OperationReport)


def operative_evidence(doc, body):
    """Exercise actual parameter/recompute/restore; always restore in finally."""
    feature = body.Tip
    if type(feature.Proxy) is not DirectEditProxy:
        raise ValueError('direct_edit_proxy_required')
    plan = json.loads(feature.PlanData)
    original = _solid(feature.Shape).copy()
    parameter = 'OffsetDistance' if plan['operation']['kind']=='offset' else 'ReplacementShift'
    before = float(getattr(feature,parameter))
    step = max(plan['kernel_tolerance_mm']*100,abs(before)*.01,.001)
    setattr(feature,parameter,before+step)
    try:
        doc.recompute()
        if feature.BuildStatus!='ok':
            raise ValueError('operative_perturbation_failed')
        altered = _solid(feature.Shape).copy()
        difference = original.cut(altered).Volume+altered.cut(original).Volume
        if difference<=plan['kernel_tolerance_mm']**3:
            raise ValueError('direct_edit_parameter_inert')
        evidence = {'feature':feature.Name,'parameter':parameter,'before':before,'after':before+step,
                    'operative':True,'symmetric_difference_mm3':difference,'restored':False,
                    'artifact_probe':dict(kind='scalar',object=feature.Name,property=parameter,
                                          delta=(before+step)-before)}
    finally:
        setattr(feature,parameter,before)
        feature.touch()
        doc.recompute()
        if feature.BuildStatus!='ok':
            raise ValueError('operative_restore_failed')
        restored = _solid(feature.Shape)
        error = original.cut(restored).Volume+restored.cut(original).Volume
        if error>max(plan['kernel_tolerance_mm']**3,original.Volume*1e-10):
            raise ValueError('operative_restore_geometry_mismatch')
    evidence['restored']=True
    evidence['restore_symmetric_difference_mm3']=error
    return [evidence]
