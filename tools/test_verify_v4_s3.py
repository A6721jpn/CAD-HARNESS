"""S3 host and mocked behavior; admission-only STEP bytes never reach CAD."""
import copy
import json
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_inputs as inputs, cad_verify_v4_plans as plans
from tools import cad_verify_v4_s1 as capabilities, cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_pilot as pilot, cad_verify_v4_s3_contracts as contracts
from tools import cad_verify_v4_agent as agent
from tools import cad_verify_v4_worker as worker
from tools.test_verify_v4_s1 import _HostFixtures
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class S3HostAdmission(_HostFixtures, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.manifest['profile'] = 'c-s3'
        self.save_manifest()

    def packet(self):
        packet = super().packet()
        packet['profile'] = 'c-s3'
        facts = packet['assets']['reference']
        facts.update(profile='c-s3', signature_precision_mm=1e-6)
        facts['faces'][0].update(adjacent_face_ids=[], parameterization=dict(
            domain_uv=[0, 2, 0, 3], corner_points_mm=[[0,0,0],[2,0,0],[0,3,0],[2,3,0]],
            degree_u=None, degree_v=None, reason='non_spline_surface'))
        return packet

    def rebuild_plan(self):
        return dict(schema='cad-harness.plan.v4c', profile='c-s3', family='surface_rebuild',
                    asset_id='reference', source_sha256=self.manifest['assets']['reference']['sha256'],
                    grid=[[dict(face_id='Face1', signature='1'*64, adjacent_face_ids=[],
                                swap_uv=False, reverse_u=False, reverse_v=False)]],
                    continuity='G2', fit_tolerance_mm=.002, kernel_tolerance_mm=1e-6,
                    max_degree=8, max_poles=128)

    def files(self):
        paths = [self.root/name for name in ('prepared.json','plan.json','card.json')]
        values = [self.packet(), self.rebuild_plan(), dict(schema='cad-harness.judge-card.v4c',
            profile='c-s3', source='independent_dev', numerical_uncertainty_mm=1e-6,
            criteria=[dict(id='valid',metric='solid_valid',expected_solids=1)])]
        for path, value in zip(paths, values):
            ledger.write_json(path, value)
        return paths

    def test_only_explicit_s3_admits_rebuild_and_stagebound_documents(self):
        self.assertEqual(contracts.validate_plan(self.rebuild_plan(), self.manifest_path,
                                               self.packet()), self.rebuild_plan())
        for profile in ('c-s1','c-s2','original'):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                plans.validate_plan(self.rebuild_plan(), profile=profile)
        for kind, value in (('inputs',self.manifest),('prepared',self.packet()),('plan',self.rebuild_plan())):
            for profile in ('c-s1','c-s2'):
                candidate = dict(value, profile=profile)
                with self.subTest(kind=kind,profile=profile), self.assertRaises(ValueError):
                    contracts.validate_document(candidate, kind)
            with self.assertRaises(ValueError):
                contracts.validate_document(dict(value, executable='forbidden'), kind)

    def test_grid_selectors_bind_hash_signature_adjacency_and_orientation(self):
        for field, value in (('signature','3'*64),('adjacent_face_ids',['Face2']),
                             ('swap_uv',1),('reverse_u','false'),('code','x')):
            plan = self.rebuild_plan()
            plan['grid'][0][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                contracts.validate_plan(plan,self.manifest_path,self.packet())
        for field, value in (('source_sha256','4'*64),('continuity','G1')):
            with self.assertRaises(ValueError):
                contracts.validate_plan(dict(self.rebuild_plan(),**{field:value}),self.manifest_path,self.packet())
        plan = self.rebuild_plan()
        plan['grid'].append(copy.deepcopy(plan['grid'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate_face'):
            contracts.validate_plan(plan)
        plan['grid'][1].append(copy.deepcopy(plan['grid'][0][0]))
        with self.assertRaisesRegex(ValueError,'not_rectangular'):
            contracts.validate_plan(plan)

    def test_parameterization_finite_domain_corners_and_degree_consistency(self):
        for field, value in (('domain_uv',[0,0,0,1]),('domain_uv',[0,1,0,float('nan')]),
                             ('corner_points_mm',[[0,0,0]]),('degree_u',3),('reason',None)):
            packet = self.packet()
            packet['assets']['reference']['faces'][0]['parameterization'][field] = value
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                inputs.verify_prepared(packet,self.manifest_path)
        packet = self.packet()
        packet['assets']['reference']['source_sha256'] = '5'*64
        with self.assertRaisesRegex(ValueError,'prepared_source_mismatch'):
            inputs.verify_prepared(packet,self.manifest_path)

    def test_checker_facts_cannot_be_generator_input_or_selection(self):
        self.manifest['assets']['checker'] = dict(self.manifest['assets']['reference'],role='checker')
        self.save_manifest()
        packet = self.packet()
        packet['assets']['checker'] = copy.deepcopy(packet['assets']['reference'])
        packet['assets']['checker']['asset_id'] = 'checker'
        self.assertNotIn('checker',inputs.model_inputs(packet,self.manifest_path)['assets'])
        with self.assertRaisesRegex(ValueError,'selection_not_generator_asset'):
            agent.PlanSkillAdapter(b'skill','request',self.manifest_path,packet,
                                  [dict(asset_id='checker',face_id='Face1',signature='1'*64)])

    def test_cards_reject_unknown_fields_and_invalid_maps(self):
        card = ledger.read_json(self.files()[2])
        with self.assertRaises(ValueError):
            contracts.validate_judge_card(dict(card, extra=True))
        bad = copy.deepcopy(card)
        bad['criteria'][0]['metric'] = 'g3_continuity'
        with self.assertRaises(ValueError):
            contracts.validate_judge_card(bad)
        bad['criteria'][0] = dict(id='dev',metric='surface_deviation',maximum_mm=.1,
            output_region_mm=[0,2,0,3,0,1],selection_tolerance_mm=1e-6,
            output_patches=[dict(bounds_mm=[0,2,0,3,0,1],domain_uv=[0,0,0,1],
                chart_uv=[0,1,0,1],swap_uv=False,reverse_u=False,reverse_v=False)],
            resources=dict(max_depth=4,max_cells=128))
        with self.assertRaises(ValueError):
            contracts.validate_judge_card(bad)

    def test_pipeline_rejects_omitting_any_required_quality_gate(self):
        prepared, plan, card_path = self.files()
        card = ledger.read_json(card_path)
        common = dict(output_region_mm=[0,2,0,3,0,1], selection_tolerance_mm=.001,
            output_patches=[dict(bounds_mm=[0,2,0,3,0,1], domain_uv=[0,2,0,3],
                chart_uv=[0,1,0,1], swap_uv=False, reverse_u=False, reverse_v=False)],
            resources=dict(max_depth=4,max_cells=128))
        side = dict(patch=0,axis='u',value=.5,range=[0,1],reverse=False)
        card['criteria'].extend([
            dict(id='faces',metric='face_count',scope='full',relation='delta',
                 correspondence='spatial_fixed_frame',expected_delta=0),
            dict(id='deviation',metric='surface_deviation',maximum_mm=.07,**copy.deepcopy(common)),
            dict(id='G2',metric='g2_continuity',maximum_position_mm=.0007,
                 maximum_normal_sin=.001,maximum_curvature_per_mm=.0003,
                 seams=[dict(a=copy.deepcopy(side),b=copy.deepcopy(side))],**copy.deepcopy(common)),
            dict(id='native',metric='native_roundtrip',maximum_bounds_difference_mm=.001,
                 maximum_volume_difference_mm3=.02,require_editable=True)])
        job = dict(profile='c-s3',manifest=str(self.manifest_path),prepared=str(prepared),
                   plan=str(plan),card=str(card_path))
        for missing in ('solid_valid','face_count','surface_deviation','g2_continuity','native_roundtrip'):
            incomplete = copy.deepcopy(card)
            incomplete['criteria'] = [c for c in card['criteria'] if c['metric'] != missing]
            incomplete_path = self.root / ('card-without-' + missing + '.json')
            ledger.write_json(incomplete_path,incomplete)
            job['card'] = str(incomplete_path)
            # Focused cards are valid for an individual measurement, but cannot
            # certify a complete rebuilt handover through the native pipeline.
            contracts.validate_judge_card(incomplete)
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                worker._loaded(job)
        complete_path = self.root / 'complete-card.json'
        ledger.write_json(complete_path,card)
        job['card'] = str(complete_path)
        admitted, _, _ = worker._loaded(job)
        self.assertEqual(admitted['source_sha256'],self.manifest['assets']['reference']['sha256'])

    def test_request_parse_repair_is_shared_and_cad_attempts_capped(self):
        prepared, _, card = self.files()
        request = self.root/'request.txt'
        request.write_text('Independent mocked surface case',encoding='utf-8')
        purposes = []
        def model(text,data,*,purpose,timeout):
            purposes.append(purpose)
            return '{invalid' if purpose == 'source' else json.dumps(self.rebuild_plan())
        def compile_mock(*args,**kwargs):
            return dict(status='FAIL',compile=dict(status='FAIL'),verification=None)
        with patch.object(capabilities,'compile_candidate',side_effect=compile_mock) as compile_call:
            value, code = capabilities.request(request,card,self.root/'run',
                manifest_path=self.manifest_path,prepared_path=prepared,model=model,profile='c-s3')
        self.assertEqual((code,value['status'],value['cad_attempts']), (1,'FAIL',2))
        self.assertEqual(purposes,['source','parse_repair','repair'])
        self.assertEqual(compile_call.call_count,2)
        self.assertEqual(value['physical_model_attempts'],0)

    def test_replay_binds_request_prepared_profile_and_order(self):
        prepared, _, _ = self.files()
        replay = self.root/'replay.json'
        value = dict(schema='cad-harness.plan-replay.v4c',profile='c-s3',
            request_sha256=ledger.sha(b'request'),prepared_sha256=ledger.file_sha(prepared),
            responses=[dict(purpose='source',text=json.dumps(self.rebuild_plan()))])
        ledger.write_json(replay,value)
        model = capabilities.PlanReplay(replay,b'request',prepared,profile='c-s3')
        with self.assertRaisesRegex(ValueError,'out_of_order'):
            model('request',{},purpose='repair',timeout=1)
        with self.assertRaisesRegex(ValueError,'replay_binding'):
            capabilities.PlanReplay(replay,b'changed',prepared,profile='c-s3')
        with self.assertRaisesRegex(ValueError,'replay_binding'):
            capabilities.PlanReplay(replay,b'request',prepared,profile='c-s2')

    def test_foreign_result_preserves_raw_capture_without_pass(self):
        def process(argv,captures,**kwargs):
            ledger.write_json(self.root/'work'/'result.json',dict(status='PASS',profile='c-s2'))
            captures['stdout'].feed(b'foreign native bytes\n')
            captures['stderr'].feed(b'raw diagnostic\n')
            return 0
        with ledger.Journal(self.root/'ledger.jsonl','foreign','s3-development') as journal:
            with self.assertRaisesRegex(ValueError,'native_result_profile_mismatch'):
                capabilities.native_work('identity',self.root/'work',journal,process=process,profile='c-s3')
        self.assertEqual((self.root/'work.stdout.bin').read_bytes(),b'foreign native bytes\n')
        self.assertEqual((self.root/'work.stderr.bin').read_bytes(),b'raw diagnostic\n')
        self.assertEqual(ledger.summarize(self.root/'ledger.jsonl')['deterministic_work']['statuses'],{'INCOMPLETE':1})

    def test_prepared_bundle_cannot_downgrade_stage(self):
        prepared, _, _ = self.files()
        request = self.root/'request.txt'
        request.write_bytes(b'Independent bundle\r\n')
        out = self.root/'bundle'
        pilot.bundle_prepared_request(request,self.manifest_path,prepared,out)
        value = ledger.read_json(out/'bundle.json')
        value['profile'] = 'c-s2'
        (out/'bundle.json').write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaises(ValueError):
            pilot.verify_prepared_bundle(out/'bundle.json')

    def test_source_drift_stops_before_native_attempt_or_repair(self):
        prepared, _, card = self.files()
        request = self.root/'request.txt'
        request.write_text('Independent drift case',encoding='utf-8')
        purposes = []
        def model(text,data,*,purpose,timeout):
            purposes.append(purpose)
            with self.step.open('ab') as stream:
                stream.write(b'changed')
            return json.dumps(self.rebuild_plan())
        value, code = capabilities.request(request,card,self.root/'drift',
            manifest_path=self.manifest_path,prepared_path=prepared,model=model,profile='c-s3')
        self.assertEqual((code,value['status'],value['cad_attempts']), (1,'INCOMPLETE',0))
        self.assertEqual(purposes,['source'])

