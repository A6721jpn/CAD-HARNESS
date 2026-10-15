"""Focused host runner integrity/aggregation tests; subprocess/native work mocked."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import cad_verify_v4_c2_stress as stress


class StressRunnerIntegrity(unittest.TestCase):

    def test_generator_bytes_are_immutable_too(self):
        suite = stress.ROOT / 'design/cad-harness-verify-v4/dev-c2-stress'
        real_sha = stress.sha
        def changed(path):
            return '0' * 64 if Path(path).name == 'generate.py' else real_sha(path)
        with mock.patch.object(stress, 'sha', side_effect=changed):
            with self.assertRaises(ValueError):
                stress.snapshot_suite(suite)

    def test_git_lf_manifest_accepted_and_both_raw_commitments_retained(self):
        suite = stress.ROOT / 'design/cad-harness-verify-v4/dev-c2-stress'
        manifest = stress.read_json(suite / 'manifest.json')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = (suite / 'manifest.json').read_bytes()
            (root / 'manifest.json').write_bytes(original.replace(b'\r\n', b'\n'))
            (root / 'generate.py').write_bytes((suite / 'generate.py').read_bytes())
            for case in manifest['cases']:
                (root / case['filename']).write_bytes((suite / case['filename']).read_bytes())
            value = stress.snapshot_suite(root)
            commitments = value['manifest_commitments']
            self.assertEqual(commitments['actual_raw_sha256'], stress.GIT_MANIFEST_SHA256)
            self.assertEqual(commitments['checkout_raw_sha256'], stress.MANIFEST_SHA256)
            self.assertEqual(commitments['semantic_json_sha256'], stress.SEMANTIC_MANIFEST_SHA256)
            self.assertEqual((suite / 'manifest.json').read_bytes(), original)

    def test_manifest_tampering_rejected_before_manifest_parse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'manifest.json').write_bytes(b'{')
            with self.assertRaises(ValueError):
                stress.snapshot_suite(root)

    def test_single_png_tampering_fails_frozen_suite(self):
        suite = stress.ROOT / 'design/cad-harness-verify-v4/dev-c2-stress'
        real_sha = stress.sha
        def changed(path):
            return '0' * 64 if Path(path).name == 'case14_calligraphic_monogram.png' else real_sha(path)
        with mock.patch.object(stress, 'sha', side_effect=changed):
            with self.assertRaises(ValueError):
                stress.snapshot_suite(suite)

    def test_selection_only_ever_development_label(self):
        manifest = dict(cases=[dict(id='first'), dict(id='second')])
        self.assertEqual(stress.select_cases(manifest, None), (manifest['cases'], 'full_suite'))
        self.assertEqual(stress.select_cases(manifest, ['second', 'first'])[1], 'development_selection')
        for ids in (['missing'], ['first', 'first']):
            with self.assertRaises(ValueError):
                stress.select_cases(manifest, ids)

    def test_forbidden_paths_rejected_without_filesystem_metadata(self):
        with mock.patch.object(Path, 'is_symlink', side_effect=AssertionError('metadata accessed')):
            for name in ('pilot-user', 'v4-holdout-private'):
                with self.assertRaises(ValueError):
                    stress.public_path(stress.ROOT / name / 'never-open')

    def test_closed_environment_has_no_credentials_or_live_guards(self):
        with mock.patch.dict(stress.os.environ, {'PATH': 'native-bin', 'OPENAI_API_KEY': 'secret',
                'CAD_VERIFY_ARTIFACT_NATIVE': '1', 'PYTHONPATH': 'untrusted'}, clear=True):
            env = stress.command_environment()
        for key in ('OPENAI_API_KEY', 'CAD_VERIFY_ARTIFACT_NATIVE', 'PYTHONPATH'):
            self.assertNotIn(key, env)


    def test_nested_islands_are_separate_pads_with_only_immediate_holes(self):
        loops = [dict(role='outer'), dict(role='hole', parent=0), dict(role='outer', parent=1),
                 dict(role='hole', parent=2), dict(role='outer')]
        self.assertEqual(stress.component_loops(dict(loops=loops)),
                         [[loops[0], loops[1]], [loops[2], loops[3]], [loops[4]]])


class StressRunnerAggregation(unittest.TestCase):
    @staticmethod
    def rows():
        return [dict(case_id='case' + str(i), status='PASS',
                     arms={arm: dict(status='PASS') for arm in ('bare', 'harness')}) for i in range(14)]

    def test_only_all_fourteen_both_arms_and_integrity_can_pass(self):
        rows = self.rows()
        ids = [r['case_id'] for r in rows]
        result = stress.aggregate(rows, ids, label='full_suite', integrity_ok=True)
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(result['full_suite_pass'])
        for changed in ('arm', 'case', 'missing', 'duplicate', 'integrity', 'selection'):
            modified = copy.deepcopy(rows)
            if changed == 'arm':
                modified[-1]['arms']['bare']['status'] = 'UNVERIFIED'
            if changed == 'case':
                modified[0]['status'] = 'FAIL'
            if changed == 'missing':
                modified.pop()
            if changed == 'duplicate':
                modified[-1] = modified[0]
            with self.subTest(changed=changed):
                result = stress.aggregate(modified, ids,
                    label='development_selection' if changed == 'selection' else 'full_suite',
                    integrity_ok=changed != 'integrity')
                self.assertEqual(result['status'], 'BLOCKED')
                self.assertFalse(result['full_suite_pass'])
        result = stress.aggregate(rows[:1], ids[:1], label='development_selection', integrity_ok=True)
        self.assertEqual(result['development_status'], 'PASS')
        self.assertEqual(result['status'], 'BLOCKED')

    def test_neutral_requires_all_card_checks_both_formats_and_shared_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            stress.write_json(out / 'card.json', dict(criteria=[dict(id='solid'), dict(id='radius')]))
            stress.write_json(out / 'runtime.json', dict(sdk='fixed'))
            stress.write_json(out / 'judge-runtime.json', dict(sdk='fixed'))
            judge = dict(status='PASS', checks=[dict(id='solid', status='PASS'), dict(id='radius', status='PASS')])
            summary = dict(status='PASS', result=dict(status='PASS', editability_ok=True,
                judges={arm: copy.deepcopy(judge) for arm in ('fcstd', 'step')},
                runtime_binding=dict(path=str(out / 'judge-runtime.json'))))
            self.assertTrue(stress.neutral_pass(dict(returncode=0), summary, out))
            # Bundle-specific extensions are independently checked by the
            # neutral checker; shared SDK/cache/root identity cannot differ.
            stress.write_json(out / 'judge-runtime.json', dict(sdk='fixed', extension_files={'declared-proxy': {}}))
            self.assertTrue(stress.neutral_pass(dict(returncode=0), summary, out))
            for mutation in ('exit', 'missing_check', 'unverified', 'editability', 'runtime'):
                value = copy.deepcopy(summary)
                if mutation == 'missing_check':
                    value['result']['judges']['step']['checks'].pop()
                if mutation == 'unverified':
                    value['result']['judges']['fcstd']['checks'][0]['status'] = 'UNVERIFIED'
                if mutation == 'editability':
                    value['result']['editability_ok'] = False
                if mutation == 'runtime':
                    stress.write_json(out / 'judge-runtime.json', dict(sdk='drift'))
                with self.subTest(mutation=mutation):
                    self.assertFalse(stress.neutral_pass(dict(returncode=1 if mutation == 'exit' else 0), value, out))

    def test_non_failfast_both_neutral_calls_and_both_arm_construction_failure(self):
        cases = [dict(id='case' + str(i), filename='case' + str(i) + '.png') for i in range(14)]
        frozen = dict(manifest=dict(cases=cases), files={})
        def fake_command(argv, out, *, timeout):
            event = dict(returncode=0, argv=argv)
            if '_prepare' in argv:
                target = Path(argv[argv.index('--out') + 1])
                if target.parent.name == 'case0':
                    event['returncode'] = 1
                    stderr = target.parent / 'preparation-stderr.bin'
                    stderr.write_bytes(b'Traceback (most recent call last):\nValueError: contour_nonmanifold_pixel_contact\n')
                    event['stderr'] = stress.record(stderr)
                else:
                    target.mkdir()
                    stress.write_json(target / 'preparation.json', dict(status='PASS'))
            elif '_build' in argv:
                target = Path(argv[argv.index('--out') + 1])
                if target.parent.name == 'case1' and target.name == 'bare':
                    event['returncode'] = 1
                else:
                    target.mkdir()
                    stress.write_json(target / 'construction.json', dict(status='PASS'))
            else:
                target = Path(argv[argv.index('--run-dir') + 1])
                target.mkdir()
                stress.write_json(target / 'summary.json', dict(status='PASS'))
                if target.parent.name == 'case2' and target.name == 'neutral-bare':
                    event['returncode'] = 1
            return event
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(stress, 'snapshot_suite', return_value=frozen), \
                mock.patch.object(stress, 'run_command', side_effect=fake_command), \
                mock.patch.object(stress, 'neutral_pass', side_effect=lambda command, *args: command['returncode'] == 0):
            result = stress.run(Path(temporary) / 'evidence', Path(temporary) / 'frozen')
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertEqual(len(result['cases']), 14)
            self.assertTrue(result['complete'])
            for arm in ('bare', 'harness'):
                self.assertEqual(result['cases'][0]['arms'][arm]['status'], 'FAIL')
            self.assertEqual(result['cases'][0]['preparation_failure']['error_type'], 'ValueError')
            self.assertEqual(result['cases'][1]['status'], 'FAIL')
            self.assertEqual(result['cases'][1]['arms']['bare']['status'], 'FAIL')
            self.assertEqual(result['cases'][1]['arms']['harness']['status'], 'PASS')
            self.assertEqual(result['cases'][2]['arms']['bare']['status'], 'FAIL')
            self.assertEqual(result['cases'][2]['arms']['harness']['status'], 'PASS')
            self.assertEqual(result['cases'][-1]['status'], 'PASS')

    def test_after_hash_failure_blocks_with_complete_case_reports(self):
        cases = [dict(id='case' + str(i)) for i in range(14)]
        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(stress, 'snapshot_suite', side_effect=[dict(manifest=dict(cases=cases), files={}), ValueError('drift')]), \
                mock.patch.object(stress, 'run_command', return_value=dict(returncode=1)):
            out = Path(temporary) / 'evidence'
            result = stress.run(out, Path(temporary) / 'frozen')
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertFalse(result['suite_integrity_ok'])
            self.assertEqual(len(result['cases']), 14)

    def test_existing_output_never_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                stress.run(Path(temporary), Path(temporary).parent / 'unused-frozen')


if __name__ == '__main__':
    unittest.main()
