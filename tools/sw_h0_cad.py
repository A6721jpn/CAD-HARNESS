"""Fixed spec->SW compilation and truthful legacy-gate result interoperability.

Only the fixed hash-bound wrapper is executed. No model-generated Python, gold
or card is supplied to the COM worker. Existing M1 neutral predicates are reused.
"""
import json
import math
from pathlib import Path
import subprocess
import time

from tools import cad_spec,cad_verify_v4_ledger as ledger,sw_m0 as base
from tools.sw_m1_inputs import private_path
from tools.cad_verify_guard import Stop


def compile_candidate(spec):
    spec=cad_spec.validate_spec(spec)
    expected=ledger.sha(cad_spec.canonical(spec).encode('utf-8'))
    return ('import json,sys\nfrom pathlib import Path\n'
        'sys.path.insert(0,'+repr(str(base.ROOT))+')\n'
        'from tools import sw_h0_worker as worker,cad_spec,cad_verify_v4_ledger as ledger\n'
        'from tools.sw_m1_inputs import private_path\n'
        'job=json.loads(private_path(sys.argv[1]).read_text(encoding="utf-8"))\n'
        'worker.admit(job)\n'
        'if ledger.sha(cad_spec.canonical(cad_spec.validate_spec(job["spec"])).encode("utf-8"))!='+repr(expected)+':\n'
        '    raise RuntimeError("candidate_spec_binding")\n'
        'raise SystemExit(worker.run(sys.argv[1]))\n')


class Compiler:
    def __getattr__(self,name):return getattr(cad_spec,name)
    def compile_spec(self,spec):return compile_candidate(spec)


def child(argv,out,stem,timeout,*,SW=False):
    if not math.isfinite(timeout) or timeout<=0:raise Stop('H0_CAD_deadline_exhausted')
    tick=time.monotonic()
    with (out/(stem+'.stdout.bin')).open('xb') as stdout,(out/(stem+'.stderr.bin')).open('xb') as stderr:
        p=subprocess.Popen(argv,cwd=base.ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False)
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # This is ONLY the owned Python client/SDK process. Never taskkill /T
            # or stop/restart the shared SLDWORKS.exe COM server.
            p.kill();p.wait(timeout=10)
            raise Stop('STOP_SW_nonresponse_no_restart' if SW else 'H0_neutral_worker_timeout')
    return code,p.pid,time.monotonic()-tick


def sdk(module,job):
    bootstrap='import runpy,sys;sys.path[:0]='+repr([str(base.ROOT),str(base.FC_BIN)])+';runpy.run_module('+repr(module)+',run_name="__main__")'
    return [str(base.FC_BIN/'python.exe'),'-I','-B','-c',bootstrap,str(job)]


