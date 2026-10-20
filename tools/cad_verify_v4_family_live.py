"""Authorized finite family expansion; importing this module performs no work.

The operational execution index is deliberately not a parser for the unpublished
family-roster layout. Its opaque bytes and the public commitment are hash-bound
by the common trial runtime. Neither checker cards nor roster bytes are model
inputs. All scored denominators, strata, reservations and thresholds are signed
constants, not registration overrides. Source changes require a new final lock.
"""
from collections import Counter
import math
from pathlib import Path, PurePosixPath
import re

if __package__:
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_plans as plans
    from . import cad_verify_v4_s1 as s1, cad_verify_v4_trials as trials
    from . import cad_verify_v4_c2_recipe as c2_recipe, cad_verify_v4_inputs as inputs
    from .cad_verify_guard import Stop
else:
    import cad_verify_v4_ledger as ledger, cad_verify_v4_plans as plans
    import cad_verify_v4_s1 as s1, cad_verify_v4_trials as trials
    import cad_verify_v4_c2_recipe as c2_recipe, cad_verify_v4_inputs as inputs
    from cad_verify_guard import Stop

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'design/cad-harness-verify-v4/schemas/family-live-registration.schema.json'
GENERATOR = 'openai-codex/gpt-6.1-sol'
THINKING = 'xhigh'
FAMILIES = {
    'C1': dict(profile='c-s1', count=10, minimum=8,
               strata={'prismatic': (4, 3), 'stepped_oriented': (3, 2), 'curved_irregular': (3, 2)}),
    'C2': dict(profile='c-s1', count=10, minimum=8,
               strata={'convex': (3, 2), 'connected_holes': (4, 3), 'notch_tool_access': (3, 2)}),
    'C3': dict(profile='c-s1', count=8, minimum=7,
               strata={'numeric': (3, 2), 'alphanumeric': (3, 2), 'dense': (2, 2)}),
    'C4': dict(profile='c-s2', count=8, minimum=6,
               strata={'planar_oblique': (2, 1), 'curved_offsets': (2, 1),
                       'finite_planar_replacement': (2, 1), 'preservation': (2, 1)}),
    'C5': dict(profile='c-s3', count=7, minimum=5,
               strata={'two_patch': (3, 2), 'trimmed_multi_patch': (4, 3)}),
}
RESERVATIONS = {family + ':' + purpose: spec['count'] * factor
                for family, spec in FAMILIES.items()
                for purpose, factor in (('generation', 3), ('judge', 1))}
CONTROL_SPECS = {
    'AC-corrupt-step': ('inspect_step', {'manifest', 'recipe'}, {'asset_id'}, 'ambiguous_step_length_unit'),
    'AC-open-contour': ('planar_geometry', {'contour'}, {'curve_tolerance_mm'}, 'judge_open_loop'),
    'AC-tool-infeasible': ('tool_access', {'contour'}, {'criterion'}, 'tool_access_FAIL'),
    'AC-unavailable-glyph': ('validate_context', {'manifest', 'prepared', 'card', 'context'}, set(), 'glyph_coverage'),
}
MODEL_ROLES = {'request', 'input_manifest', 'prepared', 'source_asset', 'recipe', 'font', 'license'}
ENTRY_FILENAMES = {'request': 'request.txt', 'input_manifest': 'manifest.json',
                   'prepared': 'prepared.json', 'card': 'card.json', 'context': 'context.json'}
OPERATIONAL_ROLES = {
    'family_public_commitment', 'judge_rubric', 'public_commitment', 'source_commitment',
    'protocol', 'rubric', 'preregistration', 'custody', 'adapter_demonstration',
    'isolation_demonstration', 'bare_runtime_inventory', 'bare_runtime_staging_proof', 'preparation_evidence',
    'custody_provisioning', 'custody_retrieval_proof', 'human_judge_identity',
}


def _published_path(value):
    if not isinstance(value, str) or not value:
        raise ValueError('published_relative_path_required')
    path = PurePosixPath(value)
    if (path.is_absolute() or '..' in path.parts or ':' in value or '\\' in value
            or str(path) != value or value == '.'):
        raise ValueError('published_relative_path_invalid')
    return path


