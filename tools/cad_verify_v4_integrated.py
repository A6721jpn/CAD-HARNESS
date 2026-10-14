"""Root-anchored implementation evidence, never authority for a live trial.

Only explicit safe source paths are given to read-only Git commands. The lock is
an integrity snapshot, not a signature or a substitute for trusted native proof.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess

if __package__:
    from . import cad_run, cad_verify_v4_agent as agent, cad_verify_v4_inputs as inputs
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_s1 as s1
    from . import cad_verify_v4_plans as plans
    from .cad_verify_guard import Stop
else:
    import cad_run, cad_verify_v4_agent as agent, cad_verify_v4_inputs as inputs
    import cad_verify_v4_ledger as ledger, cad_verify_v4_s1 as s1
    import cad_verify_v4_plans as plans
    from cad_verify_guard import Stop

ROOT = Path(__file__).resolve().parents[1]
DESIGN = 'design/cad-harness-verify-v4'
PROFILES = ('original', 'c-s1', 'c-s2', 'c-s3')
FAMILIES = dict(C1='c-s1', C2='c-s1', C3='c-s1', C4='c-s2', C5='c-s3')
POLICIES = dict(original='policy.json', **{'c-s1': 'capability-policy.json',
                'c-s2': 'policy-c-s2.json', 'c-s3': 'policy-c-s3.json'})
ARCHIVES = ('original-profile-snapshot.zip', 's1-profile-snapshot.zip', 's2-profile-snapshot.zip')
FONT = 'skills/cad-harness-v4/fonts/DejaVuSansMono.ttf'
LICENSE = 'skills/cad-harness-v4/fonts/LICENSE_DEJAVU'
SCHEMA = 'cad-harness.integrated-lock.v4'


def _runtime_api():
    if __package__:
        from . import cad_verify_v4_runtime
    else:
        import cad_verify_v4_runtime
    return cad_verify_v4_runtime


def _same(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)


def _path(value, base=None, *, regular=True):
    # Check the supplied spelling before joining, resolving, or doing metadata IO.
    inputs._lexical(value)
    path = Path(value)
    if not path.is_absolute():
        path = (base if base is not None else Path.cwd()) / path
    return inputs.guarded_path(path, regular=regular)


def _record(path):
    path = _path(path)
    before = path.stat()
    digest = ledger.file_sha(path)
    after = path.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if identity(before) != identity(after):
        raise Stop('integrated_file_changed_during_read:' + str(path))
    return dict(path=str(path), sha256=digest, bytes=after.st_size)


def _json(path):
    before = _record(path)
    value = ledger.read_json(path)
    if before != _record(path):
        raise Stop('integrated_json_changed_during_read:' + str(path))
    return value


def _git(root, *args):
    overrides = {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE'}
    environment = {key: value for key, value in os.environ.items() if key.upper() not in overrides}
    environment.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
    result = subprocess.run(['git', '--no-optional-locks', '--literal-pathspecs', '-C', str(root), *args],
                            stdin=subprocess.DEVNULL, capture_output=True, shell=False, timeout=60,
                            env=environment)
    if result.returncode:
        raise Stop('integrated_git_provenance_unavailable')
    return result.stdout


def _head(root):
    top = _git(root, 'rev-parse', '--show-toplevel').decode('utf-8').strip()
    if _path(top, regular=False) != root:
        raise Stop('integrated_git_root_mismatch')
    lines = _git(root, 'rev-parse', '--verify', 'HEAD').decode('ascii').splitlines()
    tree = _git(root, 'rev-parse', '--verify', 'HEAD^{tree}').decode('ascii').strip()
    if len(lines) != 1 or not all(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', v) for v in (lines[0], tree)):
        raise Stop('integrated_git_identity_contract')
    return dict(head=lines[0], tree=tree)


def _sources(root):
    # Existing inventories cover all tools, the entire registered skill, schema
    # contracts and prior archives, without entering any development user inputs.
    names = set()
    for profile in PROFILES[1:]:
        names.update(s1.implementation_bindings(root, profile=profile))
    names.update(DESIGN + '/dev-' + profile + '/generate.py' for profile in PROFILES[1:])
    names.update((FONT, LICENSE, DESIGN + '/schemas/integrated-lock.schema.json'))
    names.update(_path(path).relative_to(root).as_posix()
                 for path in _runtime_api().repository_caches(root))
    files = {}
    for name in sorted(names):
        path = _path(root / name)
        if not path.is_relative_to(root) or path.relative_to(root).as_posix() != name:
            raise Stop('integrated_source_outside_root')
        files[name] = _record(path)
    return files


def _git_files(root, head, files):
    result = {}
    # Bounded batches avoid the Windows command-line length limit. No repository
    # traversal, status, diff, index write, or unrestricted tree query is used.
    names = sorted(files)
    blobs = {}
    for start in range(0, len(names), 50):
        raw = _git(root, 'ls-tree', '-z', head, '--', *names[start:start + 50])
        for row in raw.split(b'\0'):
            if not row:
                continue
            header, name = row.split(b'\t', 1)
            mode, kind, oid = header.decode('ascii').split()
            name = name.decode('utf-8')
            if name not in files or kind != 'blob' or mode not in ('100644', '100755'):
                raise Stop('integrated_git_file_contract')
            blobs[name] = (mode, oid)
    for name, record in files.items():
        mode, oid = blobs.get(name, (None, None))
        raw = _path(record['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record['sha256'] or len(raw) != record['bytes']:
            raise Stop('integrated_source_race')
        working_blob = hashlib.new('sha256' if len(head) == 64 else 'sha1',
                                  b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
        result[name] = dict(blob=oid, mode=mode,
                           overlay='untracked' if oid is None else 'clean' if oid == working_blob else 'modified')
    return result


def _profiles(root):
    result = {}
    for profile in PROFILES:
        policy = _path(root / DESIGN / POLICIES[profile])
        value = _json(policy)
        if type(value.get('live_authorized_calls')) is not int or value['live_authorized_calls'] != 0:
            raise Stop('integrated_policy_not_zero_live')
        if profile == 'original':
            if __package__:
                from . import eval_verify_v4
            else:
                import eval_verify_v4
            ready = eval_verify_v4.preflight(policy, root=root)
        else:
            ready = s1.preflight(root, profile=profile)
        result[profile] = dict(skill_sha256=ledger.sha(agent.bundle(root, profile=profile)),
                               policy_sha256=_record(policy)['sha256'], preflight=ready)
    return result


def _archives(root):
    result = {}
    for name, stage in zip(ARCHIVES, (None, 'c-s1', 'c-s2')):
        path = _path(root / DESIGN / name)
        s1.verify_original_snapshot(path, stage=stage)
        result[name] = _record(path)
    return result


def _recipes(paths):
    result = []
    seen = set()
    for value in paths:
        path = _path(value)
        if str(path) in seen:
            raise Stop('integrated_duplicate_recipe')
        seen.add(str(path))
        recipe = _json(path)
        kind = {'cad-harness.step-recipe.v4c': 'step-recipe',
                'cad-harness.contour-recipe.v4c': 'contour-recipe'}.get(recipe.get('schema'))
        if kind is None:
            raise Stop('integrated_recipe_contract')
        plans.validate_document(recipe, kind, profile=recipe.get('profile', 'c-s1'))
        result.append(_record(path))
    return sorted(result, key=lambda r: r['path'])


def _recipe_commitments(prepared, profile, recipes):
    registered = {}
    for record in recipes:
        recipe = _json(record['path'])
        kind = recipe['schema']
        registered.setdefault((inputs.canonical_sha(recipe), recipe['profile'], kind), []).append(record)
    resolved = {}

    def visit(value, inherited_profile, inherited_kind):
        if isinstance(value, dict):
            current_profile = value.get('profile', inherited_profile)
            current_kind = {'cad-harness.step-facts.v4c': 'cad-harness.step-recipe.v4c',
                            'cad-harness.contour.v4c': 'cad-harness.contour-recipe.v4c'}.get(
                                value.get('schema'), inherited_kind)
            for key, digest in value.items():
                if key.endswith('recipe_sha256'):
                    kind = ('cad-harness.step-recipe.v4c' if key.startswith('step_') else
                            'cad-harness.contour-recipe.v4c' if key.startswith('contour_') else current_kind)
                    matches = registered.get((digest, current_profile, kind), [])
                    if not matches:
                        raise Stop('integrated_prepared_recipe_not_registered')
                    for record in matches:
                        resolved[record['path']] = record
            for child in value.values():
                visit(child, current_profile, current_kind)
        elif isinstance(value, list):
            for child in value:
                visit(child, inherited_profile, inherited_kind)

    visit(prepared, profile, None)
    return list(resolved.values())


def _geometry_result(result, card):
    def number(value):
        return type(value) in (int, float) and math.isfinite(value)
    measurements = result.get('measurements', {})
    if not isinstance(measurements, dict):
        raise Stop('integrated_neutral_measurements_missing')
    for representation in ('fcstd', 'step'):
        shape = measurements.get(representation, {})
        bounds = shape.get('bounds_mm')
        volume = shape.get('volume_mm3')
        if (shape.get('valid') is not True or type(shape.get('solids')) is not int or shape['solids'] != 1
                or not number(volume) or volume <= 0 or not isinstance(bounds, list) or len(bounds) != 6
                or not all(number(value) for value in bounds)
                or any(bounds[i] >= bounds[i + 1] for i in (0, 2, 4))):
            raise Stop('integrated_neutral_invalid_geometry')
    evidence = result.get('native_evidence', {})
    for field in ('bounds_difference_mm', 'volume_difference_mm3'):
        if not number(evidence.get(field)) or evidence[field] < 0:
            raise Stop('integrated_neutral_roundtrip_measurement_missing')
    native, step = measurements['fcstd'], measurements['step']
    derived = dict(bounds_difference_mm=max(abs(a - b) for a, b in zip(native['bounds_mm'], step['bounds_mm'])),
                   volume_difference_mm3=abs(native['volume_mm3'] - step['volume_mm3']))
    for criterion in card['criteria']:
        if criterion['metric'] == 'native_roundtrip':
            for measured, maximum in (('bounds_difference_mm', 'maximum_bounds_difference_mm'),
                                      ('volume_difference_mm3', 'maximum_volume_difference_mm3')):
                if maximum not in criterion or derived[measured] > criterion[maximum]:
                    raise Stop('integrated_neutral_roundtrip_acceptance_failed')
    if any(evidence[field] != value for field, value in derived.items()):
        raise Stop('integrated_neutral_roundtrip_evidence_inconsistent')


def _editability_result(edit, bundle):
    probes = edit.get('probes')
    if edit.get('status') != 'PASS' or not isinstance(probes, list) or not probes:
        raise Stop('integrated_neutral_edit_probe_missing')
    if bundle['probes'] and not _same([row.get('probe') for row in probes], bundle['probes']):
        raise Stop('integrated_neutral_edit_probe_registration_mismatch')
    number = lambda value: type(value) in (int, float) and math.isfinite(value)
    if __package__:
        from . import cad_verify_v4_artifacts as artifacts
    else:
        import cad_verify_v4_artifacts as artifacts
    schema = _json(_path(artifacts.SCHEMA))
    for row in probes:
        if (not isinstance(row, dict) or row.get('operative') is not True or row.get('restored') is not True
                or not isinstance(row.get('probe'), dict) or 'old' not in row or 'new' not in row
                or _same(row['old'], row['new']) or row.get('error') is not None
                or row.get('error_type') is not None or row.get('changed') is False
                or row.get('status', 'PASS') != 'PASS'):
            raise Stop('integrated_neutral_edit_probe_contradictory')
        probe = row['probe']
        plans._check(probe, schema['$defs']['probe'], schema, 'integrated_observed_probe')
        if probe['kind'] in ('scalar', 'sketch_constraint'):
            consistent = (number(row['old']) and number(row['new']) and
                          row['new'] == row['old'] + probe['delta'])
        elif probe['kind'] in ('vector', 'vector_list'):
            old, new = row['old'], row['new']
            consistent = (isinstance(old, list) and isinstance(new, list) and len(old) == len(new) == 3
                          and all(number(value) for value in old + new)
                          and new == [value + delta for value, delta in zip(old, probe['delta_mm'])])
        else:
            consistent = (isinstance(row['old'], str) and isinstance(row['new'], str)
                          and row['new'] == row['old'] + probe['suffix'])
        if not consistent:
            raise Stop('integrated_neutral_edit_probe_observation_mismatch')
        floor, restore = row.get('numerical_floor_mm3'), row.get('restore_difference_mm3')
        if not number(floor) or floor <= 0 or not number(restore) or not 0 <= restore <= floor:
            raise Stop('integrated_neutral_edit_probe_restore_failed')
        invalidated = row.get('invalidated_on_rejected_edit')
        difference = row.get('symmetric_difference_mm3')
        if invalidated is True:
            if difference is not None:
                raise Stop('integrated_neutral_edit_probe_contradictory')
        elif invalidated is not False or not number(difference) or difference <= floor:
            raise Stop('integrated_neutral_edit_probe_nonoperative')


def _proof_runtime(result, snapshot, root, native_files, extension_paths, frozen=None):
    _runtime_api().verify(snapshot, root=root, extension_paths=extension_paths, native_files=native_files)
    if (snapshot['native_files'] != native_files or snapshot['root'] != str(root)
            or snapshot['sdk_root'] != str(_path(cad_run.FREECAD_DIR, regular=False))):
        raise Stop('integrated_neutral_runtime_snapshot_mismatch')
    runtime = result.get('runtime')
    if not isinstance(runtime, dict):
        raise Stop('integrated_neutral_runtime_missing')
    executable = _path(runtime.get('python_executable', ''))
    if (runtime.get('freecad_version', [])[:3] != ['1', '1', '4']
            or not executable.is_relative_to(_path(cad_run.FREECAD_DIR, regular=False))
            or str(executable) not in native_files or not isinstance(runtime.get('python_version'), str)
            or not runtime['python_version'] or runtime.get('document_closed') is not True
            or type(runtime.get('gui_up')) is not int or runtime['gui_up'] != 0
            or type(runtime.get('owned_pid')) is not int or runtime['owned_pid'] != result['owned_pid']):
        raise Stop('integrated_neutral_runtime_identity_mismatch')
    if frozen is not None and any(runtime.get(key) != frozen[key] for key in
                                  ('freecad_version', 'python_executable', 'python_version')):
        raise Stop('integrated_neutral_runtime_identity_mismatch')


def _proof(proof_path, *, root=ROOT, recipes=(), runtime=None):
    """Validate actual same-card results and close every data/path dependency."""
    dependencies = {}
    pending = []
    implementation = {}
    native_files = (_runtime_api().native_files() if runtime is None else
                    {name: record['sha256'] for name, record in runtime['files'].items()})

    def add(value, base=None, expected=None):
        path = _path(value, base)
        record = _record(path)
        if expected is not None:
            for key in ('sha256', 'bytes'):
                if key in expected and not _same(record[key], expected[key]):
                    raise Stop('integrated_proof_dependency_mismatch:' + str(path))
        old = dependencies.get(str(path))
        if old is not None and old != record:
            raise Stop('integrated_proof_dependency_race')
        if old is None:
            dependencies[str(path)] = record
            if path.suffix.lower() == '.json':
                pending.append(path)
        return path

    proof_path = add(proof_path)
    proof = _json(proof_path)
    if (not isinstance(proof, dict) or set(proof) != {'schema', 'evidence_mode', 'live_calls', 'cases'}
            or proof['schema'] != 'cad-harness.neutral-proof.v4'
            or proof['evidence_mode'] != 'independent_dev'
            or type(proof['live_calls']) is not int or proof['live_calls'] != 0
            or not isinstance(proof['cases'], list) or len(proof['cases']) != 5):
        raise Stop('integrated_neutral_proof_contract')
    seen = set()
    for case in proof['cases']:
        keys = {'family', 'profile', 'input_manifest_path', 'prepared_path', 'card_path',
                'context_path', 'bare_result_path', 'harness_result_path'}
        if not isinstance(case, dict) or set(case) != keys:
            raise Stop('integrated_neutral_case_contract')
        family, profile = case['family'], case['profile']
        if family not in FAMILIES or FAMILIES[family] != profile or family in seen:
            raise Stop('integrated_neutral_case_roster')
        if profile not in implementation:
            implementation[profile] = s1.implementation_bindings(root, profile=profile)
        seen.add(family)
        paths = {key: add(case[field], proof_path.parent) for key, field in
                 (('manifest', 'input_manifest_path'), ('prepared', 'prepared_path'),
                  ('card', 'card_path'), ('context', 'context_path'))}
        manifest = inputs.load_manifest(paths['manifest'])
        if manifest['profile'] != profile or manifest.get('evidence_mode') != 'independent_dev':
            raise Stop('integrated_neutral_input_profile')
        prepared = inputs.verify_prepared(paths['prepared'], paths['manifest'])
        for recipe in _recipe_commitments(prepared, profile, recipes):
            add(recipe['path'], expected=recipe)
        card = plans.validate_judge_card(_json(paths['card']), profile=profile)
        if __package__:
            from . import cad_verify_v4_artifact_judges as neutral
        else:
            import cad_verify_v4_artifact_judges as neutral
        context = neutral.validate_context(_json(paths['context']), paths['manifest'],
                                           paths['prepared'], paths['card'], profile=profile)
        if context.get('family') != family:
            raise Stop('integrated_neutral_context_family')
        for asset_id in manifest['assets']:
            asset = inputs.resolve_asset(paths['manifest'], asset_id)
            add(asset['path'], expected=asset['record'])
        expected_bindings = {key + '_sha256': dependencies[str(path)]['sha256'] for key, path in paths.items()}
        for arm in ('bare_result_path', 'harness_result_path'):
            path = add(case[arm], proof_path.parent)
            result = _json(path)
            if (result.get('schema') != 'cad-harness.artifact-check-result.v4'
                    or result.get('profile') != profile or result.get('family') != family
                    or result.get('status') != 'PASS' or result.get('document_closed') is not True
                    or type(result.get('gui_up')) is not int or result['gui_up'] != 0
                    or type(result.get('owned_pid')) is not int or result['owned_pid'] <= 0
                    or type(result.get('live_calls')) is not int or result['live_calls'] != 0):
                raise Stop('integrated_neutral_result_contract')
            if result.get('code_bindings') != implementation[profile]:
                raise Stop('integrated_neutral_stale_implementation')
            sources = result.get('source_paths')
            if not isinstance(sources, dict) or set(sources) != set(paths) | {'bundle'}:
                raise Stop('integrated_neutral_source_paths')
            for key, source in paths.items():
                if add(sources[key], path.parent) != source:
                    raise Stop('integrated_neutral_same_card_mismatch')
            bundle_path = add(sources['bundle'], path.parent)
            bindings = dict(expected_bindings, bundle_sha256=dependencies[str(bundle_path)]['sha256'])
            if not _same(result.get('bindings'), bindings):
                raise Stop('integrated_neutral_bindings_mismatch')
            if __package__:
                from . import cad_verify_v4_artifacts as artifacts
            else:
                import cad_verify_v4_artifacts as artifacts
            bundle, _, extensions = artifacts.load_bundle(bundle_path, profile=profile)
            for extension in bundle['extensions']:
                add(extension['path'], bundle_path.parent, extension)
            runtime_record = result.get('runtime_binding')
            if not isinstance(runtime_record, dict) or set(runtime_record) != {'path', 'sha256', 'bytes'}:
                raise Stop('integrated_neutral_runtime_binding_missing')
            runtime_path = add(runtime_record['path'], path.parent, runtime_record)
            snapshot = _json(runtime_path)
            _proof_runtime(result, snapshot, root, native_files, tuple(extensions.values()), frozen=runtime)
            for collection in ('repository_caches', 'extension_files'):
                for name, digest in snapshot[collection].items():
                    add(name, expected={'sha256': digest})
            for key, bundle_key in (('native', 'native'), ('step', 'step')):
                artifact = result.get('artifacts', {}).get(key)
                registered = bundle.get(bundle_key)
                if not isinstance(artifact, dict) or not isinstance(registered, dict):
                    raise Stop('integrated_neutral_artifact_missing')
                if add(artifact['path'], path.parent, artifact) != add(registered['path'], bundle_path.parent, registered):
                    raise Stop('integrated_neutral_artifact_mismatch')
            evidence = result.get('native_evidence', {})
            if any(evidence.get(key) is not True for key in ('fcstd_reopened', 'step_reopened', 'editable')):
                raise Stop('integrated_neutral_reopen_editability_missing')
            _geometry_result(result, card)
            _editability_result(result.get('editability', {}), bundle)
            judges = result.get('judges')
            if not isinstance(judges, dict) or set(judges) != {'fcstd', 'step'}:
                raise Stop('integrated_neutral_judges_missing')
            criteria = {row['id']: row['metric'] for row in card['criteria']}
            for judgement in judges.values():
                checks = judgement.get('checks', [])
                if (judgement.get('status') != 'PASS' or judgement.get('profile') != profile
                        or len(checks) != len(criteria) or any(row.get('status') != 'PASS' for row in checks)
                        or {row.get('id'): row.get('metric') for row in checks} != criteria):
                    raise Stop('integrated_neutral_card_criteria_mismatch')
            roundtrip = result.get('roundtrip')
            wanted = {row['id'] for row in card['criteria'] if row['metric'] == 'native_roundtrip'}
            if (not isinstance(roundtrip, list) or len(roundtrip) != len(wanted)
                    or {row.get('id') for row in roundtrip} != wanted
                    or any(row.get('status') != 'PASS' for row in roundtrip)):
                raise Stop('integrated_neutral_roundtrip_mismatch')

    def visit(value, base):
        if isinstance(value, dict):
            if 'path' in value and isinstance(value['path'], str):
                add(value['path'], base, value)
            for key, child in value.items():
                if key != 'path' and (key.endswith('_path') and isinstance(child, str)):
                    add(child, base)
                elif key.endswith('_paths') and isinstance(child, list):
                    for item in child:
                        add(item, base)
                elif key == 'source_paths' and isinstance(child, dict):
                    for item in child.values():
                        add(item, base)
                else:
                    visit(child, base)
        elif isinstance(value, list):
            for child in value:
                visit(child, base)

    while pending:
        path = pending.pop()
        visit(_json(path), path.parent)
    for path, record in dependencies.items():
        if _record(path) != record:
            raise Stop('integrated_proof_changed_during_read')
    return dependencies[str(proof_path)], dict(sorted(dependencies.items()))




def _fonts(root):
    font, license_path = _path(root / FONT), _path(root / LICENSE)
    with font.open('rb') as stream:
        if stream.read(4) not in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
            raise Stop('integrated_registered_font_invalid')
    if not license_path.read_text(encoding='utf-8').strip():
        raise Stop('integrated_registered_license_empty')
    return {'DejaVuSansMono': dict(font=_record(font), license=_record(license_path))}


def _unchanged(value):
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256', 'bytes'} and _record(value['path']) != value:
            raise Stop('integrated_bound_file_changed')
        for child in value.values():
            _unchanged(child)
    elif isinstance(value, list):
        for child in value:
            _unchanged(child)


def _runtime(identity, evidence):
    if (identity.get('status') != 'PASS' or identity.get('document_closed') is not True
            or type(identity.get('gui_up')) is not int or identity['gui_up'] != 0):
        raise Stop('integrated_runtime_identity_unverified')
    runtime = identity.get('runtime', {})
    pinned = _path(cad_run.FREECAD_DIR, regular=False)
    files = runtime.get('files')
    required = {'FreeCAD', 'Part', 'Sketcher', 'numpy', 'scipy', 'PIL', 'shapely',
                'contourpy', 'fontTools', 'OCC'}
    dependencies = identity.get('dependencies', {})
    if not isinstance(files, dict) or not files or set(dependencies) != required:
        raise Stop('integrated_runtime_inventory_missing')
    executable = str(_path(runtime.get('python_executable', '')))
    if (identity.get('sdk_files') != files or _runtime_api().native_files(pinned) != files
            or runtime.get('freecad_version', [])[:3] != ['1', '1', '4']
            or not isinstance(runtime.get('python_version'), str) or not runtime['python_version']
            or runtime.get('document_closed') is not True
            or type(runtime.get('gui_up')) is not int or runtime['gui_up'] != 0
            or type(runtime.get('owned_pid')) is not int or runtime['owned_pid'] != identity.get('owned_pid')
            or runtime['owned_pid'] <= 0 or executable not in files
            or any(not value['files'] for value in dependencies.values())):
        raise Stop('integrated_runtime_inventory_incomplete')
    for dependency in dependencies.values():
        source = _path(dependency['path'])
        if not source.is_relative_to(pinned) or str(source) not in files:
            raise Stop('integrated_runtime_module_outside_sdk')
        for item in dependency['files']:
            if (_record(item['path']) != item or files.get(item['path']) != item['sha256']):
                raise Stop('integrated_runtime_module_file_changed')
    for item in identity.get('native_libraries', []):
        if _record(item['path']) != item or files.get(item['path']) != item['sha256']:
            raise Stop('integrated_runtime_library_changed')
    records = {}
    for name, digest in files.items():
        path = _path(name)
        record = _record(path)
        if not path.is_relative_to(pinned) or record['sha256'] != digest:
            raise Stop('integrated_runtime_dependency_changed')
        records[str(path)] = record
    evidence = _path(evidence)
    out = evidence.parent.parent
    execution = {name: _record(out / name) for name in
                 ('ledger.jsonl', 'runtime.job.json', 'runtime.stdout.bin', 'runtime.stderr.bin')}
    if (out / 'runtime.ready.json').exists():
        execution['runtime.ready.json'] = _record(out / 'runtime.ready.json')
    return dict(sdk_root=str(pinned), freecad_version=runtime['freecad_version'],
                python_version=runtime['python_version'], python_executable=executable,
                occt_version=identity['occt_version'],
                modules={name: value['path'] for name, value in sorted(dependencies.items())},
                files=dict(sorted(records.items())), evidence=_record(evidence), execution=execution)


def _schema(value, root):
    schema = _json(_path(root / DESIGN / 'schemas/integrated-lock.schema.json'))
    plans._check(value, schema, schema, 'integrated-lock')
    if (value.get('schema') != SCHEMA or value.get('stage') != 'implementation'
            or value.get('status') != 'offline_locked' or value.get('evidence_mode') != 'independent_dev'
            or value.get('authorization') is not None or value.get('final_v4_ready') is not False
            or type(value.get('live_calls')) is not int or value['live_calls'] != 0
            or set(value.get('profiles', {})) != set(PROFILES)):
        raise Stop('integrated_zero_live_contract')


def create(run_dir, *, root=ROOT, proof_path, recipe_paths=(), process=None):
    """Write exactly one SHA payload/manifest, plus owned native identity evidence."""
    root = _path(root, regular=False)
    before_head = _head(root)
    files = _sources(root)
    profiles, archives = _profiles(root), _archives(root)
    recipes = _recipes(recipe_paths)
    proof, dependencies = _proof(proof_path, root=root, recipes=recipes)
    fonts = _fonts(root)
    git_files = _git_files(root, before_head['head'], files)
    out = ledger.new_directory(s1.safe_path(run_dir))
    with ledger.Journal(out / 'ledger.jsonl', out.name, 'integrated-implementation-lock') as journal:
        journal.append('run_started', evidence_mode='independent_dev', live_calls=0)
        identity = s1.native_work('identity', out / 'runtime', journal, process=process)
        journal.append('run_finished', live_calls=0, stop_reason=None)
    runtime = _runtime(identity, out / 'runtime/result.json')
    value = dict(schema=SCHEMA, stage='implementation', status='offline_locked',
                 root=str(root), freeze_dir=str(out), authorization=None, final_v4_ready=False,
                 evidence_mode='independent_dev', live_calls=0,
                 git=dict(**before_head, files=git_files), files=files, profiles=profiles,
                 archives=archives, fonts=fonts, recipes=recipes, proof=proof,
                 dependencies=dependencies, runtime=runtime)
    if before_head != _head(root) or files != _sources(root) or git_files != _git_files(root, before_head['head'], files):
        raise Stop('integrated_source_or_head_changed_during_lock')
    if (profiles != _profiles(root) or archives != _archives(root) or recipes != _recipes([r['path'] for r in recipes])
            or (proof, dependencies) != _proof(proof_path, root=root, recipes=recipes, runtime=runtime)
            or runtime != _runtime(_json(runtime['evidence']['path']), runtime['evidence']['path'])):
        raise Stop('integrated_dependency_changed_during_lock')
    # Validate before publishing either lock file; sha256_file exists only in the manifest.
    _schema(dict(value, sha256_file='0' * 64), root)
    _unchanged(value)
    if before_head != _head(root):
        raise Stop('integrated_head_changed_before_publication')
    ledger.write_json(out / 'SHA256.json', value)
    value['sha256_file'] = ledger.file_sha(out / 'SHA256.json')
    ledger.write_json(out / 'manifest.json', value)
    return value


def verify(manifest_path, *, root=ROOT):
    """Fail closed on changed HEAD, working bytes, authority or proof dependencies."""
    root = _path(root, regular=False)
    path = _path(manifest_path)
    manifest_record = _record(path)
    value = _json(path)
    _schema(value, root)
    if value['root'] != str(root) or value['freeze_dir'] != str(path.parent) or path.name != 'manifest.json':
        raise Stop('integrated_root_or_output_anchor_mismatch')
    sha_path = _path(path.parent / 'SHA256.json')
    if (_record(sha_path)['sha256'] != value['sha256_file']
            or not _same(_json(sha_path), {k: v for k, v in value.items() if k != 'sha256_file'})):
        raise Stop('integrated_sha_wrapper_mismatch')
    head = _head(root)
    if head != {k: value['git'][k] for k in ('head', 'tree')}:
        raise Stop('integrated_head_changed')
    files = _sources(root)
    if files != value['files'] or _git_files(root, head['head'], files) != value['git']['files']:
        raise Stop('integrated_working_source_changed')
    if _profiles(root) != value['profiles'] or _archives(root) != value['archives']:
        raise Stop('integrated_profile_changed')
    fonts = _fonts(root)
    if fonts != value['fonts'] or _recipes([r['path'] for r in value['recipes']]) != value['recipes']:
        raise Stop('integrated_font_or_recipe_changed')
    runtime = value['runtime']
    if _runtime(_json(runtime['evidence']['path']), runtime['evidence']['path']) != runtime:
        raise Stop('integrated_runtime_changed')
    proof, dependencies = _proof(value['proof']['path'], root=root, recipes=value['recipes'], runtime=runtime)
    if proof != value['proof'] or dependencies != value['dependencies']:
        raise Stop('integrated_neutral_proof_changed')
    if (head != _head(root) or files != _sources(root) or _record(path) != manifest_record
            or (proof, dependencies) != _proof(value['proof']['path'], root=root,
                                              recipes=value['recipes'], runtime=runtime)):
        raise Stop('integrated_changed_during_verification')
    _unchanged(value)
    if _record(sha_path)['sha256'] != value['sha256_file'] or head != _head(root):
        raise Stop('integrated_wrapper_or_head_changed_during_verification')
    return value
