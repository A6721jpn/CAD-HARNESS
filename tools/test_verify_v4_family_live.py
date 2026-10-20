"""Independent DEV/no-network family runner boundary and scoring regressions.

No holdout, pilot, provider, or native process is opened by these host tests.
Native-process injection models result transport only, never native validity.
"""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from tools import cad_verify_v4_family_live as family
from tools import cad_verify_v4_inputs as inputs, cad_verify_v4_judges as judges
from tools import cad_verify_v4_artifact_judges as artifact_judges
from tools import cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_c2_recipe as c2_recipe
from tools import cad_verify_v4_artifacts as artifacts, cad_verify_v4_worker as worker
from tools.cad_verify_guard import Stop
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def dev_card(entry):
    criteria = [dict(id='valid', metric='solid_valid'),
                dict(id='roundtrip', metric='native_roundtrip', require_editable=True)]
    if entry['family'] == 'C2':
        criteria += [dict(id='radius', metric='min_radius', minimum_mm=.25),
                     dict(id='access', metric='tool_access', tool_radius_mm=.25)]
    if entry['family'] == 'C5':
        criteria += [dict(id='g2', metric='g2_continuity'),
                     dict(id='deviation', metric='surface_deviation', maximum_mm=.005)]
    return dict(schema='cad-harness.judge-card.v4c', source='independent_dev',
                profile=entry['profile'], criteria=criteria)


def dev_tool_criterion():
    return dict(tool_radius_mm=.25, maximum_uncovered_mm2=0, area_uncertainty_mm2=.000001,
                curve_tolerance_mm=.000001, buffer_segments=64, require_connected=True)


class DevRegistration:
    def __init__(self, root):
        self.root = root
        self.files, self.cards = {}, {}
        roster = self.file('roster', b'opaque independent DEV bytes; intentionally not JSON\n', 'family_roster')
        rubric = self.file('rubric', {'schema': 'unit_mock_rubric', 'frozen': True}, 'judge_rubric')
        entries = []
        active_recipe = c2_recipe.load()
        for name, spec in family.FAMILIES.items():
            number = 0
            for stratum, (count, _) in spec['strata'].items():
                for _ in range(count):
                    number += 1
                    entry = dict(id=f'{name}-{number:02d}', family=name, profile=spec['profile'], stratum=stratum)
                    for field in ('request', 'input_manifest', 'prepared', 'card', 'context'):
                        value = (b'Independent DEV construction request\n' if field == 'request'
                                 else dev_card(entry) if field == 'card'
                                 else {'schema': 'unit_mock_' + field, 'evidence_mode': 'independent_dev'})
                        if field == 'prepared' and name == 'C2':
                            value['assets'] = {'dev_contour': dict(schema='cad-harness.contour.v4c',
                                recipe=active_recipe['recipe'],
                                recipe_sha256=active_recipe['canonical_sha256'])}
                        entry[field] = self.file(entry['id'] + '_' + field, value, field)
                        self.files[entry[field]]['published_relative_path'] = ('generative/' + entry['id'] + '/'
                                                                            + family.ENTRY_FILENAMES[field])
                    entry['model_inputs'] = [entry['request'], entry['input_manifest'], entry['prepared']]
                    self.cards[entry['id']] = dev_card(entry)
                    entries.append(entry)
        controls = []
        proof = self.file('admission_results', {'independent_dev': True,
            'expected': {key: value[3] for key, value in family.CONTROL_SPECS.items()}}, 'admission_invalidity_proof')
        self.files[proof]['published_relative_path'] = 'admission/results.json'
        for record_id, (checker, names, _, _) in family.CONTROL_SPECS.items():
            parameters = ({'asset_id': 'broken'} if checker == 'inspect_step'
                          else {'curve_tolerance_mm': .001} if checker == 'planar_geometry'
                          else {'criterion': dev_tool_criterion()} if checker == 'tool_access' else {})
            control = dict(id=record_id, profile='c-s1', checker=checker, parameters=parameters,
                           inputs={name: self.file(record_id + '_' + name, {'independent_dev': True},
                                                   'admission_control') for name in names},
                           invalidity_proof=proof)
            for name, file_id in control['inputs'].items():
                self.files[file_id]['published_relative_path'] = 'admission/' + record_id + '/' + name
            controls.append(control)
        rows = [record['sha256'] + '  ' + str(record['bytes']) + '  ' + record['published_relative_path']
                for record in self.files.values() if record['origin'] == 'published_cohort']
        public = self.file('public', ('## SHA-256\n\n```\n' + '\n'.join(rows) + '\n```\n').encode(),
                           'family_public_commitment')
        self.value = dict(schema='cad-harness.live-registration.v1',
                          execution_schema='cad-harness.family-execution-registration.v1',
                          phase='families', trial_id='dev-family-trial', cycle_id='dev-cycle',
                          source_root=str(root), cohort=dict(schema='cad-harness.family-roster.v1',
                              **{key: self.files[roster][key] for key in ('path', 'sha256', 'bytes')}),
                          files=self.files, public_commitment=public, rubric=rubric,
                          entries=entries, controls=controls,
                          order=[control['id'] for control in controls] + [entry['id'] for entry in entries])

    def file(self, file_id, value, role):
        path = self.root / (file_id + ('.bin' if isinstance(value, bytes) else '.json'))
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            ledger.write_json(path, value)
        operational = role in family.OPERATIONAL_ROLES
        self.files[file_id] = dict(path=path.name, sha256=ledger.file_sha(path), bytes=path.stat().st_size,
                                  role=role, origin='operational' if operational else 'published_cohort')
        if not operational:
            self.files[file_id]['published_relative_path'] = path.name
        return file_id

    def path(self, file_id):
        record = self.files[file_id]
        path = self.root / record['path']
        if ledger.file_sha(path) != record['sha256'] or path.stat().st_size != record['bytes']:
            raise ValueError('dev_fixture_changed')
        return path


