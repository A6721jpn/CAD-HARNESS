"""H2's explicit sealed-fixture custody adapter; numeric driver/score unchanged."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import types
import subprocess

from tools import sw_h2_fixtures as fixtures,sw_h0_runtime as runtime
from tools import cad_verify_v4_agent as agent,cad_verify_v4_freeze as freezing
from tools import cad_verify_v4_ledger as ledger,sw_m0 as base
from tools.cad_verify_guard import Stop
from tools.sw_m1_inputs import private_path

ROOT=base.ROOT
CANDIDATE='modeling-h2-r1.md'
GATE='''if not preview and (gold["provenance"]["authority"] != "human" or gold["provenance"]["confirmed"] is not True):
    raise ValueError("eval_human_gold_required")'''
REPLACEMENT='''if not preview:
    _h2_fixture_admission(gold, gold_path)'''


def canonical(value):return json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode()


def description_only(original,candidate):
    """Accept one body paragraph; preserve every unchanged original byte/EOL."""
    old=original.replace(b'\r\n',b'\n').split(b'\n\n')
    new=candidate.replace(b'\r\n',b'\n').split(b'\n\n')
    if len(old)!=len(new):raise Stop('H2_description_structure_changed')
    changes=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
    if len(changes)!=1 or changes[0]<2:raise Stop('H2_description_only_required')
    i=changes[0]
    if b'\n' in old[i] or b'\n' in new[i] or not new[i].strip():raise Stop('H2_single_body_paragraph_required')
    if original.count(old[i])!=1:raise Stop('H2_description_paragraph_ambiguous')
    return original.replace(old[i],new[i],1)


def bundles():
    folder=ROOT/'skills/cad-harness-v4'
    original=agent.bundle(ROOT) # Includes original embedded-policy admission.
    modeling=(folder/'modeling.md').read_bytes()
    changed=description_only(modeling,(folder/CANDIDATE).read_bytes())
    candidate=b'\n'.join(((folder/'SKILL.md').read_bytes(),changed,(folder/'contracts.md').read_bytes()))
    return {'A':original,'B':candidate}


def adapted_tree(source):
    tree=ast.parse(source);functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_driver']
    if len(functions)!=1:raise Stop('H2_driver_function_identity')
    function=functions[0];before=ast.dump(function,include_attributes=False)
    expected=ast.dump(ast.parse(GATE).body[0],include_attributes=False)
    class AdmissionOnly(ast.NodeTransformer):
        count=0
        def visit_If(self,node):
            if ast.dump(node,include_attributes=False)==expected:
                self.count+=1
                return ast.copy_location(ast.parse(REPLACEMENT).body[0],node)
            return self.generic_visit(node)
    visitor=AdmissionOnly();visitor.visit(function)
    if visitor.count!=1:raise Stop('H2_driver_admission_gate_changed')
    module=ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
    return module,dict(original_function_ast_sha256=ledger.sha(before.encode()),
        fixture_function_ast_sha256=ledger.sha(ast.dump(function,include_attributes=False).encode()),
        replacement_count=visitor.count,original_gate=GATE,replacement_gate=REPLACEMENT,
        numeric_scoring_or_state_machine_changes=False)


def context(experiment):
    fixtures.folder(experiment) # Validate before constructing any public path.
    if (fixtures.PUBLIC/experiment/'quarantine.json').exists():raise Stop('H2_dataset_quarantined')
    out,seal,entries=fixtures.admitted(experiment)
    proof_path=out/'native-controls/proof.json';proof=ledger.read_json(proof_path)
    expected={(e['id'],label) for e in entries for label in ('positive','negative')}
    rows=proof.get('rows',[])
    if (proof.get('status')!='PASS' or proof.get('experiment')!=experiment
            or len(rows)!=len(expected) or {(r['id'],r['control']) for r in rows}!=expected
            or any(r.get('passed') is not True for r in rows)
            or proof.get('seal_sha256')!=ledger.file_sha(out/'seal.json')
            or proof.get('factory_sha256')!=seal['factory_sha256']):raise Stop('H2_native_control_custody')
    source={name:ledger.file_sha(ROOT/name) for name in fixtures.CONTROL_SOURCES}
    if proof.get('source_sha256')!=source:raise Stop('H2_native_control_source_changed')
    bound={str(out/name):digest for name,digest in seal['files'].items()}
    bound.update({str(p):ledger.file_sha(p) for p in (out/'seal.json',proof_path)})
    for entry in entries:
        for control in ('positive','negative'):
            where=out/'native-controls'/entry['case']/control
            for name in ('result.json','com-result.json'):
                bound[str(where/name)]=ledger.file_sha(where/name)
    return out,entries,bound


def fixture_admission(experiment,entry,gold,gold_path):
    _,entries,_=context(experiment)
    expected=next((e for e in entries if e['case']==entry['case']),None)
    if (expected is None or private_path(gold_path)!=private_path(expected['gold_path'])
            or ledger.file_sha(gold_path)!=expected['gold_sha256']
            or canonical(gold)!=canonical(expected['gold'])
            or gold['provenance']['authority']!='fixture' or gold['provenance']['confirmed'] is not False
            or entry['request_sha256']!=expected['request_sha256']
            or entry['route']!='spec' or entry['max_calls']!=3):raise Stop('H2_fixture_admission_failed')


def driver(adapter,transport,experiment,entry):
    original=agent.adapted_driver(adapter,transport)
    tree,_=adapted_tree(Path(agent.v3.__file__).read_text(encoding='utf-8'))
    scope=dict(original.__globals__)
    scope['_h2_fixture_admission']=lambda gold,path:fixture_admission(experiment,entry,gold,path)
    exec(compile(tree,str(agent.v3.__file__)+'[H2-fixture-admission]','exec'),scope)
    return scope['run_driver']


def literal_transport():
    # H0 makes a private v4 transport class on each module load. Change only
    # that new class, never either production import or the files on disk.
    spec=importlib.util.spec_from_file_location('tools._sw_h2_literal_runtime',ROOT/'tools/sw_h0_runtime.py')
    local=importlib.util.module_from_spec(spec);spec.loader.exec_module(local)
    source=Path(local._LiveTransport._invoke.__code__.co_filename)
    tree=ast.parse(source.read_text(encoding='utf-8'))
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LiveTransport']
    if len(classes)!=1:raise Stop('H2_transport_class_identity')
    methods=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name=='_invoke']
    if len(methods)!=1:raise Stop('H2_transport_method_identity')
    method=methods[0];before=ast.dump(method,include_attributes=False)
    expected=ast.dump(ast.parse('"@"+str(payload)',mode='eval').body,include_attributes=False)
    class LiteralOnly(ast.NodeTransformer):
        count=0
        def visit_BinOp(self,node):
            if ast.dump(node,include_attributes=False)==expected:
                self.count+=1
                return ast.copy_location(ast.parse("payload.read_text(encoding='utf-8')",mode='eval').body,node)
            return self.generic_visit(node)
    visitor=LiteralOnly();visitor.visit(method)
    if visitor.count!=1:raise Stop('H2_transport_payload_expression_changed')
    scope=dict(local._LiveTransport._invoke.__globals__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
        str(source)+'[H2-literal-prompt]','exec'),scope)
    local._LiveTransport._invoke=scope['_invoke']
    proof=dict(original_invoke_ast_sha256=ledger.sha(before.encode()),
        literal_invoke_ast_sha256=ledger.sha(ast.dump(method,include_attributes=False).encode()),
        replacement_count=visitor.count,input_mode='literal_json_argument',stdin='DEVNULL',
        numeric_scoring_slots_or_timers_changed=False)
    return local.Transport,proof


def user_packet_matches(stdout,payload):
    """Verify resolved native user messages, not merely the file/argv wrapper."""
    expected=canonical(ledger.read_json(payload));seen=0
    with Path(stdout).open('rb') as stream:
        for raw in stream:
            try:event=json.loads(raw)
            except (ValueError,UnicodeError):continue
            message=event.get('message') if isinstance(event,dict) else None
            if not isinstance(message,dict) or message.get('role')!='user':continue
            content=message.get('content')
            if isinstance(content,str):text=content
            elif isinstance(content,list) and all(isinstance(c,dict) and c.get('type')=='text' and isinstance(c.get('text'),str) for c in content):
                text=''.join(c['text'] for c in content)
            else:return False
            try:actual=json.loads(text)
            except ValueError:return False
            if canonical(actual)!=expected:return False
            seen+=1
    return seen>0


_TRANSPORT_BASE,TRANSPORT_ADAPTATION=literal_transport()


class Transport(_TRANSPORT_BASE):
    def _invoke(self,argv,**kwargs):
        model=len(argv)>1 and argv[1] in ('exec','--version')
        if model:kwargs['cwd']=self.manifest['generation_cwd']
        try:
            completed=super()._invoke(argv,**kwargs)
            if model and argv[1]=='exec' and not self.fatal:
                payload=self.out/('logical-%04d'%self.logical_call)/'payload.json'
                if not user_packet_matches(self.out/self.last_attempt/'stdout.bin',payload):
                    self.fatal=self.guard.stop_reason='H2_model_prompt_envelope_mismatch'
                    raise Stop(self.fatal)
            return completed
        except BaseException as exc:
            if not model:
                proof=None
                if isinstance(exc,Stop) and str(exc)=='H0_neutral_worker_timeout':
                    proof=neutral_timeout_certificate(Path(argv[argv.index('--out-dir')+1]),self.manifest['solidworks'])
                if proof:
                    self.manifest['_known_episode_timeout']=proof
                    self.fatal='H2_closed_SW_neutral_timeout'
                else:self.manifest['_native_uncertain']=True
            raise


def isolated_execute(experiment,entry,episode,manifest,journal,pool,*,process=None):
    if process is None and manifest.get('evidence_mode')!='live':raise Stop('H2_live_requires_frozen_manifest')
    # Two isolated modules; no monkey-patching production imports or code files.
    spec=importlib.util.spec_from_file_location('tools._sw_h2_h0_trial',ROOT/'tools/sw_h0.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    variant=bundles()[manifest['variant']]
    class Agent:
        def __getattr__(self,name):return getattr(agent,name)
        def bundle(self,root):return variant
        def adapted_driver(self,adapter,transport):return driver(adapter,transport,experiment,entry)
    module.agent=Agent()
    module.runtime=types.SimpleNamespace(Guard=runtime.Guard,Transport=Transport,SafeAdapter=runtime.SafeAdapter)
    return module.execute(entry,episode,manifest,journal,pool,process=process)


def solidworks_identity():
    # Existing ROT object only. Limited process query reads its executable path;
    # no ownership, ACL, user preferences, document or lifecycle changes.
    code=r'''
import ctypes,ctypes.wintypes as W,hashlib,json,pythoncom
from win32com.client.dynamic import Dispatch
pythoncom.CoInitialize()
app=Dispatch(pythoncom.GetActiveObject('SldWorks.Application').QueryInterface(pythoncom.IID_IDispatch))
data={}
for key,name in (('pid','GetProcessID'),('revision','RevisionNumber'),('documents','GetDocumentCount')):
 app._FlagAsMethod(name);data[key]=getattr(app,name)()
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
k.CloseHandle.argtypes=[W.HANDLE]
handle=k.OpenProcess(0x1000,False,data['pid'])
if not handle:raise ctypes.WinError(ctypes.get_last_error())
try:
 size=W.DWORD(32768);name=ctypes.create_unicode_buffer(size.value)
 if not k.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
 data['executable']=name.value
 with open(name.value,'rb') as file:data['sha256']=hashlib.file_digest(file,'sha256').hexdigest()
finally:k.CloseHandle(handle)
print(json.dumps(data))
'''
    result=subprocess.run([str(base.SW_PYTHON),'-B','-c',code],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,check=True)
    identity=json.loads(result.stdout)
    if identity['documents']!=0:raise Stop('STOP_SW_existing_documents_no_document_touched')
    return identity


def neutral_timeout_certificate(out,identity):
    """A killed SDK client is not an unresponsive shared COM server."""
    try:
        path=private_path(Path(out)/'com-result.json');com=ledger.read_json(path)
        if (com.get('status')!='PASS' or com.get('stop') is not False
                or com.get('COM_state_unknown') is not False or type(com.get('final_documents')) is not int or com['final_documents']!=0
                or (com.get('pid'),com.get('revision'))!=(identity['pid'],identity['revision'])):return None
        if solidworks_identity()!=identity:return None
        return dict(SW_completion_sha256=ledger.file_sha(path),SW_identity_unchanged=True,
            document_closed=True,failed_component='owned_neutral_SDK_worker',scored_pass=False)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError):return None


def continuation_prefix(experiment,entries,bound,new_manifest):
    """Admit a complete old calibration prefix, including its failed timeout."""
    out=fixtures.folder(experiment);path=out/'experiment-manifest.json';old=ledger.read_json(path)
    old_sha=ledger.file_sha(path)
    if (old_sha!=ledger.read_json(out/'experiment-SHA256.json')['manifest_sha256']
            or old['schema']!='harness2.solidworks.skill.freeze.v3' or old.get('evidence_mode')!='live'
            or old.get('experiment')!=experiment or old['input_files']!=bound):raise Stop('H2_continuation_old_manifest')
    allowed={'tools/sw_h2.py','tools/sw_h2_runtime.py','tools/test_sw_h2.py','H2_SKILL_PLAN.md'}
    if set(old['files'])!=set(new_manifest['files']) or any(old['files'][k]!=v for k,v in new_manifest['files'].items() if k not in allowed):
        raise Stop('H2_continuation_critical_source_changed')
    critical=('policy_sha256','generator','host','solidworks','runtime_files','OMP_PROFILE','generator_config_sha256',
        'skill_sha256','fixture_admission','transport_adaptation','generation_cwd','protocol','development_ids','holdout_ids')
    if any(canonical(old[k])!=canonical(new_manifest[k]) for k in critical):raise Stop('H2_continuation_contract_changed')
    expected={e['case']:e for e in entries};prefix={};rows=[];missing=False
    bindings={str(p):ledger.file_sha(p) for p in (path,out/'experiment-SHA256.json')}
    for case in old['development_ids']:
        for repeat in range(1,6):
            label='C'+case+'R'+str(repeat);trial=private_path(runtime.PRIVATE/('h2-'+experiment+'-'+label))
            saved=trial/'trial-result.json'
            if not saved.exists():missing=True;continue
            if missing:raise Stop('H2_continuation_noncontiguous_prefix')
            row=ledger.read_json(saved);own=ledger.read_json(trial/'manifest.json')
            expected_entry=copy.deepcopy(expected[case]);expected_entry['id']=label
            packet=ledger.read_json(trial/'inputs-private.json')
            if (row.get('experiment_manifest_sha256')!=old_sha or row.get('label')!=label or row.get('case')!=case
                    or row.get('variant')!='A' or row.get('phase')!='calibration' or type(row.get('passed')) is not bool
                    or row.get('initial_model_input_verified') is not True
                    or ledger.file_sha(trial/'manifest.json')!=row['manifest_sha256']
                    or ledger.read_json(trial/'SHA256.json')['manifest_sha256']!=row['manifest_sha256']
                    or ledger.file_sha(trial/'ledger.jsonl')!=row['ledger_sha256']
                    or own['files']!=old['files'] or own['generator']!=old['generator']
                    or own['skill_sha256']!=old['skill_sha256']['A']
                    or canonical(packet)!=canonical([expected_entry])
                    or ledger.file_sha(trial/'inputs-private.json')!=own['inputs_packet_sha256']):
                raise Stop('H2_continuation_saved_trial_binding')
            events=list(ledger.rows(trial/'ledger.jsonl'))
            starts={e['attempt_id'] for e in events if e['event']=='attempt_started' and e.get('operation')=='model'}
            ends={e['attempt_id'] for e in events if e['event']=='attempt_finished' and e.get('operation')=='model'}
            if starts!=ends or ledger.summarize(trial/'ledger.jsonl')['conservative_reserved_calls']!=row['model_calls']:
                raise Stop('H2_continuation_pending_call')
            for p in (saved,trial/'manifest.json',trial/'SHA256.json',trial/'inputs-private.json',trial/'ledger.jsonl'):
                bindings[str(p)]=ledger.file_sha(p)
            for event in events:
                for stream in (event.get('streams') or {}).values():
                    p=private_path(stream['path'])
                    if not p.is_relative_to(trial) or ledger.file_sha(p)!=stream['sha256']:raise Stop('H2_continuation_stream_changed')
                    bindings[str(p)]=stream['sha256']
            prefix[label]=dict(result_sha256=ledger.file_sha(saved),ledger_sha256=row['ledger_sha256'],old_manifest_sha256=old_sha)
            rows.append(row)
    if not rows or len(rows)%5 or [r['label'] for r in rows if r.get('stopped')]!=[rows[-1]['label']] or rows[-1]['passed']:
        raise Stop('H2_continuation_terminal_timeout_required')
    label=rows[-1]['label'];trial=runtime.PRIVATE/('h2-'+experiment+'-'+label)
    driver=trial/'episode/reports/cad-run/request-mvp1';report_path=driver/'driver-run.json';report=ledger.read_json(report_path)
    if report.get('message_code')!='H0_neutral_worker_timeout' or report.get('cad_attempts') not in (1,2):
        raise Stop('H2_continuation_not_neutral_timeout')
    native_out=driver/('a%d-mvp1'%report['cad_attempts'])
    proof=neutral_timeout_certificate(native_out,new_manifest['solidworks'])
    if not proof:raise Stop('H2_continuation_SW_not_certified_closed')
    for p in (report_path,native_out/'com-result.json'):bindings[str(p)]=ledger.file_sha(p)
    return dict(source_manifest_sha256=old_sha,prefix=prefix,safe_timeout_label=label,
        neutral_timeout_certificate=proof,bound_input_files=bindings)


def prepare(experiment,*,smoke=False,continuation=False):
    out,entries,bound=context(experiment)
    policy=freezing._policy(ROOT,ROOT/'design/cad-harness-verify-v4/policy.json')
    files=freezing.bindings(ROOT);files['H2_SKILL_PLAN.md']=ledger.file_sha(ROOT/'H2_SKILL_PLAN.md')
    generator=dict(model=freezing.MODEL,thinking=freezing.THINKING,**freezing._executable('omp'))
    if not all(generator.get(k) for k in ('omp','version','sha256')):raise Stop('H2_omp_identity_unavailable')
    host=freezing._host()
    if host['hostname']!=freezing.REQUIRED_HOST:raise Stop('H2_wrong_host')
    solidworks=solidworks_identity()
    for entry in entries:
        for control in ('positive','negative'):
            record=ledger.read_json(out/'native-controls'/entry['case']/control/'com-result.json')
            if (record['pid'],record['revision'])!=(solidworks['pid'],solidworks['revision']):
                raise Stop('H2_native_control_SW_instance_changed')
    _,adaptation=adapted_tree(Path(agent.v3.__file__).read_text(encoding='utf-8'))
    work=private_path(out/'generator-cwd');work.mkdir(exist_ok=True)
    prefix='continuation' if continuation else 'preflight' if smoke else 'experiment'
    path=out/(prefix+'-manifest.json')
    manifest=dict(schema='harness2.solidworks.skill.freeze.v4',experiment=experiment,prepared_at=ledger.utc(),
        policy_sha256=policy,files=files,input_files=bound,generator=generator,host=host,solidworks=solidworks,
        runtime_files={str(p):ledger.file_sha(p) for p in (base.SW_PYTHON,base.FC_BIN/'python.exe')},
        OMP_PROFILE=os.environ.get('OMP_PROFILE'),generator_config_sha256=ledger.sha(canonical(runtime.MODEL_CONFIG)),
        quota_snapshot='C:/dev/v4-ops/quota.json',generation_cwd=str(work),context_manifest=str(path),
        evidence_mode='unit_mock' if smoke else 'live',
        skill_sha256={arm:ledger.sha(value) for arm,value in bundles().items()},fixture_admission=adaptation,
        transport_adaptation=TRANSPORT_ADAPTATION,
        development_ids=[e['case'] for e in entries if e['role']=='development'],
        holdout_ids=[e['case'] for e in entries if e['role']=='holdout'],
        protocol=dict(calibration_per_case=5,baseline_pass_counts=[2,3],matched_pairs=5,max_pairs=10,
            cache_basis='initial_accepted_model_call',cache_max_difference_percentage_points=1,
            cache_fraction='cache_read_tokens/(input_uncached_tokens+cache_read_tokens+cache_write_tokens)',
            required_pass_gain=2,final_holdout_all_pass=True,pool_cap=40,max_calls_per_episode=3),
        authorization='UNIT_MOCK_NO_LIVE_AUTHORIZATION' if smoke else
            'USER 2026-10-28 01:18/01:30: autonomous skill-text-only independent Codex batches <=50; conservatively cap40')
    if continuation:
        resume=continuation_prefix(experiment,entries,bound,manifest)
        manifest['resume']=resume;manifest['input_files'].update(resume['bound_input_files'])
    ledger.write_json(path,manifest)
    digest=ledger.file_sha(path);ledger.write_json(out/(prefix+'-SHA256.json'),{'manifest_sha256':digest})
    public={k:manifest[k] for k in ('schema','experiment','prepared_at','policy_sha256','skill_sha256','fixture_admission','transport_adaptation','protocol','development_ids','holdout_ids','solidworks','evidence_mode')}
    public.update(manifest_sha256=digest,source_sha256=files,generator={k:generator[k] for k in ('model','thinking','version','sha256')},live_model_calls=0)
    if continuation:public['resume']={k:manifest['resume'][k] for k in ('source_manifest_sha256','safe_timeout_label')}
    if continuation:public['resume']['prefix_labels']=list(manifest['resume']['prefix'])
    ledger.write_json(fixtures.PUBLIC/experiment/(prefix+'-manifest-public.json'),public)
    return public


def load(experiment,*,continuation=False):
    out,entries,bound=context(experiment)
    prefix='continuation' if continuation else 'experiment'
    path=out/(prefix+'-manifest.json');manifest=ledger.read_json(path)
    if ledger.file_sha(path)!=ledger.read_json(out/(prefix+'-SHA256.json'))['manifest_sha256']:raise Stop('H2_experiment_manifest_changed')
    expected_bound=bound|((manifest.get('resume') or {}).get('bound_input_files') or {})
    if (manifest['schema']!='harness2.solidworks.skill.freeze.v4' or manifest['experiment']!=experiment
            or manifest['input_files']!=expected_bound or manifest['skill_sha256']!={a:ledger.sha(b) for a,b in bundles().items()}
            or manifest['generator']['model']!=freezing.MODEL or manifest['generator']['thinking']!=freezing.THINKING
            or continuation!=bool(manifest.get('resume'))):raise Stop('H2_experiment_binding')
    if any(ledger.file_sha(p)!=digest for p,digest in expected_bound.items()):raise Stop('H2_continuation_input_changed')
    current=freezing.bindings(ROOT);current['H2_SKILL_PLAN.md']=ledger.file_sha(ROOT/'H2_SKILL_PLAN.md')
    if manifest['files']!=current:raise Stop('H2_experiment_source_changed')
    if manifest.get('evidence_mode')!='live':raise Stop('H2_live_requires_frozen_manifest')
    return out,manifest,entries


def trial_manifest(experiment,shared,entry,label,variant,pool_name,pool_scope):
    run='h2-'+experiment+'-'+label;out=private_path(runtime.PRIVATE/run);out.mkdir(exist_ok=False)
    episode_entry=copy.deepcopy(entry);episode_entry['id']=label
    ledger.write_json(out/'inputs-private.json',[episode_entry])
    manifest=copy.deepcopy(shared)
    manifest.update(run=run,scope='H2-skill-text-only',variant=variant,charged_call_cap=40,budget_pool=pool_name,budget_scope=pool_scope,
        skill_sha256=shared['skill_sha256'][variant],inputs_packet_sha256=ledger.file_sha(out/'inputs-private.json'))
    shared_path=private_path(shared['context_manifest'])
    manifest['input_files'][str(shared_path)]=ledger.file_sha(shared_path)
    ledger.write_json(out/'manifest.json',manifest)
    manifest['manifest_sha256']=ledger.file_sha(out/'manifest.json')
    ledger.write_json(out/'SHA256.json',{'manifest_sha256':manifest['manifest_sha256']})
    return out,manifest,episode_entry


def initial_measurement(events,episode):
    accepted=[e for e in events if e.get('event')=='attempt_finished' and e.get('operation')=='model' and e.get('charged') is True]
    if not accepted:return dict(initial_usage=None,initial_payload_sha256=None,initial_cwd=None,initial_model_input_verified=False)
    first=accepted[0];values=(first.get('usage') or {}).get('values',{})
    path=episode/('logical-%04d'%first['logical_call_id'])/'payload.json'
    submitted=ledger.read_json(episode/first['attempt_id']/'submitted.json')
    return dict(initial_usage={name:values.get(key) for name,key in (
            ('input_uncached_tokens','input_tokens'),('cache_read_tokens','cached_input_tokens'),
            ('cache_write_tokens','cache_write_input_tokens'))},
        initial_payload_sha256=ledger.file_sha(path),initial_cwd=submitted['cwd'],
        initial_model_input_verified=user_packet_matches(first['streams']['stdout']['path'],path))
