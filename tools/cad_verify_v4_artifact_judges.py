"""Plan-free, host-safe admission and shared stage-card artifact metrology.

The context is checker-only measurement registration, never generator input.
No candidate history, proxy, feature name, fit report or constructor is used.
validate_context returns a dict with out-of-band bound-file handles; callers
crossing a process boundary must validate again, not copy the admitted handle.
"""
import copy
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/schemas'
STAGES = {'c-s1': 'cad_verify_v4_judges', 'c-s2': 'cad_verify_v4_s2_judges',
          'c-s3': 'cad_verify_v4_s3_judges'}
FAMILIES = {'C1': 'c-s1', 'C2': 'c-s1', 'C3': 'c-s1', 'C4': 'c-s2', 'C5': 'c-s3'}
CONTOUR_METRICS = {'min_radius', 'tool_access', 'boundary_hausdorff', 'image_iou'}
REFERENCE_METRICS = {'reference_gap', 'reference_clearance', 'reference_contact',
                     'translation_clearance', 'reference_play'}


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '') + name)


class _CheckedContext(dict):
    """Data dictionary with private admission handles, not serialized fields."""
    def __init__(self, value, paths):
        super().__init__(copy.deepcopy(value))
        self._paths = tuple(paths)
        self._commitment = _module('cad_verify_v4_inputs').canonical_sha(value)


def _reference(value, manifest_path, prepared):
    inputs = _module('cad_verify_v4_inputs')
    asset = inputs.resolve_asset(manifest_path, value['asset_id'], 'step')
    facts = prepared['assets'].get(value['asset_id'])
    if (asset['record']['role'] != 'reference' or asset['digest'] != value['source_sha256']
            or facts is None or facts.get('source_sha256') != asset['digest']):
        raise ValueError('context_immutable_reference_binding')
    inputs._validate_facts(facts)
    if facts['units'] != 'mm' or facts['frame']['axis_transform'] != 'identity':
        raise ValueError('context_source_frame')
    return facts


def _measurements(value, manifest_path, prepared, card):
    inputs = _module('cad_verify_v4_inputs')
    family = value['family']
    reference, contour, engravings = value['reference'], value['contour'], value['engravings']
    if (contour is not None or engravings) and value['profile'] != 'c-s1':
        raise ValueError('context_s1_measurements_profile')
    if family in ('C4', 'C5') and reference is None:
        raise ValueError('context_reference_required')
    if reference is not None:
        facts = _reference(reference, manifest_path, prepared)
        if family == 'C5':
            grid = reference.get('grid')
            if not grid or any(len(row) != len(grid[0]) for row in grid):
                raise ValueError('context_rectangular_atlas_required')
            cells = [cell for row in grid for cell in row]
            if len({cell['face_id'] for cell in cells}) != len(cells):
                raise ValueError('context_duplicate_atlas_face')
            rows = {face['id']: face for face in facts['faces']}
            for cell in cells:
                fact = rows.get(cell['face_id'])
                if (fact is None or fact['ambiguous'] or fact['signature'] != cell['signature']
                        or fact['adjacent_face_ids'] != cell['adjacent_face_ids']):
                    raise ValueError('context_atlas_source_selector_mismatch')
        elif 'grid' in reference:
            raise ValueError('context_atlas_family')
    if contour is not None:
        record = prepared['assets'].get(contour['contour_id'])
        if not record or record['schema'] != 'cad-harness.contour.v4c' or record['units'] != 'mm':
            raise ValueError('context_contour_prerequisite')
        if family == 'C2':
            inputs.contour_solid_count(record)
    for engraving in engravings:
        _module('cad_verify_v4_plans')._axis(engraving['rotation_axis'])
        baseline = inputs.resolve_asset(manifest_path, engraving['baseline_asset_id'], 'step')
        if baseline['record']['role'] != 'checker':
            raise ValueError('context_baseline_must_be_checker_only')
        # Host admission checks the registered repertoire/license only. Actual
        # font parsing and glyph geometry belong to the pinned native checker.
        font = inputs.resolve_asset(manifest_path, engraving['font_id'], 'font')
        inputs.resolve_asset(manifest_path, font['record']['license_asset_id'], 'license')
        if any(not character.isspace() and character not in font['record']['glyphs']
               for character in engraving['text']):
            raise ValueError('glyph_coverage')
    for criterion in card['criteria']:
        metric = criterion['metric']
        if metric in CONTOUR_METRICS:
            record = prepared['assets'].get(criterion['contour_id'])
            if not record or record.get('schema') != 'cad-harness.contour.v4c' or record.get('units') != 'mm':
                raise ValueError('context_card_contour_prerequisite')
            needs_output = metric in ('min_radius', 'tool_access') or criterion.get('leg') == 'contour_to_output'
            if needs_output and (contour is None or contour['contour_id'] != criterion['contour_id']):
                raise ValueError('context_card_contour_mismatch')
        if metric == 'engraving':
            if not 0 <= criterion['index'] < len(engravings):
                raise ValueError('context_card_engraving_missing')
        if metric in REFERENCE_METRICS:
            asset = inputs.resolve_asset(manifest_path, criterion['asset_id'], 'step')
            _reference({'asset_id': criterion['asset_id'], 'source_sha256': asset['digest']},
                       manifest_path, prepared)


