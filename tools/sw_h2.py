"""Frozen H2 development: baseline ladder, alternating matched pairs, fresh holdout."""
import argparse
import copy
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_h2_runtime as native,sw_h2_fixtures as fixtures,sw_h0_runtime as runtime
from tools import sw_h0_cad as cad,sw_m0 as base,cad_verify_v4_ledger as ledger,cad_spec
from tools.sw_h0_budget import Pool,BudgetJournal
from tools.cad_verify_guard import Stop,quota_snapshot
from tools.sw_m1_inputs import private_path

QUOTA_STOPS=frozenset(('quota_soft_stop','quota_hard_stop','quota_snapshot_missing_or_invalid',
    'quota_snapshot_invalid','quota_snapshot_invalid_time','quota_snapshot_future','quota_snapshot_stale'))
PUBLIC_STOPS=QUOTA_STOPS|frozenset(('H2_trial_stopped','STOP_SW_state_unknown_no_restart',
    'STOP_SW_unavailable_or_documents_open','H2_SW_runtime_changed','H2_model_prompt_envelope_mismatch'))


def cache_match(a,b):
    def valid(row):
        usage=row.get('initial_usage') or {}
        counts=tuple(usage.get(k) for k in ('input_uncached_tokens','cache_read_tokens','cache_write_tokens'))
        if any(type(v) is not int or v<0 for v in counts):return None
        total=sum(counts)
        return (total,counts[1]) if total>0 else None
    x,y=valid(a),valid(b)
    if x is None or y is None:return False,'unknown_or_invalid_initial_cache'
    if 100*abs(x[1]*y[0]-y[1]*x[0])>x[0]*y[0]:return False,'initial_cache_rate_mismatch'
    return True,None


def compare(pairs):
    if len(pairs)!=5:return dict(eligible=False,reason='five_matched_pairs_required')
    a=[p['A'] for p in pairs];b=[p['B'] for p in pairs]
    passed_a=sum(r['passed'] is True for r in a);passed_b=sum(r['passed'] is True for r in b)
    metrics={}
    for name in ('model_calls','active_s'):
        values=[[r.get(name) for r in arm] for arm in (a,b)]
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for arm in values for v in arm):
            return dict(eligible=False,reason='adoption_measurement_missing')
        metrics[name]={'A_mean':sum(values[0])/5,'B_mean':sum(values[1])/5}
    reason=None
    if passed_b-passed_a<2:reason='pass_gain_below_two'
    elif sum(r['critical_invention'] for r in b)>sum(r['critical_invention'] for r in a):reason='critical_invention_increased'
    elif any(v['B_mean']>v['A_mean'] for v in metrics.values()):reason='calls_or_active_time_worse'
    return dict(eligible=reason is None,reason=reason,A_passed=passed_a,B_passed=passed_b,matched_pairs=5,metrics=metrics)


def plan_trials(phase,case,index=0):
    if phase=='calibration':return [dict(label='C'+case+'R'+str(i),case=case,variant='A') for i in range(1,6)]
    if phase=='comparison':return [dict(label='P%02d'%index+arm,case=case,variant=arm) for arm in ('A','B')]
    if phase=='final':return [dict(label='F'+key,case=key,variant='B') for key in case]
    raise Stop('H2_unknown_phase')


def pending_trials(plan,completed):
    """A committed A is never regenerated when resuming its unfinished B."""
    labels=[t['label'] for t in plan]
    if set(completed)-set(labels):raise Stop('H2_unit_unexpected_result')
    seen_pending=False
    for label in labels:
        if label not in completed:seen_pending=True
        elif seen_pending:raise Stop('H2_unit_result_order_corrupt')
    return [t for t in plan if t['label'] not in completed]