def published_commitments(text):
    """Parse the public fenced SHA table, not a private roster or input file.

    The public document has one final table containing both active paths and
    explicitly prefixed retired history. Duplicate paths are ambiguous and are
    rejected, never resolved by choosing a favorable/latest row.
    """
    if not isinstance(text, str):
        raise ValueError('published_commitment_text')
    lines = text.splitlines()
    headings = [index for index, line in enumerate(lines) if line.strip() == '## SHA-256']
    if len(headings) != 1:
        raise ValueError('published_sha_heading')
    section = lines[headings[0] + 1:]
    if sum(line.strip().startswith('```') for line in section) != 2:
        raise ValueError('published_sha_table_ambiguous')
    opened, closed, records = False, False, {}
    for line in section:
        if line.strip() == '```':
            if not opened:
                opened = True
                continue
            closed = True
            break
        if not opened:
            if line.startswith('## '):
                break
            continue
        if not line.strip():
            continue
        match = re.fullmatch(r'([0-9a-f]{64})  ([0-9]+)  (.+)', line)
        if match is None:
            raise ValueError('published_sha_row')
        digest, size, relative = match.groups()
        _published_path(relative)
        if relative in records:
            raise ValueError('published_duplicate_path:' + relative)
        records[relative] = dict(sha256=digest, bytes=int(size))
    if not opened or not closed or not records:
        raise ValueError('published_sha_table_incomplete')
    return records


def validate_published_record(record, commitments):
    """Require exact active public membership of an original byte record."""
    relative = record.get('published_relative_path')
    path = _published_path(relative)
    if any(part.casefold().startswith('retired-') for part in path.parts):
        raise ValueError('published_retired_cohort_refused')
    expected = commitments.get(relative)
    if expected is None or any(record.get(key) != expected[key] for key in ('sha256', 'bytes')):
        raise ValueError('published_original_identity_mismatch:' + relative)


def validate_published_files(registration, path_for_id):
    """Check explicit source provenance against an authenticated public copy.

    Only the finite metadata allowlist may be staged operationally. Reclassifying
    a request, asset, card, prepared document or roster cannot evade publication.
    `path_for_id` is the caller's authenticated resolver, never a source-tree read.
    """
    key = 'public_commitment' if 'public_commitment' in registration else 'source_commitment'
    file_id = registration[key]
    commitment_record = registration['files'][file_id]
    if (commitment_record.get('origin') != 'operational'
            or commitment_record.get('role') not in {'family_public_commitment', 'public_commitment', 'source_commitment'}):
        raise ValueError('published_commitment_metadata_required')
    commitments = published_commitments(path_for_id(file_id).read_text(encoding='utf-8-sig'))
    seen_originals = set()
    for record in registration['files'].values():
        if record.get('origin') == 'published_cohort':
            validate_published_record(record, commitments)
            relative = record['published_relative_path']
            if relative in seen_originals:
                raise ValueError('published_original_alias_refused')
            seen_originals.add(relative)
        elif (record.get('origin') != 'operational' or record.get('role') not in OPERATIONAL_ROLES
              or 'published_relative_path' in record):
            raise ValueError('published_original_cannot_be_operational')
    return commitments


