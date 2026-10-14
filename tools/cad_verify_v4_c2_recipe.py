"""Host-safe, immutable ONE C2 production recipe and its explicit registration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

if __package__:
    from . import cad_verify_v4_contours as contours
    from . import cad_verify_v4_inputs as inputs
    from . import cad_verify_v4_ledger as ledger
    from . import cad_verify_v4_plans as plans
else:
    import cad_verify_v4_contours as contours
    import cad_verify_v4_inputs as inputs
    import cad_verify_v4_ledger as ledger
    import cad_verify_v4_plans as plans

ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = 'design/cad-harness-verify-v4/c2-production-recipe-cycle2.json'
REGISTRATION_PATH = 'design/cad-harness-verify-v4/c2-production-registration.json'
RECIPE_SHA256 = '0b6d09b67c67a050de5247e9c28f95abc454ee33b2c8cef604f5839ea7dc7e04'
CANONICAL_SHA256 = 'e061fa8618dbd22bfa810999f3d6b5ab5f33d2c07d7cdd7734566486f5224231'
REGISTRATION_SHA256 = '5b97fc37d4d3cf6ae751258f84fee001b4c4156e1bb7fdc3b1e5fe9e82568146'
RETIRED = [{'family': 'C2', 'profile': 'c-s1', 'recipe': {
    'path': 'design/cad-harness-verify-v4/c2-production-recipe.json',
    'sha256': 'ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00',
    'canonical_sha256': '361235a66c015765b65fbd1041c031a84b1b369c671a205dc1b4363d63eb8c06'},
    'reason': 'C-R6: preserve all source components and islands; historical recipe is not active'}]


def _read(root, relative, expected_sha):
    inputs._lexical(relative, relative=True)
    path = inputs.guarded_path(root / relative)
    before = path.read_bytes()
    if hashlib.sha256(before).hexdigest() != expected_sha:
        raise ValueError('c2_production_file_sha256:' + relative)
    value = ledger.read_json(path)
    # Recheck both path safety and bytes after parsing: never bind a raced read.
    if inputs.guarded_path(root / relative) != path or path.read_bytes() != before:
        raise ValueError('c2_production_file_changed_during_read:' + relative)
    return value, dict(path=str(path), sha256=expected_sha, bytes=len(before))


def load(root=ROOT):
    """Validate frozen bytes, strict policy and the sole registration; no correction."""
    root = inputs.guarded_path(root, regular=False)
    registration, registration_record = _read(root, REGISTRATION_PATH, REGISTRATION_SHA256)
    expected = {
        'schema': 'cad-harness.c2-production-registration.v4c',
        'entries': [{'family': 'C2', 'profile': 'c-s1', 'recipe': {
            'path': RECIPE_PATH, 'sha256': RECIPE_SHA256,
            'canonical_sha256': CANONICAL_SHA256}}],
        'retired': RETIRED,
    }
    if registration != expected:
        raise ValueError('c2_production_registration_policy')
    recipe, record = _read(root, RECIPE_PATH, RECIPE_SHA256)
    canonical = json.dumps(recipe, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False, allow_nan=False).encode('utf-8')
    if hashlib.sha256(canonical).hexdigest() != CANONICAL_SHA256:
        raise ValueError('c2_production_canonical_sha256')
    plans.validate_document(recipe, 'contour-recipe', profile='c-s1')
    contours.validate_recipe(recipe)
    # The canonical pin commits every policy field, including alpha foreground,
    # no rounding/simplification, final height, and independent biarc settings.
    return dict(path=record['path'], sha256=record['sha256'],
                canonical_sha256=CANONICAL_SHA256, recipe=recipe,
                registration=registration_record)


def bindings(root=ROOT):
    """Return both explicitly registered files for the implementation freeze."""
    loaded = load(root)
    return {RECIPE_PATH: loaded['sha256'],
            REGISTRATION_PATH: loaded['registration']['sha256']}
