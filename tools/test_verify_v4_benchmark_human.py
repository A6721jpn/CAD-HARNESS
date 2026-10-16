"""Independent unit-mock human receipt tests; no person/model/CAD is impersonated live."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import cad_verify_v4_benchmark as benchmark
from tools import cad_verify_v4_trials as trials
from tools.test_verify_v4_benchmark import FakeSession, registration


def condition_dataset():
    reg = registration()
    conditions = []
    for pair in reg['pairs']:
        for arm in benchmark.ARMS:
            row = dict(pair=pair['id'], arm=arm, family=pair['family'], stratum=pair['stratum'],
                       **benchmark._failed('DEV-not-started'))
            if pair['id'] == 'B01':
                handover = {'bundle': {'sha256': ('a' if arm == 'with_harness' else 'b') * 64}}
                row.update(status='UNVERIFIED', construction_status='PASS', reason=None,
                    timing={m: 10 if arm == 'with_harness' else 20 for m in benchmark.METRICS},
                    deterministic={'status': 'PASS', 'result': {'geometry_ok': True, 'editability_ok': True}},
                    judge={'status': 'PASS'}, first_handover=handover, final_handover=handover,
                    execution={'status': 'PASS', 'first_handover': handover})
            conditions.append(row)
    data = dict(schema=benchmark.SCHEMA, trial_id=reg['trial_id'], comparison='harness-versus-bare-agent',
                status='awaiting_human_verdicts', evidence_mode='unit_mock', conditions=conditions, pairs=[],
                event_prefix_sha256='0' * 64, enrolled_pairs=20, enrolled_conditions=40,
                qualified_conditions=0, censored_conditions=40, per_arm={}, limitations=[],
                runtime={'evidence_mode': 'unit_mock', 'live_calls': 0})
    return reg, data


def verdict(dataset, condition, *, status='adopted'):
    row = next(r for r in dataset['conditions'] if r['pair'] + ':' + r['arm'] == condition)
    return dict(schema='cad-harness.benchmark-user-verdict.v1', trial_id=dataset['trial_id'],
                dataset_sha256=benchmark.digest(dataset), condition=condition,
                artifact_bundle_sha256=benchmark._bundle_sha(row), judge_id='DEV-human-judge',
                source='external_human', status=status, observed_at='2026-10-16T00:00:00+00:00',
                critical_dimension_error=False, fabrication=False, first_handover_reviewed=True,
                evidence_sha256='e' * 64)


class HumanPureResults(unittest.TestCase):
    def test_actual_bound_human_adoption_unlocks_only_complete_pairs_without_mutating_base(self):
        reg, data = condition_dataset()
        before = benchmark.canonical(data)
        decisions = [verdict(data, 'B01:' + arm) for arm in benchmark.ARMS]
        result = benchmark.apply_user_verdicts(data, reg, decisions)
        self.assertEqual(benchmark.canonical(data), before)
        self.assertEqual(result['qualified_conditions'], 2)
        self.assertEqual(result['censored_conditions'], 38)
        self.assertEqual(result['pairs'][0]['savings']['full_wall_s']['saving'], 10)
        self.assertEqual(result['pairs'][0]['savings']['full_wall_s']['reduction_percent'], 50)
        self.assertTrue(all(row['savings']['full_wall_s']['saving'] is None for row in result['pairs'][1:]))
        self.assertEqual(result['status'], 'awaiting_human_verdicts')
        self.assertEqual(result['evidence_mode'], 'unit_mock')

    def test_first_fatal_history_cannot_be_erased_by_favorable_human_receipt(self):
        reg, data = condition_dataset()
        data['conditions'][0]['execution']['first_handover']['critical_dimension_error'] = True
        result = benchmark.apply_user_verdicts(data, reg, [verdict(data, 'B01:with_harness')])
        row = result['conditions'][0]
        self.assertFalse(row['qualified_completion'])
        self.assertTrue(row['adoption']['critical_error_ever'])
        self.assertEqual(row['status'], 'FAIL')
        self.assertIsNone(row['completion_time_s'])

    def test_ordinary_correction_is_allowed_only_with_verified_elapsed_300_seconds(self):
        reg, data = condition_dataset()
        row = data['conditions'][0]
        row['deterministic']['handover_history'] = [{'verdict': {'status': 'FAIL'}}]
        row['execution']['correction'] = {'elapsed_s': 280, 'verified_within_300_s': True}
        result = benchmark.apply_user_verdicts(data, reg, [verdict(data, 'B01:with_harness')])
        self.assertTrue(result['conditions'][0]['qualified_completion'])
        row['execution']['correction'] = {'elapsed_s': 301, 'verified_within_300_s': True}
        result = benchmark.apply_user_verdicts(data, reg, [verdict(data, 'B01:with_harness')])
        self.assertFalse(result['conditions'][0]['qualified_completion'])

    def test_unknown_critical_observation_stays_null_not_assumed_false(self):
        reg, data = condition_dataset()
        decision = verdict(data, 'B01:with_harness')
        decision['critical_dimension_error'] = None
        result = benchmark.apply_user_verdicts(data, reg, [decision])
        self.assertIsNone(result['conditions'][0]['adoption']['critical_error_ever'])
        self.assertFalse(result['conditions'][0]['qualified_completion'])

    def test_duplicate_judge_identity_and_artifact_replacements_are_rejected(self):
        reg, data = condition_dataset()
        decision = verdict(data, 'B01:with_harness')
        with self.assertRaisesRegex(ValueError, 'duplicate_human_verdict'):
            benchmark.apply_user_verdicts(data, reg, [decision, decision])
        for key, replacement, reason in [('judge_id', 'not-registered', 'unregistered_human'),
                                          ('artifact_bundle_sha256', 'f' * 64, 'artifact_binding'),
                                          ('first_handover_reviewed', False, 'actual_handovers')]:
            with self.subTest(key=key):
                changed = dict(decision, **{key: replacement})
                with self.assertRaisesRegex(ValueError, reason):
                    benchmark.apply_user_verdicts(data, reg, [changed])


class HumanDurableIntake(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='benchmark-human-independent-unit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reg = registration()
        self.stores = [self.root / 'primary', self.root / 'backup']
        for store in self.stores:
            store.mkdir()
        self.reg['durability'].update(location=str(self.stores[0]), backup_location=str(self.stores[1]))
        self.session = FakeSession(self.root, self.reg)
        self.session.capture_images = Mock(return_value=[])
        self.patches = [patch('subprocess.Popen', side_effect=AssertionError('no actual process in unit receipt tests')),
                        patch('subprocess.run', side_effect=AssertionError('no actual process in unit receipt tests'))]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        def execution(entry, out, arm):
            current = self.session
            current.tick += 10 if arm == 'with_harness' else 20
            if entry['id'] != 'B01':
                return dict(status='unsubmitted', reason='DEV-unit-unsubmitted', artifact_bundle=None,
                            artifact_verdict={'status': 'UNVERIFIED'}, images=[], handovers=[],
                            first_handover=None, final_handover=None, native_cad_intervals=[])
            out = Path(out)
            out.mkdir()
            native, step = out / 'model.FCStd', out / 'model.step'
            native.write_bytes(b'EXPLICIT_UNIT_MOCK_NATIVE_' + arm.encode())
            step.write_bytes(b'EXPLICIT_UNIT_MOCK_STEP_' + arm.encode())
            bundle = dict(schema='cad-harness.artifact-bundle.v4', profile='c-s1', evidence_mode='unit_mock',
                          native=benchmark.bare._record(native), step=benchmark.bare._record(step),
                          output_object=None, probes=[], extensions=[])
            bundle_path = out / 'artifacts.json'
            bundle_path.write_bytes(benchmark.canonical(bundle))
            handover = dict(at_wall=current.tick, at_active=current.tick, turn=1,
                            artifact_bundle=str(bundle_path), bundle=benchmark.bare._record(bundle_path))
            return dict(status='PASS' if arm == 'with_harness' else 'submitted', artifact_bundle=str(bundle_path),
                        artifact_verdict={'status': 'PASS', 'result': {'geometry_ok': True, 'editability_ok': True}},
                        first_handover=handover, final_handover=handover, handovers=[handover],
                        native_cad_intervals=[], images=[])
        self.session.execute_plan = lambda entry, out, **options: execution(entry, out, 'with_harness')
        with patch.object(trials, 'TrialSession', return_value=self.session), \
                patch.object(benchmark, 'validate_bound_inputs', return_value=self.reg), \
                patch.object(benchmark, 'verify_durability', return_value=self.stores), \
                patch.object(benchmark.bare, 'validate_runtime'), \
                patch.object(benchmark.bare, 'construct', side_effect=lambda current, entry, out, **options: execution(entry, out, 'bare')), \
                patch.object(benchmark.bare, 'check_artifacts', return_value={'status': 'PASS', 'result': {'geometry_ok': True, 'editability_ok': True}}):
            self.summary = benchmark.run('DEV-manifest', 'DEV-authorization', self.session.out, process=Mock())
        self.dataset = json.loads(Path(self.summary['dataset']).read_bytes())
        self.original_dataset_hash = benchmark.bare.isolation.file_hash(self.session.out / 'dataset.json')

    def write_receipt_inputs(self, condition, status='adopted'):
        evidence = self.root / (condition.replace(':', '-') + '.evidence')
        evidence.write_bytes(b'EXPLICIT_UNIT_FIXTURE_OF_EXTERNAL_HUMAN_EVIDENCE')
        document = verdict(self.dataset, condition, status=status)
        document['evidence_sha256'] = benchmark.bare.isolation.file_hash(evidence)
        source = self.root / (condition.replace(':', '-') + '.verdict.json')
        source.write_bytes(benchmark.canonical(document))
        return source, evidence

    def test_once_only_receipts_survive_local_deletion_and_publish_new_immutable_results(self):
        for arm in benchmark.ARMS:
            source, evidence = self.write_receipt_inputs('B01:' + arm)
            receipt = benchmark.record_user_verdict(self.session.out, source, evidence)
            self.assertEqual(receipt['status'], 'recorded_once')
            self.assertEqual(receipt['new_model_calls'], 0)
            self.assertEqual(len(receipt['custody']), 2)
        intake = benchmark._human_intake(self.session.out)
        for directory in intake.iterdir():
            for path in directory.iterdir():
                path.unlink()
            directory.rmdir()
        intake.rmdir()
        source, evidence = self.write_receipt_inputs('B01:with_harness', status='refused')
        with self.assertRaises(FileExistsError):
            benchmark.record_user_verdict(self.session.out, source, evidence)
        result = benchmark.user_results(self.session.out, self.root / 'human-revision')
        self.assertEqual(result['human_receipts'], 2)
        self.assertEqual(result['qualified_conditions'], 2)
        self.assertEqual(result['censored_conditions'], 38)
        self.assertEqual(result['new_model_calls'], 0)
        self.assertEqual(result['evidence_mode'], 'unit_mock')
        self.assertEqual(benchmark.bare.isolation.file_hash(self.session.out / 'dataset.json'), self.original_dataset_hash)
        self.assertTrue((self.root / 'human-revision/pairs.csv').is_file())
        derived = json.loads(Path(result['dataset']).read_bytes())
        self.assertEqual(derived['supersedes']['dataset_sha256'], benchmark.digest(self.dataset))
        self.assertEqual(derived['pairs'][0]['savings']['full_wall_s']['saving'], 10)
        for receipt in result['custody']['stores']:
            stored = Path(receipt['location'])
            self.assertTrue((stored / 'human-receipts/B01-bare/evidence.bin').is_file())
            self.assertEqual(benchmark.bare.isolation.file_hash(stored / 'hash-index.json'), receipt['hash_index_sha256'])

    def test_missing_backup_and_modified_sealed_artifact_fail_closed(self):
        source, evidence = self.write_receipt_inputs('B01:with_harness')
        benchmark.record_user_verdict(self.session.out, source, evidence)
        backup = benchmark._human_store_paths(self.reg, 'B01:with_harness')[1]
        (backup / 'evidence.bin').write_bytes(b'CHANGED_UNIT_EVIDENCE')
        with self.assertRaisesRegex(ValueError, 'receipt_changed'):
            benchmark.user_results(self.session.out, self.root / 'must-not-publish')
        self.assertFalse((self.root / 'must-not-publish').exists())
        (self.session.out / 'B01-with_harness/model.FCStd').write_bytes(b'CHANGED_UNIT_NATIVE')
        source, evidence = self.write_receipt_inputs('B01:bare')
        with self.assertRaisesRegex(ValueError, 'sealed_evidence_changed'):
            benchmark.record_user_verdict(self.session.out, source, evidence)


if __name__ == '__main__':
    unittest.main()
