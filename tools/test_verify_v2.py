"""Only the signed v2 contracts; all provider and CAD launches here are mocked."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import tomllib
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from tools import cad_agent, cad_spec, cad_verify_v2_agent as driver, cad_verify_v2_probe as probe, eval_verify_v2 as evaluation
from tools.cad_verify_guard import Fault, Guard as V1Guard
from tools.cad_verify_v2_guard import Budget, Guard, Stop
from tools.test_support import start_tempdirs, stop_tempdirs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'design/cad-harness-verify-v2'
NOW=datetime(2026,10,13,0,0,tzinfo=timezone.utc)


def setUpModule():
    global _temp_patches
    _temp_patches=start_tempdirs()


def tearDownModule(): stop_tempdirs(_temp_patches)


def spec(case):
    g=probe.load_gold(BASE/'test'/case/'gold.json')
    return dict(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world',
        regions=[dict(bounds=g['bbox'])],holes=[{k:v for k,v in h.items() if k!='through'} for h in g['holes']],
        pockets=[{k:v for k,v in p.items() if k!='sharp'} for p in g['pockets']],finish=g['finish'])


class V2Contracts(unittest.TestCase):
    def setup_root(self,d):
        root=Path(d)/'repo'
        for name in ('skills/freecad-modeling/SKILL.md','design/cad-harness-mvp/build-schema.json'):
            p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes((ROOT/name).read_bytes())
        return root

    def snapshot(self,d,percent=20):
        path=Path(d)/'snapshot.json'
        path.write_text(json.dumps(dict(snapshot_id='mock',observed_at=NOW.isoformat(),used_percent=percent)),encoding='utf-8')
        return path

    def drive(self,d,case,outputs,plans=(),route='spec',fault=None,clock=None,after_cad=None,preview=False,after_exec=None):
        root=self.setup_root(d); folder=BASE/'test'/case
        calls=[]; cads=[]
        def runner(argv,**kwargs):
            self.assertFalse(kwargs['shell'])
            if argv[1]=='--version': return subprocess.CompletedProcess(argv,0,'mock CLI','')
            if argv[1]=='exec':
                calls.append((argv,kwargs))
                Path(argv[argv.index('-o')+1]).write_text(outputs[len(calls)-1],encoding='utf-8')
                if after_exec: after_exec(len(calls))
                if clock: clock[0]+=10
                return subprocess.CompletedProcess(argv,0,'{"type":"turn.completed","usage":{"input_tokens":11,"output_tokens":2}}','')
            self.assertEqual(Path(argv[2]).name,'cad_run.py')
            self.assertEqual(argv[argv.index('--probe-profile')+1],'verify-v2')
            cads.append((argv,kwargs))
            source,out,gold=[Path(argv[argv.index(k)+1]) for k in ('--script','--out-dir','--gold')]
            out.mkdir(); (out/'input.py').write_bytes(source.read_bytes()); (out/'gold.json').write_bytes(gold.read_bytes())
            r=dict(schema='cad-harness.cad_run.v0',task_id=case,probe_profile='verify-v2',
                script_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),gold_sha256=hashlib.sha256(gold.read_bytes()).hexdigest(),
                status='ok',geometry_ok=True,editability_ok=True,probe_pass=True,probe_status='pass',script_completed=True,
                verification_pass=True,document_closed=True,cleanup_status='exited',cad_exit_code=0,
                verification_cleanup_status='exited',verification_exit_code=0,owned_pid=100+len(cads),verification_pid=200+len(cads),
                verification=dict(verification_pass=True,document_closed=True),failed_phase=None,next_actor=None,
                generator=argv[argv.index('--generator')+1],measurements={'editability':{'native_valid':True}})
            if len(plans)>=len(cads): r.update(plans[len(cads)-1])
            (out/'result.json').write_text(json.dumps(r),encoding='utf-8')
            if clock: clock[0]+=10
            if after_cad: after_cad(len(cads),r)
            return subprocess.CompletedProcess(argv,0 if r['status']=='ok' else 1,json.dumps(r),'')
        guard=Guard(self.snapshot(d),clock=(lambda:clock[0]) if clock else None,now=lambda:NOW)
        rubric=json.loads((folder/'rubric.json').read_text(encoding='utf-8')) if (folder/'rubric.json').is_file() else None
        answer=(folder/'answer.txt').read_text(encoding='utf-8') if route=='completion' else None
        result,code=driver.run_driver('mock-v2-mvp1','MOCK-NO-MODEL', (folder/'description.txt').read_text(encoding='utf-8'),
            folder/'gold.json' if (folder/'gold.json').is_file() else None,root=root,runner=runner,guard=guard,
            route=route,rubric=rubric,answer=answer,fault=fault,preview=preview)
        return result,code,calls,cads,guard

    def failure(self,predicate='holes'):
        return dict(status='failed',geometry_ok=False,probe_pass=False,probe_status='predicate_fail',
                    failed_phase='probe',next_actor='sol',predicate_diff=[predicate],code_owner='sol')

    def test_source_parse_before_fault_still_guarantees_real_repair(self):
        folder=BASE/'test/K1'; source=(folder/'positive.py').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as d:
            r,code,calls,cads,guard=self.drive(d,'K1',['invalid','{"unsupported":["geometry"]}',source,source],
                [self.failure('roller'),{}],route='source',fault=Fault(folder/'fault.json'))
            self.assertEqual((code,len(calls),len(cads),guard.calls),(0,4,2,4))
            self.assertEqual([c['purpose'] for c in r['calls']],['interpretation','parse_repair','source','repair'])
            self.assertEqual((r['parse_repairs'],r['repair_calls']),(1,1))
            self.assertTrue(r['repair_eligible']); self.assertIsNone(r['repair_not_attempted_reason'])
            context=next(tomllib.loads(arg)['developer_instructions'] for arg in calls[-1][0] if arg.startswith('developer_instructions='))
            previous=json.loads(context.split('Do not alter the user request or grading rules:\n',1)[1])
            self.assertEqual(previous['source'],(folder/'candidate.py').read_text(encoding='utf-8'))
            self.assertTrue(r['fault']['established'] and r['fault']['detected'])
            self.assertEqual(cads[-1][0][cads[-1][0].index('--timeout-s')+1],'90')
            self.assertEqual(cads[-1][0][cads[-1][0].index('--verification-timeout-s')+1],'90')
            self.assertLessEqual(calls[-1][1]['timeout'],180)

    def test_spec_repair_uses_the_one_unspent_parse_slot(self):
        folder=BASE/'test/K3'; good=json.dumps(spec('K3'))
        with tempfile.TemporaryDirectory() as d:
            r,code,calls,cads,_=self.drive(d,'K3',[good,'invalid',good],[self.failure(),{}],fault=Fault(folder/'fault.json'))
            self.assertEqual((code,len(calls),len(cads)),(0,3,2))
            self.assertEqual([c['purpose'] for c in r['calls']],['interpretation','repair','parse_repair'])
            self.assertEqual(r['budget_counts']['parse_repair'],1)
            self.assertLessEqual(calls[-1][1]['timeout'],60)

    def test_settled_in_schema_editability_misses_invoke_repair_and_record_eligibility(self):
        for case in ('W6','S2','A1','C2','C3','K3'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as d:
                completion=case.startswith('C')
                folder=BASE/'test'/case
                question=[json.dumps({'needs_clarification':json.loads((folder/'rubric.json').read_text(encoding='utf-8'))['required_fields']})] if completion else []
                fail=self.failure('holes' if case=='K3' else 'editability')
                fail.update(geometry_ok=case!='K3',editability_ok=False)
                r,code,calls,cads,_=self.drive(d,case,question+[json.dumps(spec(case)),'invalid','invalid'],[fail],
                    route='completion' if completion else 'spec',fault=Fault(folder/'fault.json') if case=='K3' else None)
                self.assertEqual((code,len(calls),len(cads)),(1,4 if completion else 3,1))
                self.assertTrue(r['repair_eligible']); self.assertEqual(r['repair_calls'],1)
                self.assertEqual(r['parse_repairs'],1); self.assertIsNone(r['repair_not_attempted_reason'])
                self.assertEqual(r['calls'][-2]['purpose'],'repair')
                self.assertEqual(r['calls'][-2]['stage'],'repair')
                root=Path(d)/'repo'
                for name in ('description.txt','gold.json','rubric.json','answer.txt','binding.json','fault.json','candidate.json'):
                    source=folder/name
                    if source.is_file():
                        target=root/evaluation.DESIGN/'test'/case/name
                        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(source.read_bytes())
                order=json.loads((BASE/'run-order.json').read_text(encoding='utf-8'))
                entry=next(e for e in order['entries'] if e['case']==case)
                row=evaluation.record(root,entry,'mock-v2-mvp1')
                self.assertIsNone(row['stop_reason'],row.get('error'))
                self.assertTrue(row['completed']); self.assertTrue(row['repair_eligible'])
                self.assertEqual(row['repair_calls'],1); self.assertFalse(row['passed'])

    def test_two_parse_failures_stop_without_hidden_calls(self):
        with tempfile.TemporaryDirectory() as d:
            r,code,calls,cads,_=self.drive(d,'A1',['invalid','invalid'])
            self.assertEqual((code,len(calls),len(cads)),(1,2,0))
            self.assertEqual(r['parse_repairs'],1)

    def test_completion_binds_two_payloads_without_resetting_budget(self):
        for case,field in [('C2','plate_thickness'),('C3','hole_positions')]:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as d:
                clock=[0.0]
                r,code,calls,cads,_=self.drive(d,case,[json.dumps({'needs_clarification':[field]}),json.dumps(spec(case))],
                                              route='completion',clock=clock)
                raw=(BASE/'test'/case/'description.txt').read_bytes()
                answer=(BASE/'test'/case/'answer.txt').read_bytes()
                self.assertEqual(calls[0][0][-1].encode('utf-8'),raw)
                self.assertEqual(calls[1][0][-1].encode('utf-8'),raw+b'\n'+answer)
                self.assertEqual((code,len(calls),len(cads)),(0,2,1))
                self.assertEqual(r['initial_q_score'],1); self.assertTrue(r['completion_reached'])
                self.assertEqual(r['wall_ms'],30000)
                report_file=Path(d)/'repo/reports/cad-run/mock-v2-mvp1/first-response.json'
                self.assertEqual(json.loads(report_file.read_text(encoding='utf-8')),r['first_response'])

    def test_completion_wrong_or_invented_first_response_never_receives_answer(self):
        for response in ('{"needs_clarification":["hole_positions"]}',json.dumps(spec('C2')),'invalid'):
            with self.subTest(response=response[:40]),tempfile.TemporaryDirectory() as d:
                r,code,calls,cads,_=self.drive(d,'C2',[response],route='completion')
                self.assertEqual((code,len(calls),len(cads)),(1,1,0))
                self.assertFalse(r['completion_reached']); self.assertEqual(r['initial_q_score'],0)

    def test_ask_is_always_one_call_zero_cad(self):
        for response in ('{"needs_clarification":["plate_thickness"]}','invalid',json.dumps(spec('A1'))):
            with tempfile.TemporaryDirectory() as d:
                r,_,calls,cads,_=self.drive(d,'A2',[response],route='ask')
                self.assertEqual((len(calls),len(cads),r['parse_repairs']),(1,0,0))

    def test_guard_can_stop_repair_without_consuming_a_fake_repair_call(self):
        with tempfile.TemporaryDirectory() as d:
            r,code,calls,cads,_=self.drive(d,'A1',[json.dumps(spec('A1'))],[self.failure()],
                after_cad=lambda n,result:self.snapshot(d,55))
            self.assertEqual((code,len(calls),len(cads)),(1,1,1))
            self.assertEqual(r['repair_calls'],0)
            self.assertIn('quota_soft_stop',r['repair_not_attempted_reason'])
        with tempfile.TemporaryDirectory() as d:
            r,code,calls,cads,_=self.drive(d,'C2',['{"needs_clarification":["plate_thickness"]}'],route='completion',
                after_exec=lambda n:self.snapshot(d,55))
            self.assertEqual((code,len(calls),len(cads)),(1,1,0))
            self.assertEqual(r['initial_q_score'],1); self.assertFalse(r['completion_reached'])
            self.assertIn('quota_soft_stop',r['completion_not_reached_reason'])

    def test_probe_exception_is_harness_stop_and_not_model_repair(self):
        with tempfile.TemporaryDirectory() as d:
            failure=self.failure(); failure.update(probe_status='exception',code_owner='harness',next_actor='human')
            r,code,calls,cads,_=self.drive(d,'A1',[json.dumps(spec('A1'))],[failure])
            self.assertEqual((code,len(calls),len(cads),r['repair_calls']),(1,1,1,0))
            self.assertIn('harness:',r['message_code'])

    def test_reserved_time_and_old_guard_cap(self):
        with tempfile.TemporaryDirectory() as d:
            clock=[0.0]; b=Budget(4,lambda:clock[0])
            b.call('interpretation'); b.call('parse_repair'); b.call('source'); b.cad()
            clock[0]=449
            b.begin_repair(); b.call('repair')
            self.assertEqual(b.counts['repair'],1)
            self.assertEqual(b.sol_timeout('repair'),180)
            self.assertLessEqual(b.stage_deadline,900)
            with self.assertRaises(ValueError): b.call('parse_repair')
            self.assertEqual((b.counts['parse_repair'],b.counts['repair']),(1,1))
            snapshot=self.snapshot(d)
            full=Guard(snapshot,call_budget=163,now=lambda:NOW)
            self.assertEqual((full.call_budget,full.deadline-full.started),(163,10800))
            for _ in range(163): full.before_call()
            self.assertEqual(full.calls,163)
            with self.assertRaisesRegex(Stop,'budget'): full.before_call()
            self.assertEqual(full.calls,163)
            with self.assertRaises(ValueError): Guard(snapshot,call_budget=164)
            with self.assertRaises(ValueError): V1Guard(snapshot,call_budget=126)
            guard=Guard(snapshot,clock=lambda:clock[0],now=lambda:NOW)
            clock[0]=guard.deadline-959
            with self.assertRaisesRegex(Stop,'reserve'): guard.before_episode(3)

    def test_active_driving_graph_excludes_origins_isolated_loops_and_radius_edges(self):
        constraints=[NS(Type='Coincident',First=0,Second=2,Third=-2000,Driving=True),
            NS(Type='PointOnObject',First=2,Second=1,Third=-2000,Driving=True),
            NS(Type='Equal',First=3,Second=4,Third=-2000,Driving=True),
            NS(Type='PointOnObject',First=0,Second=-1,Third=-2000,Driving=True),
            NS(Type='PointOnObject',First=3,Second=-1,Third=-2000,Driving=True),
            NS(Type='Radius',First=4,Second=0,Third=-2000,Driving=True)]
        sketch=NS(GeometryCount=5,Constraints=constraints,getActive=lambda i:True,
                  getDriving=lambda i:(_ for _ in ()).throw(ValueError('Invalid constraint id')))
        paths=probe.reachable(sketch,{0:[{'geometry':0}]})
        self.assertEqual(set(paths),{0,1,2})
        constraints[1].Driving=False
        self.assertEqual(set(probe.reachable(sketch,{0:[{'geometry':0}]})),{0,2})

    def test_data_description_answer_gold_analytic_numbers_and_order(self):
        planned={line.split('|')[1].split('/')[0].strip():line.split('|')[2].strip()
                 for line in (BASE/'PLAN-V2-CONSENSUS.md').read_text(encoding='utf-8').splitlines() if line.startswith('| ')}
        expected={'W1':math.pi*((20**2-5**2)*48-(20**2-17**2)*8),'W2':40*(1500-600+80),
            'W3':math.pi*(8**2-5**2)*(32*math.pi/2),'W4':72*48*24-64*40*20+64*12*4/2,
            'W5':math.pi*(48**2-12**2-6*3**2)*10-2*10*3*2,
            'W6':96*64*14-2*22*14*4-6*math.pi*2.5**2*14-(160-4/3),
            'S2':70*50*13,'A1':90*50*12-math.pi*5**2*12,'C2':76*44*11-4*math.pi*3**2*11,
            'C3':72*46*9-2*math.pi*3.5**2*9}
        for case,target in expected.items():
            folder=BASE/'test'/case; g=probe.load_gold(folder/'gold.json')
            self.assertAlmostEqual(g['volume']['target_mm3'],target,places=8)
            text=(folder/'description.txt').read_bytes()
            self.assertNotIn('寸法列'.encode('utf-8'),text)
            placement='' if case in ('W3','A1') else 'XY中心、下面Z=0。'
            self.assertEqual(text.decode('utf-8'),planned[case]+placement+'単位mm。他の加工なし。')
            if case.startswith('C'):
                answer=(folder/'answer.txt').read_bytes(); self.assertFalse(answer.endswith(b'\n'))
                text+=b'\n'+answer
            self.assertEqual(text.decode('utf-8'),g['description'])
        for fault,clean in [('K1','W1'),('K2','W5'),('K3','W6')]:
            self.assertEqual((BASE/'test'/fault/'description.txt').read_bytes(),(BASE/'test'/clean/'description.txt').read_bytes())
            self.assertEqual(probe.load_gold(BASE/'test'/fault/'gold.json')['volume'],probe.load_gold(BASE/'test'/clean/'gold.json')['volume'])
        order=json.loads((BASE/'run-order.json').read_text(encoding='utf-8'))
        self.assertEqual((len(order['entries']),sum(e['min_calls'] for e in order['entries']),sum(e['max_calls'] for e in order['entries'])),(60,83,163))
        self.assertEqual(sum(e['scored'] for e in order['entries']),51)

    def eval_root(self,d):
        root=Path(d)/'repo'
        refs=json.loads((BASE/'dev/v1-references.json').read_text(encoding='utf-8'))
        names=set(evaluation.CODE)|set(refs['files'])
        names.update(p.relative_to(ROOT).as_posix() for p in BASE.rglob('*') if p.is_file() and
            (p.relative_to(BASE).parts[0] in ('test','dev') or p.name in ('PLAN-V2-CONSENSUS.md','run-order.json')))
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'design/cad-harness-mvp/eval-v1').glob('*.json'))
        for name in names:
            target=root/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes((ROOT/name).read_bytes())
        return root.resolve()

    def test_frozen_mock_suite_aggregate_completion_denominator_and_repair_binding(self):
        """60 episodes use mock providers/CAD; aggregation must never launch either."""
        with tempfile.TemporaryDirectory() as d:
            root=self.eval_root(d); base=root/evaluation.DESIGN; snapshot=self.snapshot(d); clock=[0.0]
            phase2=evaluation.freeze(root)
            with self.assertRaises(FileExistsError): evaluation.freeze(root)
            with self.assertRaisesRegex(Stop,'reviewed_freeze'): evaluation.load(root)
            (base/'SHA256.json').rename(base/'SHA256.phase2.archive.json')
            self.assertEqual(json.loads((base/'SHA256.phase2.archive.json').read_text(encoding='utf-8')),phase2)
            cli=root/'.cli/codex.exe'; cli.parent.mkdir(); cli.write_bytes(b'MOCK EXECUTABLE ONLY')
            frozen=evaluation.freeze(root,'verify-v2-reviewed-mock','abcdef1','abcdef2',str(cli),
                runner=lambda argv,**kw:subprocess.CompletedProcess(argv,0,'mock CLI',''))
            order=json.loads((base/'run-order.json').read_text(encoding='utf-8'))
            state={}; time_stop={'active':False}
            actual_driver=driver.run_driver
            def enter_driver(name,*args,**kwargs):
                state.clear(); state.update(entry=next(e for e in order['entries'] if name.endswith('-'+e['id']+'-mvp1')),calls=0,cads=0)
                return actual_driver(name,*args,**kwargs)
            def result(out,source,gold,case,profile='verify-v2',generator='compiler',failure=False,timeout=300):
                out.mkdir(parents=True); (out/'input.py').write_bytes(source); (out/'gold.json').write_bytes(gold.read_bytes())
                r=dict(schema='cad-harness.cad_run.v0',task_id=case,probe_profile=profile,
                    script_sha256=evaluation.sha(source),gold_sha256=evaluation.sha(gold.read_bytes()),timeout_s=timeout,
                    status='ok',geometry_ok=True,editability_ok=True,probe_pass=True,probe_status='pass',script_completed=True,
                    verification_pass=True,document_closed=True,cleanup_status='exited',cad_exit_code=0,
                    verification_cleanup_status='exited',verification_exit_code=0,owned_pid=101,verification_pid=202,
                    verification=dict(verification_pass=True,document_closed=True),failed_phase=None,next_actor=None,
                    generator=generator,measurements={'editability':{'native_valid':True}})
                if failure: r.update(self.failure('roller' if case=='K1' else 'holes'))
                else:
                    r['artifact_sha256']={}
                    for filename in ('model.FCStd','model.step'):
                        raw=('MOCK '+case+' '+filename).encode('utf-8'); (out/filename).write_bytes(raw)
                        r['artifact_sha256'][filename]=evaluation.sha(raw)
                    (out/'verify-result.json').write_text(json.dumps(r['verification']),encoding='utf-8')
                (out/'result.json').write_text(json.dumps(r),encoding='utf-8')
                return r
            def runner(argv,**kwargs):
                self.assertFalse(kwargs['shell'])
                if argv[1]=='--version': return subprocess.CompletedProcess(argv,0,'mock CLI','')
                e=state['entry']; case=e['case']; folder=(root/'design/cad-harness-verify/test'/case) if e['group']=='dev' else base/'test'/case
                if argv[1]=='exec':
                    state['calls']+=1; call=state['calls']; clock[0]+=.1
                    question=e['route'] in ('ask','completion') and call==1
                    if question:
                        fields=json.loads((folder/'rubric.json').read_text(encoding='utf-8'))['required_fields']
                        if case=='C2' and e['round']==1: fields=['hole_positions']
                        text='invalid' if case=='C2' and e['round']==3 else json.dumps({'needs_clarification':fields})
                    elif e['route']=='source':
                        if case=='K1' and e['round']==1 and call==1: text='invalid'
                        elif call==(2 if case=='K1' and e['round']==1 else 1): text='{"unsupported":["geometry"]}'
                        else: text=(folder/'positive.py').read_text(encoding='utf-8')
                    else:
                        if e['group']=='dev':
                            g=json.loads((folder/'gold.json').read_text(encoding='utf-8'))
                            value=dict(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world',
                                regions=[dict(bounds=g['bbox'])],holes=[{k:v for k,v in h.items() if k!='through'} for h in g['holes']],
                                pockets=[{k:v for k,v in p.items() if k!='sharp'} for p in g['pockets']],finish=g['finish'])
                        else: value=spec(case)
                        text=json.dumps(value)
                    Path(argv[argv.index('-o')+1]).write_bytes(text.encode('utf-8'))
                    return subprocess.CompletedProcess(argv,0,'{"type":"turn.completed","usage":{"input_tokens":11,"output_tokens":2}}','')
                self.assertEqual(Path(argv[2]).name,'cad_run.py'); state['cads']+=1; clock[0]+=.1
                source,out,gold=[Path(argv[argv.index(k)+1]) for k in ('--script','--out-dir','--gold')]
                r=result(out,source.read_bytes(),gold,case,generator=argv[argv.index('--generator')+1],
                         failure=(e['group']=='fault' or time_stop['active'] and e['id']=='geometry-W6-r1') and state['cads']==1,
                         timeout=int(argv[argv.index('--timeout-s')+1]))
                return subprocess.CompletedProcess(argv,1 if r['status']=='failed' else 0,json.dumps(r),'')
            def mvp(name,codex,input_text,gold,**kwargs):
                guard=kwargs['guard']; q=guard.before_call(); clock[0]+=.1
                where=evaluation.eval_mvp.run_path(root,name); out=where/'a1-mvp1'; case=json.loads(gold.read_text(encoding='utf-8'))['case_id']
                r=result(out,b'def build(doc): return doc\n',gold,case,profile='mvp-v1')
                rep=dict(schema='cad-harness.cad_agent.mvp1',run_id=name,task_id=case,mode='description',
                    description_sha256=cad_agent.digest(input_text),gold_sha256=evaluation.sha(gold.read_bytes()),wall_ms=100,status='ok',
                    llm_calls=1,cad_attempts=1,unsupported_to_source=False,message_code='completed',
                    calls=[dict(kind='interpretation',prompt_sha256=cad_agent.digest(input_text),quota_snapshot=q,
                        usage=[dict(values=dict(input_tokens=11,output_tokens=2))])],
                    attempts=[dict(source_sha256=r['script_sha256'],out_dir=out.relative_to(root).as_posix(),result=r)],
                    final_out_dir=out.relative_to(root).as_posix(),cli_version='mock CLI',agents_sha256=cad_agent.agents_identity(root),settings=frozen['settings'])
                for k,p in [('skill_sha256','skills/freecad-modeling/SKILL.md'),('schema_sha256','design/cad-harness-mvp/build-schema.json'),
                    ('compiler_sha256','tools/cad_spec.py'),('probe_sha256','tools/cad_spec_probe.py')]: rep[k]=frozen['files'][p]
                (where/'driver-run.json').write_text(json.dumps(rep),encoding='utf-8'); return rep,0
            def legacy(args,root):
                out=Path(args.out_dir); out.mkdir(parents=True); clock[0]+=.1
                good=out.name.split('-r1-mvp1')[0].endswith('good')
                (out/'result.json').write_text(json.dumps(dict(probe_pass=good,document_closed=True,cleanup_status='exited',cad_exit_code=0)),encoding='utf-8')
            with patch.object(driver,'run_driver',side_effect=enter_driver),patch.object(cad_agent,'run_mvp_driver',side_effect=mvp),\
                 patch.object(evaluation.cad_run,'run_attempt',side_effect=legacy),patch('builtins.print'):
                run=evaluation.run('mock-suite',snapshot,root=root,runner=runner,clock=lambda:clock[0],now=lambda:NOW)
            self.assertIsNone(run['stop_reason'],[(r['id'],r.get('error'),r.get('stop_reason')) for r in run['rows'] if r.get('stop_reason')])
            self.assertEqual((len(run['rows']),run['real_calls'],run['dev_calls']),(60,82,4))
            launch=Mock(side_effect=AssertionError('aggregate must launch nothing'))
            with patch('subprocess.run',launch): doc=evaluation.aggregate('mock-suite','mock-suite',root,clock=lambda:clock[0])
            launch.assert_not_called()
            self.assertTrue(doc['summary']['bar_met'],doc['summary'])
            self.assertEqual((doc['summary']['completion']['C2']['completion']['successes'],
                doc['summary']['completion']['C2']['completion']['planned']),(1,3))
            self.assertEqual(doc['summary']['completion']['C2']['conditional_completion']['denominator'],1)
            self.assertEqual(doc['summary']['repair_calls'],6)
            self.assertEqual(doc['summary']['parse_repair_calls'],1)
            self.assertIsNone(doc['provider_tokens']['completion']['reasoning_output_tokens'])
            self.assertEqual(doc['provider_tokens']['completion']['input_tokens'],10*11)
            # Lose the repair reservation after a settled first failure. Later
            # episodes keep the same suite clock/counters, and aggregate keeps
            # the partial episode's timeout and wall without a version stop.
            time_stop['active']=True
            begin_repair=Budget.begin_repair
            def delayed_repair(budget):
                if state['entry']['id']=='geometry-W6-r1': clock[0]=budget.started+450.01
                return begin_repair(budget)
            with patch.object(driver,'run_driver',side_effect=enter_driver),patch.object(cad_agent,'run_mvp_driver',side_effect=mvp),\
                 patch.object(evaluation.cad_run,'run_attempt',side_effect=legacy),patch.object(Budget,'begin_repair',delayed_repair),patch('builtins.print'):
                timed=evaluation.run('mock-time-suite',snapshot,root=root,runner=runner,clock=lambda:clock[0],now=lambda:NOW)
            missed=next(r for r in timed['rows'] if r['id']=='geometry-W6-r1')
            next_row=timed['rows'][missed['sequence']]
            self.assertIsNone(timed['stop_reason']); self.assertIsNone(missed['stop_reason'])
            self.assertEqual(missed['episode_stop_reason'],'repair_time_reservation_lost')
            self.assertEqual(missed['repair_not_attempted_reason'],'repair_time_reservation_lost')
            self.assertEqual((missed['failure_class'],missed['completed'],missed['passed'],missed['repair_calls']),('timeout',False,False,0))
            self.assertTrue(missed['repair_eligible']); self.assertTrue(next_row['completed'])
            self.assertGreaterEqual(missed['wall_s'],450)
            self.assertEqual(timed['deadline_monotonic']-timed['started_monotonic'],10800)
            with patch('subprocess.run',launch): timed_doc=evaluation.aggregate('mock-time-suite','mock-time-suite',root,clock=lambda:clock[0])
            launch.assert_not_called()
            timed_part=timed_doc['summary']['per_part']['W6']
            self.assertIsNone(timed_doc['summary']['stop_reason']); self.assertFalse(timed_doc['summary']['bar_met'])
            self.assertEqual((timed_part['planned'],timed_part['completed'],timed_part['successes']),(3,2,2))
            self.assertIsNone(timed_part['wilson95']); self.assertGreaterEqual(timed_part['wall_s']['maximum'],450)
            with self.assertRaisesRegex(ValueError,'aggregate_exists'): evaluation.aggregate('mock-suite','mock-suite',root)
            with self.assertRaisesRegex(ValueError,'prefix_exists'): evaluation.run('mock-suite',snapshot,root=root,runner=launch)
            cli.write_bytes(b'CHANGED MOCK EXECUTABLE')
            with self.assertRaisesRegex(Stop,'cli_sha_mismatch'): evaluation.load(root)
            cli.write_bytes(b'MOCK EXECUTABLE ONLY')
            c=base/'test/C2/answer.txt'; c.write_bytes(c.read_bytes()+b' ')
            with self.assertRaisesRegex(Stop,'sha_mismatch'): evaluation.load(root)
            launch.assert_not_called()

    def test_incomplete_cohort_has_no_interval_and_null_tokens_are_not_zero(self):
        order=json.loads((BASE/'run-order.json').read_text(encoding='utf-8'))
        rows=[evaluation.empty_row(e,'mock-'+e['id']+'-mvp1') for e in order['entries']]
        for r in rows:
            r.update(completed=True,passed=True,sol_calls=1,cad_attempts=0,wall_s=1,failure_class=None)
            if r['group']=='fault': r.update(fault=dict(established=True,detected=True,reached=True),repair_calls=1)
            if r['group']=='completion': r.update(completion_reached=True,initial_q_score=1)
        rows[-7]['completed']=False
        summary=evaluation.summarize(rows,order)
        self.assertTrue(summary['core_complete']); self.assertTrue(summary['bar_met'])
        self.assertIsNone(summary['completion']['C3']['completion']['wilson95'])
        self.assertIsNone(summary['completion']['C3']['conditional_completion']['wilson95'])
        self.assertIsNone(evaluation.metric(rows)['provider_tokens']['input_tokens'])


if __name__=='__main__': unittest.main()
