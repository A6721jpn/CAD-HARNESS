"""S1 confined input admission, STEP facts and canonical generator packets.

Native geometry is imported only by inspect_step. Host validators never import CAD.
"""
import copy
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat

if __package__:
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_plans as plans
else:
    import cad_verify_v4_ledger as ledger
    import cad_verify_v4_plans as plans

FORBIDDEN = {'pilot-user', 'v4-holdout-private'}
EXTENSIONS = {'step': {'.step', '.stp'}, 'image': {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'},
              'font': {'.ttf', '.otf'}, 'contour': {'.json'}, 'facts': {'.json'},
              'license': {'.txt', ''}}


def canonical_sha(value):
    return ledger.sha(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8'))


def _lexical(path, relative=False):
    text = os.fspath(path)
    parts = re.split(r'[\\/]', text)
    if any(p.casefold().rstrip(' .') in FORBIDDEN for p in parts):
        raise ValueError('private_input_path_forbidden')
    if any(p in ('.', '..') for p in parts):
        raise ValueError('input_path_traversal')
    if relative and (PureWindowsPath(text).is_absolute() or PureWindowsPath(text).drive or PurePosixPath(text).is_absolute()):
        raise ValueError('asset_path_absolute')
    if relative and (not text or ':' in text or '\\' in text or any(not p or p.rstrip(' .') != p for p in parts)):
        raise ValueError('asset_path_not_canonical')
    return Path(text)


def guarded_path(path, *, regular=True):
    """Reject private lexical names before *any* filesystem lookup; no links/reparse points."""
    path = _lexical(path).absolute()
    for component in reversed((path, *path.parents)):
        try:
            info = component.lstat()
        except OSError as error:
            raise ValueError('input_path_missing') from error
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('linked_input_path')
        if component != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError('input_parent_not_directory')
    if regular and not stat.S_ISREG(info.st_mode):
        # info above is the leaf because the ancestors were processed root first.
        raise ValueError('input_not_regular_file')
    path = path.resolve()
    _lexical(path)
    return path


def _manifest(path):
    path = guarded_path(path)
    manifest = plans.validate_document(ledger.read_json(path), 'inputs')
    for asset_id, record in manifest['assets'].items():
        _lexical(record['path'], relative=True)
        if record['kind'] == 'font':
            license_record = manifest['assets'].get(record['license_asset_id'])
            if license_record is None or license_record['kind'] != 'license':
                raise ValueError('font_license_missing')
        elif 'license_asset_id' in record or 'glyphs' in record:
            raise ValueError('nonfont_registry_fields')
    return path, manifest


def _resolve(path, manifest, asset_id, expected_kind=None):
    record = manifest['assets'].get(asset_id)
    if record is None:
        raise ValueError('unknown_asset_id')
    if expected_kind is not None and record['kind'] != expected_kind:
        raise ValueError('asset_kind_mismatch')
    relative = _lexical(record['path'], relative=True)
    target = guarded_path(path.parent / relative)
    if not target.is_relative_to(path.parent):
        raise ValueError('asset_outside_manifest')
    if target.suffix.lower() not in EXTENSIONS[record['kind']]:
        raise ValueError('asset_extension_mismatch')
    size = target.stat().st_size
    digest = ledger.file_sha(target)
    if size != record['bytes']:
        raise ValueError('asset_bytes_mismatch')
    if digest != record['sha256']:
        raise ValueError('asset_sha256_mismatch')
    with target.open('rb') as stream:
        prefix = stream.read(32)
    kind = record['kind']
    if kind == 'step' and not prefix.lstrip().startswith(b'ISO-10303-21;'):
        raise ValueError('asset_content_mismatch')
    if kind == 'font' and prefix[:4] not in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
        raise ValueError('asset_content_mismatch')
    if kind == 'image':
        signatures = (b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'BM', b'II*\x00', b'MM\x00*')
        if not any(prefix.startswith(s) for s in signatures):
            raise ValueError('asset_content_mismatch')
    if kind in ('contour', 'facts'):
        document = ledger.read_json(target)
        if kind == 'contour':
            plans.validate_document(document, 'contour-source')
        else:
            plans.validate_document(document, 'step-facts')
    if kind == 'license':
        if not target.read_text(encoding='utf-8').strip():
            raise ValueError('empty_font_license')
    return {'record': copy.deepcopy(record), 'path': target, 'digest': digest}


def load_manifest(path):
    path, manifest = _manifest(path)
    for asset_id in manifest['assets']:
        _resolve(path, manifest, asset_id)
    return manifest


def resolve_asset(manifest_path, asset_id, expected_kind=None):
    path, manifest = _manifest(manifest_path)
    return _resolve(path, manifest, asset_id, expected_kind)


def _validate_facts(record):
    if record['topology']['faces'] != len(record['faces']):
        raise ValueError('facts_face_count_mismatch')
    expected_missing = []
    signatures = {}
    for face in record['faces']:
        signatures[face['signature']] = signatures.get(face['signature'], 0) + 1
    for index, face in enumerate(record['faces'], 1):
        if face['id'] != 'Face' + str(index):
            raise ValueError('facts_face_id_order')
        if face['ambiguous'] != (signatures[face['signature']] > 1):
            raise ValueError('facts_signature_ambiguity')
        if any(face['bounds_mm'][i] > face['bounds_mm'][i+1] for i in (0, 2, 4)):
            raise ValueError('facts_face_bounds')
        if face['normal'] is None:
            if face['normal_kind'] != 'unavailable' or face['normal_reason'] is None:
                raise ValueError('facts_normal_validity')
        elif not math.isclose(sum(v*v for v in face['normal']), 1, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError('facts_normal_not_unit')
        if face['normal'] is not None:
            if face['normal_kind'] == 'unavailable':
                raise ValueError('facts_normal_validity')
            if face['normal_kind'] == 'constant' and face['normal_reason'] is not None:
                raise ValueError('facts_normal_validity')
            if face['normal_kind'] == 'surface_parameter_midpoint' and face['normal_reason'] != 'local_surface_normal_not_global_face_normal':
                raise ValueError('facts_normal_validity')
        if face['ambiguous']:
            expected_missing.append(face['id'] + ':ambiguous_signature')
        if face['normal_reason']:
            expected_missing.append(face['id'] + ':' + face['normal_reason'])
    if record['coverage'] != {'complete': not expected_missing, 'missing_reasons': expected_missing}:
        raise ValueError('facts_coverage_mismatch')
    if any(record['bounds_mm'][i] > record['bounds_mm'][i+1] for i in (0, 2, 4)):
        raise ValueError('facts_bounds')


def verify_prepared(packet_or_path, manifest_path):
    packet = ledger.read_json(guarded_path(packet_or_path)) if isinstance(packet_or_path, (str, os.PathLike)) else packet_or_path
    packet = plans.validate_document(packet, 'prepared')
    path, manifest = _manifest(manifest_path)
    load_manifest(path)
    if packet['source_manifest_sha256'] != ledger.file_sha(path):
        raise ValueError('prepared_manifest_mismatch')
    for asset_id, record in packet['assets'].items():
        source = _resolve(path, manifest, asset_id)
        if record['asset_id'] != asset_id:
            raise ValueError('prepared_asset_id_mismatch')
        if record['schema'] == 'cad-harness.step-facts.v4c':
            _validate_facts(record)
            if source['record']['kind'] != 'step' or record['source_sha256'] != source['digest']:
                raise ValueError('prepared_source_mismatch')
            if record['provenance']['manifest_sha256_before'] != packet['source_manifest_sha256'] or record['provenance']['manifest_sha256_after'] != packet['source_manifest_sha256']:
                raise ValueError('prepared_manifest_provenance_mismatch')
            if any(record['provenance'][key] != source['digest'] for key in ('asset_sha256_before', 'asset_sha256_after')):
                raise ValueError('prepared_asset_provenance_mismatch')
        elif record['schema'] == 'cad-harness.contour.v4c':
            if record['provenance'].get('kind') == 'independent_analytic_source':
                if source['record']['kind'] != 'contour' or record['source_sha256'] != source['digest']:
                    raise ValueError('prepared_analytic_source_mismatch')
                original = ledger.read_json(source['path'])
                for key in ('units', 'bounds_mm', 'nominal_width_mm', 'loops', 'source_image_asset_id'):
                    if original[key] != record[key]:
                        raise ValueError('prepared_analytic_geometry_mismatch')
                image = _resolve(path, manifest, record['source_image_asset_id'], 'image')
                if image['digest'] != record['source_image_sha256']:
                    raise ValueError('prepared_analytic_image_mismatch')
            else:
                if source['record']['kind'] != 'image' or record['source_image_sha256'] != source['digest'] or record['source_manifest_sha256'] != packet['source_manifest_sha256']:
                    raise ValueError('prepared_source_mismatch')
                if canonical_sha(record['recipe']) != record['recipe_sha256'] or canonical_sha(record['source_mask']) != record['mask_sha256']:
                    raise ValueError('prepared_contour_hash_mismatch')
                if canonical_sha({key: value for key, value in record.items() if key != 'record_sha256'}) != record['record_sha256']:
                    raise ValueError('prepared_contour_record_mismatch')
        else:
            raise ValueError('unsupported_prepared_asset')
    return packet


def model_inputs(packet, manifest_path=None):
    """Allowlist generator context. No original paths, masks, recipes or checker targets."""
    packet = verify_prepared(packet, manifest_path) if manifest_path is not None else plans.validate_document(packet, 'prepared')
    result = {'schema': 'cad-harness.model-inputs.v4c', 'profile': 'c-s1',
              'source_manifest_sha256': packet['source_manifest_sha256'], 'assets': {}, 'fonts': {}}
    for asset_id in sorted(packet['assets']):
        record = packet['assets'][asset_id]
        if record['schema'] == 'cad-harness.step-facts.v4c':
            _validate_facts(record)
        keys = ('schema', 'profile', 'asset_id', 'source_sha256', 'units', 'bounds_mm', 'topology', 'frame', 'faces', 'coverage') if record['schema'] == 'cad-harness.step-facts.v4c' else ('schema', 'profile', 'asset_id', 'units', 'bounds_mm', 'nominal_width_mm', 'loops', 'topology')
        result['assets'][asset_id] = {key: copy.deepcopy(record[key]) for key in keys}
    if manifest_path is not None:
        path, manifest = _manifest(manifest_path)
        for font_id in sorted(manifest['assets']):
            record = manifest['assets'][font_id]
            if record['kind'] == 'font':
                font = _resolve(path, manifest, font_id, 'font')
                license_asset = _resolve(path, manifest, record['license_asset_id'], 'license')
                result['fonts'][font_id] = dict(font_sha256=font['digest'], glyphs=record['glyphs'],
                                                license_sha256=license_asset['digest'])
    return result


def _bounds(shape):
    box = shape.BoundBox
    return [float(box.XMin), float(box.XMax), float(box.YMin), float(box.YMax), float(box.ZMin), float(box.ZMax)]


def _step_units(path):
    text = path.read_text(encoding='ascii', errors='strict')
    units = set()
    for prefix in re.findall(r'SI_UNIT\s*\(\s*(\$|\.[A-Z]+\.)\s*,\s*\.METRE\.\s*\)', text, re.I):
        unit = {'$': 'm', '.MILLI.': 'mm', '.CENTI.': 'cm'}.get(prefix.upper())
        if unit is None:
            raise ValueError('unsupported_step_length_unit')
        units.add(unit)
    conversions = re.findall(r'CONVERSION_BASED_UNIT\s*\(\s*\'([^\']+)\'', text, re.I)
    length_conversions = [u.casefold() for u in conversions if u.casefold() not in ('degree', 'degrees', 'radian')]
    if length_conversions:
        if any(u not in ('inch', 'inches') for u in length_conversions):
            raise ValueError('unsupported_step_length_unit')
        if units - {'m'}:
            raise ValueError('ambiguous_step_length_unit')
        # SI metre appears as the conversion basis, not as the document length unit.
        return 'inch'
    if len(units) != 1:
        raise ValueError('ambiguous_step_length_unit')
    return units.pop()


def inspect_step(manifest_path, asset_id, recipe, out):
    recipe = plans.validate_document(recipe, 'step-recipe')
    manifest_path = guarded_path(manifest_path)
    manifest_before = ledger.file_sha(manifest_path)
    resolved = resolve_asset(manifest_path, asset_id, 'step')
    if ledger.file_sha(manifest_path) != manifest_before:
        raise ValueError('input_changed_during_preparation')
    units = _step_units(resolved['path'])
    if units != recipe['source_units']:
        raise ValueError('step_source_units_mismatch')
    # Native interpreter is mandatory; host admission does not import these modules.
    try:
        import FreeCAD
        import Part
    except ImportError as error:
        raise ValueError('native_interpreter_required') from error
    shape = Part.Shape()
    shape.read(str(resolved['path']))
    if shape.isNull() or not shape.isValid() or not shape.Faces:
        raise ValueError('invalid_step_shape')
    faces = []
    precision = recipe['signature_precision_mm']
    for index, face in enumerate(shape.Faces, 1):
        surface_type = type(face.Surface).__name__
        normal = None
        normal_reason = None
        normal_kind = 'unavailable'
        try:
            u0, u1, v0, v1 = face.ParameterRange
            vector = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            length = vector.Length
            if not math.isfinite(length) or length == 0:
                raise ValueError('undefined_normal')
            normal = [float(vector.x / length), float(vector.y / length), float(vector.z / length)]
            normal_kind = 'constant' if isinstance(face.Surface, Part.Plane) else 'surface_parameter_midpoint'
            if normal_kind != 'constant':
                normal_reason = 'local_surface_normal_not_global_face_normal'
        except (RuntimeError, ValueError, AttributeError, OverflowError):
            normal_reason = 'native_normal_unavailable'
        center = [float(face.CenterOfMass.x), float(face.CenterOfMass.y), float(face.CenterOfMass.z)]
        bounds = _bounds(face)
        signature_data = {'surface_type': surface_type,
                          'area_quantized': round(float(face.Area) / (precision * precision)),
                          'center_quantized': [round(v / precision) for v in center],
                          'bounds_quantized': [round(v / precision) for v in bounds],
                          'normal_quantized': None if normal is None else [round(v, 12) for v in normal]}
        faces.append({'id': 'Face' + str(index), 'signature': canonical_sha(signature_data),
                      'ambiguous': False, 'surface_type': surface_type, 'area_mm2': float(face.Area),
                      'center_mm': center, 'bounds_mm': bounds, 'normal': normal,
                      'normal_kind': normal_kind, 'normal_reason': normal_reason})
    counts = {}
    for face in faces:
        counts[face['signature']] = counts.get(face['signature'], 0) + 1
    missing = []
    for face in faces:
        face['ambiguous'] = counts[face['signature']] > 1
        if face['ambiguous']:
            missing.append(face['id'] + ':ambiguous_signature')
        if face['normal_reason']:
            missing.append(face['id'] + ':' + face['normal_reason'])
    manifest_after = ledger.file_sha(manifest_path)
    asset_after = resolve_asset(manifest_path, asset_id, 'step')['digest']
    if manifest_before != manifest_after or resolved['digest'] != asset_after:
        raise ValueError('input_changed_during_preparation')
    facts = {'schema': 'cad-harness.step-facts.v4c', 'profile': 'c-s1', 'asset_id': asset_id,
             'source_sha256': resolved['digest'], 'units': 'mm', 'bounds_mm': _bounds(shape),
             'topology': {'solids': len(shape.Solids), 'shells': len(shape.Shells), 'faces': len(shape.Faces), 'edges': len(shape.Edges)},
             'frame': {'source_axes': recipe['source_axes'], 'source_units': units,
                       'import_units': 'mm', 'axis_transform': 'identity',
                       'thickness_mm': None, 'thickness_reason': 'requires_explicit_face_pair_not_bbox'},
             'faces': faces, 'coverage': {'complete': not missing, 'missing_reasons': missing},
             'recipe_sha256': canonical_sha(recipe),
             'provenance': {'manifest_sha256_before': manifest_before, 'manifest_sha256_after': manifest_after,
                            'asset_sha256_before': resolved['digest'], 'asset_sha256_after': asset_after,
                            'importer': 'FreeCAD.Part.Shape.read', 'freecad_version': '.'.join(FreeCAD.Version()[:3])}}
    packet = {'schema': 'cad-harness.prepared.v4c', 'profile': 'c-s1', 'source_manifest_sha256': manifest_before, 'assets': {asset_id: facts}}
    plans.validate_document(packet, 'prepared')
    output = Path(out)
    _lexical(output)
    if output.suffix.lower() == '.json':
        guarded_path(output.parent, regular=False)
        ledger.write_json(output, packet)
    else:
        if output.exists():
            output = guarded_path(output, regular=False)
            if not output.is_dir() or any(output.iterdir()):
                raise ValueError('output_not_empty_directory')
        else:
            guarded_path(output.parent, regular=False)
            output = ledger.new_directory(output)
        ledger.write_json(output / 'prepared.json', packet)
    return packet