def validate_active_c2_prepared(prepared):
    """Bind canonical prepared identities to the byte-pinned active recipe."""
    active = c2_recipe.load(ROOT)
    contours = [row for row in prepared.get('assets', {}).values()
                if row.get('schema') == 'cad-harness.contour.v4c']
    if not contours or any(row.get('recipe_sha256') != active['canonical_sha256'] or
                           inputs.canonical_sha(row.get('recipe')) != active['canonical_sha256']
                           for row in contours):
        raise ValueError('published_active_c2_recipe_required')


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate_registration(registration):
    """Validate only the new execution index; never read private roster fields."""
    schema = ledger.read_json(SCHEMA)
    plans._check(registration, schema, schema, 'family_execution_registration')
    files = registration['files']
    seen_paths = set()
    for record in files.values():
        path = PurePosixPath(record['path'])
        if (path.is_absolute() or '..' in path.parts or ':' in record['path']
                or '\\' in record['path'] or record['path'] in seen_paths):
            raise ValueError('family_file_path')
        seen_paths.add(record['path'])
    cohort = registration['cohort']
    if not any(record['role'] == 'family_roster' and all(record[key] == cohort[key]
               for key in ('path', 'sha256', 'bytes')) for record in files.values()):
        raise ValueError('family_opaque_roster_binding')
    for field, role in (('public_commitment', 'family_public_commitment'), ('rubric', 'judge_rubric')):
        if files.get(registration[field], {}).get('role') != role:
            raise ValueError('family_' + field + '_binding')
    entries = registration['entries']
    expected_ids = {f'{family}-{number:02d}' for family, spec in FAMILIES.items()
                    for number in range(1, spec['count'] + 1)}
    if len({entry['id'] for entry in entries}) != 43 or {entry['id'] for entry in entries} != expected_ids:
        raise ValueError('family_enrolled_identities')
    checker_ids = {entry[field] for entry in entries for field in ('card', 'context')}
    checker_ids.update((registration['rubric'], registration['public_commitment']))
    for control in registration['controls']:
        checker_ids.update(control['inputs'].values())
        checker_ids.add(control['invalidity_proof'])
    for entry in entries:
        family = entry['family']
        if not entry['id'].startswith(family + '-') or entry['profile'] != FAMILIES[family]['profile']:
            raise ValueError('family_identity_profile')
        for field in ('request', 'input_manifest', 'prepared', 'card', 'context'):
            if entry[field] not in files or files[entry[field]]['role'] != field:
                raise ValueError('family_entry_file:' + field)
        if len({entry[field] for field in ('request', 'input_manifest', 'prepared', 'card', 'context')}) != 5:
            raise ValueError('family_entry_file_alias')
        if entry['request'] not in entry['model_inputs']:
            raise ValueError('family_request_not_model_input')
        for file_id in entry['model_inputs']:
            if file_id in checker_ids or files.get(file_id, {}).get('role') not in MODEL_ROLES:
                raise ValueError('family_private_checker_model_input')
        if not set(entry.get('images', [])) <= set(entry['model_inputs']):
            raise ValueError('family_unapproved_image')
        if family == 'C2':
            number = int(entry['id'].rsplit('-', 1)[1])
            stratum = 'convex' if number <= 3 else 'connected_holes' if number <= 7 else 'notch_tool_access'
            if entry['stratum'] != stratum:
                raise ValueError('family_c2_published_stratum_identity')
    for family, spec in FAMILIES.items():
        actual = Counter(entry['stratum'] for entry in entries if entry['family'] == family)
        if actual != Counter({name: count for name, (count, _) in spec['strata'].items()}):
            raise ValueError('family_signed_stratum_counts:' + family)
    controls = registration['controls']
    if {control['id'] for control in controls} != set(CONTROL_SPECS):
        raise ValueError('family_control_identities')
    for control in controls:
        checker, inputs, parameters, _ = CONTROL_SPECS[control['id']]
        if (control['checker'] != checker or set(control['inputs']) != inputs
                or set(control['parameters']) != parameters):
            raise ValueError('family_control_checker_contract')
        if any(file_id not in files for file_id in control['inputs'].values()):
            raise ValueError('family_control_file')
        if files.get(control['invalidity_proof'], {}).get('role') != 'admission_invalidity_proof':
            raise ValueError('family_control_independent_invalidity_proof')
        if checker == 'inspect_step' and (not isinstance(control['parameters']['asset_id'], str)
                                          or not control['parameters']['asset_id']):
            raise ValueError('family_control_asset_id')
        if checker == 'planar_geometry' and not _positive(control['parameters']['curve_tolerance_mm']):
            raise ValueError('family_control_curve_tolerance')
        if checker == 'tool_access':
            criterion = control['parameters']['criterion']
            required = {'tool_radius_mm', 'maximum_uncovered_mm2', 'area_uncertainty_mm2',
                        'curve_tolerance_mm', 'buffer_segments', 'require_connected'}
            if not isinstance(criterion, dict) or set(criterion) != required:
                raise ValueError('family_control_explicit_tool_criterion')
            for field in ('tool_radius_mm', 'curve_tolerance_mm'):
                if not _positive(criterion[field]):
                    raise ValueError('family_control_tool_criterion_number')
            for field in ('maximum_uncovered_mm2', 'area_uncertainty_mm2'):
                value = criterion[field]
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError('family_control_tool_criterion_number')
            if (type(criterion['require_connected']) is not bool
                    or type(criterion['buffer_segments']) is not int
                    or not 8 <= criterion['buffer_segments'] <= 4096):
                raise ValueError('family_control_tool_criterion_geometry_settings')
    if set(registration['order']) != expected_ids | set(CONTROL_SPECS):
        raise ValueError('family_complete_frozen_order')
    return registration


