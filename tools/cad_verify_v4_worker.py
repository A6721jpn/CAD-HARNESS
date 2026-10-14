"""Headless data-only worker. Parent owns process/PID, timeouts and raw capture.

Run native bin/python.exe tools/cad_verify_v4_worker.py --job ABS_JOB_JSON
with stdin closed and the native bin directory on DLL search/PATH. Compile and
verify MUST be separate processes; each closes every document before reporting.
"""
import argparse
import importlib
import json
import math
import os
from pathlib import Path
import platform
import sys


def _module(name):
    return importlib.import_module(('.' if __package__ else '') + name, __package__)


def _safe(path, regular=True):
    return _module('cad_verify_v4_inputs').guarded_path(path, regular=regular)


def _read(path):
    return _module('cad_verify_v4_ledger').read_json(_safe(path))


def _out(path):
    path = _safe(path, regular=False)
    if not path.is_dir():
        raise ValueError('output_directory_missing')
    return path


def _runtime(App):
    return {'owned_pid': os.getpid(), 'freecad_version': list(App.Version()),
            'gui_up': App.GuiUp, 'python_executable': sys.executable,
            'python_version': platform.python_version()}


def _bindings(job):
    ledger = _module('cad_verify_v4_ledger')
    inputs = _module('cad_verify_v4_inputs')
    manifest = inputs.load_manifest(job['manifest'])
    return {**{key + '_sha256': ledger.file_sha(_safe(job[key]))
               for key in ('manifest', 'prepared', 'plan', 'card')},
            'assets': {asset_id: inputs.resolve_asset(job['manifest'], asset_id)['digest']
                       for asset_id in manifest['assets']}}


def _loaded(job):
    inputs = _module('cad_verify_v4_inputs')
    plans = _module('cad_verify_v4_plans')
    profile = job.get('profile', 'c-s1')
    prepared = inputs.verify_prepared(job['prepared'], job['manifest'])
    if prepared['profile'] != profile:
        raise ValueError('worker_input_profile_mismatch')
    plan = plans.validate_plan(_read(job['plan']), job['manifest'], prepared, profile=profile)
    card = plans.validate_judge_card(_read(job['card']), profile=profile)
    return plan, prepared, card


def _close(App):
    for name in list(App.listDocuments()):
        App.closeDocument(name)
    return not App.listDocuments()


def _artifacts(out):
    ledger = _module('cad_verify_v4_ledger')
    return {key: {'path': str(out / name), 'sha256': ledger.file_sha(_safe(out / name)),
                  'bytes': (out / name).stat().st_size}
            for key, name in (('native', 'model.FCStd'), ('step', 'model.step'))}


def _compile(App, job, out):
    import Part
    compiler = _module('cad_verify_v4_compile')
    plan, prepared, card = _loaded(job)
    before = _bindings(job)
    editor = _module('cad_verify_v4_s2_edit') if job.get('profile') == 'c-s2' else compiler
    doc = App.newDocument('S2Candidate' if job.get('profile') == 'c-s2' else 'S1Candidate')
    body = editor.build_plan(doc, plan, job['manifest'], prepared)
    editability = editor.operative_evidence(doc, body)
    measurements = compiler.shape_measurements(body.Shape, tight_bounds=job.get('profile') == 'c-s2')
    # A new directory is the only destination; no existing artifacts are overwritten.
    doc.saveAs(str(out / 'model.FCStd'))
    Part.export([body], str(out / 'model.step'))
    after = _bindings(job)
    if before != after:
        raise ValueError('compile_input_changed')
    return {'status': 'PASS', 'geometry_ok': True, 'editability_ok': True,
            'editability': editability, 'measurements': measurements, 'metrics': measurements,
            'bounds_mm': measurements['bounds_mm'], 'volume_mm3': measurements['volume_mm3'],
            'bindings': before, 'artifacts': _artifacts(out),
            'source_paths': {key: str(_safe(job[key])) for key in ('manifest', 'prepared', 'plan', 'card')},
            'family': plan['family'], 'plan_sha256': before['plan_sha256'],
            **({'operation_report': editor.operation_report(body)} if job.get('profile') == 'c-s2' else {})}


