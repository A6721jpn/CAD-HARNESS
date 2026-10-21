"""Minimum signed v3 contracts; model/CAD launches are mocked."""
from datetime import datetime,timezone,timedelta
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from tools import cad_agent,cad_spec,cad_run_freecad,cad_verify_v3_probe as probe,cad_verify_v3_agent as driver,eval_verify_v3 as evaluation,smoke_verify_v3 as smoke
from tools.cad_verify_v3_guard import Budget,Guard,Fault,Stop
from tools.cad_verify_v3_diagnostics import finalize
from tools.test_support import start_tempdirs,stop_tempdirs

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/evaluation.DESIGN
NOW=datetime(2026,10,13,4,0,tzinfo=timezone.utc)
REVIEW_RUN='mock-v3-solfix-r1-mvp1'
SOURCE='import FreeCAD\nimport Part\nimport Sketcher\ndef build(doc):\n    return doc.addObject("PartDesign::Body", "Body")\n'

def setUpModule():
    global _temp_patches
    _temp_patches=start_tempdirs()
def tearDownModule():stop_tempdirs(_temp_patches)
def realistic_driving(sketch):
    def get_driving(index):
        c=sketch.Constraints[index]
        if c.Type not in ('Distance','DistanceX','DistanceY','Radius','Diameter','Angle'):
            raise ValueError('Invalid constraint id')
        return getattr(c,'Driving',True)
    return get_driving

def spec(case):
    g=probe.load_gold(BASE/'test'/case/'gold.json')
    return dict(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world',regions=[dict(bounds=g['bbox'])],
        holes=[{k:v for k,v in h.items() if k!='through'} for h in g['holes']],pockets=[{k:v for k,v in p.items() if k!='sharp'} for p in g['pockets']],finish=g['finish'])

