"""Actual independent DEV construction/check/render across c-s1/c-s2/c-s3.

The 47-row protocol is covered by deterministic family tests. This smoke retains
its enrollment admission but constructs only three independent DEV records with
an injected provider. No holdout/pilot or live-model outcome is claimed.
"""
from contextlib import redirect_stdout
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_trials as trials, cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_model_judge as judge, eval_verify_v4 as cli
from tools.test_verify_v4_trials import Fixture
from tools.test_verify_v4_family_live import DevRegistration
from tools.test_verify_v4_live import response
from tools.test_support import start_tempdirs, stop_tempdirs

NATIVE = (os.environ.get('CAD_VERIFY_LAUNCHERS_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def _replace(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2)+'\n', encoding='utf-8')


def _rebind_manifest(value, digest):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('manifest_sha256_before', 'manifest_sha256_after'):
                value[key] = digest
            elif isinstance(item, (dict, list)):
                _rebind_manifest(item, digest)
    elif isinstance(value, list):
        for item in value:
            _rebind_manifest(item, digest)


def _install_case(registry, case, entry):
    """Stage independent geometry; enforce the signed family bound on DEV C5."""
    root = registry.root
    original = ledger.read_json(case['input_manifest_path'])
    manifest = dict(original, evidence_mode='custodian', assets={})
    for asset_id, source_record in original['assets'].items():
        binding = copy.deepcopy(source_record)
        source = Path(case['input_manifest_path']).parent / binding['path']
        relative = entry['id']+'-assets/'+binding['path']
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        binding['path'] = relative
        manifest['assets'][asset_id] = binding
        identity = entry['id']+'-asset-'+asset_id
        registry.files[identity] = dict(path=relative, sha256=binding['sha256'], bytes=binding['bytes'],
            role='font' if binding['kind']=='font' else 'license' if binding['kind']=='license' else 'source_asset',
            origin='published_cohort', published_relative_path='generative/'+entry['id']+'/'+source_record['path'])
        if binding['role'] != 'checker':
            entry['model_inputs'].append(identity)
    manifest_path = root / registry.files[entry['input_manifest']]['path']
    _replace(manifest_path, manifest)
    digest = ledger.file_sha(manifest_path)
    packet = ledger.read_json(case['prepared_path'])
    packet['source_manifest_sha256'] = digest
    _rebind_manifest(packet, digest)
    prepared = root / registry.files[entry['prepared']]['path']
    _replace(prepared, packet)
    card = root / registry.files[entry['card']]['path']
    if entry['family'] == 'C5':
        source_root = Path(case['prepared_path']).parent
        card_value = ledger.read_json(source_root / 'g2_pair-card.json')
        plan = ledger.read_json(source_root / 'g2_pair-plan.json')
        signed_limit = next(criterion['maximum_mm'] for criterion in registry.cards[entry['id']]['criteria']
                            if criterion['metric'] == 'surface_deviation')
        for criterion in card_value['criteria']:
            if criterion['metric'] == 'surface_deviation':
                criterion['maximum_mm'] = signed_limit
        plan['fit_tolerance_mm'] = min(plan['fit_tolerance_mm'], signed_limit)
    else:
        card_value = ledger.read_json(case['card_path'])
        plan = ledger.read_json(Path(case['context_path']).parent / 'harness-plan.json')
    _replace(card, card_value)
    context = ledger.read_json(case['context_path'])
    if entry['family'] == 'C5':
        context['reference'] = {key: copy.deepcopy(plan[key]) for key in ('asset_id', 'source_sha256', 'grid')}
    context.update(manifest_sha256=digest, prepared_sha256=ledger.file_sha(prepared), card_sha256=ledger.file_sha(card))
    _replace(root / registry.files[entry['context']]['path'], context)
    (root / registry.files[entry['request']]['path']).write_bytes(
        ('Independent DEV '+case['family']+' native construction and neutral verification.\r\n').encode())
    return plan


@unittest.skipUnless(NATIVE, 'set CAD_VERIFY_LAUNCHERS_NATIVE=1 under pinned native Python')
class NativeLauncherSmoke(unittest.TestCase):
    def test_authorized_custodian_plan_actual_native_and_visual_adjudication(self):
        report = os.environ.get('CAD_VERIFY_LAUNCHERS_REPORT')
        if report:
            root = Path(report).absolute()
            root.mkdir(parents=True, exist_ok=False)
        else:
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name)
        with patch.dict(os.environ, OMP_PROFILE='independent-unit-operator'):
            fixture = Fixture(root, count=1)
            fixture.source = root / 'dev-cohort'
            fixture.source.mkdir()
            registry = DevRegistration(fixture.source)
            cases = ledger.read_json(Path(os.environ['CAD_VERIFY_S1_FIXTURES']).parent / 'fixtures.json')['cases']
            by_family = {case['family']:case for case in cases}
            selected = [entry for entry in registry.value['entries'] if entry['id'] in ('C1-01','C4-01','C5-01')]
            plans = {}
            for entry in registry.value['entries']:
                if entry in selected:
                    plans[entry['profile']] = _install_case(registry, by_family[entry['family']], entry)
                else:
                    _replace(registry.path(entry['input_manifest']), dict(schema='unit_mock_input_manifest', assets={}))
            _replace(fixture.source / registry.files['roster']['path'],
                     dict(schema='cad-harness.family-roster.v1', independent_dev=True))
            rubric = dict(schema=judge.RUBRIC_SCHEMA, id='DEV-native-shape', items=[
                dict(id='geometry', criterion='Actual DEV geometry is visible in the approved views.', visual=True)])
            _replace(fixture.source / registry.files[registry.value['rubric']]['path'], rubric)
            for record in registry.files.values():
                path = fixture.source / record['path']
                record.update(sha256=ledger.file_sha(path), bytes=path.stat().st_size)
            registry.value['cohort'].update({key:registry.files['roster'][key] for key in ('path','sha256','bytes')})
            rows = [record['sha256']+'  '+str(record['bytes'])+'  '+record['published_relative_path']
                    for record in registry.files.values() if record['origin']=='published_cohort']
            public = fixture.source / registry.files['public']['path']
            public.write_text('## SHA-256\n\n```\n'+'\n'.join(rows)+'\n```\n', encoding='utf-8')
            registry.files['public'].update(sha256=ledger.file_sha(public), bytes=public.stat().st_size)
            fixture.registration = registry.value
            _replace(fixture.registration_path, fixture.registration)
            fixture.auth.update(phase='families', trial_id=registry.value['trial_id'], cycle_id=registry.value['cycle_id'],
                registration_sha256=ledger.file_sha(fixture.registration_path), reserved_calls=trials.reservations(registry.value))
            _replace(fixture.auth_path, fixture.auth)
            with redirect_stdout(io.StringIO()) as stdout:
                code = cli.main(['freeze-live-trial','--registration',str(fixture.registration_path),
                    '--authorization',str(fixture.auth_path),'--integrated-manifest',str(fixture.lock_path),
                    '--run-dir',str(fixture.manifest_path.parent)], verifier=fixture.verifier,
                    executable_resolver=fixture.resolver)
            self.assertEqual(code, 0, stdout.getvalue())
            calls = []
            def process(argv, captures, *, cwd, timeout):
                payload = ledger.read_json(next(Path(arg[1:]) for arg in argv if arg.startswith('@')))
                target = payload['runtime_data']['target']
                model = argv[argv.index('--model')+1]
                calls.append(dict(target=target, model=model, argv=list(argv)))
                if target == 'plan':
                    data = payload['runtime_data']['inputs']
                    self.assertNotIn('checker_stock', data['assets'])
                    text = json.dumps(plans[data['profile']])
                else:
                    text = json.dumps(dict(schema=judge.VERDICT_SCHEMA, rubric_id=rubric['id'],
                        items=[dict(id='geometry',status='PASS',reason='Injected DEV visual verdict')],
                        critical_dimension_error=False,fabrication=False))
                captures['stdout'].feed(response(text, model=model.removeprefix('openai-codex/')))
                captures['stderr'].feed(b'Injected DEV transport only\r\n')
                return 0
            records = []
            with trials.TrialSession(fixture.manifest_path, fixture.auth_path, root/'run', phase='families',
                    process=process, verifier=fixture.verifier) as session:
                for entry in selected:
                    # Synthetic local quota evidence, never a provider/quota call.
                    fixture.quota.write_text(json.dumps(dict(snapshot_id='independent-native-dev',
                        observed_at=ledger.utc(), used_percent=0)), encoding='utf-8')
                    result = session.execute_plan(entry, root/'run'/entry['id'],
                                                  pool=entry['family']+':generation', **trials.GENERATOR, max_calls=3)
                    self.assertEqual(result['status'], 'PASS', json.dumps(result, default=str))
                    native = result['artifact_verdict']['result']
                    self.assertTrue(native['geometry_ok'])
                    self.assertTrue(native['editability_ok'])
                    self.assertTrue(native['native_evidence']['fcstd_reopened'])
                    self.assertTrue(native['native_evidence']['step_reopened'])
                    self.assertEqual(len(result['images']), 4)
                    judgment = session.judge(entry['id'], 'Independent DEV shape judgment',
                        result['artifact_verdict'], rubric, pool=entry['family']+':judge', images=result['images'])
                    self.assertEqual(judgment['status'], 'PASS', judgment)
                    self.assertEqual(session.charged[entry['family']+':generation'], 1)
                    self.assertEqual(session.charged[entry['family']+':judge'], 1)
                    records.append(dict(id=entry['id'], profile=entry['profile'], result=result, judgment=judgment))
                self.assertEqual(session.summary()['live_calls'], 0)
                self.assertEqual([call['target'] for call in calls], ['plan','rubric_verdict']*3)
                ledger.write_json(root/'smoke-result.json', dict(schema='cad-harness.launcher-dev-smoke.v1',
                    evidence_mode='unit_mock', actual_native=True, live_calls=0, attempted_dev_records=3,
                    family_holdout='not_run', pilot='not_run', records=records, accounting=session.summary()))

    def test_contour_and_engraving_metadata_proves_actual_neutral_editability(self):
        from tools import cad_verify_v4_s1 as s1, cad_verify_v4_artifacts as artifacts
        from tools import cad_verify_v4_worker as worker
        report = os.environ.get('CAD_VERIFY_LAUNCHERS_REPORT')
        if report:
            root = Path(report).parent / 'native-probe-smoke'
            root.mkdir(parents=True, exist_ok=False)
        else:
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name)
        cases = ledger.read_json(Path(os.environ['CAD_VERIFY_S1_FIXTURES']).parent / 'fixtures.json')['cases']
        records = []
        for case in cases:
            if case['family'] not in ('C2', 'C3'):
                continue
            out = root / case['family']
            out.mkdir()
            with ledger.Journal(out/'compile-ledger.jsonl', case['family'], 'independent-dev') as journal:
                compiled = s1.native_work('compile', out/'compiled', journal, profile=case['profile'],
                    manifest=case['input_manifest_path'], prepared=case['prepared_path'], card=case['card_path'],
                    plan=str(Path(case['context_path']).parent/'harness-plan.json'))
            self.assertEqual(compiled['status'], 'PASS', compiled)
            pair = worker._artifacts(out/'compiled')
            extensions = [dict(module=module, **trials._record(
                trials.ROOT/'tools'/(module.removeprefix('tools.')+'.py')))
                for module in compiled['restoration_modules']]
            bundle = dict(schema='cad-harness.artifact-bundle.v4', profile=case['profile'],
                evidence_mode='independent_dev', native=pair['native'], step=pair['step'],
                output_object=compiled['output_object'], probes=compiled['artifact_probes'], extensions=extensions)
            bundle_path = out/'artifacts.json'
            ledger.write_json(bundle_path, bundle)
            result = artifacts.check(case['input_manifest_path'], case['prepared_path'], case['card_path'],
                case['context_path'], bundle_path, out/'neutral', profile=case['profile'])
            self.assertEqual(result['status'], 'PASS', result)
            self.assertTrue(result['result']['editability_ok'])
            self.assertTrue(result['result']['native_evidence']['editable'])
            records.append(dict(family=case['family'], compile=compiled, neutral=result))
        ledger.write_json(root/'probe-smoke.json', dict(schema='cad-harness.native-probe-dev-smoke.v1',
            evidence_mode='independent_dev', actual_native=True, live_calls=0, records=records))


if __name__ == '__main__':
    unittest.main()
