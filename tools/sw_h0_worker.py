"""Trusted H0 SW worker: candidate spec only; never accepts gold/card inputs."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base
from tools.sw_m1_inputs import private_path
from tools.sw_m1_build import Builder
from tools.cad_spec import validate_spec


def candidate_plan(spec):
    spec=validate_spec(spec)
    plan={k:copy.deepcopy(v) for k,v in spec.items() if k in ('regions','steps','center_xy','holes','pockets','finish')}
    plan['profile']=spec['family']
    if spec.get('regions'):
        bounds=[r['bounds'] for r in spec['regions']]
        plan['bbox']=[(min if i%2==0 else max)(b[i] for b in bounds) for i in range(6)]
    return plan


def admit(job):
    if not isinstance(job,dict) or set(job)-{'out','spec','healthcheck'}:
        raise ValueError('H0_worker_candidate_only_no_gold_or_card')
    if job.get('healthcheck') is True:
        if set(job)!={'out','healthcheck'}:raise ValueError('H0_healthcheck_fields')
        return None
    if set(job)!={'out','spec'}:raise ValueError('H0_candidate_fields')
    return candidate_plan(job['spec'])


def run(job_path):
    job=json.loads(private_path(job_path).read_text(encoding='utf-8'))
    plan=admit(job)
    out=private_path(job['out']);session=None;t=time.perf_counter()
    result=dict(status='FAIL',stop=False,worker_pid=os.getpid(),paid_model_calls=0)
    try:
        session=base.Session(out)
        result.update(pid=session.pid,revision=session.revision,initial_documents=0)
        if plan is None:
            result.update(status='PASS',healthcheck=True,final_documents=session.call(session.app,'GetDocumentCount'))
        else:
            session.adopt(session.call(session.app,'NewDocument',session.template,0,0.,0.))
            result['native_features']=Builder(session).build(plan)
            result['native']=session.save(out/'positive.sldprt')
            result['before_step']=session.save(out/'before-reopen.step',copy=True)
            session.close();session.reopen(out/'positive.sldprt')
            if not session.call(session.owned,'EditRebuild3'):raise RuntimeError('owned_native_reopen_rebuild_failed')
            result['reopened_step']=session.save(out/'reopened.step',copy=True)
            session.close()
            original=base.digest(out/'positive.sldprt')
            shutil.copyfile(out/'positive.sldprt',out/'edit-copy.sldprt')
            session.reopen(out/'edit-copy.sldprt')
            parameter=result['native_features']['edit_parameter']
            edit={'performed':False,'scope':'one_consumed_SW_dimension_change_and_restore'}
            dimension=session.call(session.owned,'Parameter',parameter) if parameter else None
            if dimension is not None:
                old=float(dimension.SystemValue)
                edit['native_parameter']=parameter
                changed=session.call(dimension,'SetSystemValue3',old*1.01,1,None)==0 and session.call(session.owned,'EditRebuild3')
                if changed:edit['changed_step']=session.save(out/'edited.step',copy=True)
                restored=session.call(dimension,'SetSystemValue3',old,1,None)==0 and session.call(session.owned,'EditRebuild3')
                if changed and restored:
                    edit['restored_step']=session.save(out/'restored.step',copy=True);edit['performed']=True
            session.close()
            result.update(edit=edit,original_native_unchanged=base.digest(out/'positive.sldprt')==original,
                final_documents=session.call(session.app,'GetDocumentCount'),status='PASS')
            if not result['original_native_unchanged']:raise RuntimeError('owned_original_native_changed')
    except Exception as exc:
        result.update(status='FAIL',error_type=type(exc).__name__,traceback=traceback.format_exc(),
            stop=session is None or session.uncertain or (isinstance(exc,RuntimeError) and str(exc).startswith('STOP_')))
    finally:
        if session:
            try:session.close()
            except Exception:result.update(status='FAIL',stop=True,cleanup_traceback=traceback.format_exc())
            result['COM_state_unknown']=session.uncertain
            session.events.close()
        result['seconds']=time.perf_counter()-t
        base.save_json(out/'com-result.json',result)
    print(json.dumps({k:result[k] for k in ('status','stop','pid','worker_pid','healthcheck','initial_documents','final_documents','error_type') if k in result}))
    return 0 if result['status']=='PASS' else 2 if result['stop'] else 1


if __name__=='__main__':
    try:raise SystemExit(run(sys.argv[1]))
    except Exception as exc:
        print(json.dumps({'status':'STOPPED','stop':True,'error_type':type(exc).__name__}));raise SystemExit(2)