class V3Contracts(unittest.TestCase):
    def test_attempt_identity_binds_sealed_gold_not_scoring_stratum(self):
        from tools import cad_verify_v4_live as live
        for group,profile in (("mvp","mvp-v1"),("geometry","verify-v3")):
            with self.subTest(profile=profile),tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve()
                where=root/"reports/cad-run/request-mvp1"
                attempt=where/"a1-mvp1"
                attempt.mkdir(parents=True)
                source=b"# independent DEV metadata fixture; never executed\n"
                gold_bytes=json.dumps(dict(case_id="DEV-SAVED-TASK")).encode("utf-8")
                gold=root/"gold.json"
                gold.write_bytes(gold_bytes)
                (attempt/"gold.json").write_bytes(gold_bytes)
                (attempt/"input.py").write_bytes(source)
                result=dict(schema="cad-harness.cad_run.v0",task_id="DEV-SAVED-TASK",
                    probe_profile=profile,script_sha256=evaluation.sha(source),
                    gold_sha256=evaluation.sha(gold_bytes),status="failed",
                    geometry_ok=False,editability_ok=None,probe_pass=False,
                    stage_statuses=dict(build="pass",geometry="fail",editability="not_reached",
                                        export="not_reached",reimport="not_reached"),
                    stage_measurements=dict(build={},geometry={},editability=None,export=None,reimport=None))
                record=dict(out_dir=attempt.relative_to(root).as_posix(),source_sha256=evaluation.sha(source),
                    result=result,stage="initial",attempt=1,started_elapsed_s=0,ended_elapsed_s=1,
                    build_timeout_s=300,reimport_timeout_s=300)
                report=dict(status="failed",wall_ms=1000,attempts=[record],llm_calls=1)
                entry=dict(group=group,case="DEV-SCORING-STRATUM",route="mvp" if group=="mvp" else "source")
                (attempt/"result.json").write_text(json.dumps(result),encoding="utf-8")
                evaluation.check_attempts(root,entry,report,where,gold)
                row=live.score_episode(entry,report,"independent-dev",wall_s=1,active_s=1)
                self.assertEqual((row["completed"],row["passed"],row["final"]["geometry"]),
                                 (True,False,False))
                # A result using the stratum instead of its bound gold identity is still refused.
                result["task_id"]=entry["case"]
                (attempt/"result.json").write_text(json.dumps(result),encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"attempt_gold_binding"):
                    evaluation.check_attempts(root,entry,report,where,gold)

    def test_solfix_a2_fault_source_sha_mirrors_driver_reextraction_for_crlf_fixture(self):
        crlf=SOURCE.replace('\n','\r\n')
        expected=hashlib.sha256(cad_agent.source_from_final(crlf).encode('utf-8')).hexdigest()
        self.assertEqual(evaluation.fault_source_sha(crlf),expected)
        self.assertEqual(evaluation.fault_source_sha(SOURCE),hashlib.sha256(SOURCE.encode('utf-8')).hexdigest())

    def test_solfix_a1_cad_timeout_cap_with_no_deadline_guard(self):
        self.assertEqual(driver.cap_timeout(300,math.inf),300)
        self.assertEqual(driver.cap_timeout(300,120.9),120)
        self.assertEqual(driver.cap_timeout(60,500.0),60)
    def test_active_respects_freecad_datum_api_and_geometric_activity(self):
        types=('Distance','DistanceX','DistanceY','Radius','Diameter','Angle',
            'Coincident','Horizontal','Vertical','Equal','Symmetric','PointOnObject','Parallel')
        sketch=NS(Constraints=[NS(Type=kind,Driving=False) for kind in types],getActive=lambda i:True)
        queried=[]
        native=realistic_driving(sketch)
        def get_driving(index):queried.append(index);return native(index)
        sketch.getDriving=get_driving
        for i,kind in enumerate(types):
            with self.subTest(kind=kind):
                self.assertEqual(probe.active(sketch,i),i>=6)
                sketch.Constraints[i].Driving=True
                self.assertTrue(probe.active(sketch,i))
        self.assertEqual(queried,[i for i in range(6) for _ in range(2)])
        queried.clear();sketch.getActive=lambda i:False
        for i in range(len(types)):self.assertFalse(probe.active(sketch,i))
        self.assertEqual(queried,[])
        with self.assertRaisesRegex(ValueError,'Invalid constraint id'):native(6)

    def test_missing_controls_stop_before_output_allocation_or_CAD(self):
        matrix=json.loads((BASE/'dev/native-matrix.json').read_text(encoding='utf-8'))
        files={'tools/fixtures/verify_v3_native.py',evaluation.DESIGN+'/dev/native-matrix.json',evaluation.DESIGN+'/dev/D1/gold.json'}
        for c in ('G1','G2','G3','G4','G5','G6','S3','A4','C4','C5','F4','F5','F6'):
            files.update(evaluation.DESIGN+'/test/'+c+'/'+name for name in ('positive.py','negative.py','offline.json'))
        files.update(evaluation.DESIGN+'/test/'+c+'/fault.json' for c in ('F4','F5','F6'))
        files.update((evaluation.DESIGN+'/test/F4/candidate.py',evaluation.DESIGN+'/test/F5/candidate.py',evaluation.DESIGN+'/test/F6/candidate.json'))
        files.update(e['source'] for e in matrix['entries'])
        for e in matrix['parameter_edits']:files.update((e['source'],e['folder']+'/gold.json'))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'repo'
            for name in files:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(json.dumps(matrix).encode() if name.endswith('native-matrix.json') else b'mock presence only; never executed')
            evaluation.require_controls(root)
            missing_cases=[('tools/fixtures/verify_v3_native.py',True),
                (evaluation.DESIGN+'/test/G1/positive.py',False),
                (matrix['entries'][0]['source'],True),
                (matrix['parameter_edits'][0]['folder']+'/gold.json',True)]
            for index,(name,dev_only) in enumerate(missing_cases):
                with self.subTest(missing=name):
                    path=root/name;original=path.read_bytes()
                    path.unlink()  # disposable mock repository only
                    with patch.object(smoke,'ROOT',root),patch.object(cad_agent,'new_run_dir') as allocation,patch.object(smoke.cad_run,'run_attempt') as launch,patch.object(evaluation,'data_check') as data:
                        with self.assertRaises(Stop) as error:smoke.smoke('review-fixes-preflight-r%d-mvp1'%(index+1),dev_only=dev_only)
                        self.assertIn('independent_native_controls_pending:',str(error.exception));self.assertIn(name,str(error.exception))
                        allocation.assert_not_called();launch.assert_not_called();data.assert_not_called()
                    path.write_bytes(original)

    def drive(self,d,case,outputs,fail=False,route='spec',clock=None,after_cad=None,fault=None,preview=False,provider=False,sleeper=None,cap=163,rerun_name=None):
        root=Path(d)/'repo';folder=BASE/'test'/case;calls=[];cads=[]
        for name in ('skills/freecad-modeling/SKILL.md','design/cad-harness-mvp/build-schema.json'):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
        for p in folder.iterdir():
            dest=root/evaluation.DESIGN/'test'/case/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
        def runner(argv,**kw):
            self.assertFalse(kw['shell'])
            if argv[1]=='--version':return subprocess.CompletedProcess(argv,0,'MOCK CLI','')
            if argv[1]=='exec':
                calls.append((argv,kw));value=outputs[len(calls)-1]
                if clock:clock[0]+=10
                if isinstance(value,dict):return subprocess.CompletedProcess(argv,value.get('exit',1),value['stdout'],value.get('stderr',''))
                Path(argv[argv.index('-o')+1]).write_text(value,encoding='utf-8')
                return subprocess.CompletedProcess(argv,0,'{"type":"turn.completed","usage":{"input_tokens":11,"output_tokens":2}}','')
            self.assertEqual(argv[argv.index('--probe-profile')+1],'verify-v3');cads.append((argv,kw))
            source,out,gold=[Path(argv[argv.index(k)+1]) for k in ('--script','--out-dir','--gold')]
            out.mkdir();(out/'input.py').write_bytes(source.read_bytes());(out/'gold.json').write_bytes(gold.read_bytes())
            r=dict(schema='cad-harness.cad_run.v0',task_id=case,probe_profile='verify-v3',script_sha256=evaluation.sha(source.read_bytes()),gold_sha256=evaluation.sha(gold.read_bytes()),
                status='ok',geometry_ok=True,editability_ok=True,probe_pass=True,probe_status='pass',script_completed=True,verification_pass=True,document_closed=True,
                cleanup_status='exited',cad_exit_code=0,verification_cleanup_status='exited',verification_exit_code=0,owned_pid=100,verification_pid=200,
                verification=dict(verification_pass=True,document_closed=True),failed_phase=None,next_actor=None,generator=argv[argv.index('--generator')+1],
                measurements={'volume_mm3':123,'editability':{'native_valid':True}},stage_statuses=dict.fromkeys(('build','geometry','editability','export','reimport'),'pass'),
                stage_measurements=dict.fromkeys(('build','geometry','editability','export','reimport')))
            if fail and len(cads)==1:
                r.update(status='failed',geometry_ok=True,editability_ok=False,probe_pass=False,probe_status='predicate_fail',failed_phase='probe',next_actor='sol',code_owner='script',predicate_diff=['editability'],verification=None,verification_pid=None,verification_pass=False)
                r['stage_statuses'].update(editability='fail',export='not_reached',reimport='not_reached')
            finalize(r);(out/'result.json').write_text(json.dumps(r),encoding='utf-8')
            if clock:clock[0]+=10
            if after_cad:after_cad()
            return subprocess.CompletedProcess(argv,0 if r['status']=='ok' else 1,json.dumps(r),'')
        snapshot=Path(d)/'quota.json';snapshot.write_text(json.dumps(dict(snapshot_id='mock',observed_at=NOW.isoformat(),used_percent=20)))
        guard=Guard(snapshot,call_budget=cap,clock=(lambda:clock[0]) if clock else None,now=lambda:NOW)
        rubric=json.loads((folder/'rubric.json').read_text(encoding='utf-8')) if (folder/'rubric.json').is_file() else None
        answer=(folder/'answer.txt').read_text(encoding='utf-8') if route=='completion' else None
        invoke=evaluation.rerun2_driver if rerun_name else driver.run_driver
        report,code=invoke(rerun_name or REVIEW_RUN,'MOCK-NO-SOL',(folder/'description.txt').read_text(encoding='utf-8'),folder/'gold.json' if (folder/'gold.json').is_file() else None,
            root=root,runner=runner,guard=guard,route=route,rubric=rubric,answer=answer,fault=fault,preview=preview,provider_retry=provider,sleeper=sleeper)
        return root,report,code,calls,cads,guard

    def test_rerun2_allowlist_rejects_other_partial_and_duplicate_ids(self):
        wanted='geometry-G5-r1,geometry-G1-r2'
        self.assertEqual(evaluation.rerun2_ids(wanted),{'geometry-G5-r1','geometry-G1-r2'})
        with patch.object(evaluation,'load') as load,patch.object(driver,'run_driver') as launch:
            for bad in ('geometry-G6-r1,geometry-G1-r2','geometry-G5-r1','geometry-G5-r1,geometry-G5-r1',wanted+',q-A5-r5'):
                with self.subTest(ids=bad),self.assertRaisesRegex(Stop,'rerun2_id_allowlist'):
                    evaluation.rerun('mock-rerun2',bad,'unused','unused')
            load.assert_not_called();launch.assert_not_called()

    def test_rerun2_existing_targets_refused_before_loading_or_launching(self):
        for tail in ('suite','geometry-G5-r1','geometry-G1-r2','execution'):
            with self.subTest(target=tail),tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();prefix='mock-rerun2'
                if tail=='suite':target=Path(str(evaluation.paths(root,prefix))+'-rerun2')
                else:target=evaluation.driver_path(root,evaluation.run_name(prefix,dict(id='geometry-G5-r1' if tail=='execution' else tail))+'-rerun2'+('-mvp1' if tail=='execution' else ''))
                target.mkdir(parents=True)
                with patch.object(evaluation,'load') as load,patch.object(driver,'run_driver') as launch:
                    with self.assertRaisesRegex(Stop,'rerun2_prefix_exists'):
                        evaluation.rerun(prefix,'geometry-G5-r1,geometry-G1-r2','unused','unused',root=root)
                    load.assert_not_called();launch.assert_not_called()

    def test_rerun2_unchanged_driver_and_relocated_artifact_bindings(self):
        name='mock-rerun2-geometry-G5-r1-mvp1-rerun2'
        with tempfile.TemporaryDirectory() as d:
            root,report,code,calls,cads,guard=self.drive(d,'G5',[json.dumps({'unsupported':['native source required']}),SOURCE],
                route='source',provider=True,rerun_name=name)
            self.assertEqual((code,len(calls),len(cads),guard.calls),(0,2,1,2))
            self.assertEqual(report['run_id'],name);self.assertEqual(report['execution_run'],name+'-mvp1')
            where=evaluation.driver_path(root,name)
            self.assertTrue(where.is_dir());self.assertFalse(evaluation.driver_path(root,name+'-mvp1').exists())
            self.assertEqual(json.loads((where/'driver-run.json').read_text(encoding='utf-8')),report)
            evaluation.check_transport(report,where)
            for c in report['calls']:
                for key,item in c['context_artifacts'].items():
                    self.assertTrue((root/item['path']).is_relative_to(where))
                    self.assertEqual(evaluation.sha((root/item['path']).read_bytes()),c[key+'_sha256'])
            attempt=report['attempts'][0]
            self.assertEqual(evaluation.sha((root/attempt['out_dir']/'input.py').read_bytes()),attempt['source_sha256'])

    def test_rerun2_mock_execution_and_substitution_preserve_every_other_row(self):
        prefix='mock-rerun2';order=json.loads((BASE/'run-order.json').read_text(encoding='utf-8'))
        identity_files=('skills/freecad-modeling/SKILL.md','design/cad-harness-mvp/build-schema.json','tools/cad_spec.py',
            'tools/cad_verify_v3_probe.py','tools/cad_verify_probe.py')
        old=dict(schema='cad-harness.verify-sha.v3',profile='verify-v3',version='verify-v3-reviewed-r1',local_commit='32dab3a',plan_commit='fd7e215',
            cli=dict(path='MOCK-NO-SOL',version='MOCK CLI',sha256='mock'),settings=dict(model=cad_agent.MODEL),agents_sha256={},
            files={p:'original-'+p for p in (*evaluation.SOLFIX_CODE,*identity_files)})
        base_manifest=copy.deepcopy(old);base_manifest['version']=evaluation.SOLFIX_VERSION
        base_manifest['files'].update({p:'solfix-'+p for p in evaluation.SOLFIX_CODE|evaluation.SOLFIX_DOCS})
        current=copy.deepcopy(base_manifest)
        current['files'].update({p:'rerun2-'+p for p in ('tools/eval_verify_v3.py','tools/test_verify_v3.py')})
        driver_identity=dict(cli_version='MOCK CLI',agents_sha256={},settings=current['settings'],
            **{k:current['files'][p] for k,p in zip(('skill_sha256','schema_sha256','compiler_sha256','probe_sha256','shared_probe_sha256'),identity_files)})
        with tempfile.TemporaryDirectory() as d:
            root=(Path(d)/'repo').resolve();base=root/evaluation.DESIGN;base.mkdir(parents=True)
            archive=base/'SHA256.run-r1.json';evaluation.write_json(archive,old);evaluation.write_json(base/'SHA256.json',current)
            evaluation.write_json(base/'run-order.json',order)
            first=dict(schema='cad-harness.verify-run.v3',profile='verify-v3',version=old['version'],prefix=prefix,
                started_monotonic=1000,deadline_monotonic=11800,wall_s=2366.75,real_calls=54,call_budget=163,
                sha_manifest=evaluation.sha(archive.read_bytes()),frozen_sha256=old['files'],rows=[])
            rows=[]
            for e in order['entries']:
                original=evaluation.empty_row(e,evaluation.run_name(prefix,e))
                if e['sequence']<=46:original.update(completed=True,passed=e['id'] not in evaluation.RERUN2_IDS,sol_calls=e['min_calls'])
                if e['id'] in evaluation.RERUN2_IDS:original['failure_class']='interpretation'
                if e['sequence']==47:original['sol_calls']=1
                first['rows'].append(original)
                row=copy.deepcopy(original) if e['sequence']<=46 else evaluation.empty_row(e,evaluation.run_name(prefix,e)+'-resume1')
                row.update(completed=True,passed=e['id'] not in evaluation.RERUN2_IDS,sol_calls=e['min_calls'],cad_attempts=0,wall_s=1,
                    segment=1 if e['sequence']<=46 else 2,initial_q_score=1,completion_reached=e['group']=='completion')
                if e['group']=='fault':row.update(fault=dict(reached=True,established=True,detected=True),repair_calls=1)
                rows.append(row)
            original_dir=evaluation.paths(root,prefix);original_dir.mkdir(parents=True)
            evaluation.write_json(original_dir/'suite-run.json',first)
            evaluation.write_json(original_dir/'plan.json',dict(version=old['version'],sha_manifest=first['sha_manifest'],entries=order['entries'],
                started_monotonic=1000,deadline_monotonic=11800))
            resumed=Path(str(original_dir)+'-resume1');resumed.mkdir()
            evaluation.write_json(resumed/'suite-run.json',dict(sha_manifest='solfix-manifest',frozen_sha256=base_manifest['files']))
            evaluation.write_json(resumed/'plan.json',dict(mock=True))
            annotations=[dict(id=id_,run=evaluation.run_name(prefix,next(e for e in order['entries'] if e['id']==id_)),
                original_score_preserved=True,summary=dict(provider_rejected=True)) for id_ in sorted(evaluation.RERUN2_IDS)]
            prior=dict(schema='cad-harness.verify-aggregate.v3',profile='verify-v3',prefix=prefix,version=evaluation.SOLFIX_VERSION,
                plan_commit='fd7e215',sha_manifest='solfix-manifest',frozen_sha256=base_manifest['files'],real_calls=84,transport_attempts=84,
                groups={g:[r for r in rows if r['group']==g] for g in evaluation.GROUPS},summary=evaluation.summarize(rows,order),
                historical_provider_attempts=annotations,provider_rejected_attempts=[],
                segments=[dict(sha_manifest=first['sha_manifest'],suite_sha256=evaluation.sha((original_dir/'suite-run.json').read_bytes())),
                    dict(suite_sha256=evaluation.sha((resumed/'suite-run.json').read_bytes()))])
            source=root/'reports/aggregate-verify-v3-mock-solfix.json';evaluation.write_json(source,prior);source.with_suffix('.csv').write_text('mock csv',encoding='utf-8')
            for case in ('G5','G1'):
                dest=base/'test'/case;dest.mkdir(parents=True)
                for p in (BASE/'test'/case).iterdir():
                    if p.is_file():(dest/p.name).write_bytes(p.read_bytes())
            quota=root/'quota.json';evaluation.write_json(quota,dict(snapshot_id='mock',observed_at=NOW.isoformat(),used_percent=20))
            preserved={p:p.read_bytes() for p in root.rglob('*') if p.is_file()};executed=[]
            def fake_driver(name,codex,raw,gold,**kw):
                guard=kw['guard'];self.assertIsNone(guard.deadline);self.assertEqual(guard.call_budget,163)
                self.assertEqual(guard.calls,105+2*len(executed));self.assertTrue(kw['provider_retry'])
                self.assertEqual((kw['route'],kw['max_calls']),('source',4))
                kw['runner']([codex,'--version'])
                guard.before_call();guard.before_call();executed.append(name)
                out=cad_agent.new_run_dir(root,name)
                report=dict(provider_policy=driver.PROVIDER_POLICY,prior_provider_attempts=0,calls=[dict(provider_rejected=False)]*2,
                    attempts=[],run_id=name,llm_calls=2)
                evaluation.write_json(out/'driver-run.json',report);return report,0
            def fake_record(repo,e,name):
                self.assertIn(e['id'],evaluation.RERUN2_IDS)
                row=evaluation.empty_row(e,name);row.update(completed=True,passed=True,sol_calls=2,cad_attempts=0,wall_s=1,
                    unsupported_to_source=True,unsupported_origin='model',driver_identity=driver_identity)
                return row
            def evidence(repo,row):return next(a for a in annotations if a['id']==row['id'])
            def mock_runner(argv,**kw):return subprocess.CompletedProcess(argv,0,'MOCK CLI','')
            with (patch.object(evaluation,'verify_frozen'),patch.object(evaluation,'historical_provider',side_effect=evidence),
                    patch.object(driver,'run_driver',side_effect=fake_driver),patch.object(evaluation,'record',side_effect=fake_record) as scored):
                result=evaluation.rerun(prefix,'geometry-G1-r2,geometry-G5-r1',quota,archive,root=root,runner=mock_runner,clock=lambda:20000,now=lambda:NOW)
                selected=[e for e in order['entries'] if e['id'] in evaluation.RERUN2_IDS]
                self.assertEqual(executed,[evaluation.run_name(prefix,e)+'-rerun2-mvp1' for e in selected])
                self.assertEqual((result['inherited_calls'],result['real_calls'],result['total_real_calls']),(105,4,109))
                self.assertIsNone(result['stop_reason']);self.assertEqual(len(result['quota_snapshots']),4)
                final=evaluation.aggregate(prefix,'mock-solfix-rerun2',root=root,run_manifest=archive,rerun2=True)
                self.assertTrue(final['summary']['bar_met']);self.assertEqual(final['total_charged_calls'],109)
                self.assertEqual((final['real_calls'],final['archived_charged_calls']),(88,21))
                self.assertEqual({r['id'] for r in final['substituted_rows']},evaluation.RERUN2_IDS)
                before=[r for rs in prior['groups'].values() for r in rs];after=[r for rs in final['groups'].values() for r in rs]
                self.assertEqual([r for r in before if r['id'] not in evaluation.RERUN2_IDS],[r for r in after if r['id'] not in evaluation.RERUN2_IDS])
                for pair in final['substituted_rows']:
                    self.assertEqual(pair['original'],next(r for r in before if r['id']==pair['id']))
                    self.assertFalse(pair['original']['passed']);self.assertTrue(pair['replacement']['passed'])
                self.assertEqual(scored.call_count,4)
                with self.assertRaisesRegex(Stop,'aggregate_exists_or_linked'):
                    evaluation.aggregate(prefix,'mock-solfix-rerun2',root=root,run_manifest=archive,rerun2=True)
                self.assertTrue(all(p.read_bytes()==data for p,data in preserved.items()))

    def test_solfix_exact_error_full_output_and_bounded_capture(self):
        rejection=json.dumps(dict(type='event_msg',payload=dict(type='task_complete',error=dict(codex_error_info='server_overloaded'))))
        self.assertTrue(driver.provider_summary(rejection)['provider_rejected'])
        for bad in (rejection.replace('server_overloaded','server_overloaded_more'),
                json.dumps(dict(message='server_overloaded')),rejection+'\n'+json.dumps(dict(type='item.completed',item=dict(type='agent_message',text='partial'))),
                rejection+'\n'+json.dumps(dict(type='response_item',payload=dict(type='message',role='assistant',content=[dict(text='partial')])))):
            self.assertFalse(driver.provider_summary(bad)['provider_rejected'])
        self.assertFalse(driver.provider_summary(rejection,'a final response')['provider_rejected'])
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'episode';out.mkdir();row=dict(call=1)
            # Typed rejection before the retained tail is still found in the full stream.
            stdout=rejection+'\n'+('x'*20000);completed=subprocess.CompletedProcess([],1,stdout,'e'*20000)
            driver.capture_transport(out,root,row,completed,driver.provider_summary(stdout))
            self.assertTrue(row['provider_summary']['provider_rejected'])
            for item in row['transport_artifacts'].values():
                self.assertLessEqual((root/item['path']).stat().st_size,16384)
                self.assertEqual(evaluation.sha((root/item['path']).read_bytes()),item['sha256'])

    def test_solfix_streaming_capture_reads_full_events_without_full_output_buffers(self):
        session='12345678-1234-1234-1234-123456789abc'
        events=[dict(type='thread.started',thread_id=session),dict(type='error',codex_error_info='server_overloaded')]
        stdout=('\n'.join(json.dumps(e) for e in events)+'\n'+'é'*20000).encode('utf-8')
        stderr=('警告'*20000).encode('utf-8')
        class Process:
            returncode=1
            def __init__(self,*args,**kwargs):
                self.stdout=io.BytesIO(stdout);self.stderr=io.BytesIO(stderr)
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def wait(self,timeout=None):return self.returncode
            def kill(self):pass
        with patch.object(driver.subprocess,'Popen',side_effect=Process) as popen:
            completed=driver.bounded_run(['MOCK-NO-SOL','exec'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
        self.assertEqual(popen.call_args.kwargs['stdout'],subprocess.PIPE)
        self.assertNotIn('capture_output',popen.call_args.kwargs)
        self.assertTrue(completed.provider_summary['provider_rejected']);self.assertEqual(completed.exec_metadata,(session,None))
        for key,raw in (('stdout',stdout),('stderr',stderr)):
            captured=completed.transport_capture[key]
            self.assertLessEqual(len(captured['tail']),16384)
            self.assertEqual(captured['full_bytes'],len(raw));self.assertEqual(captured['full_sha256'],evaluation.sha(raw))
            self.assertLessEqual(len(getattr(completed,key).encode('utf-8')),16384)
        # A message or uninspectable event outside the tail prevents a resend.
        capture=driver.StreamCapture(parse=True)
        capture.feed(json.dumps(dict(type='item.completed',item=dict(type='agent_message',text='partial')))+'\n')
        capture.feed('x'*(driver.EVENT_CHARS+1)+'\n');capture.feed(json.dumps(events[1]));capture.finish()
        self.assertFalse(capture.summary()['provider_rejected']);self.assertFalse(capture.summary()['parse_complete'])
        with patch.object(Process,'wait',side_effect=[subprocess.TimeoutExpired('mock',10),1]),patch.object(driver.subprocess,'Popen',side_effect=Process):
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                driver.bounded_run(['MOCK-NO-SOL','exec'],capture_output=True,timeout=10)
        self.assertLessEqual(len(caught.exception.stdout.encode('utf-8')),16384)
        self.assertEqual(caught.exception.transport_capture['stdout']['full_bytes'],len(stdout))

    def test_solfix_unlimited_transport_unbudgeted_and_identical(self):
        rejection=dict(stdout=json.dumps(dict(type='error',codex_error_info='server_overloaded')),stderr='provider refusal')
        waits=[]
        with tempfile.TemporaryDirectory() as d:
            root,r,code,calls,cads,g=self.drive(d,'A5',[rejection]*5+[json.dumps({'needs_clarification':['pocket_depth']})],
                route='ask',provider=True,sleeper=waits.append,cap=1)
            self.assertEqual(code,0);self.assertEqual(len(calls),6);self.assertEqual(g.calls,1)
            self.assertEqual(r['llm_calls'],1);self.assertEqual(r['logical_calls'],1);self.assertEqual(r['provider_rejected_attempts'],5)
            self.assertEqual(r['budget_counts']['question'],1);self.assertEqual(r['parse_repairs'],0);self.assertEqual(r['repair_calls'],0)
            self.assertEqual(r['provider_wait_s'],3000);self.assertEqual(sum(waits),3000);self.assertTrue(all(t<=60 for t in waits))
            self.assertTrue(all(argv==calls[0][0] for argv,_ in calls));self.assertEqual(r['first_response_call'],6)
            self.assertEqual(len(g.snapshots),6);self.assertTrue(all(c['quota_snapshot']['decision']=='allow' for c in r['calls']))
            evaluation.check_transport(r,root/'reports/cad-run'/REVIEW_RUN)
        with tempfile.TemporaryDirectory() as d:
            root,r,code,calls,cads,g=self.drive(d,'A5',[dict(stdout=json.dumps(dict(type='error',codex_error_info='rate_limit')))],route='ask',provider=True,sleeper=lambda t:self.fail('unknown error retried'))
            self.assertEqual(len(calls),1);self.assertEqual(g.calls,1);self.assertEqual(r['provider_rejected_attempts'],0)

    def test_solfix_wait_keeps_time_and_quota_stops(self):
        rejection=dict(stdout=json.dumps(dict(type='error',codex_error_info='server_overloaded')))
        with tempfile.TemporaryDirectory() as d:
            clock=[0.0]
            root,r,code,calls,cads,g=self.drive(d,'A5',[rejection],route='ask',clock=clock,provider=True,sleeper=lambda s:clock.__setitem__(0,clock[0]+s))
            self.assertEqual(len(calls),1);self.assertEqual(g.calls,0);self.assertEqual(r['llm_calls'],0)
            self.assertEqual(r['message_code'],'episode_stage_deadline_exceeded');self.assertEqual(r['calls'][0]['wait_requested_s'],600)
            self.assertLess(r['provider_wait_s'],600);self.assertEqual(r['budget_counts']['question'],0)
            entry=next(e for e in json.loads((BASE/'run-order.json').read_text())['entries'] if e['case']=='A5')
            row=evaluation.record(root,entry,REVIEW_RUN)
            self.assertFalse(row['completed']);self.assertIsNone(row['stop_reason']);self.assertEqual(row['failure_class'],'timeout')
        with tempfile.TemporaryDirectory() as d:
            def change_quota(s):
                p=Path(d)/'quota.json';data=json.loads(p.read_text());data['used_percent']=55;p.write_text(json.dumps(data))
            root,r,code,calls,cads,g=self.drive(d,'A5',[rejection],route='ask',provider=True,sleeper=change_quota)
            self.assertEqual(len(calls),1);self.assertEqual(g.calls,0);self.assertEqual(r['message_code'],'quota_soft_stop')
        with tempfile.TemporaryDirectory() as d:
            def hard_quota(s):
                p=Path(d)/'quota.json';data=json.loads(p.read_text());data['used_percent']=60;p.write_text(json.dumps(data))
            _,r,_,calls,_,g=self.drive(d,'A5',[rejection],route='ask',provider=True,sleeper=hard_quota)
            self.assertEqual(len(calls),1);self.assertEqual(g.calls,0);self.assertEqual(r['message_code'],'quota_hard_stop')
        with tempfile.TemporaryDirectory() as d:
            clock=[0.0]
            root,r,_,_,_,_=self.drive(d,'C4',[json.dumps(dict(needs_clarification=['plate_thickness'])),rejection],
                route='completion',clock=clock,provider=True,sleeper=lambda s:clock.__setitem__(0,clock[0]+s))
            entry=next(e for e in json.loads((BASE/'run-order.json').read_text())['entries'] if e['case']=='C4')
            row=evaluation.record(root,entry,REVIEW_RUN)
            self.assertFalse(row['completed']);self.assertIsNone(row['stop_reason'],row.get('error'));self.assertEqual(row['initial_q_score'],1)
            self.assertEqual(row['q_score'],1);self.assertTrue(row['completion_reached']);self.assertEqual(row['failure_class'],'timeout')

    def test_solfix_manifest_change_allowlist_and_inherited_clock(self):
        old=dict(schema='cad-harness.verify-sha.v3',profile='verify-v3',version='verify-v3-reviewed-r1',
            cli={},settings={},agents_sha256={},plan_commit='fd7e215',files={p:'old' for p in evaluation.SOLFIX_CODE})
        old['files']['gold.json']='unchanged';current=copy.deepcopy(old);current['version']=evaluation.SOLFIX_VERSION
        current['files'].update({p:'new' for p in evaluation.SOLFIX_CODE});current['files'].update({p:'new' for p in evaluation.SOLFIX_DOCS})
        with patch.object(evaluation,'verify_frozen'):
            self.assertEqual(evaluation.transition(ROOT,old,current),sorted(evaluation.SOLFIX_CODE))
            broken=copy.deepcopy(current);broken['files']['gold.json']='changed'
            with self.assertRaisesRegex(Stop,'allowlist'):evaluation.transition(ROOT,old,broken)
            broken=copy.deepcopy(current);broken['settings']['model']='other'
            with self.assertRaisesRegex(Stop,'identity'):evaluation.transition(ROOT,old,broken)
        g=Guard('unused',clock=lambda:540000)
        g.inherit(dict(started_monotonic=534990.093,deadline_monotonic=545790.093,real_calls=54,call_budget=163))
        self.assertEqual(g.deadline,545790.093);self.assertEqual(g.calls,54);self.assertEqual(g.call_budget-g.calls,109)
        g=Guard('unused',clock=lambda:550000)
        g.inherit(dict(started_monotonic=534990.093,deadline_monotonic=545790.093,real_calls=54,call_budget=163),no_deadline=True)
        self.assertIsNone(g.deadline);self.assertEqual(g.started,534990.093);self.assertEqual(g.calls,54)
        self.assertTrue(math.isinf(g.remaining()))
        g.before_episode(109)
        with self.assertRaisesRegex(Stop,'insufficient_call_budget'):g.before_episode(110)
        self.assertEqual(Budget(1,clock=lambda:550000).settings()['deadline_s'],900)
        with self.assertRaisesRegex(Stop,'binding'):
            g.inherit(dict(started_monotonic=540000,deadline_monotonic=550800,real_calls=54,call_budget=162))

    def test_solfix_resume_and_two_manifest_aggregate_preserve_originals(self):
        prefix='mock-v3-solfix-resume-r1';order=json.loads((BASE/'run-order.json').read_text(encoding='utf-8'))
        old=dict(schema='cad-harness.verify-sha.v3',profile='verify-v3',version='verify-v3-reviewed-r1',local_commit='32dab3a',plan_commit='fd7e215',
            cli=dict(path='MOCK-NO-SOL',version='MOCK CLI',sha256='mock'),settings={},agents_sha256={},files={p:'before-'+p for p in evaluation.SOLFIX_CODE})
        old['files']['immutable-gold.json']='unchanged'
        current=copy.deepcopy(old);current['version']=evaluation.SOLFIX_VERSION
        current['files'].update({p:evaluation.sha((ROOT/p).read_bytes()) for p in evaluation.SOLFIX_CODE|evaluation.SOLFIX_DOCS})
        original=dict(schema='cad-harness.verify-run.v3',profile='verify-v3',version=old['version'],prefix=prefix,
            started_monotonic=534990.093,deadline_monotonic=545790.093,wall_s=2366.75,real_calls=54,call_budget=163,stop_reason='harness:missing_report_or_artifact',frozen_sha256=old['files'],rows=[])
        plan=dict(profile='verify-v3',version=old['version'],entries=order['entries'],started_monotonic=534990.093,deadline_monotonic=545790.093,started_at='2026-10-13T06:08:29.573298+00:00')
        for e in order['entries']:
            row=evaluation.empty_row(e,evaluation.run_name(prefix,e))
            if e['sequence']<=46:row.update(completed=True,passed=True,wall_s=0,sol_calls=e['min_calls'],cad_attempts=0,ended_elapsed_s=1000)
            if e['sequence']==47:row.update(sol_calls=1,stop_reason='harness:missing_report_or_artifact',ended_elapsed_s=2366.735)
            if e['id'] in ('geometry-G5-r1','geometry-G1-r2'):row.update(passed=False,failure_class='interpretation')
            original['rows'].append(row)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'repo';base=root/evaluation.DESIGN;base.mkdir(parents=True)
            archive=base/'SHA256.run-r1.json';archive.write_text(json.dumps(old),encoding='utf-8')
            (base/'SHA256.json').write_text(json.dumps(current),encoding='utf-8')
            digest=evaluation.sha(archive.read_bytes());original['sha_manifest']=plan['sha_manifest']=digest
            directory=evaluation.paths(root,prefix);directory.mkdir(parents=True)
            (directory/'suite-run.json').write_text(json.dumps(original),encoding='utf-8');(directory/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
            prior_name=original['rows'][46]['run'];prior_dir=evaluation.driver_path(root,prior_name);prior_dir.mkdir()
            prior=dict(calls=[dict(kind='spec',purpose='question',context_sha256='same-context',prompt_sha256='same-prompt',ended_at='2026-10-13T06:47:55.800559+00:00')])
            (prior_dir/'driver-run.json').write_text(json.dumps(prior),encoding='utf-8')
            for e in order['entries'][46:]:
                source=BASE/'test'/e['case'];dest=base/'test'/e['case'];dest.mkdir(parents=True,exist_ok=True)
                for p in source.iterdir():
                    if p.is_file():(dest/p.name).write_bytes(p.read_bytes())
            quota=Path(d)/'quota.json';timepoint=original['started_monotonic']+12000
            now=datetime.fromisoformat(plan['started_at'])+timedelta(seconds=12000)
            quota.write_text(json.dumps(dict(snapshot_id='mock',observed_at=now.isoformat(),used_percent=10)))
            preserved=evaluation.original_artifacts(root,prefix,order);executed=[]
            def fake_driver(name,codex,raw,gold,**kw):
                self.assertIsNone(kw['guard'].deadline);self.assertEqual(kw['guard'].call_budget,163)
                self.assertEqual(kw['guard'].calls,54+len(executed));self.assertTrue(kw['provider_retry'])
                kw['guard'].before_call();executed.append(name)
                out=evaluation.driver_path(root,name);out.mkdir()
                c={**prior['calls'][0], 'provider_rejected':False}
                r=dict(provider_policy=driver.PROVIDER_POLICY,prior_provider_attempts=kw['prior_provider_attempts'],calls=[c],llm_calls=1)
                (out/'driver-run.json').write_text(json.dumps(r),encoding='utf-8');return r,0
            def fake_record(repo,e,name):
                if not name.endswith('-resume1'):return copy.deepcopy(original['rows'][e['sequence']-1])
                row=evaluation.empty_row(e,name);row.update(completed=True,passed=True,sol_calls=1,cad_attempts=0,wall_s=0,stop_reason=None,failure_class=None);return row
            def provider(repo,row):return dict(id=row['id'],run=row['run'],original_score_preserved=row['completed'])
            with (patch.object(evaluation,'load',return_value=(current,order)),patch.object(evaluation,'verify_frozen'),patch.object(evaluation,'historical_provider',side_effect=provider),
                    patch.object(driver,'run_driver',side_effect=fake_driver),patch.object(evaluation,'record',side_effect=fake_record),patch.object(evaluation,'legacy_record',side_effect=fake_record)):
                second=evaluation.resume(prefix,quota,archive,root=root,clock=lambda:timepoint,now=lambda:now)
                self.assertEqual(executed,[evaluation.run_name(prefix,e)+'-resume1' for e in order['entries'][46:]])
                self.assertEqual(second['inherited_calls'],54);self.assertEqual(second['total_real_calls'],68);self.assertIsNone(second['deadline_monotonic'])
                self.assertEqual(second['deadline'],evaluation.RESUME_DEADLINE)
                self.assertEqual(second['original_deadline_monotonic'],545790.093)
                self.assertEqual(evaluation.original_artifacts(root,prefix,order),preserved)
                result=evaluation.aggregate(prefix,'mock-solfix',root=root,clock=lambda:timepoint,run_manifest=archive)
                self.assertTrue(result['summary']['versions_consistent']);self.assertEqual(result['real_calls'],68)
                self.assertTrue(result['summary']['deadline_ok']);self.assertIsNone(result['deadline_monotonic'])
                self.assertEqual(result['segments'][1]['deadline'],evaluation.RESUME_DEADLINE)
                self.assertTrue(result['segments'][0]['deadline_ok']);self.assertEqual(result['segments'][0]['deadline_monotonic'],545790.093)
                self.assertEqual(len(result['segments']),2);self.assertEqual(result['segments'][0]['completed_preserved'],46)
                self.assertFalse(next(r for r in result['groups']['geometry'] if r['id']=='geometry-G5-r1')['passed'])
                self.assertFalse(next(r for r in result['groups']['geometry'] if r['id']=='geometry-G1-r2')['passed'])
                self.assertEqual(result['original_partial']['id'],'q-A5-r5');self.assertFalse(result['original_partial']['completed'])
                self.assertEqual(evaluation.original_artifacts(root,prefix,order),preserved)
                # A changed archived suite is rejected before any aggregate output.
                (directory/'plan.json').write_text('{}')
                with self.assertRaises((Stop,KeyError)):evaluation.aggregate(prefix,'tamper-solfix',root=root,clock=lambda:timepoint,run_manifest=archive)

    def test_data_bytes_gold_and_exact_order_caps(self):
        self.assertEqual(evaluation.data_check(),dict(cases=18,episodes=60,planned_calls=83,max_calls=163,sol_calls=0,cad_attempts=0))
        order=json.loads((BASE/'run-order.json').read_text());order['entries'][17:19]=reversed(order['entries'][17:19])
        with self.assertRaises(Stop):evaluation.validate_order(order)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(Stop,'independent_native_controls_pending'):evaluation.require_controls(Path(d))

    def test_schema_first_one_exact_capability_and_non_source_rejection(self):
        raw=dict(schema='cad-harness.build-spec.v1',family='stepped_shaft',units='mm',frame='world',center_xy=[0,0],steps=[dict(diameter=46,z=[0,54])],holes=[dict(center_xy=[0,0],diameter=14,z=[0,54])])
        kind,_,e=driver.interpretation(raw,True);self.assertEqual(kind,'unsupported');self.assertEqual(e['unsupported_origin'],'validator');self.assertTrue(e['schema_valid']);self.assertFalse(e['compiler_supported'])
        with self.assertRaisesRegex(ValueError,'unsupported_shaft_operation'):driver.interpretation(raw,False)
        for invalid in [dict(raw,family='roller'),dict(raw,extra=1)]:
            with self.assertRaises(ValueError):driver.interpretation(invalid,True)
        with patch.object(cad_spec,'validate_spec',side_effect=ValueError('unsupported_finish')):
            with self.assertRaisesRegex(ValueError,'unsupported_finish'):driver.interpretation(raw,True)
        for text in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):cad_spec.read_json(text)

    def test_validator_capability_routes_without_P_and_archives_exact_context(self):
        raw=dict(schema='cad-harness.build-spec.v1',family='stepped_shaft',units='mm',frame='world',center_xy=[0,0],steps=[dict(diameter=46,z=[0,54])],holes=[dict(center_xy=[0,0],diameter=14,z=[0,54])])
        with tempfile.TemporaryDirectory() as d:
            root,r,code,calls,cads,_=self.drive(d,'G1',[json.dumps(raw),SOURCE],route='source')
            self.assertEqual((code,len(calls),len(cads),r['parse_repairs']),(0,2,1,0));self.assertEqual(r['unsupported_origin'],'validator')
            for key,item in r['calls'][1]['context_artifacts'].items():self.assertEqual(evaluation.sha((root/item['path']).read_bytes()),r['calls'][1][key+'_sha256'])
            self.assertEqual((root/r['calls'][1]['context_artifacts']['prompt']['path']).read_bytes(),(BASE/'test/G1/description.txt').read_bytes())
            context=(root/r['calls'][1]['context_artifacts']['context']['path']).read_text(encoding='utf-8')
            self.assertNotIn('24432',context);self.assertNotIn('gold.json',context)

    def test_parse_then_settled_in_schema_miss_reaches_actual_R(self):
        with tempfile.TemporaryDirectory() as d:
            root,r,code,calls,cads,_=self.drive(d,'A4',['invalid',json.dumps(spec('A4')),'invalid'],fail=True)
            self.assertEqual((code,len(calls),len(cads),r['parse_repairs'],r['repair_calls']),(1,3,1,1,1));self.assertTrue(r['repair_eligible'])
            self.assertEqual([c['purpose'] for c in r['calls']],['interpretation','parse_repair','repair'])
            entry=next(e for e in json.loads((BASE/'run-order.json').read_text())['entries'] if e['case']=='A4')
            row=evaluation.record(root,entry,REVIEW_RUN);self.assertIsNone(row['stop_reason'],row.get('error'));self.assertTrue(row['completed']);self.assertEqual(row['failure_class'],'editability_pre_export')
            self.assertEqual(row['final_stage_statuses']['export'],'not_reached')

    def test_solfix_rejected_P_and_R_remain_unconsumed_time_stops(self):
        rejection=dict(stdout=json.dumps(dict(type='error',codex_error_info='server_overloaded')))
        for repair in (False,True):
            with self.subTest(repair=repair),tempfile.TemporaryDirectory() as d:
                tick=[0.0];outputs=[json.dumps(spec('A4')) if repair else 'invalid',rejection]
                root,r,_,calls,cads,guard=self.drive(d,'A4',outputs,fail=repair,provider=True,clock=tick,sleeper=lambda s:tick.__setitem__(0,tick[0]+s))
                self.assertEqual((len(calls),r['llm_calls'],guard.calls,r['parse_repairs'],r['repair_calls']),(2,1,1,0,0))
                self.assertEqual(r['calls'][-1]['purpose'],'repair' if repair else 'parse_repair')
                self.assertEqual(r['message_code'],'episode_stage_deadline_exceeded');self.assertLess(r['provider_wait_s'],600)
                entry=next(e for e in json.loads((BASE/'run-order.json').read_text())['entries'] if e['case']=='A4')
                row=evaluation.record(root,entry,REVIEW_RUN)
                self.assertIsNone(row['stop_reason'],row.get('error'));self.assertFalse(row['completed']);self.assertEqual(row['failure_class'],'timeout')
                if repair:self.assertEqual(row['initial_stage_statuses']['editability'],'fail');self.assertTrue(row['repair_eligible'])

    def test_repair_reservation_is_episode_stop_not_shared_reset(self):
        tick=[0.0]
        with tempfile.TemporaryDirectory() as d:
            root,r,_,_,_,guard=self.drive(d,'A4',[json.dumps(spec('A4'))],fail=True,clock=tick,after_cad=lambda:tick.__setitem__(0,451))
            # CAD returned outside initial450: no R; clock stays the same.
            self.assertEqual(r['message_code'],'episode_stage_deadline_exceeded');self.assertEqual(guard.started,0)
        b=Budget(3,clock=lambda:tick[0]);b.attempts=1;tick[0]+=451
        with self.assertRaisesRegex(Stop,'repair_time_reservation_lost'):b.begin_repair()
        report=dict(message_code='repair_time_reservation_lost',attempts=[])
        self.assertIsNone(evaluation.harness_failure(report))

    def test_budget_slots_and_reservations(self):
        tick=[0.0];b=Budget(4,clock=lambda:tick[0]);b.call('interpretation');b.call('parse_repair');b.call('source');b.cad();tick[0]=100;b.begin_repair()
        self.assertEqual(b.sol_timeout('repair'),180);b.call('repair');b.cad()
        with self.assertRaises(ValueError):b.cad()
        with self.assertRaises((ValueError,Stop)):b.call('repair')
        self.assertLessEqual(b.cad_timeout(),90)
        with self.assertRaises(ValueError):Guard('none',call_budget=164)

    def test_completion_answer_bytes_correct_wrong_and_additional_question(self):
        for c,field in [('C4','plate_thickness'),('C5','hole_positions')]:
            with self.subTest(case=c),tempfile.TemporaryDirectory() as d:
                _,r,code,calls,cads,_=self.drive(d,c,[json.dumps(dict(needs_clarification=[field])),json.dumps(spec(c))],route='completion')
                self.assertEqual((code,len(calls),len(cads)),(0,2,1));self.assertTrue(r['completion_reached'])
                expected=(BASE/'test'/c/'description.txt').read_bytes()+b'\n'+(BASE/'test'/c/'answer.txt').read_bytes()
                self.assertEqual(calls[1][0][-1].encode(),expected);self.assertEqual(r['completion_input_sha256'],evaluation.sha(expected))
            with tempfile.TemporaryDirectory() as d:
                _,r,_,calls,cads,_=self.drive(d,c,['{"needs_clarification":["axis"]}'],route='completion')
                self.assertEqual((len(calls),len(cads)),(1,0));self.assertFalse(r['completion_reached'])
            with tempfile.TemporaryDirectory() as d:
                _,r,_,calls,cads,_=self.drive(d,c,[json.dumps(dict(needs_clarification=[field])),json.dumps(dict(needs_clarification=[field]))],route='completion')
                self.assertEqual(r['message_code'],'completion_additional_question');self.assertEqual((len(calls),len(cads)),(2,0))

    def test_ask_no_parse_or_CAD_and_F6_only_one_numeric_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            _,r,_,calls,cads,_=self.drive(d,'A5',['invalid'],route='ask');self.assertEqual((len(calls),len(cads),r['parse_repairs'],r['repair_calls']),(1,0,0,0))
        clean=cad_spec.validate_spec(spec('F6'));fault=Fault(BASE/'test/F6/fault.json');changed=fault.inject('spec',clean)
        self.assertEqual(changed['holes'][0]['diameter'],9);rest=copy.deepcopy(changed);rest['holes'][0]['diameter']=6;self.assertEqual(rest,clean)
        self.assertTrue(fault.record['injected']);self.assertEqual(fault.inject('spec',changed),changed)

    def test_role_arithmetic_cannot_pass_detached_decoy_or_half_width(self):
        op=lambda label,kind,v:dict(boundary_role=label,type=kind,value_mm=v,geometry=1)
        self.assertTrue(probe.prove_role('groove_depth',1.25,[op('outer','Radius',14.5),op('bottom','Radius',13.25)],[],[]))
        self.assertTrue(probe.prove_role('groove_depth',1.25,[op('outer','Diameter',29),op('bottom','Diameter',26.5)],[],[]))
        self.assertFalse(probe.prove_role('groove_depth',1.25,[op('unrelated','Radius',1.25)],[],[]))
        self.assertFalse(probe.prove_role('groove_width',6,[],[],[dict(role='groove_width',operative=False,value_mm=6)]))
        self.assertFalse(probe.prove_role('groove_width',6,[],[],[],[dict(active=True,both_boundaries=False,center_proved=True,half_width_mm=3)]))
        self.assertTrue(probe.prove_role('groove_width',6,[],[],[],[dict(active=True,both_boundaries=True,center_proved=True,half_width_mm=3)]))
        s=NS(Name='NewDev',ExpressionEngine=[('Constraints[0]','Constraints.outer_radius')],Constraints=[NS(Type='Radius'),NS(Type='Radius')],getIndexViaName=lambda name:1,getActive=lambda i:True)
        s.getDriving=realistic_driving(s)
        rows=[dict(sketch='NewDev',constraint=1,value_mm=14.5)]
        self.assertEqual(probe.expression_driver(s,0,rows,{'NewDev':s})['value_mm'],14.5)
        s.ExpressionEngine=[('Constraints[0]','Constraints.outer_radius+0')];self.assertIsNone(probe.expression_driver(s,0,rows,{'NewDev':s}))
        s.ExpressionEngine=[('Constraints[0]','Constraints.bad_alias')]
        def missing(name):raise ValueError('unknown alias')
        s.getIndexViaName=missing;self.assertIsNone(probe.expression_driver(s,0,rows,{'NewDev':s}))

    def test_reachability_negative_anchor_not_a_hub(self):
        cons=[NS(Type='DistanceX',First=0,Second=-1,Third=-1,Driving=True),NS(Type='DistanceX',First=1,Second=-1,Third=-1,Driving=True),NS(Type='Radius',First=2,Second=-1,Third=-1,Driving=True)]
        s=NS(GeometryCount=3,Constraints=cons,getActive=lambda n:True)
        self.assertEqual(set(probe.v2.reachable(s,{0:[]})),{0})
        cons.append(NS(Type='Coincident',First=0,Second=1,Third=-1,Driving=True));self.assertEqual(set(probe.v2.reachable(s,{0:[]})),{0,1})
        cons[-1].Driving=False;self.assertEqual(set(probe.v2.reachable(s,{0:[]})),{0})
        constraints=[NS(Type='Radius',First=1,Second=-2000,Third=-2000,Value=14.5,Driving=True),NS(Type='Equal',First=0,Second=1,Third=-2000,Driving=True)]
        sk=NS(Name='NewDev',GeometryCount=2,Constraints=constraints,getActive=lambda i:True,getConstruction=lambda i:i==1)
        sk.getDriving=realistic_driving(sk)
        with patch.object(probe,'geometry',return_value=dict(kind='circle',radius=14.5,center=[0,0,0])):
            rows,_=probe.driver_rows([],{'NewDev':sk},{'NewDev':{0:[]}},{})
            self.assertEqual(rows[0]['operands'][0]['geometry'],0);self.assertEqual(rows[0]['operands'][0]['binding'],'active_circle_equal')
            constraints[1].Type='Coincident'
            rows,_=probe.driver_rows([],{'NewDev':sk},{'NewDev':{0:[]}},{})
            self.assertFalse(rows[0]['operands'])

    def test_consumed_coordinate_driver_uses_native_origin_sentinel_and_not_free_chord(self):
        class Vec:
            def __init__(self,x,y,z):self.x=x;self.y=y;self.z=z
        placement=NS(multVec=lambda v:Vec(v.x,0,v.y))
        line=NS(StartPoint=Vec(14.5,0,0),EndPoint=Vec(14.5,37,0))
        c=NS(Type='DistanceX',First=0,FirstPos=1,Second=-2000,SecondPos=0,Third=-2000,Value=14.5,Driving=True)
        s=NS(Name='NewDev',GeometryCount=1,Geometry=[line],Constraints=[c],Placement=placement,getActive=lambda i:True,getConstruction=lambda i:False)
        s.getDriving=realistic_driving(s)
        rows,_=probe.driver_rows([],{'NewDev':s},{'NewDev':{0:[dict(feature='Pad',link='Profile',geometry=0)]}},{})
        self.assertEqual(rows[0]['operands'][0]['type'],'radial_coordinate');self.assertEqual(rows[0]['operands'][0]['boundary'],14.5)
        self.assertNotIn('span',rows[0])
        c.Second=-3
        rows,_=probe.driver_rows([],{'NewDev':s},{'NewDev':{0:[]}},{})
        self.assertFalse(rows[0]['operands']);self.assertNotIn('span',rows[0])

    def test_phase_labels_geometry_precedence_and_unexecuted_null(self):
        for geometry,edit,expected in [(False,False,'geometry_pre_export'),(True,False,'editability_pre_export')]:
            r=dict(geometry_ok=geometry,editability_ok=edit,probe_status='predicate_fail');finalize(r)
            self.assertEqual(r['failure_class_v3'],expected);self.assertEqual(r['stage_statuses']['reimport'],'not_reached');self.assertIsNone(r['stage_measurements']['reimport'])
        r=dict(failed_phase='export');finalize(r);self.assertEqual(r['failure_class_v3'],'export_failure')

    def test_actual_worker_native_compiler_miss_is_settled_for_v3_only(self):
        for profile,expected_actor in [('verify-v2','human'),('verify-v3','sol')]:
            with self.subTest(profile=profile),tempfile.TemporaryDirectory() as d:
                documents={};doc=NS(recompute=lambda:None,saveAs=lambda path:Path(path).write_bytes(b'diagnostic'))
                def create(name):doc.Name=name;documents[name]=doc;return doc
                app=NS(GuiUp=0,Version=lambda:['1','1','4'],newDocument=create,listDocuments=lambda:dict(documents),closeDocument=lambda name:documents.pop(name))
                body=NS(Document=doc,TypeId='PartDesign::Body')
                observed=dict(probe_pass=False,predicates={'editability':False},geometry_ok=True,editability_ok=False,measurements={'volume_mm3':1,'editability':{'native_valid':True}},predicate_details={'checks':[]})
                r=cad_run_freecad.execute(app,lambda unused:body,Path(d)/'model.FCStd',lambda *args:None,lambda *args:observed,step_path=Path(d)/'model.step',generator='compiler',profile=profile)
                self.assertEqual(r['next_actor'],expected_actor);self.assertTrue(r['script_completed']);self.assertTrue(r['document_closed']);self.assertFalse((Path(d)/'model.step').exists())
                if profile=='verify-v3':
                    self.assertEqual(r['stage_statuses']['geometry'],'pass');self.assertEqual(r['stage_statuses']['editability'],'fail');self.assertEqual(r['stage_statuses']['export'],'not_reached');self.assertIsNone(r['stage_measurements']['export'])
        self.assertTrue(probe.length_mode(NS(Type='Length')));self.assertFalse(probe.length_mode(NS(Type='ThroughAll',Length=6,Length2=6)))

    def test_stock_full_volume_and_completed_cohort_statistics_remain_separate(self):
        order=json.loads((BASE/'run-order.json').read_text());rows=[evaluation.empty_row(e,e['id']+'-mvp1') for e in order['entries']]
        s=evaluation.summarize(rows,order);self.assertFalse(s['bar_met']);self.assertIsNone(s['completion']['C4']['completion']['wilson95'])
        stock=probe.load_gold(BASE/'test/S3/gold.json');self.assertEqual(stock['volume']['target_mm3'],55944);self.assertEqual(stock['volume_scope'],[-37,37,-27,27,0,14])
        self.assertAlmostEqual(probe.load_gold(BASE/'test/G1/gold.json')['volume']['target_mm3'],24432.5*math.pi)

if __name__=='__main__':unittest.main()
