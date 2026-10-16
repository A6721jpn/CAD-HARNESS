"""Independent DEV-only benchmark enrollment, clocks, custody and runner tests."""
import base64
import copy
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import cad_verify_v4_benchmark as benchmark
from tools import cad_verify_v4_trials as trials


def registration():
    files = {}
    def add(key, role='protocol'):
        files[key] = dict(path=key + '.json', sha256='1' * 64, bytes=1, role=role,
                          origin='operational' if role != 'original_request' else 'published_cohort')
        return key
    result = dict(schema='cad-harness.live-registration.v1', phase='benchmark', trial_id='DEV-benchmark',
                  cycle_id='DEV-cycle', source_root='DEV-no-private-source', cohort={}, files=files,
                  pairs=[], order=[], order_seed='independent-fixed-DEV-seed',
                  reservations=dict(benchmark.RESERVATIONS), caps={'active_s_per_arm': 1200, 'calls_per_arm': 3},
                  bare_runtime={'root': str(Path(tempfile.gettempdir()) / 'DEV-frozen-private-freecad'),
                                'inventory': add('runtime', 'bare_runtime_inventory'),
                                'staging_proof': add('staging', 'bare_runtime_staging_proof')},
                  rubric=add('rubric'), protocol=add('protocol'), source_commitment=add('public'),
                  adapter_demonstration=add('adapter'), isolation_demonstration=add('isolation'),
                  custody={'author': 'DEV-author', 'reviewer': 'DEV-reviewer', 'custodian': 'DEV-custodian'},
                  human_judges=[{'id': 'DEV-human-judge', 'kind': 'human', 'qualification_evidence': add('human', 'human_judge_identity')}],
                  clocks={'clock_id': 'DEV-clock', 'boot_id': 'DEV-boot', 'utc_reference': '2026-01-01T00:00:00+00:00', 'resolution_s': 1e-7},
                  durability={'store_id': 'DEV-registered-store', 'location': 'DEV-primary', 'backup_location': 'DEV-backup',
                              'retention': 'DEV-registered-retention', 'versioning': 'DEV-immutable-versions',
                              'immutable': True, 'custodian': 'DEV-custodian',
                              'provisioning_evidence': add('provisioning'), 'retrieval_proof': add('retrieval')})
    number = 0
    for family, strata in benchmark.STRATA.items():
        family_pairs = []
        for stratum, count in strata.items():
            for _ in range(count):
                number += 1
                identifier = 'B%02d' % number
                entry = dict(id=identifier, family=family, stratum=stratum,
                             profile='c-s1' if family in ('C1', 'C2', 'C3') else 'c-s2' if family == 'C4' else 'c-s3',
                             same_card_both_arms=True, independent_fresh=True, original_assets=[], preparation={})
                for field in ('request', 'input_manifest', 'prepared', 'card', 'context', 'pair_record'):
                    entry[field] = add(identifier + '-' + field, 'original_request' if field == 'request' else 'protocol')
                for arm in benchmark.ARMS:
                    entry['preparation'][arm] = dict(preparation_intervals=[], native_cad_intervals=[], custody_hold_intervals=[],
                        recorded_once=True, evidence=add(identifier + '-' + arm + '-preparation'), clock_id='DEV-clock', active_s=0)
                result['pairs'].append(entry)
                family_pairs.append(identifier)
        for index, identifier in enumerate(family_pairs):
            arms = benchmark.ARMS if index % 2 == 0 else tuple(reversed(benchmark.ARMS))
            result['order'].extend({'pair': identifier, 'arm': arm} for arm in arms)
    return result


