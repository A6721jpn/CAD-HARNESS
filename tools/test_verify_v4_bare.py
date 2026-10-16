"""Independent DEV-only bare protocol/accounting tests; never launch a process."""
import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import zipfile

from tools import cad_verify_v4_bare as bare
from tools import cad_verify_v4_artifacts as artifacts


class MockBoundary:
    """Explicit unit dependency, not a security boundary or live fallback."""
    python = Path('DEV-python.exe')

    def __init__(self, *args, **kwargs):
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True


class Session:
    mode = 'unit_mock'

    def __init__(self, root, responses):
        self.root, self.responses, self.tick = Path(root), iter(responses), 100.
        self.registration, self.events, self.calls = {}, [], []
        self.check_artifacts = Mock(return_value={'status': 'PASS'})

    def wall(self):
        return self.tick

    clock = wall

    def check(self):
        pass

    def path(self, key):
        return self.root / key

    def input_images(self, identifiers):
        return tuple(self.path(key) for key in identifiers)

    def event(self, kind, **fields):
        self.events.append((kind, fields))

    def call(self, record, request, runtime, **kwargs):
        self.calls.append((record, request, json.loads(json.dumps(runtime)), kwargs))
        self.tick += 1
        return next(self.responses)

    def summary(self):
        return {'charged_calls': {'bare:generation': len(self.calls)}, 'physical_attempts': len(self.calls)}


def action_write(path, content):
    return dict(kind='write', path=path, content_base64=base64.b64encode(content).decode('ascii'))


def handover(*, final=True):
    return dict(native='out/model.FCStd', step='out/model.step', source=['build.py'],
                extensions=[], output_object=None, probes=[], final=final)


def batch(actions=(), submitted=None):
    return json.dumps({'actions': list(actions), 'handover': submitted})


class BareToolBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bare-independent-dev-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'request').write_bytes(b'Original request\r\nunchanged\n')
        (self.root / 'asset').write_bytes(b'independent original asset')
        self.entry = dict(id='B01', profile='c-s1', request='request',
                          original_assets=[{'file': 'asset', 'name': 'part.step'}])
        self.patches = [patch('subprocess.Popen', side_effect=AssertionError('process forbidden')),
                        patch('subprocess.run', side_effect=AssertionError('process forbidden'))]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_third_tool_producing_response_can_submit_without_fourth_call(self):
        responses = [batch([action_write('build.py', b'print("DEV")')]), batch(),
                     batch([action_write('out/model.FCStd', b'ordinary-native-bytes'),
                            action_write('out/model.step', b'ordinary-step-bytes')], handover())]
        session = Session(self.root, responses)
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary)
        self.assertEqual(result['status'], 'submitted')
        self.assertEqual(result['calls'], 3)
        self.assertEqual(result['first_handover']['turn'], 3)
        self.assertEqual(result['first_handover'], result['final_handover'])
        self.assertEqual(len(session.calls), 3)
        self.assertEqual({c[0] for c in session.calls}, {'B01:bare'})
        for _, request, runtime, options in session.calls:
            self.assertEqual(request, 'Original request\r\nunchanged\n')
            self.assertEqual(options['pool'], 'bare:generation')
            self.assertEqual(options['model'], bare.MODEL)
            self.assertEqual(options['thinking'], 'xhigh')
            self.assertEqual(options['skill'], b'')
            self.assertNotIn('prepared', runtime)
            self.assertNotIn('card', runtime)
        bundle = json.loads(Path(result['artifact_bundle']).read_text(encoding='utf-8'))
        self.assertEqual(Path(bundle['native']['path']).read_bytes(), b'ordinary-native-bytes')
        self.assertEqual(bundle['evidence_mode'], 'unit_mock')
        self.assertFalse(result['boundary']['enforcement_verified'])
        self.assertEqual(result['human_engineering_time'], {'value': None, 'reason': 'not_applicable'})

    def test_first_handover_bytes_survive_later_edit_without_checker_feedback(self):
        first = [action_write('build.py', b'original'), action_write('out/model.FCStd', b'first-native'),
                 action_write('out/model.step', b'first-step')]
        session = Session(self.root, [batch(first, handover(final=False)),
                                    batch([action_write('out/model.FCStd', b'final-native')], handover())])
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary)
        self.assertEqual(result['calls'], 2)
        self.assertEqual(len(result['handovers']), 2)
        self.assertNotEqual(result['first_handover']['files']['out/model.FCStd']['sha256'],
                            result['final_handover']['files']['out/model.FCStd']['sha256'])
        session.check_artifacts.assert_not_called()

    def test_three_unsubmitted_responses_remain_failure_not_zero_time_success(self):
        session = Session(self.root, [batch(), batch(), batch()])
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary)
        self.assertEqual(result['status'], 'unsubmitted')
        self.assertIsNone(result['artifact_bundle'])
        self.assertEqual(result['calls'], 3)
        self.assertGreater(result['end'] - result['start'], 0)

    def test_missing_containment_is_not_replaced_with_host_execution(self):
        session = Session(self.root, [batch()])
        def unavailable(*args, **kwargs):
            raise bare.isolation.BoundaryUnavailable('DEV-denied')
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=unavailable)
        self.assertEqual(result['status'], 'construction_error')
        self.assertEqual(session.calls, [])
        self.assertIn('DEV-denied', result['reason'])

    def test_live_mode_rejects_mock_boundary_before_input_release(self):
        session = Session(self.root, [])
        session.mode = 'live'
        with self.assertRaisesRegex(ValueError, 'injection_live_forbidden'):
            bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary)
        self.assertFalse((self.root / 'run').exists())

    def test_active_budget_includes_continuations_and_never_resets(self):
        session = Session(self.root, [batch(), batch(), batch()])
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary, active_limit=2)
        self.assertEqual(result['status'], 'timed_out')
        self.assertEqual(result['calls'], 2)
        self.assertEqual(session.calls[0][3]['timeout'], 2)
        self.assertEqual(session.calls[1][3]['timeout'], 1)

    def test_supervisor_refuses_traversal_devices_case_variant_inputs_and_links(self):
        root = self.root / 'scratch'
        root.mkdir()
        for path in ('../outside', 'C:/outside', '/absolute', 'a//b', 'CON', 'x/NUL.txt', 'x.', 'a:ads', 'x\\y'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                bare.scoped(root, path, write=True)
        with self.assertRaisesRegex(ValueError, 'inputs_read_only'):
            bare.scoped(root, 'INPUTS/asset', write=True)
        source, linked = root / 'source', root / 'linked'
        source.write_bytes(b'original')
        try:
            os.link(source, linked)
        except OSError:
            self.skipTest('filesystem does not support independent hardlink fixture')
        with self.assertRaisesRegex(ValueError, 'hardlink'):
            bare.scoped(root, 'linked', write=True)

    def test_model_origin_restoration_is_rejected_before_neutral_native_process(self):
        session = Session(self.root, [])
        bundle = self.root / 'bundle.json'
        bundle.write_text('{}', encoding='utf-8')
        with patch.object(artifacts, 'load_bundle', return_value=({}, {'native': self.root / 'model.FCStd'}, {'model_feature': self.root / 'model_feature.py'})):
            result = bare.check_artifacts(session, self.entry, bundle, self.root / 'check')
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertFalse(result['untrusted_restoration_executed'])
        session.check_artifacts.assert_not_called()

    def test_undeclared_python_archive_is_rejected_without_import(self):
        native = self.root / 'model.FCStd'
        with zipfile.ZipFile(native, 'w') as archive:
            archive.writestr('Document.xml', '<Document><Python module="malicious" class="Feature" value="None"/></Document>')
        session = Session(self.root, [])
        with patch.object(artifacts, 'load_bundle', return_value=({}, {'native': native}, {})):
            result = bare.check_artifacts(session, self.entry, 'DEV-bundle', self.root / 'check')
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertIn('undeclared_python', result['reason'])
        session.check_artifacts.assert_not_called()

    @staticmethod
    def _mock_initialization(argv):
        # Unit fixture only: never an OS/native demonstration or live receipt.
        return (bare.HOST_INIT_PREFIX + argv[6] + ':' + json.dumps({
            'schema': 'freecad.host-init.v1', 'version': ['1', '1', '4'], 'gui_up': False}) + '\n').encode('utf-8')

    def test_tool_process_receipt_keeps_full_streams_but_hides_host_paths_from_model(self):
        session = Session(self.root, [])
        scratch = self.root / 'scratch'
        scratch.mkdir()
        boundary = MockBoundary()
        def process(argv, *, stdout, stderr, timeout):
            self.assertEqual(argv[:6], ['DEV-python.exe', '-I', '-B', '-u', '-c', bare.PYTHON_BOOTSTRAP])
            self.assertEqual(argv[7:], ['build.py'])
            Path(stdout).write_bytes(b'full DEV stdout')
            Path(stderr).write_bytes(self._mock_initialization(argv) + b'full DEV stderr')
            session.tick += 4
            return dict(returncode=0, start=100., end=104., stdout=str(stdout), stderr=str(stderr))
        boundary.run = Mock(side_effect=process)
        loop = bare.ToolLoop(session, scratch, boundary, self.root, lambda: 20, 'B01:bare')
        visible = loop.execute({'kind': 'python', 'args': ['build.py']})
        self.assertEqual(set(visible), {'returncode', 'stdout_base64', 'stderr_base64'})
        self.assertNotIn(str(self.root), json.dumps(visible))
        self.assertEqual(base64.b64decode(visible['stdout_base64']), b'full DEV stdout')
        self.assertEqual(loop.native_intervals, [[100., 104.]])
        receipt = [e for kind, e in session.events if kind == 'bare_tool'][0]
        self.assertEqual(receipt['record_id'], 'B01:bare')
        self.assertIn('sha256', receipt['result']['stdout_record'])
        self.assertEqual(receipt['result']['initialization']['bootstrap_sha256'], bare.BOOTSTRAP_SHA256)
        self.assertEqual(session.calls, [])

    def test_failed_tool_preserves_native_interval_and_captured_error_stream(self):
        session = Session(self.root, [])
        scratch = self.root / 'scratch'
        scratch.mkdir()
        boundary = MockBoundary()
        def timeout(argv, *, stdout, stderr, timeout):
            Path(stderr).write_bytes(self._mock_initialization(argv) + b'failed DEV process')
            session.tick += 2
            raise TimeoutError('DEV-owned-timeout')
        boundary.run = Mock(side_effect=timeout)
        loop = bare.ToolLoop(session, scratch, boundary, self.root, lambda: 20, 'B01:bare')
        with self.assertRaises(TimeoutError):
            loop.execute({'kind': 'python', 'args': ['build.py']})
        self.assertEqual(loop.native_intervals, [[100., 102.]])
        receipt = [e for kind, e in session.events if kind == 'bare_process_stopped'][0]
        self.assertEqual(receipt['streams']['stderr']['bytes'], (self.root / 'tool-001.stderr').stat().st_size)
        self.assertEqual(receipt['initialization']['version'], ['1', '1', '4'])
        self.assertTrue(any(kind == 'bare_tool' and 'TimeoutError' in fields['error'] for kind, fields in session.events))

    def test_missing_explicit_handover_is_retained_as_failed_first_declaration(self):
        session = Session(self.root, [batch([], handover())])
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary)
        self.assertEqual(result['status'], 'construction_error')
        self.assertEqual(result['first_handover']['collection_status'], 'failed')
        self.assertEqual(result['first_handover']['turn'], 1)
        self.assertIsNone(result['artifact_bundle'])
        self.assertEqual(result['calls'], 1)


    def test_bundle_named_source_is_never_overwritten_by_collector_metadata(self):
        scratch = self.root / 'scratch'
        (scratch / 'out').mkdir(parents=True)
        (scratch / 'out/model.FCStd').write_bytes(b'DEV_NATIVE_BYTES')
        (scratch / 'out/model.step').write_bytes(b'DEV_STEP_BYTES')
        snapshots = []
        for index, name in enumerate(('bundle.json', 'BUNDLE.JSON')):
            with self.subTest(name=name):
                payload = b'DEV_SELF_AUTHORED_SOURCE_' + name.encode('ascii')
                (scratch / name).write_bytes(payload)
                declaration = handover()
                declaration['source'] = [name]
                out = self.root / ('collection-' + str(index))
                result = bare.collect(scratch, declaration, out, profile='c-s1', evidence_mode='unit_mock')
                record = result['reproducible_source'][0]
                self.assertEqual(Path(record['path']).read_bytes(), payload)
                self.assertEqual(bare.isolation.file_hash(record['path']), record['sha256'])
                self.assertTrue(Path(record['path']).is_relative_to(out / 'submitted'))
                self.assertNotEqual(Path(result['artifact_bundle']).read_bytes(), payload)
                snapshots.append((record, payload))
        for record, payload in snapshots:
            self.assertEqual(Path(record['path']).read_bytes(), payload)
            self.assertEqual(bare.isolation.file_hash(record['path']), record['sha256'])

    def test_case_insensitive_source_aliases_are_rejected_before_collection(self):
        scratch = self.root / 'scratch'
        scratch.mkdir()
        declaration = handover()
        declaration['source'] = ['bundle.json', 'BUNDLE.JSON']
        with self.assertRaisesRegex(ValueError, 'alias_collision'):
            bare.collect(scratch, declaration, self.root / 'collection', profile='c-s1')
        self.assertFalse((self.root / 'collection').exists())

    def test_malformed_response_and_tool_inspection_each_consume_a_continuation(self):
        final = [action_write('build.py', b'DEV_SOURCE'), action_write('out/model.FCStd', b'DEV_NATIVE'),
                 action_write('out/model.step', b'DEV_STEP')]
        session = Session(self.root, ['not valid JSON',
            batch([{'kind': 'read', 'path': 'does-not-exist'}]), batch(final, handover())])
        result = bare.construct(session, self.entry, self.root / 'run', boundary_factory=MockBoundary)
        self.assertEqual(result['status'], 'submitted')
        self.assertEqual(result['calls'], 3)
        self.assertEqual(len(session.calls), 3)
        history = session.calls[2][2]['history']
        self.assertEqual(history[0]['tool_results'][0]['error'], 'invalid_action_batch')
        self.assertEqual(history[1]['tool_results'][0]['error'], 'FileNotFoundError')
        self.assertNotIn(str(self.root), json.dumps(history))

    def test_original_asset_mutation_fails_closed_before_another_model_response(self):
        session = Session(self.root, [])
        scratch = self.root / 'scratch'
        (scratch / 'inputs').mkdir(parents=True)
        original = scratch / 'inputs/part.step'
        original.write_bytes(b'ORIGINAL_DEV_ASSET')
        record = bare._record(original)
        record['name'] = 'inputs/part.step'
        boundary = MockBoundary()
        def mutate(argv, *, stdout, stderr, timeout):
            original.write_bytes(b'CHANGED_DEV_ASSET')
            Path(stdout).write_bytes(b'')
            Path(stderr).write_bytes(self._mock_initialization(argv))
            return dict(returncode=0, start=100., end=100., stdout=str(stdout), stderr=str(stderr))
        boundary.run = Mock(side_effect=mutate)
        loop = bare.ToolLoop(session, scratch, boundary, self.root, lambda: 20, 'B01:bare', [record])
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'original_input_changed'):
            loop.execute({'kind': 'python', 'args': ['build.py']})
        self.assertEqual(session.calls, [])

    def test_every_python_entry_mode_uses_initialized_pinned_bootstrap(self):
        session = Session(self.root, [])
        scratch = self.root / 'scratch'
        scratch.mkdir()
        boundary = MockBoundary()
        observed = []
        def process(argv, *, stdout, stderr, timeout):
            observed.append(argv)
            Path(stdout).write_bytes(b'')
            Path(stderr).write_bytes(self._mock_initialization(argv))
            return dict(returncode=0, stdout=str(stdout), stderr=str(stderr))
        boundary.run = Mock(side_effect=process)
        loop = bare.ToolLoop(session, scratch, boundary, self.root, lambda: 20, 'B01:bare')
        entries = [['-c', 'print(1)'], ['-m', 'independent_dev.module'], ['build.py', 'argument']]
        for args in entries:
            loop.execute({'kind': 'python', 'args': args})
        self.assertEqual([argv[7:] for argv in observed], entries)
        self.assertTrue(all(argv[:6] == ['DEV-python.exe', '-I', '-B', '-u', '-c', bare.PYTHON_BOOTSTRAP] for argv in observed))
        self.assertEqual(len(loop.native_intervals), 3)
        for args in ([], ['-S', 'build.py'], ['-c'], ['-m', '../escape'], ['../escape.py']):
            with self.subTest(args=args), self.assertRaises(ValueError):
                loop.execute({'kind': 'python', 'args': args})
        self.assertEqual(boundary.run.call_count, 3)

    def test_unverified_initialization_is_not_reported_as_native_cad_host_time(self):
        session = Session(self.root, [])
        scratch = self.root / 'scratch'
        scratch.mkdir()
        boundary = MockBoundary()
        def process(argv, *, stdout, stderr, timeout):
            Path(stdout).write_bytes(b'')
            Path(stderr).write_bytes(b'NO_INITIALIZED_FREECAD_HOST')
            session.tick += 3
            return dict(returncode=0, stdout=str(stdout), stderr=str(stderr))
        boundary.run = Mock(side_effect=process)
        loop = bare.ToolLoop(session, scratch, boundary, self.root, lambda: 20, 'B01:bare')
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'initialization_unverified'):
            loop.execute({'kind': 'python', 'args': ['build.py']})
        self.assertEqual(loop.native_intervals, [])
        self.assertEqual(loop.unverified_native_intervals, [[100., 103.]])

