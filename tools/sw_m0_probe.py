"""Independent M0 STEP measurements; existing v4 geometry kernels stay unedited.

P1's unchanged historical gate is reported separately from the USER's additional
0.005mm check. SolidWorks history/edit evidence is separate, not forged FreeCAD
PartDesign history. Neither mass properties nor a minimum distance proves G2.
"""
import copy
import json
import math
from pathlib import Path
import sys
import time

from tools import cad_spec_probe as probe
from tools.sw_m0 import ROOT, digest, output_path, save_json


def analytic_volume(height=20):
    # Integral of (40-2a(z))*(30-2a(z)), a=3-sqrt(9-(z-(H-3))^2).
    # Top-edge cylinder intersections are mitred, not spherical corner blends.
    r, width, depth = 3., 40., 30.
    loss = (2-math.pi/2)*(width+depth)*r*r + (2*math.pi-20/3)*r**3
    return width*depth*height-20*15*5-loss


def measure(shape, gold):
    checks = probe.Checks(gold['case_id'])
    measurements = probe.measure_shape(shape, gold, checks)
    return {'passed':all(checks.predicates.values()),'measurements':measurements,
            'predicates':checks.predicates,'checks':checks.records}


def comparison(a,b,gold):
    # Same metrics as v4 neutral reimport evidence; not a Hausdorff certificate.
    bounds_ok = probe.same_bounds(probe.bounds(a),probe.bounds(b),.005)
    volume_relative = abs(a.Volume-b.Volume)/max(abs(a.Volume),1e-30)
    difference = a.cut(b).Volume+b.cut(a).Volume
    return {'passed':bounds_ok and volume_relative<=gold['tolerances']['volume_relative']
                     and difference/max(a.Volume,1e-30)<=gold['tolerances']['volume_relative'],
            'bounds_within_mm':.005,'volume_relative':volume_relative,
            'symmetric_difference_mm3':difference,'maximum_surface_deviation_mm':None,
            'method':'bbox, volume and exact BRep boolean difference; NOT certified maximum deviation'}