def validate_context(value, manifest_path, prepared_path, card_path, *, profile=None):
    """Bind strict checker measurements to actual immutable input/card bytes.

    Missing registrations are authoring prerequisites (ValueError), not PASS.
    No native modules are imported, opened or launched during admission.
    """
    inputs = _module('cad_verify_v4_inputs')
    ledger = _module('cad_verify_v4_ledger')
    plans = _module('cad_verify_v4_plans')
    schema = ledger.read_json(SCHEMAS / 'artifact-context.schema.json')
    plans._check(value, schema, schema, 'artifact-context')
    if FAMILIES[value['family']] != value['profile'] or (profile is not None and profile != value['profile']):
        raise ValueError('context_profile_family_mismatch')
    paths = tuple(inputs.guarded_path(path) for path in (manifest_path, prepared_path, card_path))
    for path, field in zip(paths, ('manifest_sha256', 'prepared_sha256', 'card_sha256')):
        if ledger.file_sha(path) != value[field]:
            raise ValueError('context_' + field + '_mismatch')
    manifest = inputs.load_manifest(paths[0])
    prepared = inputs.verify_prepared(paths[1], paths[0])
    card = _module(STAGES[value['profile']]).validate_card(ledger.read_json(paths[2]))
    if any(document['profile'] != value['profile'] for document in (manifest, prepared, card)):
        raise ValueError('context_bound_document_profile_mismatch')
    _measurements(value, paths[0], prepared, card)
    for path, field in zip(paths, ('manifest_sha256', 'prepared_sha256', 'card_sha256')):
        if ledger.file_sha(path) != value[field]:
            raise ValueError('context_bound_file_changed_during_admission')
    return _CheckedContext(value, paths)


def expected_solid_count(context, prepared):
    """Derive C2 cardinality only from the authenticated measurement binding."""
    inputs = _module('cad_verify_v4_inputs')
    ledger = _module('cad_verify_v4_ledger')
    if not isinstance(context, _CheckedContext):
        raise ValueError('context_requires_validate_context')
    if inputs.canonical_sha(context) != context._commitment:
        raise ValueError('context_frozen_measurements_changed')
    admitted = validate_context(context, *context._paths, profile=context['profile'])
    bound = ledger.read_json(context._paths[1])
    if inputs.canonical_sha(prepared) != inputs.canonical_sha(bound):
        raise ValueError('context_supplied_prepared_or_card_mismatch')
    if admitted['profile'] != 'c-s1' or admitted['family'] != 'C2':
        return 1
    contour = admitted['contour']
    if contour is None:
        return 1
    return inputs.contour_solid_count(bound['assets'][contour['contour_id']])


def judge(context, manifest_path, prepared, body_or_shape, card, *, native_evidence=None):
    """Score ordinary native/STEP geometry through exactly the existing kernels.

    Requires the handle returned by validate_context. Bound JSON and source
    assets are rechecked for each representation; the candidate is never repaired.
    Native shape certification limitations are those of the selected stage.
    """
    inputs = _module('cad_verify_v4_inputs')
    ledger = _module('cad_verify_v4_ledger')
    if not isinstance(context, _CheckedContext):
        raise ValueError('context_requires_validate_context')
    if inputs.canonical_sha(context) != context._commitment:
        raise ValueError('context_frozen_measurements_changed')
    if inputs.guarded_path(manifest_path) != context._paths[0]:
        raise ValueError('context_manifest_path_mismatch')
    admitted = validate_context(context, *context._paths, profile=context['profile'])
    bound_prepared, bound_card = (ledger.read_json(path) for path in context._paths[1:])
    if (inputs.canonical_sha(prepared) != inputs.canonical_sha(bound_prepared)
            or inputs.canonical_sha(card) != inputs.canonical_sha(bound_card)):
        raise ValueError('context_supplied_prepared_or_card_mismatch')
    stage = _module(STAGES[admitted['profile']])
    expected_solids = expected_solid_count(admitted, prepared)
    if admitted['profile'] != 'c-s1':
        result = stage.judge(admitted['reference'], manifest_path, prepared, body_or_shape,
                             card, native_evidence=native_evidence)
    else:
        baselines = {}
        if admitted['engravings']:
            import Part
            for index, engraving in enumerate(admitted['engravings']):
                asset = inputs.resolve_asset(manifest_path, engraving['baseline_asset_id'], 'step')
                try:
                    baseline = Part.Shape()
                    baseline.read(str(asset['path']))
                    if (not baseline.isNull() and baseline.isValid()
                            and len(baseline.Solids) == expected_solids and baseline.Volume > 0):
                        baselines[index] = baseline
                except (RuntimeError, OSError, ValueError):
                    pass  # Absent native certificate becomes UNVERIFIED in the shared kernel.
        result = stage.judge(admitted, manifest_path, prepared, body_or_shape, card,
                             native_evidence=native_evidence, baseline_shapes=baselines,
                             allow_history_baseline=False)
    # Detect changed context dependencies across native measurement as well.
    validate_context(context, *context._paths, profile=context['profile'])
    return result
