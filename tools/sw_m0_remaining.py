"""Zero-model M0 follow-up: SW polynomial controls and mass-accuracy audit.

Existing application attachment and owned-document safety reuse sw_m0.Session.
Only new outputs are written. A COM timeout stops the Python client ONLY and
leaves the session lock for a human; it never retries or stops SolidWorks.
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base

CONFIG=base.FIXTURES/'remaining-controls.json'
ORIGINAL=base.OUTPUTS/'m0-20261022-04'


def control_net(config,region,decoy,shift):
    """Hand-declared power polynomial -> cubic Bernstein grid, in API metres."""
    x0,x1,y0,y1=region
    terms={(r['i'],r['j']):r['value'] for r in config['polynomial_mm']}
    if decoy:
        # +0.4*(x-1)^2 on RIGHT patch: same height/slope, different curvature.
        for key,value in (((2,0),.4),((1,0),-.8),((0,0),.4)):
            terms[key]=terms.get(key,0)+value
    local={}
    for (i,j),value in terms.items():
        for k in range(i+1):
            for h in range(j+1):
                local[k,h]=local.get((k,h),0)+value*math.comb(i,k)*math.comb(j,h)*x0**(i-k)*(x1-x0)**k*y0**(j-h)*(y1-y0)**h
    # IModeler dispatch uses V-major/U-minor control coordinates.
    coords=[]
    for v in range(4):
        for u in range(4):
            z=sum(c*math.comb(u,k)/math.comb(3,k)*math.comb(v,h)/math.comb(3,h)
                  for (k,h),c in local.items() if k<=u and h<=v)
            coords.extend(((x0+(x1-x0)*u/3)/1000,(y0+(y1-y0)*v/3)/1000,(z+shift)/1000))
    return coords


def com(out):
    from win32com.client import VARIANT
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    result={'status':'FAIL','paid_model_calls':0,'started_at':base.utc(),'cases':{}}
    session=None
    t=time.perf_counter()
    try:
        session=base.Session(out)
        result.update(solidworks_pid=session.pid,revision=session.revision,initial_documents=0)
        def array(values):
            return VARIANT(session.pc.VT_ARRAY|session.pc.VT_R8,tuple(values))
        modeler=session.call(session.app,'GetModeler')
        # Official dispatch API: eight int32 values packed in four binary64s.
        props=struct.unpack('<4d',struct.pack('<8i',4,4,4,4,0,0,3,0))
        knots=(0.,0.,0.,0.,1.,1.,1.,1.)
        for case in config['cases']:
            tick=time.perf_counter()
            doc=session.adopt(session.call(session.app,'NewDocument',session.template,0,0.,0.))
            for index,region in enumerate(config['patch_regions_mm']):
                session.guard()
                coords=control_net(config,region,case['curvature_decoy'] and index==1,case['shift_z_mm'])
                surface=session.call(modeler,'CreateBsplineSurface',array(props),array(knots),array(knots),array(coords))
                if surface is None:raise RuntimeError('SW_bspline_creation_failed')
                sheet=session.call(modeler,'CreateSheetFromSurface',surface,array((0.,1.,0.,1.)))
                if sheet is None:raise RuntimeError('SW_sheet_creation_failed')
                feature=session.call(doc,'CreateFeatureFromBody3',sheet,False,0)
                if feature is None:raise RuntimeError('SW_sheet_feature_failed')
                feature.Name='M0_AnalyticPatch%d'%index
            if not session.call(doc,'EditRebuild3'):raise RuntimeError('SW_surface_rebuild_failed')
            row={'native':session.save(out/(case['id']+'.sldprt')),
                 'step':session.save(out/(case['id']+'.step'),copy=True),
                 'seconds':time.perf_counter()-tick}
            result['cases'][case['id']]=row
            session.close()
        source=ORIGINAL/'positive.sldprt'
        before=base.digest(source)
        shutil.copyfile(source,out/'volume-copy.sldprt')
        doc=session.reopen(out/'volume-copy.sldprt')
        session.call(doc,'ClearSelection2',True)
        legacy=session.mass()
        audit={'source_sha256':before,'legacy_body_mass':legacy,'extension_levels':[], 'object_levels':[]}
        ext=doc.Extension
        for level in (0,1,2):
            status=session.out_int()
            values=session.call(ext,'GetMassProperties2',level,status,False)
            if status.value or not values:raise RuntimeError('SW_mass_properties_status:'+str(status.value))
            audit['extension_levels'].append({'level':level,'status':status.value,'volume_mm3':float(values[3])*1e9,'area_mm2':float(values[4])*1e6,'raw_SI':list(values)})
        mass=session.call(ext,'CreateMassProperty2')
        mass.UseSystemUnits=True
        audit['object_initial_accuracy']=int(mass.AccuracyLevel)
        for level in (0,1,2):
            mass.AccuracyLevel=level
            if not session.call(mass,'Recalculate'):raise RuntimeError('SW_mass_recalculate_failed')
            audit['object_levels'].append({'level':int(mass.AccuracyLevel),'volume_mm3':float(mass.Volume)*1e9,'area_mm2':float(mass.SurfaceArea)*1e6})
        session.close()
        audit['source_unchanged']=base.digest(source)==before
        if not audit['source_unchanged']:raise RuntimeError('original_M0_native_changed')
        result.update(status='PASS',mass_audit=audit,final_documents=session.call(session.app,'GetDocumentCount'))
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        if session:
            try:session.close()
            except Exception as exc:result.update(status='FAIL',cleanup_error=str(exc))
            result['COM_state_unknown']=session.uncertain
            session.events.close()
        result.update(seconds=time.perf_counter()-t,finished_at=base.utc())
        base.save_json(out/'com-result.json',result)
    return 0 if result['status']=='PASS' else 1


def run(out):
    out=base.output_path(out)
    out.mkdir(parents=True,exist_ok=False)
    lock=base.OUTPUTS/'session.lock'
    with lock.open('x',encoding='utf-8') as f:json.dump({'out':str(out),'at':base.utc()},f)
    stopped=False
    result={'status':'FAIL','paid_model_calls':0,'started_at':base.utc(),'out':str(out)}
    result['source_sha256']={name:base.digest(ROOT/name) for name in (
        'tools/sw_m0.py','tools/sw_m0_remaining.py','tools/sw_m0_remaining_probe.py','tools/sw_m0_distance.py',
        'tools/cad_verify_v4_s3_judges.py','design/harness2-sw-m0/remaining-controls.json')}
    tick=time.perf_counter()
    try:
        argv=[str(base.SW_PYTHON),'-B',str(Path(__file__).resolve()),'--com-worker',str(out)]
        with (out/'com.stdout.bin').open('xb') as stdout,(out/'com.stderr.bin').open('xb') as stderr:
            p=subprocess.Popen(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
            try:code=p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=10);stopped=True
                raise RuntimeError('STOP_SW_state_unknown_no_retry_or_restart')
        result['com_exit']=code
        c=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
        if code:
            stopped=bool(c.get('COM_state_unknown')) or c.get('error','').startswith('STOP_') or 'STOP_' in c.get('cleanup_error','')
            raise RuntimeError('COM_failed:'+c.get('error','unknown'))
        bootstrap='import runpy,sys;sys.path[:0]='+repr([str(ROOT),str(base.FC_BIN)])+';runpy.run_module("tools.sw_m0_remaining_probe",run_name="__main__")'
        argv=[str(base.FC_BIN/'python.exe'),'-I','-B','-c',bootstrap,str(out)]
        with (out/'judge.stdout.bin').open('xb') as stdout,(out/'judge.stderr.bin').open('xb') as stderr:
            p=subprocess.run(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,timeout=300)
        result['judge_exit']=p.returncode
        result['judge']=json.loads((out/'judge-result.json').read_text(encoding='utf-8'))
        result['status']='PASS' if p.returncode==0 and result['judge']['status']=='PASS' else 'FAIL'
    except Exception as exc:result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(seconds=time.perf_counter()-tick,finished_at=base.utc(),manual_recovery_required=stopped)
        base.save_json(out/'result.json',result)
        if not stopped:lock.unlink()
    print(json.dumps({'status':result['status'],'seconds':result['seconds'],'out':str(out),'error':result.get('error')}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--out');g.add_argument('--com-worker')
    a=p.parse_args()
    raise SystemExit(com(base.output_path(a.com_worker)) if a.com_worker else run(a.out))
