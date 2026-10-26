"""H0 budget/isolation consumer boundaries; no model or SolidWorks calls."""
from pathlib import Path
import tempfile
import unittest
import json
import os
import socket
from datetime import datetime,timezone
from tools import sw_h0_runtime as runtime,cad_verify_v4_ledger as ledger
from tools.sw_h0_budget import Pool,BudgetJournal
from tools.sw_h0_worker import admit
from tools.cad_verify_guard import Stop
from tools.sw_m1_inputs import PRIVATE


class H0SafetyTests(unittest.TestCase):
    def test_pending_calls_survive_restart_and_refuse_call_41(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as tmp:
            root=Path(tmp)/'pool'
            with Pool(root) as pool:
                for i in range(40):pool.reserve(str(i))
            with Pool(root) as pool:
                self.assertEqual(pool.summary()['pending_or_unknown_calls'],40)
                with self.assertRaises(Stop):pool.reserve('41')

    def test_only_verified_no_output_overload_releases_reservation(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as tmp:
            root=Path(tmp)
            with Pool(root/'pool') as pool:
                with BudgetJournal(root/'journal.jsonl','r','h0',pool=pool) as journal:
                    args=dict(episode_id='e',attempt_id='1',operation='model')
                    journal.append('attempt_started',**args)
                    journal.append('attempt_finished',**args,charged=False,provider_rejected=True,
                        provider_summary=dict(provider_rejected=True,assistant_output=False,
                            parse_complete=True,error_infos=['server_overloaded']))
                    self.assertEqual(pool.remaining,40)
                    args['attempt_id']='2';journal.append('attempt_started',**args)
                    with self.assertRaises(Stop):
                        journal.append('attempt_finished',**args,charged=False,provider_rejected=True,
                            provider_summary=dict(provider_rejected=True,assistant_output=True,
                                parse_complete=True,error_infos=['server_overloaded']))
                    self.assertEqual(pool.summary()['pending_or_unknown_calls'],1)

    def test_candidate_worker_refuses_gold_and_cards_before_COM(self):
        for extra in ('gold','gold_path','card','answer','reference_shape'):
            with self.subTest(extra=extra),self.assertRaises(ValueError):
                admit({'out':'unused','spec':{},extra:{'fake_secret':123.456}})

    def test_quota_boundaries_and_changed_input_stop_before_any_call(self):
        runtime.PRIVATE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime.PRIVATE) as tmp:
            root=Path(tmp);packet=root/'inputs-private.json';packet.write_text('[]')
            generator=root/'fake-generator';generator.write_text('not executable')
            snapshot=root/'quota.json'
            manifest=dict(run=root.name,files={},input_files={},runtime_files={},
                host={'hostname':socket.gethostname()},OMP_PROFILE=os.environ.get('OMP_PROFILE'),
                generator={'omp':str(generator),'sha256':ledger.file_sha(generator)},
                inputs_packet_sha256=ledger.file_sha(packet),quota_snapshot=str(snapshot))
            ledger.write_json(root/'manifest.json',manifest)
            manifest['manifest_sha256']=ledger.file_sha(root/'manifest.json')
            with Pool(root/'pool') as pool:
                with BudgetJournal(root/'journal.jsonl','r','mock',pool=pool) as journal:
                    guard=runtime.Guard(manifest,pool,journal)
                    for percent,reason in ((54.9,None),(55,'quota_soft_stop'),(60,'quota_hard_stop')):
                        snapshot.write_text(json.dumps(dict(snapshot_id='synthetic',used_percent=percent,
                            observed_at=datetime.now(timezone.utc).isoformat())))
                        if reason:
                            with self.assertRaises(Stop):guard.before_run(1)
                            self.assertEqual(guard.stop_reason,reason)
                        else:guard.before_run(1)
                    self.assertEqual(pool.used,0)
                    packet.write_text('{}')
                    with self.assertRaises(Stop):guard.check()
                    self.assertEqual(guard.stop_reason,'H0_frozen_file_changed')

    def test_repair_runtime_data_never_projects_oracle_expectations(self):
        adapter=runtime.SafeAdapter(b'fixed instructions','synthetic request')
        secret='SYNTHETIC_ORACLE_SECRET_987654'
        previous={'build_spec':{'schema':'candidate already returned by model'},
            'gold':secret,'result':{'task_id':secret,
                'measurements':{'expected':secret,'original_geometry_pass':False},
                'predicate_details':{'checks':[{'field':'bbox','passed':False,'expected':secret}]}}}
        context=adapter.developer_context('unused','Retain this output path for CAD repair',previous)
        self.assertNotIn(secret,context)
        self.assertNotIn('expected',context)
        observed=json.loads(context.split(runtime.agent.MARKER,1)[1])['observations']['result']
        self.assertIs(observed['measurements']['original_geometry_pass'],False)

    def test_successful_and_failed_episode_calls_share_accounting_and_fail_closed(self):
        runtime.PRIVATE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime.PRIVATE) as tmp:
            root=Path(tmp);packet=root/'inputs-private.json';packet.write_text('[]')
            executable=root/'fake-OMP';executable.write_text('not executable')
            snapshot=root/'quota.json'
            snapshot.write_text(json.dumps(dict(snapshot_id='synthetic',used_percent=1,
                observed_at=datetime.now(timezone.utc).isoformat())))
            manifest=dict(run=root.name,files={},input_files={},runtime_files={},
                host={'hostname':socket.gethostname()},OMP_PROFILE=os.environ.get('OMP_PROFILE'),
                inputs_packet_sha256=ledger.file_sha(packet),quota_snapshot=str(snapshot),
                generator=dict(omp=str(executable),sha256=ledger.file_sha(executable),
                    version='UNIT-MOCK',model='openai-codex/gpt-6.1-sol',thinking='xhigh'))
            ledger.write_json(root/'manifest.json',manifest)
            manifest['manifest_sha256']=ledger.file_sha(root/'manifest.json')
            def provider(argv,captures,**kwargs):
                event=dict(type='message_end',message=dict(role='assistant',provider='openai-codex',
                    model='gpt-6.1-sol',content=[dict(type='text',text='{}')],stopReason='stop'))
                captures['stdout'].feed((json.dumps(event)+'\n').encode())
                return 0
            with Pool(root/'pool') as pool:
                with BudgetJournal(root/'journal.jsonl','r','unit_mock',pool=pool) as journal:
                    guard=runtime.Guard(manifest,pool,journal)
                    for number in (1,2):
                        out=root/str(number);out.mkdir()
                        transport=runtime.Transport(manifest,journal,out,'synthetic request',b'fixed',guard,
                            entry={},process=provider)
                        transport.episode='synthetic-'+str(number)
                        guard.before_episode(1);guard.before_call()
                        completed=transport([str(executable),'exec','-o',str(out/'final.txt'),
                            'developer_instructions='+json.dumps('fixed'),'synthetic request'],
                            cwd=str(out),timeout=10)
                        self.assertEqual(completed.returncode,0)
                        self.assertIsNone(transport.fatal)
                    costs=ledger.summarize(root/'journal.jsonl')
                    self.assertEqual(costs['physical_model_attempts'],2)
                    self.assertEqual(costs['conservative_reserved_calls'],pool.used)
                    self.assertEqual(costs['capture']['complete'],4)
                    def refused(argv,captures,**kwargs):
                        captures['stderr'].feed(b'synthetic launch refusal\n')
                        return 1
                    out=root/'refused';out.mkdir()
                    transport=runtime.Transport(manifest,journal,out,'synthetic request',b'fixed',guard,
                        entry={},process=refused)
                    transport.episode='synthetic-refused'
                    guard.before_episode(1);guard.before_call()
                    completed=transport([str(executable),'exec','-o',str(out/'final.txt'),
                        'developer_instructions='+json.dumps('fixed'),'synthetic request'],
                        cwd=str(out),timeout=10)
                    self.assertEqual(completed.returncode,1)
                    self.assertEqual(transport.fatal,'H0_model_launch_or_response_failure')
                    costs=ledger.summarize(root/'journal.jsonl')
                    self.assertEqual(costs['physical_model_attempts'],3)
                    self.assertEqual(pool.used,3)
                    self.assertEqual(costs['capture']['complete'],6)


if __name__=='__main__':unittest.main()
