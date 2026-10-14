"""Host integrity tests with isolated Git/source/data roots; no native/model calls.

The native process is injected and emits explicitly synthetic fixture records.
These tests exercise lock consumers, not CAD correctness or genuine native proof.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import cad_verify_v4_integrated as integrated
from tools import cad_verify_v4_freeze as freezing, cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_s1 as s1
from tools.cad_verify_guard import Stop
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n', encoding='utf-8')


class IntegratedLockHost(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.design = self.root / integrated.DESIGN
        self._source_root()
        self._git('init', '--quiet')
        self._git('config', 'core.autocrlf', 'false')
        self._git('add', '-f', '--', *integrated._sources(self.root))
        self._commit('independent initial fixture')
        self.sdk = self.base / 'sdk'
        self.identity = self._identity_fixture()
        sdk_patch = patch.object(integrated.cad_run, 'FREECAD_DIR', self.sdk)
        sdk_patch.start()
        self.addCleanup(sdk_patch.stop)
        self.recipe_paths = []
        self.recipe_by_profile = {}
        for profile in ('c-s1', 'c-s2', 'c-s3'):
            recipe = self.base / profile / 'source-recipe.json'
            save(recipe, dict(schema='cad-harness.step-recipe.v4c', profile=profile,
                              source_axes=['X', 'Y', 'Z'], source_units='mm', signature_precision_mm=.001))
            self.recipe_paths.append(recipe)
            self.recipe_by_profile[profile] = recipe
        self.recipe = self.recipe_paths[0]
        self.proof_path = self.base / 'proof' / 'proof.json'
        self.cases = []
        for family, profile in integrated.FAMILIES.items():
            self.cases.append(self._case(family, profile))
        self.proof = dict(schema='cad-harness.neutral-proof.v4', evidence_mode='independent_dev',
                          live_calls=0, cases=self.cases)
        save(self.proof_path, self.proof)
        # No provider transport can be used by these integrity operations.
        import socket
        deny_network = patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden'))
        deny_network.start()
        self.addCleanup(deny_network.stop)

    def _git(self, *args):
        result = subprocess.run(['git', '-C', str(self.root), *args], stdin=subprocess.DEVNULL,
                                capture_output=True, check=True, timeout=30)
        return result.stdout

    def _commit(self, message):
        self._git('-c', 'user.name=Independent Fixture', '-c', 'user.email=fixture@example.invalid',
                  'commit', '--quiet', '--allow-empty', '-m', message)

    def _source_root(self):
        for name in (*freezing.FIXED_FILES, integrated.DESIGN + '/PLAN-V4-ADDENDUM-C.md'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('independent source fixture\n', encoding='utf-8')
        skill = self.root / 'skills/cad-harness-v4'
        skill.mkdir(parents=True, exist_ok=True)
        from tools import eval_verify_v4
        save(self.root / 'design/cad-harness-mvp/build-schema.json', {'type': 'object', 'properties': {}})
        original = dict(schema='cad-harness.policy.v4', live_authorized_calls=0,
                        route_caps=dict(eval_verify_v4.v3.CAPS),
                        quota=dict(consult_percent=55, stop_percent=60, max_snapshot_age_s=300),
                        pending_live_decisions=[])
        save(self.design / 'policy.json', original)
        (skill / 'SKILL.md').write_text('<!-- policy:start -->\n' + json.dumps(original)
                                       + '\n<!-- policy:end -->\n', encoding='utf-8')
        for name in ('modeling.md', 'contracts.md', 'c-s1.md', 'contracts-c-s1.md',
                     'c-s2.md', 'contracts-c-s2.md', 'c-s3.md', 'contracts-c-s3.md'):
            (skill / name).write_text('independently authored fixture ' + name, encoding='utf-8')
        (skill / 'modeling.md').write_bytes((self.root / 'skills/freecad-modeling/SKILL.md').read_bytes())
        (skill / 'contracts.md').write_text(eval_verify_v4.contract_text(self.root), encoding='utf-8')
        common = dict(schema='cad-harness.capability-policy.v4c', stage='implementation',
                      live_authorized_calls=0, provider_calls_allowed=False,
                      model_calls_allowed=False, final_v4_ready=False)
        policies = {
            'c-s1': dict(common, profile='c-s1', s2_features_allowed=False,
                         families=['reference_fixture', 'contour_extrude']),
            'c-s2': dict(common, profile='c-s2', families=['step_direct_edit'], operations=['offset', 'replace'],
                         candidate_solid_count=1, original_holdout_calls=163, original_holdout_changed=False,
                         s3_features_allowed=False),
            'c-s3': dict(common, profile='c-s3', families=['surface_rebuild'], continuity='G2',
                         candidate_solid_count=1, original_holdout_calls=163, original_holdout_changed=False),
        }
        for profile, policy in policies.items():
            save(self.design / integrated.POLICIES[profile], policy)
            for name in ('input-manifest', 'prepared-inputs', 'capability-plan', 'judge-card',
                         'judge-result', 'capability-manifest', 'step-facts', 'step-recipe', 'contour'):
                prefix = s1.STAGES[profile]['schema_prefix']
                save(self.design / 'schemas' / (prefix + name + '.schema.json'), {'type': 'object'})
            path = self.design / ('dev-' + profile) / 'generate.py'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture_number = 17\n', encoding='utf-8')
        # The production recipe is public policy, not a reused case or gold.
        from tools import cad_verify_v4_c2_recipe
        for relative in (cad_verify_v4_c2_recipe.RECIPE_PATH,
                         cad_verify_v4_c2_recipe.REGISTRATION_PATH):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((integrated.ROOT / relative).read_bytes())
        source = self.design / 'dev-c2-production/generate.py'
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('independent_recipe_fixture = 19\n', encoding='utf-8')
        # Only the lock's real public schema is reused, never production evidence.
        source_schema = integrated.ROOT / integrated.DESIGN / 'schemas/integrated-lock.schema.json'
        target = self.design / 'schemas/integrated-lock.schema.json'
        target.write_bytes(source_schema.read_bytes())
        for name, profile in zip(integrated.ARCHIVES, (None, 'c-s1', 'c-s2')):
            metadata = dict(schema='cad-harness.stage-snapshot.v4c' if profile else
                            'cad-harness.original-snapshot.v4', files={})
            if profile:
                metadata['profile'] = profile
            with zipfile.ZipFile(self.design / name, 'w') as archive:
                archive.writestr('snapshot.json', json.dumps(metadata))
        for name, raw in ((integrated.FONT, b'\0\1\0\0synthetic admission font'),
                          (integrated.LICENSE, b'Independent fixture font permission\n'),
                          ('tools/independent.py', b'answer = 17\n'),
                          ('tools/__pycache__/independent.cpython-311.pyc', b'synthetic cached source fixture')):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

    def _identity_fixture(self):
        names = ('FreeCAD', 'Part', 'Sketcher', 'numpy', 'scipy', 'PIL', 'shapely',
                 'contourpy', 'fontTools', 'OCC')
        dependencies = {}
        for name in names:
            path = self.sdk / 'modules' / (name + '.py')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture_dependency = ' + repr(name) + '\n', encoding='utf-8')
            record = integrated._record(path)
            dependencies[name] = dict(version='fixture-only', path=str(path), files=[record])
        executable = self.sdk / 'bin/python.exe'
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_bytes(b'not an executable: host integrity fixture')
        sdk_cache = self.sdk / 'modules/__pycache__/Part.cpython-311.pyc'
        sdk_cache.parent.mkdir(parents=True)
        sdk_cache.write_bytes(b'synthetic SDK executable cache fixture')
        files = integrated._runtime_api().native_files(self.sdk)
        runtime = dict(owned_pid=123, gui_up=0, freecad_version=['1', '1', '4'],
                       python_executable=str(executable), python_version='3.11.0',
                       document_closed=True, files=files)
        return dict(schema='cad-harness.native-result.v4c', profile='c-s1', operation='identity',
                    status='PASS', document_closed=True, owned_pid=123, gui_up=0,
                    dependencies=dependencies, native_libraries=[], sdk_files=files,
                    occt_version='fixture-occt', runtime=runtime)

    def _facts(self, profile, manifest_path, step):
        manifest_sha, asset_sha = ledger.file_sha(manifest_path), ledger.file_sha(step)
        face = dict(id='Face1', signature='1' * 64, ambiguous=False, surface_type='Plane', area_mm2=6,
                    center_mm=[1, 1.5, 0], bounds_mm=[0, 2, 0, 3, 0, 0], normal=[0, 0, -1],
                    normal_kind='constant', normal_reason=None)
        if profile != 'c-s1':
            face['adjacent_face_ids'] = []
        if profile == 'c-s3':
            face['parameterization'] = dict(domain_uv=[0, 2, 0, 3],
                corner_points_mm=[[0, 0, 0], [2, 0, 0], [2, 3, 0], [0, 3, 0]],
                degree_u=None, degree_v=None, reason='non_spline_surface')
        facts = dict(schema='cad-harness.step-facts.v4c', profile=profile, asset_id='reference',
            source_sha256=asset_sha, units='mm', bounds_mm=[0, 2, 0, 3, 0, 4],
            topology=dict(solids=1, shells=1, faces=1, edges=4),
            frame=dict(source_axes=['X', 'Y', 'Z'], source_units='mm', import_units='mm', axis_transform='identity',
                       thickness_mm=None, thickness_reason='requires_explicit_face_pair_not_bbox'),
            faces=[face], coverage=dict(complete=True, missing_reasons=[]),
            recipe_sha256=integrated.inputs.canonical_sha(ledger.read_json(self.recipe_by_profile[profile])),
            provenance=dict(manifest_sha256_before=manifest_sha, manifest_sha256_after=manifest_sha,
                asset_sha256_before=asset_sha, asset_sha256_after=asset_sha,
                importer='FreeCAD.Part.Shape.read', freecad_version='host-admission-only'))
        if profile != 'c-s1':
            facts['signature_precision_mm'] = .001
        return facts

    def _case(self, family, profile):
        folder = self.proof_path.parent / family
        folder.mkdir(parents=True)
        step = folder / 'independent-source.step'
        step.write_bytes(b'ISO-10303-21;\nindependent host admission bytes\n')
        font = folder / 'registered.ttf'
        font.write_bytes(b'\0\1\0\0fixture registered font')
        license_path = folder / 'LICENSE.txt'
        license_path.write_text('Independent fixture permission\n', encoding='utf-8')
        assets = {}
        for name, kind, role, path in (('reference', 'step', 'reference', step),
                                      ('font', 'font', 'font', font),
                                      ('license', 'license', 'license', license_path)):
            if profile != 'c-s1' and kind != 'step':
                continue
            record = integrated._record(path)
            assets[name] = dict(kind=kind, role=role, path=path.name,
                                sha256=record['sha256'], bytes=record['bytes'])
        if profile == 'c-s1':
            assets['font'].update(license_asset_id='license', glyphs='A')
        paths = {key: folder / (key + '.json') for key in ('manifest', 'prepared', 'card', 'context')}
        save(paths['manifest'], dict(schema='cad-harness.inputs.v4c', profile=profile,
                                    evidence_mode='independent_dev', assets=assets))
        save(paths['prepared'], dict(schema='cad-harness.prepared.v4c', profile=profile,
             source_manifest_sha256=ledger.file_sha(paths['manifest']),
             assets={'reference': self._facts(profile, paths['manifest'], step)}))
        criteria = [dict(id='solid', metric='solid_valid'), dict(id='roundtrip', metric='native_roundtrip',
                    maximum_bounds_difference_mm=.001, maximum_volume_difference_mm3=.001, require_editable=True)]
        card = dict(schema='cad-harness.judge-card.v4c', profile=profile, source='independent_dev', criteria=criteria)
        if profile == 'c-s1':
            card['linear_tolerance_mm'] = .001
        else:
            card['numerical_uncertainty_mm'] = .0001
            criteria[0]['expected_solids'] = 1
        save(paths['card'], card)
        context = dict(schema='cad-harness.artifact-context.v4', profile=profile, family=family,
                       reference=None, contour=None, engravings=[],
                       **{key + '_sha256': ledger.file_sha(paths[key]) for key in ('manifest', 'prepared', 'card')})
        if family in ('C4', 'C5'):
            context['reference'] = dict(asset_id='reference', source_sha256=ledger.file_sha(step))
        if family == 'C5':
            context['reference']['grid'] = [[dict(face_id='Face1', signature='1' * 64,
                adjacent_face_ids=[], swap_uv=False, reverse_u=False, reverse_v=False)]]
        save(paths['context'], context)
        case = dict(family=family, profile=profile, input_manifest_path=str(paths['manifest']),
                    prepared_path=str(paths['prepared']), card_path=str(paths['card']), context_path=str(paths['context']))
        for arm in ('bare', 'harness'):
            arm_dir = folder / arm
            arm_dir.mkdir()
            artifacts = {}
            for key, name in (('native', 'ordinary.FCStd'), ('step', 'ordinary.step')):
                path = arm_dir / name
                path.write_bytes(('host fixture, not native evidence: ' + family + arm + key).encode('ascii'))
                artifacts[key] = integrated._record(path)
            extension = arm_dir / 'independent_feature.py'
            extension.write_text('fixture_parameter = 17\n', encoding='utf-8')
            extension.with_suffix('.pyc').write_bytes(b'synthetic adjacent extension cache')
            bundle = arm_dir / 'bundle.json'
            save(bundle, dict(schema='cad-harness.artifact-bundle.v4', profile=profile,
                evidence_mode='independent_dev', native=artifacts['native'], step=artifacts['step'],
                output_object=None, probes=[],
                extensions=[dict(module='independent_feature', **integrated._record(extension))]))
            runtime_binding = arm_dir / 'runtime-binding.json'
            save(runtime_binding, integrated._runtime_api().capture(self.root, extension_paths=[extension]))
            bindings = {key + '_sha256': ledger.file_sha(path) for key, path in paths.items()}
            bindings['bundle_sha256'] = ledger.file_sha(bundle)
            checks = [dict(id=row['id'], metric=row['metric'], status='PASS') for row in criteria]
            result = dict(schema='cad-harness.artifact-check-result.v4', profile=profile, family=family,
                status='PASS', document_closed=True, gui_up=0, owned_pid=123, live_calls=0,
                code_bindings=s1.implementation_bindings(self.root, profile=profile), bindings=bindings,
                source_paths={**{key: str(path) for key, path in paths.items()}, 'bundle': str(bundle)},
                measurements={key: dict(valid=True, solids=1, volume_mm3=24.,
                                        bounds_mm=[0., 2., 0., 3., 0., 4.]) for key in ('fcstd', 'step')},
                artifacts=artifacts, native_evidence=dict(fcstd_reopened=True, step_reopened=True, editable=True,
                    bounds_difference_mm=0., volume_difference_mm3=0.),
                runtime=copy.deepcopy(self.identity['runtime']), runtime_binding=integrated._record(runtime_binding),
                editability=dict(status='PASS', probes=[dict(
                    probe=dict(kind='scalar', object='ordinaryPad', property='Length', delta=.1),
                    old=4., new=4.1, operative=True, restored=True, invalidated_on_rejected_edit=False,
                    symmetric_difference_mm3=.6, numerical_floor_mm3=1e-10, restore_difference_mm3=0.)]),
                judges={key: dict(profile=profile, status='PASS', checks=checks) for key in ('fcstd', 'step')},
                roundtrip=[dict(id='roundtrip', status='PASS')])
            result_path = arm_dir / 'result.json'
            save(result_path, result)
            case[arm + '_result_path'] = str(result_path)
        return case

    def _process(self, argv, captures, *, cwd, timeout):
        # Explicit process injection: never execute the fake SDK binary.
        job = ledger.read_json(argv[-1])
        out = Path(job['out'])
        save(out / 'result.json', self.identity)
        captures['stdout'].feed(b'independent injected identity fixture\n')
        captures['stderr'].feed(b'')
        return 0

    def lock(self):
        out = self.base / 'lock'
        value = integrated.create(out, root=self.root, proof_path=self.proof_path,
                                  recipe_paths=self.recipe_paths, process=self._process)
        return out / 'manifest.json', value

    def proof_check(self):
        return integrated._proof(self.proof_path, root=self.root, recipes=integrated._recipes(self.recipe_paths))

    def rewrite_lock(self, manifest_path, value):
        payload = {key: item for key, item in value.items() if key != 'sha256_file'}
        save(manifest_path.parent / 'SHA256.json', payload)
        value['sha256_file'] = ledger.file_sha(manifest_path.parent / 'SHA256.json')
        save(manifest_path, value)

    def test_public_create_verify_and_transitive_plan_free_dependencies(self):
        path, value = self.lock()
        self.assertEqual(integrated.verify(path, root=self.root), value)
        self.assertEqual(set(value['profiles']), set(integrated.PROFILES))
        dependency_paths = set(value['dependencies'])
        self.assertIn(str(self.proof_path.parent / 'C3/bare/independent_feature.py'), dependency_paths)
        self.assertIn(str(self.proof_path.parent / 'C3/registered.ttf'), dependency_paths)
        self.assertIn(str(self.proof_path.parent / 'C3/LICENSE.txt'), dependency_paths)
        self.assertIn(str(self.proof_path.parent / 'C3/bare/runtime-binding.json'), dependency_paths)
        self.assertIn(str(self.proof_path.parent / 'C3/bare/independent_feature.pyc'), dependency_paths)
        self.assertIn('tools/__pycache__/independent.cpython-311.pyc', value['files'])
        self.assertEqual(value['profiles']['original']['preflight']['status'], 'offline_ready')
        self.assertIsNone(value['authorization'])
        self.assertFalse(value['final_v4_ready'])

    def test_new_head_with_identical_tree_fails(self):
        path, value = self.lock()
        self._commit('new HEAD, unchanged tree')
        self.assertEqual(integrated._head(self.root)['tree'], value['git']['tree'])
        with self.assertRaisesRegex(Stop, 'integrated_head_changed'):
            integrated.verify(path, root=self.root)

    def test_dirty_source_bytes_fail(self):
        path, _ = self.lock()
        (self.root / 'tools/independent.py').write_text('answer = 18\n', encoding='utf-8')
        with self.assertRaisesRegex(Stop, 'integrated_working_source_changed'):
            integrated.verify(path, root=self.root)

    def test_git_overlay_distinguishes_dirty_and_untracked_bytes(self):
        path = self.root / 'tools/independent.py'
        path.write_text('answer = 19\n', encoding='utf-8')
        untracked = self.root / 'tools/new_feature.py'
        untracked.write_text('new_answer = 23\n', encoding='utf-8')
        files = integrated._sources(self.root)
        result = integrated._git_files(self.root, integrated._head(self.root)['head'], files)
        self.assertEqual(result['tools/independent.py']['overlay'], 'modified')
        self.assertIsNotNone(result['tools/independent.py']['blob'])
        self.assertEqual(result['tools/new_feature.py'], dict(blob=None, mode=None, overlay='untracked'))

    def test_authorization_escalation_fails_even_with_recalculated_wrapper(self):
        path, original = self.lock()
        for key, item in (('authorization', {'trial': True}), ('final_v4_ready', True),
                          ('live_calls', 1), ('live_calls', False), ('unexpected_authority', True)):
            with self.subTest(key=key, item=item):
                value = copy.deepcopy(original)
                value[key] = item
                self.rewrite_lock(path, value)
                with self.assertRaises((ValueError, Stop)):
                    integrated.verify(path, root=self.root)

    def test_missing_profile_is_not_a_partial_lock(self):
        path, value = self.lock()
        del value['profiles']['c-s3']
        self.rewrite_lock(path, value)
        with self.assertRaises((ValueError, Stop)):
            integrated.verify(path, root=self.root)

    def test_root_anchor_cannot_be_relocated(self):
        path, value = self.lock()
        value['root'] = str(self.base)
        self.rewrite_lock(path, value)
        with self.assertRaisesRegex(Stop, 'integrated_root_or_output_anchor_mismatch'):
            integrated.verify(path, root=self.root)

    def test_missing_font_license_recipe_and_proof_files_fail_closed(self):
        path, _ = self.lock()
        names = [self.root / integrated.FONT, self.root / integrated.LICENSE, self.recipe,
                 self.proof_path.parent / 'C1/registered.ttf', self.proof_path.parent / 'C1/LICENSE.txt',
                 self.proof_path.parent / 'C2/bare/ordinary.step',
                 self.proof_path.parent / 'C5/harness/independent_feature.py']
        for target in names:
            with self.subTest(path=str(target)):
                raw = target.read_bytes()
                target.unlink()
                try:
                    with self.assertRaises((ValueError, Stop, OSError)):
                        integrated.verify(path, root=self.root)
                finally:
                    target.write_bytes(raw)

    def test_changed_recipe_runtime_and_transitive_extension_fail(self):
        path, _ = self.lock()
        targets = [self.recipe, self.sdk / 'modules/Part.py',
                   self.proof_path.parent / 'C5/bare/independent_feature.py']
        for target in targets:
            with self.subTest(path=str(target)):
                original = target.read_bytes()
                target.write_bytes(original + b'\n')
                try:
                    with self.assertRaises((ValueError, Stop)):
                        integrated.verify(path, root=self.root)
                finally:
                    target.write_bytes(original)

    def test_same_card_bindings_judge_coverage_and_stale_code_fail(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        original = ledger.read_json(result_path)
        mutations = []
        changed = copy.deepcopy(original)
        changed['bindings']['card_sha256'] = 'f' * 64
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['source_paths']['card'] = self.cases[1]['card_path']
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['judges']['step']['checks'].pop()
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['code_bindings']['tools/independent.py'] = 'f' * 64
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['native_evidence']['editable'] = False
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['editability']['probes'] = []
        mutations.append(changed)
        for index, changed in enumerate(mutations):
            with self.subTest(mutation=index):
                save(result_path, changed)
                with self.assertRaises(Stop):
                    self.proof_check()
        save(result_path, original)

    def test_contradictory_pass_geometry_and_card_thresholds_fail(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        original = ledger.read_json(result_path)
        for key, value in (('valid', False), ('solids', 2), ('solids', True),
                           ('volume_mm3', 0.), ('bounds_mm', [0., 0., 0., 3., 0., 4.])):
            with self.subTest(field=key, value=value):
                changed = copy.deepcopy(original)
                changed['measurements']['step'][key] = value
                save(result_path, changed)
                with self.assertRaisesRegex(Stop, 'integrated_neutral_invalid_geometry'):
                    self.proof_check()
        changed = copy.deepcopy(original)
        changed['native_evidence']['bounds_difference_mm'] = .002
        save(result_path, changed)
        with self.assertRaisesRegex(Stop, 'integrated_neutral_roundtrip_evidence_inconsistent'):
            self.proof_check()
        save(result_path, original)

    def test_missing_unrelated_and_wrong_profile_recipe_registrations_fail(self):
        unrelated = self.base / 'unrelated-recipe.json'
        document = ledger.read_json(self.recipe)
        document['signature_precision_mm'] = .002
        save(unrelated, document)
        registrations = [[], [unrelated, *self.recipe_paths[1:]], self.recipe_paths[1:]]
        for index, paths in enumerate(registrations):
            with self.subTest(registrations=index):
                with self.assertRaisesRegex(Stop, 'integrated_prepared_recipe_not_registered'):
                    integrated.create(self.base / ('recipe-refusal-' + str(index)), root=self.root,
                                      proof_path=self.proof_path, recipe_paths=paths, process=self._process)

    def test_canonical_recipe_commitments_accept_different_json_whitespace(self):
        original = ledger.file_sha(self.recipe)
        self.recipe.write_bytes(self.recipe.read_bytes() + b' \n')
        self.assertNotEqual(ledger.file_sha(self.recipe), original)
        path, value = self.lock()
        self.assertEqual(integrated.verify(path, root=self.root), value)
        self.assertIn(str(self.recipe), value['dependencies'])

    def test_unregistered_prepared_commitment_fails_even_with_updated_bindings(self):
        case = self.cases[0]
        prepared_path = Path(case['prepared_path'])
        prepared = ledger.read_json(prepared_path)
        prepared['assets']['reference']['recipe_sha256'] = 'e' * 64
        save(prepared_path, prepared)
        context_path = Path(case['context_path'])
        context = ledger.read_json(context_path)
        context['prepared_sha256'] = ledger.file_sha(prepared_path)
        save(context_path, context)
        for arm in ('bare_result_path', 'harness_result_path'):
            result_path = Path(case[arm])
            result = ledger.read_json(result_path)
            result['bindings']['prepared_sha256'] = ledger.file_sha(prepared_path)
            result['bindings']['context_sha256'] = ledger.file_sha(context_path)
            save(result_path, result)
        with self.assertRaisesRegex(Stop, 'integrated_prepared_recipe_not_registered'):
            self.proof_check()

    def test_incomplete_and_contradictory_observed_probes_fail(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        original = ledger.read_json(result_path)
        alterations = [('operative', None), ('operative', False), ('restored', False),
                       ('symmetric_difference_mm3', 0.), ('restore_difference_mm3', .1),
                       ('numerical_floor_mm3', None), ('new', 8.), ('error', 'contradictory rejection')]
        for key, value in alterations:
            with self.subTest(field=key, value=value):
                changed = copy.deepcopy(original)
                probe = changed['editability']['probes'][0]
                if value is None:
                    del probe[key]
                else:
                    probe[key] = value
                save(result_path, changed)
                with self.assertRaises((ValueError, Stop)):
                    self.proof_check()
        changed = copy.deepcopy(original)
        changed['editability']['probes'] = [{}]
        save(result_path, changed)
        with self.assertRaises(Stop):
            self.proof_check()
        save(result_path, original)

    def test_observed_rejected_edit_can_prove_operative_restore(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        result = ledger.read_json(result_path)
        probe = result['editability']['probes'][0]
        probe['invalidated_on_rejected_edit'] = True
        del probe['symmetric_difference_mm3']
        save(result_path, result)
        proof, dependencies = self.proof_check()
        self.assertEqual(proof['sha256'], ledger.file_sha(self.proof_path))
        self.assertIn(str(result_path), dependencies)

    def test_roundtrip_acceptance_uses_derived_geometry_not_claimed_zero(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        original = ledger.read_json(result_path)
        for field, value in (('volume_mm3', 30.), ('bounds_mm', [.002, 2., 0., 3., 0., 4.])):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed['measurements']['step'][field] = value
                save(result_path, changed)
                with self.assertRaisesRegex(Stop, 'integrated_neutral_roundtrip_acceptance_failed'):
                    self.proof_check()
        changed = copy.deepcopy(original)
        changed['measurements']['step']['volume_mm3'] = 24.0005
        save(result_path, changed)
        with self.assertRaisesRegex(Stop, 'integrated_neutral_roundtrip_evidence_inconsistent'):
            self.proof_check()
        save(result_path, original)

    def test_sdk_change_after_demo_is_rejected_before_new_identity_launch(self):
        target = self.sdk / 'modules/Part.py'
        target.write_bytes(target.read_bytes() + b'\nchanged_after_demonstration = True\n')
        def forbidden_launch(*args, **kwargs):
            self.fail('historical runtime mismatch must reject before fresh identity')
        with self.assertRaises((ValueError, Stop)):
            integrated.create(self.base / 'stale-sdk-lock', root=self.root, proof_path=self.proof_path,
                              recipe_paths=self.recipe_paths, process=forbidden_launch)
        self.assertFalse((self.base / 'stale-sdk-lock/manifest.json').exists())

    def test_repository_cache_change_after_demo_is_rejected_before_identity(self):
        target = self.root / 'tools/__pycache__/independent.cpython-311.pyc'
        target.write_bytes(target.read_bytes() + b'changed_after_demo')
        def forbidden_launch(*args, **kwargs):
            self.fail('historical repository cache mismatch must reject before identity')
        with self.assertRaises((ValueError, Stop)):
            integrated.create(self.base / 'stale-cache-lock', root=self.root, proof_path=self.proof_path,
                              recipe_paths=self.recipe_paths, process=forbidden_launch)
        self.assertFalse((self.base / 'stale-cache-lock/manifest.json').exists())

    def test_tampered_snapshot_inventory_fails_with_recalculated_file_record(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        result = ledger.read_json(result_path)
        snapshot_path = Path(result['runtime_binding']['path'])
        snapshot = ledger.read_json(snapshot_path)
        snapshot['native_files'][str(self.sdk / 'modules/Part.py')] = 'f' * 64
        save(snapshot_path, snapshot)
        result['runtime_binding'] = integrated._record(snapshot_path)
        save(result_path, result)
        with self.assertRaises((ValueError, Stop)):
            self.proof_check()

    def test_proof_python_identity_must_match_fresh_frozen_sdk_identity(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        result = ledger.read_json(result_path)
        result['runtime']['python_version'] = '0.0.0'
        save(result_path, result)
        out = self.base / 'wrong-python-lock'
        with self.assertRaisesRegex(Stop, 'integrated_neutral_runtime_identity_mismatch'):
            integrated.create(out, root=self.root, proof_path=self.proof_path,
                              recipe_paths=self.recipe_paths, process=self._process)
        self.assertFalse((out / 'manifest.json').exists())
        self.assertFalse((out / 'SHA256.json').exists())

    def test_missing_execution_runtime_and_inconsistent_process_identity_fail(self):
        result_path = Path(self.cases[0]['bare_result_path'])
        original = ledger.read_json(result_path)
        for key in ('runtime', 'runtime_binding'):
            changed = copy.deepcopy(original)
            del changed[key]
            save(result_path, changed)
            with self.subTest(missing=key), self.assertRaises((ValueError, Stop)):
                self.proof_check()
        for key, value in (('gui_up', 1), ('document_closed', False), ('owned_pid', 999),
                           ('freecad_version', ['1', '1', '3']), ('python_version', '')):
            changed = copy.deepcopy(original)
            changed['runtime'][key] = value
            save(result_path, changed)
            with self.subTest(runtime=key), self.assertRaises((ValueError, Stop)):
                self.proof_check()
        save(result_path, original)

    def test_repository_sdk_and_extension_cached_byte_changes_fail(self):
        path, _ = self.lock()
        targets = [self.root / 'tools/__pycache__/independent.cpython-311.pyc',
                   self.sdk / 'modules/__pycache__/Part.cpython-311.pyc',
                   self.proof_path.parent / 'C5/bare/independent_feature.pyc']
        for target in targets:
            with self.subTest(path=str(target)):
                original = target.read_bytes()
                target.write_bytes(original + b'changed executable payload')
                try:
                    with self.assertRaises((ValueError, Stop)):
                        integrated.verify(path, root=self.root)
                finally:
                    target.write_bytes(original)

    def test_original_preflight_rejects_contract_and_modeling_drift(self):
        for name, error in (('contracts.md', 'output_contract_drift'), ('modeling.md', 'modeling_prose_drift')):
            target = self.root / 'skills/cad-harness-v4' / name
            original = target.read_bytes()
            target.write_bytes(original + b'\nindependent unexpected drift\n')
            try:
                with self.subTest(name=name), self.assertRaisesRegex(Stop, error):
                    integrated.create(self.base / ('drift-' + name), root=self.root,
                                      proof_path=self.proof_path, recipe_paths=self.recipe_paths,
                                      process=self._process)
            finally:
                target.write_bytes(original)

    def test_mutation_during_identity_capture_prevents_publication(self):
        def mutate(argv, captures, **kwargs):
            result = self._process(argv, captures, **kwargs)
            (self.root / 'tools/independent.py').write_text('answer = 99\n', encoding='utf-8')
            return result
        out = self.base / 'race-lock'
        with self.assertRaisesRegex(Stop, 'integrated_source_or_head_changed_during_lock'):
            integrated.create(out, root=self.root, proof_path=self.proof_path,
                              recipe_paths=self.recipe_paths, process=mutate)
        self.assertFalse((out / 'manifest.json').exists())
        self.assertFalse((out / 'SHA256.json').exists())

    def test_prohibited_spelling_is_rejected_before_any_lookup(self):
        with patch.object(Path, 'lstat', side_effect=AssertionError('metadata must not be read')):
            with self.assertRaises(ValueError):
                integrated._path(self.base / 'pilot-user' / 'not-opened.json')


if __name__ == '__main__':
    unittest.main()
