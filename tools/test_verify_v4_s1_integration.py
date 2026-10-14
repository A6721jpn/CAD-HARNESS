"""Consumer-visible S1 envelope, immutable intake and failure-accounting tests."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import unittest

from tools import cad_verify_v4_agent as agent, cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_pilot as pilot, cad_verify_v4_s1 as s1
from tools import eval_verify_v4 as facade
from tools.test_verify_v4_s1 import _HostFixtures
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class S1IntegrationAdmission(_HostFixtures, unittest.TestCase):
    def prepared_file(self):
        path = self.root / 'facts.json'
        ledger.write_json(path, self.packet())
        return path

    def card_file(self):
        path = self.root / 'card.json'
        ledger.write_json(path, dict(schema='cad-harness.judge-card.v4c', profile='c-s1',
                          source='independent_dev', linear_tolerance_mm=0,
                          criteria=[dict(id='valid', metric='solid_valid')]))
        return path

    def test_profile_separation_and_factual_packet_mutation(self):
        original = agent.SkillAdapter(b'original skill', 'request')
        with self.assertRaisesRegex(ValueError, 'requires_c_profile'):
            original.context({'target': 'plan'})
        adapter = agent.PlanSkillAdapter(b'capability skill', 'request', self.manifest_path, self.packet())
        data = dict(target='plan', stage='initial', inputs=copy.deepcopy(adapter.inputs), selection=[])
        adapter.context(data)
        data['inputs']['assets']['reference']['bounds_mm'][1] = 3
        with self.assertRaisesRegex(ValueError, 'provenance'):
            adapter.context(data)
        # An alias must not turn the adapter's mutable cache into new authority.
        adapter.inputs['assets']['reference']['bounds_mm'][1] = 3
        data['inputs'] = adapter.inputs
        with self.assertRaisesRegex(ValueError, 'provenance'):
            adapter.context(data)

    def test_selection_is_bound_to_unambiguous_face_identity(self):
        selected = dict(asset_id='reference', face_id='Face1', signature='1'*64)
        adapter = agent.PlanSkillAdapter(b'skill', 'request', self.manifest_path, self.packet(), [selected])
        data = dict(target='plan', inputs=adapter.inputs, selection=[dict(selected, signature='2'*64)])
        with self.assertRaisesRegex(ValueError, 'provenance'):
            adapter.context(data)
        for selection in (0, '', [dict(selected, face_id='Face2')], [selected, selected]):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                agent.PlanSkillAdapter(b'skill', 'request', self.manifest_path, self.packet(), selection)

    def test_direct_bundle_survives_original_removal_without_rebinding_facts(self):
        prepared = self.prepared_file()
        request = self.root / 'verbatim.txt'
        request.write_bytes(' independent request\r\n終端 '.encode('utf-8'))
        context = self.root / 'original-context.txt'
        context.write_bytes(b'context\r\nkept verbatim\n')
        out = self.root / 'bundle'
        pilot.bundle_prepared_request(request, self.manifest_path, prepared, out, context_path=context)
        for source in (request, self.manifest_path, prepared, self.step, context):
            source.unlink()
        checked = pilot.verify_prepared_bundle(out / 'bundle.json')
        self.assertIs(checked['integrity_only'], True)
        self.assertIsNone(checked['eligibility'])
        self.assertEqual(checked['source_sha256']['input_manifest'], ledger.file_sha(out / 'inputs.json'))
        self.assertEqual(checked['source_sha256']['prepared'], ledger.file_sha(out / 'prepared.json'))
        self.assertEqual((out / 'request.txt').read_bytes(), ' independent request\r\n終端 '.encode('utf-8'))
        with (out / 'independent.step').open('ab') as file:
            file.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash'):
            pilot.verify_prepared_bundle(out / 'bundle.json')

    def test_worker_interruption_keeps_partial_streams_without_model_charges(self):
        out = self.root / 'work'
        with ledger.Journal(self.root / 'ledger.jsonl', 'dev', 's1-development') as journal:
            def interrupted(argv, captures, **kwargs):
                captures['stdout'].feed(b'partial native stdout\x00\n')
                captures['stderr'].feed(b'partial native stderr\n')
                raise subprocess.TimeoutExpired(argv, kwargs['timeout'])
            with self.assertRaisesRegex(OSError, 'interrupted'):
                s1.native_work('identity', out, journal, process=interrupted)
        value = ledger.summarize(self.root / 'ledger.jsonl')
        self.assertEqual(value['physical_model_attempts'], 0)
        self.assertEqual(value['conservative_reserved_calls'], 0)
        self.assertEqual(value['deterministic_work']['statuses'], {'INCOMPLETE': 1})
        self.assertEqual(value['deterministic_work']['capture']['missing_or_partial'], 2)
        self.assertEqual((self.root / 'work.stdout.bin').read_bytes(), b'partial native stdout\x00\n')

    def test_shared_parse_slot_exhaustion_stops_before_any_native_launch(self):
        request = self.root / 'request.txt'
        request.write_text('Independent dev request', encoding='utf-8')
        prepared, card = self.prepared_file(), self.card_file()
        calls = []
        def invalid_model(text, runtime_data, *, purpose, timeout):
            calls.append(purpose)
            if len(calls) > 2:
                self.fail('parse repair retried beyond shared P1')
            return '{'
        value, code = s1.request(request, card, self.root / 'request-run',
                                 manifest_path=self.manifest_path, prepared_path=prepared, model=invalid_model)
        self.assertEqual(code, 1)
        self.assertEqual(value['status'], 'INCOMPLETE')
        self.assertEqual(calls, ['source', 'parse_repair'])
        self.assertEqual(value['cad_attempts'], 0)
        self.assertEqual(value['physical_model_attempts'], 0)
        self.assertEqual(value['costs']['physical_model_attempts'], 0)

    def test_mock_callback_cannot_mutate_authoritative_facts_for_repair(self):
        request = self.root / 'request.txt'
        request.write_text('Independent dev request', encoding='utf-8')
        prepared, card = self.prepared_file(), self.card_file()
        def corrupting_model(text, runtime_data, **kwargs):
            runtime_data['inputs']['assets']['reference']['bounds_mm'][1] = 200
            return '{'
        value, code = s1.request(request, card, self.root / 'request-run',
                                 manifest_path=self.manifest_path, prepared_path=prepared, model=corrupting_model)
        self.assertEqual(code, 1)
        self.assertEqual(value['stop_reason'], 'plan_runtime_provenance')
        self.assertEqual(value['replayed_responses'], 1)
        self.assertEqual(value['cad_attempts'], 0)

    def test_s1_cannot_admit_a_pilot_or_holdout_from_cli_flags(self):
        for phase in ('pilot', 'holdout'):
            with self.subTest(phase=phase), contextlib.redirect_stdout(io.StringIO()) as output:
                code = facade.main(['run', '--profile', 'c-s1', '--phase', phase,
                                    '--manifest', str(self.root / 'absent-manifest.json'),
                                    '--sealed-input', str(self.root / 'absent-cohort.json'),
                                    '--run-dir', str(self.root / 'must-not-exist')])
            value = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(value['reason'], 's1_is_development_only_not_final_trial_authorization')
            self.assertEqual(value['live_calls'], 0)
            self.assertFalse((self.root / 'must-not-exist').exists())

    def test_bound_replay_rejects_changed_preparation_before_response_use(self):
        prepared = self.prepared_file()
        replay = self.root / 'replay.json'
        ledger.write_json(replay, dict(schema='cad-harness.plan-replay.v4c', profile='c-s1',
                         request_sha256=ledger.sha(b'request'), prepared_sha256='0'*64,
                         responses=[dict(purpose='source', text='{}')]))
        with self.assertRaisesRegex(ValueError, 'replay_binding'):
            s1.PlanReplay(replay, b'request', prepared)

    def test_development_batch_path_escape_fails_before_output_allocation(self):
        replay = self.root / 'batch.json'
        ledger.write_json(replay, dict(schema='cad-harness.plan-batch-replay.v4c', profile='c-s1',
            evidence_mode='independent_dev', entries=[dict(id='independent', request='../outside.txt',
              card='card.json', input_manifest='inputs.json', prepared='prepared.json', replay='response.json')]))
        with self.assertRaisesRegex(ValueError, 'entry_path'):
            s1.run_development(replay, self.root / 'must-not-exist')
        self.assertFalse((self.root / 'must-not-exist').exists())

    def test_repair_diagnostics_cannot_disclose_checker_targets_or_files(self):
        secret='SENSITIVE-CHECKER-GOLD'
        report=dict(status='FAIL',compile=dict(status='PASS',measurements=dict(bounds_mm=[0,12,0,8,0,2])),
            verification=dict(source_paths=dict(card=secret),judgement=dict(checks=[
                dict(id='fit',metric='bounds',status='FAIL',
                     measured=dict(actual_mm=12,expected_mm=987654321,source_path=secret),
                     target=secret,uncertainty=dict(bound_mm=.01,card_path=secret),evidence=dict(gold=secret))])))
        visible=s1.repair_observations(report)
        encoded=json.dumps(visible)
        self.assertNotIn(secret,encoded)
        self.assertNotIn('987654321',encoded)
        self.assertEqual(visible['checks'][0]['measured'],{'actual_mm':12})
        self.assertEqual(visible['checks'][0]['uncertainty'],{'bound_mm':.01})

    def test_native_transport_failure_stops_incomplete_without_model_repair(self):
        request=self.root/'request.txt';request.write_bytes(b'Independent native timeout control')
        prepared,card=self.prepared_file(),self.card_file()
        plan=dict(schema='cad-harness.plan.v4c',profile='c-s1',family='reference_fixture',
            build_spec=dict(schema='cad-harness.build-spec.v1',family='rect_prism',
                units='mm',frame='world',regions=[dict(bounds=[0,4,0,3,0,2])],
                pockets=[],holes=[],finish=None),references=[],engravings=[])
        purposes=[]
        def recorded(text,runtime_data,*,purpose,timeout):
            purposes.append(purpose)
            return json.dumps(plan)
        def interrupted(argv,captures,**kwargs):
            captures['stderr'].feed(b'owned native process timed out')
            raise subprocess.TimeoutExpired(argv,kwargs['timeout'])
        result,code=s1.request(request,card,self.root/'interrupted-request',
            manifest_path=self.manifest_path,prepared_path=prepared,model=recorded,process=interrupted)
        self.assertEqual(code,1)
        self.assertEqual(result['status'],'INCOMPLETE')
        self.assertEqual(purposes,['source'])
        self.assertEqual(result['cad_attempts'],1)
        self.assertEqual(result['costs']['deterministic_work']['statuses'],{'INCOMPLETE':1})

    def test_original_freeze_cannot_silently_ignore_c_profile_assets(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code=facade.main(['freeze','--profile','original','--input-manifest',str(self.manifest_path),
                             '--run-dir',str(self.root/'must-not-exist')])
        self.assertEqual(code,1)
        self.assertEqual(json.loads(output.getvalue())['reason'],'s1_inputs_require_c_profile')
        self.assertFalse((self.root/'must-not-exist').exists())

    def test_implementation_lock_cannot_silently_override_phase_model_identity(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code=facade.main(['freeze','--profile','c-s1','--generator-model','unapproved-model',
                             '--run-dir',str(self.root/'must-not-exist')])
        self.assertEqual(code,1)
        self.assertEqual(json.loads(output.getvalue())['reason'],
                         's1_implementation_lock_uses_fixed_phase_models_and_no_omp_launcher')
        self.assertFalse((self.root/'must-not-exist').exists())

    def test_changed_checker_card_stops_before_native_work_or_repair(self):
        request=self.root/'request.txt';request.write_bytes(b'Independent immutable-card control')
        prepared,card=self.prepared_file(),self.card_file()
        plan=dict(schema='cad-harness.plan.v4c',profile='c-s1',family='reference_fixture',
            build_spec=dict(schema='cad-harness.build-spec.v1',family='rect_prism',
                units='mm',frame='world',regions=[dict(bounds=[0,4,0,3,0,2])],
                pockets=[],holes=[],finish=None),references=[],engravings=[])
        def recorded(text,runtime_data,**kwargs):
            # Simulate an operator/file-watcher edit, not generator file authority.
            changed=ledger.read_json(card);changed['linear_tolerance_mm']=1
            card.write_text(json.dumps(changed),encoding='utf-8')
            return json.dumps(plan)
        def forbidden_native(*args,**kwargs):
            raise AssertionError('native work after checker-card change')
        result,code=s1.request(request,card,self.root/'changed-card-request',
            manifest_path=self.manifest_path,prepared_path=prepared,model=recorded,process=forbidden_native)
        self.assertEqual(code,1)
        self.assertEqual(result['status'],'INCOMPLETE')
        self.assertEqual(result['stop_reason'],'s1_request_inputs_changed')
        self.assertEqual(result['cad_attempts'],0)


if __name__ == '__main__':
    unittest.main()
