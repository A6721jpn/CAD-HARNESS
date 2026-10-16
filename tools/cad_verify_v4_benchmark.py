"""Authorized harness-versus-bare-agent benchmark; importing performs no work.

The operational registration is an explicit execution index over opaque committed
corpus bytes, not a guessed private roster schema. All 20 pairs remain enrolled.
"""
from collections import Counter
from datetime import datetime, timezone
import base64
import csv
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import time

if __package__:
    from . import cad_verify_v4_bare as bare
else:
    import cad_verify_v4_bare as bare

SCHEMA = 'cad-harness.cad-time-benchmark.v1'
RESERVATIONS = {'with_harness:generation': 60, 'bare:generation': 60, 'benchmark:judge': 40}
STRATA = {
    'C1': {'prismatic': 2, 'stepped_oriented': 1, 'curved_irregular': 1},
    'C2': {'convex': 2, 'connected_holes': 1, 'notch_tool_access': 1},
    'C3': {'numeric': 2, 'alphanumeric': 1, 'dense': 1},
    'C4': {'planar_oblique': 1, 'curved_offsets': 1, 'finite_planar_replacement': 1, 'preservation': 1},
    'C5': {'two_patch': 2, 'trimmed_multi_patch': 2}}
ARMS = ('with_harness', 'bare')
METRICS = ('full_wall_s', 'service_s', 'active_s', 'native_cad_s')


def _module(name):
    return importlib.import_module(('tools.' if __package__ else '') + name)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _intervals(values, *, allow_open=False):
    if not isinstance(values, list):
        raise ValueError('benchmark_intervals_required')
    for index, interval in enumerate(values):
        if not isinstance(interval, list) or len(interval) != 2 or not _number(interval[0]):
            raise ValueError('benchmark_interval_endpoints')
        end = interval[1]
        if end is None:
            if not allow_open or index != len(values) - 1:
                raise ValueError('benchmark_only_final_custody_hold_may_be_open')
        elif not _number(end) or end < interval[0]:
            raise ValueError('benchmark_interval_endpoints')
    return values


def union(intervals):
    """Union, not addition, of overlapping monotonic operation intervals."""
    ordered = sorted(_intervals(intervals))
    merged = []
    for start, end in ordered:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged)