class Experiment:
    def __init__(self,experiment,*,continuation=False):
        self.name=experiment;self.out,self.shared,self.entries=native.load(experiment,continuation=continuation)
        self.pub=fixtures.PUBLIC/experiment;self.by_case={e['case']:e for e in self.entries}
        self.identity=ledger.file_sha(self.shared['context_manifest'])
        self.native_uncertain=False

    def check_quota(self):
        record=quota_snapshot(self.shared['quota_snapshot'])
        if record['decision']!='allow':raise Stop(record['decision'])
        return record

    def completed(self,trial):
        path=runtime.PRIVATE/('h2-'+self.name+'-'+trial['label'])/'trial-result.json'
        if not path.exists():return None
        result=ledger.read_json(path)
        prefix=(self.shared.get('resume') or {}).get('prefix',{}).get(trial['label'])
        expected_identity=prefix['old_manifest_sha256'] if prefix else self.identity
        if (result['experiment_manifest_sha256']!=expected_identity or result['label']!=trial['label']
                or result['case']!=trial['case'] or result['variant']!=trial['variant']
                or prefix and ledger.file_sha(path)!=prefix['result_sha256']):raise Stop('H2_saved_trial_binding')
        trial_dir=path.parent
        if ledger.file_sha(trial_dir/'ledger.jsonl')!=result['ledger_sha256']:raise Stop('H2_saved_ledger_changed')
        if result.get('stopped'):
            resume=self.shared.get('resume') or {}
            if not prefix or trial['label']!=resume.get('safe_timeout_label') or result['passed'] is not False:
                raise Stop('H2_saved_trial_stopped')
        return result

    def pool_name(self,index=1):return self.shared['funding']['pools'][index-1]['name']
    def pool_scope(self,index=1):return self.shared['funding']['pools'][index-1]['scope']

    def _funding_used(self):
        used=0
        for item in self.shared['funding']['pools']:
            root=private_path(runtime.PRIVATE/item['name']);path=root/'calls.jsonl'
            if item.get('prefix_bytes'):
                if not path.exists() or ledger.sha(path.read_bytes()[:item['prefix_bytes']])!=item['prefix_sha256']:
                    raise Stop('H2_carry_prefix_changed')
            if not path.exists():
                if item['starting_reserved']:raise Stop('H2_carry_pool_missing')
                continue
            with Pool(root,scope=item['scope']) as pool:
                if pool.summary()['pending_or_unknown_calls']:raise Stop('H2_unsettled_pool_call')
                if pool.used<item['starting_reserved']:raise Stop('H2_carry_balance_reduced')
                used+=pool.used-item['starting_reserved']
        return used

    @contextmanager
    def unit_pool(self,key,phase,trials,completed):
        pending=pending_trials(trials,completed)
        if not pending:
            yield None;return
        needed=3*len(pending)
        unit_path=self.out/('unit-'+key+'.json')
        identity=dict(phase=phase,trials=trials,experiment_manifest_sha256=self.identity)
        if self._funding_used()+needed>self.shared['funding']['maximum_logical_calls']:raise Stop('H2_authorized_call_cap')
        if unit_path.exists():
            plan=ledger.read_json(unit_path)
            if any(plan[k]!=v for k,v in identity.items()):raise Stop('H2_unit_plan_changed')
            index=plan['pool_index']
            if type(index) is not int or not 1<=index<=len(self.shared['funding']['pools']):raise Stop('H2_unit_pool_identity')
            if plan['pool_scope']!=self.pool_scope(index):raise Stop('H2_unit_pool_identity')
            with Pool(runtime.PRIVATE/self.pool_name(index),scope=self.pool_scope(index)) as pool:
                if pool.remaining<needed:raise Stop('H2_planned_unit_budget_lost')
                yield pool
            return
        if completed:raise Stop('H2_results_without_unit_plan')
        for index in range(1,len(self.shared['funding']['pools'])+1):
            with Pool(runtime.PRIVATE/self.pool_name(index),scope=self.pool_scope(index)) as pool:
                if pool.remaining<needed:continue
                ledger.write_json(unit_path,dict(**identity,pool_index=index,pool_scope=pool.scope,
                    reserved_worst_case=needed,planned_at=ledger.utc()))
                yield pool
                return
        raise Stop('H2_authorized_call_cap')

    def trial(self,trial,pool,phase):
        self.check_quota()
        entry=self.by_case[trial['case']]
        if entry['role']!=('holdout' if phase=='final' else 'development'):raise Stop('H2_role_scope')
        out,manifest,entry=native.trial_manifest(self.name,self.shared,entry,trial['label'],trial['variant'],
            pool.root.name,pool.scope)
        try:
            with BudgetJournal(out/'ledger.jsonl',manifest['run'],'H2_'+phase,pool=pool) as journal:
                guard=runtime.Guard(manifest,pool,journal);guard.before_run(entry['max_calls'])
                ledger.write_json(out/'CLAIM.json',dict(manifest_sha256=manifest['manifest_sha256'],cap=40,
                    pool_scope=pool.scope,at=ledger.utc(),evidence_mode='live'))
                row,stopped,_=native.isolated_execute(self.name,entry,out/'episode',manifest,journal,pool)
        finally:
            self.native_uncertain|=bool(manifest.get('_native_uncertain'))
        timeout_proof=manifest.get('_known_episode_timeout')
        if stopped=='H2_closed_SW_neutral_timeout' and timeout_proof:
            if row['passed'] is not False:raise Stop('H2_timeout_cannot_pass')
            stopped=None
            row.update(episode_timeout=True,timeout_certificate=timeout_proof,failure_class='neutral_worker_timeout')
        if stopped:ledger.write_json(out/'stop-private.json',dict(reason=stopped))
        events=list(ledger.rows(out/'ledger.jsonl'))
        measurements=native.initial_measurement(events,out/'episode')
        if not measurements['initial_model_input_verified'] and not stopped:stopped='H2_model_prompt_envelope_mismatch'
        result=dict(row,**measurements,label=trial['label'],case=trial['case'],variant=trial['variant'],phase=phase,
            experiment_manifest_sha256=self.identity,manifest_sha256=manifest['manifest_sha256'],
            ledger_sha256=ledger.file_sha(out/'ledger.jsonl'),stopped=bool(stopped),
            tokens={k:ledger.nullable_total((e.get('usage') or {}).get('values',{}).get(k)
                for e in events if e.get('event')=='attempt_finished' and e.get('operation')=='model')['total'] for k in ledger.USAGE_KEYS})
        # Producer error strings are not a privacy boundary. Keep raw errors private.
        result['failure_class']='candidate_rejected' if result.get('failure_class') else None
        ledger.write_json(out/'trial-result.json',result)
        ledger.write_json(self.pub/(trial['label']+'.json'),result)
        print(json.dumps({k:result[k] for k in ('label','variant','completed','passed','model_calls','cad_attempts','repair_calls','active_s')}),flush=True)
        if stopped:
            if self.native_uncertain:raise Stop('STOP_SW_state_unknown_no_restart')
            raise Stop(stopped if stopped in PUBLIC_STOPS else 'H2_trial_stopped')
        if result['initial_cwd']!=self.shared['generation_cwd']:raise Stop('H2_generation_cwd_mismatch')
        return result

    def unit(self,key,phase,trials):
        completed={t['label']:value for t in trials if (value:=self.completed(t)) is not None}
        with self.unit_pool(key,phase,trials,completed) as handle:
            if handle is not None and native.solidworks_identity()!=self.shared['solidworks']:raise Stop('H2_SW_runtime_changed')
            if handle is not None:
                for trial in pending_trials(trials,completed):completed[trial['label']]=self.trial(trial,handle,phase)
        return [completed[t['label']] for t in trials]

    def run(self):
        selected=None;calibration=[];matched=[];pairs=[];decision=None
        try:
            for case in self.shared['development_ids']:
                rows=self.unit('calibration-'+case,'calibration',plan_trials('calibration',case))
                passed=sum(r['passed'] is True for r in rows);calibration.append(dict(case=case,passed=passed,n=5))
                if passed in (2,3):selected=case;break
            ledger.write_json(self.out/'calibration.json',dict(rows=calibration,selected=selected)) if not (self.out/'calibration.json').exists() else None
            if selected is None:return self.finish('baseline_difficulty_gate_not_met',calibration,[],None,[])
            for index in range(1,11):
                a,b=self.unit('pair-%02d'%index,'comparison',plan_trials('comparison',selected,index))
                if a['initial_payload_sha256'] is None or a['initial_payload_sha256']!=b['initial_payload_sha256']:
                    raise Stop('H2_pair_request_or_runtime_changed')
                eligible,reason=cache_match(a,b)
                pair=dict(index=index,A=a,B=b,cache_matched=eligible,excluded_reason=reason);pairs.append(pair)
                if eligible:matched.append(pair)
                if len(matched)==5:break
            decision=compare(matched)
            if not decision['eligible']:return self.finish(decision['reason'],calibration,pairs,decision,[])
            final=self.unit('final','final',plan_trials('final',self.shared['holdout_ids']))
            adopted=all(r['passed'] is True for r in final)
            return self.finish('adopt_candidate' if adopted else 'fresh_holdout_failed',calibration,pairs,decision,final)
        except Stop as exc:
            if str(exc)!='H2_authorized_call_cap':raise
            return self.finish('authorized_call_budget_exhausted',calibration,pairs,decision,[])

    def finish(self,reason,calibration,pairs,decision,final):
        trials=[ledger.read_json(p) for p in self.pub.glob('*.json') if p.name.startswith(('CH2D','P0','P10','FH2H'))]
        report=dict(schema='harness2.solidworks.skill.result.v1',experiment=self.name,at=ledger.utc(),
            experiment_manifest_sha256=self.identity,status='complete',reason=reason,adopted=reason=='adopt_candidate',
            calibration=calibration,pair_count=len(pairs),matched_pairs=sum(p['cache_matched'] for p in pairs),
            excluded_pair_indices=[p['index'] for p in pairs if not p['cache_matched']],comparison=decision,
            final_holdout_passed=sum(r['passed'] is True for r in final),final_holdout_n=len(final),
            total_reserved_model_calls=sum(r['model_calls'] for r in trials),wall_s=sum(r['wall_s'] for r in trials),
            active_s=sum(r['active_s'] for r in trials),statistical_confirmation=False,
            model=self.shared['generator']['model'],thinking=self.shared['generator']['thinking'])
        ledger.write_json(self.out/'result.json',report);ledger.write_json(self.pub/'result.json',report)
        print(json.dumps(report),flush=True)
        return report


