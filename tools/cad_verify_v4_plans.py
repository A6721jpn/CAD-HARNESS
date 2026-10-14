"""Host-only, data-only S1 schema and plan admission. No native imports."""
import copy
import math
from pathlib import Path

if __package__:
    from . import cad_spec, cad_verify_v4_ledger as ledger
else:
    import cad_spec
    import cad_verify_v4_ledger as ledger

SCHEMAS = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/schemas'
PROFILE = 'c-s1'


def validate_profile(profile):
    if profile != PROFILE or not isinstance(profile, str):
        raise ValueError('unknown_s1_profile')
    return profile


def _check(value, node, root, where):
    if '$ref' in node:
        ref = node['$ref']
        if ref.startswith('#/'):
            target = root
            for part in ref[2:].split('/'):
                target = target[part]
            return _check(value, target, root, where)
        if '/' in ref or '\\' in ref or not ref.endswith('.json'):
            raise ValueError('unsafe_schema_reference')
        other = ledger.read_json(SCHEMAS / ref)
        return _check(value, other, other, where)
    if 'oneOf' in node:
        matches = 0
        for choice in node['oneOf']:
            try:
                _check(value, choice, root, where)
                matches += 1
            except ValueError:
                pass
        if matches != 1:
            raise ValueError(where + ':oneOf')
    types = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str), 'boolean': type(value) is bool,
             'integer': type(value) is int, 'number': type(value) in (int, float) and math.isfinite(value),
             'null': value is None}
    expected = node.get('type')
    if expected is not None and not any(types.get(t, False) for t in ([expected] if isinstance(expected, str) else expected)):
        raise ValueError(where + ':type')
    if 'const' in node and (type(value) is not type(node['const']) or value != node['const']):
        raise ValueError(where + ':const')
    if 'enum' in node and not any(type(value) is type(v) and value == v for v in node['enum']):
        raise ValueError(where + ':enum')
    if isinstance(value, dict):
        properties = node.get('properties', {})
        if set(node.get('required', [])) - set(value):
            raise ValueError(where + ':required')
        extra = set(value) - set(properties)
        policy = node.get('additionalProperties', True)
        if extra and policy is False:
            raise ValueError(where + ':unknown_field')
        for key, item in value.items():
            if key in properties:
                _check(item, properties[key], root, where + '.' + key)
            elif isinstance(policy, dict):
                _check(item, policy, root, where + '.' + key)
        if len(value) < node.get('minProperties', 0):
            raise ValueError(where + ':empty')
        if 'propertyNames' in node:
            for key in value:
                _check(key, node['propertyNames'], root, where + ':key')
    if isinstance(value, list):
        if not node.get('minItems', 0) <= len(value) <= node.get('maxItems', math.inf):
            raise ValueError(where + ':count')
        for index, item in enumerate(value):
            if 'items' in node:
                _check(item, node['items'], root, where + '.' + str(index))
        if node.get('uniqueItems') and len({cad_spec.canonical(v) for v in value}) != len(value):
            raise ValueError(where + ':duplicates')
    if isinstance(value, str):
        if not node.get('minLength', 0) <= len(value) <= node.get('maxLength', math.inf):
            raise ValueError(where + ':length')
        if 'pattern' in node:
            import re
            if re.search(node['pattern'], value) is None:
                raise ValueError(where + ':pattern')
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError(where + ':finite')
        for name, fail in [('minimum', lambda x: value < x), ('maximum', lambda x: value > x),
                           ('exclusiveMinimum', lambda x: value <= x)]:
            if name in node and fail(node[name]):
                raise ValueError(where + ':' + name)
    for clause in node.get('allOf', []):
        if 'if' in clause:
            try:
                _check(value, clause['if'], root, where)
            except ValueError:
                continue
            _check(value, clause['then'], root, where)
        else:
            _check(value, clause, root, where)


def validate_document(value, schema_name):
    if schema_name not in {'capability', 'inputs', 'prepared', 'step-facts', 'step-recipe', 'contour', 'contour-source', 'contour-recipe', 'text-outline', 'plan', 'judge-card', 'judge-result'}:
        raise ValueError('unknown_schema')
    filename = {'capability': 'capability-manifest', 'inputs': 'input-manifest',
                'prepared': 'prepared-inputs', 'plan': 'capability-plan'}.get(schema_name, schema_name)
    schema = ledger.read_json(SCHEMAS / (filename + '.schema.json'))
    _check(value, schema, schema, schema_name)
    return copy.deepcopy(value)


def _axis(value):
    length = math.hypot(*value)
    if length == 0:
        raise ValueError('zero_rotation_axis')
    if not math.isfinite(length):
        raise ValueError('rotation_axis_magnitude')


def validate_plan(value, manifest_path=None, prepared=None):
    plan = validate_document(value, 'plan')
    if plan['family'] == 'reference_fixture':
        # Admission uses the existing compiler contract, without calling its native compiler.
        plan['build_spec'] = cad_spec.validate_spec(plan['build_spec'])
    for placement in plan['references'] + plan['engravings']:
        _axis(placement['rotation_axis'])
    if manifest_path is not None:
        if __package__:
            from . import cad_verify_v4_inputs as inputs
        else:
            import cad_verify_v4_inputs as inputs
        manifest = inputs.load_manifest(manifest_path)
        for reference in plan['references']:
            resolved = inputs.resolve_asset(manifest_path, reference['asset_id'], 'step')
            if resolved['record']['role'] != 'reference':
                raise ValueError('reference_role_mismatch')
        for engraving in plan['engravings']:
            font = inputs.resolve_asset(manifest_path, engraving['font_id'], 'font')['record']
            if any(character not in font['glyphs'] for character in engraving['text']):
                raise ValueError('font_glyph_not_registered')
        if plan['family'] == 'contour_extrude':
            record = manifest['assets'].get(plan['contour_id'])
            if record is None or record['kind'] not in ('image', 'contour'):
                raise ValueError('contour_asset_mismatch')
        if prepared is not None:
            prepared = inputs.verify_prepared(prepared, manifest_path)
    if prepared is not None and plan['family'] == 'contour_extrude':
        record = prepared.get('assets', {}).get(plan['contour_id'])
        if record is None or record.get('schema') != 'cad-harness.contour.v4c':
            raise ValueError('prepared_contour_missing')
        validate_document(record, 'contour')
    return plan


def validate_judge_card(value):
    card = validate_document(value, 'judge-card')
    ids = [item['id'] for item in card['criteria']]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_criterion_id')
    for item in card['criteria']:
        if 'face_ids' in item and len(set(item['face_ids'])) != len(item['face_ids']):
            raise ValueError('duplicate_reference_face_id')
        if 'rotation_axis' in item:
            _axis(item['rotation_axis'])
        if 'direction' in item and sum(x*x for x in item['direction']) == 0:
            raise ValueError('zero_play_direction')
        if 'interval_mm' in item and item['interval_mm'][0] > item['interval_mm'][1]:
            raise ValueError('play_interval')
        if item['metric']=='reference_play' and 'interval_mm' in item and not item['interval_mm'][0] <= 0 <= item['interval_mm'][1]:
            raise ValueError('play_search_without_datum')
        if 'expected_mm' in item and isinstance(item['expected_mm'], list) and any(item['expected_mm'][i] > item['expected_mm'][i+1] for i in (0, 2, 4)):
            raise ValueError('judge_bounds_interval')
    return card
