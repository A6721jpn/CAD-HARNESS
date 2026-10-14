"""Independent production-alpha native behavior; never launches CAD at discovery.

Set CAD_VERIFY_C2_RECIPE_NATIVE=1 under Python 3.11.14 / FreeCAD 1.1.4.
All sources are newly authored public DEV data in temporary directories. These
checks exercise the production registry/preparer and actual B-reps, not source
text, wiring echoes, analytic-prepared stand-ins, or a pilot-derived tolerance.
"""
from __future__ import annotations

import copy
import importlib.util
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE = (os.environ.get('CAD_VERIFY_C2_RECIPE_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
REASON = 'set CAD_VERIFY_C2_RECIPE_NATIVE=1 under pinned Python 3.11.14 / FreeCAD 1.1.4; no discovery launch'


@unittest.skipUnless(NATIVE, REASON)
class C2ProductionNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        from tools import cad_verify_v4_artifact_judges as adapter
        from tools import cad_verify_v4_artifacts as artifacts
        from tools import cad_verify_v4_c2_recipe as registry
        from tools import cad_verify_v4_compile as compiler
        from tools import cad_verify_v4_contours as contours
        from tools import cad_verify_v4_inputs as inputs
        from tools import cad_verify_v4_judges as judges
        from tools import cad_verify_v4_ledger as ledger

        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App, cls.Part = App, Part
        cls.adapter, cls.artifacts, cls.registry = adapter, artifacts, registry
        cls.compiler, cls.contours, cls.inputs, cls.judges, cls.ledger = compiler, contours, inputs, judges, ledger
        source = Path(__file__).resolve().parents[1]/'design/cad-harness-verify-v4/dev-c2-production/generate.py'
        spec = importlib.util.spec_from_file_location('independent_c2_production_sources', source)
        cls.source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.source)
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-production-native-')
        cls.addClassCleanup(temporary.cleanup)
        cls.result = cls.source.generate(Path(temporary.name)/'sources')
        cls.manifest = Path(cls.result['manifest_path'])
        cls.root = cls.manifest.parent
        cls.packet = ledger.read_json(cls.result['prepared_path'])
        cls.ring = cls.packet['assets']['ring']
        cls.recipe = registry.load()['recipe']
        cls.card = ledger.read_json(cls.result['card_path'])
        cls.context = adapter.validate_context(ledger.read_json(cls.result['context_path']), cls.manifest,
                                               cls.result['prepared_path'], cls.result['card_path'])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-recipe-case-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.sequence = 0

    def prepare(self, asset='ring', recipe=None):
        self.sequence += 1
        return self.contours.prepare_contour(self.manifest, asset, recipe or self.recipe,
                                            self.work/('prepared-%d' % self.sequence))

    def close(self, name):
        if name in self.App.listDocuments():
            self.App.closeDocument(name)

    def build(self, record):
        doc = self.App.newDocument('IndependentC2Case')
        self.addCleanup(self.close, doc.Name)
        packet = dict(schema='cad-harness.prepared.v4c', profile='c-s1',
                      source_manifest_sha256=self.ledger.file_sha(self.manifest),
                      assets={record['asset_id']: record})
        plan = dict(schema='cad-harness.plan.v4c', profile='c-s1', family='contour_extrude',
                    contour_id=record['asset_id'], width_mm=record['nominal_width_mm'],
                    thickness_mm=3., origin_mm=[0, 0, 0], references=[], engravings=[])
        body = self.compiler.build_plan(doc, plan, self.manifest, packet)
        doc.recompute()
        return doc, body, packet, plan

    def assert_uniform_mapping(self, before, after, factor, offset):
        self.assertEqual(len(before), len(after))
        for first, second in zip(before, after):
            self.assertEqual(first['role'], second['role'])
            self.assertEqual(first.get('parent'), second.get('parent'))
            self.assertEqual(len(first['segments']), len(second['segments']))
            for a, b in zip(first['segments'], second['segments']):
                self.assertEqual(a['kind'], b['kind'])
                for key in ('p0', 'pm', 'p1'):
                    if key in a:
                        for axis in (0, 1):
                            self.assertAlmostEqual(b[key][axis], factor*a[key][axis]+offset[axis], places=8)

    def test_deterministic_production_derivation_and_hash_closure(self):
        first, second = self.prepare(), self.prepare()
        self.assertEqual(first, second)
        self.assertEqual(first, self.ring)
        self.assertEqual(self.contours.validate_contour(copy.deepcopy(first)), first)
        self.assertEqual(first['recipe_sha256'], self.inputs.canonical_sha(self.recipe))
        self.assertEqual(first['source_image_sha256'], self.ledger.file_sha(self.result['fixture_paths']['ring']))
        self.assertEqual(first['mask_sha256'], self.inputs.canonical_sha(first['source_mask']))
        raw = {key: value for key, value in first.items() if key != 'record_sha256'}
        self.assertEqual(first['record_sha256'], self.inputs.canonical_sha(raw))
        bad = copy.deepcopy(first)
        bad['loops'][0]['segments'][0]['p0'][0] += .05
        with self.assertRaises(ValueError):
            self.contours.validate_contour(bad)
        # A self-consistent hash is not authority to alter frozen mask geometry.
        bad['record_sha256'] = self.inputs.canonical_sha(
            {key: value for key, value in bad.items() if key != 'record_sha256'})
        with self.assertRaises(ValueError):
            self.contours.validate_contour(bad)

    def test_alpha_127_128_129_cells_and_invisible_rgb_are_semantic(self):
        threshold = self.prepare('threshold')
        rows = threshold['source_mask']['rows']
        self.assertEqual(rows[:32], [[] for _ in range(32)])
        self.assertEqual(rows[32:96], [[[32, 104]] for _ in range(64)])
        self.assertEqual(rows[96:], [[] for _ in range(32)])
        self.assertEqual(sum(b-a for row in rows for a, b in row), 72*64)
        visible, invisible = self.prepare('ring'), self.prepare('invisible_rgb')
        self.assertNotEqual(visible['decoded_rgba_sha256'], invisible['decoded_rgba_sha256'])
        self.assertNotEqual(visible['source_image_sha256'], invisible['source_image_sha256'])
        for key in ('source_mask', 'mask_sha256', 'source_loops', 'loops', 'pixel_to_mm',
                    'bounds_mm', 'nominal_width_mm', 'reports', 'topology'):
            self.assertEqual(visible[key], invisible[key], key)

    def test_final_contour_height_order_and_uniform_aspect(self):
        # Fixed-mm dev mode independently exposes the same fit in pixel units.
        # This is a second real preparation, NOT an alternative production path.
        unit_recipe = copy.deepcopy(self.recipe)
        unit_recipe['scale'] = dict(mm_per_pixel=1., origin_mm=[0, 0])
        for asset in ('ellipse', 'rounded_rectangle'):
            with self.subTest(asset=asset):
                unit, final = self.prepare(asset, unit_recipe), self.prepare(asset)
                bounds = self.contours.geometry_bounds(unit)
                factor = 50./(bounds[3]-bounds[2])
                offset = [-factor*bounds[0], -factor*bounds[2]]
                self.assertAlmostEqual(final['pixel_to_mm']['scale_mm_per_pixel'], factor, places=10)
                self.assertAlmostEqual(final['bounds_mm'][0], 0., places=9)
                self.assertAlmostEqual(final['bounds_mm'][2], 0., places=9)
                self.assertAlmostEqual(final['bounds_mm'][3]-final['bounds_mm'][2], 50., places=9)
                self.assertAlmostEqual(final['nominal_width_mm']/50.,
                                       (bounds[1]-bounds[0])/(bounds[3]-bounds[2]), places=9)
                self.assert_uniform_mapping(unit['loops'], final['loops'], factor, offset)
                self.assert_uniform_mapping(unit['source_loops'], final['source_loops'], factor, offset)
                self.assertAlmostEqual(final['pixel_to_mm']['origin_mm'][0], offset[0], places=9)
                self.assertAlmostEqual(final['pixel_to_mm']['origin_mm'][1], offset[1], places=9)
                self.assertTrue(any(segment['kind'] == 'arc' for loop in final['loops']
                                    for segment in loop['segments']), 'smooth source must produce actual curves')
                doc, body, _, _ = self.build(final)
                self.assertTrue(body.Shape.isValid())
                self.assertEqual(len(body.Shape.Solids), 1)
                self.assertAlmostEqual(body.Shape.BoundBox.YLength, 50., places=7)
                self.assertAlmostEqual(body.Shape.BoundBox.XLength, final['nominal_width_mm'], places=7)
                self.close(doc.Name)

    def test_padding_changes_image_origin_not_canonical_geometry_or_scale(self):
        original, padded = self.prepare(), self.prepare('padded_ring')
        factor = original['pixel_to_mm']['scale_mm_per_pixel']
        self.assertAlmostEqual(padded['pixel_to_mm']['scale_mm_per_pixel'], factor, places=10)
        self.assert_uniform_mapping(original['loops'], padded['loops'], 1., [0., 0.])
        self.assert_uniform_mapping(original['source_loops'], padded['source_loops'], 1., [0., 0.])
        # Padding shifts original pixels +23 X and +21 world-up pixel Y.
        self.assertAlmostEqual(padded['pixel_to_mm']['origin_mm'][0],
                               original['pixel_to_mm']['origin_mm'][0]-23*factor, places=8)
        self.assertAlmostEqual(padded['pixel_to_mm']['origin_mm'][1],
                               original['pixel_to_mm']['origin_mm'][1]-21*factor, places=8)
        self.assertEqual(padded['source_mask']['width'], 176)
        self.assertEqual(padded['source_mask']['height'], 160)

    def test_genuine_sharp_corners_remain_and_actual_radius_fails_not_repaired(self):
        sharp = self.prepare('sharp')
        self.assertFalse(sharp['recipe']['rounding']['allowed'])
        self.assertEqual(self.contours.minimum_radius(sharp), 0.)
        self.assertEqual(sharp['reports']['minimum_radius_mm'], 0.)
        doc, body, packet, plan = self.build(sharp)
        self.assertTrue(body.Shape.isValid())
        card = dict(schema='cad-harness.judge-card.v4c', profile='c-s1', source='independent_dev',
                    linear_tolerance_mm=1e-5, criteria=[dict(id='actual', metric='min_radius',
                    contour_id='sharp', minimum_mm=.25, angular_tolerance_rad=1e-6)])
        result = self.judges.judge(plan, self.manifest, packet, body, card)
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertGreater(result['checks'][0]['measured']['sharp_corners'], 0)
        self.assertEqual(result['checks'][0]['measured']['minimum_mm'], 0.)
        self.close(doc.Name)

    def test_hole_preservation_empty_islands_and_diagonal_contacts(self):
        self.assertEqual(self.ring['topology']['source'],
                         dict(components=1, holes=1, euler_characteristic=0))
        self.assertEqual(self.ring['topology']['source'], self.ring['topology']['output'])
        self.assertEqual([loop['role'] for loop in self.ring['loops']], ['outer', 'hole'])
        self.assertEqual(self.ring['loops'][1]['parent'], 0)
        for asset, reason in (('empty', 'empty_mask'), ('island', 'multiple_islands'),
                              ('diagonal', 'nonmanifold')):
            with self.subTest(asset=asset), self.assertRaisesRegex(ValueError, reason):
                self.prepare(asset)

    def test_native_independent_annulus_both_arms_roundtrip_and_operative_edits(self):
        for arm in ('bare', 'harness'):
            with self.subTest(arm=arm):
                bundle, files, extensions = self.artifacts.load_bundle(self.result[arm+'_bundle_path'], profile='c-s1')
                if arm == 'bare':
                    self.assertEqual(bundle['probes'], [])
                    self.assertEqual(extensions, {})
                self.artifacts._guard_archive(files['native'], extensions, set(files.values()) | set(extensions.values()))
                doc = self.App.openDocument(str(files['native']))
                try:
                    body = doc.getObject(bundle['output_object'])
                    doc.recompute()
                    shape = body.Shape.copy()
                    self.assertTrue(shape.isValid())
                    self.assertEqual(len(shape.Solids), 1)
                    self.assertAlmostEqual(shape.BoundBox.YLength, 50., places=7)
                    self.assertAlmostEqual(shape.BoundBox.ZLength, 3., places=7)
                    if arm == 'bare':
                        self.assertAlmostEqual(shape.Volume, math.pi*(25**2-(25*20/48)**2)*3, places=6)
                        self.assertAlmostEqual(shape.BoundBox.XMin, 0., places=7)
                        self.assertAlmostEqual(shape.BoundBox.YMin, 0., places=7)
                    step = self.Part.Shape()
                    step.read(str(files['step']))
                    self.assertTrue(step.isValid())
                    self.assertEqual(len(step.Solids), 1)
                    editability, editable = self.artifacts.operative(self.App, doc, body, bundle['probes'])
                    self.assertTrue(editable, editability)
                    self.assertTrue(all(row['restored'] for row in editability['probes']))
                    self.assertGreater(editability['probes'][0]['symmetric_difference_mm3'], 0.)
                    if arm == 'bare':
                        self.assertEqual(editability['probes'][0]['probe']['property'], 'Length')
                    self.assertAlmostEqual(body.Shape.Volume, shape.Volume, places=6)
                    a, b = shape.BoundBox, step.BoundBox
                    bounds_difference = max(abs(getattr(a, key)-getattr(b, key)) for key in
                                            ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'))
                    evidence = dict(fcstd_reopened=True, step_reopened=True, editable=editable,
                                    bounds_difference_mm=bounds_difference,
                                    volume_difference_mm3=abs(shape.Volume-step.Volume))
                    result = self.adapter.judge(self.context, self.manifest, self.packet, body,
                                                self.card, native_evidence=evidence)
                    checks = {row['id']: row for row in result['checks']}
                    for key in ('solid', 'final_height', 'thickness', 'native', 'image_to_contour_iou',
                                'image_to_contour_hausdorff', 'contour_to_output_iou', 'contour_to_output_hausdorff'):
                        self.assertEqual(checks[key]['status'], 'PASS', result)
                    # Native sections, not preprocessing reports, must certify
                    # this independently authored smooth annulus's manufacture.
                    self.assertEqual(checks['actual_min_radius']['status'], 'PASS', result)
                    self.assertEqual(checks['actual_tool_access']['status'], 'PASS', result)
                finally:
                    self.App.closeDocument(doc.Name)

    def test_one_fixed_registration_rejects_post_scoring_refit_and_translation(self):
        doc = self.App.openDocument(str(self.ledger.read_json(self.result['bare_bundle_path'])['native']['path']))
        try:
            body = doc.getObject('IndependentAnnulus')
            shape = body.Shape.copy()
            source_before = self.ledger.file_sha(self.result['prepared_path'])
            card_before = self.ledger.file_sha(self.result['card_path'])
            shape.translate(self.App.Vector(3, 0, 0))
            result = self.adapter.judge(self.context, self.manifest, self.packet, shape, self.card)
            checks = {row['id']: row for row in result['checks']}
            self.assertEqual(checks['contour_to_output_hausdorff']['status'], 'FAIL', result)
            # Source leg is frozen and cannot move with the candidate bbox.
            self.assertEqual(checks['image_to_contour_iou']['status'], 'PASS', result)
            scaled = body.Shape.copy()
            scaled.scale(1.12)
            result = self.adapter.judge(self.context, self.manifest, self.packet, scaled, self.card)
            checks = {row['id']: row for row in result['checks']}
            self.assertEqual(checks['final_height']['status'], 'FAIL', result)
            self.assertEqual(checks['contour_to_output_hausdorff']['status'], 'FAIL', result)
            self.assertEqual(checks['image_to_contour_iou']['status'], 'PASS', result)
            self.assertEqual(self.ledger.file_sha(self.result['prepared_path']), source_before)
            self.assertEqual(self.ledger.file_sha(self.result['card_path']), card_before)
            bad = copy.deepcopy(self.packet)
            bad['assets']['ring']['pixel_to_mm']['origin_mm'][0] += 3
            with self.assertRaises(ValueError):
                self.contours.validate_contour(bad['assets']['ring'])
        finally:
            self.App.closeDocument(doc.Name)


if __name__ == '__main__':
    unittest.main()
