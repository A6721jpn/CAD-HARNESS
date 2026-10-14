"""Host-safe strict c-s2 schemas; no CAD imports or cross-stage fallback."""
import copy
from pathlib import Path

if __package__:
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_plans as plans
else:
    import cad_verify_v4_ledger as ledger
    import cad_verify_v4_plans as plans

PROFILE = 'c-s2'
SCHEMAS = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/schemas'
NAMES = {'capability': 'capability-manifest', 'inputs': 'input-manifest',
         'prepared': 'prepared-inputs', 'step-facts': 'step-facts',
         'step-recipe': 'step-recipe', 'plan': 'capability-plan',
         'judge-card': 'judge-card', 'judge-result': 'judge-result'}


def validate_document(value, name):
    if name not in NAMES:
        raise ValueError('unknown_s2_schema')
    if not isinstance(value, dict) or value.get('profile') != PROFILE:
        raise ValueError('s2_document_profile')
    schema = ledger.read_json(SCHEMAS / ('s2-' + NAMES[name] + '.schema.json'))
    plans._check(value, schema, schema, 's2.' + name)
    return copy.deepcopy(value)


def validate_plan(value, manifest_path=None, prepared=None):
    if __package__:
        from . import cad_verify_v4_s2_edit
    else:
        import cad_verify_v4_s2_edit
    return cad_verify_v4_s2_edit.validate_plan(value, manifest_path, prepared)


def validate_judge_card(value):
    if __package__:
        from . import cad_verify_v4_s2_judges
    else:
        import cad_verify_v4_s2_judges
    return cad_verify_v4_s2_judges.validate_card(value)
