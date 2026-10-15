"""Offline C-R7 paired neutral stress evidence; never a live/model entry point.

Run: python -B -m tools.cad_verify_v4_c2_stress --out NEW --suite FROZEN
Optional repeated --case IDs are development diagnostics, never full-suite proof.
The bare arm is independent C++ construction from the SHARED production-derived
contour, NOT an independently traced/fitted source oracle. No suite runs here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SHA256 = '22fa7cff277a6445a65da6a31b8dfb62024c1bda5ed8c7a4f3c3b2a8052d1c70'
GIT_MANIFEST_SHA256 = '95786c1e84ff19a4216c96941e890816dcb439f54fd1916ddaa581a29ec00810'
SEMANTIC_MANIFEST_SHA256 = '766b0f1b888bb6a5898c0abe1b5a3d18c5d73dbee7b467a79c32936ea3260048'
SUITE_SHA256 = '0d18fb809e508bf011765bae529865d09569b311dc6053d86ed77aabfe36028c'
GENERATOR_SHA256 = 'c76fdd90e9b563ff819faf7e6a71d3ab81a1746ea821c062a6f447d61ab73e49'
DISCLOSURE = ('Independent C++ Sketcher/PartDesign Pad construction from the same declared '
              'typed production-derived canonical contour; NOT independent source tracing/fitting.')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def record(path):
    path = Path(path).absolute()
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def public_path(path):
    """Reject forbidden namespaces lexically before even resolving/statting them."""
    path = Path(path).absolute()
    if any(p.casefold() in ('pilot-user', 'v4-holdout-private') for p in path.parts):
        raise ValueError('forbidden_source_namespace')
    # Do not traverse directory links into undeclared source trees.
    for parent in (path, *path.parents):
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('linked_path_forbidden')
    return path


def snapshot_suite(suite):
    suite = public_path(suite)
    manifest_path = public_path(suite / 'manifest.json')
    raw = manifest_path.read_bytes()
    raw_digest = hashlib.sha256(raw).hexdigest()
    normalized_digest = hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
    if raw_digest not in (MANIFEST_SHA256, GIT_MANIFEST_SHA256) or normalized_digest != GIT_MANIFEST_SHA256:
        raise ValueError('frozen_manifest_hash_mismatch')
    manifest = json.loads(raw)
    semantic_digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()
    if semantic_digest != SEMANTIC_MANIFEST_SHA256:
        raise ValueError('frozen_manifest_semantics_mismatch')
    cases = manifest['cases']
    if (manifest['schema'] != 'cad-harness.c2-stress-suite.v1' or
            manifest['cases_count'] != 14 or len(cases) != 14 or
            len({c['id'] for c in cases}) != 14 or len({c['filename'] for c in cases}) != 14):
        raise ValueError('frozen_suite_requires_all_fourteen_unique_cases')
    files, digest = {'manifest.json': record(manifest_path)}, hashlib.sha256()
    generator = record(public_path(suite / 'generate.py'))
    if generator['sha256'] != GENERATOR_SHA256:
        raise ValueError('frozen_generator_hash_mismatch')
    files['generate.py'] = generator
    for case in cases:
        if case['filename'] != case['id'] + '.png' or Path(case['filename']).name != case['filename']:
            raise ValueError('suite_case_path_invalid')
        path = public_path(suite / case['filename'])
        item = record(path)
        if item['sha256'] != case['sha256'] or item['bytes'] != case['bytes']:
            raise ValueError('frozen_png_changed:' + case['id'])
        files[case['filename']] = item
        digest.update((case['id'] + ':' + item['sha256'] + ':').encode('utf-8'))
    if digest.hexdigest() != SUITE_SHA256 or manifest['suite_sha256'] != SUITE_SHA256:
        raise ValueError('frozen_suite_digest_mismatch')
    # Extra PNGs cannot disappear from the effective suite silently.
    if {p.name for p in suite.iterdir() if p.suffix.casefold() == '.png'} != {c['filename'] for c in cases}:
        raise ValueError('unexpected_suite_png')
    return dict(manifest=manifest, files=files, manifest_commitments=dict(
        actual_raw_sha256=raw_digest, checkout_raw_sha256=MANIFEST_SHA256,
        git_blob_raw_sha256=GIT_MANIFEST_SHA256, crlf_normalized_sha256=normalized_digest,
        semantic_json_sha256=semantic_digest, normalization='CRLF to LF for comparison only; never rewrite input'))


def select_cases(manifest, selected):
    if not selected:
        return manifest['cases'], 'full_suite'
    if len(set(selected)) != len(selected) or set(selected) - {c['id'] for c in manifest['cases']}:
        raise ValueError('unknown_or_duplicate_case_selection')
    return [c for c in manifest['cases'] if c['id'] in selected], 'development_selection'


def command_environment():
    # Closed child environment: no provider keys, authorization or live guard flags.
    permitted = {'systemroot', 'windir', 'path', 'pathext', 'temp', 'tmp', 'userprofile',
                 'appdata', 'localappdata', 'programdata', 'programfiles', 'programfiles(x86)',
                 'commonprogramfiles', 'comspec', 'number_of_processors', 'processor_architecture'}
    value = {k: v for k, v in os.environ.items() if k.casefold() in permitted}
    value.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', QT_QPA_PLATFORM='offscreen',
                 OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    return value


def run_command(argv, out, *, timeout):
    """Durable complete binary streams, including interruption/launch errors."""
    out = Path(out)
    out.mkdir()
    env = command_environment()
    started = time.time()
    event = dict(argv=[str(a) for a in argv], cwd=str(ROOT), env=env, stdin='DEVNULL',
                 started_unix_s=started, timeout_s=timeout, live_calls=0)
    event['collector_runtime'] = dict(python_version=sys.version, executable=record(sys.executable), runner=record(__file__))
    executable = Path(event['argv'][0])
    event['command_executable'] = record(executable) if executable.is_file() else dict(path=str(executable), missing=True)
    write_json(out / 'command.json', event)
    tick = time.monotonic()
    with (out / 'stdout.bin').open('wb') as stdout, (out / 'stderr.bin').open('wb') as stderr:
        try:
            process = subprocess.run(event['argv'], cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, timeout=timeout, check=False, shell=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            event['returncode'] = process.returncode
        except Exception as exc:
            event.update(returncode=None, error_type=type(exc).__name__, error=str(exc))
            stderr.write(traceback.format_exc().encode('utf-8'))
    event.update(wall_s=time.monotonic() - tick, finished_unix_s=time.time(),
                 stdout=record(out / 'stdout.bin'), stderr=record(out / 'stderr.bin'))
    write_json(out / 'command.json', event)
    return event


def protocol():
    path = ROOT / 'design/cad-harness-verify-v4/dev-c2-production/generate.py'
    spec = importlib.util.spec_from_file_location('c2_stress_fixed_dev_protocol', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native():
    import FreeCAD as App
    if sys.version_info[:3] != (3, 11, 14) or tuple(App.Version()[:3]) != ('1', '1', '4') or App.GuiUp != 0:
        raise ValueError('pinned_headless_FreeCAD_1_1_4_python_3_11_14_required')
    return App


def prepare_case(suite, case_id, out):
    native()
    from tools import cad_verify_v4_c2_recipe as registry
    from tools import cad_verify_v4_contours as contours
    from tools import cad_verify_v4_plans as plans
    from tools import cad_verify_v4_runtime as runtime
    from tools import cad_verify_v4_s1 as facade
    frozen = snapshot_suite(suite)
    case = next(c for c in frozen['manifest']['cases'] if c['id'] == case_id)
    out = Path(out)
    out.mkdir()
    source = public_path(Path(suite) / case['filename'])
    # Bundle an exact byte copy; typed asset paths must stay relative and
    # cannot escape their manifest root. Never re-encode the locked source.
    bundled = out / source.name
    shutil.copyfile(source, bundled)
    copied = record(bundled)
    if copied['sha256'] != case['sha256'] or copied['bytes'] != case['bytes']:
        raise ValueError('stress_source_copy_changed')
    manifest = out / 'manifest.json'
    write_json(manifest, dict(schema='cad-harness.inputs.v4c', profile='c-s1', evidence_mode='independent_dev',
        assets={'ring': dict(kind='image', role='checker', **dict(copied, path=bundled.name))}))
    production = registry.load()
    binding = runtime.capture(ROOT)
    implementation = facade.implementation_bindings(ROOT, profile='c-s1')
    write_json(out / 'runtime.json', binding)
    contour = contours.prepare_contour(manifest, 'ring', production['recipe'], out / 'production-contour')
    packet = dict(schema='cad-harness.prepared.v4c', profile='c-s1',
                  source_manifest_sha256=sha(manifest), assets={'ring': contour})
    prepared, card, context = (out / name for name in ('prepared.json', 'card.json', 'context.json'))
    write_json(prepared, packet)
    fixed = protocol()
    card_value = fixed._card(contour)
    # Tighten only measurement resolution, never the radius/area acceptance
    # budgets. Long boundaries otherwise leave a tube enclosure > 0.1 mm².
    tool_curve_tolerance = fixed.DEV_CONTROLS['curve_tolerance_mm'] / 4
    for criterion in card_value['criteria']:
        if criterion['metric'] == 'tool_access':
            criterion['curve_tolerance_mm'] = tool_curve_tolerance
    plans.validate_judge_card(card_value, profile='c-s1')
    write_json(card, card_value)
    write_json(context, dict(schema='cad-harness.artifact-context.v4', profile='c-s1', family='C2',
        manifest_sha256=sha(manifest), prepared_sha256=sha(prepared), card_sha256=sha(card),
        reference=None, engravings=[], contour=dict(contour_id='ring', scale=1., origin_mm=[0, 0, 0], thickness_mm=3.)))
    plan = dict(schema='cad-harness.plan.v4c', profile='c-s1', family='contour_extrude', contour_id='ring',
        width_mm=contour['nominal_width_mm'], thickness_mm=3., origin_mm=[0, 0, 0], references=[], engravings=[])
    plans.validate_plan(plan, manifest, packet, profile='c-s1')
    write_json(out / 'harness-plan.json', plan)
    runtime.verify(binding, root=ROOT)
    if implementation != facade.implementation_bindings(ROOT, profile='c-s1'):
        raise ValueError('preparation_implementation_drift')
    if snapshot_suite(suite) != frozen:
        raise ValueError('preparation_suite_drift')
    result = dict(status='PASS', evidence_mode='independent_dev', live_calls=0,
        bare_disclosure=DISCLOSURE, dev_uncertainty=dict(fixed.DEV_CONTROLS,
            tool_access_curve_tolerance_mm=tool_curve_tolerance),
        original_source=record(source), bundled_source=copied,
        fixed_card_source=record(ROOT / 'design/cad-harness-verify-v4/dev-c2-production/generate.py'),
        production_recipe={k: production[k] for k in ('path', 'sha256', 'canonical_sha256')},
        production_registration={k: production['registration'][k] for k in ('path', 'sha256', 'bytes')},
        implementation_bindings=implementation,
        shared_inputs={p.name: record(p) for p in (manifest, prepared, card, context, out / 'runtime.json')})
    write_json(out / 'preparation.json', result)
    return result


def component_loops(contour):
    """Each material island gets a Pad with only its immediately owned holes."""
    loops = contour['loops']
    return [[loop] + [child for child in loops if child['role'] == 'hole' and child.get('parent') == index]
            for index, loop in enumerate(loops) if loop['role'] == 'outer']


def build_bare(doc, contour):
    """Own C++ geometry/Sketcher/Pad graph. No compiler, plan or Python proxy."""
    import FreeCAD as App
    import Part
    import Sketcher
    bodies, probes = [], []
    for index, loops in enumerate(component_loops(contour)):
        body = doc.addObject('PartDesign::Body', 'IndependentPiece' + str(index))
        sketch = body.newObject('Sketcher::SketchObject', 'CanonicalSketch' + str(index))
        for loop in loops:
            for segment in loop['segments']:
                def point(key):
                    return App.Vector(*segment[key], 0)
                if segment['kind'] == 'line':
                    geometry = Part.LineSegment(point('p0'), point('p1'))
                elif segment['kind'] == 'arc':
                    geometry = Part.Arc(point('p0'), point('pm'), point('p1'))
                else:
                    raise ValueError('bare_requires_declared_line_arc_contour')
                number = sketch.addGeometry(geometry, False)
                sketch.addConstraint(Sketcher.Constraint('Block', number))
        pad = body.newObject('PartDesign::Pad', 'OrdinaryPad' + str(index))
        pad.Profile, pad.Length = sketch, 3.
        body.Tip = pad
        bodies.append(body)
        probes.append(dict(kind='scalar', object=pad.Name, property='Length', delta=.01))
    if not bodies:
        raise ValueError('bare_no_declared_material_pieces')
    if len(bodies) == 1:
        output = bodies[0]
    else:
        output = doc.addObject('Part::Compound', 'IndependentCompound')
        output.Links = bodies
    doc.recompute()
    return output, probes


def build_case(preparation, arm, out):
    App = native()
    from tools import cad_verify_v4_runtime as runtime
    from tools import cad_verify_v4_s1 as facade
    preparation, out = Path(preparation), Path(out)
    shared = read_json(preparation / 'preparation.json')
    for item in shared['shared_inputs'].values():
        if record(item['path']) != item:
            raise ValueError('shared_preparation_input_changed')
    binding = read_json(preparation / 'runtime.json')
    runtime.verify(binding, root=ROOT)
    if shared['implementation_bindings'] != facade.implementation_bindings(ROOT, profile='c-s1'):
        raise ValueError('construction_implementation_drift')
    packet = read_json(preparation / 'prepared.json')
    contour = packet['assets']['ring']
    expected_solids = contour['topology']['source']['components']
    out.mkdir()
    doc = App.newDocument('Stress' + arm)
    try:
        if arm == 'bare':
            output, probes = build_bare(doc, contour)
        else:
            from tools import cad_verify_v4_compile as compiler
            output = compiler.build_plan(doc, read_json(preparation / 'harness-plan.json'), preparation / 'manifest.json', packet)
            features = [obj for obj in doc.Objects if 'Thickness' in obj.PropertiesList
                        and 'Proxy' in obj.PropertiesList and obj.Proxy is not None]
            probes = [dict(kind='scalar', object=obj.Name, property='Thickness', delta=.01) for obj in features]
            if not probes:
                raise ValueError('harness_missing_operative_thickness_probe')
        doc.recompute()
        shape = output.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != expected_solids or shape.Volume <= 0:
            raise ValueError('construction_invalid_or_lost_piece')
        native_path, step = out / 'part.FCStd', out / 'part.step'
        doc.saveAs(str(native_path))
        shape.exportStep(str(step))
        extensions = {}
        for obj in doc.Objects:
            if 'Proxy' in obj.PropertiesList and obj.Proxy is not None:
                if arm == 'bare':
                    raise ValueError('bare_python_proxy_forbidden')
                cls = type(obj.Proxy)
                source = inspect.getsourcefile(cls)
                if source is None:
                    raise ValueError('unbound_harness_extension')
                extensions[cls.__module__] = dict(module=cls.__module__, **record(source))
        bundle = dict(schema='cad-harness.artifact-bundle.v4', profile='c-s1', evidence_mode='independent_dev',
            native=record(native_path), step=record(step), output_object=output.Name, probes=probes,
            extensions=list(extensions.values()))
        write_json(out / 'artifacts.json', bundle)
    finally:
        App.closeDocument(doc.Name)
    runtime.verify(binding, root=ROOT)
    for item in shared['shared_inputs'].values():
        if record(item['path']) != item:
            raise ValueError('construction_changed_shared_input')
    if shared['implementation_bindings'] != facade.implementation_bindings(ROOT, profile='c-s1'):
        raise ValueError('construction_implementation_drift')
    result = dict(status='PASS', arm=arm, expected_solids=expected_solids, live_calls=0,
                  bundle=record(out / 'artifacts.json'), document_closed=True, gui_up=App.GuiUp,
                  shared_inputs=shared['shared_inputs'], bare_disclosure=DISCLOSURE)
    write_json(out / 'construction.json', result)
    return result


def neutral_pass(command, summary, preparation):
    if command.get('returncode') != 0 or summary.get('status') != 'PASS':
        return False
    result = summary.get('result', {})
    if not result.get('editability_ok') or result.get('status') != 'PASS':
        return False
    expected_ids = {c['id'] for c in read_json(Path(preparation) / 'card.json')['criteria']}
    for representation in ('fcstd', 'step'):
        judge = result.get('judges', {}).get(representation, {})
        checks = judge.get('checks', [])
        if (judge.get('status') != 'PASS' or len(checks) != len(expected_ids) or
                {c.get('id') for c in checks} != expected_ids or any(c.get('status') != 'PASS' for c in checks)):
            return False
    runtime_path = result.get('runtime_binding', {}).get('path')
    if not runtime_path:
        return False
    actual = read_json(runtime_path)
    shared = read_json(Path(preparation) / 'runtime.json')
    # The native checker independently binds each bundle's declared extension
    # dependencies (none for C++ bare; compiler proxy for harness). SDK, caches
    # and roots must still be identical to the shared preparation runtime.
    return ({k: v for k, v in actual.items() if k != 'extension_files'} ==
            {k: v for k, v in shared.items() if k != 'extension_files'})


def aggregate(rows, expected_ids, *, label, integrity_ok):
    ids = [row['case_id'] for row in rows]
    complete = len(ids) == len(expected_ids) and len(set(ids)) == len(ids) and set(ids) == set(expected_ids)
    passing = complete and integrity_ok and all(row.get('status') == 'PASS' and
        all(row.get('arms', {}).get(arm, {}).get('status') == 'PASS' for arm in ('bare', 'harness')) for row in rows)
    final = label == 'full_suite' and len(expected_ids) == 14 and passing
    return dict(status='PASS' if final else 'BLOCKED', development_status='PASS' if passing else 'FAIL',
        label=label, full_suite_pass=final, selected_count=len(expected_ids), reported_count=len(rows),
        complete=complete, suite_integrity_ok=integrity_ok, passed_cases=sum(r.get('status') == 'PASS' for r in rows),
        cases=rows, live_calls=0, authorization=None, final_v4_ready=False, bare_disclosure=DISCLOSURE)


def command_failure(command, fallback):
    """Surface the actual final native exception without dropping raw stderr."""
    reason, error_type = command.get('error'), command.get('error_type')
    path = command.get('stderr', {}).get('path')
    if path:
        try:
            lines = Path(path).read_bytes().decode('utf-8', errors='replace').splitlines()
            final = next((line.strip() for line in reversed(lines) if line.strip()), None)
            if final:
                reason = final
                name, separator, _ = final.partition(':')
                if separator and name.isidentifier():
                    error_type = name
        except OSError:
            pass
    return dict(reason=reason or fallback, error_type=error_type, stderr=command.get('stderr'))


def run(out, suite, selected=None, *, timeout=1800):
    from tools import cad_run
    out, suite = public_path(out), public_path(suite)
    if out == suite or suite in out.parents or out in suite.parents:
        raise ValueError('evidence_must_be_separate_from_frozen_suite')
    if out.exists():
        raise ValueError('fresh_output_directory_required')
    out.mkdir(parents=True)
    rows, integrity_ok, error = [], False, None
    before, cases, label = None, [], 'full_suite' if not selected else 'development_selection'
    try:
        before = snapshot_suite(suite)
        write_json(out / 'suite-before.json', before)
        cases, label = select_cases(before['manifest'], selected)
        native_python = str(cad_run.FREECAD_DIR / 'bin/python.exe')
        prefix = [native_python, '-B', '-m', 'tools.cad_verify_v4_c2_stress']
        for case in cases:
            case_out = out / case['id']
            case_out.mkdir()
            preparation = case_out / 'prepared'
            row = dict(case_id=case['id'], source=case, status='FAIL', arms={
                arm: dict(status='FAIL', reason='not_constructed') for arm in ('bare', 'harness')}, commands=[])
            try:
                command = run_command(prefix + ['_prepare', '--suite', str(suite), '--case-id', case['id'],
                    '--out', str(preparation)], case_out / 'command-prepare', timeout=timeout)
                row['commands'].append(command)
                if command['returncode'] != 0 or not (preparation / 'preparation.json').is_file():
                    row['preparation_failure'] = command_failure(command, 'source_preparation_failed_both_arms')
                    raise ValueError('source_preparation_failed_both_arms:' + row['preparation_failure']['reason'])
                row['preparation'] = read_json(preparation / 'preparation.json')
                builds = {}
                for arm in ('bare', 'harness'):
                    builds[arm] = run_command(prefix + ['_build', '--preparation', str(preparation), '--arm', arm,
                        '--out', str(case_out / arm)], case_out / ('command-build-' + arm), timeout=timeout)
                    row['commands'].append(builds[arm])
                # Actual neutral CLI twice; do not stop if the first arm fails.
                for arm in ('bare', 'harness'):
                    if builds[arm]['returncode'] != 0 or not (case_out / arm / 'construction.json').is_file():
                        row['arms'][arm] = dict(status='FAIL', reason='construction_failed')
                        continue
                    try:
                        command = run_command([sys.executable, '-B', '-m', 'tools.eval_verify_v4', 'judge-artifacts',
                            '--profile', 'c-s1', '--input-manifest', str(preparation / 'manifest.json'),
                            '--prepared', str(preparation / 'prepared.json'), '--card', str(preparation / 'card.json'),
                            '--context', str(preparation / 'context.json'), '--artifact-bundle',
                            str(case_out / arm / 'artifacts.json'), '--run-dir', str(case_out / ('neutral-' + arm))],
                            case_out / ('command-judge-' + arm), timeout=timeout)
                        row['commands'].append(command)
                        path = case_out / ('neutral-' + arm) / 'summary.json'
                        summary = read_json(path) if path.is_file() else {}
                        row['arms'][arm] = dict(status='PASS' if neutral_pass(command, summary, preparation) else 'FAIL',
                            construction=read_json(case_out / arm / 'construction.json'), neutral_summary=summary,
                            neutral_summary_path=str(path), command=command)
                    except Exception as exc:
                        row['arms'][arm] = dict(status='FAIL', reason=str(exc), error_type=type(exc).__name__)
                row['status'] = 'PASS' if all(a['status'] == 'PASS' for a in row['arms'].values()) else 'FAIL'
            except Exception as exc:
                row.update(error=str(exc), error_type=type(exc).__name__)
                for arm in row['arms']:
                    row['arms'][arm].update(status='FAIL', reason=str(exc))
            rows.append(row)
            write_json(case_out / 'report.json', row)
    except Exception as exc:
        error = dict(error=str(exc), error_type=type(exc).__name__)
    finally:
        try:
            after = snapshot_suite(suite)
            write_json(out / 'suite-after.json', after)
            integrity_ok = before is not None and before == after
        except Exception as exc:
            write_json(out / 'suite-after.json', dict(status='FAIL', error=str(exc), error_type=type(exc).__name__))
        summary = aggregate(rows, [c['id'] for c in cases], label=label, integrity_ok=integrity_ok)
        if error:
            summary.update(status='BLOCKED', development_status='FAIL', full_suite_pass=False, runner_error=error)
        summary.update(schema='cad-harness.c2-stress-evidence.v1', suite=str(suite), runner=record(__file__))
        write_json(out / 'summary.json', summary)
    return summary


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ('_prepare', '_build'):
        action = argv.pop(0)
        parser = argparse.ArgumentParser(description='Internal isolated offline construction worker')
        parser.add_argument('--out', required=True)
        if action == '_prepare':
            parser.add_argument('--suite', required=True)
            parser.add_argument('--case-id', required=True)
        else:
            parser.add_argument('--preparation', required=True)
            parser.add_argument('--arm', choices=('bare', 'harness'), required=True)
        args = parser.parse_args(argv)
        try:
            result = (prepare_case(public_path(args.suite), args.case_id, public_path(args.out)) if action == '_prepare'
                      else build_case(public_path(args.preparation), args.arm, public_path(args.out)))
        except Exception:
            traceback.print_exc()
            return 1
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--out', required=True)
        parser.add_argument('--suite', required=True)
        parser.add_argument('--case', action='append', help='Development diagnostic only, never final full-suite evidence')
        args = parser.parse_args(argv)
        try:
            result = run(args.out, args.suite, args.case)
        except Exception:
            traceback.print_exc()
            return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
