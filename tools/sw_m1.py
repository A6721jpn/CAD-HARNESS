"""M1 deterministic gold portability queue, no providers/models/billed calls.

Private inputs/derived CAD/logs stay ignored. Stdout/public reports contain only
ordinal, public family/route metadata, statuses, fixed reasons and elapsed time.
"""
import argparse
import copy
import hashlib
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base
from tools.sw_m1_build import Builder,Unsupported,construction
from tools.sw_m1_inputs import PRIVATE,private_path,COHORT_SHA
from tools import sw_m1_saved as saved_tools

PROFILES=('roller','taper','elbow','ribbed_box','flange','rect_prism')
PUBLIC_FIELDS={'sequence','group','route','profile','geometry','extra_distance_0_005','G2',
    'SW_editability','original_behavioural_score','original_FreeCAD_native_history',
    'negative_control','reason','status','failed_predicate_groups','distance_reason',
    'error_type','failure_site','seconds','COM_worker_seconds','neutral_worker_seconds'}


def validate_public_row(row):
    if not isinstance(row,dict) or set(row)-PUBLIC_FIELDS:
        raise RuntimeError('private_field_in_public_projection')
    metadata={'group':{'dev','legacy','mvp','geometry','q','completion','fault','independent_dev'},
              'route':{'source','spec','mvp','completion','ask','offline'},
              'profile':set(PROFILES)|{'rect_stack','stepped_shaft','unsupported_profile',None}}
    codes=PUBLIC_FIELDS-set(metadata)-{'sequence','seconds','COM_worker_seconds',
        'neutral_worker_seconds','failure_site','failed_predicate_groups','error_type'}
    for key,value in row.items():
        if key in metadata:
            if value not in metadata[key]:raise RuntimeError('nonpublic_metadata_value')
        elif key=='sequence':
            if type(value) is not int or not 1<=value<=60:raise RuntimeError('public_sequence')
        elif key in ('seconds','COM_worker_seconds','neutral_worker_seconds'):
            if type(value) not in (int,float) or not math.isfinite(value) or value<0:
                raise RuntimeError('public_time')
        elif key in codes:
            if value is not None and (not isinstance(value,str) or re.fullmatch(r'[A-Z][A-Z0-9_]{0,95}',value) is None):
                raise RuntimeError('private_payload_under_public_status')
        elif key=='error_type':
            if value is not None and (not isinstance(value,str) or re.fullmatch(r'[A-Za-z_]{1,64}',value) is None):
                raise RuntimeError('public_error_type')
        elif key=='failed_predicate_groups':
            allowed={'valid_solid','bbox','volume','holes','pockets','steps','sections','finish',
                     'roller','taper','elbow','box','rib','walls','flange','stock','editability'}
            if not isinstance(value,list) or any(v not in allowed for v in value):
                raise RuntimeError('private_predicate_identity')
        elif key=='failure_site':
            if not isinstance(value,list):raise RuntimeError('public_failure_site')
            for frame in value:
                if not isinstance(frame,dict) or set(frame)!={'file','line','function'}:
                    raise RuntimeError('private_failure_payload')
                if (not isinstance(frame['file'],str) or '/' in frame['file'] or '\\' in frame['file']
                        or type(frame['line']) is not int or frame['line']<1
                        or not isinstance(frame['function'],str)):
                    raise RuntimeError('private_failure_identity')