def reservation(registration):
    validate_registration(registration)
    return dict(RESERVATIONS)


def _card_requirements(entry, card):
    criteria = card.get('criteria', [])
    ids = [row.get('id') for row in criteria]
    if not criteria or len(set(ids)) != len(ids) or None in ids:
        raise ValueError('family_card_criteria')
    if card.get('profile') != entry['profile']:
        raise ValueError('family_card_profile')
    metrics = {row['metric'] for row in criteria}
    if not {'solid_valid', 'native_roundtrip'} <= metrics:
        raise ValueError('family_card_native_validity_editability_required')
    if any(row.get('require_editable') is not True for row in criteria if row['metric'] == 'native_roundtrip'):
        raise ValueError('family_card_operative_editability_required')
    if entry['family'] == 'C2':
        if not {'min_radius', 'tool_access'} <= metrics:
            raise ValueError('family_c2_mandatory_actual_tool_metrics')
        for row in criteria:
            if row['metric'] in ('min_radius', 'tool_access'):
                value = row.get('minimum_mm' if row['metric'] == 'min_radius' else 'tool_radius_mm')
                if not _positive(value) or value < .25:
                    raise ValueError('family_c2_minimum_tool_radius')
    if entry['family'] == 'C5':
        if not {'g2_continuity', 'surface_deviation'} <= metrics:
            raise ValueError('family_c5_g2_deviation_required')
        for row in criteria:
            if row['metric'] == 'surface_deviation':
                value = row.get('maximum_mm')
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= .005:
                    raise ValueError('family_c5_signed_deviation_limit')
    return criteria


def validate_bound_inputs(registration, path_for_id):
    """Admission on authenticated files only; the opaque roster is never parsed."""
    validate_registration(registration)
    validate_published_files(registration, path_for_id)
    for entry in registration['entries']:
        _card_requirements(entry, ledger.read_json(path_for_id(entry['card'])))
        for field in ('request', 'input_manifest', 'prepared', 'card', 'context'):
            record = registration['files'][entry[field]]
            if record.get('published_relative_path') != 'generative/' + entry['id'] + '/' + ENTRY_FILENAMES[field]:
                raise ValueError('published_family_entry_identity')
        if entry['family'] == 'C2':
            validate_active_c2_prepared(ledger.read_json(path_for_id(entry['prepared'])))
    for control in registration['controls']:
        for file_id in control['inputs'].values():
            relative = registration['files'][file_id].get('published_relative_path', '')
            if not relative.startswith('admission/' + control['id'] + '/'):
                raise ValueError('published_admission_control_identity')
        proof = registration['files'][control['invalidity_proof']]
        if proof.get('published_relative_path') != 'admission/results.json':
            raise ValueError('published_admission_invalidity_proof')


