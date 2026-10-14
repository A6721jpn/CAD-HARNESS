"""Independent C5 native behaviors; no process/CAD work at test discovery.

Opt in with CAD_VERIFY_S3_NATIVE=1 under the pinned FreeCAD Python. All source
geometry/cards are authored independently in dev-c-s3, never from a pilot.
"""
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE = (os.environ.get('CAD_VERIFY_S3_NATIVE') == '1' and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
REASON = 'native S3 not exercised: set CAD_VERIFY_S3_NATIVE=1 under pinned FreeCAD Python'


def _module(name):
    return importlib.import_module(('tools.' if __package__ else '') + name)


@unittest.skipUnless(NATIVE, REASON)
class S3NativeSurfaceRebuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App, cls.Part = App, Part
        cls.rebuild = _module('cad_verify_v4_s3_rebuild')
        cls.inputs = _module('cad_verify_v4_inputs')
        cls.ledger = _module('cad_verify_v4_ledger')
        value = os.environ.get('CAD_VERIFY_S3_FIXTURES')
        if value:
            cls.root = cls.inputs.guarded_path(value, regular=False)
        else:
            source = Path(__file__).resolve().parents[1] / 'design/cad-harness-verify-v4/dev-c-s3/generate.py'
            spec = importlib.util.spec_from_file_location('s3_independent_source', source)
            generator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generator)
            temporary = tempfile.TemporaryDirectory(prefix='cad-s3-independent-source-')
            cls.addClassCleanup(temporary.cleanup)
            cls.root = generator.generate(Path(temporary.name) / 'assets')
        cls.manifest = cls.root / 'manifest.json'
        cls.prepared = cls.ledger.read_json(cls.root / 'prepared.json')

    def setUp(self):
        self.doc = self.App.newDocument('S3Native')
        self.addCleanup(self.close, self.doc.Name)

    def close(self, name):
        if name in self.App.listDocuments():
            self.App.closeDocument(name)

    def plan(self, name='g1_pair'):
        return self.ledger.read_json(self.root / (name + '-plan.json'))

    def source(self, name='g1_pair'):
        result = self.Part.Shape()
        result.read(str(self.root / (name + '.step')))
        return result

    def build(self, name='g1_pair', doc=None):
        return self.rebuild.build_plan(doc or self.doc, self.plan(name), self.manifest, self.prepared)

    @staticmethod
    def difference(a, b):
        return a.cut(b).Volume + b.cut(a).Volume

    def test_non_g2_freeform_region_is_reconstructed_and_other_material_unchanged(self):
        source = self.source()
        digest = self.ledger.file_sha(self.root / 'g1_pair.step')
        body = self.build()
        self.assertTrue(body.Shape.isValid())
        self.assertEqual(len(body.Shape.Solids), 1)
        self.assertEqual(len(body.Shape.Faces), len(source.Faces) - 1)
        # A copied G1 reference or only a renamed cached Shape cannot pass.
        self.assertGreater(self.difference(source, body.Shape), 1e-4)
        # This ROI contains the curved bottom and lower wall material, but no
        # fitted top. Its independent datum is fixed before reconstruction.
        roi = self.Part.makeBox(28., 18., 9., self.App.Vector(0, 0, -6))
        self.assertLess(self.difference(source.common(roi), body.Shape.common(roi)), 1e-7)
        self.assertEqual(self.ledger.file_sha(self.root / 'g1_pair.step'), digest)

    def test_geometrically_equivalent_swapped_reversed_input_has_same_result(self):
        first = self.build()
        other_doc = self.App.newDocument('S3Reparameterized')
        self.addCleanup(self.close, other_doc.Name)
        other = self.build('reparameterized_pair', other_doc)
        self.assertTrue(other.Shape.isValid())
        self.assertEqual(len(other.Shape.Solids), 1)
        self.assertLess(self.difference(first.Shape, other.Shape), 1e-7)
        self.assertLess(self.difference(self.source(), self.source('reparameterized_pair')), 1e-7)

    def test_oblique_translated_source_preserves_its_original_world_frame(self):
        base = self.build()
        temporary = tempfile.TemporaryDirectory(prefix='cad-s3-oblique-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        pose = self.App.Placement(self.App.Vector(-11,6,13),self.App.Rotation(self.App.Vector(2,-1,3),23))
        source = self.source()
        source.transformShape(pose.toMatrix())
        asset = root/'oblique.step'
        source.exportStep(str(asset))
        manifest = root/'manifest.json'
        self.ledger.write_json(manifest,dict(schema='cad-harness.inputs.v4c',profile='c-s3',
            evidence_mode='independent_dev',assets=dict(reference=dict(kind='step',role='reference',
                path=asset.name,sha256=self.ledger.file_sha(asset),bytes=asset.stat().st_size))))
        recipe = self.ledger.read_json(self.root/'step-recipe.json')
        prepared = self.inputs.inspect_step(manifest,'reference',recipe,root/'facts.json')
        tops = [f for f in prepared['assets']['reference']['faces'] if f['normal'] is not None and
                pose.Rotation.inverted().multVec(self.App.Vector(*f['normal'])).z > .8]
        plan = self.plan()
        plan['asset_id'] = 'reference'
        plan['source_sha256'] = self.ledger.file_sha(asset)
        plan['grid'] = []
        for i in range(2):
            face = next(f for f in tops if abs(pose.inverse().multVec(self.App.Vector(*f['center_mm'])).x-14*(i+.5))<1.)
            plan['grid'].append([dict(face_id=face['id'],signature=face['signature'],
                adjacent_face_ids=face['adjacent_face_ids'],swap_uv=False,reverse_u=False,reverse_v=False)])
        doc = self.App.newDocument('S3Oblique')
        self.addCleanup(self.close,doc.Name)
        body = self.rebuild.build_plan(doc,plan,manifest,prepared)
        self.assertTrue(body.Shape.isValid())
        restored_frame = body.Shape.copy()
        restored_frame.transformShape(pose.inverse().toMatrix())
        self.assertLess(self.difference(base.Shape,restored_frame),1e-7)

    def test_both_tensor_directions_merge_without_removing_unselected_faces(self):
        source = self.source('four_patch')
        self.assertAlmostEqual(source.Volume, 2 * 14. * 2 * 18. * 9., places=6)
        body = self.build('four_patch')
        self.assertEqual(len(body.Shape.Faces), len(source.Faces) - 3)
        self.assertEqual(len(body.Shape.Solids), 1)
        self.assertTrue(body.Shape.isValid())
        roi = self.Part.makeBox(28., 36., 9., self.App.Vector(0, 0, -6))
        self.assertLess(self.difference(source.common(roi), body.Shape.common(roi)), 1e-7)

    def test_already_g2_geometry_is_merged_without_inventing_a_new_shape(self):
        source = self.source('g2_pair')
        body = self.build('g2_pair')
        self.assertEqual(len(body.Shape.Faces), len(source.Faces) - 1)
        self.assertTrue(body.Shape.isValid())
        self.assertLess(self.difference(source, body.Shape), 1e-7)

    def test_interior_pole_edit_changes_actual_solid_and_restores(self):
        body = self.build()
        feature = body.Tip
        original = body.Shape.copy()
        offsets = [self.App.Vector(value) for value in feature.PoleOffsets]
        changed = [self.App.Vector(value) for value in offsets]
        definition = json.loads(feature.SurfaceData)
        nu, nv = len(definition['poles']), len(definition['poles'][0])
        index = (nu // 2) * nv + nv // 2
        changed[index] = self.App.Vector(0, 0, .04)
        try:
            feature.PoleOffsets = changed
            self.doc.recompute()
            self.assertEqual(feature.BuildStatus, 'ok')
            self.assertTrue(body.Shape.isValid())
            self.assertGreater(self.difference(original, body.Shape), 1e-4)
        finally:
            feature.PoleOffsets = offsets
            feature.touch()
            self.doc.recompute()
        self.assertLess(self.difference(original, body.Shape), 1e-7)

    def test_rejected_boundary_edit_clears_cached_shape_and_recovers(self):
        body = self.build()
        feature = body.Tip
        original = body.Shape.copy()
        offsets = [self.App.Vector(value) for value in feature.PoleOffsets]
        changed = [self.App.Vector(value) for value in offsets]
        changed[0] = self.App.Vector(.02, 0, 0)
        try:
            feature.PoleOffsets = changed
            self.doc.recompute()
            self.assertTrue(feature.Shape.isNull())
            self.assertNotEqual(feature.BuildStatus, 'ok')
        finally:
            feature.PoleOffsets = offsets
            feature.touch()
            self.doc.recompute()
        self.assertTrue(body.Shape.isValid())
        self.assertLess(self.difference(original, body.Shape), 1e-7)

    def test_incompatible_fit_tolerance_cannot_leave_partial_native_model(self):
        plan = self.plan()
        plan['fit_tolerance_mm'] = 1e-9
        digest = self.ledger.file_sha(self.root / 'g1_pair.step')
        with self.assertRaises(ValueError):
            self.rebuild.build_plan(self.doc, plan, self.manifest, self.prepared)
        self.assertEqual(len(self.doc.Objects), 0)
        self.assertEqual(self.ledger.file_sha(self.root / 'g1_pair.step'), digest)

    def test_forged_matching_atlas_and_plan_do_not_override_actual_geometry(self):
        plan, prepared = self.plan(), copy.deepcopy(self.prepared)
        selection = plan['grid'][0][0]
        selection['signature'] = '0' * 64
        selected = next(f for f in prepared['assets'][plan['asset_id']]['faces'] if f['id'] == selection['face_id'])
        selected['signature'] = selection['signature']
        with self.assertRaises(ValueError):
            self.rebuild.build_plan(self.doc, plan, self.manifest, prepared)
        self.assertEqual(len(self.doc.Objects), 0)

    def test_tiny_notch_cannot_be_filled_under_an_area_error_allowance(self):
        points = [(0, 0), (14, 0), (14, 18), (8.0002, 18),
                  (8.0002, 17.9998), (8, 17.9998), (8, 18), (0, 18), (0, 0)]
        face = self.Part.Face(self.Part.makePolygon([self.App.Vector(x, y, 0) for x, y in points]))
        self.assertTrue(face.isValid())
        self.assertEqual(len(face.Wires), 1)
        self.assertGreater(14 * 18 - face.Area, 0)
        self.assertLess(14 * 18 - face.Area, 1e-6 * face.Length)
        with self.assertRaises(self.rebuild.UnsupportedDomain):
            self.rebuild._rectangular_trim(face)


if __name__ == '__main__':
    unittest.main()