def publish(path,value):
    # No arbitrary producer dictionaries are copied to public output.
    if isinstance(value,list):
        for row in value:
            validate_public_row(row)
    with Path(path).open('w',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def negative_plan(plan):
    p=copy.deepcopy(plan);kind=p['profile']
    if kind=='roller':p['groove_depth']*=1.1
    elif kind=='taper':p['top'][0]*=1.02
    elif kind=='elbow':p['outer_radius']*=1.02
    elif kind=='ribbed_box':p['rib_thickness']*=1.02
    elif kind=='flange':p['bore_radius']*=1.02
    elif kind in ('rect_prism','rect_stack'):
        if p.get('pockets'):p['pockets'][0]['depth']+=max(.05,p['pockets'][0]['depth']*.02)
        else:
            b=p['bbox'];change=max(.05,(b[5]-b[4])*.02);b[5]+=change
            if p.get('regions'):p['regions'][-1]['bounds'][5]+=change
    else:raise Unsupported('negative_profile_not_registered')
    return p


def com_case(job_path):
    job=json.loads(private_path(job_path).read_text(encoding='utf-8'))
    out=private_path(job['out']);result={'status':'FAIL','paid_model_calls':0,'at':base.utc()}
    session=None;t=time.perf_counter()
    try:
        session=base.Session(out)
        result.update(pid=session.pid,initial_documents=0)
        def build(plan):
            session.adopt(session.call(session.app,'NewDocument',session.template,0,0.,0.))
            builder=Builder(session)
            return builder.build(plan)
        plan=construction(job['gold'])
        if job.get('reuse_native'):
            result.update(saved_tools.copied_native_result(out,plan))
            parameter=result['native_features']['edit_parameter']
        else:
            result['native_features']=build(plan)
            parameter=result['native_features']['edit_parameter']
            result['native']=session.save(out/'positive.sldprt')
            result['before_step']=session.save(out/'before-reopen.step',copy=True)
            session.close()
            session.reopen(out/'positive.sldprt')
            if not session.call(session.owned,'EditRebuild3'):raise RuntimeError('reopened_native_rebuild_failed')
            result['reopened_step']=session.save(out/'reopened.step',copy=True)
            session.close()
        original=base.digest(out/'positive.sldprt')
        shutil.copyfile(out/'positive.sldprt',out/'edit-copy.sldprt')
        session.reopen(out/'edit-copy.sldprt')
        edit={'performed':False,'scope':'one_native_consumed_parameter_not_all_original_FreeCAD_roles'}
        dimension=None;old=None
        try:
            dimension=session.call(session.owned,'Parameter',parameter) if parameter else None
            if dimension is not None:
                old=float(dimension.SystemValue)
                edit['native_parameter']=parameter
                changed=session.call(dimension,'SetSystemValue3',old*1.01,1,None)==0 and session.call(session.owned,'EditRebuild3')
                if changed:
                    edit['changed_step']=session.save(out/'edited.step',copy=True)
                restored=session.call(dimension,'SetSystemValue3',old,1,None)==0 and session.call(session.owned,'EditRebuild3')
                if changed and restored:
                    edit['restored_step']=session.save(out/'restored.step',copy=True)
                    edit['performed']=True
                else:edit['reason']='native_parameter_edit_or_restore_rebuild_failed'
            else:edit['reason']='native_parameter_missing'
        except Exception:
            edit['traceback']=traceback.format_exc()
            if session.uncertain:raise
            if dimension is not None and old is not None:
                session.call(dimension,'SetSystemValue3',old,1,None)
                session.call(session.owned,'EditRebuild3')
        session.close()
        result['edit']=edit
        result['original_native_unchanged']=base.digest(out/'positive.sldprt')==original
        if not result['original_native_unchanged']:raise RuntimeError('original_native_changed')
        if job.get('negative'):
            try:
                result['negative_features']=build(negative_plan(plan))
                result['negative_step']=session.save(out/'negative.step',copy=True)
                session.close()
            except Exception:
                result['negative_traceback']=traceback.format_exc()
                if session.uncertain:raise
                session.close()
        result.update(status='PASS',final_documents=session.call(session.app,'GetDocumentCount'))
    except Exception as exc:
        result.update(error_type=type(exc).__name__,traceback=traceback.format_exc(),
            unsupported=isinstance(exc,Unsupported),
            stop=session is None or bool(session.uncertain) or (isinstance(exc,RuntimeError) and str(exc).startswith('STOP_')),
            failure_site=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)])
    finally:
        if session:
            try:session.close()
            except Exception:
                result.update(status='FAIL',stop=True,cleanup_traceback=traceback.format_exc())
            result['COM_state_unknown']=session.uncertain
            session.events.close()
        result['seconds']=time.perf_counter()-t
        base.save_json(out/'com-result.json',result)
    return 0 if result['status']=='PASS' else 1