def good_generation(entry, card):
    checks = []
    for criterion in card['criteria']:
        metric = criterion['metric']
        evidence, measured = {}, None
        if metric == 'min_radius':
            evidence = dict(source='actual_native_section_line_arc_geometry')
            measured = dict(lower_mm=.3, upper_mm=.31)
        elif metric == 'tool_access':
            evidence = dict(claim='actual_output_planar_disk_center_only')
            measured = dict(status='PASS', uncovered_upper_mm2=0)
        elif metric == 'g2_continuity':
            evidence = dict(coverage='all_registered_grid_face_boundaries_and_actual_native_knot_seams')
        elif metric == 'surface_deviation':
            evidence = dict(coverage='full_bidirectional_trimmed_regions')
            measured = dict(lower_mm=0, upper_mm=.004)
        checks.append(dict(id=criterion['id'], metric=metric, status='PASS', evidence=evidence, measured=measured))
    judged = dict(status='PASS', checks=checks)
    native = dict(status='PASS', geometry_ok=True, editability_ok=True,
                  native_evidence=dict(fcstd_reopened=True, step_reopened=True, editable=True),
                  judges={'fcstd': copy.deepcopy(judged), 'step': copy.deepcopy(judged)})
    return dict(status='PASS', evidence_mode='unit_mock', first_handover={'status': 'SUBMITTED'},
                artifact_bundle='unit-mock-artifacts', native_cad_intervals=[[2, 3]],
                artifact_verdict=dict(status='PASS', result=native), images=[])


class FakeSession:
    """Enforce independent pools and once-per-record calls, not canned scoring."""
    mode = 'unit_mock'

    def __init__(self, fixture, out):
        self.fixture, self.registration, self.out = fixture, fixture.value, out
        self.generation_calls, self.judge_calls, self.native_calls, self.events = [], [], [], []
        self.generation_overrides, self.judge_overrides, self.control_overrides = {}, {}, {}
        self.charged = dict.fromkeys(family.RESERVATIONS, 0)
        self.check_count, self.stop_at_check = 0, None
        self.native_process = self.native

    def __enter__(self):
        self.out.mkdir()
        self.journal = ledger.Journal(self.out / 'ledger.jsonl', 'dev', 'families')
        return self

    def __exit__(self, *args):
        self.journal.close()

    def path(self, file_id):
        return self.fixture.path(file_id)

    def check(self):
        self.check_count += 1
        if self.check_count == self.stop_at_check:
            raise Stop('quota_stop')

    def event(self, kind, **fields):
        self.events.append(dict(event=kind, **fields))
        self.journal.append(kind, **fields)

    def execute_plan(self, entry, out, *, pool, model, thinking, max_calls, active_limit):
        if entry['id'] in [row['id'] for row in self.generation_calls]:
            raise AssertionError('favorable_generation_rerun')
        if self.charged[pool] + 3 > family.RESERVATIONS[pool]:
            raise Stop('pool_budget_exhausted:' + pool)
        self.charged[pool] += 3
        self.generation_calls.append(dict(id=entry['id'], pool=pool, model=model,
                                          thinking=thinking, max_calls=max_calls, active_limit=active_limit))
        value = self.generation_overrides.get(entry['id'])
        if isinstance(value, BaseException):
            raise value
        return copy.deepcopy(value if value is not None else good_generation(entry, self.fixture.cards[entry['id']]))

    def judge(self, record_id, request, deterministic, rubric, *, pool, images):
        if record_id in [row['id'] for row in self.judge_calls]:
            raise AssertionError('favorable_judge_rerun')
        if self.charged[pool] + 1 > family.RESERVATIONS[pool]:
            raise Stop('pool_budget_exhausted:' + pool)
        self.charged[pool] += 1
        self.judge_calls.append(dict(id=record_id, pool=pool, request=request, images=images))
        value = self.judge_overrides.get(record_id, {'status': 'PASS'})
        if isinstance(value, BaseException):
            raise value
        return copy.deepcopy(value)

    def native(self, argv, captures, *, cwd, timeout):
        job = ledger.read_json(argv[argv.index('--job') + 1])
        if job['operation'] != 'admission-control':
            raise AssertionError('unexpected_native_operation')
        control = job['control']
        self.native_calls.append(control)
        result = dict(status='PASS', profile='c-s1', evidence_mode='unit_mock',
                      control_id=control['id'], checker=control['checker'], admitted=False, refused=True,
                      observed_reason=family.CONTROL_SPECS[control['id']][3],
                      model_calls=0, generated_deliverable=False)
        result.update(self.control_overrides.get(control['id'], {}))
        ledger.write_json(Path(job['out']) / 'result.json', result)
        captures['stdout'].feed(b'independent DEV injected admission evidence\n')
        captures['stderr'].feed(b'')
        return 0 if result['status'] == 'PASS' else 1

    def summary(self):
        return dict(pools=dict(self.charged), evidence_mode=self.mode)


class FamilyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cad-family-independent-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        source = self.root / 'source'
        source.mkdir()
        self.fixture = DevRegistration(source)
        self.session = FakeSession(self.fixture, self.root / 'run')
        for name in ('subprocess.run', 'subprocess.Popen'):
            p = patch(name, side_effect=AssertionError('provider/native launch forbidden'))
            p.start()
            self.addCleanup(p.stop)

    def run_family(self):
        with patch.object(family.trials, 'TrialSession', return_value=self.session) as constructor:
            result = family.run('dev-manifest', 'dev-authorization', self.session.out,
                                process=lambda *a, **k: (_ for _ in ()).throw(AssertionError('model forbidden')),
                                native_process=self.session.native, verifier=lambda *a: None)
        self.assertEqual(constructor.call_args.kwargs['phase'], 'families')
        return result

    def test_registration_binds_opaque_roster_without_parsing_it(self):
        family.validate_registration(self.fixture.value)
        family.validate_bound_inputs(self.fixture.value, self.fixture.path)
        self.assertFalse(self.fixture.path('roster').read_bytes().startswith(b'{'))
        bad = copy.deepcopy(self.fixture.value)
        bad['cohort']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'opaque_roster_binding'):
            family.validate_registration(bad)

    def test_publication_parser_rejects_duplicate_unsafe_and_ambiguous_rows(self):
        row = 'a' * 64 + '  7  generative/C1-01/request.txt'
        valid = '## SHA-256\n\n```\n' + row + '\n```\n'
        self.assertEqual(family.published_commitments(valid),
                         {'generative/C1-01/request.txt': {'sha256': 'a' * 64, 'bytes': 7}})
        for text in (valid.replace(row, row + '\n' + row),
                     valid.replace('generative/C1-01/request.txt', '../request.txt'),
                     valid.replace('  7  ', '  not-bytes  '),
                     valid + '```\n' + row + '\n```\n',
                     valid.replace('```\n', '', 1)):
            with self.subTest(text=text), self.assertRaises(ValueError):
                family.published_commitments(text)

    def test_original_source_membership_cannot_be_reclassified_or_substituted(self):
        family.validate_published_files(self.fixture.value, self.fixture.path)
        request_id = self.fixture.value['entries'][0]['request']
        for mutation in ('hash', 'bytes', 'unpublished', 'operational_source'):
            bad = copy.deepcopy(self.fixture.value)
            record = bad['files'][request_id]
            if mutation == 'hash':
                record['sha256'] = '0' * 64
            elif mutation == 'bytes':
                record['bytes'] += 1
            elif mutation == 'unpublished':
                record['published_relative_path'] = 'unpublished/request.txt'
            else:
                record['origin'] = 'operational'
                del record['published_relative_path']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                family.validate_published_files(bad, self.fixture.path)
        aliased = copy.deepcopy(self.fixture.value)
        card_id = aliased['entries'][0]['card']
        aliased['files']['cloned_card'] = dict(aliased['files'][card_id], path='cloned-card.json', role='source_asset')
        with self.assertRaisesRegex(ValueError, 'original_alias_refused'):
            family.validate_published_files(aliased, self.fixture.path)
        record = dict(published_relative_path='retired-c2-cycle2/generative/C2-01/request.txt',
                      sha256='a' * 64, bytes=1)
        with self.assertRaisesRegex(ValueError, 'retired_cohort_refused'):
            family.validate_published_record(record, {record['published_relative_path']: {'sha256': 'a' * 64, 'bytes': 1}})

    def test_active_c2_production_recipe_is_required_without_inspecting_geometry(self):
        active = c2_recipe.load()
        contour = dict(schema='cad-harness.contour.v4c', recipe=active['recipe'],
                       recipe_sha256=active['canonical_sha256'])
        prepared = {'assets': {'logo': contour}}
        family.validate_active_c2_prepared(prepared)
        for mutation in ('missing', 'raw_file_digest', 'forged_hash', 'inactive_recipe', 'mixed_recipes'):
            bad = copy.deepcopy(prepared)
            if mutation == 'missing':
                bad['assets'] = {}
            elif mutation == 'raw_file_digest':
                bad['assets']['logo']['recipe_sha256'] = active['sha256']
            else:
                changed = bad['assets']['logo']
                changed['recipe']['scale']['canonical_height_mm'] += 1
                if mutation in ('inactive_recipe', 'mixed_recipes'):
                    changed['recipe_sha256'] = inputs.canonical_sha(changed['recipe'])
                if mutation == 'mixed_recipes':
                    bad['assets']['active'] = copy.deepcopy(contour)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'active_c2_recipe_required'):
                family.validate_active_c2_prepared(bad)
        bad = copy.deepcopy(self.fixture.value)
        bad['entries'][0]['card'] = bad['entries'][1]['card']
        with self.assertRaisesRegex(ValueError, 'family_entry_identity'):
            family.validate_bound_inputs(bad, self.fixture.path)

    def test_exact_enrollment_and_complete_once_only_order(self):
        for change in ('missing', 'duplicate', 'wrong_identity', 'missing_control', 'repeated_order'):
            bad = copy.deepcopy(self.fixture.value)
            if change == 'missing':
                bad['entries'].pop()
            elif change == 'duplicate':
                bad['entries'][-1] = copy.deepcopy(bad['entries'][0])
            elif change == 'wrong_identity':
                bad['entries'][0]['id'] = 'C1-11'
            elif change == 'missing_control':
                bad['controls'][0] = copy.deepcopy(bad['controls'][1])
            else:
                bad['order'][-1] = bad['order'][0]
            with self.subTest(change=change), self.assertRaises(ValueError):
                family.validate_registration(bad)

    def test_signed_strata_and_c2_identity_assignments_cannot_change(self):
        bad = copy.deepcopy(self.fixture.value)
        bad['entries'][0]['stratum'] = 'stepped_oriented'
        with self.assertRaisesRegex(ValueError, 'signed_stratum_counts'):
            family.validate_registration(bad)
        bad = copy.deepcopy(self.fixture.value)
        c2 = [entry for entry in bad['entries'] if entry['family'] == 'C2']
        c2[0]['stratum'], c2[3]['stratum'] = c2[3]['stratum'], c2[0]['stratum']
        with self.assertRaisesRegex(ValueError, 'published_stratum_identity'):
            family.validate_registration(bad)

    def test_generator_allowlist_rejects_checker_or_roster_leakage(self):
        for file_id in ('roster', self.fixture.value['entries'][0]['card'],
                        self.fixture.value['entries'][-1]['context'], self.fixture.value['rubric']):
            bad = copy.deepcopy(self.fixture.value)
            bad['entries'][0]['model_inputs'].append(file_id)
            with self.subTest(file_id=file_id), self.assertRaisesRegex(ValueError, 'private_checker_model_input'):
                family.validate_registration(bad)

    def test_all_signed_gates_and_separate_pools_pass_on_complete_mock_evidence(self):
        result = self.run_family()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual((result['enrolled'], result['generative_denominator'], result['control_denominator']), (47, 43, 4))
        self.assertEqual(len(self.session.generation_calls), 43)
        self.assertEqual(len(self.session.judge_calls), 43)
        self.assertEqual(len(self.session.native_calls), 4)
        self.assertEqual(result['accounting']['pools'], family.RESERVATIONS)
        for call in self.session.generation_calls:
            self.assertEqual((call['model'], call['thinking'], call['max_calls'], call['active_limit']),
                             ('openai-codex/gpt-6.1-sol', 'xhigh', 3, 1200))
            self.assertEqual(call['pool'], call['id'].split('-')[0] + ':generation')
        for call in self.session.judge_calls:
            self.assertEqual(call['pool'], call['id'].split('-')[0] + ':judge')
        self.assertEqual(result['families']['C2']['tool_verified'], 10)

    def test_failures_refusals_and_unverified_remain_in_registered_denominators(self):
        for record_id, status in (('C1-01', 'FAIL'), ('C1-02', 'REFUSED'), ('C1-05', 'UNVERIFIED')):
            self.session.generation_overrides[record_id] = dict(status=status)
        result = self.run_family()
        c1 = result['families']['C1']
        self.assertEqual((c1['denominator'], c1['successes'], c1['status']), (10, 7, 'FAIL'))
        self.assertEqual(c1['strata']['prismatic']['denominator'], 4)
        self.assertEqual(c1['statuses']['REFUSED'], 1)
        self.assertEqual(len(self.session.judge_calls), 40)
        self.assertEqual(result['families']['C2']['status'], 'PASS')

    def test_aggregate_success_cannot_override_a_failed_stratum_or_pool_families(self):
        self.session.generation_overrides['C1-01'] = {'status': 'FAIL'}
        self.session.generation_overrides['C1-02'] = {'status': 'FAIL'}
        result = self.run_family()
        c1 = result['families']['C1']
        self.assertEqual(c1['successes'], 8)
        self.assertEqual(c1['strata']['prismatic']['successes'], 2)
        self.assertEqual(c1['status'], 'FAIL')
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['families']['C5']['status'], 'PASS')

    def test_every_signed_family_stratum_minimum_is_independent_of_aggregate(self):
        cases = [('C1', 'prismatic', 2, 8), ('C2', 'convex', 2, 8),
                 ('C3', 'dense', 1, 7), ('C4', 'finite_planar_replacement', 2, 6),
                 ('C5', 'two_patch', 2, 5)]
        for name, stratum, failure_count, aggregate in cases:
            records = {entry['id']: dict(id=entry['id'], stratum=entry.get('stratum'),
                status='PASS', full_pass=True, tool_verified=True, correct_refusal=True, false_acceptance=False)
                for entry in self.fixture.value['entries'] + self.fixture.value['controls']}
            failing = [entry['id'] for entry in self.fixture.value['entries']
                       if entry['family'] == name and entry['stratum'] == stratum][:failure_count]
            for record_id in failing:
                records[record_id].update(status='FAIL', full_pass=False)
            result = family.summarize(self.fixture.value, records)
            with self.subTest(family=name):
                self.assertEqual(result['families'][name]['minimum'], aggregate)
                self.assertEqual(result['families'][name]['successes'], aggregate)
                self.assertFalse(result['families'][name]['strata'][stratum]['passed'])
                self.assertEqual(result['families'][name]['status'], 'FAIL')
                self.assertEqual(result['status'], 'FAIL')

    def test_c2_ten_of_ten_actual_tool_gate_is_mandatory(self):
        entry = next(entry for entry in self.fixture.value['entries'] if entry['id'] == 'C2-01')
        generated = good_generation(entry, self.fixture.cards[entry['id']])
        for representation in generated['artifact_verdict']['result']['judges'].values():
            radius = next(row for row in representation['checks'] if row['metric'] == 'min_radius')
            radius['evidence']['source'] = 'prepared_contour_proxy'
        self.session.generation_overrides[entry['id']] = generated
        result = self.run_family()
        c2 = result['families']['C2']
        self.assertEqual((c2['successes'], c2['tool_verified'], c2['tool_denominator'], c2['status']), (9, 9, 10, 'FAIL'))
        self.assertNotIn(entry['id'], [call['id'] for call in self.session.judge_calls])

    def test_c5_requires_full_g2_and_global_deviation_at_most_point005(self):
        entry = next(entry for entry in self.fixture.value['entries'] if entry['family'] == 'C5')
        for mutation in ('sampled', 'over_limit', 'missing_g2', 'missing_step'):
            generated = good_generation(entry, self.fixture.cards[entry['id']])
            result = generated['artifact_verdict']['result']
            if mutation == 'missing_step':
                del result['judges']['step']
            else:
                checks = result['judges']['fcstd']['checks']
                if mutation == 'missing_g2':
                    checks[:] = [row for row in checks if row['metric'] != 'g2_continuity']
                else:
                    deviation = next(row for row in checks if row['metric'] == 'surface_deviation')
                    if mutation == 'sampled':
                        deviation['evidence']['coverage'] = 'sampled_points'
                    else:
                        deviation['measured']['upper_mm'] = .005001
            with self.subTest(mutation=mutation):
                evidence = family._artifact_evidence(entry, generated, self.fixture.cards[entry['id']])
                self.assertNotEqual(evidence['status'], 'PASS')
                self.assertFalse(evidence['surface_verified'])

    def test_missing_or_weakened_card_gates_are_rejected_before_generation(self):
        for name in ('C2', 'C5'):
            entry = next(entry for entry in self.fixture.value['entries'] if entry['family'] == name)
            card = copy.deepcopy(self.fixture.cards[entry['id']])
            card['criteria'].pop()
            with self.subTest(family=name), self.assertRaises(ValueError):
                family._card_requirements(entry, card)
        entry = next(entry for entry in self.fixture.value['entries'] if entry['family'] == 'C5')
        card = copy.deepcopy(self.fixture.cards[entry['id']])
        card['criteria'][-1]['maximum_mm'] = .006
        with self.assertRaisesRegex(ValueError, 'signed_deviation_limit'):
            family._card_requirements(entry, card)

    def test_malformed_judge_and_critical_pass_are_not_favorably_rescored(self):
        self.session.judge_overrides['C1-01'] = {'status': 'unrecognized'}
        self.session.judge_overrides['C1-02'] = {'status': 'PASS', 'critical_violation': True}
        result = self.run_family()
        records = {row['id']: row for row in result['records']}
        self.assertEqual(records['C1-01']['status'], 'UNVERIFIED')
        self.assertFalse(records['C1-01']['full_pass'])
        self.assertEqual(records['C1-02']['status'], 'FAIL')
        self.assertEqual(result['families']['C1']['false_acceptances'], 1)
        self.assertEqual(result['families']['C1']['status'], 'FAIL')
        self.assertEqual(len(self.session.judge_calls), 43)
        self.assertEqual(len({row['id'] for row in self.session.judge_calls}), 43)

    def test_quota_stop_retains_unstarted_records_and_append_only_evidence(self):
        self.session.stop_at_check = 7
        result = self.run_family()
        self.assertEqual(result['stop_reason'], 'quota_stop')
        self.assertEqual(len(result['records']), 47)
        records = {row['id']: row for row in result['records']}
        self.assertEqual(records['C1-03']['status'], 'UNSTARTED')
        self.assertEqual(records['C1-03']['unstarted_reason'], 'quota_stop')
        self.assertEqual(result['families']['C1']['denominator'], 10)
        self.assertEqual(result['families']['C5']['denominator'], 7)
        rows = list(ledger.rows(self.session.out / 'ledger.jsonl'))
        self.assertEqual([row['event_id'] for row in rows], list(range(1, len(rows) + 1)))
        self.assertEqual(rows[-1]['event'], 'family_finished')
        self.assertTrue((self.session.out / 'family-enrollment.json').is_file())
        self.assertTrue((self.session.out / 'family-result.json').is_file())

    def test_budget_exhaustion_never_borrows_from_another_family_or_judge_pool(self):
        self.session.charged['C1:generation'] = 30
        result = self.run_family()
        self.assertEqual(result['stop_reason'], 'pool_budget_exhausted:C1:generation')
        self.assertEqual(self.session.charged['C1:judge'], 0)
        self.assertEqual(self.session.charged['C2:generation'], 0)
        self.assertEqual(self.session.charged['C5:generation'], 0)
        self.assertEqual(len(self.session.generation_calls), 0)
        self.assertEqual(result['families']['C1']['denominator'], 10)
        self.assertEqual(family.reservation(self.fixture.value), {
            'C1:generation': 30, 'C1:judge': 10, 'C2:generation': 30, 'C2:judge': 10,
            'C3:generation': 24, 'C3:judge': 8, 'C4:generation': 24, 'C4:judge': 8,
            'C5:generation': 21, 'C5:judge': 7})

    def test_controls_have_no_generation_judgment_or_generated_deliverable(self):
        self.session.control_overrides['AC-tool-infeasible'] = dict(status='UNVERIFIED', admitted=None, refused=False)
        self.session.control_overrides['AC-open-contour'] = dict(generated_deliverable=True)
        result = self.run_family()
        self.assertEqual(result['controls']['correct_refusals'], 2)
        self.assertEqual(result['controls']['denominator'], 4)
        self.assertEqual(result['controls']['status'], 'FAIL')
        self.assertEqual(len(self.session.native_calls), 4)
        self.assertFalse(any(row['id'].startswith('AC-') for row in self.session.generation_calls))
        self.assertFalse(any(row['id'].startswith('AC-') for row in self.session.judge_calls))
        for control in self.session.native_calls:
            self.assertTrue(all(Path(path).is_absolute() for path in control['inputs'].values()))

    def test_unexpected_worker_errors_retain_actual_status_and_are_not_retried(self):
        self.session.generation_overrides['C3-01'] = RuntimeError('native fixture worker failure')
        result = self.run_family()
        record = next(row for row in result['records'] if row['id'] == 'C3-01')
        self.assertEqual((record['status'], record['error_type']), ('ERROR', 'RuntimeError'))
        self.assertEqual(result['families']['C3']['denominator'], 8)
        self.assertEqual(len(self.session.generation_calls), 43)
        self.assertEqual(len(self.session.judge_calls), 42)

    def test_native_admission_runs_real_corrupt_step_checker_before_native_import(self):
        step = self.root / 'independent-corrupt.step'
        step.write_bytes(b'ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n')
        manifest = self.root / 'independent-inputs.json'
        ledger.write_json(manifest, dict(schema='cad-harness.inputs.v4c', profile='c-s1',
            evidence_mode='independent_dev', assets={'broken': dict(kind='step', role='checker',
                path=step.name, sha256=ledger.file_sha(step), bytes=step.stat().st_size)}))
        recipe = self.root / 'independent-recipe.json'
        ledger.write_json(recipe, dict(schema='cad-harness.step-recipe.v4c', profile='c-s1',
            source_axes=['X', 'Y', 'Z'], source_units='mm', signature_precision_mm=1e-6))
        result = family.native_admission(dict(id='AC-corrupt-step', checker='inspect_step',
            parameters={'asset_id': 'broken'}, inputs={'manifest': str(manifest), 'recipe': str(recipe)}), self.root)
        self.assertEqual((result['status'], result['refused'], result['observed_reason']),
                         ('PASS', True, 'ambiguous_step_length_unit'))
        self.assertEqual((result['model_calls'], result['generated_deliverable']), (0, False))

    def test_native_admission_rejects_unrelated_errors_as_unverified_not_correct_refusal(self):
        contour = self.root / 'independent-contour.json'
        ledger.write_json(contour, dict(units='mm', loops=[]))
        control = dict(id='AC-open-contour', checker='planar_geometry',
                       parameters={'curve_tolerance_mm': .001}, inputs={'contour': str(contour)})
        with patch.object(judges, 'planar_geometry', side_effect=ValueError('unrelated_schema_error')) as checker:
            result = family.native_admission(control, self.root)
        checker.assert_called_once()
        self.assertEqual((result['status'], result['refused']), ('UNVERIFIED', False))
        with patch.object(judges, 'planar_geometry', side_effect=ValueError('judge_open_loop')):
            result = family.native_admission(control, self.root)
        self.assertEqual((result['status'], result['refused']), ('PASS', True))

    def test_native_tool_control_requires_proven_fail_not_unverified_or_success(self):
        contour = self.root / 'tool-contour.json'
        ledger.write_json(contour, {'independent_dev': True})
        control = dict(id='AC-tool-infeasible', checker='tool_access',
                       parameters={'criterion': dev_tool_criterion()}, inputs={'contour': str(contour)})
        for measured, expected in (('FAIL', 'PASS'), ('UNVERIFIED', 'UNVERIFIED'), ('PASS', 'FAIL')):
            with self.subTest(measured=measured), patch.object(judges, 'tool_access', return_value={'status': measured}) as checker:
                result = family.native_admission(control, self.root)
            checker.assert_called_once()
            self.assertEqual(result['status'], expected)
            self.assertEqual(result['refused'], measured == 'FAIL')

    def test_native_glyph_control_uses_context_admission_not_model_refusal(self):
        paths = {}
        for name in ('manifest', 'prepared', 'card', 'context'):
            path = self.root / ('glyph-' + name + '.json')
            ledger.write_json(path, {'independent_dev': True})
            paths[name] = str(path)
        with patch.object(artifact_judges, 'validate_context', side_effect=ValueError('glyph_coverage')) as checker:
            result = family.native_admission(dict(id='AC-unavailable-glyph', checker='validate_context',
                parameters={}, inputs=paths), self.root)
        checker.assert_called_once()
        self.assertEqual((result['status'], result['observed_reason'], result['model_calls']), ('PASS', 'glyph_coverage', 0))


class NativeWorkerBoundaryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cad-native-boundary-independent-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ('subprocess.run', 'subprocess.Popen'):
            p = patch(name, side_effect=AssertionError('native/model launch forbidden'))
            p.start()
            self.addCleanup(p.stop)

    def record(self, path):
        return dict(path=str(path), sha256=ledger.file_sha(path), bytes=path.stat().st_size)

    def authority_fixture(self, mode='unit_mock'):
        paths, source_files = {}, {}
        for key in ('manifest', 'prepared', 'card', 'context'):
            path = self.root / (key + '.json')
            ledger.write_json(path, {'evidence_mode': 'custodian'} if key == 'manifest'
                              else {'independent_dev': key})
            paths[key], source_files[key] = path, self.record(path)
        execution = self.root / 'execution.json'
        ledger.write_json(execution, {'evidence_mode': mode})
        claim = self.root / 'claim.json'
        ledger.write_json(claim, dict(manifest_sha256=ledger.file_sha(execution), run_dir=str(self.root)))
        entry = dict(id='DEV-01', profile='c-s1', input_manifest='manifest',
                     prepared='prepared', card='card', context='context')
        frozen = dict(evidence_mode=mode, registration_data={'entries': [entry]}, source_files=source_files)
        job = dict(profile='c-s1', execution_manifest=self.record(execution))
        return job, paths, frozen, {'claim_file': self.record(claim)}

    def test_native_custodian_admission_binds_all_four_sources_and_existing_claim(self):
        job, paths, frozen, claim = self.authority_fixture()
        with patch.object(family.trials, 'verify_trial', return_value=(frozen, None)) as verify:
            with patch.object(family.trials, 'verify_execution_claim', return_value=claim) as claimed:
                result = artifacts.authorized_native_inputs(job, paths, {'evidence_mode': 'custodian'})
        verify.assert_called_once_with(Path(job['execution_manifest']['path']),
                                       verifier=ledger.read_json, allow_mock=True)
        claimed.assert_called_once_with(Path(job['execution_manifest']['path']), frozen)
        self.assertEqual(result['registered_entries'], ['DEV-01'])
        self.assertEqual(result['claim_file'], claim['claim_file'])
        self.assertFalse(result['model_authorization'])

    def test_live_native_admission_does_not_select_mock_integrated_verifier(self):
        job, paths, frozen, claim = self.authority_fixture(mode='live')
        with patch.object(family.trials, 'verify_trial', return_value=(frozen, None)) as verify:
            with patch.object(family.trials, 'verify_execution_claim', return_value=claim):
                result = artifacts.authorized_native_inputs(job, paths, {'evidence_mode': 'custodian'})
        verify.assert_called_once_with(Path(job['execution_manifest']['path']))
        self.assertEqual(result['frozen_evidence_mode'], 'live')

    def test_native_admission_rejects_unclaimed_or_cross_entry_source_tuples(self):
        job, paths, frozen, claim = self.authority_fixture()
        with patch.object(family.trials, 'verify_trial', return_value=(frozen, None)):
            with patch.object(family.trials, 'verify_execution_claim', side_effect=Stop('missing_execution_claim')):
                with self.assertRaisesRegex(Stop, 'missing_execution_claim'):
                    artifacts.authorized_native_inputs(job, paths, {'evidence_mode': 'custodian'})
        original = frozen['registration_data']['entries'][0]
        frozen['source_files']['wrong_context'] = dict(frozen['source_files']['context'], sha256='0' * 64)
        frozen['source_files']['wrong_manifest'] = dict(frozen['source_files']['manifest'], sha256='0' * 64)
        frozen['registration_data']['entries'] = [
            dict(original, id='DEV-left', context='wrong_context'),
            dict(original, id='DEV-right', input_manifest='wrong_manifest')]
        with patch.object(family.trials, 'verify_trial', return_value=(frozen, None)):
            with patch.object(family.trials, 'verify_execution_claim', return_value=claim):
                with self.assertRaisesRegex(ValueError, 'registered_input_tuple_required'):
                    artifacts.authorized_native_inputs(job, paths, {'evidence_mode': 'custodian'})

    def test_native_admission_rejects_changed_execution_record_before_verification(self):
        job, paths, _, _ = self.authority_fixture()
        job['execution_manifest']['sha256'] = '0' * 64
        with patch.object(family.trials, 'verify_trial') as verify:
            with self.assertRaisesRegex(ValueError, 'artifact_dependency_changed'):
                artifacts.authorized_native_inputs(job, paths, {'evidence_mode': 'custodian'})
        verify.assert_not_called()

    def test_unscoped_native_checker_remains_dev_only(self):
        with self.assertRaisesRegex(ValueError, 'independent_dev_only'):
            artifacts.authorized_native_inputs({}, {}, {'evidence_mode': 'custodian'})
        self.assertIsNone(artifacts.authorized_native_inputs({}, {}, {'evidence_mode': 'independent_dev'}))
        with self.assertRaisesRegex(ValueError, 'authorized_execution_scope_required'):
            artifacts.execution_manifest_record({'manifest_path': 'not-a-session'})

    def test_execution_record_requires_an_actual_session_or_plan_scope(self):
        manifest = self.root / 'manifest.json'
        ledger.write_json(manifest, {'independent_dev': True})
        session = object.__new__(family.trials.TrialSession)
        session.manifest_path = manifest
        plan = object.__new__(family.trials.PlanExecution)
        plan.session = session
        self.assertEqual(artifacts.execution_manifest_record(session), self.record(manifest))
        self.assertEqual(artifacts.execution_manifest_record(plan), self.record(manifest))
        plan.session = object()
        with self.assertRaisesRegex(ValueError, 'authorized_session_required'):
            artifacts.execution_manifest_record(plan)

    def test_facade_carries_bound_execution_record_and_preserves_mock_summary_mode(self):
        job, paths, _, _ = self.authority_fixture()
        scope = object.__new__(family.trials.TrialSession)
        scope.manifest_path = Path(job['execution_manifest']['path'])
        scope.mode = 'unit_mock'
        bundle = self.root / 'bundle.json'
        ledger.write_json(bundle, {'independent_dev': True})
        with patch.object(artifacts._module('cad_verify_v4_s1'), '_manifest_inputs',
                          return_value=(paths['manifest'], {}, None)):
            with patch.object(artifact_judges, 'validate_context'), patch.object(artifacts, 'load_bundle'):
                with patch.object(artifacts._module('cad_verify_v4_s1'), 'native_work',
                                  return_value={'status': 'PASS', 'evidence_mode': 'unit_mock'}) as native:
                    result = artifacts.check(paths['manifest'], paths['prepared'], paths['card'], paths['context'],
                                             bundle, self.root / 'checked', execution=scope)
        self.assertEqual(native.call_args.kwargs['execution_manifest'], job['execution_manifest'])
        self.assertEqual(result['evidence_mode'], 'unit_mock')
        self.assertEqual(result['execution_manifest_sha256'], job['execution_manifest']['sha256'])
        self.assertTrue(Path(result['summary_path']).is_file())
        self.assertTrue(Path(result['ledger_path']).is_file())
        self.assertEqual(result['live_calls'], 0)
        self.assertIsNone(result['authorization'])

    def archive(self, name, nodes):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Document.xml', '<Document>' + nodes + '</Document>')
        return path

    def test_restoration_modules_come_from_actual_serialized_dependencies_only(self):
        ordinary = self.archive('ordinary.FCStd', '')
        self.assertEqual(artifacts.restoration_modules(ordinary), [])
        self.assertEqual(artifacts._guard_archive(ordinary, {}, set()), set())
        with self.assertRaisesRegex(ValueError, 'native_unused_python_dependency'):
            artifacts._guard_archive(ordinary, {'tools.cad_verify_v4_compile': self.root / 'unused.py'}, set())
        nodes = ('<Python module="tools.cad_verify_v4_compile" class="ContourProxy" value="null"/>'
                 '<Python module="tools.cad_verify_v4_s2_edit" class="DirectEditProxy" value="null"/>'
                 '<Python module="tools.cad_verify_v4_compile" class="EngravingProxy" value="null"/>')
        python = self.archive('python.FCStd', nodes)
        self.assertEqual(artifacts.restoration_modules(python),
                         ['tools.cad_verify_v4_compile', 'tools.cad_verify_v4_s2_edit'])
        with self.assertRaisesRegex(ValueError, 'native_undeclared_python_dependency'):
            artifacts._guard_archive(python, {}, set())

    def test_probe_metadata_preserves_exact_performed_scalar_vector_and_text_edits(self):
        probes = [
            dict(kind='scalar', object='ContourExtrude', property='Thickness', delta=.03),
            dict(kind='vector', object='Engraving0', property='Origin', delta_mm=[.001, 0, 0]),
            dict(kind='text', object='Engraving0', property='Text', suffix='A'),
            dict(kind='scalar', object='DirectEdit', property='ReplacementShift', delta=.001),
            dict(kind='vector_list', object='SurfaceRebuild', property='PoleOffsets',
                 index=14, delta_mm=[0, 0, .002]),
        ]
        evidence = [dict(operative=True, restored=True, artifact_probe=probe) for probe in probes]
        self.assertEqual(worker.artifact_probes(evidence), probes)
        for bad in ([], [dict(operative=False, artifact_probe=probes[0])],
                    [dict(operative=True, restored=False, artifact_probe=probes[0])],
                    [dict(operative=True)], [dict(operative=True, artifact_probe={'kind': 'unregistered'})]):
            with self.subTest(evidence=bad), self.assertRaises(ValueError):
                worker.artifact_probes(bad)


