"""Mechanical gold portability judge; private numeric evidence never printed.

Original geometry functions/cards are unchanged. Additional whole-boundary
0.005mm and native SW operational editing are distinct columns, NOT a v4 score.
"""
import copy
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base
from tools.sw_m1_distance import whole_distance as boundary_distance
from tools.sw_m1_build import construction
from tools.sw_m1_inputs import private_path


def load_shape(path):
    import Part
    s=Part.Shape();s.read(str(path))
    if s.isNull() or not s.isValid() or len(s.Solids)!=1 or s.Volume<=0:
        raise ValueError('candidate_not_valid_single_solid')
    return s


def original_geometry(shape,g):
    if g.get('schema')=='cad-harness.verify-gold.v3':
        from tools import cad_verify_probe as p
    else:
        from tools import cad_spec_probe as p
    checks=p.Checks(g['case_id'])
    measured=p.measure_shape(shape,g,checks)
    return {'passed':all(checks.predicates.values()),'predicates':checks.predicates,
            'measurements':measured,'checks':checks.records}


def independent_reference(g):
    import FreeCAD as App
    import Part
    if 'parameters' not in g:
        from tools.cad_spec import build_native,validate_spec
        s=construction(g)
        spec={k:copy.deepcopy(v) for k,v in s.items() if k in ('regions','steps','center_xy','pockets','holes','finish')}
        spec.update(schema='cad-harness.build-spec.v1',family=s['profile'],units='mm',frame='world')
        for q in spec.get('pockets',[]):q.pop('sharp',None)
        doc=App.newDocument('M1_Independent_Reference')
        try:return build_native(doc,validate_spec(spec)).Shape.copy()
        finally:App.closeDocument(doc.Name)
    p=g['parameters'];kind=p['profile']
    def box(b):return Part.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],App.Vector(b[0],b[2],b[4]))
    def cylinder(r,z):return Part.makeCylinder(r,z[1]-z[0],App.Vector(0,0,z[0]))
    def pocket(shape,q):
        b=q['bounds'];lo=q['top_z']-q['depth']
        return shape.cut(box(b+[lo,q['top_z']]))
    if kind=='roller':
        s=cylinder(p['radius'],[0,p['length']]).cut(cylinder(p['bore_radius'],[0,p['length']]))
        ring=cylinder(p['radius'],p['groove_z']).cut(cylinder(p['radius']-p['groove_depth'],p['groove_z']))
        s=s.cut(ring)
    elif kind=='taper':
        wires=[]
        for z,wh in ((0,p['bottom']),(p['height'],p['top'])):
            w,d=wh;points=[App.Vector(x,y,z) for x,y in ((-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2),(-w/2,-d/2))]
            wires.append(Part.makePolygon(points))
        s=Part.makeLoft(wires,True,True)
    elif kind=='elbow':
        outer=Part.Wire(Part.makeCircle(p['outer_radius'],App.Vector(0,0,0),App.Vector(1,0,0)))
        inner=Part.Wire(Part.makeCircle(p['inner_radius'],App.Vector(0,0,0),App.Vector(1,0,0)))
        s=Part.Face(outer).cut(Part.Face(inner)).revolve(App.Vector(0,p['path_radius'],0),App.Vector(0,0,1),90)
    elif kind=='ribbed_box':
        b,t=p['bbox'],p['wall'];inner=[b[0]+t,b[1]-t,b[2]+t,b[3]-t]
        s=pocket(box(b),dict(bounds=inner,top_z=b[5],depth=b[5]-t))
        x0,x1=inner[:2];y=-p['rib_thickness']/2
        wire=Part.makePolygon([App.Vector(x0,y,t),App.Vector(x1,y,t),App.Vector(x1,y,p['rib_top']),App.Vector(x0,y,t)])
        rib=Part.Face(wire).extrude(App.Vector(0,p['rib_thickness'],0));s=s.fuse(rib)
    elif kind=='flange':
        s=cylinder(p['radius'],[0,p['thickness']]).cut(cylinder(p['bore_radius'],[0,p['thickness']]))
        for i in range(p['pcd_count']):
            a=2*math.pi*i/p['pcd_count'];c=App.Vector(p['pcd_radius']*math.cos(a),p['pcd_radius']*math.sin(a),0)
            s=s.cut(Part.makeCylinder(p['hole_radius'],p['thickness'],c))
        for q in p.get('pockets',[]):s=pocket(s,q)
    elif kind=='rect_prism':
        b=p['bbox'];s=box(b)
        for q in p.get('pockets',[]):s=pocket(s,q)
        for h in p.get('holes',[]):
            lo,hi=h.get('z',b[4:6]);x,y=h['center_xy']
            s=s.cut(Part.makeCylinder(h['diameter']/2,hi-lo,App.Vector(x,y,lo)))
        f=p.get('finish')
        if f:
            selected=[]
            for edge in s.Edges:
                pts=[v.Point for v in edge.Vertexes]
                if len(pts)==2 and all(abs(pt.z-b[5])<1e-7 for pt in pts) and any(
                    all(abs(getattr(pt,axis)-side)<1e-7 for pt in pts)
                    for axis,side in (('x',b[0]),('x',b[1]),('y',b[2]),('y',b[3]))):selected.append(edge)
            if len(selected)!=4:raise ValueError('independent_reference_finish_selection')
            s=s.makeFillet(f['size'],selected) if f['kind']=='fillet' else s.makeChamfer(f['size'],selected)
    else:raise ValueError('reference_profile_unsupported')
    s=s.removeSplitter()
    if not s.isValid() or len(s.Solids)!=1:raise ValueError('reference_invalid')
    return s