def _roundtrip_criteria(card, evidence):
    checks = []
    for criterion in card['criteria']:
        if criterion['metric'] != 'native_roundtrip':
            continue
        fields = ('maximum_bounds_difference_mm', 'maximum_volume_difference_mm3', 'require_editable')
        if any(field not in criterion for field in fields):
            checks.append({'id': criterion['id'], 'status': 'UNVERIFIED', 'reason': 'missing_roundtrip_acceptance'})
            continue
        passed = evidence['bounds_difference_mm'] <= criterion['maximum_bounds_difference_mm'] and evidence['volume_difference_mm3'] <= criterion['maximum_volume_difference_mm3'] and (not criterion['require_editable'] or evidence['editable'])
        checks.append({'id': criterion['id'], 'status': 'PASS' if passed else 'FAIL'})
    if not checks:
        checks.append({'id': None, 'status': 'UNVERIFIED', 'reason': 'missing_native_roundtrip_criterion'})
    return checks


def _verify(App, job, out):
    import Part
    compiler = _module('cad_verify_v4_compile')
    profile = job.get('profile', 'c-s1')
    editor = _module('cad_verify_v4_s2_edit') if profile == 'c-s2' else compiler
    judges = _module('cad_verify_v4_s2_judges' if profile == 'c-s2' else 'cad_verify_v4_judges')
    plan, prepared, card = _loaded(job)
    before = _bindings(job)
    candidate = _out(job.get('candidate_dir', job['out']))
    built = _read(candidate / 'result.json')
    if (built.get('profile') != profile or built.get('status') != 'PASS'
            or built.get('document_closed') is not True):
        raise ValueError('compile_not_successful')
    if built.get('bindings') != before or built.get('artifacts') != _artifacts(candidate):
        raise ValueError('artifact_input_binding_mismatch')
    doc = App.openDocument(str(_safe(candidate / 'model.FCStd')))
    bodies = [obj for obj in doc.Objects if obj.TypeId == 'PartDesign::Body']
    if len(bodies) != 1:
        raise ValueError('reopen_body_count')
    body = bodies[0]
    allowed_proxies = ((editor.DirectEditProxy,) if profile == 'c-s2' else
                       (compiler.ContourProxy, compiler.EngravingProxy))
    # Proxy restoration executes only the frozen installed implementation. A missing or
    # changed proxy is not accepted even if a cached Shape happens to remain valid.
    for obj in body.Group:
        if obj.TypeId == 'PartDesign::FeaturePython':
            if type(obj.Proxy) not in allowed_proxies:
                raise ValueError('untrusted_or_missing_feature_proxy')
    for obj in doc.Objects:
        obj.touch()
    doc.recompute()
    compiler.check_document(doc, body)
    editor.check_model_inputs(body, plan, prepared, job['manifest'])
    restored = compiler.shape_measurements(body.Shape, tight_bounds=profile == 'c-s2')
    editability = editor.operative_evidence(doc, body)
    step_doc = App.newDocument('S1IndependentSTEP')
    Part.insert(str(_safe(candidate / 'model.step')), step_doc.Name)
    step_doc.recompute()
    shapes = [obj.Shape for obj in step_doc.Objects if hasattr(obj, 'Shape') and not obj.Shape.isNull()]
    if len(shapes) != 1:
        raise ValueError('step_candidate_object_count')
    step_shape = shapes[0]
    imported = compiler.shape_measurements(step_shape, tight_bounds=profile == 'c-s2')
    base = built['measurements']
    bound_delta = max(abs(a - b) for measurement in (restored, imported)
                      for a, b in zip(base['bounds_mm'], measurement['bounds_mm']))
    volume_delta = max(abs(base['volume_mm3'] - measurement['volume_mm3'])
                       for measurement in (restored, imported))
    evidence = {'fcstd_reopened': True, 'step_reopened': True, 'editable': True,
                'bounds_difference_mm': bound_delta, 'volume_difference_mm3': volume_delta}
    # Judge each independently reopened representation; STEP cannot prove parametrics,
    # so the operative FCStd proof is passed as explicit context rather than inferred.
    baselines = {index: doc.getObject('Engraving' + str(index)).Base.Shape.copy()
                 for index in range(len(plan.get('engravings', [])))}
    fcstd_judge = judges.judge(plan, job['manifest'], prepared, body, card,
                               native_evidence=evidence, baseline_shapes=baselines)
    step_judge = judges.judge(plan, job['manifest'], prepared, step_shape, card,
                              native_evidence=evidence, baseline_shapes=baselines)
    roundtrip = _roundtrip_criteria(card, evidence)
    if before != _bindings(job) or built['artifacts'] != _artifacts(candidate):
        raise ValueError('verify_input_or_artifact_changed')
    statuses = [row['status'] for row in roundtrip]
    statuses.extend((fcstd_judge['status'], step_judge['status']))
    status = 'FAIL' if 'FAIL' in statuses else 'PASS' if all(s == 'PASS' for s in statuses) else 'UNVERIFIED'
    return {'status': status, 'geometry_ok': True, 'editability_ok': True,
            'bindings': before, 'artifacts': built['artifacts'],
            'compile_result_sha256': _module('cad_verify_v4_ledger').file_sha(candidate / 'result.json'),
            'candidate_dir': str(candidate),
            'measurements': {'built': base, 'fcstd': restored, 'step': imported},
            'metrics': {'built': base, 'fcstd': restored, 'step': imported},
            'native_evidence': evidence, 'roundtrip': roundtrip,
            'editability': editability, 'judges': {'fcstd': fcstd_judge, 'step': step_judge},
            'source_paths': {key: str(_safe(job[key])) for key in ('manifest', 'prepared', 'plan', 'card')},
            'judgement': fcstd_judge}


