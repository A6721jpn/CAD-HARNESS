"""Independent S2 controls, no editor/compiler imports and no discovery launches.

Run native controls only with CAD_VERIFY_S2_NATIVE=1 under the pinned FreeCAD
Python. Fixtures are authored analytically inside temporary directories; no
pilot/private data, live calls, candidate reports, or candidate implementation.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE = (os.environ.get('CAD_VERIFY_S2_NATIVE') == '1' and
          sys.version_info[:3] == (3,11,14) and importlib.util.find_spec('FreeCAD') is not None)
NATIVE_REASON = 'set CAD_VERIFY_S2_NATIVE=1 under pinned FreeCAD Python; no launch at discovery'


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '')+name)


def _card(*criteria):
    return dict(schema='cad-harness.judge-card.v4c',profile='c-s2',source='independent_dev',
                numerical_uncertainty_mm=1e-5,criteria=list(criteria))


class S2JudgeAdmission(unittest.TestCase):
    def setUp(self):
        self.judges = _module('cad_verify_v4_s2_judges')

    def test_strict_missing_tolerance_and_uncertainty_rejected(self):
        c = dict(id='dimension',metric='unchanged_dimension',definition='axis_extent',axis='X',tolerance_mm=.001)
        card = _card(c)
        self.assertEqual(self.judges.validate_card(card),card)
        del c['tolerance_mm']
        with self.assertRaises(ValueError):
            self.judges.validate_card(card)
        card = _card(dict(id='solid',metric='solid_valid',expected_solids=1))
        del card['numerical_uncertainty_mm']
        with self.assertRaises(ValueError):
            self.judges.validate_card(card)

    def test_nonfinite_unknown_fields_and_duplicate_ids_rejected(self):
        card = _card(dict(id='solid',metric='solid_valid',expected_solids=1))
        for key,value in (('numerical_uncertainty_mm',float('nan')),('profile','c-s1'),('report',{'passed':True})):
            bad = copy.deepcopy(card);bad[key] = value
            with self.assertRaises(ValueError):
                self.judges.validate_card(bad)
        card['criteria'] *= 2
        with self.assertRaises(ValueError):
            self.judges.validate_card(card)

    def test_admission_returns_independent_copy(self):
        card = _card(dict(id='solid',metric='solid_valid',expected_solids=1))
        result = self.judges.validate_card(card)
        result['criteria'][0]['expected_solids'] = 2
        self.assertEqual(card['criteria'][0]['expected_solids'],1)

    def test_single_solid_policy_cannot_be_overridden_by_card(self):
        for count in (0,2):
            with self.assertRaises(ValueError):
                self.judges.validate_card(_card(dict(id='solid',metric='solid_valid',expected_solids=count)))


@unittest.skipUnless(NATIVE,NATIVE_REASON)
class S2IndependentNativeJudges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3]) != ('1','1','4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App,cls.Part = App,Part
        cls.inputs = _module('cad_verify_v4_inputs')
        cls.ledger = _module('cad_verify_v4_ledger')
        cls.judges = _module('cad_verify_v4_s2_judges')
        cls.plans = _module('cad_verify_v4_plans')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cad-s2-independent-judges-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.set_source(self.Part.makeBox(12,8,4))

    def set_source(self,shape):
        self.original = shape
        self.source_index = getattr(self,'source_index',0)+1
        source_root = self.root / ('source-'+str(self.source_index))
        source_root.mkdir()
        step = source_root/'source.step'
        shape.exportStep(str(step))
        self.manifest = source_root/'manifest.json'
        digest = self.ledger.file_sha(step)
        manifest = dict(schema='cad-harness.inputs.v4c',profile='c-s2',evidence_mode='independent_dev',
            assets={'source':dict(kind='step',role='reference',path='source.step',sha256=digest,bytes=step.stat().st_size)})
        self.manifest.write_text(json.dumps(manifest),encoding='utf-8')
        recipe = dict(schema='cad-harness.step-recipe.v4c',profile='c-s2',source_axes=['X','Y','Z'],source_units='mm',signature_precision_mm=1e-6)
        self.prepared = self.inputs.inspect_step(self.manifest,'source',recipe,source_root/'prepared.json')
        self.facts = self.prepared['assets']['source']
        top = max(self.facts['faces'],key=lambda f:f['center_mm'][2])
        self.plan = dict(schema='cad-harness.plan.v4c',profile='c-s2',family='step_direct_edit',asset_id='source',source_sha256=digest,
            selection={k:top[k] for k in ('signature','adjacent_face_ids')},operation=dict(kind='offset',distance_mm=.5,reconnect='extend_intersect_trim'),kernel_tolerance_mm=1e-6)
        self.plan['selection']['face_id'] = top['id']

    def face_at(self,z,sign):
        faces = [f for f in self.facts['faces'] if abs(f['center_mm'][2]-z)<1e-6 and f['normal'] and sign*f['normal'][2]>.9]
        self.assertEqual(len(faces),1)
        return faces[0]['id']

    def thickness(self,scope='continuous',top=4.5):
        return dict(id='wall',metric='thickness_distribution',scope=scope,convention='directed_material_chord',direction=[0,0,1],
            domain=dict(origin_mm=[1,1,0],u=[1,0,0],v=[0,1,0],size_mm=[10,6]),
            opposed_sets=dict(a=dict(source_face_ids=[self.face_at(0,-1)],output_region_mm=[0,12,0,8,-.1,.1]),
                              b=dict(source_face_ids=[self.face_at(4,1)],output_region_mm=[0,12,0,8,top-.1,top+.1])),
            expected_range_mm=[top,top],tolerance_mm=.001,samples=[3,3],ray_length_mm=30)

    def run_judge(self,shape,*criteria,**context):
        card = _card(*criteria)
        result = self.judges.judge(self.plan,self.manifest,self.prepared,shape,card,**context)
        self.plans.validate_document(result,'judge-result',profile='c-s2')
        return result

    def assert_status(self,result,status):
        self.assertEqual(result['status'],status,result)
        for check in result['checks']:
            self.assertIn('units',check['evidence'])
            self.assertIsNotNone(check['target'])
            self.assertIsNotNone(check['tolerance'])

    def test_planar_global_certificate_same_card_native_and_independent_step(self):
        shape = self.Part.makeBox(12,8,4.5)
        c = self.thickness()
        native = self.run_judge(shape,c)
        self.assert_status(native,'PASS')
        self.assertAlmostEqual(native['checks'][0]['measured']['global_min_mm'],4.5)
        self.assertEqual(native['checks'][0]['evidence']['coverage'],'entire_declared_rectangle')
        path = self.root/'independent-output.step';shape.exportStep(str(path))
        reopened = self.Part.Shape();reopened.read(str(path))
        self.assert_status(self.run_judge(reopened,c),'PASS')

    def test_wrong_sign_wrong_thickness_and_far_decoy_fail(self):
        c = self.thickness()
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5,self.App.Vector(0,0,-.5)),c),'FAIL')
        wrong = self.thickness(top=4)
        wrong['expected_range_mm'] = [4.5,4.5]
        self.assert_status(self.run_judge(self.original,wrong),'FAIL')
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5,self.App.Vector(50,0,0)),c),'FAIL')

    def test_sampled_scope_never_claims_global_extrema(self):
        result = self.run_judge(self.Part.makeBox(12,8,4.5),self.thickness(scope='sampled'))
        self.assert_status(result,'PASS')
        check = result['checks'][0]
        self.assertIsNone(check['measured']['global_min_mm'])
        self.assertIsNone(check['measured']['global_max_mm'])
        self.assertFalse(check['evidence']['continuous_certificate'])
        self.assertEqual(check['evidence']['coverage'],'declared_cell_centres_only')

    def test_interior_cavity_outside_samples_cannot_receive_global_pass(self):
        output = self.Part.makeBox(12,8,4.5).cut(self.Part.makeBox(.3,.3,.3,self.App.Vector(1.1,1.1,1)))
        result = self.run_judge(output,self.thickness())
        self.assert_status(result,'UNVERIFIED')
        self.assertIsNone(result['checks'][0]['measured']['global_min_mm'])
        self.assertIn('not_convex',result['checks'][0]['evidence']['reason'])

    def test_interior_cavity_on_sample_multiple_material_hits_fail(self):
        output = self.Part.makeBox(12,8,4.5).cut(self.Part.makeBox(1,1,1,self.App.Vector(5.5,3.5,1)))
        result = self.run_judge(output,self.thickness())
        self.assert_status(result,'FAIL')
        self.assertTrue(result['checks'][0]['evidence']['ray_problems'])

    def test_multiple_solids_along_ray_and_wrong_opposing_set_fail(self):
        bottom = self.Part.makeBox(12,8,2)
        upper = self.Part.makeBox(12,8,2,self.App.Vector(0,0,3))
        self.assert_status(self.run_judge(self.Part.makeCompound([bottom,upper]),self.thickness(top=5)),'FAIL')
        c = self.thickness()
        c['opposed_sets']['a']['output_region_mm'] = [0,12,0,8,4.4,4.6]
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5),c),'FAIL')

    def test_incomplete_continuous_domain_and_partial_output_patch_rejected(self):
        c = self.thickness()
        c['domain']['size_mm'] = [12,8]
        result = self.run_judge(self.Part.makeBox(12,8,4.5),c)
        self.assertIn(result['status'],('FAIL','UNVERIFIED'),result)
        c = self.thickness()
        c['opposed_sets']['b']['output_region_mm'] = [5,7,3,5,4.4,4.6]
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5),c),'FAIL')

    def test_curved_actual_geometry_keeps_continuous_unknown(self):
        output = self.Part.makeBox(12,8,4.5).fuse(self.Part.makeCylinder(.05,.4,self.App.Vector(1.2,1.2,4.5)))
        result = self.run_judge(output,self.thickness())
        self.assert_status(result,'UNVERIFIED')
        self.assertIsNone(result['checks'][0]['measured']['global_max_mm'])
        self.assertIn('not_planar',result['checks'][0]['evidence']['reason'])

    def test_curved_feature_outside_full_ray_domain_does_not_block_local_certificate(self):
        output = self.Part.makeBox(12,8,4.5).cut(self.Part.makeCylinder(.3,1,self.App.Vector(.5,.5,0)))
        self.assert_status(self.run_judge(output,self.thickness()),'PASS')

    def test_analytic_tilted_replacement_affine_extrema_certificate(self):
        points = [self.App.Vector(0,0,0),self.App.Vector(12,0,0),self.App.Vector(12,0,5.5),self.App.Vector(0,0,4.5),self.App.Vector(0,0,0)]
        output = self.Part.Face(self.Part.makePolygon(points)).extrude(self.App.Vector(0,8,0))
        c = self.thickness(top=5)
        c['opposed_sets']['b']['output_region_mm'] = [0,12,0,8,4.4,5.6]
        c['expected_range_mm'] = [4.5+1/12,5.5-1/12]
        result = self.run_judge(output,c)
        self.assert_status(result,'PASS')
        self.assertAlmostEqual(result['checks'][0]['measured']['global_min_mm'],4.5+1/12,places=6)
        self.assertAlmostEqual(result['checks'][0]['measured']['global_max_mm'],5.5-1/12,places=6)

    def test_unchanged_source_axis_not_card_target_or_candidate_report(self):
        c = dict(id='width',metric='unchanged_dimension',definition='axis_extent',axis='X',tolerance_mm=.001)
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5),c),'PASS')
        self.assert_status(self.run_judge(self.Part.makeBox(13,8,4.5),c,operation_report={'unchanged':True}),'FAIL')

    def test_trimmed_bspline_support_is_not_source_axis_extent(self):
        def slab(width):
            surface = self.Part.BSplineSurface()
            poles = [[self.App.Vector(width*(i-1),8*(j-1),0) for j in range(4)] for i in range(4)]
            surface.buildFromPolesMultsKnots(poles,[4,4],[4,4],[0,1],[0,1],False,False,3,3)
            return surface.toShape(1/3,2/3,1/3,2/3).extrude(self.App.Vector(0,0,4.5))
        # Independently authored polynomial support spans three times the
        # trimmed rectangle. Native legacy bounds enclose that remote support.
        output = slab(12)
        self.assertGreater(output.BoundBox.XLength,24)
        self.assertGreater(output.BoundBox.YLength,16)
        width = dict(id='width',metric='unchanged_dimension',definition='axis_extent',axis='X',tolerance_mm=.001)
        height = dict(id='height',metric='unchanged_dimension',definition='axis_extent',axis='Y',tolerance_mm=.001)
        result = self.run_judge(output,dict(id='solid',metric='solid_valid',expected_solids=1),width,height)
        self.assert_status(result,'PASS')
        self.assertAlmostEqual(result['checks'][1]['measured']['output_mm'],12,places=5)
        self.assertAlmostEqual(result['checks'][2]['measured']['output_mm'],8,places=5)
        self.assert_status(self.run_judge(slab(13),width),'FAIL')

    def test_source_vertex_landmarks_and_ambiguity(self):
        c = dict(id='base_width',metric='unchanged_dimension',definition='landmark_distance',landmarks_mm=[[0,0,0],[12,0,0]],search_radius_mm=.2,tolerance_mm=.001)
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5),c),'PASS')
        self.assert_status(self.run_judge(self.Part.makeBox(12.1,8,4.5),c),'FAIL')
        c['search_radius_mm'] = 20
        self.assert_status(self.run_judge(self.original,c),'UNVERIFIED')

    def test_full_region_counts_and_explicit_spatial_correspondence(self):
        full = dict(id='full',metric='face_count',scope='full',relation='equal',expected_count=6,correspondence='spatial_fixed_frame')
        regional = dict(id='base_region',metric='face_count',scope='region',relation='delta',expected_delta=0,
            correspondence='spatial_fixed_frame',region_mm=[1,11,1,7,-.1,.1],region_rule='positive_area_clip')
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5),full,regional),'PASS')
        full['expected_count'] = 7
        self.assert_status(self.run_judge(self.original,full),'FAIL')
        top = dict(regional,id='top_region',region_mm=[1,11,1,7,3.9,4.1])
        self.assert_status(self.run_judge(self.Part.makeBox(12,8,4.5),top),'FAIL')

    def test_local_feature_movement_equal_bbox_and_volume_fails_roi(self):
        base = self.Part.makeBox(12,8,4)
        original = base.fuse(self.Part.makeCylinder(.5,1,self.App.Vector(3,3,4)))
        shifted = base.fuse(self.Part.makeCylinder(.5,1,self.App.Vector(7,3,4)))
        self.set_source(original)
        self.assertAlmostEqual(original.Volume,shifted.Volume,places=6)
        self.assertEqual(self.judges._bounds(original),self.judges._bounds(shifted))
        c = dict(id='local',metric='preserved_region',region_mm=[2,8,2,4,3,5.1],maximum_symmetric_difference_mm3=.001,volume_uncertainty_mm3=.0001)
        self.assert_status(self.run_judge(original,c),'PASS')
        result = self.run_judge(shifted,c)
        self.assert_status(result,'FAIL')
        self.assertEqual(result['checks'][0]['evidence']['claim'],'bounded_material_volume_change_not_surface_deviation')

    def test_empty_preserved_roi_and_insufficient_numeric_budget_unknown(self):
        c = dict(id='local',metric='preserved_region',region_mm=[50,51,0,1,0,1],maximum_symmetric_difference_mm3=.001,volume_uncertainty_mm3=.0001)
        self.assert_status(self.run_judge(self.original,c),'UNVERIFIED')
        card = _card(dict(id='solid',metric='solid_valid',expected_solids=1));card['numerical_uncertainty_mm'] = 1e-12
        result = self.judges.judge(self.plan,self.manifest,self.prepared,self.original,card)
        self.assert_status(result,'UNVERIFIED')

    def test_missing_ray_coverage_and_source_wrong_face_unknown(self):
        c = self.thickness();c['ray_length_mm'] = 1
        self.assert_status(self.run_judge(self.original,c),'UNVERIFIED')
        c = self.thickness();c['opposed_sets']['a']['source_face_ids'] = [self.face_at(4,1)]
        c['opposed_sets']['b']['source_face_ids'] = [self.face_at(0,-1)]
        self.assert_status(self.run_judge(self.original,c),'UNVERIFIED')

    def test_hash_tamper_and_reordered_original_facts_not_accepted(self):
        c = dict(id='solid',metric='solid_valid',expected_solids=1)
        prepared = copy.deepcopy(self.prepared)
        self.prepared['assets']['source']['faces'].reverse()
        self.assert_status(self.run_judge(self.original,c),'UNVERIFIED')
        self.prepared = prepared
        self.plan['source_sha256'] = '0'*64
        self.assert_status(self.run_judge(self.original,c),'UNVERIFIED')

    def test_actual_solid_null_shell_and_multi_solid_controls(self):
        c = dict(id='solid',metric='solid_valid',expected_solids=1)
        self.assert_status(self.run_judge(self.original,c),'PASS')
        self.assert_status(self.run_judge(self.Part.Shape(),c),'FAIL')
        self.assert_status(self.run_judge(self.Part.makeShell(self.original.Faces),c),'FAIL')
        other = self.Part.makeBox(1,1,1,self.App.Vector(20,0,0))
        self.assert_status(self.run_judge(self.Part.makeCompound([self.original,other]),c),'FAIL')

    def test_actual_native_and_step_reopen_roundtrip(self):
        doc = self.App.newDocument('S2IndependentRoundtrip')
        self.addCleanup(self.close_document,doc.Name)
        body = doc.addObject('PartDesign::Body','Body')
        box = body.newObject('PartDesign::AdditiveBox','AnalyticBox')
        box.Length,box.Width,box.Height = 12,8,4.5
        doc.recompute()
        before = body.Shape.copy()
        path = self.root/'native.FCStd';doc.saveAs(str(path))
        step = self.root/'output.step';before.exportStep(str(step))
        self.App.closeDocument(doc.Name)
        reopened = self.App.openDocument(str(path))
        self.addCleanup(self.close_document,reopened.Name)
        native_body = reopened.getObject('Body')
        native_box = reopened.getObject('AnalyticBox')
        native_box.Height = 4.75;reopened.recompute()
        operative = abs(native_body.Shape.Volume-before.Volume)>1
        native_box.Height = 4.5;reopened.recompute()
        imported = self.Part.Shape();imported.read(str(step))
        bounds = lambda a,b:max(abs(x-y) for x,y in zip(self.judges._bounds(a),self.judges._bounds(b)))
        evidence = dict(fcstd_reopened=not native_body.Shape.isNull(),step_reopened=not imported.isNull(),editable=operative,
            bounds_difference_mm=max(bounds(before,native_body.Shape),bounds(before,imported)),
            volume_difference_mm3=max(abs(before.Volume-native_body.Shape.Volume),abs(before.Volume-imported.Volume)))
        c = dict(id='native',metric='native_roundtrip',maximum_bounds_difference_mm=.001,maximum_volume_difference_mm3=.001,require_editable=True)
        self.assert_status(self.run_judge(native_body,c,native_evidence=evidence),'PASS')
        self.assert_status(self.run_judge(imported,c,native_evidence=evidence),'PASS')
        evidence['editable'] = False
        self.assert_status(self.run_judge(imported,c,native_evidence=evidence),'FAIL')
        self.assert_status(self.run_judge(imported,c),'UNVERIFIED')

    def close_document(self,name):
        if name in self.App.listDocuments():
            self.App.closeDocument(name)


if __name__ == '__main__':
    unittest.main()