class BenchmarkRegistration(unittest.TestCase):
    def test_exact_twenty_pairs_fixed_strata_and_counterbalanced_order(self):
        value = registration()
        self.assertIs(benchmark.validate_registration(value), value)
        for mutate, reason in (
                (lambda v: v['pairs'].pop(), 'twenty_pairs'),
                (lambda v: v['pairs'][0].update(stratum='wrong'), 'family_strata'),
                (lambda v: v['pairs'][0].update(id='DEV-replacement'), 'published_identity'),
                (lambda v: v['order'].__setitem__(1, v['order'][0]), 'complete_once'),
                (lambda v: v['reservations'].update({'bare:generation': 61}), 'reservations'),
                (lambda v: v['caps'].update(calls_per_arm=4), 'signed_caps'),
                (lambda v: v['pairs'][0]['preparation']['bare'].update(recorded_once=False), 'no_replay')):
            with self.subTest(reason=reason):
                changed = copy.deepcopy(value)
                mutate(changed)
                with self.assertRaisesRegex(ValueError, reason):
                    benchmark.validate_registration(changed)

    def test_installed_runtime_or_missing_staging_proof_is_not_preregisterable(self):
        value = registration()
        for mutate in (
                lambda v: v['bare_runtime'].update(root=str(benchmark.bare.isolation.PINNED_PYTHON.parent.parent)),
                lambda v: v['bare_runtime'].pop('staging_proof'),
                lambda v: v['files']['staging'].update(role='protocol'),
                lambda v: v['files']['runtime'].update(origin='published_cohort')):
            changed = copy.deepcopy(value)
            mutate(changed)
            with self.assertRaisesRegex(ValueError, 'verified_private_runtime'):
                benchmark.validate_registration(changed)

    def test_order_must_be_two_firsts_per_arm_in_every_family(self):
        value = registration()
        value['order'] = [dict(pair=p['id'], arm=a) for p in value['pairs'] for a in benchmark.ARMS]
        with self.assertRaisesRegex(ValueError, 'balanced_first_order'):
            benchmark.validate_registration(value)

    def test_harness_derived_asset_cannot_be_registered_as_bare_input(self):
        value = registration()
        value['pairs'][0]['original_assets'] = [{'name': 'contour.json', 'file': value['pairs'][0]['prepared']}]
        with self.assertRaisesRegex(ValueError, 'original_asset_only'):
            benchmark.validate_registration(value)

    def test_unverified_backup_and_preparation_clock_are_not_silently_accepted(self):
        value = registration()
        value['durability']['backup_location'] = value['durability']['location']
        with self.assertRaisesRegex(ValueError, 'immutable_backup'):
            benchmark.validate_registration(value)
        value = registration()
        value['pairs'][0]['preparation']['bare']['clock_id'] = 'different-boot'
        with self.assertRaisesRegex(ValueError, 'clock_mismatch'):
            benchmark.validate_registration(value)

    def test_checker_gold_and_masks_are_excluded_but_typed_original_raster_is_mandatory(self):
        manifest = {'assets': {
            'reference': dict(path='reference.step', kind='step', role='reference', sha256='2' * 64, bytes=1),
            'gold': dict(path='original-looking.step', kind='step', role='checker', sha256='2' * 64, bytes=1),
            'raw': dict(path='mask-looking-original.png', kind='image', role='checker', sha256='2' * 64, bytes=1),
            'mask': dict(path='original-looking.png', kind='image', role='checker', sha256='2' * 64, bytes=1),
            'contour': dict(path='contour.json', kind='contour', role='contour', sha256='2' * 64, bytes=1),
            'font': dict(path='font.ttf', kind='font', role='font', sha256='2' * 64, bytes=1),
            'license': dict(path='license.txt', kind='license', role='license', sha256='2' * 64, bytes=1)}}
        prepared = {'assets': {'contour': {'schema': 'cad-harness.contour.v4c',
                                         'source_image_asset_id': 'raw',
                                         'source_mask': {'encoding': 'row-runs', 'rows': []}}}}
        expected = {'reference.step', 'mask-looking-original.png', 'font.ttf', 'license.txt'}
        self.assertEqual(set(benchmark.original_source_assets(manifest, prepared)), expected)
        production = {'assets': {'raw_contour': dict(path='raw.png', kind='image', role='contour')}}
        self.assertEqual(set(benchmark.original_source_assets(production, {'assets': {}})), {'raw.png'})
        families = benchmark._module('cad_verify_v4_family_live')
        with tempfile.TemporaryDirectory(prefix='benchmark-exposure-independent-dev-') as temporary:
            root = Path(temporary)
            metadata = {}
            for name, value in (('input_manifest', manifest), ('prepared', prepared), ('card', {})):
                metadata[name] = root / (name + '.json')
                metadata[name].write_text(json.dumps(value), encoding='utf-8')
            for extra, omit_raw in (('gold', False), ('mask', False), (None, True)):
                with self.subTest(extra=extra, omit_raw=omit_raw):
                    value = registration()
                    pair = value['pairs'][0]
                    for field, name in dict(request='request.txt', input_manifest='manifest.json', prepared='prepared.json',
                                            card='card.json', context='context.json', pair_record='pair.json').items():
                        value['files'][pair[field]]['published_relative_path'] = 'benchmark/B01/' + name
                    selected = ['reference', 'font', 'license'] + ([] if omit_raw else ['raw']) + ([extra] if extra else [])
                    for key in selected:
                        record = manifest['assets'][key]
                        value['files']['original_' + key] = dict(path='unused-' + key, role='original_asset',
                            origin='published_cohort', sha256=record['sha256'], bytes=record['bytes'],
                            published_relative_path='benchmark/B01/' + record['path'])
                    pair['original_assets'] = [{'name': manifest['assets'][key]['path'], 'file': 'original_' + key} for key in selected]
                    pair['original_images'] = [] if omit_raw else ['original_raw']
                    paths = {pair[field]: path for field, path in metadata.items()}
                    with patch.object(families, 'validate_published_files'), patch.object(families, '_card_requirements'):
                        with self.assertRaisesRegex(ValueError, 'same_original_manifest_assets'):
                            benchmark.validate_bound_inputs(value, paths.__getitem__)

    def test_metadata_only_isolation_flags_do_not_satisfy_retained_execution_evidence(self):
        proof = dict(schema='cad-harness.bare-isolation-smoke.v1', evidence_mode='unit_mock',
                     lpac=True, zero_capabilities=True, native_freecad=True, cleanup_restored=True)
        with self.assertRaisesRegex(ValueError, 'actual_retained_isolation_source_streams'):
            benchmark._validate_isolation_streams(proof)

    def test_echoed_initialization_object_without_nonce_bound_stderr_is_rejected(self):
        source, stdout, stderr = b'DEV_UNIT_SOURCE', b'DEV_UNIT_STDOUT', b'DEV_NOT_A_BOOTSTRAP'
        encode = lambda value: base64.b64encode(value).decode('ascii')
        sha = lambda value: hashlib.sha256(value).hexdigest()
        process = dict(isolation='windows_lpac_zero_capabilities', lpac_token_verified=True, job_assigned=True,
            capability_count=0, job_child_limit=1, cleanup_status='exited', stdin='NUL', returncode=0,
            lpac_token_evidence=dict(schema='cad-harness.lpac-accesscheck.v1',
                world_only_read=False, all_application_packages_read=False, own_package_read=True),
            stdout_base64=encode(stdout), stderr_base64=encode(stderr),
            stdout_record=dict(sha256=sha(stdout), bytes=len(stdout)), stderr_record=dict(sha256=sha(stderr), bytes=len(stderr)),
            initialization=dict(schema='freecad.host-init.v1', version=['1', '1', '4'], gui_up=False,
                                bootstrap_sha256=benchmark.bare.BOOTSTRAP_SHA256))
        proof = dict(evidence_mode='unit_mock', source_base64=encode(source), source_sha256=sha(source),
            relocated_python='DEV-private-python', stdout_sha256=sha(stdout), stderr_sha256=sha(stderr),
            native_process=process, shell_process=dict(process), timeout_process=dict(process),
            native_command=['DEV-private-python', '-I', '-B', '-u', '-c', benchmark.bare.PYTHON_BOOTSTRAP, '1' * 32, 'build.py'])
        with self.assertRaisesRegex(ValueError, 'actual_bootstrap_stream'):
            benchmark._validate_isolation_streams(proof)

    def test_mocked_native_receipt_cannot_satisfy_actual_adapter_prerequisite(self):
        value = registration()
        with tempfile.TemporaryDirectory(prefix='benchmark-adapter-metadata-dev-') as temporary:
            path = Path(temporary) / 'unit-only.json'
            path.write_text(json.dumps(dict(schema='cad-harness.benchmark-adapter-demonstration.v1',
                evidence_mode='unit_mock', actual_native=True, live_calls=0, profile='c-s1',
                same_card_sha256='1' * 64, methods={'ordinary': {}, 'with_harness': {}})), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'actual_neutral_adapter_demonstration'):
                benchmark._validate_adapter_demonstration(value, lambda key: path)