def dev_inputs(out):
    rows=[]
    for index,name in enumerate(('G1','G2','G3','G4','G5','G6','S3'),1):
        path=ROOT/'design/cad-harness-verify-v3/test'/name/'gold.json'
        g=json.loads(path.read_text(encoding='utf-8'))
        rows.append({'sequence':index,'group':'independent_dev','route':'source','profile':g['profile'],
            'gold':g,'gold_path':str(path),'gold_sha256':base.digest(path),'card':{}})
    # A new developer control, derived ONLY from public P2. No finish: the
    # last feature is a through hole whose overrun cannot prove editability.
    g=json.loads((ROOT/'design/cad-harness-mvp/eval-v1/P2.json').read_text(encoding='utf-8'))
    g.update(case_id='M1_POCKET_THROUGH',description='Independent public pocket plus through-hole editing control, no finish.',finish=None,
        provenance={'authority':'fixture','decision':'M1-independent-public-control','version':1,'confirmed':False})
    g['description_sha256']=hashlib.sha256(g['description'].encode('utf-8')).hexdigest()
    b=g['bbox']
    volume=math.prod(b[i+1]-b[i] for i in (0,2,4))
    volume-=sum((p['bounds'][1]-p['bounds'][0])*(p['bounds'][3]-p['bounds'][2])*p['depth'] for p in g['pockets'])
    volume-=sum(math.pi*(h['diameter']/2)**2*(h['z'][1]-h['z'][0]) for h in g['holes'])
    g['volume'].update(target_mm3=volume,formula='box - pockets - through-hole cylinders')
    path=out/'independent-legacy-gold.json';base.save_json(path,g)
    rows.append({'sequence':8,'group':'independent_dev','route':'spec','profile':'rect_prism',
        'gold':g,'gold_path':str(path),'gold_sha256':base.digest(path),'card':{}})
    return {'entries':rows,'paid_model_calls':0,'scope':'public_independent_native_controls'}