class StagedRuntimeAdmission(unittest.TestCase):
    """Real DEV byte copies with a substituted source pin, never SDK execution."""
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='bare-staging-independent-dev-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source, self.target = self.root / 'source', self.root / 'private-runtime'
        for name, content in {'bin/python.exe': b'DEV_PINNED_PYTHON',
                              'bin/Lib/site-packages/cycler/__pycache__/cycler.pyc': b'DEV_CACHE_BYTES',
                              'doc/offline.txt': b'DEV_OFFLINE_DOCUMENTATION'}.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (self.source / 'empty-library').mkdir()
        for item in (patch.object(bare.isolation, 'PINNED_PYTHON', self.source / 'bin/python.exe'),
                     patch.object(bare.isolation, 'boot_id', return_value='DEV-boot'),
                     patch('subprocess.Popen', side_effect=AssertionError('no staging process')),
                     patch.object(bare.isolation.WindowsBoundary, '_api', side_effect=AssertionError('no staging ACL API'))):
            item.start()
            self.addCleanup(item.stop)

    def stage(self):
        return bare.isolation.stage_runtime(self.source, self.target)

    def test_complete_independent_copy_includes_cache_and_empty_directories(self):
        staged = self.stage()
        self.assertEqual(staged['root'], str(self.target))
        self.assertEqual(staged['inventory']['directories'][-1], 'empty-library')
        for name, record in staged['inventory']['files'].items():
            source, target = self.source / name, self.target / name
            self.assertEqual(source.read_bytes(), target.read_bytes())
            self.assertEqual(record['bytes'], target.stat().st_size)
            self.assertEqual(target.stat().st_nlink, 1)
            self.assertNotEqual((source.stat().st_dev, source.stat().st_ino), (target.stat().st_dev, target.stat().st_ino))
        self.assertIn('bin/Lib/site-packages/cycler/__pycache__/cycler.pyc', staged['inventory']['files'])
        self.assertEqual(staged['proof']['purpose'], 'pretrial_software_environment')
        self.assertEqual(staged['proof']['source_python']['sha256'], staged['proof']['python']['sha256'])
        self.assertNotEqual(staged['proof']['source_python']['path'], staged['proof']['python']['path'])
        self.assertEqual(bare.isolation.validate_staged_runtime(self.target, staged['inventory'], staged['proof']), self.target)
        (self.root / 'inventory.json').write_bytes(bare.isolation.canonical(staged['inventory']))
        (self.root / 'proof.json').write_bytes(bare.isolation.canonical(staged['proof']))
        config = dict(root=str(self.target), inventory='inventory.json', staging_proof='proof.json')
        self.assertEqual(bare.validate_runtime(Session(self.root, []), config), self.target)

    def test_staged_bytes_and_closed_inventory_tampering_fail(self):
        staged = self.stage()
        python = self.target / 'bin/python.exe'
        python.write_bytes(b'DEV_ALTERNATE_SOFTWARE')
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'staged_inventory_changed'):
            bare.isolation.validate_staged_runtime(self.target, staged['inventory'], staged['proof'])
        python.write_bytes((self.source / 'bin/python.exe').read_bytes())
        (self.target / 'unadmitted.py').write_bytes(b'DEV_EXTRA')
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'staged_inventory_changed'):
            bare.isolation.validate_staged_runtime(self.target, staged['inventory'], staged['proof'])

    def test_original_pin_and_source_bytes_remain_authoritative(self):
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'original_pinned_source'):
            bare.isolation.stage_runtime(self.root, self.target)
        staged = self.stage()
        (self.source / 'bin/python.exe').write_bytes(b'DEV_SOURCE_REPLACEMENT')
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'source_inventory_changed'):
            bare.isolation.validate_staged_runtime(self.target, staged['inventory'], staged['proof'])

    def test_relocation_proof_and_private_copy_prerequisites_are_not_metadata_echoes(self):
        staged = self.stage()
        changed = dict(staged['proof'], root=str(self.source))
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'staging_proof_mismatch'):
            bare.isolation.validate_staged_runtime(self.target, staged['inventory'], changed)
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'private_copy_required'):
            bare.isolation.validate_staged_runtime(self.source, staged['inventory'], staged['proof'])
        with patch.object(bare.isolation, 'os', SimpleNamespace(name='nt')):
            with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'verified_private_runtime_required'):
                bare.isolation.WindowsBoundary(self.root, self.source)
            with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'scratch_source_overlap'):
                bare.isolation.WindowsBoundary(self.source, self.target, runtime_inventory=staged['inventory'], staging_proof=staged['proof'])
        with self.assertRaisesRegex(ValueError, 'staged_runtime_configuration_required'):
            bare.validate_runtime(Session(self.root, []), dict(root=str(self.source), inventory='old.json'))

    def test_existing_destination_and_unreadable_cache_are_not_skipped(self):
        self.target.mkdir()
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'new_private_destination'):
            self.stage()
        self.target.rmdir()
        with patch.object(bare.isolation.os, 'walk', side_effect=PermissionError('DEV_inaccessible_cache')):
            with self.assertRaisesRegex(PermissionError, 'inaccessible_cache'):
                self.stage()
        self.assertFalse(self.target.exists())

    def test_hardlink_replacement_cannot_share_source_security(self):
        staged = self.stage()
        python = self.target / 'bin/python.exe'
        python.unlink()
        os.link(self.source / 'bin/python.exe', python)
        with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'private_hardlink'):
            bare.isolation.validate_staged_runtime(self.target, staged['inventory'], staged['proof'])