def run_candidate(spec,entry,out,script,*,cad_timeout,reimport_timeout,total_timeout):
    out=private_path(out);out.mkdir(parents=True,exist_ok=False)
    script=private_path(script)
    if script.read_text(encoding='utf-8')!=compile_candidate(spec):raise Stop('H0_fixed_compiler_binding')
    started=time.monotonic();first_deadline=started+cad_timeout;end=started+total_timeout
    worker_job=out/'worker-job.json'
    base.save_json(worker_job,dict(out=str(out),spec=spec))
    code,pid,_=child([str(base.SW_PYTHON),'-B',str(script),str(worker_job)],out,'SW',min(cad_timeout,total_timeout-30),SW=True)
    com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
    if com.get('stop') or com.get('COM_state_unknown'):raise Stop('STOP_SW_state_unknown_no_restart')
    result=dict(schema='cad-harness.cad_run.v0',backend='solidworks-fixed-spec-neutral-v1',
        task_id=entry['gold']['case_id'],probe_profile='verify-v3',generator='compiler',
        script_sha256=base.digest(script),gold_sha256=entry['gold_sha256'],
        status='failed',geometry_ok=None,editability_ok=None,probe_pass=False,probe_status='fail',
        script_completed=com['status']=='PASS',document_closed=com.get('final_documents')==0,
        cleanup_status='exited',cad_exit_code=code,owned_pid=pid,
        verification_pass=False,verification_cleanup_status=None,verification_exit_code=None,
        verification_pid=None,verification={},failed_phase='build',next_actor='human',
        code_owner='harness',message_code='H0_SW_build_failed',measurements=None,predicate_details={})
    if com['status']!='PASS':
        result['error_type']=com.get('error_type')
        base.save_json(out/'result.json',result);return result
    # Sealed gold is introduced only AFTER the candidate-only SW worker exited.
    job={k:entry[k] for k in ('sequence','group','route','profile','gold','gold_path','gold_sha256')}
    job['out']=str(out);job_path=out/'job.json';base.save_json(job_path,job)
    primary,_,_=child(sdk('tools.sw_m1_judge',job_path),out,'neutral-primary',min(first_deadline,end-30)-time.monotonic())
    detail=json.loads((out/'judge-private.json').read_text(encoding='utf-8'))
    public=detail['public']
    if public.get('error_type'):raise Stop('H0_neutral_checker_error')
    edit=detail.get('SW_operational_edit',{})
    editable=bool(edit.get('changed_symmetric_volume_mm3',0)>edit.get('uncertainty_mm3',math.inf)
        and edit.get('restore',{}).get('status')=='PASS' and com.get('original_native_unchanged'))
    # Same compound M1 requirement, attributed truthfully: restoring a wrong
    # candidate can prove native editing, but cannot prove correct geometry.
    geometry=bool(public['geometry']=='PASS' and public['extra_distance_0_005']=='PASS'
        and edit.get('restored_original_geometry',{}).get('passed'))
    result.update(geometry_ok=geometry,editability_ok=editable,
        failed_phase='probe',next_actor='sol',code_owner='candidate',message_code='H0_candidate_predicate_rejected',
        measurements=dict(original_geometry_pass=public['geometry']=='PASS',whole_boundary_pass=public['extra_distance_0_005']=='PASS',
            native_reopened=True,native_edit_restored=editable),
        predicate_details={'checks':[{'field':k,'passed':False} for k in public.get('failed_predicate_groups',[])]})
    if public['extra_distance_0_005']!='PASS':result['predicate_details']['checks'].append({'field':'whole_boundary','passed':False})
    if not editable:
        result.update(code_owner='harness',message_code='H0_native_editability_unverified',next_actor='human')
    if geometry and editable:
        verification_code,verification_pid,_=child(sdk('tools.sw_h0_verify',job_path),out,'neutral-fresh-reimport',
            min(reimport_timeout,end-time.monotonic()-30))
        verification=json.loads((out/'verification-private.json').read_text(encoding='utf-8'))
        if verification.get('error_type'):raise Stop('H0_fresh_verification_error')
        result.update(verification_pid=verification_pid,verification_exit_code=verification_code,
            verification_cleanup_status='exited',verification_pass=verification['verification_pass'],
            verification={k:verification[k] for k in ('verification_pass','document_closed','owned_pid','STEP_sha256')})
        if verification_code==0 and verification['verification_pass'] and verification['document_closed']:
            result.update(status='ok',probe_status='pass',probe_pass=True,failed_phase=None,next_actor=None,
                message_code='completed')
        else:result.update(failed_phase='verification',next_actor='human',code_owner='harness',message_code='H0_fresh_reimport_failed')
    result.update(wall_s=time.monotonic()-started,SW_pid=com['pid'],SW_exited=False,
        candidate_spec_sha256=ledger.sha(cad_spec.canonical(spec).encode('utf-8')),
        executed_worker_sha256=base.digest(base.ROOT/'tools/sw_h0_worker.py'))
    base.save_json(out/'result.json',result)
    return result