def native_admission(control, out):
    """Trusted worker-only deterministic checks; no generation/judgment route.

    Inputs here are authenticated released absolute paths, not arbitrary source
    instructions. An unrelated parse/environment error is UNVERIFIED, never the
    expected refusal. The independent invalidity proof is retained separately.
    """
    if __package__:
        from . import cad_verify_v4_inputs as inputs, cad_verify_v4_judges as judges
        from . import cad_verify_v4_artifact_judges as artifacts
    else:
        import cad_verify_v4_inputs as inputs, cad_verify_v4_judges as judges
        import cad_verify_v4_artifact_judges as artifacts
    checker, required_inputs, parameters, expected = CONTROL_SPECS[control['id']]
    if (control['checker'] != checker or set(control['inputs']) != required_inputs
            or set(control['parameters']) != parameters):
        raise ValueError('family_control_checker_contract')
    paths = {key: inputs.guarded_path(path) for key, path in control['inputs'].items()}
    before = {key: ledger.file_sha(path) for key, path in paths.items()}
    observed, error_type, admitted = None, None, None
    status, measurement = 'UNVERIFIED', None
    try:
        if checker == 'inspect_step':
            inputs.inspect_step(paths['manifest'], control['parameters']['asset_id'],
                                ledger.read_json(paths['recipe']), out)
        elif checker == 'planar_geometry':
            judges.planar_geometry(ledger.read_json(paths['contour']), control['parameters']['curve_tolerance_mm'])
        elif checker == 'tool_access':
            measurement = judges.tool_access(ledger.read_json(paths['contour']), control['parameters']['criterion'])
            observed = 'tool_access_' + measurement['status']
            admitted = measurement['status'] == 'PASS'
            status = 'PASS' if measurement['status'] == 'FAIL' else 'FAIL' if admitted else 'UNVERIFIED'
        else:
            artifacts.validate_context(ledger.read_json(paths['context']), paths['manifest'],
                                       paths['prepared'], paths['card'], profile='c-s1')
        if checker != 'tool_access':
            admitted, status = True, 'FAIL'
    except ValueError as exc:
        observed, error_type, admitted = str(exc), type(exc).__name__, False
        status = 'PASS' if observed == expected else 'UNVERIFIED'
    if before != {key: ledger.file_sha(path) for key, path in paths.items()}:
        raise ValueError('family_admission_input_changed')
    return dict(status=status, checker=checker, control_id=control['id'], admitted=admitted,
                refused=status == 'PASS' and admitted is False, expected_reason=expected,
                observed_reason=observed, error_type=error_type, measurement=measurement,
                bindings=before, model_calls=0, generated_deliverable=False)


def _artifact_evidence(entry, generation, card):
    """Require the full neutral checker on both handover representations."""
    criteria = _card_requirements(entry, card)
    expected = {row['id']: row['metric'] for row in criteria}
    wrapper = generation.get('artifact_verdict')
    result = wrapper.get('result') if isinstance(wrapper, dict) else None
    if not isinstance(result, dict):
        return dict(status='UNVERIFIED', complete=False, tool_verified=False, surface_verified=False,
                    reason='neutral_artifact_verdict_missing')
    representations = {}
    for name in ('fcstd', 'step'):
        judge = result.get('judges', {}).get(name, {})
        checks = judge.get('checks', [])
        if not isinstance(checks, list) or any(not isinstance(row, dict) for row in checks):
            checks = []
        actual = {row.get('id'): row.get('metric') for row in checks}
        complete = actual == expected and len(checks) == len(expected)
        passing = complete and judge.get('status') == 'PASS' and all(row.get('status') == 'PASS' for row in checks)
        tool = complete
        surface = complete
        for row in checks:
            metric, evidence = row.get('metric'), row.get('evidence', {})
            if metric == 'min_radius':
                tool = tool and row.get('status') == 'PASS' and evidence.get('source') == 'actual_native_section_line_arc_geometry'
            elif metric == 'tool_access':
                tool = tool and row.get('status') == 'PASS' and evidence.get('claim') == 'actual_output_planar_disk_center_only'
            elif metric == 'g2_continuity':
                surface = (surface and row.get('status') == 'PASS'
                           and evidence.get('coverage') == 'all_registered_grid_face_boundaries_and_actual_native_knot_seams')
            elif metric == 'surface_deviation':
                upper = (row.get('measured') or {}).get('upper_mm')
                surface = (surface and row.get('status') == 'PASS' and type(upper) in (int, float)
                           and math.isfinite(upper) and 0 <= upper <= .005
                           and evidence.get('coverage') == 'full_bidirectional_trimmed_regions')
        representations[name] = dict(complete=complete, passing=passing, tool_verified=tool, surface_verified=surface)
    native = result.get('native_evidence', {})
    complete = all(row['complete'] for row in representations.values())
    numeric = (wrapper.get('status') == 'PASS' and result.get('status') == 'PASS'
               and result.get('geometry_ok') is True and result.get('editability_ok') is True
               and all(native.get(key) is True for key in ('fcstd_reopened', 'step_reopened', 'editable'))
               and all(row['passing'] for row in representations.values()))
    tool = entry['family'] == 'C2' and all(row['tool_verified'] for row in representations.values())
    surface = entry['family'] == 'C5' and all(row['surface_verified'] for row in representations.values())
    if entry['family'] == 'C2':
        numeric = numeric and tool
    if entry['family'] == 'C5':
        numeric = numeric and surface
    return dict(status='PASS' if numeric else 'FAIL' if result.get('status') == 'FAIL' else 'UNVERIFIED',
                complete=complete, tool_verified=tool, surface_verified=surface,
                representations=representations, result=result)


