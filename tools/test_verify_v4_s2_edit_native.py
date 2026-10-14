"""Independent S2 behavioral tests; no native process at discovery.

Explicit CAD_VERIFY_S2_NATIVE=1 and pinned FreeCAD Python are required. Suites
are run by the integration owner, never during parallel implementation.
"""
import copy
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE = os.environ.get('CAD_VERIFY_S2_NATIVE')=='1' and sys.version_info[:3]==(3,11,14) and importlib.util.find_spec('FreeCAD') is not None
REASON = 'native S2 not exercised: set CAD_VERIFY_S2_NATIVE=1 under pinned FreeCAD Python'


def _module(name):
    return importlib.import_module(('tools.' if __package__ else '')+name)


@unittest.skipUnless(NATIVE,REASON)
class S2NativeDirectEdit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3])!=('1','1','4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App,cls.Part = App,Part
        cls.editor = _module('cad_verify_v4_s2_edit')
        cls.inputs = _module('cad_verify_v4_inputs')
        cls.ledger = _module('cad_verify_v4_ledger')
        source = Path(__file__).resolve().parents[1]/'design/cad-harness-verify-v4/dev-c-s2/generate.py'
        spec = importlib.util.spec_from_file_location('s2_independent_source',source)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        value = os.environ.get('CAD_VERIFY_S2_FIXTURES')
        if value:
            cls.root = cls.inputs.guarded_path(value,regular=False)
        else:
            temp = tempfile.TemporaryDirectory(prefix='cad-s2-independent-source-')
            cls.addClassCleanup(temp.cleanup)
            cls.root = generator.generate(Path(temp.name)/'assets')
        cls.manifest = cls.root/'manifest.json'
        cls.prepared = cls.ledger.read_json(cls.root/'prepared.json')
        cls.expected = cls.ledger.read_json(cls.root/'expected.json')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cad-s2-native-test-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.doc = self.App.newDocument('S2Native')
        self.addCleanup(self.close,self.doc.Name)

    def close(self,name):
        if name in self.App.listDocuments():
            self.App.closeDocument(name)

    def plan(self,name='featured_plate_out'):
        return self.ledger.read_json(self.root/(name+'-plan.json'))

    def build(self,plan=None):
        return self.editor.build_plan(self.doc,plan or self.plan(),self.manifest,self.prepared)

    def source(self,asset_id):
        shape = self.Part.Shape()
        shape.read(str(self.root/(asset_id+'.step')))
        return shape

    def test_signed_selected_face_offsets_original_immutable_and_preserved_local_cavity(self):
        originals = {p:self.ledger.file_sha(p) for p in self.root.glob('*.step')}
        for suffix,z in [('out',8.),('in',6.)]:
            doc = self.App.newDocument('Signed'+suffix)
            self.addCleanup(self.close,doc.Name)
            plan = self.plan('featured_plate_'+suffix)
            body = self.editor.build_plan(doc,plan,self.manifest,self.prepared)
            self.assertEqual(len(body.Shape.Solids),1)
            self.assertTrue(body.Shape.isValid())
            self.assertEqual(len(body.Shape.Faces),8)
            self.assertAlmostEqual(body.Shape.BoundBox.ZMax,z,places=6)
            self.assertAlmostEqual(body.Shape.Volume,self.expected['featured_plate'][suffix+'_volume_mm3'],places=5)
            roi = self.Part.makeBox(4,4,2.5,self.App.Vector(2,2,0))
            source = self.source('featured_plate')
            self.assertLess(source.common(roi).cut(body.Shape.common(roi)).Volume+body.Shape.common(roi).cut(source.common(roi)).Volume,1e-8)
            self.assertIs(body.Tip.Proxy.__class__,self.editor.DirectEditProxy)
            self.assertEqual(len(body.Group),1)
        self.assertEqual(originals,{p:self.ledger.file_sha(p) for p in originals})

    def test_curved_cylindrical_per_face_offset_reconnects_original_caps(self):
        for suffix,radius in [('out',6.),('in',4.)]:
            doc = self.App.newDocument('Cylinder'+suffix)
            self.addCleanup(self.close,doc.Name)
            body = self.editor.build_plan(doc,self.plan('cylinder_'+suffix),self.manifest,self.prepared)
            self.assertAlmostEqual(body.Shape.Volume,math.pi*radius*radius*9,places=5)
            self.assertEqual(len(body.Shape.Faces),3)
            self.assertAlmostEqual(body.Shape.BoundBox.ZMin,0.,places=6)
            self.assertAlmostEqual(body.Shape.BoundBox.ZMax,9.,places=6)
            cylindrical = [f for f in body.Shape.Faces if isinstance(f.Surface,self.Part.Cylinder)]
            self.assertEqual(len(cylindrical),1)
            self.assertAlmostEqual(cylindrical[0].Surface.Radius,radius,places=6)

    def test_smooth_bspline_swept_face_signed_local_offsets_and_reconnection(self):
        source = self.source('smooth_roof')
        self.assertAlmostEqual(source.Volume,1674.,places=5)
        for suffix,distance in [('out',.5),('in',-.5)]:
            doc = self.App.newDocument('Smooth'+suffix)
            self.addCleanup(self.close,doc.Name)
            plan = self.plan('smooth_roof_'+suffix)
            body = self.editor.build_plan(doc,plan,self.manifest,self.prepared)
            self.assertTrue(body.Shape.isValid())
            self.assertEqual(len(body.Shape.Solids),1)
            self.assertEqual(len(body.Shape.Faces),6)
            self.assertGreater((body.Shape.Volume-source.Volume)*distance,0.)
            face = source.Faces[int(plan['selection']['face_id'][4:])-1]
            self.assertNotIsInstance(face.Surface,self.Part.Plane)
            self.assertNotIsInstance(face.Surface,self.Part.Cylinder)
            u0,u1,v0,v1 = face.ParameterRange
            skin = self.Part.makeCompound(body.Shape.Faces)
            for fraction in (.2,.4,.6,.8):
                u,v = u0+fraction*(u1-u0),(v0+v1)/2
                expected = face.valueAt(u,v)+face.normalAt(u,v)*distance
                self.assertLess(self.Part.Vertex(expected).distToShape(skin)[0],1e-5)
            history = self.editor.operation_report(body)['kernel_history']
            selected = next(row for row in history['faces'] if row['source_id']==plan['selection']['face_id'])
            self.assertTrue(selected['outputs'])
            self.assertTrue(any('Offset.Generated' in link['history_paths'] for link in selected['outputs']))
            self.assertTrue(all(e['operative'] and e['restored'] for e in self.editor.operative_evidence(doc,body)))

    def test_oblique_source_is_not_axis_aligned_box_reconstruction(self):
        body = self.build(self.plan('rotated_plate_out'))
        self.assertAlmostEqual(body.Shape.Volume,self.expected['featured_plate']['out_volume_mm3'],places=5)
        self.assertEqual(len(body.Shape.Faces),8)
        normals = [f.normalAt(sum(f.ParameterRange[:2])/2,sum(f.ParameterRange[2:])/2) for f in body.Shape.Faces if isinstance(f.Surface,self.Part.Plane)]
        self.assertTrue(any(all(abs(v)>1e-3 for v in n) for n in normals))

    def test_distinct_tilted_replacement_support_and_reconnected_neighbors(self):
        plan = self.plan('featured_plate_replace')
        body = self.build(plan)
        self.assertAlmostEqual(body.Shape.Volume,self.expected['featured_plate']['replace_volume_mm3'],places=5)
        self.assertAlmostEqual(body.Shape.BoundBox.ZMax,9.8,places=6)
        self.assertEqual(len(body.Shape.Faces),8)
        report = self.editor.operation_report(body)
        self.assertEqual(report['operation']['kind'],'replace')
        self.assertTrue(report['replacement_output_face_ids'])
        replacement_links = report['kernel_history']['replacement_operand_faces']
        self.assertTrue(replacement_links)
        self.assertTrue(any('Common.Modified' in method for row in replacement_links for link in row['outputs'] for method in link['history_paths']))
        self.assertTrue(any(row['outputs'] for row in report['kernel_history']['edges']))
        for face_id in report['replacement_output_face_ids']:
            face = body.Shape.Faces[int(face_id[4:])-1]
            for vertex in face.Vertexes:
                p = vertex.Point
                self.assertAlmostEqual(p.z,8+.1*p.x,places=5)
            self.assertAlmostEqual(abs(face.normalAt(0,0).x),.1/math.sqrt(1.01),places=6)
        self.assertTrue(self.editor.check_model_inputs(body,plan,self.prepared,self.manifest))
        self.assertTrue(all(e['operative'] and e['restored'] for e in self.editor.operative_evidence(self.doc,body)))

    def test_real_native_save_reopen_and_parameter_changes(self):
        for name in ('featured_plate_out','featured_plate_replace'):
            doc = self.App.newDocument('Save'+name)
            self.addCleanup(self.close,doc.Name)
            plan = self.plan(name)
            body = self.editor.build_plan(doc,plan,self.manifest,self.prepared)
            expected = body.Shape.Volume
            path = self.work/(name+'.FCStd')
            doc.saveAs(str(path))
            self.close(doc.Name)
            restored = self.App.openDocument(str(path))
            self.addCleanup(self.close,restored.Name)
            restored.recompute()
            reopened = restored.getObject('Model')
            self.assertTrue(self.editor.check_model_inputs(reopened,plan,self.prepared,self.manifest))
            evidence = self.editor.operative_evidence(restored,reopened)
            self.assertGreater(evidence[0]['symmetric_difference_mm3'],0)
            self.assertTrue(evidence[0]['restored'])
            self.assertAlmostEqual(reopened.Shape.Volume,expected,places=5)
            exported = self.work/(name+'.step')
            reopened.Shape.exportStep(str(exported))
            shape = self.Part.Shape();shape.read(str(exported))
            self.assertTrue(shape.isValid())
            self.assertEqual(len(shape.Solids),1)
            self.assertAlmostEqual(shape.Volume,expected,places=5)

    def test_face_id_alone_stale_adjacency_reordered_and_ambiguous_rejected(self):
        for mutate in (
            lambda p:p['selection'].__setitem__('signature','0'*64),
            lambda p:p['selection'].__setitem__('face_id','Face1'),
            lambda p:p['selection'].__setitem__('adjacent_face_ids',list(reversed(p['selection']['adjacent_face_ids']))),
            lambda p:p['selection'].__setitem__('adjacent_face_ids',[])):
            plan = self.plan();mutate(plan)
            with self.assertRaises(ValueError):self.build(plan)
        packet = copy.deepcopy(self.prepared)
        faces = packet['assets']['featured_plate']['faces']
        faces[0],faces[-1] = faces[-1],faces[0]
        with self.assertRaises(ValueError):
            self.editor.build_plan(self.doc,self.plan(),self.manifest,packet)
        plan = self.plan('box_out')
        record = self.prepared['assets']['ambiguous']
        face = record['faces'][0]
        plan.update(asset_id='ambiguous',source_sha256=record['source_sha256'],selection={'face_id':face['id'],'signature':face['signature'],'adjacent_face_ids':face['adjacent_face_ids']})
        with self.assertRaises(ValueError):self.build(plan)

    def test_failed_recompute_clears_shape_and_recovery_rebuilds_from_original(self):
        body = self.build()
        feature = body.Tip
        feature.OffsetDistance = -100.
        self.doc.recompute()
        self.assertTrue(feature.Shape.isNull())
        self.assertTrue(feature.BuildStatus.startswith('failed:'))
        self.assertEqual(feature.OperationReport,'')
        feature.OffsetDistance = 1.
        self.doc.recompute()
        self.assertEqual(feature.BuildStatus,'ok')
        self.assertAlmostEqual(feature.Shape.Volume,self.expected['featured_plate']['out_volume_mm3'],places=5)
        feature.OriginalBrep = feature.OriginalBrep+'tamper'
        feature.touch();self.doc.recompute()
        self.assertTrue(feature.Shape.isNull())
        self.assertTrue(feature.BuildStatus.startswith('failed:'))

    def test_replacement_extension_boundary_and_dependency_bindings(self):
        plan = self.plan('featured_plate_replace')
        plan['operation']['extension_limit_mm'] = .2
        with self.assertRaises(ValueError):self.build(plan)
        self.assertFalse(self.doc.Objects)
        plan = self.plan('featured_plate_replace')
        plan['operation']['replacement_source_sha256'] = '0'*64
        with self.assertRaises(ValueError):self.build(plan)
        plan = self.plan('featured_plate_replace')
        curved = self.prepared['assets']['cylinder']
        face = next(f for f in curved['faces'] if f['surface_type']=='Cylinder')
        plan['operation'].update(replacement_asset_id='cylinder',replacement_source_sha256=curved['source_sha256'],replacement_selection={'face_id':face['id'],'signature':face['signature'],'adjacent_face_ids':face['adjacent_face_ids']})
        with self.assertRaises(ValueError):self.build(plan)
        plan = self.plan('featured_plate_replace')
        patch = self.prepared['assets']['undersized_plane']
        face = patch['faces'][0]
        plan['operation'].update(replacement_asset_id='undersized_plane',replacement_source_sha256=patch['source_sha256'],
            replacement_selection={'face_id':face['id'],'signature':face['signature'],'adjacent_face_ids':face['adjacent_face_ids']})
        with self.assertRaises(ValueError):self.build(plan)

    def test_provenance_does_not_fabricate_displaced_face_identity(self):
        body = self.build()
        report = self.editor.operation_report(body)
        selected = next(row for row in report['correspondence']['faces'] if row['source_id']==self.plan()['selection']['face_id'])
        self.assertEqual(selected['relation'],'unmapped')
        self.assertEqual(selected['outputs'],[])
        self.assertTrue(report['correspondence']['unmapped_output_faces'])
        self.assertEqual(len(report['correspondence']['faces']),8)
        self.assertTrue(report['valid'])
        kernel_selected = next(row for row in report['kernel_history']['faces'] if row['source_id']==self.plan()['selection']['face_id'])
        self.assertEqual(kernel_selected['relation'],'kernel_link')
        self.assertTrue(kernel_selected['outputs'])
        for link in kernel_selected['outputs']:
            face = body.Shape.Faces[int(link['output_id'][4:])-1]
            self.assertAlmostEqual(face.CenterOfMass.z,8.,places=6)

    def test_supervised_direct_edit_native_and_independent_step_verification(self):
        capabilities = _module('cad_verify_v4_s1')
        result = capabilities.compile_candidate(
            self.manifest,self.root/'prepared.json',self.root/'plan.json',self.root/'card.json',
            self.work/'supervised',profile='c-s2')
        self.assertEqual(result['status'],'PASS',result)
        expected = self.expected['featured_plate']['out_volume_mm3']
        self.assertAlmostEqual(result['compile']['measurements']['volume_mm3'],expected,places=5)
        for representation in ('fcstd','step'):
            self.assertAlmostEqual(
                result['verification']['measurements'][representation]['volume_mm3'],expected,places=5)
        self.assertNotEqual(result['compile']['owned_pid'],result['verification']['owned_pid'])
        self.assertTrue(result['compile']['document_closed'])
        self.assertTrue(result['verification']['document_closed'])

    def test_supervised_smooth_edit_preserves_trimmed_extents_and_analytic_normal_offsets(self):
        capabilities = _module('cad_verify_v4_s1')
        plan = self.plan('smooth_roof_out')
        card = self.ledger.read_json(self.root/'smooth-card.json')
        source = self.source('smooth_roof')
        self.assertAlmostEqual(source.Volume,1674.,places=5)
        result = capabilities.compile_candidate(
            self.manifest,self.root/'prepared.json',self.root/'smooth_roof_out-plan.json',
            self.root/'smooth-card.json',self.work/'smooth-supervised',profile='c-s2')
        self.assertEqual(result['status'],'PASS',result)
        self.assertNotEqual(result['compile']['owned_pid'],result['verification']['owned_pid'])
        self.assertTrue(result['compile']['document_closed'])
        self.assertTrue(result['verification']['document_closed'])
        source_bounds = self.prepared['assets']['smooth_roof']['bounds_mm']
        for measurement in (result['compile']['measurements'],
                            result['verification']['measurements']['fcstd'],
                            result['verification']['measurements']['step']):
            bounds = measurement['bounds_mm']
            for axis,index in [('X',0),('Y',2)]:
                tolerance = next(c['tolerance_mm'] for c in card['criteria']
                                 if c['metric']=='unchanged_dimension' and c['axis']==axis)
                self.assertLessEqual(abs((bounds[index+1]-bounds[index])-
                    (source_bounds[index+1]-source_bounds[index])),tolerance)
            self.assertEqual(measurement['solids'],1)
            self.assertTrue(measurement['valid'])
            self.assertGreater(measurement['volume_mm3'],1674.)
        imported = self.Part.Shape()
        imported.read(result['compile']['artifacts']['step']['path'])
        self.assertEqual(len(imported.Faces),6)
        skin = self.Part.makeCompound(imported.Faces)
        # Independently evaluated authored cubic, not candidate surface probes:
        # x(t)=18t; z(t)=7+6t-9t²+3t³; dz/dt=6-18t+9t².
        for t in (.2,.4,.6,.8):
            z = 7+6*t-9*t*t+3*t*t*t
            derivative = 6-18*t+9*t*t
            normal = self.App.Vector(-derivative,0,18)
            normal = normal/normal.Length
            expected = self.App.Vector(18*t,6,z)+normal*plan['operation']['distance_mm']
            self.assertLess(self.Part.Vertex(expected).distToShape(skin)[0],1e-5)

    def test_missing_tolerance_and_arbitrary_code_are_rejected_host_safely(self):
        plan = self.plan();del plan['kernel_tolerance_mm']
        with self.assertRaises(ValueError):self.editor.validate_plan(plan)
        plan = self.plan();plan['operation']['python'] = 'raise RuntimeError()'
        with self.assertRaises(ValueError):self.editor.validate_plan(plan)
        plan = self.plan();plan['operation']['distance_mm'] = 0
        with self.assertRaises(ValueError):self.editor.validate_plan(plan)


if __name__=='__main__':
    unittest.main()