def run_case(entry,out,negative,saved=None,redo_edit=False):
    out.mkdir(parents=True,exist_ok=False)
    job=dict(entry,out=str(out),negative=negative)
    if saved and redo_edit:job['reuse_native']=True
    base.save_json(out/'job.json',job)
    row={key:entry[key] for key in ('sequence','group','route','profile')}
    row.update(status='FAIL',geometry='NOT_RUN',extra_distance_0_005='NOT_RUN',G2='NOT_REQUIRED_BY_ORIGINAL_CARD',
        SW_editability='NOT_RUN',negative_control='NOT_RUN',original_behavioural_score='NOT_RUN_NO_LLM',
        original_FreeCAD_native_history='NOT_APPLICABLE_TO_SW_NATIVE',reason='NOT_STARTED')
    t=time.perf_counter();stop=False
    try:
        if saved:saved_tools.prepare(entry,out,saved,redo_edit)
        if not saved or redo_edit:
            argv=[str(base.SW_PYTHON),'-B',str(Path(__file__).resolve()),'--com-worker',str(out/'job.json')]
            with (out/'com.stdout.bin').open('xb') as stdout,(out/'com.stderr.bin').open('xb') as stderr:
                process=subprocess.Popen(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
                try:code=process.wait(timeout=300)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait(timeout=10);stop=True
                    raise RuntimeError('STOP_SW_state_unknown_client_only_stopped')
        else:code=0
        com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
        row['COM_worker_seconds']=com['seconds'] if not saved or redo_edit else 0.
        if code:
            row.update(status='NOT_BUILDABLE' if com.get('unsupported') else 'BUILD_FAILED',reason='SW_NATIVE_RECIPE_REJECTED',
                error_type=com.get('error_type'),failure_site=com.get('failure_site',[]))
            stop=bool(com.get('stop') or com.get('COM_state_unknown'))
        else:
            bootstrap='import runpy,sys;sys.path[:0]='+repr([str(ROOT),str(base.FC_BIN)])+';runpy.run_module("tools.sw_m1_judge",run_name="__main__")'
            argv=[str(base.FC_BIN/'python.exe'),'-I','-B','-c',bootstrap,str(out/'job.json')]
            with (out/'judge.stdout.bin').open('xb') as stdout,(out/'judge.stderr.bin').open('xb') as stderr:
                jp=subprocess.run(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,timeout=300)
            if (out/'judge-public.json').is_file():
                row.update(json.loads((out/'judge-public.json').read_text(encoding='utf-8')))
                detail=json.loads((out/'judge-private.json').read_text(encoding='utf-8'))
                row['neutral_worker_seconds']=detail['seconds']
            else:row.update(status='FAIL',reason='NEUTRAL_RESULT_MISSING')
            if negative and row['negative_control']=='NOT_RUN':
                row['negative_control']='BUILD_FAILED_NOT_A_VALID_NEGATIVE'
    except Exception as exc:
        base.save_json(out/'host-error-private.json',{'traceback':traceback.format_exc()})
        if isinstance(exc,saved_tools.CustodyError):stop=True
        row.update(status='STOPPED' if stop else 'FAIL',reason='HOST_OR_OWNED_WORKER_ERROR',error_type=type(exc).__name__)
    row['seconds']=time.perf_counter()-t
    if set(row)-PUBLIC_FIELDS:raise RuntimeError('private_field_in_case_public_projection')
    base.save_json(out/'row-public.json',row)
    return row,stop


def run(out,public,packet=None,dev=False,reuse_from=None,reuse_public=None):
    out=private_path(out);out.mkdir(parents=True,exist_ok=False)
    public=Path(public).absolute()
    if not public.is_relative_to(ROOT/'reports/sw-m1') or '..' in public.parts:
        raise ValueError('M1_public_output_path')
    public.mkdir(parents=True,exist_ok=False)
    # A hard safety gate: no gold/CAD output is produced unless Git ignores it.
    check=subprocess.run(['git','check-ignore','-q',str(out/'job.json')],cwd=ROOT,stdin=subprocess.DEVNULL,capture_output=True)
    if check.returncode:raise RuntimeError('private_outputs_not_ignored_by_Git')
    inputs=dev_inputs(out) if dev else json.loads(private_path(packet).read_text(encoding='utf-8'))
    if not dev and (inputs.get('cohort_sha256')!=COHORT_SHA or len(inputs['entries'])!=60):
        raise ValueError('M1_original_input_packet_binding')
    base.save_json(out/'input-packet.json',inputs)
    rows=[];negative_profiles=set();stopped=False
    reuse=saved_tools.context(reuse_from,reuse_public,inputs) if reuse_from else None
    rechecked=0;reedited=0
    bindings={name:base.digest(ROOT/name) for name in ('tools/sw_m1.py','tools/sw_m1_inputs.py','tools/sw_m1_build.py','tools/sw_m1_judge.py','tools/sw_m1_distance.py','tools/sw_m1_saved.py','tools/sw_m0.py','tools/sw_m0_distance.py','tools/cad_verify_probe.py','tools/cad_verify_v3_probe.py','tools/cad_verify_v4_s3_judges.py')}
    header={'schema':'sw-harness.M1-portability.v1','scope':inputs['scope'],'paid_model_calls':0,
        'source_sha256':bindings,'input_packet_sha256':base.digest(out/'input-packet.json'),
        'original_v4_result_changed':False,'started_at':base.utc()}
    if reuse:header.update(saved_run_manifest_sha256=reuse['source_manifest_sha256'],
        original_source_sha256=reuse['source_sha256'],original_execution_seconds=reuse['summary']['seconds'],
        timing_scope='original_execution_plus_incremental_recheck',new_native_generation=False)
    base.save_json(public/'manifest.json',header)
    lock=base.OUTPUTS/'session.lock'
    with lock.open('x',encoding='utf-8') as f:json.dump({'out':str(out),'at':base.utc()},f)
    tick=time.perf_counter()
    try:
        for entry in inputs['entries']:
            original=reuse['rows'][entry['sequence']-1] if reuse else None
            if original and (original['status']=='NOT_APPLICABLE' or
                    original['status']=='PASS' and original['extra_distance_0_005']=='PASS'
                    and original['SW_editability']=='PASS_ONE_PARAMETER_CHANGE_REBUILD_RESTORE'):
                row=copy.deepcopy(original)
            elif original:
                redo_edit=entry['profile'] in ('rect_prism','rect_stack') and original['SW_editability']!='PASS_ONE_PARAMETER_CHANGE_REBUILD_RESTORE'
                row,stopped=run_case(entry,out/('case-%03d'%entry['sequence']),False,
                    reuse['root']/('case-%03d'%entry['sequence']),redo_edit)
                rechecked+=1;reedited+=int(redo_edit)
                for key in ('seconds','COM_worker_seconds','neutral_worker_seconds'):
                    if key in original or key in row:row[key]=original.get(key,0)+row.get(key,0)
            elif entry['route'] in ('ask','offline'):
                row={key:entry[key] for key in ('sequence','group','route','profile')}
                row.update(status='NOT_APPLICABLE',geometry='NOT_APPLICABLE',extra_distance_0_005='NOT_APPLICABLE',
                    G2='NOT_APPLICABLE',SW_editability='NOT_APPLICABLE',negative_control='NOT_APPLICABLE',
                    original_behavioural_score='NOT_RUN_NO_LLM',original_FreeCAD_native_history='NOT_APPLICABLE_TO_SW_NATIVE',
                    reason='ORIGINAL_QUESTION_TEST' if entry['route']=='ask' else 'ORIGINAL_OFFLINE_CONTRAST',seconds=0.)
            else:
                negative=entry['profile'] not in negative_profiles
                negative_profiles.add(entry['profile'])
                row,stopped=run_case(entry,out/('case-%03d'%entry['sequence']),negative)
            rows.append(row);publish(public/'rows.json',rows);print(json.dumps(row,ensure_ascii=False),flush=True)
            if stopped:break
        summary=dict(header,finished_at=base.utc(),seconds=time.perf_counter()-tick,
            status='STOPPED' if stopped else 'COMPLETE',rows=len(rows),rechecked_saved_cases=rechecked,
            reedited_owned_native_cases=reedited)
        if reuse:summary.update(incremental_recheck_seconds=summary['seconds'],
            seconds=summary['seconds']+reuse['summary']['seconds'])
        summary.update(
            geometry_pass=sum(r['geometry']=='PASS' for r in rows),
            geometry_fail=sum(r['geometry']=='FAIL' for r in rows),
            extra_distance_pass=sum(r['extra_distance_0_005']=='PASS' for r in rows),
            not_applicable=sum(r['status']=='NOT_APPLICABLE' for r in rows),
            build_failed=sum(r['status'] in ('BUILD_FAILED','NOT_BUILDABLE') for r in rows),
            negative_rejected=sum(r['negative_control']=='REJECTED' for r in rows),
            negative_false_pass=sum(r['negative_control']=='FALSE_PASS' for r in rows),
            SW_operational_edit_pass=sum(r['SW_editability']=='PASS_ONE_PARAMETER_CHANGE_REBUILD_RESTORE' for r in rows),
            manual_recovery_required=stopped)
        base.save_json(public/'summary.json',summary)
    finally:
        if not stopped:lock.unlink()
    print(json.dumps(summary,ensure_ascii=False))
    return 2 if stopped else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out');parser.add_argument('--public');parser.add_argument('--inputs')
    parser.add_argument('--dev',action='store_true');parser.add_argument('--com-worker')
    parser.add_argument('--reuse-from');parser.add_argument('--reuse-public')
    a=parser.parse_args()
    try:
        if bool(a.reuse_from)!=bool(a.reuse_public) or a.dev and a.reuse_from:
            raise ValueError('paired_original_saved_run_required')
        raise SystemExit(com_case(a.com_worker) if a.com_worker else run(a.out,a.public,a.inputs,a.dev,a.reuse_from,a.reuse_public))
    except Exception as exc:
        print(json.dumps({'status':'STOPPED','stage':'M1_driver','error_type':type(exc).__name__,'paid_model_calls':0}))
        raise SystemExit(2)
