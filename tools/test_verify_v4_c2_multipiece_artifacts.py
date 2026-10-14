"""Source-bound compound artifact behavior; all geometry is independent dev data.

Native controls require CAD_VERIFY_C2_MULTIPIECE_NATIVE=1 in the pinned SDK.
No providers, private inputs, installs, or implicit native discovery launches.
"""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

from tools import cad_verify_v4_artifact_judges as adapter
from tools import cad_verify_v4_artifacts as artifacts
from tools import cad_verify_v4_integrated as integrated
from tools import cad_verify_v4_ledger as ledger
from tools.test_verify_v4_artifact_judges_native import ContextFixtures, card_for

NATIVE = (os.environ.get('CAD_VERIFY_C2_MULTIPIECE_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
REASON = 'set CAD_VERIFY_C2_MULTIPIECE_NATIVE=1 under pinned native FreeCAD Python'
ROOT = Path(__file__).resolve().parents[1]


class BoundCountAdmission(ContextFixtures, unittest.TestCase):
    def setUp(self):
        super().setUp()
        source = self.root / 'checker.step'
        source.write_bytes(b'ISO-10303-21;\n/* host admission only */\nEND-ISO-10303-21;')
        self.save_inputs('c-s1', {'checker': self.record(source, 'step', 'checker')})
        self.prepared = self.measurement_packet('c-s1')
        self.card = card_for('c-s1', dict(id='solid', metric='solid_valid'))
        self.value = self.context('C1', self.prepared, self.card)

    def test_other_family_bound_assets_do_not_grant_a_count_override(self):
        checked = self.admit(self.value)
        self.assertEqual(adapter.expected_solid_count(checked, self.prepared), 1)
        for field in ('expected_solids', 'solid_count', 'components'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.admit(dict(self.value, **{field: 3}))
        changed = copy.deepcopy(self.prepared)
        changed['assets']['checker']['topology']['solids'] = 3
        with self.assertRaisesRegex(ValueError, 'supplied_prepared_or_card'):
            adapter.expected_solid_count(checked, changed)
        with self.assertRaisesRegex(ValueError, 'requires_validate_context'):
            adapter.expected_solid_count(dict(checked), self.prepared)

    def test_integrated_geometry_rejects_extra_solids_for_authenticated_c1(self):
        checked = self.admit(self.value)
        shape = dict(valid=True, solids=1, volume_mm3=6., bounds_mm=[0, 1, 0, 2, 0, 3])
        result = dict(measurements={'fcstd': dict(shape), 'step': dict(shape)},
                      native_evidence=dict(bounds_difference_mm=0., volume_difference_mm3=0.))
        integrated._geometry_result(result, self.card, context=checked, prepared=self.prepared)
        for count in (0, 2, 3):
            bad = copy.deepcopy(result)
            bad['measurements']['step']['solids'] = count
            with self.subTest(count=count), self.assertRaisesRegex(Exception, 'invalid_geometry'):
                integrated._geometry_result(bad, self.card, context=checked, prepared=self.prepared)

    def test_count_derivation_rechecks_bound_context_and_card_bytes(self):
        checked = self.admit(self.value)
        checked['family'] = 'C2'
        with self.assertRaisesRegex(ValueError, 'frozen_measurements'):
            adapter.expected_solid_count(checked, self.prepared)
        checked = self.admit(self.value)
        with self.card_path.open('ab') as stream:
            stream.write(b'\n')
        with self.assertRaisesRegex(ValueError, 'card_sha256'):
            adapter.expected_solid_count(checked, self.prepared)


@unittest.skipUnless(NATIVE, REASON)
class CompoundArtifactBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        from tools import cad_verify_v4_runtime as runtime, cad_verify_v4_worker as worker
        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD')
        cls.App, cls.Part, cls.worker = App, Part, worker
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-artifact-fixtures-')
        cls.addClassCleanup(temporary.cleanup)
        cls.fixture_root = Path(temporary.name)
        source = ROOT / 'design/cad-harness-verify-v4/dev-c2-multipiece/generate.py'
        spec = importlib.util.spec_from_file_location('independent_c2_artifact_fixture', source)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        cls.fixture = generator.generate(cls.fixture_root / 'fixtures')
        cls.runtime_paths = {}
        for arm in ('bare', 'harness'):
            _, _, extensions = artifacts.load_bundle(cls.fixture[arm + '_bundle_path'])
            path = cls.fixture_root / (arm + '-runtime.json')
            ledger.write_json(path, runtime.capture(ROOT, extension_paths=extensions.values()))
            cls.runtime_paths[arm] = path

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-artifact-check-')
        self.addCleanup(temporary.cleanup)
        self.addCleanup(self.close_all)
        self.root = Path(temporary.name)
        self.sequence = 0

    def close_all(self):
        for name in list(self.App.listDocuments()):
            self.App.closeDocument(name)

    def run_check(self, arm='bare', *, bundle=None, card=None, context=None, prepared=None, manifest=None):
        self.sequence += 1
        out = self.root / ('check-' + str(self.sequence))
        out.mkdir()
        return self.worker.execute(dict(operation='artifact-verify', profile='c-s1',
            manifest=str(manifest or self.fixture['manifest_path']),
            prepared=str(prepared or self.fixture['prepared_path']),
            card=str(card or self.fixture['card_path']), context=str(context or self.fixture['context_path']),
            bundle=str(bundle or self.fixture[arm + '_bundle_path']),
            runtime_binding=str(self.runtime_paths[arm]), out=str(out)))

    def test_both_arms_reopen_step_and_edit_every_source_piece(self):
        for arm in ('bare', 'harness'):
            with self.subTest(arm=arm):
                result = self.run_check(arm)
                self.assertEqual(result['status'], 'PASS', result)
                self.assertTrue(result['document_closed'])
                for representation in ('fcstd', 'step'):
                    self.assertEqual(result['measurements'][representation]['solids'], 3)
                covered = {index for row in result['editability']['probes']
                           for index in row['changed_solid_indices']}
                self.assertEqual(covered, {0, 1, 2})
                checked = adapter.validate_context(ledger.read_json(self.fixture['context_path']),
                    self.fixture['manifest_path'], self.fixture['prepared_path'], self.fixture['card_path'])
                integrated._geometry_result(result, ledger.read_json(self.fixture['card_path']),
                    context=checked, prepared=ledger.read_json(self.fixture['prepared_path']))
                bundle = ledger.read_json(self.fixture[arm + '_bundle_path'])
                integrated._editability_result(result['editability'], bundle, expected_solids=3)

    def altered_bundle(self, *, count=None, step_count=None, only_one_probe=False):
        bundle, files, _ = artifacts.load_bundle(self.fixture['bare_bundle_path'])
        bundle = copy.deepcopy(bundle)
        if count is not None:
            doc = self.App.openDocument(str(files['native']))
            output = doc.getObject(bundle['output_object'])
            links = list(output.Links)
            if count < len(links):
                output.Links = links[:count]
            else:
                extra = doc.addObject('Part::Feature', 'UnrelatedExtraSolid')
                extra.Shape = self.Part.makeBox(1, 1, 3, self.App.Vector(70, 0, 0))
                output.Links = links + [extra]
            doc.recompute()
            native = self.root / ('count-' + str(count) + '.FCStd')
            doc.saveAs(str(native))
            self.App.closeDocument(doc.Name)
            bundle['native'] = self.file_record(native)
        if step_count is not None:
            shape = self.Part.Shape()
            shape.read(str(files['step']))
            solids = list(shape.Solids)
            if step_count < len(solids):
                solids = solids[:step_count]
            else:
                solids.append(self.Part.makeBox(1, 1, 3, self.App.Vector(70, 0, 0)))
            path = self.root / ('step-count-' + str(step_count) + '.step')
            self.Part.makeCompound(solids).exportStep(str(path))
            bundle['step'] = self.file_record(path)
        if only_one_probe:
            bundle['probes'] = bundle['probes'][:1]
        path = self.root / ('bundle-' + str(len(list(self.root.glob('bundle-*.json')))) + '.json')
        ledger.write_json(path, bundle)
        return path

    @staticmethod
    def file_record(path):
        return dict(path=str(path), sha256=ledger.file_sha(path), bytes=path.stat().st_size)

    def test_missing_and_extra_native_or_step_solids_fail(self):
        for representation in ('native', 'step'):
            for count in (2, 4):
                with self.subTest(representation=representation, count=count):
                    bundle = self.altered_bundle(**{'count' if representation == 'native' else 'step_count': count})
                    result = self.run_check(bundle=bundle)
                    self.assertEqual(result['status'], 'FAIL', result)
                    self.assertTrue(result['document_closed'])

    def test_one_operative_piece_cannot_certify_other_cached_pieces(self):
        result = self.run_check(bundle=self.altered_bundle(only_one_probe=True))
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertFalse(result['editability_ok'])
        self.assertTrue(result['editability']['probes'][0]['operative'])
        self.assertEqual(len(result['editability']['probes'][0]['changed_solid_indices']), 1)

    def test_other_families_cannot_admit_the_same_compound(self):
        card = card_for('c-s1', dict(id='solid', metric='solid_valid'))
        card_path = self.root / 'other-family-card.json'
        ledger.write_json(card_path, card)
        for family in ('C1', 'C3'):
            with self.subTest(family=family):
                context = ledger.read_json(self.fixture['context_path'])
                context.update(family=family, contour=None, card_sha256=ledger.file_sha(card_path))
                context_path = self.root / (family + '-context.json')
                ledger.write_json(context_path, context)
                result = self.run_check(card=card_path, context=context_path)
                self.assertEqual(result['status'], 'FAIL', result)
                self.assertIn('single_output_body', result['error'])

    def test_single_piece_c2_still_rejects_a_compound(self):
        from PIL import Image, ImageDraw
        from tools import cad_verify_v4_c2_recipe as registry, cad_verify_v4_contours as contours
        image = self.root / 'single.png'
        rgba = Image.new('RGBA', (80, 80), (91, 13, 250, 0))
        ImageDraw.Draw(rgba).ellipse((10, 10, 70, 70), fill=(31, 92, 117, 255))
        rgba.save(image)
        manifest = self.root / 'single-manifest.json'
        ledger.write_json(manifest, dict(schema='cad-harness.inputs.v4c', profile='c-s1',
            evidence_mode='independent_dev', assets={'single': dict(kind='image', role='checker',
                **dict(self.file_record(image), path=image.name))}))
        record = contours.prepare_contour(manifest, 'single', registry.load()['recipe'], self.root / 'single-contour')
        prepared = self.root / 'single-prepared.json'
        ledger.write_json(prepared, dict(schema='cad-harness.prepared.v4c', profile='c-s1',
            source_manifest_sha256=ledger.file_sha(manifest), assets={'single': record}))
        card = self.root / 'single-card.json'
        ledger.write_json(card, card_for('c-s1', dict(id='solid', metric='solid_valid')))
        context = self.root / 'single-context.json'
        ledger.write_json(context, dict(schema='cad-harness.artifact-context.v4', profile='c-s1', family='C2',
            manifest_sha256=ledger.file_sha(manifest), prepared_sha256=ledger.file_sha(prepared),
            card_sha256=ledger.file_sha(card), reference=None, engravings=[],
            contour=dict(contour_id='single', scale=1., origin_mm=[0, 0, 0], thickness_mm=3.)))
        checked = adapter.validate_context(ledger.read_json(context), manifest, prepared, card)
        self.assertEqual(adapter.expected_solid_count(checked, ledger.read_json(prepared)), 1)
        result = self.run_check(manifest=manifest, prepared=prepared, card=card, context=context)
        self.assertEqual(result['status'], 'FAIL', result)

    def test_worker_compile_then_reopen_uses_source_count(self):
        base = Path(self.fixture['prepared_path']).parent
        fields = dict(profile='c-s1', manifest=self.fixture['manifest_path'],
            prepared=self.fixture['prepared_path'], plan=str(base / 'harness-plan.json'), card=self.fixture['card_path'])
        compile_out = self.root / 'compiled'
        compile_out.mkdir()
        built = self.worker.execute(dict(operation='compile', out=str(compile_out), **fields))
        self.assertEqual(built['status'], 'PASS', built)
        self.assertEqual(built['measurements']['solids'], 3)
        verify_out = self.root / 'verified'
        verify_out.mkdir()
        result = self.worker.execute(dict(operation='verify', candidate_dir=str(compile_out),
            out=str(verify_out), **fields))
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['measurements']['step']['solids'], 3)
        self.assertTrue(result['document_closed'])


if __name__ == '__main__':
    unittest.main()
