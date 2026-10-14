"""Host-safe strict c-s3 admission; native geometry remains lazy and independent."""
import copy
from pathlib import Path

if __package__:
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_plans as plans
else:
    import cad_verify_v4_ledger as ledger
    import cad_verify_v4_plans as plans

PROFILE = 'c-s3'
SCHEMAS = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/schemas'
NAMES = {'capability': 'capability-manifest', 'inputs': 'input-manifest',
         'prepared': 'prepared-inputs', 'step-facts': 'step-facts',
         'step-recipe': 'step-recipe', 'plan': 'capability-plan',
         'judge-card': 'judge-card', 'judge-result': 'judge-result'}


def validate_document(value, name):
    if name not in NAMES:
        raise ValueError('unknown_s3_schema')
    if not isinstance(value, dict) or value.get('profile') != PROFILE:
        raise ValueError('s3_document_profile')
    schema = ledger.read_json(SCHEMAS / ('s3-' + NAMES[name] + '.schema.json'))
    plans._check(value, schema, schema, 's3.' + name)
    return copy.deepcopy(value)


def validate_plan(value, manifest_path=None, prepared=None):
    plan = validate_document(value, 'plan')
    grid = plan['grid']
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('s3_grid_not_rectangular')
    cells = [cell for row in grid for cell in row]
    if len({cell['face_id'] for cell in cells}) != len(cells):
        raise ValueError('s3_grid_duplicate_face')
    if manifest_path is not None:
        if __package__:
            from . import cad_verify_v4_inputs as inputs
        else:
            import cad_verify_v4_inputs as inputs
        manifest = inputs.load_manifest(manifest_path)
        resolved = inputs.resolve_asset(manifest_path, plan['asset_id'], 'step')
        if (manifest['profile'] != PROFILE or resolved['record']['role'] != 'reference'
                or resolved['digest'] != plan['source_sha256']):
            raise ValueError('s3_immutable_reference_binding')
        if prepared is not None:
            prepared = inputs.verify_prepared(prepared, manifest_path)
    if prepared is not None:
        prepared = validate_document(prepared, 'prepared')
        facts = prepared['assets'].get(plan['asset_id'])
        if facts is None or facts['source_sha256'] != plan['source_sha256']:
            raise ValueError('s3_prepared_source_binding')
        if __package__:
            from . import cad_verify_v4_inputs as inputs
        else:
            import cad_verify_v4_inputs as inputs
        inputs._validate_facts(facts)
        for cell in cells:
            matches = [face for face in facts['faces'] if face['id'] == cell['face_id']
                       and face['signature'] == cell['signature'] and not face['ambiguous']]
            if len(matches) != 1 or matches[0]['adjacent_face_ids'] != cell['adjacent_face_ids']:
                raise ValueError('s3_selector_unresolved_or_incomplete')
    return plan


def validate_judge_card(value):
    if __package__:
        from . import cad_verify_v4_s3_judges
    else:
        import cad_verify_v4_s3_judges
    return cad_verify_v4_s3_judges.validate_card(value)