class BenchmarkAccounting(unittest.TestCase):
    def test_full_wall_service_active_and_native_union_are_matched_not_summed(self):
        prep = dict(preparation_intervals=[[10, 20]], native_cad_intervals=[[12, 15]], custody_hold_intervals=[[20, 80]], active_s=10)
        value = benchmark.measured(prep, 100, 140, 30, [[101, 111], [105, 119], [130, 135]])
        self.assertEqual(value['full_wall_s'], 130)
        self.assertEqual(value['service_s'], 70)
        self.assertEqual(value['active_s'], 40)
        self.assertEqual(value['native_cad_s'], 26)
        self.assertEqual(value['human_active_s'], {'value': None, 'reason': 'not_applicable'})
        self.assertEqual(value['kernel_cpu_s'], {'value': None, 'reason': 'not_measured'})

    def test_prospective_custody_hold_closes_at_release_without_replaying_preparation(self):
        value = registration()
        prep = value['pairs'][0]['preparation']['with_harness']
        prep.update(preparation_intervals=[[10, 20]], native_cad_intervals=[[12, 15]],
                    custody_hold_intervals=[[20, None]], active_s=10)
        benchmark.validate_registration(value)
        measured = benchmark.measured(prep, 100, 140, 30, [[105, 110]])
        self.assertEqual(measured['full_wall_s'], 130)
        self.assertEqual(measured['service_s'], 50)
        self.assertEqual(measured['active_s'], 40)
        self.assertEqual(measured['custody_hold_intervals'], [[20, 100]])
        self.assertEqual(prep['custody_hold_intervals'], [[20, None]])
        prep['custody_hold_intervals'] = [[15, None]]
        with self.assertRaisesRegex(ValueError, 'open_custody_hold_overlap'):
            benchmark.validate_registration(value)

    def test_failed_and_zero_missing_baselines_propagate_null_without_cherry_picking(self):
        successful = dict(qualified_completion=True, timing={m: 12 for m in benchmark.METRICS})
        baseline = dict(qualified_completion=True, timing={m: 10 for m in benchmark.METRICS})
        comparison = benchmark.savings(successful, baseline)
        self.assertEqual(comparison['full_wall_s']['saving'], -2)
        self.assertEqual(comparison['full_wall_s']['reduction_percent'], -20)
        baseline['timing']['active_s'] = 0
        baseline['timing']['native_cad_s'] = None
        comparison = benchmark.savings(successful, baseline)
        self.assertEqual(comparison['active_s'], {'saving': None, 'reduction_percent': None, 'reason': 'zero_baseline'})
        self.assertEqual(comparison['native_cad_s']['reason'], 'missing_matched_metric')
        baseline['qualified_completion'] = False
        self.assertTrue(all(v['saving'] is None for v in benchmark.savings(successful, baseline).values()))

    def test_missing_human_decision_never_becomes_automatic_adoption(self):
        deterministic = {'status': 'PASS', 'result': {'geometry_ok': True, 'editability_ok': True}}
        self.assertFalse(benchmark._qualified(deterministic, {'status': 'PASS'}, {'status': 'unknown', 'critical_error_ever': None}))
        self.assertFalse(benchmark._qualified(deterministic, {'status': 'PASS'}, {'status': 'adopted', 'critical_error_ever': True}))
        self.assertTrue(benchmark._qualified(deterministic, {'status': 'PASS'}, {'status': 'adopted', 'critical_error_ever': False}))


    def test_unverified_host_initialization_keeps_native_total_null_with_reason(self):
        row = benchmark._failed('DEV_host_initialization_missing')
        row['execution'] = {'unverified_python_host_intervals': [[100., 102.]]}
        row['timing']['native_cad_s'] = 5.
        benchmark._condition_record(Mock(), row)
        self.assertIsNone(row['timing']['native_cad_s'])
        self.assertEqual(row['timing']['observed_initialized_native_host_s'], 5.)
        self.assertEqual(row['timing_missing_reasons']['native_cad_s'],
                         'pinned_freecad_host_initialization_unverified')