def run(experiment,*,continuation=False):
    experiment=Experiment(experiment,continuation=continuation)
    lock=base.OUTPUTS/'session.lock';own=experiment.out/'controller.lock';unsafe=False
    with own.open('x') as file:
        file.write(json.dumps({'pid':os.getpid(),'scope':'H2-skill-text-only'}));file.flush();os.fsync(file.fileno())
    locked=False
    try:
        if (experiment.out/'result.json').exists():return ledger.read_json(experiment.out/'result.json')
        experiment.check_quota()
        with lock.open('x') as file:json.dump(dict(scope='H2-skill-text-only',experiment=experiment.name,pid=os.getpid()),file)
        locked=True
        health=experiment.out/('health-'+str(time.time_ns()));health.mkdir()
        job=health/'worker-job.json';ledger.write_json(job,dict(out=str(health),healthcheck=True))
        code,_,_=cad.child([str(base.SW_PYTHON),'-B',str(ROOT/'tools/sw_h0_worker.py'),str(job)],health,'health',30,SW=True)
        if code:unsafe=True;raise Stop('STOP_SW_unavailable_or_documents_open')
        return experiment.run()
    except BaseException as exc:
        unsafe=unsafe or experiment.native_uncertain
        ledger.write_json(experiment.out/('stop-private-'+str(time.time_ns())+'.json'),
            dict(error_type=type(exc).__name__,traceback=traceback.format_exc()))
        reason=str(exc) if isinstance(exc,Stop) and str(exc) in PUBLIC_STOPS else 'H2_action_stopped'
        event=dict(status='STOPPED',at=ledger.utc(),reason=reason,manual_SW_recovery_required=unsafe)
        ledger.write_json(experiment.pub/('stop-'+str(time.time_ns())+'.json'),event)
        with (ROOT/'H0_PROGRESS.md').open('a',encoding='utf-8') as file:
            file.write('\n- H2停止 '+json.dumps(event,ensure_ascii=False)+'\n')
        raise
    finally:
        if locked and not unsafe:lock.unlink()
        own.unlink()


