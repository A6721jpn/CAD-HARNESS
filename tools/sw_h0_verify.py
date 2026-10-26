"""Fresh pinned SDK verification of actual SW-exported STEP, machine-only gold."""
import json
import os
from pathlib import Path
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base
from tools import sw_m1_judge as m1
from tools.sw_m1_inputs import private_path
from tools.sw_m1_distance import whole_distance


def verify(job_path):
    import FreeCAD as App
    import Part
    job=json.loads(private_path(job_path).read_text(encoding='utf-8'))
    out=private_path(job['out']);t=time.perf_counter()
    result=dict(verification_pass=False,owned_pid=os.getpid(),document_closed=False)
    try:
        if list(App.Version())[:3]!=['1','1','4'] or App.GuiUp:raise RuntimeError('pinned_headless_SDK_required')
        if base.digest(job['gold_path'])!=job['gold_sha256']:raise RuntimeError('original_gold_binding')
        from tools import cad_verify_v3_probe,cad_spec_probe
        loader=cad_verify_v3_probe.load_gold if job['gold'].get('schema')=='cad-harness.verify-gold.v3' else cad_spec_probe.load_gold
        gold=loader(job['gold_path'])
        if gold!=job['gold']:raise RuntimeError('copied_gold_binding')
        com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
        step=out/'reopened.step'
        if base.digest(step)!=com['reopened_step']['sha256']:raise RuntimeError('STEP_binding')
        shape=m1.load_shape(step)
        geometry=m1.original_geometry(shape,gold)
        reference=m1.independent_reference(gold)
        distance=whole_distance(reference,shape,.005)
        result.update(original_geometry=geometry,whole_boundary=distance,
            FreeCAD=list(App.Version()),OCCT=Part.OCC_VERSION,
            verification_pass=bool(geometry['passed'] and distance['status']=='PASS'),
            STEP_sha256=base.digest(step),document_closed=not bool(App.listDocuments()))
        result['verification_pass'] &= result['document_closed']
    except Exception as exc:
        result.update(error_type=type(exc).__name__,traceback=traceback.format_exc())
    result['seconds']=time.perf_counter()-t
    base.save_json(out/'verification-private.json',result)
    print(json.dumps({k:result[k] for k in ('verification_pass','owned_pid','document_closed','error_type') if k in result}))
    return 0 if result['verification_pass'] else 1


if __name__=='__main__':raise SystemExit(verify(sys.argv[1]))
