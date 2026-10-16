"""Closed-authority and real shared-transport regressions; no provider/native calls."""
import copy
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_trials as trials, cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_model_judge as judge, eval_verify_v4 as cli
from tools.cad_verify_guard import Stop
from tools.test_support import start_tempdirs, stop_tempdirs
from tools.test_verify_v4_live import response, OVERLOAD
from tools.test_verify_v4_s1 import _HostFixtures
from tools import cad_verify_v4_agent as agent


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class Clock:
    def __init__(self):
        self.value = 0.0
        self.origin = datetime.now(timezone.utc) - timedelta(seconds=1)

    def __call__(self):
        return self.value

    def utc(self):
        return (self.origin + timedelta(seconds=self.value)).isoformat()

    def advance(self, seconds):
        self.value += seconds


class Fixture:
    """Explicit DEV files; the implementation verifier/executable are injected."""
    def __init__(self, root, count=3):
        self.root, self.clock = Path(root), Clock()
        self.source = self.root / 'source'
        self.source.mkdir()
        self.files, self.observed = {}, []
        self.quota = self.root / 'quota.json'
        self.refresh_quota()
        self.rubric = dict(schema=judge.RUBRIC_SCHEMA, id='independent-dev',
                           items=[dict(id='requested-shape', criterion='Independent DEV shape', visual=False)])
        rubric = self.add('rubric', self.rubric, 'rubric')
        entries = []
        for index in range(count):
            identity = 'DEV-%d' % (index + 1)
            entries.append(dict(id=identity,
                request=self.add(identity+'-request', b'Independent DEV request\r\nunchanged bytes\r\n', 'request'),
                deterministic=self.add(identity+'-native', dict(status='PASS'), 'deterministic'),
                rubric=rubric, images=[]))
        self.registration = dict(schema=trials.REGISTRATION_SCHEMA, phase='judge', trial_id='dev-trial',
            cycle_id='dev-cycle', source_root=str(self.source), files=self.files, entries=entries,
            order=[entry['id'] for entry in entries], judge=dict(trials.ASTRA), budget={'judge': count})
        self.registration_path = self.root / 'registration.json'
        ledger.write_json(self.registration_path, self.registration)
        self.lock_path = self.root / 'implementation.json'
        ledger.write_json(self.lock_path, dict(schema=trials.integrated.SCHEMA, authorization=None))
        self.executable = self.root / 'never-executed-omp.exe'
        self.executable.write_bytes(b'Independent DEV identity; never execute')
        self.auth = dict(schema=trials.AUTH_SCHEMA, phase='judge', trial_id='dev-trial', cycle_id='dev-cycle',
            approved_by='DEV fixture, not a live approval', user_approved=True, clock_confirmation=True,
            independent_control_validation=True, registration_sha256=ledger.file_sha(self.registration_path),
            integrated_manifest_sha256=ledger.file_sha(self.lock_path), quota_snapshot=str(self.quota),
            omp_profile='independent-unit-operator', reserved_calls={'judge': count})
        self.auth_path = self.root / 'authorization.json'
        ledger.write_json(self.auth_path, self.auth)
        self.manifest_path = self.root / 'freeze' / 'manifest.json'

    def add(self, identity, value, role):
        filename = identity + ('.bin' if isinstance(value, bytes) else '.json')
        path = self.source / filename
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            ledger.write_json(path, value)
        self.files[identity] = dict(path=filename, sha256=ledger.file_sha(path), bytes=path.stat().st_size, role=role)
        return identity

    def refresh_quota(self, used=0, age=0):
        observed = datetime.fromisoformat(self.clock.utc()) - timedelta(seconds=age)
        self.quota.write_text(json.dumps(dict(snapshot_id='independent-dev', observed_at=observed.isoformat(),
                                               used_percent=used)), encoding='utf-8')

    def sleep(self, seconds):
        self.clock.advance(seconds)
        self.refresh_quota()

    def verifier(self, path):
        return ledger.read_json(path)

    def resolver(self, ignored):
        return dict(omp=str(self.executable), sha256=ledger.file_sha(self.executable), version='DEV-never-run')

    def freeze(self):
        return trials.freeze_trial(self.registration_path, self.auth_path, self.lock_path,
            self.manifest_path.parent, verifier=self.verifier, executable_resolver=self.resolver)

    def verdict(self, status='PASS'):
        return json.dumps(dict(schema=judge.VERDICT_SCHEMA, rubric_id=self.rubric['id'],
            items=[dict(id='requested-shape', status=status, reason='Independent DEV judgment')],
            critical_dimension_error=False, fabrication=False))

    def process(self, argv, captures, *, cwd, timeout):
        self.observed.append(dict(argv=list(argv), timeout=timeout))
        self.clock.advance(2)
        captures['stdout'].feed(response(self.verdict(), model='gpt-6-astra'))
        captures['stderr'].feed(b'Independent DEV raw stderr\r\n')
        return 0

    def session(self, *, process=None, out='run', phase='judge'):
        return trials.TrialSession(self.manifest_path, self.auth_path, self.root / out, phase=phase,
            process=self.process if process is None else process, wall=self.clock, sleep=self.sleep,
            verifier=self.verifier)


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        environment = patch.dict(os.environ, OMP_PROFILE='independent-unit-operator')
        environment.start()
        self.addCleanup(environment.stop)
        no_provider = patch.object(trials.live, 'stream_process', side_effect=AssertionError('NO LIVE CALL'))
        no_provider.start()
        self.addCleanup(no_provider.stop)

    def test_separate_authorization_refuses_before_source_access(self):
        fixture = Fixture(self.root)
        invalid = dict(fixture.auth, registration_sha256='1'*64)
        fixture.auth_path.write_text(json.dumps(invalid), encoding='utf-8')
        with patch.object(trials, '_source_files', side_effect=AssertionError('unauthorized source read')):
            with self.assertRaisesRegex(Stop, 'separate_authorization'):
                fixture.freeze()
        self.assertFalse(fixture.manifest_path.parent.exists())

    def test_mock_manifest_cannot_launch_without_injected_transport(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        with self.assertRaisesRegex(Stop, 'mock_manifest_not_live'):
            trials.verify_trial(fixture.manifest_path)
        with self.assertRaisesRegex(Stop, 'requires_injected_transport'):
            trials.TrialSession(fixture.manifest_path, fixture.auth_path, self.root/'run',
                                phase='judge', verifier=fixture.verifier)

    def test_authorization_copy_or_renamed_freeze_cannot_reset_entitlement(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        copy_path = self.root / 'copied-authorization.json'
        copy_path.write_bytes(fixture.auth_path.read_bytes())
        with self.assertRaisesRegex(Stop, 'already_frozen'):
            trials.freeze_trial(fixture.registration_path, copy_path, fixture.lock_path, self.root/'another-freeze',
                                verifier=fixture.verifier, executable_resolver=fixture.resolver)
        trials.verify_trial(fixture.manifest_path, verifier=fixture.verifier, allow_mock=True)
        self.assertEqual(fixture.observed, [])

    def test_new_approval_cannot_retake_same_registered_trial_identity(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        path = self.root / 'changed-approval.json'
        ledger.write_json(path, dict(fixture.auth, approved_by='different DEV approval, same trial'))
        with self.assertRaisesRegex(Stop, 'already_frozen'):
            trials.freeze_trial(fixture.registration_path, path, fixture.lock_path, self.root/'retake-freeze',
                                verifier=fixture.verifier, executable_resolver=fixture.resolver)
        trials.verify_trial(fixture.manifest_path, verifier=fixture.verifier, allow_mock=True)
        self.assertEqual(fixture.observed, [])

    def test_native_injection_cannot_receive_a_live_label(self):
        with self.assertRaisesRegex(Stop, 'injected_native_requires_injected_model'):
            trials.TrialSession('unused', 'unused', self.root/'unused', phase='judge',
                                native_process=lambda *args, **kwargs: 0)
        self.assertFalse((self.root/'unused').exists())

    def test_falsy_injected_transport_never_falls_back_to_live_provider(self):
        fixture = Fixture(self.root, count=1)
        fixture.freeze()
        class FalsyTransport:
            def __bool__(self):
                return False
            def __call__(self, *args, **kwargs):
                return fixture.process(*args, **kwargs)
        with fixture.session(process=FalsyTransport()) as session:
            session.call('DEV-1', 'DEV', {}, pool='judge', **trials.ASTRA, purpose='judge', max_calls=1)
            self.assertEqual(session.mode, 'unit_mock')
            self.assertEqual(session.summary()['live_calls'], 0)
        self.assertEqual(len(fixture.observed), 1)

    def test_unrelated_public_table_cannot_relabel_a_live_cohort(self):
        canonical = trials.ROOT / 'design/cad-harness-verify-v4/holdout-families-commitment.md'
        registration = {'phase':'families', 'public_commitment':'published'}
        bindings = trials._public_bindings(registration, {'published':trials._record(canonical)}, 'live')
        self.assertEqual(bindings['families']['sha256'], ledger.file_sha(canonical))
        unrelated = self.root / 'unrelated-public.md'
        unrelated.write_text('Independent DEV text, not the canonical commitment.\\n', encoding='utf-8')
        with self.assertRaisesRegex(Stop, 'canonical_public_commitment'):
            trials._public_bindings(registration, {'published':trials._record(unrelated)}, 'live')

    def test_postprocessing_errors_retain_driver_and_first_handover(self):
        for stage in ('neutral', 'render'):
            with self.subTest(stage=stage):
                case = self.root / stage
                case.mkdir()
                fixture = Fixture(case)
                fixture.freeze()
                candidate = case / 'generated'
                candidate.mkdir()
                (case/'execution').mkdir()
                (candidate/'model.FCStd').write_bytes(b'DEV artifact bytes, never opened natively')
                (candidate/'model.step').write_bytes(b'ISO-10303-21; DEV, never imported')
                driver = dict(status='PASS', stop_reason=None, result=dict(candidate_dir=str(candidate),
                    compile=dict(status='PASS', output_object='Model', artifact_probes=[], restoration_modules=[])))
                paths = dict.fromkeys(('request','card','input_manifest','prepared'), fixture.registration_path)
                with fixture.session() as session:
                    with patch.object(session, 'release_entry', return_value=paths), patch.object(
                            trials.s1, 'request', return_value=(driver, 0)):
                        with patch.object(session, 'check_artifacts',
                                side_effect=OSError('DEV neutral worker interrupted') if stage=='neutral' else None,
                                return_value={'status':'PASS','result':{'status':'PASS'}}), patch.object(
                                session, 'capture_images', side_effect=OSError('DEV rendering interrupted')):
                            result = session.execute_plan(dict(id='DEV-1', profile='c-s1'), case/'execution',
                                                          pool='judge', **trials.ASTRA)
                    self.assertEqual(result['status'], 'ERROR')
                    self.assertEqual(result['driver_result']['status'], 'PASS')
                    self.assertIsNotNone(result['first_handover'])
                    self.assertEqual(result['first_handover']['status'], 'PASS' if stage=='render' else 'UNVERIFIED')
                    self.assertEqual(ledger.read_json(result['checkpoint'])['status'], 'ERROR')
                    self.assertEqual(result['error']['type'], 'OSError')
                    self.assertTrue(session.fatal)
                self.assertEqual(fixture.observed, [])

    def test_operator_profile_change_and_cross_phase_launch_are_refused(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        with patch.dict(os.environ, OMP_PROFILE='changed-operator'):
            with self.assertRaisesRegex(Stop, 'execution_identity_changed'):
                fixture.session()
        with self.assertRaisesRegex(Stop, 'phase_mismatch'):
            fixture.session(phase='pilot')
        self.assertFalse((fixture.manifest_path.parent/'execution-claim.json').exists())

    def test_recomputed_wrapper_cannot_change_frozen_model_or_trial_identity(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        value = ledger.read_json(fixture.manifest_path)
        value['judge'] = dict(model=trials.GENERATOR['model'], thinking='xhigh')
        payload = {key: item for key, item in value.items() if key != 'sha256_file'}
        (fixture.manifest_path.parent/'SHA256.json').write_text(json.dumps(payload), encoding='utf-8')
        value['sha256_file'] = ledger.file_sha(fixture.manifest_path.parent/'SHA256.json')
        fixture.manifest_path.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaisesRegex(Stop, 'execution_identity_changed'):
            fixture.session()
        self.assertEqual(fixture.observed, [])

    def test_changed_source_and_second_execution_cannot_retake_a_trial(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        with fixture.session() as session:
            session.check()
        with self.assertRaises(FileExistsError):
            fixture.session(out='retake')
        request = fixture.source / fixture.files['DEV-1-request']['path']
        request.write_bytes(b'changed source')
        with self.assertRaisesRegex(Stop, 'input_commitment_mismatch'):
            trials.verify_trial(fixture.manifest_path, verifier=fixture.verifier, allow_mock=True)
        self.assertEqual(fixture.observed, [])

    def test_soft_hard_stale_and_invalid_quota_admit_zero_calls(self):
        for used, age in ((55, 0), (60, 0), (0, 301), (None, 0)):
            with self.subTest(used=used, age=age):
                case = self.root / ('case-'+str(used)+'-'+str(age))
                case.mkdir()
                fixture = Fixture(case)
                fixture.freeze()
                fixture.refresh_quota(used, age)
                with fixture.session() as session:
                    with self.assertRaises(Stop):
                        session.call('DEV-1', 'DEV', {}, pool='judge', **trials.ASTRA,
                                     purpose='judge', max_calls=1)
                    self.assertEqual(session.charged, {'judge': 0})
                self.assertEqual(fixture.observed, [])

    def test_authorization_cannot_be_spent_on_another_purpose_or_record(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        with fixture.session() as session:
            for identity, purpose, model, maximum in (
                    ('DEV-1', 'source', trials.GENERATOR, 3),
                    ('not-enrolled', 'judge', trials.ASTRA, 1),
                    ('DEV-1', 'judge', trials.ASTRA, 2)):
                with self.subTest(identity=identity, purpose=purpose, maximum=maximum):
                    with self.assertRaises(Stop):
                        session.call(identity, 'DEV', {}, pool='judge', **model,
                                     purpose=purpose, max_calls=maximum)
            self.assertEqual(session.charged, {'judge': 0})
        self.assertEqual(fixture.observed, [])

    def test_many_exact_overloads_consume_one_slot_and_no_active_wait(self):
        fixture = Fixture(self.root, count=1)
        fixture.freeze()
        outputs = iter([OVERLOAD]*7 + [response(fixture.verdict(), model='gpt-6-astra')])
        envelopes = []
        def process(argv, captures, *, cwd, timeout):
            payload = next(Path(arg[1:]) for arg in argv if arg.startswith('@'))
            envelopes.append((list(argv), payload.read_bytes()))
            fixture.clock.advance(2)
            captures['stdout'].feed(next(outputs))
            captures['stderr'].feed(b'raw DEV stderr\x00')
            return 0
        with fixture.session(process=process) as session:
            text = session.call('DEV-1', 'DEV request\r\n', {'target': 'verdict'}, pool='judge',
                                **trials.ASTRA, purpose='judge', max_calls=1)
            self.assertEqual(json.loads(text)['schema'], judge.VERDICT_SCHEMA)
            self.assertEqual(session.charged, {'judge': 1})
            self.assertEqual(session.summary()['physical_attempts'], 8)
            self.assertEqual(session.clock(), 2)
            self.assertEqual(fixture.clock(), 7*602+2)
            self.assertTrue(all(value == envelopes[0] for value in envelopes))
            with self.assertRaisesRegex(Stop, 'budget_exhausted'):
                session.call('DEV-1', 'DEV', {}, pool='judge', **trials.ASTRA, purpose='judge', max_calls=1)
        events = list(ledger.rows(self.root/'run/ledger.jsonl'))
        completed = [event for event in events if event['event'] == 'attempt_finished']
        self.assertEqual([event['charged'] for event in completed], [False]*7+[True])
        self.assertTrue(all(Path(event['streams']['stderr']['path']).read_bytes() == b'raw DEV stderr\x00'
                            for event in completed))

    def test_quota_during_exempt_wait_refunds_only_that_reservation(self):
        fixture = Fixture(self.root, count=1)
        fixture.freeze()
        def process(argv, captures, *, cwd, timeout):
            fixture.observed.append(argv)
            captures['stdout'].feed(OVERLOAD)
            captures['stderr'].feed(b'overload DEV')
            return 0
        def sleep(seconds):
            fixture.clock.advance(seconds)
            fixture.refresh_quota(55)
        with fixture.session(process=process) as session:
            session.sleep = sleep
            with self.assertRaisesRegex(Stop, 'quota_stop'):
                session.call('DEV-1', 'DEV', {}, pool='judge', **trials.ASTRA, purpose='judge', max_calls=1)
            self.assertEqual(session.charged, {'judge': 0})
            self.assertEqual(session.summary()['physical_attempts'], 1)
        self.assertEqual(len(fixture.observed), 1)

    def test_capture_failure_is_charged_preserved_and_terminal(self):
        fixture = Fixture(self.root)
        fixture.freeze()
        def process(argv, captures, *, cwd, timeout):
            fixture.observed.append(argv)
            captures['stdout'].feed(b'partial DEV\xff')
            captures['stderr'].feed(b'failed DEV\x00')
            raise OSError('independent DEV pipe failure')
        with fixture.session(process=process) as session:
            with self.assertRaises(OSError):
                session.call('DEV-1', 'DEV', {}, pool='judge', **trials.ASTRA, purpose='judge', max_calls=1)
            with self.assertRaisesRegex(Stop, 'transport_or_capture_interrupted'):
                session.call('DEV-2', 'DEV', {}, pool='judge', **trials.ASTRA, purpose='judge', max_calls=1)
            self.assertEqual(session.charged, {'judge': 1})
        completed = [row for row in ledger.rows(self.root/'run/ledger.jsonl') if row['event']=='attempt_finished']
        self.assertEqual(len(fixture.observed), 1)
        self.assertEqual(Path(completed[0]['streams']['stdout']['path']).read_bytes(), b'partial DEV\xff')
        self.assertFalse(completed[0]['streams']['stdout']['complete'])
        self.assertIsNone(completed[0]['usage']['values']['input_tokens'])

    def test_cli_executes_real_shared_transport_and_retains_stopped_denominators(self):
        fixture = Fixture(self.root)
        with redirect_stdout(io.StringIO()) as stdout:
            code = cli.main(['freeze-live-trial', '--registration', str(fixture.registration_path),
                '--authorization', str(fixture.auth_path), '--integrated-manifest', str(fixture.lock_path),
                '--run-dir', str(fixture.manifest_path.parent)], verifier=fixture.verifier,
                executable_resolver=fixture.resolver)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())['evidence_mode'], 'unit_mock')
        def process(argv, captures, *, cwd, timeout):
            code = fixture.process(argv, captures, cwd=cwd, timeout=timeout)
            fixture.refresh_quota(55)
            return code
        with redirect_stdout(io.StringIO()) as stdout:
            code = cli.main(['live-judge', '--manifest', str(fixture.manifest_path),
                '--authorization', str(fixture.auth_path), '--run-dir', str(self.root/'run')],
                process=process, wall=fixture.clock, sleep=fixture.sleep, verifier=fixture.verifier)
        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertEqual([row['status'] for row in result['records']], ['PASS','INCOMPLETE','NOT_RUN'])
        self.assertEqual(result['denominator'], 3)
        self.assertEqual(result['accounting']['charged_calls'], {'judge': 1})
        self.assertEqual(result['accounting']['live_calls'], 0)
        self.assertEqual(len(fixture.observed), 1)

    def test_manifest_asset_closure_and_checker_role_cannot_be_bypassed(self):
        asset = self.root / 'shape.step'
        asset.write_bytes(b'ISO-10303-21; Independent DEV')
        manifest = self.root / 'manifest-input.json'
        spec = dict(path='shape.step', sha256=ledger.file_sha(asset), bytes=asset.stat().st_size, role='checker')
        ledger.write_json(manifest, dict(assets={'target': spec}))
        files = {'manifest': trials._record(manifest), 'asset': trials._record(asset)}
        registration = dict(files={'manifest': {'role': 'input_manifest'}, 'asset': {'role': 'source_asset'}},
                            entries=[dict(input_manifest='manifest', model_inputs=['asset'])])
        with self.assertRaisesRegex(Stop, 'checker_asset_in_model_inputs'):
            trials._input_closure(registration, files)
        registration['entries'][0]['model_inputs'] = []
        trials._input_closure(registration, files)
        with self.assertRaisesRegex(Stop, 'unbound_manifest_asset'):
            trials._input_closure(registration, {'manifest': files['manifest']})

    def test_pilot_cannot_launch_before_complete_holdout_custody(self):
        with self.assertRaisesRegex(Stop, 'requires_completed_holdouts'):
            trials._pilot_prerequisites({'phase':'pilot'}, {}, {'sha256':'1'*64}, allow_mock=False)

    def test_final_numerics_and_fatal_history_survive_ordinary_correction(self):
        evidence = dict(status='PASS', result={'status':'PASS'},
                        handover_history=[{'status':'FAIL', 'critical_dimension_error':False}])
        self.assertEqual(judge._deterministic_status(evidence), 'PASS')
        evidence['handover_history'][0]['fabrication'] = True
        self.assertEqual(judge._deterministic_status(evidence), 'FAIL')
        evidence['handover_history'][0]['fabrication'] = False
        evidence['result']['status'] = 'FAIL'
        self.assertEqual(judge._deterministic_status(evidence), 'FAIL')


class CheckerProjectionTests(_HostFixtures, unittest.TestCase):
    def test_s1_checker_geometry_cannot_enter_generator_context_or_selection(self):
        self.manifest['assets']['checker'] = dict(self.manifest['assets']['reference'], role='checker')
        self.save_manifest()
        packet = self.packet()
        packet['assets']['checker'] = copy.deepcopy(packet['assets']['reference'])
        packet['assets']['checker']['asset_id'] = 'checker'
        adapter = agent.PlanSkillAdapter(b'DEV skill', 'Independent DEV request', self.manifest_path, packet)
        self.assertIn('reference', adapter.inputs['assets'])
        self.assertNotIn('checker', adapter.inputs['assets'])
        with self.assertRaisesRegex(ValueError, 'selection_not_generator_asset'):
            agent.PlanSkillAdapter(b'DEV skill', 'Independent DEV request', self.manifest_path, packet,
                                  [dict(asset_id='checker', face_id='Face1', signature='1'*64)])


if __name__ == '__main__':
    unittest.main()