def smoke(experiment):
    """Explicit mock only; sealed independent fixture, real SW/FreeCAD/R1."""
    native.prepare(experiment,smoke=True)
    out,entries,_=native.context(experiment)
    shared=ledger.read_json(out/'preflight-manifest.json')
    entry=next(e for e in entries if e['role']=='development')
    spec=ledger.read_json(entry['control_spec_path']);wrong=copy.deepcopy(spec);wrong['pockets'][0]['depth']+=.1
    responses=iter((wrong,spec));submissions=[]
    def process(argv,captures,*,cwd,timeout):
        if any(value.startswith('@') for value in argv):raise Stop('H2_smoke_file_header_not_blind')
        packet=json.loads(argv[-1])
        if set(packet)!={'request','runtime_data'} or packet['request']!=entry['gold']['description']:
            raise Stop('H2_smoke_request_binding')
        data=json.dumps(packet['runtime_data'])
        if any(key in data for key in ('target_mm3','description_sha256','provenance','gold_path','acceptance','target_volume','parameters')):
            raise Stop('H2_smoke_oracle_leak')
        if str(cwd)!=shared['generation_cwd'] or '--no-tools' not in argv:raise Stop('H2_smoke_invocation')
        submissions.append(ledger.sha(native.canonical(packet)))
        user=dict(type='message_end',message=dict(role='user',content=[dict(type='text',text=argv[-1])]))
        captures['stdout'].feed((json.dumps(user)+'\n').encode())
        event=dict(type='message_end',message=dict(role='assistant',provider='openai-codex',model='gpt-6.1-sol',
            content=[dict(type='text',text=cad_spec.canonical(next(responses)))],stopReason='stop'))
        captures['stdout'].feed((json.dumps(event)+'\n').encode());return 0
    trial_dir,manifest,entry=native.trial_manifest(experiment,shared,entry,'SMOKE1','B','unit-mock','H2-unit-mock')
    lock=base.OUTPUTS/'session.lock';unsafe=True
    with lock.open('x') as file:json.dump(dict(scope='H2-unit-mock',pid=os.getpid()),file)
    try:
        with Pool(trial_dir/'mock-pool',scope='H2-unit-mock') as pool:
            with BudgetJournal(trial_dir/'ledger.jsonl',manifest['run'],'H2_unit_mock',pool=pool) as journal:
                row,stopped,report=native.isolated_execute(experiment,entry,trial_dir/'episode',manifest,journal,pool,process=process)
            attempts=report['attempts'];costs=ledger.summarize(trial_dir/'ledger.jsonl')
            passed=bool(not stopped and row['passed'] and len(submissions)==2 and len(attempts)==2
                and attempts[0]['result']['geometry_ok'] is False and attempts[-1]['result']['geometry_ok'] is True
                and report['repair_calls']==1 and report['parse_repairs']==0
                and costs['physical_model_attempts']==2 and costs['cad_attempts']==2
                and costs['capture']['missing_or_partial']==0)
            unsafe=bool(manifest.get('_native_uncertain'))
            public=dict(status='PASS' if passed else 'FAIL',evidence_mode='unit_mock_with_real_SW_and_FreeCAD',
                live_model_calls=0,mock_responses=len(submissions),real_CAD_attempts=len(attempts),
                wrong_spec_rejected=bool(attempts and attempts[0]['result']['geometry_ok'] is False),
                original_driver_repair_calls=report['repair_calls'],fixture_provenance='fixture',
                source_admission_only=True,seconds=row['wall_s'],captured_streams=costs['capture']['complete'])
            ledger.write_json(fixtures.PUBLIC/experiment/'preflight-smoke.json',public)
            print(json.dumps(public),flush=True)
            if not passed:raise Stop('H2_smoke_failed')
    finally:
        if not unsafe:lock.unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run','smoke','freeze-continuation','run-continuation'));parser.add_argument('--experiment',required=True)
    args=parser.parse_args()
    try:
        if args.action in ('freeze','freeze-continuation'):
            print(json.dumps(native.prepare(args.experiment,continuation=args.action=='freeze-continuation')),flush=True)
        elif args.action=='smoke':smoke(args.experiment)
        else:run(args.experiment,continuation=args.action=='run-continuation')
    except Exception as exc:
        # No arbitrary native/Gold exception text is printed.
        reason=str(exc) if isinstance(exc,Stop) and str(exc) in PUBLIC_STOPS else 'H2_action_stopped'
        print(json.dumps(dict(status='STOPPED',error_type=type(exc).__name__,reason=reason)),flush=True)
        raise SystemExit(2)