class SecurityRollbackUnit(unittest.TestCase):
    def test_all_snapshots_are_durable_before_any_security_mutation(self):
        with tempfile.TemporaryDirectory(prefix='bare-journal-unit-dev-') as temporary:
            root = Path(temporary)
            scratch, runtime = root / 'scratch', root / 'runtime'
            scratch.mkdir()
            runtime.mkdir()
            boundary = object.__new__(bare.isolation.WindowsBoundary)
            boundary.name, boundary.scratch, boundary.runtime = 'DEV-profile', scratch, runtime
            boundary.recovery_path = root / 'security-recovery.json'
            boundary.snapshots, boundary.changed = {}, False
            boundary.k = SimpleNamespace(CreateFileW=Mock(side_effect=[123, 456]), CloseHandle=Mock())
            boundary._security = Mock(return_value=dict(descriptor=b'DEV_ORIGINAL_DESCRIPTOR', sddl='DEV_ORIGINAL S:(ML;OICI;NW;;;LW)', control=4, owned=True, private_acl=True))
            boundary.a = SimpleNamespace(SetSecurityInfo=Mock(side_effect=AssertionError('preflight cannot change rights')))
            with patch.object(bare.isolation, 'boot_id', return_value='DEV-boot'), patch.object(bare.isolation.os, 'fsync') as fsync:
                boundary._prepare_security()
            fsync.assert_called_once()
            journal = json.loads(boundary.recovery_path.read_bytes())
            self.assertEqual({record['path'] for record in journal['snapshots']}, {str(scratch), str(runtime)})
            self.assertFalse(boundary.changed)
            boundary.a.SetSecurityInfo.assert_not_called()
            self.assertEqual(boundary._restore_security(), [])
            self.assertFalse(boundary.recovery_path.exists())
            self.assertEqual(boundary.k.CloseHandle.call_count, 2)

    def test_restoration_uses_held_handles_and_rejects_changed_control(self):
        with tempfile.TemporaryDirectory(prefix='bare-security-unit-dev-') as temporary:
            root = Path(temporary)
            boundary = object.__new__(bare.isolation.WindowsBoundary)
            boundary.scratch, boundary.changed = root, True
            boundary.recovery_path = root / 'recovery.json'
            boundary.recovery_path.write_bytes(b'DEV_DURABLE_SNAPSHOT')
            snapshot = dict(handle=123, descriptor=b'DEV_DESCRIPTOR', sddl='DEV_ORIGINAL', control=0x8404)
            boundary.snapshots = {root: snapshot}
            boundary.a = SimpleNamespace(
                GetSecurityDescriptorDacl=Mock(return_value=1),
                SetSecurityInfo=Mock(return_value=0), SetKernelObjectSecurity=Mock(return_value=1),
                SetNamedSecurityInfoW=Mock(side_effect=AssertionError('path reopening is forbidden')))
            boundary.k = SimpleNamespace(CloseHandle=Mock())
            boundary._security = Mock(return_value=dict(sddl='DEV_ORIGINAL', control=0x8004))
            errors = boundary._restore_security()
            self.assertTrue(any('restore_not_exact' in error for error in errors), errors)
            self.assertTrue(boundary.recovery_path.exists(), 'failed restoration must retain durable original evidence')
            boundary.a.SetNamedSecurityInfoW.assert_not_called()

    def test_failed_handle_preflight_changes_no_acl_and_closes_prior_handles(self):
        with tempfile.TemporaryDirectory(prefix='bare-preflight-unit-dev-') as temporary:
            root = Path(temporary)
            scratch, runtime = root / 'scratch', root / 'runtime'
            scratch.mkdir()
            runtime.mkdir()
            boundary = object.__new__(bare.isolation.WindowsBoundary)
            boundary.scratch, boundary.runtime = scratch, runtime
            boundary.snapshots, boundary.changed = {}, False
            boundary.k = SimpleNamespace(CreateFileW=Mock(side_effect=[123, bare.isolation.C.c_void_p(-1).value]), CloseHandle=Mock())
            boundary._security = Mock(return_value=dict(descriptor=b'DEV', sddl='DEV S:(ML;OICI;NW;;;LW)', control=4, owned=True, private_acl=True))
            boundary.a = SimpleNamespace(SetSecurityInfo=Mock(side_effect=AssertionError('preflight cannot change rights')))
            with patch.object(bare.isolation.C, 'get_last_error', return_value=5, create=True):
                with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'preflight_handle'):
                    boundary._prepare_security()
            self.assertFalse(boundary.changed)
            self.assertEqual(boundary.snapshots, {})
            boundary.k.CloseHandle.assert_called_once_with(123)
            boundary.a.SetSecurityInfo.assert_not_called()

    def test_public_runtime_dacl_is_rejected_before_security_changes(self):
        with tempfile.TemporaryDirectory(prefix='bare-private-dacl-unit-dev-') as temporary:
            root = Path(temporary)
            scratch, runtime = root / 'scratch', root / 'runtime'
            scratch.mkdir()
            runtime.mkdir()
            boundary = object.__new__(bare.isolation.WindowsBoundary)
            boundary.scratch, boundary.runtime = scratch, runtime
            boundary.snapshots, boundary.changed = {}, False
            boundary.k = SimpleNamespace(CreateFileW=Mock(return_value=123), CloseHandle=Mock())
            boundary._security = Mock(return_value=dict(descriptor=b'DEV', sddl='DEV_PUBLIC S:(ML;OICI;NW;;;LW)', control=4, owned=True, private_acl=False))
            boundary.a = SimpleNamespace(SetSecurityInfo=Mock(side_effect=AssertionError('public copy must not receive grants')))
            with self.assertRaisesRegex(bare.isolation.BoundaryUnavailable, 'private_runtime_dacl_required'):
                boundary._prepare_security()
            self.assertFalse(boundary.changed)
            self.assertEqual(boundary.snapshots, {})
            boundary.a.SetSecurityInfo.assert_not_called()


if __name__ == '__main__':
    unittest.main()