def run(out):
    import FreeCAD as App
    import Part
    t=time.perf_counter()
    if list(App.Version())[:3]!=['1','1','4'] or App.GuiUp:
        raise RuntimeError('need_pinned_FreeCAD_1_1_4_headless')
    golden=ROOT/'design/cad-harness-mvp/eval-v1/P1.json'
    gold=probe.load_gold(golden)
    strict=copy.deepcopy(gold)
    strict['tolerances']['linear_mm']=.005  # Additional explicit M0 USER guard only.
    # The target is independently derived, not a measurement copied from SW.
    analytic=analytic_volume()
    com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
    result={'status':'FAIL','freecad_version':list(App.Version()),'occt_version':Part.OCC_VERSION,
            'paid_model_calls':0,'gold_sha256':digest(golden),
            'unchanged_P1_linear_mm':gold['tolerances']['linear_mm'],
            'additional_USER_linear_mm':.005,'analytic_volume_mm3':analytic,
            'analytic_reference_delta_mm3':analytic-gold['volume']['target_mm3'],
            'stages':{}}
    shapes={}
    for name,file in [('before_reopen','before-reopen.step'),('reopened','reopened.step'),
                      ('edited','edited.step'),('restored','restored.step'),('negative','wrong-depth.step')]:
        tick=time.perf_counter()
        shape=Part.Shape()
        shape.read(str(out/file))
        if shape.isNull():
            raise RuntimeError('STEP_null:'+name)
        shapes[name]=shape
        g,s=copy.deepcopy(gold),copy.deepcopy(strict)
        if name=='edited':
            # Preregistered DEV +1mm perturbation; original card remains untouched.
            for v in (g,s):
                v['bbox'][5]=21
                v['regions'][0]['bounds'][5]=21
                v['pockets'][0]['top_z']=21
                v['volume']['target_mm3']=analytic_volume(21)
                v['volume']['upper_exclusive']=40*30*21-20*15*5
        actual=measure(shape,g)
        tighter=measure(shape,s)
        expected_volume=analytic_volume(21 if name=='edited' else 20)
        stage={'unchanged_v4_geometry':actual,'additional_USER_0_005':tighter,
               'analytic_expected_volume_mm3':expected_volume,
               'analytic_volume_error_mm3':shape.Volume-expected_volume,
               'surface_types':{},'step_sha256':digest(out/file),'seconds':time.perf_counter()-tick}
        for face in shape.Faces:
            kind=type(face.Surface).__name__
            stage['surface_types'][kind]=stage['surface_types'].get(kind,0)+1
        result['stages'][name]=stage
    main=shapes['reopened']
    # Independent neutral native save/close/reopen AND STEP export/reimport.
    doc=App.newDocument('SW_M0_Neutral')
    obj=doc.addObject('Part::Feature','ImportedSTEP')
    obj.Shape=main
    doc.recompute()
    native=out/'neutral.FCStd'
    doc.saveAs(str(native))
    App.closeDocument(doc.Name)
    doc=App.openDocument(str(native))
    native_shape=doc.getObject('ImportedSTEP').Shape
    native_check=measure(native_shape,gold)
    native_strict=measure(native_shape,strict)
    neutral_step=out/'neutral-reexport.step'
    Part.export([doc.getObject('ImportedSTEP')],str(neutral_step))
    App.closeDocument(doc.Name)
    neutral=Part.Shape()
    neutral.read(str(neutral_step))
    neutral_check=measure(neutral,gold)
    neutral_strict=measure(neutral,strict)
    result['neutral_roundtrip']={'native_passed':native_check['passed'] and native_strict['passed'],
        'step_passed':neutral_check['passed'] and neutral_strict['passed'],
        'native_fcstd_sha256':digest(native),'step_sha256':digest(neutral_step),
        'comparison':comparison(main,neutral,gold)}
    result['native_reopen_comparison']=comparison(shapes['before_reopen'],main,gold)
    result['restore_comparison']=comparison(main,shapes['restored'],gold)
    result['edit_change']={'height_delta_mm':shapes['edited'].BoundBox.ZLength-main.BoundBox.ZLength,
                          'expected_height_delta_mm':1,
                          'volume_delta_mm3':shapes['edited'].Volume-main.Volume,
                          'expected_volume_delta_mm3':1200}
    result['SW_mass_cross_check']={}
    for name,source in [('reopened','reopened'),('edited','edited'),('restored','restored')]:
        swmass=com['stages'][source]['mass']
        result['SW_mass_cross_check'][name]={'role':'secondary_only','SW_volume_mm3':swmass['volume_mm3'],
            'FreeCAD_volume_mm3':shapes[name].Volume,
            'difference_mm3':swmass['volume_mm3']-shapes[name].Volume}
    # Existing v4 G2 certifier expressly excludes analytic/rational cylinders.
    # Do NOT change its domain, approximate rational faces, or turn UNKNOWN into PASS.
    result['G2_risk']={'status':'UNVERIFIED','required_for_this_box_card':False,
        'reason':'Existing v4 C6 full-domain certificate supports nonrational polynomial patches, not analytic/rational circular fillets. Constant-R plane/cylinder transition is G1, not G2.',
        'actual_cylindrical_radii_mm':[float(f.Surface.Radius) for f in main.Faces if isinstance(f.Surface,Part.Cylinder)],
        'positive_G2_control':'NOT_RUN; required before broader SolidWorks H0/G2 claim',
        'unchanged_certifier_sha256':digest(ROOT/'tools/cad_verify_v4_s3_judges.py')}
    stages=result['stages']
    positive=all(stages[n]['unchanged_v4_geometry']['passed'] and stages[n]['additional_USER_0_005']['passed']
                 for n in ('before_reopen','reopened','edited','restored'))
    negative=(not stages['negative']['unchanged_v4_geometry']['passed']
              and not stages['negative']['additional_USER_0_005']['passed']
              and stages['negative']['unchanged_v4_geometry']['predicates']['pockets'] is False)
    result['negative_control_rejected_by_same_gold']=negative
    delta=result['edit_change']
    edit_ok=abs(delta['height_delta_mm']-1)<=.005 and abs(delta['volume_delta_mm3']-1200)<=gold['tolerances']['volume_relative']*main.Volume
    result['editability_ok']=edit_ok and result['restore_comparison']['passed'] and com['original_native_unchanged']
    result['status']='PASS' if (positive and negative and result['editability_ok']
        and result['native_reopen_comparison']['passed'] and result['neutral_roundtrip']['native_passed']
        and result['neutral_roundtrip']['step_passed'] and result['neutral_roundtrip']['comparison']['passed']) else 'FAIL'
    result['seconds']=time.perf_counter()-t
    save_json(out/'judge-result.json',result)
    print(json.dumps({'status':result['status'],'out':str(out),'seconds':result['seconds']}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(run(output_path(sys.argv[1])))
