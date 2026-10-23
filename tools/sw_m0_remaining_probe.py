"""Read actual SW STEP output; unchanged v4 interval G2/deviation kernels.

Whole M0-box boundary coverage is additionally checked by a separate native
parallel-solid certificate; no existing v4 checker, card, or threshold changes.
"""
import copy
import json
import math
from pathlib import Path
import sys
import time

from tools import cad_verify_v4_s3_judges as j
from tools import sw_m0 as base
from tools.sw_m0_distance import boundary_distance

CONFIG=base.FIXTURES/'remaining-controls.json'
ORIGINAL=base.OUTPUTS/'m0-20261022-04'


def imported(path):
    import Part
    shape=Part.Shape();shape.read(str(path))
    if shape.isNull() or not shape.isValid():raise ValueError('invalid_SW_STEP')
    return shape


def patches(shape,eps):
    """All faces, full trims, fixed physical charts; no ROI discarded faces."""
    if len(shape.Faces)!=2:raise ValueError('expected_exactly_two_full_control_faces')
    result=[]
    for index,face in enumerate(sorted(shape.Faces,key=lambda f:f.CenterOfMass.x)):
        u0,u1,v0,v1=face.ParameterRange
        o=face.Surface.value(u0,v0)
        du=face.Surface.value(u1,v0)-o
        dv=face.Surface.value(u0,v1)-o
        swap=abs(du.y)>abs(du.x)
        dx=dv if swap else du
        dy=du if swap else dv
        if abs(abs(dx.x)-1)>eps*8 or abs(dx.y)>eps*8 or abs(abs(dy.y)-1)>eps*8 or abs(dy.x)>eps*8:
            raise ValueError('native_XY_chart_not_registered_affine_square')
        mapping=dict(domain_uv='native_full',chart_uv=[index,index+1,0.,1.],
                     swap_uv=swap,reverse_u=dx.x<0,reverse_v=dy.y<0)
        result.append(j._patch(face,mapping,eps))
    domain=[0.,2.,0.,1.]
    j._tile([p['mapping']['chart_uv'] for p in result],domain)
    j._tile([s['box'] for p in result for s in p['spans']],domain)
    return result