def _identity(App):
    ledger = _module('cad_verify_v4_ledger')
    modules = {}
    for name in ('FreeCAD', 'Part', 'Sketcher', 'numpy', 'scipy', 'PIL', 'shapely', 'contourpy', 'fontTools', 'OCC'):
        module = importlib.import_module(name)
        source = getattr(module, '__file__', None)
        record = {'version': getattr(module, '__version__', getattr(module, 'VERSION', None)),
                  'path': str(source) if source else None, 'files': []}
        if source:
            path = Path(source)
            roots = list(getattr(module, '__path__', []))
            roots.extend(str(Path(root).parent / (Path(root).name + '.libs'))
                         for root in list(roots) if (Path(root).parent / (Path(root).name + '.libs')).is_dir())
            files = {path}
            for root in roots:
                for suffix in ('*.py', '*.pyd', '*.dll', '*.so', '*.json'):
                    files.update(Path(root).rglob(suffix))
            record['files'] = [{'path': str(file), 'sha256': ledger.file_sha(file),
                                'bytes': file.stat().st_size} for file in sorted(files)]
        modules[name] = record
    import Part
    native_bin = Path(sys.executable).parent
    libraries = [{'path': str(path), 'sha256': ledger.file_sha(path), 'bytes': path.stat().st_size}
                 for path in sorted(native_bin.glob('*.dll'))]
    return {'status': 'PASS', 'dependencies': modules, 'native_libraries': libraries,
            'occt_version': getattr(Part, 'OCC_VERSION', None)}


OPERATIONS = {
    'identity': {'operation', 'out'},
    'compile': {'operation', 'manifest', 'prepared', 'plan', 'card', 'out'},
    'verify': {'operation', 'manifest', 'prepared', 'plan', 'card', 'out'},
    'judge': {'operation', 'manifest', 'prepared', 'plan', 'card', 'out'},
    'prepare-step': {'operation', 'manifest', 'asset_id', 'recipe', 'out'},
    'contour': {'operation', 'manifest', 'asset_id', 'recipe', 'out'},
    'text': {'operation', 'manifest', 'font_id', 'text', 'height_mm', 'out'},
}


