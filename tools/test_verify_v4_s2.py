"""S2 host admission boundaries; synthetic header bytes never reach CAD."""
import copy
import json
import unittest

from tools import cad_verify_v4_inputs as inputs, cad_verify_v4_plans as plans
from tools import cad_verify_v4_s1 as capabilities, cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_pilot as pilot, cad_verify_v4_s2_contracts as contracts
from tools import cad_verify_v4_agent as agent
from tools.test_verify_v4_s1 import _HostFixtures
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class S2HostAdmission(_HostFixtures, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.manifest['profile'] = 'c-s2'
        self.save_manifest()

    def packet(self):
        packet = super().packet()
        packet['profile'] = 'c-s2'
        facts = packet['assets']['reference']
        facts['profile'] = 'c-s2'
        facts['signature_precision_mm'] = 1e-6
        for face in facts['faces']:
            face['adjacent_face_ids'] = []
        return packet

    def edit_plan(self):
        return dict(schema='cad-harness.plan.v4c', profile='c-s2', family='step_direct_edit',
                    asset_id='reference', source_sha256=self.manifest['assets']['reference']['sha256'],
                    selection=dict(face_id='Face1', signature='1'*64, adjacent_face_ids=[]),
                    operation=dict(kind='offset', distance_mm=.75, reconnect='extend_intersect_trim'),
                    kernel_tolerance_mm=1e-6)

    def files(self):
        paths = [self.root / name for name in ('prepared.json', 'plan.json', 'card.json')]
        values = [self.packet(), self.edit_plan(),
                  dict(schema='cad-harness.judge-card.v4c', profile='c-s2', source='independent_dev',
                       numerical_uncertainty_mm=1e-6,
                       criteria=[dict(id='valid', metric='solid_valid', expected_solids=1)])]
        for path, value in zip(paths, values):
            ledger.write_json(path, value)
        return paths

    def test_original_stage_cannot_admit_direct_edit_or_s2_input(self):
        plan = self.edit_plan()
        with self.assertRaises(ValueError):
            plans.validate_plan(plan)
        prepared, plan_path, card = self.files()
        with self.assertRaisesRegex(ValueError, 'profile_mismatch'):
            capabilities.compile_candidate(self.manifest_path, prepared, plan_path, card, self.root/'never')
        self.assertFalse((self.root/'never').exists())

    def test_unique_selector_requires_source_hash_signature_and_adjacency(self):
        for field, value in (('source_sha256', '3'*64), ('signature', '2'*64),
                             ('adjacent_face_ids', ['Face2'])):
            candidate = self.edit_plan()
            if field == 'source_sha256':
                candidate[field] = value
            else:
                candidate['selection'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                contracts.validate_plan(candidate, self.manifest_path, self.packet())
        self.manifest['assets']['reference']['role'] = 'checker'
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'immutable_reference_binding'):
            contracts.validate_plan(self.edit_plan(), self.manifest_path, self.packet())

    def test_asymmetric_source_adjacency_cannot_become_runtime_fact(self):
        packet = self.packet()
        facts = packet['assets']['reference']
        other = copy.deepcopy(facts['faces'][0])
        other.update(id='Face2', signature='2'*64, center_mm=[1,1.5,4],
                     bounds_mm=[0,2,0,3,4,4], normal=[0,0,1])
        facts['faces'][0]['adjacent_face_ids'] = ['Face2']
        facts['faces'].append(other)
        facts['topology']['faces'] = 2
        with self.assertRaisesRegex(ValueError, 'adjacency_asymmetric'):
            inputs.model_inputs(packet, self.manifest_path)

    def test_source_drift_cannot_be_repaired_as_design_geometry(self):
        prepared, _, card = self.files()
        request = self.root/'request.txt'
        request.write_text('Independent host admission case', encoding='utf-8')
        calls = []
        def model(text, runtime_data, *, purpose, timeout):
            calls.append(purpose)
            with self.step.open('ab') as stream:
                stream.write(b'changed')
            return json.dumps(self.edit_plan())
        value, code = capabilities.request(request, card, self.root/'drift',
            manifest_path=self.manifest_path, prepared_path=prepared, model=model, profile='c-s2')
        self.assertEqual((code,value['status'],value['cad_attempts']), (1,'INCOMPLETE',0))
        self.assertEqual(calls,['source'])
        self.assertEqual(value['physical_model_attempts'],0)

    def test_foreign_worker_result_is_incomplete_with_raw_streams_retained(self):
        def foreign(argv, captures, **kwargs):
            job = ledger.read_json(argv[argv.index('--job')+1])
            path = self.root/'work'/'result.json'
            ledger.write_json(path,dict(status='PASS',profile='c-s1'))
            captures['stdout'].feed(b'foreign-stage-native-output\n')
            captures['stderr'].feed(b'preserved stderr\n')
            return 0
        journal_path = self.root/'ledger.jsonl'
        with ledger.Journal(journal_path,'foreign','s2-development') as journal:
            with self.assertRaisesRegex(ValueError,'native_result_profile_mismatch'):
                capabilities.native_work('identity',self.root/'work',journal,
                                          process=foreign,profile='c-s2')
        result = ledger.summarize(journal_path)
        self.assertEqual(result['deterministic_work']['statuses'],{'INCOMPLETE':1})
        self.assertEqual(result['physical_model_attempts'],0)
        self.assertEqual((self.root/'work.stdout.bin').read_bytes(),b'foreign-stage-native-output\n')
        self.assertEqual((self.root/'work.stderr.bin').read_bytes(),b'preserved stderr\n')

    def test_missing_thickness_acceptance_not_inherited_from_s1(self):
        card = dict(schema='cad-harness.judge-card.v4c',profile='c-s2',source='independent_dev',
                    numerical_uncertainty_mm=1e-6,criteria=[dict(id='wall',metric='thickness_distribution')])
        with self.assertRaises(ValueError):
            contracts.validate_judge_card(card)
        with self.assertRaises(ValueError):
            contracts.validate_plan(dict(self.edit_plan(),operation=dict(kind='offset',distance_mm=0,
                                                                          reconnect='extend_intersect_trim')))

    def test_bundle_cannot_relabel_s2_attachments_as_s1(self):
        prepared, _, _ = self.files()
        request = self.root/'request.txt'
        request.write_bytes(b'Independent bundle case\r\n')
        out = self.root/'bundle'
        pilot.bundle_prepared_request(request,self.manifest_path,prepared,out)
        path = out/'bundle.json'
        value = ledger.read_json(path)
        value['profile'] = 'c-s1'
        path.write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaises(ValueError):
            pilot.verify_prepared_bundle(path)

    def test_checker_only_facts_cannot_enter_model_context_or_selection(self):
        self.manifest['assets']['checker_reference'] = dict(
            self.manifest['assets']['reference'], role='checker')
        self.save_manifest()
        packet = self.packet()
        checker = copy.deepcopy(packet['assets']['reference'])
        checker['asset_id'] = 'checker_reference'
        packet['assets']['checker_reference'] = checker
        visible = inputs.model_inputs(packet,self.manifest_path)
        self.assertIn('reference',visible['assets'])
        self.assertNotIn('checker_reference',visible['assets'])
        selected = dict(asset_id='checker_reference',face_id='Face1',signature='1'*64)
        with self.assertRaisesRegex(ValueError,'selection_not_generator_asset'):
            agent.PlanSkillAdapter(b'skill','request',self.manifest_path,packet,[selected])
        with self.assertRaisesRegex(ValueError,'requires_manifest_roles'):
            inputs.model_inputs(packet)