def validate_registration(registration):
    if registration.get('schema') != 'cad-harness.live-registration.v1' or registration.get('phase') != 'benchmark':
        raise ValueError('benchmark_registration_schema')
    files = registration.get('files', {})
    pairs = registration.get('pairs')
    if not isinstance(pairs, list) or len(pairs) != 20:
        raise ValueError('benchmark_exactly_twenty_pairs')
    expected_ids = {'B%02d' % n for n in range(1, 21)}
    if {p.get('id') for p in pairs} != expected_ids:
        raise ValueError('benchmark_original_published_identity_enrollment')
    for family, strata in STRATA.items():
        subset = [p for p in pairs if p.get('family') == family]
        if Counter(p.get('stratum') for p in subset) != Counter(strata):
            raise ValueError('benchmark_family_strata:' + family)
    for pair in pairs:
        family = 'C' + str((int(pair['id'][1:]) - 1) // 4 + 1)
        if pair['family'] != family or pair.get('profile') != ('c-s1' if family in ('C1', 'C2', 'C3') else 'c-s2' if family == 'C4' else 'c-s3'):
            raise ValueError('benchmark_family_profile_identity')
        for key in ('request', 'input_manifest', 'prepared', 'card', 'context', 'pair_record'):
            if pair.get(key) not in files:
                raise ValueError('benchmark_bound_file:' + key)
        if files[pair['request']].get('role') != 'original_request':
            raise ValueError('benchmark_original_request_only')
        if pair.get('same_card_both_arms') is not True or pair.get('independent_fresh') is not True:
            raise ValueError('benchmark_same_card_fresh_corpus_required')
        originals = pair.get('original_assets')
        if not isinstance(originals, list) or len({a.get('name', '').casefold() for a in originals}) != len(originals):
            raise ValueError('benchmark_original_asset_index')
        for asset in originals:
            bare._relative(asset['name'])
            if asset.get('file') not in files or files[asset['file']].get('role') != 'original_asset':
                raise ValueError('benchmark_original_asset_only')
        if not set(pair.get('original_images', [])).issubset({a['file'] for a in originals}):
            raise ValueError('benchmark_original_images_only')
        preparations = pair.get('preparation')
        if not isinstance(preparations, dict) or set(preparations) != set(ARMS):
            raise ValueError('benchmark_preparation_records_required')
        for arm in ARMS:
            prep = preparations[arm]
            _intervals(prep.get('preparation_intervals'))
            _intervals(prep.get('custody_hold_intervals'), allow_open=True)
            _intervals(prep.get('native_cad_intervals'))
            if union(prep['preparation_intervals'] + prep['native_cad_intervals']) != union(prep['preparation_intervals']):
                raise ValueError('benchmark_preparation_native_interval_outside_work')
            if not isinstance(prep.get('recorded_once'), bool) or not prep['recorded_once']:
                raise ValueError('benchmark_preparation_no_replay')
            if prep.get('evidence') not in files:
                raise ValueError('benchmark_preparation_evidence_required')
            if prep.get('clock_id') != registration.get('clocks', {}).get('clock_id'):
                raise ValueError('benchmark_preparation_clock_mismatch')
            if not _number(prep.get('active_s')) or prep['active_s'] < 0:
                raise ValueError('benchmark_preparation_active_required')
            # Pre-freeze preparation contains no authorized provider invocation:
            # research holds are separate, and ordinary work/idle is charged.
            if prep['active_s'] != union(prep['preparation_intervals']):
                raise ValueError('benchmark_preparation_active_not_fully_charged')
            holds = prep['custody_hold_intervals']
            closed = [v for v in holds if v[1] is not None]
            if union(prep['preparation_intervals'] + closed) != union(prep['preparation_intervals']) + union(closed):
                raise ValueError('benchmark_preparation_hold_overlap')
            if holds and holds[-1][1] is None and any(b > holds[-1][0] for _, b in prep['preparation_intervals'] + closed):
                raise ValueError('benchmark_open_custody_hold_overlap')
    order = registration.get('order')
    if not isinstance(order, list) or len(order) != 40:
        raise ValueError('benchmark_frozen_forty_slots')
    if Counter((slot.get('pair'), slot.get('arm')) for slot in order) != Counter((i, a) for i in expected_ids for a in ARMS):
        raise ValueError('benchmark_frozen_order_complete_once')
    first = {i: next(s['arm'] for s in order if s['pair'] == i) for i in expected_ids}
    for family in STRATA:
        if Counter(first[p['id']] for p in pairs if p['family'] == family) != Counter(with_harness=2, bare=2):
            raise ValueError('benchmark_balanced_first_order:' + family)
    if not isinstance(registration.get('order_seed'), str) or not registration['order_seed']:
        raise ValueError('benchmark_preregistered_seed_required')
    if registration.get('reservations') != RESERVATIONS:
        raise ValueError('benchmark_separate_exact_reservations')
    if registration.get('caps') != {'active_s_per_arm': 1200, 'calls_per_arm': 3}:
        raise ValueError('benchmark_signed_caps')
    runtime = registration.get('bare_runtime', {})
    if (not isinstance(runtime, dict) or set(runtime) != {'root', 'inventory', 'staging_proof'} or
            runtime.get('inventory') not in files or runtime.get('staging_proof') not in files or
            not Path(runtime.get('root', '')).is_absolute() or
            Path(runtime['root']) == bare.isolation.PINNED_PYTHON.parent.parent or
            files[runtime['inventory']].get('role') != 'bare_runtime_inventory' or
            files[runtime['staging_proof']].get('role') != 'bare_runtime_staging_proof' or
            any(files[runtime[k]].get('origin') != 'operational' for k in ('inventory', 'staging_proof'))):
        raise ValueError('benchmark_verified_private_runtime_inventory_and_staging_required')
    for key in ('rubric', 'protocol', 'source_commitment', 'adapter_demonstration', 'isolation_demonstration'):
        if registration.get(key) not in files:
            raise ValueError('benchmark_frozen_prerequisite:' + key)
    custody = registration.get('custody', {})
    if any(not isinstance(custody.get(k), str) or not custody[k] for k in ('author', 'reviewer', 'custodian')):
        raise ValueError('benchmark_independent_custody_identities')
    if len(set(custody[k] for k in ('author', 'reviewer', 'custodian'))) != 3:
        raise ValueError('benchmark_custody_separation')
    humans = registration.get('human_judges')
    if (not isinstance(humans, list) or not humans or
            len({h.get('id') for h in humans}) != len(humans) or
            any(not isinstance(h.get('id'), str) or not h['id'].strip() or h.get('kind') != 'human' or
                h.get('qualification_evidence') not in files for h in humans)):
        raise ValueError('benchmark_registered_actual_human_judges_required')
    clocks = registration.get('clocks', {})
    if any(not isinstance(clocks.get(k), str) or not clocks[k] for k in ('clock_id', 'boot_id', 'utc_reference')) or not _number(clocks.get('resolution_s')) or clocks['resolution_s'] <= 0:
        raise ValueError('benchmark_clock_identity_required')
    validate_durability(registration)
    return registration


def original_source_assets(manifest, prepared):
    """Select ORIGINAL information by published typed roles, never filenames.

    Checker STEP gold and derived masks stay checker-only. A checker-tagged raw
    raster is original only when a typed contour explicitly names its source
    image ID; inline source_mask data is never an exposure instruction.
    """
    assets = manifest['assets']
    selected = {key for key, record in assets.items() if record['kind'] not in ('contour', 'facts') and
                (record.get('role') in ('reference', 'font', 'license') or
                 record['kind'] == 'image' and record.get('role') == 'contour')}
    for contour in prepared.get('assets', {}).values():
        if contour.get('schema') != 'cad-harness.contour.v4c' or 'source_image_asset_id' not in contour:
            continue
        image = contour['source_image_asset_id']
        if image not in assets or assets[image]['kind'] != 'image':
            raise ValueError('benchmark_typed_original_image_dependency')
        selected.add(image)
    return {assets[key]['path']: assets[key] for key in sorted(selected)}


def validate_bound_inputs(registration, path_for_id):
    """All reads go through an authenticated resolver; no private schema guess."""
    validate_registration(registration)
    families = _module('cad_verify_v4_family_live')
    families.validate_published_files(registration, path_for_id)
    for pair in registration['pairs']:
        member_names = dict(request='request.txt', input_manifest='manifest.json', prepared='prepared.json',
                            card='card.json', context='context.json', pair_record='pair.json')
        for field, name in member_names.items():
            if registration['files'][pair[field]].get('published_relative_path') != 'benchmark/' + pair['id'] + '/' + name:
                raise ValueError('benchmark_published_pair_identity')
        families._card_requirements(pair, json.loads(path_for_id(pair['card']).read_bytes()))
        prepared = json.loads(path_for_id(pair['prepared']).read_bytes())
        if pair['family'] == 'C2':
            families.validate_active_c2_prepared(prepared)
        manifest = json.loads(path_for_id(pair['input_manifest']).read_bytes())
        raw_assets = original_source_assets(manifest, prepared)
        supplied = {asset['name']: registration['files'][asset['file']] for asset in pair['original_assets']}
        if set(raw_assets) != set(supplied):
            raise ValueError('benchmark_same_original_manifest_assets')
        image_files = set()
        for asset in pair['original_assets']:
            record = registration['files'][asset['file']]
            if (record.get('published_relative_path') != 'benchmark/' + pair['id'] + '/' + asset['name'] or
                    any(record[k] != raw_assets[asset['name']][k] for k in ('sha256', 'bytes'))):
                raise ValueError('benchmark_original_asset_identity')
            if raw_assets[asset['name']]['kind'] == 'image':
                image_files.add(asset['file'])
        if set(pair.get('original_images', [])) != image_files:
            raise ValueError('benchmark_all_original_images_required')
        for arm, prep in pair['preparation'].items():
            evidence = json.loads(path_for_id(prep['evidence']).read_bytes())
            if (evidence.get('schema') != 'cad-harness.benchmark-preparation.v1' or
                    evidence.get('pair') != pair['id'] or evidence.get('arm') != arm or
                    any(evidence.get(k) != prep[k] for k in ('preparation_intervals', 'native_cad_intervals', 'custody_hold_intervals', 'recorded_once', 'clock_id', 'active_s'))):
                raise ValueError('benchmark_preparation_evidence_mismatch')
            for key, intervals in (('utc_preparation_intervals', prep['preparation_intervals']),
                                   ('utc_custody_hold_intervals', prep['custody_hold_intervals'])):
                values = evidence.get(key)
                if not isinstance(values, list) or len(values) != len(intervals):
                    raise ValueError('benchmark_preparation_utc_coverage_required')
                for endpoints, interval in zip(values, intervals):
                    if not isinstance(endpoints, list) or len(endpoints) != 2:
                        raise ValueError('benchmark_preparation_utc_endpoints')
                    if endpoints[0] is None or (endpoints[1] is None) != (interval[1] is None):
                        raise ValueError('benchmark_prospective_hold_utc_binding')
                    parsed = [datetime.fromisoformat(v) for v in endpoints if v is not None]
                    if any(v.tzinfo is None for v in parsed):
                        raise ValueError('benchmark_preparation_timezone_required')
    demonstration = json.loads(path_for_id(registration['isolation_demonstration']).read_bytes())
    if (demonstration.get('schema') != 'cad-harness.bare-isolation-smoke.v1' or
            any(demonstration.get(k) is not True for k in ('lpac', 'zero_capabilities', 'child_denied',
                'network_denied', 'external_file_denied', 'repository_denied', 'inputs_read_only', 'acl_tamper_denied',
                'root_acl_tamper_denied', 'runtime_acl_tamper_denied', 'owner_tamper_denied', 'runtime_owner_tamper_denied',
                'inputs_rename_denied', 'root_owned_by_child_user', 'construction_file_ops', 'freecad_bootstrap_initialized',
                'source_security_unchanged', 'private_runtime_verified', 'setup_failure_restored',
                'shell_file_io', 'owned_timeout_cleanup', 'native_freecad', 'cleanup_restored',
                'owner_setup_and_temp_cleanup_restored'))):
        raise ValueError('benchmark_actual_os_demonstration_required')
    runtime_root = Path(registration['bare_runtime']['root'])
    if any(path_for_id(registration['bare_runtime'][key]).resolve().is_relative_to(runtime_root.resolve())
           for key in ('inventory', 'staging_proof')):
        raise ValueError('benchmark_staging_evidence_must_be_external')
    inventory = json.loads(path_for_id(registration['bare_runtime']['inventory']).read_bytes())
    staging = json.loads(path_for_id(registration['bare_runtime']['staging_proof']).read_bytes())
    bare.isolation.validate_staged_runtime(registration['bare_runtime']['root'], inventory, staging)
    smoke_inventory, smoke_staging = demonstration.get('runtime_inventory', {}), demonstration.get('runtime_staging_proof', {})
    # The independent smoke owns and deletes its own private copy. Bind its
    # complete source-equivalence and relocation evidence, not a nonexistent
    # claim that the smoke executed the later registered destination path.
    if (smoke_inventory.get('schema') != 'cad-harness.bare-runtime.v2' or
            any(smoke_inventory.get(k) != inventory.get(k) for k in ('source_root', 'source_python', 'files', 'directories')) or
            smoke_staging.get('schema') != 'cad-harness.bare-runtime-staging.v1' or
            smoke_staging.get('root') != smoke_inventory.get('root') or
            smoke_staging.get('source_python') != inventory.get('source_python') or
            smoke_staging.get('inventory_sha256') != digest(smoke_inventory) or
            smoke_staging.get('isolation_sha256') != bare.isolation.file_hash(Path(bare.isolation.__file__)) or
            demonstration.get('relocated_python') != str(Path(smoke_inventory.get('root', '')) / 'bin/python.exe') or
            demonstration.get('runtime_inventory_sha256') != digest(smoke_inventory) or
            demonstration.get('runtime_staging_proof_sha256') != digest(smoke_staging) or
            demonstration.get('native_smoke_sha256') != bare.isolation.file_hash(Path(bare.__file__).with_name('test_verify_v4_bare_windows_native.py'))):
        raise ValueError('benchmark_actual_staged_runtime_demonstration_required')
    if (demonstration.get('evidence_mode') != 'independent_dev' or demonstration.get('live_calls') != 0 or
            demonstration.get('boot_id') != registration['clocks']['boot_id'] or
            demonstration.get('isolation_sha256') != bare.isolation.file_hash(Path(bare.isolation.__file__)) or
            demonstration.get('supervisor_sha256') != bare.isolation.file_hash(Path(bare.__file__)) or
            demonstration.get('bootstrap_sha256') != bare.BOOTSTRAP_SHA256 or
            demonstration.get('python_sha256') != inventory.get('files', {}).get('bin/python.exe', {}).get('sha256')):
        raise ValueError('benchmark_current_boundary_demonstration_required')
    _validate_isolation_streams(demonstration)
    for human in registration['human_judges']:
        record = registration['files'][human['qualification_evidence']]
        qualification = json.loads(path_for_id(human['qualification_evidence']).read_bytes())
        if (record.get('role') != 'human_judge_identity' or
                qualification.get('schema') != 'cad-harness.benchmark-human-judge.v1' or
                qualification.get('id') != human['id'] or qualification.get('kind') != 'human' or
                not isinstance(qualification.get('qualification'), str) or not qualification['qualification'].strip()):
            raise ValueError('benchmark_human_judge_identity_evidence_required')
    _validate_adapter_demonstration(registration, path_for_id)
    _validate_store_retrieval(registration, path_for_id)
    return registration


def _validate_isolation_streams(proof):
    """Require retained actual source/streams and a nonce-bound bootstrap.

    These are execution receipts, not remote attestation; unit mocks and
    metadata-only PASS dictionaries cannot satisfy this admission contract.
    """
    try:
        source = base64.b64decode(proof['source_base64'], validate=True)
        if not source or hashlib.sha256(source).hexdigest() != proof['source_sha256']:
            raise ValueError('source_bytes')
        streams = {}
        for name in ('native_process', 'shell_process', 'timeout_process'):
            process = proof[name]
            if (process['isolation'] != 'windows_lpac_zero_capabilities' or
                    process['lpac_token_verified'] is not True or process['job_assigned'] is not True or
                    process['capability_count'] != 0 or process['job_child_limit'] != 1 or
                    process['cleanup_status'] != 'exited' or process['stdin'] != 'NUL'):
                raise ValueError('actual_owned_lpac_process')
            if process.get('lpac_token_evidence') != dict(schema='cad-harness.lpac-accesscheck.v1',
                    world_only_read=False, all_application_packages_read=False, own_package_read=True):
                raise ValueError('actual_lpac_accesscheck_controls')
            streams[name] = {key: base64.b64decode(process[key + '_base64'], validate=True) for key in ('stdout', 'stderr')}
        process = proof['native_process']
        if process['returncode'] != 0 or proof['shell_process']['returncode'] != 0:
            raise ValueError('native_or_shell_failed')
        for key, payload in streams['native_process'].items():
            record = process[key + '_record']
            if (hashlib.sha256(payload).hexdigest() != proof[key + '_sha256'] or
                    record['sha256'] != proof[key + '_sha256'] or record['bytes'] != len(payload)):
                raise ValueError('retained_native_stream_changed')
        command = proof['native_command']
        if (not isinstance(command, list) or len(command) != 8 or
                command[:6] != [proof['relocated_python'], '-I', '-B', '-u', '-c', bare.PYTHON_BOOTSTRAP] or
                command[7] != 'build.py' or not isinstance(command[6], str) or len(command[6]) != 32 or
                any(c not in '0123456789abcdef' for c in command[6])):
            raise ValueError('actual_bootstrap_command')
        prefix = (bare.HOST_INIT_PREFIX + command[6] + ':').encode('ascii')
        initialized = [json.loads(line[len(prefix):]) for line in streams['native_process']['stderr'].splitlines() if line.startswith(prefix)]
        expected = dict(schema='freecad.host-init.v1', version=['1', '1', '4'], gui_up=False)
        if initialized != [expected] or process['initialization'] != dict(expected, bootstrap_sha256=bare.BOOTSTRAP_SHA256):
            raise ValueError('actual_bootstrap_stream')
        markers = [json.loads(line[len(b'BARE_DEV_RESULT='):]) for line in streams['native_process']['stdout'].splitlines()
                   if line.startswith(b'BARE_DEV_RESULT=')]
        child_checks = ('external_file_denied', 'repository_denied', 'inputs_read_only', 'acl_tamper_denied',
                        'root_acl_tamper_denied', 'runtime_acl_tamper_denied', 'owner_tamper_denied',
                        'runtime_owner_tamper_denied', 'inputs_rename_denied', 'root_owned_by_child_user',
                        'construction_file_ops', 'child_denied', 'network_denied', 'native_freecad')
        if (len(markers) != 1 or any(markers[0].get(key) is not True or proof.get(key) is not True for key in child_checks) or
                b'DEV_SHELL_OK' not in streams['shell_process']['stdout']):
            raise ValueError('actual_containment_outputs')
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('benchmark_actual_retained_isolation_source_streams_required:' + str(exc)) from exc
    return proof


def _validate_adapter_demonstration(registration, path_for_id):
    proof = json.loads(path_for_id(registration['adapter_demonstration']).read_bytes())
    card_hash = proof.get('same_card_sha256')
    if (proof.get('schema') != 'cad-harness.benchmark-adapter-demonstration.v1' or
            proof.get('evidence_mode') != 'independent_dev' or proof.get('actual_native') is not True or
            type(proof.get('live_calls')) is not int or proof['live_calls'] != 0 or
            proof.get('profile') not in ('c-s1', 'c-s2', 'c-s3') or
            not isinstance(card_hash, str) or len(card_hash) != 64 or any(c not in '0123456789abcdef' for c in card_hash) or
            set(proof.get('methods', {})) != {'ordinary', 'with_harness'}):
        raise ValueError('benchmark_actual_neutral_adapter_demonstration_required')
    expected = _module('cad_verify_v4_s1').implementation_bindings(profile=proof['profile'])
    schema = json.loads(_module('cad_verify_v4_artifacts').SCHEMA.read_bytes())
    shared_inputs = None
    for method, entry in proof['methods'].items():
        for key in ('check', 'bundle'):
            if (entry.get(key) not in registration['files'] or
                    registration['files'][entry[key]].get('origin') != 'operational' or
                    registration['files'][entry[key]].get('role') != 'adapter_demonstration'):
                raise ValueError('benchmark_adapter_demonstration_file_binding')
        summary = json.loads(path_for_id(entry['check']).read_bytes())
        bundle = json.loads(path_for_id(entry['bundle']).read_bytes())
        _module('cad_verify_v4_plans')._check(bundle, schema, schema, 'adapter_demonstration_bundle')
        result = summary.get('result', {})
        evidence = result.get('native_evidence', {})
        if (summary.get('schema') != 'cad-harness.artifact-check.v4' or
                summary.get('evidence_mode') != 'independent_dev' or summary.get('status') != 'PASS' or
                summary.get('native_work') != 1 or summary.get('live_calls') != 0 or
                result.get('status') != 'PASS' or result.get('profile') != proof['profile'] or
                result.get('geometry_ok') is not True or result.get('editability_ok') is not True or
                evidence.get('fcstd_reopened') is not True or evidence.get('step_reopened') is not True or
                evidence.get('editable') is not True or result.get('code_bindings') != expected):
            raise ValueError('benchmark_current_native_adapter_evidence_required')
        bindings = result.get('bindings', {})
        inputs = {key: bindings.get(key + '_sha256') for key in ('manifest', 'prepared', 'card', 'context')}
        if (bindings.get('card_sha256') != card_hash or
                bindings.get('bundle_sha256') != registration['files'][entry['bundle']]['sha256'] or
                any(not isinstance(value, str) or len(value) != 64 for value in inputs.values()) or
                shared_inputs is not None and inputs != shared_inputs):
            raise ValueError('benchmark_adapter_same_card_and_inputs_required')
        shared_inputs = inputs
        if bundle['profile'] != proof['profile'] or bundle['evidence_mode'] != 'independent_dev':
            raise ValueError('benchmark_adapter_bundle_schema')
        if method == 'ordinary' and bundle['extensions']:
            raise ValueError('benchmark_ordinary_adapter_cannot_require_python_restoration')
        for extension in bundle['extensions']:
            module = {'c-s1': 'cad_verify_v4_compile', 'c-s2': 'cad_verify_v4_s2_edit',
                      'c-s3': 'cad_verify_v4_s3_rebuild'}[proof['profile']]
            if extension['module'] != 'tools.' + module or extension['sha256'] != expected.get('tools/' + module + '.py'):
                raise ValueError('benchmark_adapter_unfrozen_restoration_dependency')
        for key in ('native', 'step'):
            if any(result.get('artifacts', {}).get(key, {}).get(field) != bundle[key][field]
                   for field in ('sha256', 'bytes')):
                raise ValueError('benchmark_adapter_artifact_binding')
    index_id = proof.get('hash_index')
    files = registration['files']
    if (index_id not in files or files[index_id].get('origin') != 'operational' or
            files[index_id].get('role') != 'adapter_demonstration'):
        raise ValueError('benchmark_adapter_raw_hash_index_required')
    index = json.loads(path_for_id(index_id).read_bytes())
    if (index.get('schema') != 'cad-harness.benchmark-adapter-index.v1' or
            index.get('live_calls') != 0 or not isinstance(index.get('files'), dict) or not index['files']):
        raise ValueError('benchmark_adapter_raw_hash_index_required')
    prefix = Path(files[index_id]['path']).parent
    for relative, expected_file in index['files'].items():
        logical_path = prefix.joinpath(*bare._relative(relative).parts).as_posix()
        matches = [key for key, value in files.items() if Path(value['path']).as_posix() == logical_path]
        if len(matches) != 1:
            raise ValueError('benchmark_adapter_raw_file_registration_required')
        actual = bare._record(path_for_id(matches[0]))
        if (files[matches[0]].get('role') != 'adapter_demonstration' or
                any(actual[key] != expected_file.get(key) for key in ('sha256', 'bytes'))):
            raise ValueError('benchmark_adapter_raw_file_hash_mismatch')
    return proof


def validate_durability(registration):
    store = registration.get('durability', {})
    if any(not isinstance(store.get(k), str) or not store[k] for k in ('store_id', 'location', 'retention', 'backup_location', 'versioning', 'custodian')):
        raise ValueError('benchmark_registered_backed_up_store_required')
    if store['location'] == store['backup_location'] or store.get('immutable') is not True:
        raise ValueError('benchmark_independent_immutable_backup_required')
    files = registration.get('files', {})
    for key in ('provisioning_evidence', 'retrieval_proof'):
        if store.get(key) not in files:
            raise ValueError('benchmark_durability_hash_proof_required')
    return store


def _validate_store_retrieval(registration, path_for_id, *, forbidden_root=None):
    """Retrieve the registered immutable probe from BOTH stores before release.

    Stores are mounted filesystem/UNC destinations, not a local reports label.
    Offline operation intentionally does not implement network credential clients.
    The custodian's approved provisioning/retention proof is hash-bound by auth.
    """
    store = validate_durability(registration)
    provisioning = json.loads(path_for_id(store['provisioning_evidence']).read_bytes())
    if (provisioning.get('schema') != 'cad-harness.benchmark-store-registration.v1' or
            any(provisioning.get(k) != store[k] for k in ('store_id', 'location', 'backup_location', 'retention', 'immutable', 'versioning')) or
            not provisioning.get('approved_by')):
        raise ValueError('benchmark_custody_provisioning_not_verified')
    proof = json.loads(path_for_id(store['retrieval_proof']).read_bytes())
    if proof.get('schema') != 'cad-harness.benchmark-custody-proof.v1' or proof.get('store_id') != store['store_id']:
        raise ValueError('benchmark_custody_proof_identity')
    relative = bare._relative(proof['probe']['path'])
    locations = [Path(store[k]).absolute() for k in ('location', 'backup_location')]
    if any(part.casefold() in ('v4-holdout-private', 'pilot-user') for path in locations for part in path.parts):
        raise ValueError('benchmark_store_outside_private_input_scopes_required')
    reports = Path(__file__).resolve().parents[1] / 'reports'
    forbidden = [reports] + ([Path(forbidden_root).absolute()] if forbidden_root is not None else [])
    if locations[0] == locations[1] or any(p == root or p.is_relative_to(root) or root.is_relative_to(p) for p in locations for root in forbidden):
        raise ValueError('benchmark_reports_are_not_durable_custody')
    for location in locations:
        path = bare.scoped(location, relative.as_posix())
        if not path.is_file() or path.stat().st_size != proof['probe']['bytes'] or bare.isolation.file_hash(path) != proof['probe']['sha256']:
            raise ValueError('benchmark_store_retrieval_hash_failed')
    return locations, proof


def verify_durability(session):
    locations, proof = _validate_store_retrieval(session.registration, session.path, forbidden_root=session.out)
    store = session.registration['durability']
    session.event('durable_custody_verified', store_id=store['store_id'], locations=[str(p) for p in locations],
                  proof=bare._record(session.path(store['retrieval_proof'])), probe=proof['probe'])
    return locations


class Events:
    """Canonical append-only, hash-linked event stream and regenerable index."""
    def __init__(self, path, session):
        self.path, self.session, self.hash, self.count = Path(path), session, '0' * 64, 0
        self.handle = self.path.open('xb')

    def append(self, kind, **fields):
        self.count += 1
        event = dict(schema=SCHEMA, kind=kind, sequence=self.count, previous_sha256=self.hash,
                     trial_id=self.session.registration['trial_id'], utc=datetime.now(timezone.utc).isoformat(),
                     monotonic=self.session.wall(), **fields)
        self.hash = digest(event)
        self.handle.write(canonical(dict(event, sha256=self.hash)) + b'\n')
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.session.event('benchmark_' + kind, benchmark_event_sha256=self.hash, **fields)

    def close(self):
        self.handle.close()


def measured(preparation, start, end, active_s, native_intervals):
    prep = preparation['preparation_intervals']
    prospective = preparation['custody_hold_intervals']
    holds = _intervals([[a, start if b is None else b] for a, b in prospective])
    if any(stop > start for _, stop in prep + holds):
        raise ValueError('benchmark_prefreeze_interval_after_release')
    first = min([start] + [a for a, _ in prep + holds])
    full = end - first
    native_intervals = preparation['native_cad_intervals'] + native_intervals
    return dict(full_wall_s=full, service_s=full - union(holds),
                active_s=active_s + preparation['active_s'], native_cad_s=union(native_intervals),
                operation_intervals=[[start, end]], preparation_intervals=prep, custody_hold_intervals=holds,
                prospective_custody_hold_intervals=prospective,
                native_cad_intervals=native_intervals, full_wall_interval=[first, end],
                human_active_s={'value': None, 'reason': 'not_applicable'},
                kernel_cpu_s={'value': None, 'reason': 'not_measured'})


def savings(with_record, bare_record):
    result = {}
    for metric in METRICS:
        if not with_record['qualified_completion'] or not bare_record['qualified_completion']:
            result[metric] = {'saving': None, 'reduction_percent': None, 'reason': 'censored_or_unqualified_completion'}
            continue
        before, after = bare_record['timing'].get(metric), with_record['timing'].get(metric)
        if before is None or after is None:
            result[metric] = {'saving': None, 'reduction_percent': None, 'reason': 'missing_matched_metric'}
        elif before == 0:
            result[metric] = {'saving': None, 'reduction_percent': None, 'reason': 'zero_baseline'}
        else:
            result[metric] = {'saving': before - after, 'reduction_percent': 100 * (before - after) / before, 'reason': None}
    return result


def _failed(reason, status='not_run'):
    return dict(status=status, reason=reason, qualified_completion=False, completion_time_s=None, completion_time_reason=reason,
                right_censored=True, timing={metric: None for metric in METRICS}, first_handover=None,
                final_handover=None, construction_operator={'value': None, 'reason': 'not_applicable'},
                human_engineering_time={'value': None, 'reason': 'not_applicable'})


def _completion_reason(record):
    if record['qualified_completion']:
        return None
    construction = record.get('construction_status', record['status'])
    if construction not in ('PASS', 'submitted'):
        return record.get('reason') or construction
    if record.get('deterministic', {}).get('status') != 'PASS':
        return 'deterministic_construction_not_qualified'
    if record.get('judge', {}).get('status') != 'PASS':
        return 'adjudication_not_qualified'
    adoption = record.get('adoption', {})
    if adoption.get('critical_error_ever') is True:
        return 'irreversible_critical_or_fabrication_history'
    if adoption.get('status') == 'refused':
        return 'external_human_refused'
    if adoption.get('status') in (None, 'unknown'):
        return 'actual_human_verdict_not_recorded'
    if adoption.get('critical_error_ever') is None:
        return 'external_human_critical_observation_unknown'
    return 'correction_or_adoption_not_qualified'


def _condition_record(events, record):
    unverified = record.get('execution', {}).get('unverified_python_host_intervals', [])
    if unverified:
        if record['timing'].get('native_cad_s') is not None:
            record['timing']['observed_initialized_native_host_s'] = record['timing']['native_cad_s']
        record['timing']['native_cad_s'] = None
    record['completion_time_reason'] = _completion_reason(record)
    record['timing_missing_reasons'] = {metric: record.get('reason') or 'not_observed'
                                      for metric in METRICS if record['timing'].get(metric) is None}
    if unverified:
        record['timing_missing_reasons']['native_cad_s'] = 'pinned_freecad_host_initialization_unverified'
    events.append('condition_record', **record)


def _qualified(deterministic, judge, adoption):
    result = deterministic.get('result', deterministic)
    # Astra cannot override failed geometry, editability or irreversible critical history.
    return (deterministic.get('status') == 'PASS' and result.get('geometry_ok') is True
            and result.get('editability_ok') is True and judge.get('status') == 'PASS'
            and adoption.get('status') == 'adopted' and adoption.get('critical_error_ever') is False)


def _evidence_files(root):
    """Do not dereference a generated junction/link while sealing as custodian."""
    pending, files, quarantined = [Path(root)], [], []
    while pending:
        for path in pending.pop().iterdir():
            info = path.lstat()
            if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                quarantined.append(dict(path=path.relative_to(root).as_posix(), reason='reparse_not_dereferenced'))
            elif path.is_dir():
                pending.append(path)
            elif path.is_file() and info.st_nlink == 1:
                files.append(path)
            else:
                quarantined.append(dict(path=path.relative_to(root).as_posix(), reason='nonregular_or_hardlinked_not_read'))
    if quarantined:
        path = Path(root) / 'quarantined-files.json'
        with path.open('xb') as handle:
            handle.write(canonical({'schema': 'cad-harness.benchmark-quarantine.v1', 'files': quarantined}))
        files.append(path)
    return files


def _publish(session, events, locations, *, revision=None):
    out = session.out
    # Every raw stream and native/source artifact is included, not only the summary.
    index = {p.relative_to(out).as_posix(): bare._record(p) for p in _evidence_files(out)}
    for record in index.values():
        record.pop('path')
    value = dict(schema=SCHEMA, trial_id=session.registration['trial_id'], event_prefix_sha256=events.hash,
                 files=index, event_count=events.count)
    if revision is not None:
        value['revision'] = revision
    index_path = out / 'hash-index.json'
    index_path.write_bytes(canonical(value))
    destination_name = session.registration['trial_id'] + ('-human-' + revision if revision is not None else '')
    locations = [p / destination_name for p in locations]
    receipts = []
    for destination in locations:
        destination.mkdir(parents=True, exist_ok=False)
        for relative in [*index, 'hash-index.json']:
            source, target = out / relative, destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as read, target.open('xb') as write:
                shutil.copyfileobj(read, write)
                write.flush()
                os.fsync(write.fileno())
            if source.stat().st_size != target.stat().st_size or bare.isolation.file_hash(source) != bare.isolation.file_hash(target):
                raise OSError('benchmark_durable_bundle_retrieval_failed:' + relative)
        receipts.append({'location': str(destination), 'hash_index_sha256': bare.isolation.file_hash(destination / 'hash-index.json')})
    receipt = dict(schema='cad-harness.benchmark-custody-receipt.v1', status='retrieved_hash_verified',
                   stores=receipts, retention=session.registration['durability']['retention'],
                   provisioning_evidence=session.registration['durability']['provisioning_evidence'])
    receipt_path = out / 'custody-receipt.json'
    with receipt_path.open('xb') as handle:
        handle.write(canonical(receipt))
        handle.flush()
        os.fsync(handle.fileno())
    for destination in locations:
        with (destination / receipt_path.name).open('xb') as handle:
            handle.write(receipt_path.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        if bare.isolation.file_hash(destination / receipt_path.name) != bare.isolation.file_hash(receipt_path):
            raise OSError('benchmark_custody_receipt_retrieval_failed')
    return receipt


def _native_ranges(values):
    return [[v['start'], v['end']] if isinstance(v, dict) else list(v) for v in values]


def _retain_preregistration(session):
    """Seal the actual authorization/index/implementation identities, not paths."""
    root = session.out / 'preregistration'
    root.mkdir(exist_ok=False)
    sources = {'execution-manifest': Path(session.manifest_path)}
    for key in ('registration', 'authorization', 'integrated_lock'):
        record = session.manifest[key]
        source = Path(record['path'])
        if source.stat().st_size != record['bytes'] or bare.isolation.file_hash(source) != record['sha256']:
            raise ValueError('benchmark_preregistration_binding_changed:' + key)
        sources[key] = source
    retained = {}
    for name, source in sources.items():
        before = bare._record(source)
        target = root / (name + '.json')
        with source.open('rb') as read, target.open('xb') as write:
            shutil.copyfileobj(read, write)
        after = bare._record(target)
        if any(before[k] != after[k] for k in ('sha256', 'bytes')) or bare.isolation.file_hash(source) != before['sha256']:
            raise ValueError('benchmark_preregistration_copy_changed:' + name)
        retained[name] = after
    session.event('benchmark_preregistration_retained', files=retained)
    return retained


def run(manifest_path, authorization_path, run_dir, *, process=None, native_process=None, wall=None, sleep=None, verifier=None):
    trials = _module('cad_verify_v4_trials')
    with trials.TrialSession(manifest_path, authorization_path, run_dir, phase='benchmark', process=process,
                             native_process=native_process, wall=wall, sleep=sleep, verifier=verifier) as session:
        registration = validate_bound_inputs(session.registration, session.path)
        if session.mode == 'live':
            if (registration['clocks']['boot_id'] != bare.isolation.boot_id() or
                    registration['clocks']['resolution_s'] != time.get_clock_info('monotonic').resolution):
                raise ValueError('benchmark_current_boot_or_timer_mismatch')
        locations = verify_durability(session)
        _retain_preregistration(session)
        # Validate the complete frozen offline runtime before any model invocation.
        bare.validate_runtime(session, registration['bare_runtime'])
        events = Events(session.out / 'benchmark-events.jsonl', session)
        records = {(p['id'], arm): dict(pair=p['id'], arm=arm, family=p['family'], stratum=p['stratum'],
                   agent_session_id=registration['trial_id'] + ':' + p['id'] + ':' + arm,
                   generator={'model': bare.MODEL, 'thinking': bare.THINKING}, **_failed('not_started'))
                   for p in registration['pairs'] for arm in ARMS}
        by_id = {p['id']: p for p in registration['pairs']}
        fatal_stop = None
        try:
            events.append('enrolled', order=registration['order'], reservations=RESERVATIONS,
                          clocks=registration['clocks'], comparison='harness-versus-bare-agent',
                          preparation={p['id']: p['preparation'] for p in registration['pairs']})
            for slot in registration['order']:
                pair, arm = by_id[slot['pair']], slot['arm']
                record = records[(pair['id'], arm)]
                if fatal_stop is not None:
                    record['reason'] = fatal_stop
                    _condition_record(events, record)
                    continue
                out = session.out / (pair['id'] + '-' + arm)
                started, active_started = session.wall(), session.clock()
                native_begin = len(session.native_cad_intervals)
                execution, stopped, active_stopped = None, None, None
                deterministic, judge = None, None
                events.append('arm_started', pair=pair['id'], arm=arm)
                try:
                    session.check()
                    prep = pair['preparation'][arm]
                    remaining = lambda: 1200 - prep['active_s'] - (session.clock() - active_started)
                    if remaining() <= 0:
                        raise TimeoutError('benchmark_preparation_exhausted_active_budget')
                    if arm == 'with_harness':
                        execution = session.execute_plan(pair, out, pool='with_harness:generation', model=bare.MODEL,
                            thinking=bare.THINKING, max_calls=3, active_limit=remaining())
                        deterministic = execution.get('artifact_verdict')
                        if not isinstance(deterministic, dict):
                            deterministic = {'status': 'UNVERIFIED', 'reason': 'missing_neutral_artifact_verdict'}
                    else:
                        execution = bare.construct(session, pair, out, active_limit=remaining())
                        if execution.get('status') == 'interrupted':
                            raise KeyboardInterrupt(execution.get('reason'))
                        correction = len(execution.get('handovers', [])) > 1
                        check_remaining = lambda: min(remaining(),
                            300 - (session.wall() - execution['first_handover']['at_wall']) if correction else math.inf)
                        handover_checks = []
                        for index, handover in enumerate(execution.get('handovers', [])):
                            if check_remaining() <= 0:
                                raise TimeoutError('benchmark_active_or_correction_limit')
                            checked = bare.check_artifacts(session, pair, handover['artifact_bundle'],
                                out / ('check-%d' % index), timeout=check_remaining())
                            handover_checks.append(dict(handover=handover, verdict=checked))
                        deterministic = handover_checks[-1]['verdict'] if handover_checks else {'status': 'UNVERIFIED', 'reason': 'no_handover'}
                        execution['handover_checks'] = handover_checks
                    images = execution.get('images', ())
                    if arm == 'bare' and deterministic.get('status') == 'PASS':
                        images = session.capture_images(pair, execution, out / 'evidence-images', timeout=check_remaining())
                    stopped, active_stopped = session.wall(), session.clock()
                    if remaining() < 0:
                        raise TimeoutError('benchmark_active_limit')
                    if arm == 'bare' and correction:
                        execution['correction'] = dict(elapsed_s=stopped - execution['first_handover']['at_wall'],
                                                       verified_within_300_s=check_remaining() >= 0)
                        if check_remaining() < 0:
                            raise TimeoutError('benchmark_correction_elapsed_300_s')
                    history = execution.get('handover_checks', execution.get('handover_history', []))
                    if not history and execution.get('first_handover'):
                        history = [{'handover': execution['first_handover']}]
                    deterministic = dict(status=deterministic.get('status', 'UNVERIFIED'),
                                         result=deterministic.get('result', deterministic),
                                         handover_history=history)
                    # One Astra judgment per condition, including a failed/unsubmitted condition.
                    judge = session.judge(pair['id'] + ':' + arm, session.path(pair['request']).read_bytes().decode('utf-8'),
                        deterministic, json.loads(session.path(registration['rubric']).read_bytes()),
                        pool='benchmark:judge', images=images)
                    native_ranges = _native_ranges(session.native_cad_intervals[native_begin:])
                    if arm == 'bare':
                        native_ranges += execution.get('native_cad_intervals', [])
                    timing = measured(prep, started, stopped, active_stopped - active_started, native_ranges)
                    timing['active_budget_interval'] = [active_started, active_stopped]
                    timing['observed_time_to_stop_s'] = timing['full_wall_s']
                    # Human adoption remains separate; without an actual verdict it is unknown.
                    adoption = {'status': 'unknown', 'critical_error_ever': None, 'reason': 'actual_human_verdict_not_recorded'}
                    qualified = (execution.get('status') in ('PASS', 'submitted') and
                                 _qualified(deterministic, judge, adoption))
                    construction_status = execution.get('status', 'UNVERIFIED')
                    overall = ('FAIL' if deterministic.get('status') == 'FAIL' or judge.get('status') == 'FAIL' else 'UNVERIFIED')
                    record.update(status=overall if construction_status in ('PASS', 'submitted') else construction_status,
                        construction_status=construction_status, reason=execution.get('reason'),
                        timing=timing, deterministic=deterministic, judge=judge, adoption=adoption,
                        execution=execution, qualified_completion=qualified,
                        completion_time_s=timing['full_wall_s'] if qualified else None,
                        right_censored=not qualified, first_handover=execution.get('first_handover'),
                        final_handover=execution.get('final_handover', execution.get('first_handover')))
                except (Exception, KeyboardInterrupt) as exc:
                    reason = type(exc).__name__ + ':' + str(exc)
                    if stopped is None:
                        stopped, active_stopped = session.wall(), session.clock()
                    error_status = ('timed_out' if isinstance(exc, TimeoutError) else
                                    'interrupted' if isinstance(exc, KeyboardInterrupt) else 'error')
                    if execution is None:
                        record.update(_failed(reason, error_status))
                    native_ranges = _native_ranges(session.native_cad_intervals[native_begin:])
                    if execution is not None:
                        actual_status = execution.get('status', error_status)
                        primary = execution.get('reason') or execution.get('error')
                        primary = primary if isinstance(primary, str) or primary is None else canonical(primary).decode('utf-8')
                        record.update(status=actual_status if actual_status not in ('PASS', 'submitted') else error_status,
                                      construction_status=actual_status, reason=primary or reason,
                                      secondary_stop_reason=reason, qualified_completion=False, right_censored=True,
                                      completion_time_s=None, execution=execution,
                                      first_handover=execution.get('first_handover'),
                                      final_handover=execution.get('final_handover', execution.get('first_handover')))
                        if deterministic is not None:
                            record['deterministic'] = deterministic
                        if judge is not None:
                            record['judge'] = judge
                        if arm == 'bare':
                            native_ranges += execution.get('native_cad_intervals', [])
                    record['timing'] = measured(pair['preparation'][arm], started, stopped,
                                               active_stopped - active_started, native_ranges)
                    record['timing']['active_budget_interval'] = [active_started, active_stopped]
                    record['timing']['observed_time_to_stop_s'] = record['timing']['full_wall_s']
                    # Admission/quota/source/capture failure prevents further releases, never substitutions.
                    if getattr(session, 'fatal', None) is not None or not isinstance(exc, (ValueError, TimeoutError)):
                        fatal_stop = reason
                _condition_record(events, record)
            rows = [records[(slot['pair'], slot['arm'])] for slot in registration['order']]
            paired = [dict(pair=p['id'], family=p['family'], savings=savings(records[(p['id'], 'with_harness')], records[(p['id'], 'bare')])) for p in registration['pairs']]
            runtime = session.summary()
            status = ('not_run' if runtime.get('logical_calls') == 0 and runtime.get('physical_attempts') == 0 else
                      'awaiting_human_verdicts' if any(r.get('deterministic', {}).get('status') == 'PASS'
                        and r.get('judge', {}).get('status') == 'PASS' for r in rows) else 'completed_with_enrolled_outcomes')
            dataset = dict(schema=SCHEMA, trial_id=registration['trial_id'], comparison='harness-versus-bare-agent',
                status=status, evidence_mode=session.mode,
                conditions=rows, pairs=paired, event_prefix_sha256=events.hash,
                enrolled_pairs=20, enrolled_conditions=40,
                measurement_definitions={'native_cad_s':
                    'Union wall of owned initialized pinned FreeCAD/Python HOST PROCESS invocations, '
                    'from supervisor launch through owned cleanup; includes imports, preprocessing, '
                    'self-checks and native verification/rendering, not kernel work or CPU time.',
                    'shell_file_io': 'Separate broker/tool wall intervals; not native CAD host time.',
                    'human_construction': 'Not applicable; no human-time savings are claimed.'},
                qualified_conditions=sum(r['qualified_completion'] for r in rows),
                censored_conditions=sum(r['right_censored'] for r in rows),
                per_arm={arm: {'enrolled': 20, 'qualified': sum(r['qualified_completion'] for r in rows if r['arm'] == arm),
                              'success_rate': sum(r['qualified_completion'] for r in rows if r['arm'] == arm) / 20} for arm in ARMS},
                limitations=['Human verdicts are not synthesized; adoption-dependent completion remains censored until actual verdicts exist.',
                             'Complete-pair statistics are conditional, not population productivity or human hours saved.',
                             'Provider/cache/context/preparation/workflow differences remain.'], runtime=session.summary())
            events.append('dataset_sealed', dataset_sha256=digest(dataset))
        finally:
            events.close()
        _write_dataset(session.out, dataset)
    # TrialSession has now appended run_finished and closed its journal. Every
    # published file is immutable evidence, never an open-ledger snapshot.
    custody = _publish(session, events, locations)
    summary = dict(schema=SCHEMA, dataset=str(session.out / 'dataset.json'), custody=custody,
                   status=dataset['status'], enrolled_pairs=20, enrolled_conditions=40,
                   qualified_conditions=dataset['qualified_conditions'], runtime=session.summary())
    (session.out / 'benchmark-summary.json').write_bytes(canonical(summary))
    return summary


def _write_dataset(out, dataset):
    with (Path(out) / 'dataset.json').open('xb') as handle:
        handle.write(canonical(dataset))
    with (Path(out) / 'conditions.csv').open('x', encoding='utf-8', newline='') as handle:
        keys = ['pair', 'arm', 'family', 'stratum', 'status', 'reason', 'qualified_completion', 'right_censored', 'completion_time_reason']
        writer = csv.DictWriter(handle, fieldnames=[*keys, *METRICS])
        writer.writeheader()
        for row in dataset['conditions']:
            writer.writerow({**{k: row[k] for k in keys}, **{m: row['timing'].get(m) for m in METRICS}})
    with (Path(out) / 'pairs.csv').open('x', encoding='utf-8', newline='') as handle:
        fields = ['pair', 'family', *[m + '_' + key for m in METRICS for key in ('saving', 'reduction_percent', 'reason')]]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in dataset['pairs']:
            writer.writerow({'pair': row['pair'], 'family': row['family'],
                             **{m + '_' + key: row['savings'][m][key] for m in METRICS
                                for key in ('saving', 'reduction_percent', 'reason')}})


def _metadata_path(value):
    path = Path(value).absolute()
    if any(part.casefold() in ('v4-holdout-private', 'pilot-user') for part in path.parts):
        raise ValueError('benchmark_external_metadata_scope')
    return bare.scoped(path.parent, path.name)


def _sealed_run(run_dir):
    """Verify a sealed local/retrieved bundle and both immutable custody indexes."""
    root = Path(run_dir).absolute()
    index_path = _metadata_path(root / 'hash-index.json')
    index = json.loads(index_path.read_bytes())
    if index.get('schema') != SCHEMA or not isinstance(index.get('files'), dict):
        raise ValueError('benchmark_sealed_index_required')
    for relative, record in index['files'].items():
        path = bare.scoped(root, relative)
        actual = bare._record(path) if path.is_file() else {}
        if any(actual.get(key) != record[key] for key in ('sha256', 'bytes')):
            raise ValueError('benchmark_sealed_evidence_changed:' + relative)
    required = ['dataset.json', 'benchmark-events.jsonl', 'preregistration/execution-manifest.json',
                'preregistration/registration.json', 'preregistration/authorization.json', 'preregistration/integrated_lock.json']
    if not set(required) <= set(index['files']):
        raise ValueError('benchmark_complete_preregistration_custody_required')
    dataset = json.loads((root / 'dataset.json').read_bytes())
    registration = json.loads((root / 'preregistration/registration.json').read_bytes())
    validate_registration(registration)
    manifest = json.loads((root / 'preregistration/execution-manifest.json').read_bytes())
    for key in ('registration', 'authorization', 'integrated_lock'):
        record = index['files']['preregistration/' + key + '.json']
        if any(manifest[key][field] != record[field] for field in ('sha256', 'bytes')):
            raise ValueError('benchmark_sealed_authority_binding')
    if dataset.get('trial_id') != registration['trial_id'] or dataset.get('evidence_mode') not in ('live', 'unit_mock'):
        raise ValueError('benchmark_sealed_trial_identity')
    authorization = json.loads((root / 'preregistration/authorization.json').read_bytes())
    if dataset['evidence_mode'] == 'live' and (
            authorization.get('user_approved') is not True or not authorization.get('approved_by') or
            authorization.get('registration_sha256') != manifest['registration']['sha256'] or
            authorization.get('integrated_manifest_sha256') != manifest['integrated_lock']['sha256']):
        raise ValueError('benchmark_sealed_approved_authority_required')
    receipt = json.loads(_metadata_path(root / 'custody-receipt.json').read_bytes())
    if receipt.get('status') != 'retrieved_hash_verified' or len(receipt.get('stores', [])) != 2:
        raise ValueError('benchmark_sealed_custody_receipt_required')
    local_hash = bare.isolation.file_hash(index_path)
    expected_locations = [Path(registration['durability'][key]).absolute() / registration['trial_id']
                          for key in ('location', 'backup_location')]
    if [Path(r['location']).absolute() for r in receipt['stores']] != expected_locations:
        raise ValueError('benchmark_custody_location_binding')
    for record in receipt['stores']:
        stored = _metadata_path(Path(record['location']) / 'hash-index.json')
        if record['hash_index_sha256'] != local_hash or bare.isolation.file_hash(stored) != local_hash:
            raise ValueError('benchmark_sealed_custody_index_changed')
    return root, registration, dataset, index


def _bundle_sha(condition):
    handover = condition.get('final_handover') or condition.get('first_handover') or {}
    return handover.get('bundle', {}).get('sha256') or handover.get('artifact_bundle_sha256')


def _fatal(value):
    if isinstance(value, dict):
        return (any(value.get(key) is True for key in ('critical_dimension_error', 'fabrication', 'critical_error')) or
                any(_fatal(item) for item in value.values()))
    return isinstance(value, list) and any(_fatal(item) for item in value)


def _validate_user_verdict(dataset, registration, verdict):
    expected = {'schema', 'trial_id', 'dataset_sha256', 'condition', 'artifact_bundle_sha256', 'judge_id',
                'source', 'status', 'observed_at', 'critical_dimension_error', 'fabrication',
                'first_handover_reviewed', 'evidence_sha256'}
    if (not isinstance(verdict, dict) or set(verdict) != expected or
            verdict['schema'] != 'cad-harness.benchmark-user-verdict.v1' or
            verdict['source'] != 'external_human' or verdict['status'] not in ('adopted', 'refused', 'UNVERIFIED')):
        raise ValueError('benchmark_external_human_verdict_structure')
    if verdict['trial_id'] != dataset['trial_id'] or verdict['dataset_sha256'] != digest(dataset):
        raise ValueError('benchmark_human_verdict_dataset_binding')
    conditions = {row['pair'] + ':' + row['arm']: row for row in dataset['conditions']}
    if verdict['condition'] not in conditions:
        raise ValueError('benchmark_human_verdict_unenrolled_condition')
    if verdict['judge_id'] not in {h['id'] for h in registration['human_judges']}:
        raise ValueError('benchmark_unregistered_human_identity')
    observed = datetime.fromisoformat(verdict['observed_at'])
    if observed.tzinfo is None or any(type(verdict[k]) is not bool and verdict[k] is not None
        for k in ('critical_dimension_error', 'fabrication', 'first_handover_reviewed')):
        raise ValueError('benchmark_human_verdict_observation_required')
    if (not isinstance(verdict['evidence_sha256'], str) or len(verdict['evidence_sha256']) != 64 or
            any(c not in '0123456789abcdef' for c in verdict['evidence_sha256'])):
        raise ValueError('benchmark_human_evidence_hash_required')
    condition = conditions[verdict['condition']]
    expected_bundle = _bundle_sha(condition)
    if verdict['artifact_bundle_sha256'] != expected_bundle:
        raise ValueError('benchmark_human_verdict_artifact_binding')
    if verdict['status'] == 'adopted' and (expected_bundle is None or verdict['first_handover_reviewed'] is not True):
        raise ValueError('benchmark_human_review_of_actual_handovers_required')
    return condition


def _human_intake(root):
    return bare.scoped(root.parent, root.name + '.human-receipts')


def _human_store_paths(registration, condition):
    name = condition.replace(':', '-')
    return [_metadata_path(Path(registration['durability'][key]) /
            (registration['trial_id'] + '-human-intake') / name) for key in ('location', 'backup_location')]


def record_user_verdict(run_dir, verdict_path, evidence_path):
    """One external human receipt per enrolled condition; no replacement/rescore.

    Intake is a sibling of the sealed run, never a mutation of its hash index.
    It performs no construction, CAD, model call or inferred human judgment.
    """
    root, registration, dataset, index = _sealed_run(run_dir)
    verdict_path, evidence_path = map(_metadata_path, (verdict_path, evidence_path))
    verdict_raw = verdict_path.read_bytes()
    verdict = json.loads(verdict_raw)
    _validate_user_verdict(dataset, registration, verdict)
    evidence = bare._record(evidence_path)
    if evidence['bytes'] <= 0 or evidence['sha256'] != verdict['evidence_sha256']:
        raise ValueError('benchmark_human_evidence_binding')
    bundle_sha = verdict['artifact_bundle_sha256']
    if bundle_sha is not None and not any(record['sha256'] == bundle_sha for record in index['files'].values()):
        raise ValueError('benchmark_handover_not_in_sealed_custody')
    stores = _human_store_paths(registration, verdict['condition'])
    if any(path.exists() for path in stores):
        raise FileExistsError('benchmark_human_verdict_already_in_immutable_custody')
    intake = _human_intake(root)
    intake.mkdir(exist_ok=True)
    destination = intake / verdict['condition'].replace(':', '-')
    destination.mkdir(exist_ok=False)
    records = {}
    for name, source in (('verdict.json', verdict_path), ('evidence.bin', evidence_path)):
        target = destination / name
        before = bare._record(source)
        expected_hash = hashlib.sha256(verdict_raw).hexdigest() if name == 'verdict.json' else verdict['evidence_sha256']
        if before['sha256'] != expected_hash:
            raise ValueError('benchmark_human_receipt_source_changed')
        with source.open('rb') as read, target.open('xb') as write:
            shutil.copyfileobj(read, write)
            write.flush()
            os.fsync(write.fileno())
        copied = bare._record(target)
        if any(before[k] != copied[k] for k in ('sha256', 'bytes')):
            raise ValueError('benchmark_human_receipt_copy_changed')
        records[name] = {k: before[k] for k in ('sha256', 'bytes')}
    receipt = dict(schema='cad-harness.benchmark-human-receipt.v1', condition=verdict['condition'],
                   trial_id=dataset['trial_id'], dataset_sha256=digest(dataset), files=records,
                   observed_at=verdict['observed_at'], judge_id=verdict['judge_id'])
    with (destination / 'receipt.json').open('xb') as handle:
        handle.write(canonical(receipt))
        handle.flush()
        os.fsync(handle.fileno())
    for store in stores:
        store.mkdir(parents=True, exist_ok=False)
        for name in ('verdict.json', 'evidence.bin', 'receipt.json'):
            source, target = destination / name, store / name
            with source.open('rb') as read, target.open('xb') as write:
                shutil.copyfileobj(read, write)
                write.flush()
                os.fsync(write.fileno())
            if bare.isolation.file_hash(source) != bare.isolation.file_hash(target):
                raise OSError('benchmark_human_receipt_store_retrieval_failed')
    return dict(receipt=receipt, receipt_path=str(destination / 'receipt.json'), status='recorded_once',
                evidence_mode=dataset['evidence_mode'], new_model_calls=0,
                custody=[bare._record(store / 'receipt.json') for store in stores])


def apply_user_verdicts(dataset, registration, verdicts):
    """Pure, full-denominator recomputation from externally validated receipts."""
    result = json.loads(canonical(dataset))
    seen = set()
    by_condition = {row['pair'] + ':' + row['arm']: row for row in result['conditions']}
    for verdict in verdicts:
        _validate_user_verdict(dataset, registration, verdict)
        identifier = verdict['condition']
        if identifier in seen:
            raise ValueError('benchmark_duplicate_human_verdict')
        seen.add(identifier)
        row = by_condition[identifier]
        fatal = _fatal(row.get('deterministic')) or _fatal(row.get('judge')) or _fatal(row.get('execution'))
        fatal = fatal or verdict['critical_dimension_error'] is True or verdict['fabrication'] is True
        critical_known = verdict['critical_dimension_error'] is not None and verdict['fabrication'] is not None
        adoption = dict(status=verdict['status'], judge_id=verdict['judge_id'], observed_at=verdict['observed_at'],
                        evidence_sha256=verdict['evidence_sha256'], first_handover_reviewed=verdict['first_handover_reviewed'],
                        critical_error_ever=True if fatal else False if critical_known else None)
        execution = row.get('execution', {})
        correction = execution.get('correction')
        correction_ok = (correction is None or correction.get('verified_within_300_s') is True and
                         _number(correction.get('elapsed_s')) and 0 <= correction['elapsed_s'] <= 300)
        construction_status = row.get('construction_status', row['status'])
        qualified = (construction_status in ('PASS', 'submitted') and correction_ok and not fatal and
                     _qualified(row.get('deterministic', {}), row.get('judge', {}), adoption))
        failed = fatal or verdict['status'] == 'refused' or row.get('deterministic', {}).get('status') == 'FAIL' or row.get('judge', {}).get('status') == 'FAIL'
        outcome = 'PASS' if qualified else 'FAIL' if failed else 'UNVERIFIED'
        row.update(adoption=adoption, qualified_completion=qualified, right_censored=not qualified,
                   status=outcome if construction_status in ('PASS', 'submitted') else construction_status,
                   completion_time_s=row['timing']['full_wall_s'] if qualified else None)
        row['completion_time_reason'] = _completion_reason(row)
    result['qualified_conditions'] = sum(r['qualified_completion'] for r in result['conditions'])
    result['censored_conditions'] = 40 - result['qualified_conditions']
    result['status'] = 'completed_with_enrolled_outcomes' if len(seen) == 40 else 'awaiting_human_verdicts'
    result['per_arm'] = {arm: {'enrolled': 20,
        'qualified': sum(r['qualified_completion'] for r in result['conditions'] if r['arm'] == arm),
        'success_rate': sum(r['qualified_completion'] for r in result['conditions'] if r['arm'] == arm) / 20}
        for arm in ARMS}
    result['pairs'] = [dict(pair=p['id'], family=p['family'],
        savings=savings(by_condition[p['id'] + ':with_harness'], by_condition[p['id'] + ':bare']))
        for p in registration['pairs']]
    return result


class _HumanSession:
    """Metadata-only append journal, with no generation or native execution API."""
    def __init__(self, out, registration):
        self.out, self.registration, self.wall = out, registration, time.monotonic
        self.handle = (out / 'ledger.jsonl').open('xb')

    def event(self, kind, **fields):
        self.handle.write(canonical(dict(kind=kind, utc=datetime.now(timezone.utc).isoformat(), **fields)) + b'\n')
        self.handle.flush()
        os.fsync(self.handle.fileno())


def user_results(run_dir, out_dir):
    """Append a new, durably sealed dataset revision; original evidence stays put."""
    root, registration, dataset, index = _sealed_run(run_dir)
    verdicts, retained = [], []
    for pair in registration['pairs']:
        for arm in ARMS:
            condition = pair['id'] + ':' + arm
            stores = _human_store_paths(registration, condition)
            existing = [path.exists() for path in stores]
            local = _human_intake(root) / condition.replace(':', '-')
            if not any(existing):
                if local.exists():
                    raise ValueError('benchmark_human_receipt_custody_incomplete')
                continue
            if not all(existing):
                raise ValueError('benchmark_human_receipt_backup_missing')
            receipt_paths = [bare.scoped(path, 'receipt.json') for path in stores]
            if bare.isolation.file_hash(receipt_paths[0]) != bare.isolation.file_hash(receipt_paths[1]):
                raise ValueError('benchmark_human_receipt_stores_disagree')
            receipt = json.loads(receipt_paths[0].read_bytes())
            if (receipt.get('schema') != 'cad-harness.benchmark-human-receipt.v1' or
                    receipt.get('condition') != condition or receipt.get('trial_id') != dataset['trial_id'] or
                    receipt.get('dataset_sha256') != digest(dataset)):
                raise ValueError('benchmark_human_receipt_identity')
            for name in ('verdict.json', 'evidence.bin'):
                for store in stores:
                    path = bare.scoped(store, name)
                    actual = bare._record(path)
                    if any(actual[key] != receipt['files'][name][key] for key in ('sha256', 'bytes')):
                        raise ValueError('benchmark_human_receipt_changed')
                retained.append((condition.replace(':', '-') + '/' + name, stores[0] / name))
            verdict = json.loads((stores[0] / 'verdict.json').read_bytes())
            if (receipt['condition'] != verdict['condition'] or receipt['judge_id'] != verdict['judge_id'] or
                    receipt['files']['evidence.bin']['sha256'] != verdict['evidence_sha256']):
                raise ValueError('benchmark_human_receipt_verdict_binding')
            verdicts.append(verdict)
            retained.append((condition.replace(':', '-') + '/receipt.json', receipt_paths[0]))
    if not verdicts:
        raise ValueError('benchmark_no_external_human_receipts')
    revised = apply_user_verdicts(dataset, registration, verdicts)
    bindings = [dict(logical_path=name, sha256=bare.isolation.file_hash(path), bytes=path.stat().st_size) for name, path in retained]
    revision = digest({'dataset_sha256': digest(dataset), 'receipts': bindings})
    out = _metadata_path(out_dir)
    if out == root or out.is_relative_to(root) or root.is_relative_to(out):
        raise ValueError('benchmark_human_revision_must_not_mutate_sealed_run')
    out.mkdir(parents=True, exist_ok=False)
    for (name, path), binding in zip(retained, bindings):
        target = out / 'human-receipts' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with path.open('rb') as read, target.open('xb') as write:
            shutil.copyfileobj(read, write)
        if bare.isolation.file_hash(target) != binding['sha256'] or target.stat().st_size != binding['bytes']:
            raise ValueError('benchmark_human_revision_copy_changed')
    revised['revision'] = revision
    revised['supersedes'] = dict(dataset_sha256=digest(dataset), hash_index_sha256=bare.isolation.file_hash(root / 'hash-index.json'),
                                event_prefix_sha256=dataset['event_prefix_sha256'], original_custody=json.loads((root / 'custody-receipt.json').read_bytes()))
    session = _HumanSession(out, registration)
    events = Events(out / 'benchmark-events.jsonl', session)
    try:
        events.append('human_revision_started', supersedes=revised['supersedes'])
        for verdict in verdicts:
            events.append('external_human_verdict', verdict=verdict)
        revised['event_prefix_sha256'] = events.hash
        _write_dataset(out, revised)
        events.append('dataset_sealed', dataset_sha256=digest(revised), new_model_calls=0)
    finally:
        events.close()
        session.handle.close()
    locations = [Path(registration['durability'][key]).absolute() for key in ('location', 'backup_location')]
    custody = _publish(session, events, locations, revision=revision)
    return dict(schema=SCHEMA, status=revised['status'], dataset=str(out / 'dataset.json'), custody=custody,
                revision=revision, human_receipts=len(verdicts), qualified_conditions=revised['qualified_conditions'],
                censored_conditions=revised['censored_conditions'], evidence_mode=dataset['evidence_mode'], new_model_calls=0)


def demonstrate_adapter(manifest_path, prepared_path, card_path, context_path,
                        with_harness_bundle, ordinary_bundle, run_dir, *, profile='c-s1'):
    """Actually check two independent DEV handovers against one unchanged card.

    No construction, repair, model/provider transport, process injection or live
    authorization occurs here. Existing files are retained byte-for-byte; only
    bundle location metadata is rebound to retained native/STEP copies. Frozen
    trusted restoration is eligible only for the with-harness demonstration.
    """
    if profile not in ('c-s1', 'c-s2', 'c-s3'):
        raise ValueError('benchmark_adapter_profile')
    artifacts = _module('cad_verify_v4_artifacts')
    expected = _module('cad_verify_v4_s1').implementation_bindings(profile=profile)
    inputs = {key: _metadata_path(value) for key, value in (
        ('manifest', manifest_path), ('prepared', prepared_path),
        ('card', card_path), ('context', context_path))}
    manifest = json.loads(inputs['manifest'].read_bytes())
    # Admit lexical paths before any asset dereference, including checker gold.
    assets = {key: _metadata_path(inputs['manifest'].parent.joinpath(*bare._relative(record['path']).parts))
              for key, record in manifest['assets'].items()}
    bundles = {}
    for method, path in (('with_harness', with_harness_bundle), ('ordinary', ordinary_bundle)):
        path = _metadata_path(path)
        value = json.loads(path.read_bytes())
        if value.get('evidence_mode') != 'independent_dev':
            raise ValueError('benchmark_adapter_independent_dev_bundles_only')
        for record in [value['native'], value['step'], *value['extensions']]:
            _metadata_path(path.parent / record['path'])
        if method == 'ordinary' and value['extensions']:
            raise ValueError('benchmark_ordinary_adapter_cannot_require_python_restoration')
        module = {'c-s1': 'cad_verify_v4_compile', 'c-s2': 'cad_verify_v4_s2_edit',
                  'c-s3': 'cad_verify_v4_s3_rebuild'}[profile]
        for extension in value['extensions']:
            if (extension['module'] != 'tools.' + module or
                    extension['sha256'] != expected.get('tools/' + module + '.py')):
                raise ValueError('benchmark_adapter_unfrozen_restoration_dependency')
        value, files, extensions = artifacts.load_bundle(path, profile=profile)
        if method == 'ordinary':
            artifacts._guard_archive(files['native'], {}, set())
        bundles[method] = value, files
    out = _metadata_path(run_dir)
    out.mkdir(parents=True, exist_ok=False)

    def retain(source, relative, declared=None):
        source = _metadata_path(source)
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as reader, target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        record = bare._record(target)
        if declared is not None and any(record[key] != declared[key] for key in ('sha256', 'bytes')):
            raise ValueError('benchmark_adapter_snapshot_changed')
        return record

    input_hashes = {}
    for key, path in inputs.items():
        input_hashes[key] = retain(path, 'inputs/' + key + '.json')['sha256']
    for key, path in assets.items():
        retain(path, 'input-assets/' + hashlib.sha256(key.encode('utf-8')).hexdigest() + path.suffix,
               manifest['assets'][key])
    methods = {}
    file_id = lambda relative: 'adapter_' + hashlib.sha256(relative.encode('utf-8')).hexdigest()
    for method, (value, files) in bundles.items():
        retained = dict(value)
        retained['extensions'] = list(value['extensions'])
        for key, name in (('native', 'model.FCStd'), ('step', 'model.step')):
            retained[key] = retain(files[key], method + '/submitted/' + name, value[key])
        bundle_relative = method + '/bundle.json'
        bundle_path = out / bundle_relative
        bundle_path.write_bytes(canonical(retained))
        # process=None is deliberately fixed: a mocked/native-injected receipt
        # can never become this pre-live actual-OS demonstration.
        summary = artifacts.check(inputs['manifest'], inputs['prepared'], inputs['card'], inputs['context'],
                                  bundle_path, out / method / 'check', profile=profile, process=None)
        if (summary.get('evidence_mode') != 'independent_dev' or summary.get('native_work') != 1 or
                summary.get('live_calls') != 0):
            raise ValueError('benchmark_adapter_actual_native_process_required')
        check_relative = method + '/check-summary.json'
        (out / check_relative).write_bytes(canonical(summary))
        methods[method] = {'check': file_id(check_relative), 'bundle': file_id(bundle_relative)}
        if any(bare.isolation.file_hash(path) != input_hashes[key] for key, path in inputs.items()):
            raise ValueError('benchmark_adapter_inputs_changed')
    if _module('cad_verify_v4_s1').implementation_bindings(profile=profile) != expected:
        raise ValueError('benchmark_adapter_source_changed')
    proof_relative, index_relative = 'adapter-demonstration.json', 'hash-index.json'
    proof = dict(schema='cad-harness.benchmark-adapter-demonstration.v1',
                 evidence_mode='independent_dev', actual_native=True, live_calls=0, profile=profile,
                 same_card_sha256=input_hashes['card'], methods=methods, hash_index=file_id(index_relative))
    (out / proof_relative).write_bytes(canonical(proof))
    paths = _evidence_files(out)
    index = {path.relative_to(out).as_posix(): {key: value for key, value in bare._record(path).items() if key != 'path'}
             for path in paths}
    (out / index_relative).write_bytes(canonical({
        'schema': 'cad-harness.benchmark-adapter-index.v1', 'files': index, 'live_calls': 0}))
    paths.append(out / index_relative)
    registered_files = {file_id(path.relative_to(out).as_posix()):
        dict(path=path.relative_to(out).as_posix(), origin='operational', role='adapter_demonstration',
             **{key: value for key, value in bare._record(path).items() if key != 'path'}) for path in paths}
    fragment = {'adapter_demonstration': file_id(proof_relative), 'files': registered_files}
    _validate_adapter_demonstration(fragment, lambda key: out / registered_files[key]['path'])
    return dict(proof=str(out / proof_relative), source_root=str(out), registration_fragment=fragment,
                status='PASS', evidence_mode='independent_dev', live_calls=0)