class FakeSession:
    mode = 'unit_mock'

    def __init__(self, root, value):
        self.out, self.registration, self.tick = root / 'run', value, 100.
        self.out.mkdir()
        self.native_cad_intervals, self.calls, self.judgments = [], [], []
        self.root, self.closed = root, False
        (root / 'request').write_bytes(b'Independent DEV original request\r\n')
        (root / 'rubric').write_bytes(b'{"DEV_rubric":true}')
        (self.out / 'ledger.jsonl').write_bytes(b'')
        self.manifest = {}
        for key, document in (('registration', value), ('authorization', {'evidence_mode': 'unit_mock'}),
                              ('integrated_lock', {'DEV_independent_source_only': True})):
            path = root / (key + '.json')
            path.write_bytes(benchmark.canonical(document))
            self.manifest[key] = benchmark.bare._record(path)
        self.manifest_path = root / 'execution-manifest.json'
        self.manifest_path.write_bytes(benchmark.canonical(self.manifest))

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.event('run_finished')
        self.closed = True

    def path(self, key):
        return self.root / ('rubric' if key == 'rubric' else 'request')

    def wall(self):
        return self.tick

    clock = wall

    def check(self):
        return None

    def event(self, kind, **fields):
        with (self.out / 'ledger.jsonl').open('ab') as handle:
            handle.write(benchmark.canonical({'kind': kind, **fields}) + b'\n')

    def execute_plan(self, entry, out, **options):
        self.calls.append((entry['id'], options))
        self.tick += 5
        return dict(status='PASS', artifact_verdict={'status': 'PASS', 'result': {'geometry_ok': True, 'editability_ok': True}},
                    first_handover={'monotonic': self.tick}, native_cad_intervals=[], images=[])

    def judge(self, record, request, deterministic, rubric, **options):
        self.judgments.append((record, request, rubric, options))
        self.tick += 2
        return {'status': 'PASS'}

    def summary(self):
        count = len(self.calls) + len(self.judgments)
        return {'evidence_mode': 'unit_mock', 'logical_calls': count, 'physical_attempts': count, 'live_calls': 0, 'final_v4_ready': False}