def reference(eps):
    """Independent degree-4 closed-form graph, NOT the SW control-net routine.

z=.07*x²+.04*x*y+.11*y²+.015*x³ on x=[0,2], y=[0,1].
One complete reference face versus two native SW faces; no fitter or oracle.
"""
    import FreeCAD as App
    import Part
    poles=[]
    for u in range(5):
        row=[]
        for v in range(5):
            z=(.07*4*u*(u-1)/12 + .04*2*u*v/16 + .11*v*(v-1)/12
               + .015*8*u*(u-1)*(u-2)/24)
            row.append(App.Vector(2*u/4,v/4,z))
        poles.append(row)
    surface=Part.BSplineSurface()
    surface.buildFromPolesMultsKnots(poles,[5,5],[5,5],[0.,1.],[0.,1.],False,False,4,4)
    face=surface.toShape()
    mapping=dict(domain_uv='native_full',chart_uv=[0.,2.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
    return [j._patch(face,mapping,eps)]


def continuity(actual,config,metric):
    c=dict(config['continuity'],metric=metric,resources=config['resources'])
    if metric=='g1_continuity':c.pop('maximum_curvature_per_mm')
    a=dict(patch=0,axis='u',value=1.,range=[0.,1.],reverse=False)
    b=dict(a,patch=1)
    c['seams']=[dict(a=a,b=b)]
    j._seam_coverage(actual,c,[0.,2.,0.,1.])
    status,measured,evidence=j.certify_continuity(actual,c)
    return dict(status=status,measured=measured,evidence=evidence,criterion=c,
                all_actual_faces=len(actual),card_source='existing v4 native-control continuity helper thresholds unchanged')


def box_reference():
    import FreeCAD as App
    from tools.cad_spec import build_native,loads_spec
    # Reuse the original unmodified typed v4 construction for independent gold;
    # never use SW output or SW mass numbers as the reference geometry.
    spec=loads_spec((base.FIXTURES/'positive.json').read_text(encoding='utf-8'))
    doc=App.newDocument('M0_Independent_Box_Reference')
    try:
        body=build_native(doc,spec)
        return body.Shape.copy()
    finally:App.closeDocument(doc.Name)


def run(out):
    import FreeCAD as App
    import Part
    if list(App.Version())[:3]!=['1','1','4'] or App.GuiUp:raise RuntimeError('pinned_headless_FreeCAD_required')
    tick=time.perf_counter()
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
    result={'status':'FAIL','paid_model_calls':0,'at':base.utc(),
            'FreeCAD':list(App.Version()),'OCCT':Part.OCC_VERSION,
            'unchanged_G2_judge_sha256':base.digest(base.ROOT/'tools/cad_verify_v4_s3_judges.py'),
            'control_definition_sha256':base.digest(CONFIG),'surfaces':{}}
    try:
        shapes={case['id']:imported(out/(case['id']+'.step')) for case in config['cases']}
        epsilon=max(float(s.getTolerance(1)) for s in shapes.values())+128*math.ulp(2.)
        if not 0<epsilon<=1e-5:raise ValueError('native_control_uncertainty_exhausts_existing_budget')
        ref=reference(epsilon)
        controls={name:patches(s,epsilon) for name,s in shapes.items()}
        for name,actual in controls.items():
            ds,dm,de=j.certify_deviation(ref,actual,[0.,2.,0.,1.],config['maximum_deviation_mm'],config['resources'],epsilon)
            result['surfaces'][name]={'G2':continuity(actual,config,'g2_continuity'),
                'G1':continuity(actual,config,'g1_continuity'),
                'whole_surface_deviation':dict(status=ds,measured=dm,evidence=de,target_mm=.005),
                'native_coordinate_uncertainty_mm':epsilon,
                'all_faces_mapped':len(actual)==len(shapes[name].Faces),
                'step_sha256':base.digest(out/(name+'.step')),
                'surface_types':[type(f.Surface).__name__ for f in shapes[name].Faces]}
        # Retain a separately generated, inspectable reference.
        refshape=Part.makeCompound([p['face'] for p in ref])
        refshape.exportStep(str(out/'independent-polynomial-reference.step'))
        box=imported(ORIGINAL/'reopened.step')
        ideal=box_reference()
        ideal.exportStep(str(out/'independent-box-reference.step'))
        moved=box.copy();moved.translate(App.Vector(.01,0,0))
        moved.exportStep(str(out/'box-displaced-control.step'))
        result['whole_box_boundary']={
            'positive':boundary_distance(ideal,box,.005),
            'negative':boundary_distance(ideal,moved,.005),
            'negative_description':'explicit independent DEV rigid +0.01mm X translation of the whole SW-derived box boundary',
            'reference':'unchanged v4 cad_spec.build_native on handwritten original positive spec',
            'reference_volume_mm3':ideal.Volume,'SW_STEP_volume_mm3':box.Volume,
            'original_SW_STEP_sha256':base.digest(ORIGINAL/'reopened.step')}
        from tools.sw_m0_probe import analytic_volume
        analytic=analytic_volume()
        mass=com['mass_audit']
        legacy=mass['legacy_body_mass']['volume_mm3']
        high=next(r['volume_mm3'] for r in mass['object_levels'] if r['level']==2)
        mass.update(analytic_volume_mm3=analytic,FreeCAD_STEP_volume_mm3=box.Volume,
            legacy_minus_FreeCAD_mm3=legacy-box.Volume,
            legacy_minus_high_accuracy_mm3=legacy-high,
            high_accuracy_minus_FreeCAD_mm3=high-box.Volume,
            high_accuracy_minus_analytic_mm3=high-analytic,
            legacy_minus_analytic_mm3=legacy-analytic,
            interpretation='Body.GetMassProperties default integration versus explicit higher-accuracy IMassProperty2; residual STEP/OCCT and numerical integration difference recorded separately; no scoring change',
            handling='SW volume remains secondary cross-check only. Original values preserved, never substituted into v4 geometry scoring.')
        mass['higher_accuracy_explains_major_difference']=abs(high-analytic)<abs(legacy-analytic) and abs(legacy-high)>abs(high-box.Volume)
        result['mass_audit']=mass
        s=result['surfaces'];boxchecks=result['whole_box_boundary']
        expected=(s['g2']['G2']['status']=='PASS' and s['g1_only']['G1']['status']=='PASS'
                  and s['g1_only']['G2']['status']=='FAIL'
                  and all(s[n]['whole_surface_deviation']['status']=='PASS' for n in ('g2','within'))
                  and s['displaced']['whole_surface_deviation']['status']=='FAIL'
                  and boxchecks['positive']['status']=='PASS' and boxchecks['negative']['status']=='FAIL'
                  and mass['source_unchanged'] and mass['higher_accuracy_explains_major_difference'])
        result['status']='PASS' if expected else 'FAIL'
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    result['seconds']=time.perf_counter()-tick
    base.save_json(out/'judge-result.json',result)
    print(json.dumps({'status':result['status'],'seconds':result['seconds'],'error':result.get('error')}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(run(base.output_path(sys.argv[1])))