def execute(job):
    import FreeCAD as App
    ledger = _module('cad_verify_v4_ledger')
    if not isinstance(job, dict) or job.get('operation') not in OPERATIONS:
        raise ValueError('unknown_worker_operation')
    operation = job['operation']
    profile = job.get('profile', 'c-s1')
    if profile not in ('c-s1', 'c-s2'):
        raise ValueError('worker_profile')
    if profile == 'c-s2' and operation not in ('identity', 'compile', 'verify', 'judge', 'prepare-step'):
        raise ValueError('worker_operation_not_in_profile')
    optional = {'profile'} | ({'candidate_dir'} if operation in ('verify', 'judge') else set())
    if not OPERATIONS[operation] <= set(job) or set(job) - OPERATIONS[operation] - optional:
        raise ValueError('worker_job_fields')
    # Validate every supplied path before opening a document. Parent allocates output.
    for field in ('manifest', 'prepared', 'plan', 'card'):
        if field in job:
            _safe(job[field])
    if 'recipe' in job and not isinstance(job['recipe'], dict):
        raise ValueError('worker_recipe_requires_data_object')
    if 'recipe' in job and job['recipe'].get('profile') != profile:
        raise ValueError('worker_recipe_profile_mismatch')
    if 'candidate_dir' in job:
        _safe(job['candidate_dir'], regular=False)
    out = _out(job['out'])
    if operation not in ('verify', 'judge') and any(out.iterdir()):
        raise ValueError('worker_output_not_empty')
    output_name = 'verify-result.json' if operation == 'verify' else 'judge-result.json' if operation == 'judge' else 'result.json'
    if (out / output_name).exists():
        raise ValueError('worker_result_exists')
    schema = 'cad-harness.compile-result.v4c' if operation == 'compile' else 'cad-harness.verify-result.v4c' if operation in ('verify', 'judge') else 'cad-harness.native-worker.v4c'
    result = {'schema': schema, 'profile': profile,
              'operation': operation, 'status': 'FAIL', **_runtime(App), 'document_closed': False}
    try:
        if App.GuiUp != 0 or App.listDocuments():
            raise ValueError('headless_clean_runtime_required')
        ready_path = out.parent / (out.name + '.ready.json')
        ready_temp = ready_path.with_suffix('.tmp')
        ledger.write_json(ready_temp, _runtime(App))
        ready_temp.rename(ready_path)
        if operation == 'identity':
            result.update(_identity(App))
        elif operation == 'compile':
            result.update(_compile(App, job, out))
        elif operation in ('verify', 'judge'):
            result.update(_verify(App, job, out))
        elif operation == 'prepare-step':
            inputs = _module('cad_verify_v4_inputs')
            packet = inputs.inspect_step(job['manifest'], job['asset_id'], job['recipe'], out)
            if not (out / 'prepared.json').exists():
                ledger.write_json(out / 'prepared.json', packet)
            result.update(status='PASS', prepared=packet)
        elif operation == 'contour':
            contour = _module('cad_verify_v4_contours').prepare_contour(job['manifest'], job['asset_id'], job['recipe'], out)
            packet = {'schema': 'cad-harness.prepared.v4c', 'profile': 'c-s1',
                      'source_manifest_sha256': ledger.file_sha(job['manifest']),
                      'assets': {job['asset_id']: contour}}
            ledger.write_json(out / 'prepared.json', packet)
            result.update(status='PASS', prepared=packet, contour=contour)
        elif operation == 'text':
            outline = _module('cad_verify_v4_text').text_outline(job['manifest'], job['font_id'],
                      job['text'], job['height_mm'], out / 'text-outline.json')
            result.update(status='PASS', outline=outline)
    except Exception as exc:
        result.update(status='FAIL', error_type=type(exc).__name__, error=str(exc))
    finally:
        try:
            result['document_closed'] = _close(App)
        except Exception as exc:
            result.update(status='FAIL', close_error=str(exc))
        if result['document_closed'] is not True:
            result['status'] = 'FAIL'
    result['runtime'] = {**_runtime(App), 'document_closed': result['document_closed']}
    if operation == 'identity' and result['status'] == 'PASS':
        result['runtime']['files'] = {item['path']: item['sha256']
                                      for record in result['dependencies'].values()
                                      for item in record['files']}
        result['runtime']['files'].update({item['path']: item['sha256']
                                            for item in result['native_libraries']})
        result['runtime']['files'][sys.executable] = ledger.file_sha(sys.executable)
    ledger.write_json(out / output_name, result)
    return result


def main(argv=None):
    # The captured JSON wire is UTF-8, independent of the Windows console locale.
    sys.stdout.reconfigure(encoding='utf-8', errors='strict')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', required=True)
    args = parser.parse_args(argv)
    try:
        result = execute(_read(args.job))
    except Exception as exc:
        print(json.dumps({'status': 'FAIL', 'error_type': type(exc).__name__, 'error': str(exc)}, allow_nan=False), flush=True)
        return 1
    print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