class BenchmarkRunnerAndCustody(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='benchmark-independent-dev-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_mocked_runner_preserves_all_forty_denominators_and_seals_closed_ledger(self):
        value = registration()
        session = FakeSession(self.root, value)
        stores = [self.root / 'primary', self.root / 'backup']
        for store in stores:
            store.mkdir()
        def construct(current, entry, out, **options):
            current.tick += 3
            return dict(status='unsubmitted', reason='DEV-no-submission', artifact_bundle=None,
                        first_handover=None, final_handover=None, handovers=[], native_cad_intervals=[])
        with patch.object(trials, 'TrialSession', return_value=session) as factory, \
                patch.object(benchmark, 'validate_bound_inputs', return_value=value), \
                patch.object(benchmark, 'verify_durability', return_value=stores), \
                patch.object(benchmark.bare, 'validate_runtime'), \
                patch.object(benchmark.bare, 'construct', side_effect=construct), \
                patch('subprocess.Popen', side_effect=AssertionError('no process in mocked trial')):
            summary = benchmark.run('DEV-manifest', 'DEV-authorization', session.out, process=Mock())
        self.assertEqual(factory.call_args.kwargs['phase'], 'benchmark')
        self.assertTrue(session.closed)
        self.assertEqual(len(session.calls), 20)
        self.assertTrue(all(options['pool'] == 'with_harness:generation' and options['max_calls'] == 3 for _, options in session.calls))
        self.assertEqual(len(session.judgments), 40)
        self.assertTrue(all(j[2] == {'DEV_rubric': True} for j in session.judgments))
        self.assertTrue(all(j[1].endswith('\r\n') for j in session.judgments))
        dataset = json.loads(Path(summary['dataset']).read_bytes())
        self.assertEqual(len(dataset['conditions']), 40)
        self.assertEqual(dataset['censored_conditions'], 40)
        self.assertEqual(dataset['qualified_conditions'], 0)
        self.assertEqual(summary['custody']['status'], 'retrieved_hash_verified')
        self.assertTrue(all(p['savings']['full_wall_s']['saving'] is None for p in dataset['pairs']))
        for store in stores:
            sealed = store / value['trial_id']
            self.assertIn(b'run_finished', (sealed / 'ledger.jsonl').read_bytes())
            index = json.loads((sealed / 'hash-index.json').read_bytes())
            for relative, record in index['files'].items():
                self.assertEqual(benchmark.bare.isolation.file_hash(sealed / relative), record['sha256'])
            self.assertTrue((sealed / 'custody-receipt.json').is_file())

    def test_event_chain_detects_changes_and_does_not_overwrite_existing_evidence(self):
        session = FakeSession(self.root, registration())
        path = session.out / 'events.jsonl'
        events = benchmark.Events(path, session)
        events.append('enrolled', pair='DEV-independent')
        events.append('stopped', reason='DEV-refusal')
        events.close()
        previous = '0' * 64
        for raw in path.read_bytes().splitlines():
            event = json.loads(raw)
            actual = event.pop('sha256')
            self.assertEqual(event['previous_sha256'], previous)
            self.assertEqual(benchmark.digest(event), actual)
            previous = actual
        with self.assertRaises(FileExistsError):
            benchmark.Events(path, session)

    def test_local_reports_do_not_satisfy_registered_backed_up_retrieval(self):
        value = registration()
        session = FakeSession(self.root, value)
        value['durability']['location'] = str(session.out)
        value['durability']['backup_location'] = str(self.root / 'backup')
        provisioning = {k: value['durability'][k] for k in ('store_id', 'location', 'backup_location', 'retention', 'immutable', 'versioning')}
        provisioning.update(schema='cad-harness.benchmark-store-registration.v1', approved_by='DEV-custodian')
        proof = {'schema': 'cad-harness.benchmark-custody-proof.v1', 'store_id': value['durability']['store_id'],
                 'probe': {'path': 'DEV-probe', 'bytes': 1, 'sha256': '1' * 64}}
        (self.root / 'provisioning').write_bytes(benchmark.canonical(provisioning))
        (self.root / 'retrieval').write_bytes(benchmark.canonical(proof))
        session.path = lambda key: self.root / key
        with self.assertRaisesRegex(ValueError, 'reports_are_not_durable'):
            benchmark.verify_durability(session)


    def test_sealing_quarantines_generated_hardlinks_without_reading_external_files(self):
        out = self.root / 'evidence'
        out.mkdir()
        secret = self.root / 'outside-DEV-secret'
        secret.write_bytes(b'DEV_SECRET_MUST_NOT_ENTER_CUSTODY')
        linked = out / 'generated-link'
        try:
            linked.hardlink_to(secret)
        except OSError:
            self.skipTest('filesystem does not support independent DEV hardlink fixture')
        safe = out / 'safe.txt'
        safe.write_bytes(b'DEV-owned-evidence')
        files = benchmark._evidence_files(out)
        self.assertNotIn(linked, files)
        self.assertIn(safe, files)
        quarantine = json.loads((out / 'quarantined-files.json').read_bytes())
        self.assertEqual(quarantine['files'], [{'path': 'generated-link', 'reason': 'nonregular_or_hardlinked_not_read'}])
        self.assertNotIn('DEV_SECRET_MUST_NOT_ENTER_CUSTODY', json.dumps(quarantine))

    def test_prerelease_retrieval_rechecks_probe_in_both_registered_stores(self):
        value = registration()
        stores = [self.root / 'primary', self.root / 'backup']
        for store in stores:
            store.mkdir()
            (store / 'DEV-probe').write_bytes(b'INDEPENDENT_DEV_CUSTODY_PROBE')
        value['durability'].update(location=str(stores[0]), backup_location=str(stores[1]))
        provision = {k: value['durability'][k] for k in ('store_id', 'location', 'backup_location', 'retention', 'immutable', 'versioning')}
        provision.update(schema='cad-harness.benchmark-store-registration.v1', approved_by='DEV-authorized-custodian')
        record = benchmark.bare._record(stores[0] / 'DEV-probe')
        record['path'] = 'DEV-probe'
        proof = {'schema': 'cad-harness.benchmark-custody-proof.v1', 'store_id': value['durability']['store_id'], 'probe': record}
        (self.root / 'provisioning').write_bytes(benchmark.canonical(provision))
        (self.root / 'retrieval').write_bytes(benchmark.canonical(proof))
        resolved, _ = benchmark._validate_store_retrieval(value, lambda key: self.root / key)
        self.assertEqual(resolved, stores)
        (stores[1] / 'DEV-probe').write_bytes(b'CHANGED')
        with self.assertRaisesRegex(ValueError, 'retrieval_hash_failed'):
            benchmark._validate_store_retrieval(value, lambda key: self.root / key)

    def test_execution_index_cannot_swap_published_request_for_hidden_card(self):
        value = registration()
        first = value['pairs'][0]
        value['files'][first['request']]['published_relative_path'] = 'benchmark/B01/card.json'
        families = benchmark._module('cad_verify_v4_family_live')
        resolver = Mock(side_effect=AssertionError('no source read after wrong original identity'))
        with patch.object(families, 'validate_published_files'):
            with self.assertRaisesRegex(ValueError, 'published_pair_identity'):
                benchmark.validate_bound_inputs(value, resolver)
        resolver.assert_not_called()

    def test_driver_error_checkpoint_and_first_handover_survive_downstream_judge_failure(self):
        value = registration()
        session = FakeSession(self.root, value)
        stores = [self.root / 'primary', self.root / 'backup']
        for store in stores:
            store.mkdir()
        execution = dict(status='ERROR', reason='original_driver_failure',
            driver_result={'status': 'ERROR', 'checkpoint': {'stage': 'CAD', 'captured': True}},
            first_handover={'at_wall': 101., 'checkpoint': {'first_native_capture': 'unit-only'}},
            artifact_verdict={'status': 'UNVERIFIED', 'result': {'geometry_ok': None, 'editability_ok': None}},
            native_cad_intervals=[], images=[])
        def failed_driver(entry, out, **options):
            session.calls.append((entry['id'], options))
            session.tick += 5
            session.fatal = 'original_driver_failure'
            return copy.deepcopy(execution)
        session.execute_plan = Mock(side_effect=failed_driver)
        session.judge = Mock(side_effect=RuntimeError('latched_driver_stops_judge'))
        with patch.object(trials, 'TrialSession', return_value=session), \
                patch.object(benchmark, 'validate_bound_inputs', return_value=value), \
                patch.object(benchmark, 'verify_durability', return_value=stores), \
                patch.object(benchmark.bare, 'validate_runtime'), \
                patch.object(benchmark.bare, 'construct') as bare_runner, \
                patch('subprocess.Popen', side_effect=AssertionError('no processes in mocked trial')):
            result = benchmark.run('DEV-manifest', 'DEV-authorization', session.out, process=Mock())
        data = json.loads(Path(result['dataset']).read_bytes())
        first = data['conditions'][0]
        self.assertEqual(first['status'], 'ERROR')
        self.assertEqual(first['construction_status'], 'ERROR')
        self.assertEqual(first['reason'], 'original_driver_failure')
        self.assertIn('latched_driver_stops_judge', first['secondary_stop_reason'])
        self.assertEqual(first['execution']['driver_result'], execution['driver_result'])
        self.assertEqual(first['first_handover'], execution['first_handover'])
        self.assertEqual(first['final_handover'], execution['first_handover'])
        self.assertEqual(first['deterministic']['status'], 'UNVERIFIED')
        self.assertTrue(all(row['right_censored'] for row in data['conditions']))
        self.assertEqual(len(data['conditions']), 40)
        self.assertEqual(session.execute_plan.call_count, 1)
        bare_runner.assert_not_called()

if __name__ == '__main__':
    unittest.main()