def summarize(registration, records, *, stop_reason=None):
    """Aggregate fixed denominators; never pool families, strata, or cycles."""
    families = {}
    for family, spec in FAMILIES.items():
        rows = [records[entry['id']] for entry in registration['entries'] if entry['family'] == family]
        successes = sum(row['full_pass'] is True for row in rows)
        strata = {}
        for name, (denominator, minimum) in spec['strata'].items():
            passed = sum(row['full_pass'] is True for row in rows if row['stratum'] == name)
            strata[name] = dict(successes=passed, denominator=denominator, minimum=minimum, passed=passed >= minimum)
        tool_count = sum(row.get('tool_verified') is True for row in rows)
        false_acceptances = sum(row.get('false_acceptance') is True for row in rows)
        passed = (successes >= spec['minimum'] and all(value['passed'] for value in strata.values())
                  and false_acceptances == 0 and (family != 'C2' or tool_count == 10))
        families[family] = dict(status='PASS' if passed else 'FAIL', successes=successes,
                                denominator=spec['count'], minimum=spec['minimum'], strata=strata,
                                tool_verified=tool_count if family == 'C2' else None,
                                tool_denominator=10 if family == 'C2' else None,
                                false_acceptances=false_acceptances,
                                statuses=dict(Counter(row['status'] for row in rows)))
    controls = [records[control['id']] for control in registration['controls']]
    correct = sum(row.get('correct_refusal') is True for row in controls)
    control_gate = dict(status='PASS' if correct == 4 else 'FAIL', correct_refusals=correct, denominator=4,
                        statuses=dict(Counter(row['status'] for row in controls)))
    return dict(schema='cad-harness.family-live-result.v1', phase='families', trial_id=registration['trial_id'],
                cycle_id=registration['cycle_id'], status='INCOMPLETE' if stop_reason is not None else
                    'PASS' if correct == 4 and all(row['status'] == 'PASS' for row in families.values()) else 'FAIL',
                families=families, controls=control_gate,
                enrolled=47, generative_denominator=43, control_denominator=4,
                stop_reason=stop_reason, records=[records[item] for item in registration['order']],
                reservations=dict(RESERVATIONS), pooling=False, original_163='untouched')


def _reference(path):
    return dict(path=str(path), sha256=ledger.file_sha(path), bytes=path.stat().st_size)


