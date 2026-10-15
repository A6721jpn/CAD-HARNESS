"""Independent DEV native regressions; opt in with CAD_VERIFY_C2_MULTIPIECE_NATIVE=1."""
from __future__ import annotations
import copy
import importlib.util
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE = (os.environ.get('CAD_VERIFY_C2_MULTIPIECE_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)


@unittest.skipUnless(NATIVE, 'requires opt-in pinned Python 3.11.14 / FreeCAD 1.1.4; no discovery launch')
class C2MultipieceNative(unittest.TestCase):
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
        path = Path(__file__).resolve().parents[1]/'design/cad-harness-verify-v4/dev-c2-multipiece/generate.py'
        spec = importlib.util.spec_from_file_location('independent_multi_sources', path)
        cls.source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.source)
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-multi-native-')
        cls.addClassCleanup(temporary.cleanup)
        cls.result = cls.source.generate(Path(temporary.name)/'sources')
        cls.manifest = Path(cls.result['manifest_path'])
        cls.packet = ledger.read_json(cls.result['prepared_path'])
        cls.record = cls.packet['assets']['ring']
        cls.recipe = registry.load()['recipe']
        cls.card = ledger.read_json(cls.result['card_path'])
        cls.context = adapter.validate_context(ledger.read_json(cls.result['context_path']), cls.manifest,
            cls.result['prepared_path'], cls.result['card_path'])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-multi-case-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.sequence = 0

    def prepare(self, asset='ring', recipe=None):
        self.sequence += 1
        return self.contours.prepare_contour(self.manifest, asset, recipe or self.recipe,
            self.work/('prepared-%d' % self.sequence))

    def checks(self, shape, card=None):
        result = self.adapter.judge(self.context, self.manifest, self.packet, shape, card or self.card)
        return {row['id']: row for row in result['checks']}

    def open_arm(self, arm):
        bundle, files, extensions = self.artifacts.load_bundle(self.result[arm+'_bundle_path'], profile='c-s1')
        self.artifacts._guard_archive(files['native'], extensions, set(files.values()) | set(extensions.values()))
        doc = self.App.openDocument(str(files['native']))
        self.addCleanup(self.App.closeDocument, doc.Name)
        doc.recompute()
        return doc, doc.getObject(bundle['output_object']), bundle, files

    def test_topology_nested_parents_and_authenticated_count(self):
        record = self.record
        self.assertEqual(record, self.prepare())
        self.assertEqual(record['topology']['source'], dict(components=3, holes=1, euler_characteristic=2))
        self.assertEqual(record['topology']['output'], record['topology']['source'])
        self.assertEqual(self.inputs.contour_solid_count(record), 3)
        loops = record['loops']
        self.assertEqual(sum(loop['role'] == 'outer' for loop in loops), 3)
        hole = next(i for i, loop in enumerate(loops) if loop['role'] == 'hole')
        self.assertEqual(loops[loops[hole]['parent']]['role'], 'outer')
        self.assertEqual(sum(loop.get('parent') == hole for loop in loops), 1)
        for count in (0, True, 2, 4, 3.0):
            bad = copy.deepcopy(record)
            bad['topology']['source']['components'] = count
            with self.assertRaises(ValueError):
                self.inputs.contour_solid_count(bad)
        bad = copy.deepcopy(record)
        bad['loops'][hole]['parent'] = hole
        with self.assertRaises(ValueError):
            self.contours.validate_contour(bad)

    def test_global_scaling_padding_alpha_and_strict_mode(self):
        historical = self.ledger.read_json(
            self.registry.ROOT/'design/cad-harness-verify-v4/c2-production-recipe-cycle2.json')
        final = self.prepare(recipe=historical)
        unit = copy.deepcopy(historical)
        unit['scale'] = dict(mm_per_pixel=1., origin_mm=[0, 0])
        first = self.prepare(recipe=unit)
        bounds = self.contours.geometry_bounds(first)
        factor = 50/(bounds[3]-bounds[2])
        self.assertAlmostEqual(final['pixel_to_mm']['scale_mm_per_pixel'], factor, places=9)
        for before, after in zip(first['loops'], final['loops']):
            for a, b in zip(before['segments'], after['segments']):
                for key in ('p0', 'pm', 'p1'):
                    if key in a:
                        self.assertAlmostEqual(b[key][0], factor*(a[key][0]-bounds[0]), places=8)
                        self.assertAlmostEqual(b[key][1], factor*(a[key][1]-bounds[2]), places=8)
        for asset in ('padded_ring', 'invisible_rgb'):
            value = self.prepare(asset)
            self.assertEqual(value['topology'], self.record['topology'])
            self.assertAlmostEqual(value['nominal_width_mm'], self.record['nominal_width_mm'], places=8)
            for key in ('loops', 'source_loops'):
                self.assertEqual(len(value[key]), len(self.record[key]))
                for a, b in zip(value[key], self.record[key]):
                    self.assertEqual(a['role'], b['role'])
                    self.assertEqual(a.get('parent'), b.get('parent'))
                    self.assertEqual(len(a['segments']), len(b['segments']))
                    for sa, sb in zip(a['segments'], b['segments']):
                        self.assertEqual(sa['kind'], sb['kind'])
                        for point in ('p0', 'pm', 'p1'):
                            if point in sa:
                                for axis in (0, 1):
                                    self.assertAlmostEqual(sa[point][axis], sb[point][axis], places=8)
        strict = copy.deepcopy(self.recipe)
        strict['topology'].update(components=1, holes='preserve', islands='reject')
        with self.assertRaises(ValueError):
            self.prepare(recipe=strict)
        fake_count = copy.deepcopy(self.recipe)
        fake_count['topology']['components'] = 3
        with self.assertRaises(ValueError):
            self.prepare(recipe=fake_count)
        analytic = {key: copy.deepcopy(self.record[key]) for key in
            ('schema', 'profile', 'asset_id', 'source_image_sha256', 'units', 'bounds_mm',
             'nominal_width_mm', 'loops', 'pixel_to_mm')}
        analytic.update(source_sha256=self.ledger.file_sha(self.manifest), source_image_asset_id='ring',
            provenance=dict(kind='independent_analytic_source'), topology=dict(components=3, holes=1))
        with self.assertRaises(ValueError):
            self.contours.validate_contour(analytic)

    def test_both_real_native_roundtrips_all_piece_edits_and_full_card(self):
        for arm in ('bare', 'harness'):
            with self.subTest(arm=arm):
                doc, output, bundle, files = self.open_arm(arm)
                shape = output.Shape.copy()
                self.assertTrue(shape.isValid())
                self.assertEqual(len(shape.Solids), 3)
                self.assertAlmostEqual(shape.BoundBox.YLength, 50., places=7)
                self.assertAlmostEqual(shape.BoundBox.ZLength, 3., places=7)
                if arm == 'bare':
                    self.assertEqual(bundle['extensions'], [])
                    self.assertAlmostEqual(shape.Volume, math.pi*(18.75**2-9.375**2+(25/6)**2+6.25**2)*3, places=6)
                    for probe in bundle['probes']:
                        pad = doc.getObject(probe['object'])
                        old = pad.Length.Value
                        pad.Length = old+.5
                        doc.recompute()
                        self.assertEqual(len(output.Shape.Solids), 3)
                        self.assertGreater(output.Shape.Volume, shape.Volume)
                        pad.Length = old
                        doc.recompute()
                else:
                    old = output.Thickness.Value
                    output.Thickness = old+.5
                    doc.recompute()
                    self.assertEqual(len(output.Shape.Solids), 3)
                    for solid in output.Shape.Solids:
                        self.assertAlmostEqual(solid.BoundBox.ZLength, 3.5, places=7)
                    output.Thickness = old
                    doc.recompute()
                step = self.Part.Shape()
                step.read(str(files['step']))
                self.assertTrue(step.isValid())
                self.assertEqual(len(step.Solids), 3)
                operative, editable = self.artifacts.operative(self.App, doc, output, bundle['probes'],
                    expected_solids=self.inputs.contour_solid_count(self.record))
                self.assertTrue(editable, operative)
                a, b = shape.BoundBox, step.BoundBox
                evidence = dict(fcstd_reopened=True, step_reopened=True, editable=editable,
                    bounds_difference_mm=max(abs(getattr(a, key)-getattr(b, key)) for key in
                        ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')),
                    volume_difference_mm3=abs(shape.Volume-step.Volume))
                result = self.adapter.judge(self.context, self.manifest, self.packet, output, self.card,
                    native_evidence=evidence)
                self.assertEqual(result['status'], 'PASS', result)

    def test_dropped_moved_merged_and_hole_corruptions_are_rejected(self):
        _, output, _, _ = self.open_arm('bare')
        solids = sorted(output.Shape.Solids, key=lambda solid: solid.Volume)
        dropped = self.Part.makeCompound(solids[1:])
        self.assertEqual(self.checks(dropped)['solid']['status'], 'FAIL')
        moved = [solid.copy() for solid in solids]
        moved[0].translate(self.App.Vector(4, 0, 0))
        checks = self.checks(self.Part.makeCompound(moved))
        self.assertEqual(checks['contour_to_output_hausdorff']['status'], 'FAIL')
        ring = max(solids, key=lambda solid: solid.Volume)
        filled = self.Part.makeCylinder(18.75, 3, self.App.Vector(18.75, 18.75, 0))
        disk = max((solid for solid in solids if solid is not ring), key=lambda solid: solid.BoundBox.XMax)
        self.assertEqual(self.checks(self.Part.makeCompound([filled, disk]))['solid']['status'], 'FAIL')
        bridge = self.Part.makeBox(30, 2, 3, self.App.Vector(18, 18, 0))
        merged = output.Shape.fuse(bridge)
        checks = self.checks(merged)
        self.assertTrue(any(checks[key]['status'] == 'FAIL' for key in
            ('solid', 'contour_to_output_iou', 'contour_to_output_hausdorff')))
        moved_hole = self.Part.makeCylinder(18.75, 3, self.App.Vector(18.75, 18.75, 0)).cut(
            self.Part.makeCylinder(9.375, 3, self.App.Vector(21.75, 18.75, 0)))
        others = [solid for solid in solids if solid.Volume < ring.Volume]
        self.assertEqual(self.checks(self.Part.makeCompound([moved_hole]+others))[
            'contour_to_output_hausdorff']['status'], 'FAIL')

    def test_small_sharp_piece_cannot_hide_in_aggregate_area(self):
        record = self.prepare('small_sharp')
        doc = self.App.newDocument('SmallSharpMulti')
        self.addCleanup(self.App.closeDocument, doc.Name)
        packet = dict(schema='cad-harness.prepared.v4c', profile='c-s1',
            source_manifest_sha256=self.ledger.file_sha(self.manifest), assets={'small_sharp': record})
        plan = dict(schema='cad-harness.plan.v4c', profile='c-s1', family='contour_extrude',
            contour_id='small_sharp', width_mm=record['nominal_width_mm'], thickness_mm=3.,
            origin_mm=[0, 0, 0], references=[], engravings=[])
        output = self.compiler.build_plan(doc, plan, self.manifest, packet)
        doc.recompute()
        self.assertEqual(len(output.Shape.Solids), 4)
        # The source-frozen fitter may now legitimately approximate this tiny
        # component. Corrupt only the submitted native piece into a sharp box:
        # aggregate fidelity must not substitute for all-piece actual min-R.
        solids = list(output.Shape.Solids)
        smallest = min(solids, key=lambda solid: solid.Volume)
        bounds = smallest.BoundBox
        box = self.Part.makeBox(bounds.XLength, bounds.YLength, bounds.ZLength,
            self.App.Vector(bounds.XMin, bounds.YMin, bounds.ZMin))
        candidate = doc.addObject('Part::Feature', 'UnsafeTinyPiece')
        candidate.Shape = self.Part.makeCompound(
            [box] + [solid for solid in solids if solid is not smallest])
        card = dict(schema='cad-harness.judge-card.v4c', profile='c-s1', source='independent_dev',
            linear_tolerance_mm=1e-5, criteria=[dict(id='actual', metric='min_radius',
                contour_id='small_sharp', minimum_mm=.25, angular_tolerance_rad=1e-6, projection_z_mm=1.5)])
        result = self.judges.judge(plan, self.manifest, packet, candidate, card)
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertGreater(result['checks'][0]['measured']['sharp_corners'], 0)


    def test_tool_center_connectivity_is_per_piece_not_one_global_path(self):
        shapes = [self.Part.makeCylinder(5., 3., self.App.Vector(x, 0, 0)) for x in (0., 15.)]
        record = self.judges._shape_record(self.Part.makeCompound(shapes), 1.5)
        criterion = copy.deepcopy(next(c for c in self.card['criteria'] if c['metric'] == 'tool_access'))
        criterion['require_connected'] = True
        result = self.judges.tool_access(record, criterion)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['center_components'], 2)
        self.assertTrue(result['topology_stable'])

    def test_same_global_counts_cannot_hide_a_moved_nested_piece(self):
        _, output, _, _ = self.open_arm('bare')
        solids = sorted(output.Shape.Solids, key=lambda solid: solid.Volume)
        island = solids[0].copy()
        island.translate(self.App.Vector(26, 0, 0))
        changed = self.Part.makeCompound([island] + solids[1:])
        a, _ = self.judges.planar_geometry(self.judges._shape_record(output.Shape, 1.5), 1e-4)
        b, _ = self.judges.planar_geometry(self.judges._shape_record(changed, 1.5), 1e-4)
        self.assertEqual(self.judges._topology(a), self.judges._topology(b))
        checks = self.checks(changed)
        self.assertEqual(checks['solid']['status'], 'PASS')
        self.assertEqual(checks['contour_to_output_iou']['status'], 'FAIL')
        self.assertFalse(checks['contour_to_output_iou']['evidence']['topology_matches'])
    def test_other_family_does_not_gain_compound_permission(self):
        _, output, _, _ = self.open_arm('bare')
        from tools import cad_verify_v4_judges as judges
        plan = dict(schema='cad-harness.plan.v4c', profile='c-s1', family='reference_fixture',
            references=[], engravings=[])
        card = dict(schema='cad-harness.judge-card.v4c', profile='c-s1', source='independent_dev',
            linear_tolerance_mm=1e-5, criteria=[dict(id='solid', metric='solid_valid')])
        result = judges.judge(plan, self.manifest, self.packet, output.Shape, card)
        self.assertEqual(result['status'], 'FAIL', result)


if __name__ == '__main__':
    unittest.main()