def make_native_admission_fixtures(root):
    """Author independent real controls for the parent's pinned-native smoke."""
    import Part
    root.mkdir()
    def save(name, value):
        path = root / name
        ledger.write_json(path, value)
        return str(path)
    def record(path, kind, role, **extra):
        return dict(path=path.name, kind=kind, role=role, sha256=ledger.file_sha(path),
                    bytes=path.stat().st_size, **extra)
    recipe = dict(schema='cad-harness.step-recipe.v4c', profile='c-s1',
                  source_axes=['X', 'Y', 'Z'], source_units='mm', signature_precision_mm=1e-6)
    recipe_path = save('recipe.json', recipe)
    broken = root / 'corrupt.step'
    broken.write_bytes(b'ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n')
    corrupt_manifest = save('corrupt-inputs.json', dict(schema='cad-harness.inputs.v4c', profile='c-s1',
        evidence_mode='independent_dev', assets={'broken': record(broken, 'step', 'checker')}))
    def polygon(points):
        return dict(units='mm', loops=[dict(role='outer', segments=[
            dict(kind='line', p0=a, p1=b) for a, b in zip(points, points[1:])])])
    open_contour = save('open-contour.json', polygon([[0, 0], [2, 0], [2, 2], [0, 2]]))
    narrow = save('fixed-narrow-contour.json', polygon([[0, 0], [4, 0], [4, .1], [0, .1], [0, 0]]))
    tool = dev_tool_criterion()
    baseline = root / 'baseline.step'
    Part.makeBox(12, 8, 3).exportStep(str(baseline))
    font = root / 'DejaVuSansMono.ttf'
    font.write_bytes((family.ROOT / 'skills/cad-harness-v4/fonts/DejaVuSansMono.ttf').read_bytes())
    license_path = root / 'LICENSE_DEJAVU.txt'
    license_path.write_bytes((family.ROOT / 'skills/cad-harness-v4/fonts/LICENSE_DEJAVU').read_bytes())
    glyph_manifest = save('glyph-inputs.json', dict(schema='cad-harness.inputs.v4c', profile='c-s1',
        evidence_mode='independent_dev', assets={
            'baseline': record(baseline, 'step', 'checker'),
            'font': record(font, 'font', 'font', glyphs='O', license_asset_id='license'),
            'license': record(license_path, 'license', 'license')}))
    prepared = str(root / 'glyph-prepared.json')
    inputs.inspect_step(glyph_manifest, 'baseline', recipe, prepared)
    card = save('glyph-card.json', dict(schema='cad-harness.judge-card.v4c', profile='c-s1',
        source='independent_dev', linear_tolerance_mm=.00001,
        criteria=[dict(id='glyph', metric='engraving', index=0,
                       minimum_removed_mm3=1, depth_tolerance_mm=.01)]))
    context = save('glyph-context.json', dict(schema='cad-harness.artifact-context.v4', profile='c-s1',
        family='C3', manifest_sha256=ledger.file_sha(glyph_manifest), prepared_sha256=ledger.file_sha(prepared),
        card_sha256=ledger.file_sha(card), reference=None, contour=None,
        engravings=[dict(font_id='font', text='Q', height_mm=5, depth_mm=.6, origin_mm=[2, 2, 3],
                         rotation_axis=[0, 0, 1], rotation_deg=0, baseline_asset_id='baseline')]))
    return [
        dict(id='AC-corrupt-step', checker='inspect_step', parameters={'asset_id': 'broken'},
             inputs={'manifest': corrupt_manifest, 'recipe': recipe_path}),
        dict(id='AC-open-contour', checker='planar_geometry', parameters={'curve_tolerance_mm': .001},
             inputs={'contour': open_contour}),
        dict(id='AC-tool-infeasible', checker='tool_access', parameters={'criterion': tool},
             inputs={'contour': narrow}),
        dict(id='AC-unavailable-glyph', checker='validate_context', parameters={},
             inputs={'manifest': glyph_manifest, 'prepared': prepared, 'card': card, 'context': context}),
    ]


NATIVE = (os.environ.get('CAD_VERIFY_FAMILY_NATIVE') == '1' and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)


@unittest.skipUnless(NATIVE, 'set CAD_VERIFY_FAMILY_NATIVE=1 under pinned FreeCAD Python; no discovery launch')
class NativeAdmissionSmoke(unittest.TestCase):
    def test_trusted_admission_worker_on_four_independent_real_controls(self):
        from tools import cad_verify_v4_worker as worker
        with tempfile.TemporaryDirectory(prefix='cad-family-real-independent-') as directory:
            root = Path(directory)
            controls = make_native_admission_fixtures(root / 'fixtures')
            for control in controls:
                with self.subTest(control=control['id']):
                    out = root / control['id']
                    out.mkdir()
                    result = worker.execute(dict(operation='admission-control', control=control, out=str(out)))
                    self.assertEqual((result['status'], result['refused'], result['admitted']), ('PASS', True, False))
                    self.assertEqual(result['observed_reason'], family.CONTROL_SPECS[control['id']][3])
                    self.assertEqual((result['model_calls'], result['generated_deliverable']), (0, False))
                    self.assertTrue(result['document_closed'])


if __name__ == '__main__':
    unittest.main()
