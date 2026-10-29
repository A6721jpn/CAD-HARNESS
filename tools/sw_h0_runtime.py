"""H0's frozen input lease, model isolation, quota guard and SW transport."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import threading
import time

from tools import cad_verify_v4_live as live,cad_verify_v4_agent as agent
from tools import cad_verify_v4_freeze as freezing,cad_verify_v4_ledger as ledger,cad_spec
from tools import sw_m0 as base,sw_m1_inputs as inputs,sw_h0_cad as cad
from tools.cad_verify_guard import Stop,quota_snapshot
from tools.sw_h0_budget import SCOPE as DEVELOPMENT_SCOPE

PRIVATE=inputs.PRIVATE/'h0'
PUBLIC=base.ROOT/'reports/sw-h0'
SELECTED=(23,24,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45)
MODEL_CONFIG=copy.deepcopy(live.OMP_CONFIG)
MODEL_CONFIG.update(enabledProviders=['openai-codex'],disabledProviders=[],enabledModels=[freezing.MODEL])


def _scoped_transport():
    # Respect the user's explicit Codex authorization only for this invocation.
    # Do not mutate global provider preferences or the original v4 module.
    spec=importlib.util.spec_from_file_location('tools._sw_h0_live_transport',live.__file__)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OMP_CONFIG=MODEL_CONFIG
    return module.LiveTransport


_LiveTransport=_scoped_transport()


def original_inputs():
    packet=inputs.admitted()  # Existing full original60/card/file-hash admission.
    metadata=ledger.read_json(inputs.OLD_LAUNCH);argv=metadata['argv']
    sealed=Path(argv[argv.index('--sealed-input')+1])
    if ledger.file_sha(sealed)!=inputs.COHORT_SHA:raise Stop('H0_original_cohort_binding')
    cohort=ledger.read_json(sealed)
    entries=[]
    for original,measured in zip(cohort['entries'],packet['entries']):
        if any(original[k]!=measured[k] for k in ('sequence','group','route')):raise Stop('H0_original_order_binding')
        row=dict(original,**{k:v for k,v in measured.items() if k not in original})
        row.update(card=measured['card'],gold=measured['gold'],gold_path=measured['gold_path'],
            gold_sha256=measured['gold_sha256'],profile=measured['profile'],card_sha256=measured['card_sha256'])
        row['request_path']=str(live.safe_input(sealed.parent,original['request']))
        row['request_sha256']=cohort['files'][original['request']]
        if row['sequence'] in SELECTED:
            expected='spec' if row['sequence']<39 else 'ask'
            if row['route']!=expected or row['max_calls']!=(3 if expected=='spec' else 1):raise Stop('H0_subset_card_drift')
        row['selected']=row['sequence'] in SELECTED
        entries.append(row)
    bound={str(live.safe_input(sealed.parent,name)):digest for name,digest in cohort['files'].items()}
    bound[str(sealed)]=inputs.COHORT_SHA
    return entries,bound


def selection(sequences=None):
    selected=list(SELECTED) if sequences is None else list(sequences)
    if not selected or selected!=[n for n in SELECTED if n in selected]:
        raise Stop('H0_subset_order_or_scope')
    return selected


def budget_identity(run,new_batch=False):
    if re.fullmatch(r'[A-Za-z0-9_-]{1,96}',run) is None:raise Stop('H0_run_name')
    return ('batch-'+run,'harness2-solidworks-H0-batch40-'+run) if new_batch else ('development40',DEVELOPMENT_SCOPE)


def freeze(run,*,new_batch=False,sequences=None):
    selected=selection(sequences);pool_name,pool_scope=budget_identity(run,new_batch)
    out=inputs.private_path(PRIVATE/run);out.mkdir(parents=True,exist_ok=False)
    entries,bound=original_inputs()
    for entry in entries:entry['selected']=entry['sequence'] in selected
    policy_sha=freezing._policy(base.ROOT,base.ROOT/'design/cad-harness-verify-v4/policy.json')
    files=freezing.bindings(base.ROOT);files['H0_PLAN.md']=ledger.file_sha(base.ROOT/'H0_PLAN.md')
    generator=dict(model=freezing.MODEL,thinking=freezing.THINKING,**freezing._executable('omp'))
    if not all(generator.get(k) for k in ('omp','version','sha256')):raise Stop('H0_omp_identity_unavailable')
    host=freezing._host()
    if host['hostname']!=freezing.REQUIRED_HOST:raise Stop('H0_wrong_host')
    skill=agent.bundle(base.ROOT)
    ledger.write_json(out/'inputs-private.json',entries)
    manifest=dict(schema='harness2.solidworks.H0.freeze.v2',scope='H0-batch40' if new_batch else 'H0-development40',run=run,
        charged_call_cap=40,selected=selected,budget_pool=pool_name,budget_scope=pool_scope,policy_sha256=policy_sha,files=files,
        input_files=bound,inputs_packet_sha256=ledger.file_sha(out/'inputs-private.json'),
        cohort_sha256=inputs.COHORT_SHA,skill_sha256=ledger.sha(skill),
        generator_config_sha256=ledger.sha(json.dumps(MODEL_CONFIG,sort_keys=True).encode()),
        generator=generator,host=host,quota_snapshot='C:/dev/v4-ops/quota.json',
        authorization='USER 2026-10-26 H0 development40; USER 2026-10-28 01:18/01:30 independent Codex batches <=50; each pool conservatively cap40',
        OMP_PROFILE=os.environ.get('OMP_PROFILE'),
        CAD_HARNESS_SW_PID=os.environ.get('CAD_HARNESS_SW_PID'),
        runtime_files={str(p):ledger.file_sha(p) for p in (base.SW_PYTHON,base.FC_BIN/'python.exe')})
    ledger.write_json(out/'manifest.json',manifest)
    ledger.write_json(out/'SHA256.json',dict(manifest_sha256=ledger.file_sha(out/'manifest.json')))
    pub=PUBLIC/run;pub.mkdir(parents=True,exist_ok=False)
    public={k:manifest[k] for k in ('schema','scope','run','charged_call_cap','selected','budget_pool','budget_scope','policy_sha256','cohort_sha256','skill_sha256')}
    public.update(manifest_sha256=ledger.file_sha(out/'manifest.json'),source_sha256=files,
        generator={k:generator[k] for k in ('model','thinking','version','sha256')},
        generator_access={k:MODEL_CONFIG[k] for k in ('enabledProviders','disabledProviders','enabledModels')},
        authorization_recorded=True,live_model_calls=0,prepared_at=ledger.utc())
    ledger.write_json(pub/'manifest-public.json',public)
    return manifest


class Guard:
    def __init__(self,manifest,pool,journal):
        self.manifest,self.pool,self.journal=manifest,pool,journal
        self.clock=live.WallClock();self.deadline=None
        self.calls=0;self.episode_start=0;self.episode_cap=0;self.stop_reason=None

    def check(self):
        try:
            if socket.gethostname()!=self.manifest['host']['hostname']:raise Stop('H0_host_changed')
            if os.environ.get('OMP_PROFILE')!=self.manifest['OMP_PROFILE']:raise Stop('H0_generator_environment_changed')
            if os.environ.get('CAD_HARNESS_SW_PID')!=self.manifest.get('CAD_HARNESS_SW_PID'):
                raise Stop('H0_SW_selection_environment_changed')
            maps=[{str(base.ROOT/k):v for k,v in self.manifest['files'].items()},
                self.manifest['input_files'],self.manifest['runtime_files'],
                {self.manifest['generator']['omp']:self.manifest['generator']['sha256']}]
            own=PRIVATE/self.manifest['run']
            maps.append({str(own/'manifest.json'):self.manifest['manifest_sha256'],
                str(own/'inputs-private.json'):self.manifest['inputs_packet_sha256']})
            for files in maps:
                if any(ledger.file_sha(p)!=digest for p,digest in files.items()):raise Stop('H0_frozen_file_changed')
            record=quota_snapshot(self.manifest['quota_snapshot'])
            self.journal.append('quota_checked',**record)
            if record['decision']!='allow':raise Stop(record['decision'])
            return record
        except (OSError,ValueError,KeyError) as exc:
            self.stop_reason=str(exc) if isinstance(exc,Stop) else 'H0_guard_identity_or_IO_failure'
            raise Stop(self.stop_reason) from None

    def remaining(self,reserve=30):return math.inf

    def before_run(self,minimum_calls=0):
        self.check()
        if self.pool.remaining<minimum_calls:
            self.stop_reason='insufficient_call_budget';raise Stop(self.stop_reason)

    def before_episode(self,maximum):
        self.before_run(maximum);self.episode_start=self.calls;self.episode_cap=maximum

    def before_call(self):
        self.before_run(1)
        if self.calls-self.episode_start>=self.episode_cap:raise Stop('episode_call_limit')
        self.calls+=1
        return self.check()


def model_process(guard):
    """Production model process: full streams; observe quota during long calls."""
    def execute(argv,captures,*,cwd,timeout):
        if argv[0]!=guard.manifest['generator']['omp'] or '--no-tools' not in argv:raise Stop('H0_model_invocation_binding')
        errors=[];reason=None;deadline=time.monotonic()+timeout
        p=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
        def drain(key):
            try:
                for raw in iter(lambda:getattr(p,key).read(8192),b''):captures[key].feed(raw)
            except BaseException as exc:errors.append(exc)
        threads=[threading.Thread(target=drain,args=(key,),daemon=True) for key in ('stdout','stderr')]
        for thread in threads:thread.start()
        next_quota=time.monotonic()+5
        try:
            while True:
                if errors:raise OSError('H0_capture_failed')
                left=deadline-time.monotonic()
                if left<=0:raise subprocess.TimeoutExpired(argv,timeout)
                try:p.wait(timeout=min(1,left));break
                except subprocess.TimeoutExpired:pass
                if time.monotonic()>=next_quota:
                    record=quota_snapshot(guard.manifest['quota_snapshot'])
                    guard.journal.append('quota_checked',**record)
                    if record['decision']!='allow':
                        guard.stop_reason=record['decision'];raise Stop(guard.stop_reason)
                    next_quota=time.monotonic()+5
        except BaseException:
            # argv is the pinned, tool-less OMP process, never the SW process.
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=False)
            p.kill();p.wait(timeout=10);raise
        finally:
            for thread in threads:thread.join(timeout=5)
            if any(thread.is_alive() for thread in threads) or errors:raise OSError('H0_capture_drain_failed')
        return p.returncode
    return execute


class SafeAdapter(live.LiveSkillAdapter):
    def developer_context(self,unused_skill,contract,previous=None):
        if contract.startswith('Return only complete Python source'):raise Stop('H0_source_not_in_selected_subset')
        data={'target':'spec'}
        if 'Retain this output path for CAD repair' in contract:data['stage']='repair'
        if previous is not None:
            observations={k:copy.deepcopy(previous[k]) for k in ('build_spec','invalid_output','error') if k in previous}
            result=previous.get('result') or {}
            safe={k:result[k] for k in ('failed_phase','probe_status','next_actor','message_code') if k in result}
            safe['measurements']={k:v for k,v in (result.get('measurements') or {}).items()
                if k in ('original_geometry_pass','whole_boundary_pass','native_reopened','native_edit_restored') and type(v) is bool}
            safe['failed_predicate_groups']=[c['field'] for c in result.get('predicate_details',{}).get('checks',[])
                if c.get('passed') is False and c.get('field') in ('bbox','volume','holes','pockets','steps','sections','finish','whole_boundary')]
            if result:observations['result']=safe
            data['observations']=observations
        return self.context(data)


class Transport(_LiveTransport):
    def __init__(self,manifest,journal,out,request,skill,guard,*,entry,process=None,**kwargs):
        production=process is None
        super().__init__(manifest,journal,out,request,skill,guard,
            process=model_process(guard) if production else process,**kwargs)
        self.evidence_mode='live' if production else 'unit_mock'
        self.entry=entry
        # The journal is shared across episodes; attempt IDs must be run-unique.
        self.sequence=journal.sequence
        self.logical_call=guard.pool.used

    def _invoke(self,argv,**kwargs):
        if len(argv)>1 and argv[1] in ('exec','--version'):
            completed=super()._invoke(argv,**kwargs)
            if argv[1]=='exec' and (completed.returncode!=0 or not Path(argv[argv.index('-o')+1]).is_file()):
                self.fatal='H0_model_launch_or_response_failure'
            return completed
        self.guard.check()
        if '--script' not in argv or '--generator' not in argv or argv[argv.index('--generator')+1]!='compiler':
            raise Stop('H0_only_fixed_spec_compiler')
        script=inputs.private_path(argv[argv.index('--script')+1])
        candidates=sorted(script.parent.glob('build-spec-c*.json'),key=lambda p:int(p.stem.split('-c')[-1]))
        if not candidates:raise Stop('H0_candidate_spec_missing')
        spec=cad_spec.loads_spec(candidates[-1].read_text(encoding='utf-8'))
        out=inputs.private_path(argv[argv.index('--out-dir')+1])
        self.sequence+=1;attempt='attempt-%04d'%self.sequence
        stage='repair' if len(list(script.parent.glob('input-a*.py')))>1 else 'initial'
        event=dict(episode_id=self.episode,attempt_id=attempt,operation='cad',route=self.route,stage=stage,
            retained_segment=self.scored,evidence_mode=self.evidence_mode,manifest_sha256=self.manifest['manifest_sha256'])
        self.journal.append('attempt_started',**event,source_sha256=ledger.file_sha(script))
        tick=self.wall()
        try:
            result=cad.run_candidate(spec,self.entry,out,script,
                cad_timeout=float(argv[argv.index('--timeout-s')+1]),
                reimport_timeout=float(argv[argv.index('--verification-timeout-s')+1]),
                total_timeout=float(kwargs['timeout']))
        except BaseException:
            self.fatal='H0_CAD_backend_stopped'
            self.journal.append('attempt_finished',**event,wall_s=self.wall()-tick,active_s=self.wall()-tick,
                charged=None,error='H0_CAD_backend_stopped');raise
        text=json.dumps(result)
        captures={key:ledger.StreamCapture(out/('transport-'+key+'.bin')) for key in ('stdout','stderr')}
        captures['stdout'].feed(text.encode('utf-8'))
        for path in sorted(out.glob('*.stderr.bin')):
            for raw in agent.chunks(path):captures['stderr'].feed(raw)
        streams={key:capture.finish() for key,capture in captures.items()}
        subprocess_streams={path.name:dict(path=str(path),sha256=ledger.file_sha(path),bytes=path.stat().st_size,complete=True)
            for path in out.glob('*.bin') if not path.name.startswith('transport-')}
        self.journal.append('attempt_finished',**event,wall_s=self.wall()-tick,active_s=self.wall()-tick,
            charged=None,result_sha256=ledger.file_sha(out/'result.json'),exit_code=0 if result['status']=='ok' else 1,
            streams=streams,subprocess_streams=subprocess_streams)
        self.guard.check()
        return subprocess.CompletedProcess(argv,0 if result['status']=='ok' else 1,text,'')