def run(manifest_path, authorization_path, run_dir, *, process=None, native_process=None,
        wall=None, sleep=None, verifier=None):
    """Run the sealed order once, retaining all partial outcomes and reservations."""
    with trials.TrialSession(manifest_path, authorization_path, run_dir, phase='families',
            process=process, native_process=native_process, wall=wall, sleep=sleep, verifier=verifier) as session:
        registration = validate_registration(session.registration)
        validate_bound_inputs(registration, session.path)
        by_id = {entry['id']: entry for entry in registration['entries'] + registration['controls']}
        records = {key: dict(id=key, family=entry.get('family', 'Admission'), stratum=entry.get('stratum'),
                            status='UNSTARTED', full_pass=False, tool_verified=False,
                            correct_refusal=False, false_acceptance=False)
                   for key, entry in by_id.items()}
        ledger.write_json(session.out / 'family-enrollment.json', summarize(registration, records))
        session.event('family_enrolled', order=registration['order'], records=list(records.values()),
                      reservations=RESERVATIONS, generative_denominator=43, control_denominator=4)
        stop_reason = None
        for record_id in registration['order']:
            entry, record = by_id[record_id], records[record_id]
            started, out = False, None
            try:
                session.check()
                out = ledger.new_directory(session.out / record_id)
                started = True
                record['status'] = 'STARTED'
                session.event('family_entry_started', record_id=record_id, family=record['family'],
                              stratum=record['stratum'], evidence_mode=session.mode)
                if record_id in CONTROL_SPECS:
                    control = dict(entry, inputs={key: str(session.path(file_id))
                                   for key, file_id in entry['inputs'].items()})
                    result = s1.native_work('admission-control', out / 'admission', session.journal,
                                           timeout=300, process=session.native_process, control=control)
                    expected = CONTROL_SPECS[record_id][3]
                    correct = (result.get('status') == 'PASS' and result.get('admitted') is False
                               and result.get('refused') is True and result.get('model_calls') == 0
                               and result.get('generated_deliverable') is False
                               and result.get('checker') == entry['checker']
                               and result.get('control_id') == record_id
                               and result.get('observed_reason') == expected)
                    record.update(status='REFUSED' if correct else result.get('status', 'UNVERIFIED'),
                                  correct_refusal=correct, admission=result,
                                  invalidity_proof=_reference(session.path(entry['invalidity_proof'])))
                else:
                    generation = session.execute_plan(entry, out / 'generation',
                        pool=entry['family'] + ':generation', model=GENERATOR, thinking=THINKING,
                        max_calls=3, active_limit=1200)
                    generation_path = out / 'generation-result.json'
                    ledger.write_json(generation_path, generation)
                    record.update(generation_status=generation.get('status', 'UNVERIFIED'),
                                  generation=_reference(generation_path),
                                  artifact_bundle=generation.get('artifact_bundle'),
                                  first_handover=generation.get('first_handover'),
                                  native_cad_intervals=generation.get('native_cad_intervals', []))
                    card = ledger.read_json(session.path(entry['card']))
                    deterministic = _artifact_evidence(entry, generation, card)
                    record.update(deterministic_status=deterministic['status'], tool_verified=deterministic['tool_verified'],
                                  surface_verified=deterministic['surface_verified'])
                    session.event('family_generation_finished', record_id=record_id,
                                  generation=record['generation'], deterministic_status=deterministic['status'])
                    if generation.get('status') == 'PASS' and deterministic['status'] == 'PASS':
                        request = session.path(entry['request']).read_text(encoding='utf-8-sig')
                        rubric = ledger.read_json(session.path(registration['rubric']))
                        judgment = session.judge(record_id, request, deterministic['result'], rubric,
                            pool=entry['family'] + ':judge',
                            images=tuple(generation.get('images', ())))
                        status = judgment.get('status') if isinstance(judgment, dict) else None
                        if status not in ('PASS', 'FAIL', 'UNVERIFIED'):
                            status = 'UNVERIFIED'
                        if (isinstance(judgment, dict) and 'critical_violation' in judgment
                                and type(judgment['critical_violation']) is not bool):
                            status = 'UNVERIFIED'
                        critical = isinstance(judgment, dict) and judgment.get('critical_violation') is True
                        record.update(judgment=judgment, status='FAIL' if critical else status,
                                      full_pass=status == 'PASS' and not critical,
                                      false_acceptance=status == 'PASS' and critical)
                    else:
                        record['status'] = (generation.get('status') if generation.get('status') != 'PASS'
                                            else deterministic['status']) or 'UNVERIFIED'
            except BaseException as exc:
                reason = str(exc) or type(exc).__name__
                terminal = isinstance(exc, (Stop, KeyboardInterrupt, SystemExit))
                record.update(status=('INTERRUPTED' if started else 'UNSTARTED') if terminal else 'ERROR',
                              error=reason, error_type=type(exc).__name__, full_pass=False)
                if terminal:
                    stop_reason = reason
                session.event('family_entry_error', record_id=record_id, started=started, **record)
            if out is not None:
                ledger.write_json(out / 'record.json', record)
            session.event('family_entry_finished', record_id=record_id, record=record)
            if stop_reason is not None:
                break
        if stop_reason is not None:
            for record in records.values():
                if record['status'] == 'UNSTARTED':
                    record['unstarted_reason'] = stop_reason
        result = summarize(registration, records, stop_reason=stop_reason)
        result.update(evidence_mode=session.mode, accounting=session.summary())
        session.event('family_finished', status=result['status'], families=result['families'],
                      controls=result['controls'], stop_reason=stop_reason, accounting=result['accounting'])
        ledger.write_json(session.out / 'family-result.json', result)
        return result
