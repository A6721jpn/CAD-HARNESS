"""SolidWorks H0: original policy driver, original score, development cap40."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import socket
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base,cad_verify_v4_ledger as ledger,cad_verify_v4_agent as agent
from tools import cad_verify_v4_live as live,cad_verify_v4_freeze as freezing,eval_verify
from tools import sw_h0_runtime as runtime,sw_h0_cad as cad
from tools.sw_h0_budget import Pool,BudgetJournal
from tools.sw_m1_inputs import private_path
from tools.cad_verify_guard import Stop


def execute(entry,episode,manifest,journal,pool,*,process=None):
    text=Path(entry['request_path']).read_bytes()
    if ledger.sha(text)!=entry['request_sha256']:raise Stop('H0_request_binding')
    request=text.decode('utf-8')
    skill=agent.bundle(ROOT)
    if ledger.sha(skill)!=manifest['skill_sha256']:raise Stop('H0_skill_binding')
    episode.mkdir(parents=True,exist_ok=False)
    live.setup_episode(episode,skill,ROOT)
    guard=runtime.Guard(manifest,pool,journal)
    transport=runtime.Transport(manifest,journal,episode,request,skill,guard,entry=entry,process=process)
    transport.episode=entry['id'];transport.route=entry['route'];transport.scored=True
    adapter=runtime.SafeAdapter(skill,request)
    core=agent.adapted_driver(adapter,transport)
    # Only the isolated dependency binding changes; original driver source,
    # state machine, policy slots/times and existing scoring are not edited.
    core.__globals__['cad_spec']=cad.Compiler()
    tick=time.monotonic();active_tick=transport.clock();before=pool.used
    journal.append('episode_started',episode_id=entry['id'],route=entry['route'],sequence=entry['sequence'])
    report,code=core('request-mvp1',manifest['generator']['omp'],request,entry['gold_path'],
        root=episode,runner=transport,clock=transport.clock,guard=guard,route=entry['route'],
        max_calls=entry['max_calls'],rubric=entry['card'].get('rubric'),provider_retry=True)
    report['_rubric']=entry['card'].get('rubric')
    wall=time.monotonic()-tick;active=transport.clock()-active_tick
    scored=live.score_episode(entry,report,'H0-%03d'%entry['sequence'],wall_s=wall,active_s=active)
    failure=eval_verify.harness_failure(report)
    stopped=guard.stop_reason or transport.fatal or failure
    journal.append('episode_finished',episode_id=entry['id'],sequence=entry['sequence'],
        passed=scored['passed'],wall_s=wall,active_s=active,driver_status=report['status'],
        observed_overload_recoveries=transport.recoveries)
    from tools import sw_h0_report as public
    row=public.row(entry,report,scored,wall_s=wall,active_s=active,model_calls=pool.used-before)
    return row,stopped,report


def load_manifest(run):
    if re.fullmatch(r'[A-Za-z0-9_-]{1,96}',run) is None:raise ValueError('H0_run_name')
    out=private_path(runtime.PRIVATE/run)
    manifest=ledger.read_json(out/'manifest.json')
    expected=ledger.read_json(out/'SHA256.json')['manifest_sha256']
    if ledger.file_sha(out/'manifest.json')!=expected:raise Stop('H0_manifest_binding')
    if (manifest['schema']!='harness2.solidworks.H0.freeze.v2' or manifest['run']!=run
            or manifest['charged_call_cap']!=40 or manifest['scope'] not in ('H0-development40','H0-batch40')
            or (manifest['budget_pool'],manifest['budget_scope'])!=runtime.budget_identity(run,manifest['scope']=='H0-batch40')
            or manifest['selected']!=runtime.selection(manifest['selected'])
            or manifest['generator']['model']!=freezing.MODEL or manifest['generator']['thinking']!=freezing.THINKING):
        raise Stop('H0_authorization_binding')
    manifest['manifest_sha256']=expected
    return out,manifest


def run(run):
    from tools import sw_h0_report as public
    out,manifest=load_manifest(run);pub=runtime.PUBLIC/run
    entries=ledger.read_json(out/'inputs-private.json')
    rows=[];stopped=None;t=time.monotonic();accounting=None
    lock=base.OUTPUTS/'session.lock';locked=False;unsafe=False
    with Pool(runtime.PRIVATE/manifest['budget_pool'],scope=manifest['budget_scope']) as pool:
        with BudgetJournal(out/'ledger.jsonl',run,'H0_development',pool=pool) as journal:
            prior_reserved=pool.used
            guard=runtime.Guard(manifest,pool,journal)
            try:
                guard.check()
                with lock.open('x') as file:json.dump({'run':run,'scope':manifest['scope']},file)
                locked=True
                ledger.write_json(out/'CLAIM.json',dict(manifest_sha256=manifest['manifest_sha256'],
                    scope=manifest['scope'],budget_pool=manifest['budget_pool'],at=ledger.utc(),cap=40))
                health=out/'healthcheck';health.mkdir()
                job=health/'worker-job.json';ledger.write_json(job,dict(out=str(health),healthcheck=True))
                code,_,_=cad.child([str(base.SW_PYTHON),'-B',str(ROOT/'tools/sw_h0_worker.py'),str(job)],health,'health',30,SW=True)
                if code:raise Stop('STOP_SW_unavailable_or_documents_open')
                journal.append('run_started',manifest_sha256=manifest['manifest_sha256'],
                    evidence_mode='live',selected=manifest['selected'],budget_pool=manifest['budget_pool'],call_cap=40)
                for entry in entries:
                    if entry['sequence'] not in manifest['selected']:continue
                    guard.before_run(entry['max_calls'])
                    row,reason,_=execute(entry,out/('episode-%03d'%entry['sequence']),manifest,journal,pool)
                    rows.append(row)
                    ledger.write_json(pub/('row-%03d.json'%entry['sequence']),row)
                    print(json.dumps(row),flush=True)
                    if reason:stopped=reason;break
                    guard.check()
            except BaseException as exc:
                stopped=guard.stop_reason or (str(exc) if isinstance(exc,Stop) else 'H0_host_or_storage_error')
                ledger.write_json(out/'host-error-private.json',dict(error_type=type(exc).__name__,traceback=traceback.format_exc()))
            finally:
                unsafe=bool(stopped and any(word in stopped for word in ('SW_nonresponse','SW_state_unknown','CAD_backend_stopped')))
                if locked and not unsafe:lock.unlink()
                accounting=pool.summary()
                elapsed=time.monotonic()-t
                events=list(ledger.rows(out/'ledger.jsonl'))
                excluded=sum(e.get('wall_s',0) for e in events if e['event']=='attempt_finished' and e.get('provider_rejected') is True)
                excluded+=sum(e.get('actual_s',0) for e in events if e['event']=='wait_finished')
                journal.append('run_finished',wall_s=elapsed,active_s=elapsed-excluded,wall_missing_reason=None,
                    stopped_reason=stopped,conservative_reserved_calls=accounting['conservative_reserved_calls'])
    complete=public.complete_rows(entries,rows)
    ledger.write_json(pub/'rows.json',complete)
    costs=ledger.summarize(out/'ledger.jsonl')
    ledger.write_json(out/'accounting-private.json',costs)
    if costs['conservative_reserved_calls']!=accounting['conservative_reserved_calls']-prior_reserved:
        raise Stop('H0_cost_journal_binding')
    recoveries=sum(e.get('observed_overload_recoveries',0) for e in ledger.rows(out/'ledger.jsonl'))
    summary=dict(scope=manifest['scope'],budget_pool=manifest['budget_pool'],status='STOPPED' if stopped else 'COMPLETE',
        selected=len(manifest['selected']),attempted=len(rows),completed=sum(r['completed'] for r in rows),
        passed=sum(r['passed'] is True for r in rows),not_run=sum(not r['completed'] for r in complete),
        wall_s=time.monotonic()-t,stopped_reason=public.safe_code(stopped),
        manifest_sha256=manifest['manifest_sha256'],accounting=accounting,
        tokens=costs['all_work']['tokens'],price=None,price_missing_reason='no_applicable_rate_source_or_invoice',
        overload_robustness='observed_recovery' if recoveries else 'UNVERIFIED',SW_manual_recovery_required=unsafe)
    ledger.write_json(pub/'summary.json',summary)
    public.write_summary(ROOT/'H0_SUMMARY.md',complete,accounting,
        manifest_sha256=manifest['manifest_sha256'],stopped_reason=stopped)
    print(json.dumps(summary),flush=True)
    return 2 if stopped else 0


def smoke(run):
    """Public development fixture; two mock responses, real SW and SDK judges."""
    from tools import sw_h0_report as public
    out=private_path(runtime.PRIVATE/run);out.mkdir(parents=True,exist_ok=False)
    pub=runtime.PUBLIC/run;pub.mkdir(parents=True,exist_ok=False)
    gold_path=ROOT/'design/cad-harness-verify-v3/test/G6/gold.json'
    gold=ledger.read_json(gold_path)
    spec={k:copy.deepcopy(gold[k]) for k in ('regions','pockets','holes','finish')}
    spec['regions']=[dict(bounds=copy.deepcopy(gold['parameters']['bbox']))]
    for hole in spec['holes']:hole.pop('through',None)
    for pocket in spec['pockets']:pocket.pop('sharp',None)
    spec.update(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world')
    from tools.cad_spec import validate_spec,canonical
    spec=validate_spec(spec);wrong=copy.deepcopy(spec);wrong['pockets'][0]['depth']+=.1
    responses=iter((wrong,spec));submitted=[]
    def process(argv,captures,**kwargs):
        payload_path=next(Path(v[1:]) for v in argv if v.startswith('@'))
        payload=ledger.read_json(payload_path)
        # Fixture-only smoke asserts the actual submitted envelope, not source text.
        if set(payload)!={'request','runtime_data'} or payload['request']!=gold['description']:
            raise Stop('smoke_request_payload_binding')
        forbidden=('target_mm3','description_sha256','provenance','gold_path','acceptance','target_volume')
        if any(key in json.dumps(payload['runtime_data']) for key in forbidden):raise Stop('smoke_oracle_leak')
        submitted.append(ledger.file_sha(payload_path))
        final=canonical(next(responses))
        event=dict(type='message_end',message=dict(role='assistant',provider='openai-codex',model='gpt-6.1-sol',
            content=[dict(type='text',text=final)],stopReason='stop'))
        captures['stdout'].feed((json.dumps(event)+'\n').encode());return 0
    entry=dict(sequence=23,id='independent-H0-smoke',case='G6',group='geometry',round=1,route='spec',
        min_calls=1,max_calls=3,profile='rect_prism',gold=gold,gold_path=str(gold_path),
        gold_sha256=ledger.file_sha(gold_path),request_path=str(out/'request.txt'),
        request_sha256=ledger.sha(gold['description'].encode()),card={},selected=True)
    (out/'request.txt').write_text(gold['description'],encoding='utf-8')
    entries=[entry];ledger.write_json(out/'inputs-private.json',entries)
    skill=agent.bundle(ROOT)
    manifest=dict(run=run,files={},input_files={str(gold_path):entry['gold_sha256']},
        inputs_packet_sha256=ledger.file_sha(out/'inputs-private.json'),runtime_files={},
        host=dict(hostname=socket.gethostname()),OMP_PROFILE=os.environ.get('OMP_PROFILE'),
        CAD_HARNESS_SW_PID=os.environ.get('CAD_HARNESS_SW_PID'),
        quota_snapshot='C:/dev/v4-ops/quota.json',skill_sha256=ledger.sha(skill),
        generator=dict(omp=str(ROOT/'tools/sw_h0.py'),sha256=ledger.file_sha(ROOT/'tools/sw_h0.py'),
            version='UNIT-MOCK',model=freezing.MODEL,thinking=freezing.THINKING))
    ledger.write_json(out/'manifest.json',manifest);manifest['manifest_sha256']=ledger.file_sha(out/'manifest.json')
    lock=base.OUTPUTS/'session.lock';unsafe=False
    with lock.open('x') as file:json.dump({'scope':'H0-unit-mock-smoke'},file)
    try:
        with Pool(out/'mock-pool') as pool:
            with BudgetJournal(out/'ledger.jsonl',run,'H0_unit_mock',pool=pool) as journal:
                row,stopped,report=execute(entry,out/'episode-023',manifest,journal,pool,process=process)
                native=report['attempts']
                journal.append('run_finished',wall_s=row['wall_s'],active_s=row['active_s'],wall_missing_reason=None)
                costs=ledger.summarize(out/'ledger.jsonl')
                okay=bool(not stopped and row['passed'] and len(submitted)==2 and len(native)==2
                    and native[0]['result']['geometry_ok'] is False and native[-1]['result']['geometry_ok'] is True
                    and report['repair_calls']==1 and report['parse_repairs']==0
                    and eval_verify.result_pass(native[-1]['result'])
                    and costs['physical_model_attempts']==2 and costs['cad_attempts']==2
                    and costs['capture']['missing_or_partial']==0)
                unsafe=bool(stopped)
                summary=dict(status='PASS' if okay else 'FAIL',evidence_mode='unit_mock_with_real_CAD',
                    live_model_calls=0,mock_responses=len(submitted),real_CAD_attempts=len(native),
                    wrong_spec_rejected=bool(native and native[0]['result']['geometry_ok'] is False),
                    frozen_driver_repair_calls=report['repair_calls'],passed=bool(row['passed']),
                    captured_transport_streams=costs['capture']['complete'],
                    stopped_reason=public.safe_code(stopped),seconds=row['wall_s'])
                ledger.write_json(pub/'summary.json',summary);ledger.write_json(pub/'row.json',row)
                print(json.dumps(summary),flush=True)
                return 0 if okay else 1
    finally:
        if not unsafe:lock.unlink()


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','run','smoke'));p.add_argument('--run',required=True)
    p.add_argument('--new-batch',action='store_true',help='Use a new independent <=40-call pool; never reset development40')
    p.add_argument('--sequences',nargs='+',type=int,help='Original H0 subset in original order; freeze before calls')
    args=p.parse_args()
    if re.fullmatch(r'[A-Za-z0-9_-]{1,96}',args.run) is None:raise ValueError('H0_run_name')
    if args.action!='prepare' and (args.new_batch or args.sequences is not None):p.error('batch selection is prepare-only')
    if args.action=='prepare':
        manifest=runtime.freeze(args.run,new_batch=args.new_batch,sequences=args.sequences)
        print(json.dumps(dict(status='PREPARED',selected=len(manifest['selected']),cap=40,
            budget_pool=manifest['budget_pool'],live_model_calls=0,
            model=manifest['generator']['model'],thinking=manifest['generator']['thinking'])));return 0
    return run(args.run) if args.action=='run' else smoke(args.run)


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'status':'STOPPED','error_type':type(exc).__name__,
            'reason':str(exc) if isinstance(exc,Stop) else 'H0_private_detail_retained',
            'failure_site':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}
                for f in traceback.extract_tb(exc.__traceback__)]}));raise SystemExit(2)
