"""Independent ordinary-native artifact controls; no generation/provider calls."""
import base64
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

if __package__:
    from . import cad_verify_v4_artifacts as artifacts, cad_verify_v4_ledger as ledger
else:
    import cad_verify_v4_artifacts as artifacts, cad_verify_v4_ledger as ledger

NATIVE = (os.environ.get('CAD_VERIFY_ARTIFACT_NATIVE')=='1' and sys.version_info[:3]==(3,11,14)
          and importlib.util.find_spec('FreeCAD') is not None)
REASON = 'set CAD_VERIFY_ARTIFACT_NATIVE=1 under pinned native FreeCAD Python'


def record(path):
    return dict(path=str(path),sha256=ledger.file_sha(path),bytes=path.stat().st_size)


class ArtifactIntake(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cad-neutral-intake-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.native,self.step = self.root/'plain.FCStd',self.root/'plain.step'
        self.step.write_bytes(b'ISO-10303-21; independent integrity fixture')
        self.archive('<Document/>')

    def archive(self,xml):
        with zipfile.ZipFile(self.native,'w') as z:
            z.writestr('Document.xml',xml)

    def bundle(self,extensions=None):
        path = self.root/'bundle.json'
        ledger.write_json(path,dict(schema='cad-harness.artifact-bundle.v4',profile='c-s1',
            evidence_mode='independent_dev',native=record(self.native),step=record(self.step),
            output_object=None,probes=[],extensions=extensions or []))
        return path

    def test_submitted_step_and_extension_mutations_rejected_before_native_open(self):
        path = self.bundle()
        self.step.write_bytes(b'changed STEP')
        with self.assertRaisesRegex(ValueError,'artifact_dependency_changed'):
            artifacts.load_bundle(path)
        extension = self.root/'independent_feature.py';extension.write_text('value=1\n',encoding='utf-8')
        path = self.root/'with-extension.json'
        value=ledger.read_json(self.root/'bundle.json')
        value['step']=record(self.step)
        value['extensions']=[dict(module='independent_feature',**record(extension))]
        ledger.write_json(path,value)
        extension.write_text('value=2\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'artifact_dependency_changed'):
            artifacts.load_bundle(path)

    def test_unregistered_serialized_python_and_external_document_rejected(self):
        token=base64.b64encode(json.dumps('independent:1').encode()).decode()
        self.archive('<Document><Property type="App::PropertyPythonObject"><Python value="'+token+
                     '" encoded="yes" module="unregistered_feature" class="Model"/></Property></Document>')
        with self.assertRaisesRegex(ValueError,'native_undeclared_python_dependency'):
            artifacts._guard_archive(self.native,{},set())
        self.archive('<Document><Property type="App::PropertyXLink"><XLink value="external"/></Property></Document>')
        with self.assertRaisesRegex(ValueError,'native_external_document_link'):
            artifacts._guard_archive(self.native,{},set())

    def test_archive_traversal_and_unbound_file_reads_rejected(self):
        with zipfile.ZipFile(self.native,'a') as z:
            z.writestr('../outside','not extracted')
        with self.assertRaisesRegex(ValueError,'native_archive_member_path'):
            artifacts._guard_archive(self.native,{},set())
        self.archive('<Document><Property type="App::PropertyFile"><File value="'+self.step.as_posix()+'"/></Property></Document>')
        with self.assertRaisesRegex(ValueError,'native_unbound_file_dependency'):
            artifacts._guard_archive(self.native,{},set())
        self.assertEqual(artifacts._guard_archive(self.native,{}, {self.step}),set())

    def test_prohibited_path_rejected_before_metadata_lookup(self):
        with patch.object(Path,'lstat',side_effect=AssertionError('must not look up private paths')):
            with self.assertRaises(ValueError):
                artifacts.load_bundle(self.root/'v4-holdout-private'/'not-opened.json')


@unittest.skipUnless(NATIVE,REASON)
class NativeArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        import Sketcher
        from tools import cad_verify_v4_inputs as inputs, cad_verify_v4_worker as worker
        if tuple(App.Version()[:3])!=('1','1','4'):
            raise RuntimeError('requires_pinned_FreeCAD')
        cls.App,cls.Part,cls.Sketcher,cls.inputs,cls.worker = App,Part,Sketcher,inputs,worker

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cad-neutral-native-')
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.close_all)
        self.root=Path(self.temp.name)
        source=self.root/'checker.step';self.Part.makeBox(1,1,1).exportStep(str(source))
        self.manifest=self.root/'inputs.json'
        ledger.write_json(self.manifest,dict(schema='cad-harness.inputs.v4c',profile='c-s1',
            evidence_mode='independent_dev',assets={'checker':dict(kind='step',role='checker',**dict(record(source),path=source.name))}))
        recipe=dict(schema='cad-harness.step-recipe.v4c',profile='c-s1',source_axes=['X','Y','Z'],
                    source_units='mm',signature_precision_mm=1e-6)
        packet=self.inputs.inspect_step(self.manifest,'checker',recipe,self.root/'facts.json')
        self.prepared=self.root/'prepared.json';ledger.write_json(self.prepared,packet)

    def close_all(self):
        for name in list(self.App.listDocuments()):self.App.closeDocument(name)

    def document(self,circle=False,metadata=False,auxiliary=False,status_token=False):
        doc=self.App.newDocument('IndependentOrdinary')
        body=doc.addObject('PartDesign::Body','UnrelatedBodyName')
        if auxiliary:
            static=body.newObject('PartDesign::Feature','StaticSnapshot')
            static.Shape=self.Part.makeBox(12,8,3);body.Tip=static
            note=doc.addObject('Part::Feature','EmptyAuxiliary')
            note.addProperty('App::PropertyString','Note','Notes');note.Note='memo'
            doc.recompute()
            return doc,body,note
        sketch=body.newObject('Sketcher::SketchObject','UnrelatedSketchName')
        if circle:
            sketch.addGeometry(self.Part.Circle(self.App.Vector(),self.App.Vector(0,0,1),2),False)
            sketch.addConstraint(self.Sketcher.Constraint('Radius',0,2))
        else:
            points=[(0,0),(12,0),(12,8),(0,8)]
            for a,b in zip(points,points[1:]+points[:1]):
                sketch.addGeometry(self.Part.LineSegment(self.App.Vector(*a,0),self.App.Vector(*b,0)),False)
        pad=body.newObject('PartDesign::Pad','UnrelatedPadName');pad.Profile=sketch;pad.Length=3
        if metadata:
            pad.addProperty('App::PropertyFloat','Memo','Notes');pad.Memo=1
        if status_token:
            pad.addProperty('App::PropertyString','BuildStatus','Independent');pad.BuildStatus='finished'
        body.Tip=pad;doc.recompute()
        return doc,body,pad

    def execute(self,*,circle=False,metadata=False,wrong_step=False,auxiliary=False,status_token=False):
        doc,body,pad=self.document(circle,metadata,auxiliary,status_token)
        pad_name = pad.Name
        native,step=self.root/'piece.FCStd',self.root/'piece.step'
        doc.saveAs(str(native))
        if wrong_step:self.Part.makeBox(12,8,2).exportStep(str(step))
        else:body.Shape.exportStep(str(step))
        self.App.closeDocument(doc.Name)
        bounds=[-2,2,-2,2,0,3] if circle else [0,12,0,8,0,3]
        volume=12*math.pi if circle else 288
        card=dict(schema='cad-harness.judge-card.v4c',profile='c-s1',source='independent_dev',linear_tolerance_mm=1e-5,
            criteria=[dict(id='solid',metric='solid_valid'),dict(id='bounds',metric='bounds',expected_mm=bounds),
                      dict(id='volume',metric='volume',expected_mm3=volume,tolerance_mm3=.001),
                      dict(id='native',metric='native_roundtrip',maximum_bounds_difference_mm=1e-5,
                           maximum_volume_difference_mm3=.001,require_editable=True)])
        card_path=self.root/'card.json';ledger.write_json(card_path,card)
        context_path=self.root/'context.json'
        ledger.write_json(context_path,dict(schema='cad-harness.artifact-context.v4',profile='c-s1',family='C1',
            manifest_sha256=ledger.file_sha(self.manifest),prepared_sha256=ledger.file_sha(self.prepared),
            card_sha256=ledger.file_sha(card_path),reference=None,contour=None,engravings=[]))
        if circle:probes=[dict(kind='sketch_constraint',object='UnrelatedSketchName',constraint=0,delta=.01)]
        elif auxiliary:probes=[dict(kind='text',object=pad_name,property='Note',suffix='.')]
        elif metadata:probes=[dict(kind='scalar',object=pad_name,property='Memo',delta=.1)]
        else:probes=[]
        bundle_path=self.root/'artifacts.json'
        ledger.write_json(bundle_path,dict(schema='cad-harness.artifact-bundle.v4',profile='c-s1',evidence_mode='independent_dev',
            native=record(native),step=record(step),output_object=None,probes=probes,extensions=[]))
        from tools import cad_verify_v4_runtime
        runtime_path=self.root/'runtime.json'
        ledger.write_json(runtime_path,cad_verify_v4_runtime.capture(artifacts.ROOT))
        before={str(path):ledger.file_sha(path) for path in (native,step)}
        out=self.root/'check';out.mkdir()
        result=self.worker.execute(dict(operation='artifact-verify',profile='c-s1',manifest=str(self.manifest),
            prepared=str(self.prepared),card=str(card_path),context=str(context_path),bundle=str(bundle_path),
            runtime_binding=str(runtime_path),out=str(out)))
        self.assertTrue(result['document_closed'],result)
        self.assertEqual(before,{path:ledger.file_sha(path) for path in before})
        return result

    def contour_document(self):
        from PIL import Image
        from tools import cad_verify_v4_compile as compiler
        image, source = self.root / 'mask.png', self.root / 'outline.json'
        Image.new('RGBA', (12, 8), (0, 0, 0, 255)).save(image)
        points = [[0, 0], [12, 0], [12, 8], [0, 8]]
        loops = [dict(role='outer', segments=[dict(kind='line', p0=a, p1=b)
                 for a, b in zip(points, points[1:] + points[:1])])]
        original = dict(schema='cad-harness.contour-source.v4c', profile='c-s1', units='mm',
                        bounds_mm=[0, 12, 0, 8], nominal_width_mm=12., loops=loops,
                        source_image_asset_id='mask')
        ledger.write_json(source, original)
        contour = dict(original, schema='cad-harness.contour.v4c', asset_id='outline',
                       source_sha256=ledger.file_sha(source), source_image_sha256=ledger.file_sha(image),
                       topology=dict(components=1, holes=0),
                       pixel_to_mm=dict(scale_mm_per_pixel=1., origin_mm=[0, 0], image_height_pixels=8,
                           y_axis='up', pixel_convention='closed unit cells; centers at (col+0.5,row+0.5)'),
                       provenance=dict(kind='independent_analytic_source'))
        doc = self.App.newDocument('IndependentContour')
        body = doc.addObject('PartDesign::Body', 'ContourBody')
        feature = body.newObject('PartDesign::FeaturePython', 'SourceExtrusion')
        for kind, name, value in (
                ('App::PropertyString', 'ContourData', json.dumps(contour, allow_nan=False)),
                ('App::PropertyLength', 'Width', 12.), ('App::PropertyLength', 'Thickness', 3.),
                ('App::PropertyVector', 'Origin', self.App.Vector()),
                ('App::PropertyString', 'BuildStatus', 'new')):
            feature.addProperty(kind, name, 'Independent')
            setattr(feature, name, value)
        feature.Proxy = compiler.ContourProxy()
        body.Tip = feature
        doc.recompute()
        self.assertAlmostEqual(body.Shape.Volume, 288., places=6)
        return doc, body, feature

    def test_scoped_contour_source_edits_cannot_reuse_original_admission(self):
        from tools import cad_verify_v4_compile as compiler
        doc, body, feature = self.contour_document()
        original = feature.ContourData
        changed = json.loads(original)
        changed['nominal_width_mm'] = 13.
        invalid = json.dumps(changed, allow_nan=False)
        with self.assertRaises(RuntimeError):
            with compiler.validated_contour_sources(doc):
                feature.ContourData = invalid
                with self.assertRaises(ValueError):
                    feature.Proxy.execute(feature)
                self.assertTrue(feature.Shape.isNull())
                feature.ContourData = original
                feature.Proxy.execute(feature)
                self.assertAlmostEqual(feature.Shape.Volume, 288., places=6)
                raise RuntimeError('scope_interrupted')
        feature.ContourData = invalid
        with self.assertRaises(ValueError):
            feature.Proxy.execute(feature)
        self.assertTrue(feature.Shape.isNull())

    def test_scoped_contour_edits_restore_and_saved_document_remains_editable(self):
        from tools import cad_verify_v4_compile as compiler
        doc, body, feature = self.contour_document()
        probes = [dict(kind='scalar', object=feature.Name, property=name, delta=delta)
                  for name, delta in (('Width', .5), ('Thickness', .01))]
        native = self.root / 'scoped-contour.FCStd'
        with compiler.validated_contour_sources(doc):
            evidence, editable = artifacts.operative(self.App, doc, body, probes)
            self.assertTrue(editable, evidence)
            self.assertTrue(all(row['changed_solid_indices'] == [0] for row in evidence['probes']))
            self.assertAlmostEqual(body.Shape.Volume, 288., places=6)
            doc.saveAs(str(native))
        self.App.closeDocument(doc.Name)
        reopened = self.App.openDocument(str(native))
        for obj in reopened.Objects:
            obj.touch()
        reopened.recompute()
        restored = reopened.getObject('ContourBody')
        evidence, editable = artifacts.operative(self.App, reopened, restored, probes)
        self.assertTrue(editable, evidence)
        self.assertAlmostEqual(restored.Shape.Volume, 288., places=6)

    def test_shape_difference_rejects_equal_volume_equal_bounds_different_geometry(self):
        stock = self.Part.makeBox(10, 10, 3)
        left_hole = self.Part.makeCylinder(1, 3, self.App.Vector(3, 5, 0))
        right_hole = self.Part.makeCylinder(1, 3, self.App.Vector(7, 5, 0))
        left, right = stock.cut(left_hole), stock.cut(right_hole)
        self.assertAlmostEqual(left.Volume, right.Volume, places=9)
        for name in ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'):
            self.assertEqual(getattr(left.BoundBox, name), getattr(right.BoundBox, name))
        difference = artifacts._shape_difference(left, right)
        self.assertAlmostEqual(difference, 6 * math.pi, places=6)
        self.assertGreater(difference, max(1e-10, left.Volume * 1e-12))

    def test_shape_difference_preserves_restored_and_translated_geometry_measurements(self):
        original = self.Part.makeBox(12, 8, 3)
        self.assertEqual(artifacts._shape_difference(original, original), 0.)
        restored = self.Part.Shape()
        restored.importBrepFromString(original.exportBrepToString(), False)
        self.assertEqual(artifacts._shape_difference(original, restored), 0.)
        shifted = original.copy()
        shifted.translate(self.App.Vector(1, 0, 0))
        self.assertAlmostEqual(artifacts._shape_difference(original, shifted), 48., places=6)
        separated = original.copy()
        separated.translate(self.App.Vector(20, 0, 0))
        self.assertAlmostEqual(artifacts._shape_difference(original, separated), 576., places=6)

    def test_shape_difference_keeps_common_material_as_opposing_operand(self):
        common = self.Part.makeBox(10, 10, 3)
        contained = self.Part.makeBox(2, 2, 1, self.App.Vector(1, 1, 1))
        overlapping = self.Part.makeCompound([common, contained])
        # Cancelling common from BOTH operands would falsely report the volume
        # of contained. The complete opposing common solid covers it entirely.
        self.assertEqual(artifacts._shape_difference(overlapping, common), 0.)
        self.assertEqual(artifacts._shape_difference(common, overlapping), 0.)

    def test_shape_difference_measures_changed_compound_with_copied_common_solid(self):
        common = self.Part.makeBox(4, 4, 3)
        original_piece = self.Part.makeBox(2, 2, 3, self.App.Vector(10, 0, 0))
        edited_piece = self.Part.makeBox(2, 2, 4, self.App.Vector(10, 0, 0))
        before = self.Part.makeCompound([common, original_piece])
        after = self.Part.makeCompound([edited_piece, common.copy()])
        self.assertAlmostEqual(artifacts._shape_difference(before, after), 4., places=6)
        self.assertAlmostEqual(artifacts._shape_difference(after, before), 4., places=6)
        restored = self.Part.makeCompound([original_piece.copy(), common.copy()])
        self.assertEqual(artifacts._shape_difference(before, restored), 0.)

    def test_ordinary_native_pad_is_operative_and_restored_without_harness_plan(self):
        result=self.execute()
        self.assertEqual(result['status'],'PASS',result)
        probe=result['editability']['probes'][0]
        self.assertGreater(probe['symmetric_difference_mm3'],0)
        self.assertTrue(probe['restored'])
        self.assertAlmostEqual(result['measurements']['fcstd']['volume_mm3'],288,places=6)

    def test_metadata_only_edit_does_not_prove_native_editability(self):
        result=self.execute(metadata=True)
        self.assertEqual(result['status'],'FAIL',result)
        self.assertFalse(result['native_evidence']['editable'])
        self.assertEqual(next(row for row in result['judges']['fcstd']['checks'] if row['id']=='native')['status'],'FAIL')

    def test_independent_step_mismatch_fails_common_native_and_geometry_gates(self):
        result=self.execute(wrong_step=True)
        self.assertEqual(result['status'],'FAIL',result)
        self.assertGreater(result['native_evidence']['bounds_difference_mm'],.9)
        self.assertEqual(next(row for row in result['judges']['step']['checks'] if row['id']=='volume')['status'],'FAIL')

    def test_native_sketch_dimension_drives_actual_geometry_and_restores(self):
        result=self.execute(circle=True)
        self.assertEqual(result['status'],'PASS',result)
        self.assertGreater(result['editability']['probes'][0]['symmetric_difference_mm3'],0)
        self.assertAlmostEqual(result['measurements']['fcstd']['volume_mm3'],12*math.pi,places=5)

    def test_empty_auxiliary_shape_cannot_certify_a_static_output_editable(self):
        result=self.execute(auxiliary=True)
        self.assertEqual(result['status'],'FAIL',result)
        self.assertFalse(result['native_evidence']['editable'])
        self.assertFalse(result['editability']['probes'][0]['operative'])

    def test_independent_build_status_word_is_not_a_harness_token_requirement(self):
        result=self.execute(status_token=True)
        self.assertEqual(result['status'],'PASS',result)
        self.assertTrue(result['native_evidence']['editable'])


if __name__=='__main__':
    unittest.main()