def judge(job_path):
    import FreeCAD as App
    import Part
    t=time.perf_counter()
    job=json.loads(private_path(job_path).read_text(encoding='utf-8'))
    out=private_path(job['out'])
    detail={'status':'FAIL','paid_model_calls':0,'at':base.utc()}
    public={'sequence':job['sequence'],'group':job['group'],'route':job['route'],'profile':job['profile'],
            'geometry':'UNVERIFIED','extra_distance_0_005':'UNVERIFIED','G2':'NOT_REQUIRED_BY_ORIGINAL_CARD',
            'SW_editability':'UNVERIFIED','original_behavioural_score':'NOT_RUN_NO_LLM',
            'original_FreeCAD_native_history':'NOT_APPLICABLE_TO_SW_NATIVE',
            'negative_control':'NOT_RUN','reason':None}
    try:
        if list(App.Version())[:3]!=['1','1','4'] or App.GuiUp:raise RuntimeError('pinned_headless_FreeCAD_required')
        g=job['gold']
        if base.digest(job['gold_path'])!=job['gold_sha256']:raise RuntimeError('original_gold_binding')
        if g.get('schema')=='cad-harness.verify-gold.v3':
            from tools.cad_verify_v3_probe import load_gold
        else:
            from tools.cad_spec_probe import load_gold
        validated=load_gold(job['gold_path'])
        if validated!=g:raise RuntimeError('copied_gold_changed')
        shape=load_shape(out/'reopened.step')
        geom=original_geometry(shape,g)
        public['geometry']='PASS' if geom['passed'] else 'FAIL'
        # Only fixed predicate GROUPS leave the private folder, never sub-checks
        # such as wall coordinates, expected/actual values or case identifiers.
        public['failed_predicate_groups']=[k for k,v in geom['predicates'].items() if not v]
        detail.update(original_geometry=geom,FreeCAD=list(App.Version()),OCCT=Part.OCC_VERSION)
        ref=independent_reference(g)
        ref.exportStep(str(out/'reference.step'))
        reference_geometry=original_geometry(ref,g)
        detail['reference_original_geometry']=reference_geometry
        if not reference_geometry['passed']:
            raise RuntimeError('independent_reference_does_not_satisfy_original_gold')
        distance=boundary_distance(ref,shape,.005)
        detail['whole_boundary_distance']=distance
        public['extra_distance_0_005']=distance['status']
        if distance['status']=='UNVERIFIED':public['distance_reason']='NATIVE_OFFSET_CERTIFICATE_UNAVAILABLE'
        com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
        if com.get('edit',{}).get('performed'):
            edited=load_shape(out/'edited.step');restored=load_shape(out/'restored.step')
            changed=shape.cut(edited).Volume+edited.cut(shape).Volume
            uncertainty=max(shape.getTolerance(1),edited.getTolerance(1))*(shape.Area+edited.Area)
            restore=boundary_distance(shape,restored,.005,refinements=1)
            detail['SW_operational_edit']={'changed_symmetric_volume_mm3':changed,'uncertainty_mm3':uncertainty,
                'restore':restore,'restored_original_geometry':original_geometry(restored,g),
                'scope':'ONE consumed native SW parameter; NOT complete original FreeCAD role certification'}
            if changed>uncertainty and restore['status']=='PASS' and detail['SW_operational_edit']['restored_original_geometry']['passed'] and com['original_native_unchanged']:
                public['SW_editability']='PASS_ONE_PARAMETER_CHANGE_REBUILD_RESTORE'
            else:public['SW_editability']='FAIL_OR_UNVERIFIED'
        else:public['SW_editability']='NOT_AVAILABLE_NATIVE_PARAMETER'
        if (out/'negative.step').is_file():
            negative=load_shape(out/'negative.step')
            ng=original_geometry(negative,g)
            detail['negative_original_geometry']=ng
            public['negative_control']='REJECTED' if not ng['passed'] else 'FALSE_PASS'
        public['reason']='ORIGINAL_GEOMETRY_PASSED' if geom['passed'] else 'ORIGINAL_GEOMETRY_REJECTED'
        detail['status']='PASS' if geom['passed'] and public['negative_control']!='FALSE_PASS' else 'FAIL'
        public['status']=detail['status']
    except Exception as exc:
        import traceback
        detail.update(error_type=type(exc).__name__,traceback=traceback.format_exc())
        public.update(status='FAIL',reason='NEUTRAL_CHECK_ERROR',error_type=type(exc).__name__,
            failure_site=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)])
    detail.update(seconds=time.perf_counter()-t,public=public)
    base.save_json(out/'judge-private.json',detail)
    base.save_json(out/'judge-public.json',public)
    print(json.dumps(public,ensure_ascii=False))
    return 0 if detail['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(judge(sys.argv[1]))
