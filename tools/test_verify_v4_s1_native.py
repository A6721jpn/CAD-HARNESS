"""Independent development-only native acceptance and numerical boundary tests.

No native launch at import/discovery. Explicit CAD_VERIFY_S1_NATIVE=1 and the
pinned runtime are required. CAD_VERIFY_S1_FIXTURES optionally reuses separately
generated assets; otherwise the independent source generator runs in a temporary
directory only after the explicit guard. No provider calls.
"""
import copy
import importlib.util
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE_REASON = 'native capability not exercised: set CAD_VERIFY_S1_NATIVE=1 under pinned FreeCAD Python'
NATIVE = os.environ.get('CAD_VERIFY_S1_NATIVE') == '1' and sys.version_info[:3] == (3,11,14) and importlib.util.find_spec('FreeCAD') is not None


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '')+name)


@unittest.skipUnless(NATIVE,NATIVE_REASON)
class S1NativeAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3]) != ('1','1','4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App,cls.Part=App,Part
        cls.ledger=_module('cad_verify_v4_ledger')
        cls.judges=_module('cad_verify_v4_judges')
        cls.inputs=_module('cad_verify_v4_inputs')
        cls.compiler=_module('cad_verify_v4_compile')
        cls.contours=_module('cad_verify_v4_contours')
        source=Path(__file__).resolve().parents[1]/'design/cad-harness-verify-v4/dev-c-s1/generate.py'
        spec=importlib.util.spec_from_file_location('s1_analytic_source',source)
        cls.source=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.source)
        value=os.environ.get('CAD_VERIFY_S1_FIXTURES')
        if not value:
            generated=tempfile.TemporaryDirectory(prefix='cad-s1-source-fixtures-')
            cls.addClassCleanup(generated.cleanup)
            value=cls.source.generate(Path(generated.name)/'assets')
        path=Path(value).absolute()
        if any(p.lower() in ('pilot-user','v4-holdout-private') for p in path.parts):
            raise RuntimeError('forbidden_data_path')
        cls.root=path;cls.manifest=path/'manifest.json'
        cls.expected=cls.ledger.read_json(path/'expected.json')
        cls.packet=cls.ledger.read_json(path/'prepared.json')
        cls.plan=cls.ledger.read_json(path/'plan.json')
        cls.card=cls.ledger.read_json(path/'card.json')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cad-s1-independent-')
        self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.doc=self.App.newDocument('S1Independent')
        self.addCleanup(self.close_document, self.doc.Name)

    def close_document(self, name):
        if name in self.App.listDocuments():
            self.App.closeDocument(name)

    def card_for(self,*criteria):
        return dict(schema='cad-harness.judge-card.v4c',profile='c-s1',source='independent_dev',linear_tolerance_mm=1e-5,criteria=list(criteria))

    def run_judge(self,shape,card=None,plan=None,packet=None,**context):
        return self.judges.judge(plan or self.plan,self.manifest,packet or self.packet,shape,card or self.card,**context)

    def build(self,plan=None,packet=None):
        body=self.compiler.build_plan(self.doc,plan or self.plan,self.manifest,packet or self.packet)
        self.doc.recompute()
        return body

    def assertStatus(self,result,status):
        self.assertEqual(result['status'],status,result)

    def reference_facts(self,asset='reference_box'):
        recipe=dict(schema='cad-harness.step-recipe.v4c',profile='c-s1',source_axes=['X','Y','Z'],source_units='mm',signature_precision_mm=1e-6)
        return self.inputs.inspect_step(self.manifest,asset,recipe,self.work/(asset+'.json'))

    def test_c1_original_native_facts_analytic_volume_bounds_and_faces(self):
        packet=self.reference_facts()
        facts=packet['assets']['reference_box']
        self.assertEqual(facts['units'],'mm')
        for a,b in zip(facts['bounds_mm'],[0,18,0,12,0,7]):self.assertAlmostEqual(a,b,places=6)
        self.assertEqual(facts['topology']['solids'],1)
        self.assertEqual(facts['topology']['faces'],6)
        top=[f for f in facts['faces'] if math.dist(f['center_mm'],[9,6,7])<1e-6]
        self.assertEqual(len(top),1)
        self.assertAlmostEqual(top[0]['area_mm2'],216,places=6)
        self.assertFalse(top[0]['ambiguous'])
        shape=self.Part.Shape();shape.read(str(self.root/'reference-box.step'))
        card=self.card_for(dict(id='solid',metric='solid_valid'),dict(id='volume',metric='volume',expected_mm3=1512,tolerance_mm3=1e-5))
        self.assertStatus(self.run_judge(shape,card,packet=packet),'PASS')

    def test_c1_selected_original_face_gap_contact_placement_not_min_distance(self):
        packet=self.reference_facts();facts=packet['assets']['reference_box']
        face=next(f for f in facts['faces'] if math.dist(f['center_mm'],[9,6,7])<1e-6)
        c=dict(id='gap',metric='reference_gap',asset_id='reference_box',face_id=face['id'],candidate_face_index=5,
            translation_mm=[0,0,0],rotation_axis=[0,0,1],rotation_deg=0,normal=[0,0,1],expected_gap_mm=1,
            contact_area_min_mm2=215,contact_tolerance_mm=1e-5)
        shape=self.Part.makeBox(18,12,7,self.App.Vector(0,0,8))
        self.assertStatus(self.run_judge(shape,self.card_for(c),packet=packet),'PASS')
        shape.translate(self.App.Vector(0,0,.2))
        self.assertStatus(self.run_judge(shape,self.card_for(c),packet=packet),'FAIL')
        shifted=self.Part.makeBox(18,12,7,self.App.Vector(50,0,8))
        self.assertStatus(self.run_judge(shifted,self.card_for(c),packet=packet),'FAIL')
        placed=copy.deepcopy(c);placed['translation_mm']=[5,-3,2];placed['rotation_deg']=90
        rotated=self.Part.makeBox(12,18,7,self.App.Vector(-7,-3,10))
        self.assertStatus(self.run_judge(rotated,self.card_for(placed),packet=packet),'PASS')
        c['face_id']='not-an-original-face'
        self.assertStatus(self.run_judge(shape,self.card_for(c),packet=packet),'UNVERIFIED')

    def test_c1_declared_translation_play_interval_with_certified_uncertainty(self):
        packet=self.reference_facts()
        c=dict(id='play',metric='translation_clearance',asset_id='reference_box',translation_mm=[0,0,0],
            rotation_axis=[0,0,1],rotation_deg=0,direction=[1,0,0],interval_mm=[-2,2],samples=201,penetration_tolerance_mm3=20)
        separated=self.Part.makeBox(18,12,7,self.App.Vector(0,0,10))
        result=self.run_judge(separated,self.card_for(c),packet=packet)
        self.assertStatus(result,'PASS')
        self.assertGreater(result['checks'][0]['uncertainty'],0)
        self.assertStatus(self.run_judge(self.Part.makeBox(18,12,7),self.card_for(c),packet=packet),'FAIL')
        c['penetration_tolerance_mm3']=0
        self.assertStatus(self.run_judge(separated,self.card_for(c),packet=packet),'UNVERIFIED')

    def test_c1_maximum_play_requires_collision_stops_and_explicit_convention(self):
        packet=self.reference_facts()
        outside=self.Part.makeBox(30,24,19,self.App.Vector(-6,-6,-6))
        cavity=self.Part.makeBox(22,16,11,self.App.Vector(-2,-2,-2))
        fixture=outside.cut(cavity)
        c=dict(id='bounded_play',metric='reference_play',asset_id='reference_box',
            translation_mm=[0,0,0],rotation_axis=[0,0,1],rotation_deg=0,direction=[1,0,0],
            interval_mm=[-3,3],samples=9,penetration_tolerance_mm3=1e-6,
            volume_uncertainty_mm3=1e-9,position_tolerance_mm=.01,maximum_play_mm=4.1,convention='total')
        result=self.run_judge(fixture,self.card_for(c),packet=packet)
        self.assertStatus(result,'PASS')
        measured=result['checks'][0]['measured']
        # Independent box-difference oracle: (22 - 18) = 4 mm total X play.
        self.assertLessEqual(measured['lower_play_mm'],4)
        self.assertGreaterEqual(measured['upper_play_mm'],4)
        self.assertStatus(self.run_judge(fixture,self.card_for(dict(c,maximum_play_mm=3.5)),packet=packet),'FAIL')
        self.assertStatus(self.run_judge(fixture,self.card_for(dict(c,convention='positive',maximum_play_mm=2.05)),packet=packet),'PASS')
        self.assertStatus(self.run_judge(fixture,self.card_for(dict(c,interval_mm=[-1,1])),packet=packet),'UNVERIFIED')
        wide=outside.cut(self.Part.makeBox(26,20,15,self.App.Vector(-4,-4,-4)))
        self.assertStatus(self.run_judge(wide,self.card_for(c),packet=packet),'FAIL')
        missing=dict(c);missing.pop('volume_uncertainty_mm3')
        self.assertStatus(self.run_judge(fixture,self.card_for(missing),packet=packet),'UNVERIFIED')

    def test_c1_reference_fixture_exports_only_part_and_keeps_native_pocket_operative(self):
        facts=self.reference_facts()
        packet=dict(self.packet,assets=dict(self.packet['assets'],**facts['assets']))
        spec=dict(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world',
            regions=[dict(bounds=[0,28,0,20,0,6])],pockets=[dict(bounds=[8,18,6,14],top_z=6,depth=3)],
            holes=[],finish=None)
        plan=dict(schema='cad-harness.plan.v4c',profile='c-s1',family='reference_fixture',
            build_spec=spec,references=[dict(asset_id='reference_box',translation_mm=[0,0,20],
                rotation_axis=[0,0,1],rotation_deg=0)],engravings=[])
        body=self.build(plan,packet)
        self.assertEqual(len(body.Shape.Solids),1)
        self.assertAlmostEqual(body.Shape.Volume,28*20*6-10*8*3,places=5)
        self.assertAlmostEqual(body.Shape.BoundBox.ZMax,6,places=6)
        self.doc.getObject('RectPocket0').Length=4;self.doc.recompute()
        self.assertAlmostEqual(body.Shape.Volume,28*20*6-10*8*4,places=5)
        path=self.work/'reference-fixture.step';body.Shape.exportStep(str(path))
        exported=self.Part.Shape();exported.read(str(path))
        self.assertEqual(len(exported.Solids),1)
        self.assertAlmostEqual(exported.Volume,28*20*6-10*8*4,places=5)

    def test_c1_complete_curved_face_clearance_and_contact_area(self):
        source=self.work/'curved-source.step'
        self.Part.makeCylinder(5,9).exportStep(str(source))
        manifest=self.work/'curved-inputs.json'
        self.ledger.write_json(manifest,dict(schema='cad-harness.inputs.v4c',profile='c-s1',
            evidence_mode='independent_dev',assets={'curved':dict(kind='step',role='reference',
                path=source.name,sha256=self.ledger.file_sha(source),bytes=source.stat().st_size)}))
        recipe=dict(schema='cad-harness.step-recipe.v4c',profile='c-s1',source_axes=['X','Y','Z'],
            source_units='mm',signature_precision_mm=1e-6)
        packet=self.inputs.inspect_step(manifest,'curved',recipe,self.work/'curved-facts.json')
        face=next(f for f in packet['assets']['curved']['faces'] if f['surface_type']=='Cylinder')
        base=dict(id='region',asset_id='curved',translation_mm=[0,0,0],rotation_axis=[0,0,1],
                  rotation_deg=0,face_ids=[face['id']])
        clear=dict(base,metric='reference_clearance',minimum_gap_mm=.8,strict_separation=True)
        ring=self.Part.makeCylinder(7,9).cut(self.Part.makeCylinder(6,9))
        self.assertStatus(self.judges.judge(self.plan,manifest,packet,ring,self.card_for(clear)),'PASS')
        touching=self.Part.makeCylinder(7,9).cut(self.Part.makeCylinder(5,9))
        self.assertStatus(self.judges.judge(self.plan,manifest,packet,touching,self.card_for(clear)),'FAIL')
        contact=dict(base,metric='reference_contact',maximum_contact_area_mm2=300,area_uncertainty_mm2=.001)
        result=self.judges.judge(self.plan,manifest,packet,touching,self.card_for(contact))
        self.assertStatus(result,'PASS')
        self.assertAlmostEqual(result['checks'][0]['measured']['exact_contact_area_mm2'],90*math.pi,places=5)
        self.assertStatus(self.judges.judge(self.plan,manifest,packet,touching,
            self.card_for(dict(contact,maximum_contact_area_mm2=280))),'FAIL')

    def test_c1_duplicate_face_identity_is_unverified_not_auto_selected(self):
        packet=self.reference_facts('ambiguous_reference')
        faces=packet['assets']['ambiguous_reference']['faces']
        ambiguous=[f for f in faces if f['ambiguous']]
        self.assertTrue(ambiguous,'coincident duplicate analytic faces must be ambiguous')
        c=dict(id='gap',metric='reference_gap',asset_id='ambiguous_reference',face_id=ambiguous[0]['id'],candidate_face_index=5,
            translation_mm=[0,0,0],rotation_axis=[0,0,1],rotation_deg=0,normal=[0,0,1],expected_gap_mm=0,
            contact_area_min_mm2=1,contact_tolerance_mm=1e-5)
        self.assertStatus(self.run_judge(self.Part.makeBox(18,12,7),self.card_for(c),packet=packet),'UNVERIFIED')

    def test_c2_analytic_compiler_two_leg_fidelity_and_actual_native_roundtrip(self):
        body=self.build()
        saved=self.work/'independent.FCStd';step=self.work/'independent.step'
        self.doc.saveAs(str(saved));body.Shape.exportStep(str(step))
        reopened=self.App.openDocument(str(saved))
        self.addCleanup(self.close_document, reopened.Name)
        reopened.recompute()
        restored=reopened.getObject(body.Name)
        imported=self.Part.Shape();imported.read(str(step))
        expected_volume=(34*22-(4-math.pi)*9)*4
        self.assertAlmostEqual(body.Shape.Volume,expected_volume,places=5)
        self.assertAlmostEqual(imported.Volume,expected_volume,places=5)
        evidence=dict(fcstd_reopened=True,step_reopened=True,editable=hasattr(reopened.getObject('ContourExtrude'),'Width'),
            bounds_difference_mm=max(abs(a-b) for a,b in zip(self.judges._bounds(body.Shape),self.judges._bounds(imported))),
            volume_difference_mm3=abs(restored.Shape.Volume-imported.Volume))
        self.assertStatus(self.run_judge(restored,native_evidence=evidence),'PASS')
        self.assertStatus(self.run_judge(imported,native_evidence=evidence),'PASS')
        self.assertEqual(len(restored.Shape.Solids),1)
        self.assertEqual(restored.TypeId,'PartDesign::Body')
        self.assertEqual(reopened.getObject('ContourExtrude').TypeId,'PartDesign::FeaturePython')

    def test_c2_hausdorff_uses_symmetric_maximum_and_interval_boundary(self):
        from shapely.geometry import box
        a,b=box(0,0,10,10),box(0,0,12,10)
        self.assertEqual(a.distance(b),0)
        bounds=self.judges.hausdorff_bounds(a,b,.2)
        self.assertLessEqual(bounds['lower_mm'],2)
        self.assertGreaterEqual(bounds['upper_mm'],2)
        self.assertEqual(self.judges._interval_status(bounds['lower_mm'],bounds['upper_mm'],1.9),'FAIL')
        self.assertEqual(self.judges._interval_status(bounds['lower_mm'],bounds['upper_mm'],2.2),'PASS')
        self.assertEqual(self.judges._interval_status(bounds['lower_mm'],bounds['upper_mm'],2.01),'UNVERIFIED')
        uncertain=self.judges.hausdorff_bounds(a,b,.2,.03,.04)
        self.assertAlmostEqual(uncertain['lower_mm'],1.93)
        self.assertGreater(uncertain['upper_mm'],bounds['upper_mm'])

    def test_c2_radius_remeasures_handed_over_shape_and_operative_scale(self):
        body=self.build()
        criterion=next(c for c in self.card['criteria'] if c['metric']=='min_radius')
        card=self.card_for(criterion)
        self.assertStatus(self.run_judge(body,card),'PASS')
        sharp=self.Part.makeBox(34,22,4,self.App.Vector(4,4,0))
        self.assertStatus(self.run_judge(sharp,card),'FAIL')
        self.doc.getObject('ContourExtrude').Width=17
        self.doc.recompute()
        self.assertStatus(self.run_judge(body,card),'FAIL')

    def test_c2_access_remeasures_sub_tool_width_output(self):
        body=self.build()
        criterion=next(c for c in self.card['criteria'] if c['metric']=='tool_access')
        card=self.card_for(criterion)
        self.assertStatus(self.run_judge(body,card),'PASS')
        narrow=self.Part.makeBox(.8,22,4,self.App.Vector(4,4,0))
        self.assertStatus(self.run_judge(narrow,card),'FAIL')

    def test_c2_scale_hole_island_and_fidelity_negatives(self):
        body=self.build()
        card=copy.deepcopy(self.card)
        card['criteria']=[c for c in card['criteria'] if c['metric'] in ('image_iou','boundary_hausdorff')]
        self.assertStatus(self.run_judge(body,card),'PASS')
        wrong=copy.deepcopy(self.plan);wrong['width_mm']=40
        self.assertStatus(self.run_judge(body,card,plan=wrong),'FAIL')
        for asset in ('hole_mask','inverse_mask'):
            bad=copy.deepcopy(card)
            bad['criteria']=[c for c in bad['criteria'] if c['leg']=='image_to_contour']
            for c in bad['criteria']:c['mask_asset_id']=asset
            self.assertStatus(self.run_judge(body,bad),'FAIL')
        bad=copy.deepcopy(card);bad['criteria']=[c for c in bad['criteria'] if c['metric']=='boundary_hausdorff' and c['leg']=='image_to_contour']
        bad['criteria'][0]['mask_asset_id']='island_mask'
        self.assertStatus(self.run_judge(body,bad),'FAIL')

    def test_c2_planar_tool_center_pass_fail_and_uncertainty(self):
        c=next(c for c in self.card['criteria'] if c['metric']=='tool_access')
        result=self.judges.tool_access(self.packet['assets']['analytic_contour'],c)
        self.assertEqual(result['status'],'PASS',result)
        bad=copy.deepcopy(c);bad['tool_radius_mm']=20
        self.assertEqual(self.judges.tool_access(self.packet['assets']['analytic_contour'],bad)['status'],'FAIL')
        boundary=copy.deepcopy(c);boundary['maximum_uncovered_mm2']=result['uncovered_lower_mm2']
        self.assertEqual(self.judges.tool_access(self.packet['assets']['analytic_contour'],boundary)['status'],'UNVERIFIED')
        points=[[0,0],[4,0],[4,1.75],[8,1.75],[8,0],[12,0],[12,4],[8,4],[8,2.25],[4,2.25],[4,4],[0,4]]
        dogbone=dict(units='mm',loops=[dict(role='outer',segments=[dict(kind='line',p0=p,p1=q)
            for p,q in zip(points,points[1:]+points[:1])])])
        connectivity=copy.deepcopy(c);connectivity['maximum_uncovered_mm2']=999
        split=self.judges.tool_access(dogbone,connectivity)
        self.assertEqual(split['status'],'FAIL',split)
        self.assertEqual(split['center_components'],2)

    def test_c2_integer_luminance_and_checker_mask_commitment(self):
        import numpy as np
        from PIL import Image
        rgba=np.full((30,40,4),255,dtype=np.uint8)
        rgba[4:26,4:36,:3]=[0,128,0]  # Rec.601 rounds 75.136 to 75.
        rgba[10:20,14:26,:3]=[255,0,0]  # Rounds to 76; a registered hole.
        image=self.work/'colored.png';Image.fromarray(rgba).save(image)
        manifest=self.work/'colored-inputs.json'
        self.ledger.write_json(manifest,dict(schema='cad-harness.inputs.v4c',profile='c-s1',
            evidence_mode='independent_dev',assets={'colored':dict(kind='image',role='checker',
                path=image.name,sha256=self.ledger.file_sha(image),bytes=image.stat().st_size)}))
        recipe=self.ledger.read_json(self.root/'rounding-recipe.json')
        recipe['foreground']['threshold']=75;recipe['rounding']=dict(allowed=False)
        contour=self.contours.prepare_contour(manifest,'colored',recipe,self.work/'colored-contour')
        packet=dict(schema='cad-harness.prepared.v4c',profile='c-s1',
                    source_manifest_sha256=self.ledger.file_sha(manifest),assets={'colored':contour})
        plan=dict(self.plan,contour_id='colored',width_mm=8)
        body=self.compiler.build_plan(self.doc,plan,manifest,packet);self.doc.recompute()
        criterion=dict(id='color',metric='image_iou',leg='image_to_contour',contour_id='colored',
            mask_asset_id='colored',registration=dict(origin_mm=[0,7.5],pixel_size_mm=[.25,.25],y_direction=-1),
            foreground=dict(channel='luminance',threshold=75,polarity='dark',alpha_min=255),
            minimum_iou=.999,curve_tolerance_mm=.0001)
        self.assertStatus(self.judges.judge(plan,manifest,packet,body,self.card_for(criterion)),'PASS')
        changed=copy.deepcopy(criterion);changed['foreground']['threshold']=76
        result=self.judges.judge(plan,manifest,packet,body,self.card_for(changed))
        self.assertStatus(result,'FAIL')
        self.assertEqual(result['checks'][0]['evidence']['reason'],'decoded_image_or_mask_commitment_mismatch')

    def test_c2_actual_preprocessing_permitted_rounding_vs_unsmoothed_radius(self):
        recipe=self.ledger.read_json(self.root/'rounding-recipe.json')
        rounded=self.contours.prepare_contour(self.manifest,'rectangle_mask',recipe,self.work/'rounded')
        if 'assets' in rounded:
            rounded=rounded['assets']['rectangle_mask']
        actual=self.judges.minimum_radius(rounded,1e-6)
        self.assertAlmostEqual(actual['minimum_mm'],3,places=6)
        expected_area=34*22-(4-math.pi)*9
        geometry,error=self.judges.planar_geometry(rounded,.0001)
        self.assertLess(abs(geometry.area-expected_area),.01)
        raw_recipe=copy.deepcopy(recipe)
        raw_recipe['rounding']={'allowed':False}
        raw=self.contours.prepare_contour(self.manifest,'rectangle_mask',raw_recipe,self.work/'unsmoothed')
        if 'assets' in raw:
            raw=raw['assets']['rectangle_mask']
        self.assertEqual(self.judges.minimum_radius(raw,1e-6)['minimum_mm'],0)
        # Both legs are against originals/actual output, not a self-comparison.
        packet=copy.deepcopy(self.packet);packet['assets']['rectangle_mask']=rounded
        plan=copy.deepcopy(self.plan);plan['contour_id']='rectangle_mask'
        body=self.build(plan,packet)
        criteria=[]
        for leg in ('image_to_contour','contour_to_output'):
            c=dict(id=leg,metric='boundary_hausdorff',leg=leg,contour_id='rectangle_mask',
                   maximum_mm=1.3 if leg=='image_to_contour' else .02,
                   sampling_step_mm=.02,curve_tolerance_mm=.0001)
            if leg=='image_to_contour':
                c.update(mask_asset_id='rectangle_mask',registration=dict(origin_mm=[0,30],pixel_size_mm=[.25,.25],y_direction=-1),
                         foreground=dict(channel='luminance',threshold=127,polarity='dark',alpha_min=255))
            else:c['projection_z_mm']=2
            criteria.append(c)
        self.assertStatus(self.run_judge(body,self.card_for(*criteria),plan=plan,packet=packet),'PASS')

    def test_c2_actual_hole_topology_and_preprocessing_hard_negatives(self):
        recipe=self.ledger.read_json(self.root/'rounding-recipe.json')
        hole=self.contours.prepare_contour(self.manifest,'wide_hole_mask',recipe,self.work/'wide-hole')
        geometry,error=self.judges.planar_geometry(hole,.0001)
        self.assertEqual(self.judges._topology(geometry),dict(components=1,holes=1))
        self.assertLess(abs(geometry.area-648),.02)
        self.assertAlmostEqual(self.judges.minimum_radius(hole,1e-6)['minimum_mm'],3,places=6)
        for asset in ('island_mask','diagonal_mask','nonopaque_mask'):
            with self.subTest(asset=asset):
                with self.assertRaises(ValueError):
                    self.contours.prepare_contour(self.manifest,asset,recipe,self.work/asset)
        too_large=copy.deepcopy(recipe);too_large['rounding']['radius_mm']=20
        with self.assertRaises(ValueError):
            self.contours.prepare_contour(self.manifest,'rectangle_mask',too_large,self.work/'unfit-radius')
        no_budget=copy.deepcopy(recipe);no_budget['limits']['max_deviation_mm']=0
        with self.assertRaises(ValueError):
            self.contours.prepare_contour(self.manifest,'rectangle_mask',no_budget,self.work/'no-deviation')
        missing=copy.deepcopy(recipe);missing.pop('foreground')
        with self.assertRaises(ValueError):
            self.contours.prepare_contour(self.manifest,'rectangle_mask',missing,self.work/'missing-policy')

    def test_c2_native_bounds_volume_dimension_and_missing_acceptance(self):
        body=self.build();criteria=[c for c in self.card['criteria'] if c['metric'] in ('bounds','volume','unchanged_dimension')]
        card=self.card_for(*criteria)
        self.assertStatus(self.run_judge(body,card),'PASS')
        self.doc.getObject('ContourExtrude').Thickness=5;self.doc.recompute()
        self.assertStatus(self.run_judge(body,card),'FAIL')
        missing=self.card_for(dict(id='no-volume-tolerance',metric='volume',expected_mm3=body.Shape.Volume))
        self.assertStatus(self.run_judge(body,missing),'UNVERIFIED')
        missing.pop('linear_tolerance_mm')
        self.assertStatus(self.run_judge(body,missing),'UNVERIFIED')
        compound=self.Part.makeCompound([self.Part.makeBox(1,1,1),self.Part.makeBox(1,1,1,self.App.Vector(3,0,0))])
        self.assertStatus(self.run_judge(compound,self.card_for(dict(id='solid',metric='solid_valid'))),'FAIL')

    def engraving_plan(self):
        p=copy.deepcopy(self.plan)
        e=self.expected['engraving']
        p['engravings']=[dict(font_id='dev_font',text=e['text'],height_mm=e['height_mm'],depth_mm=e['depth_mm'],
            origin_mm=e['origin_mm'],rotation_axis=e['rotation_axis'],rotation_deg=e['rotation_deg'])]
        return p

    def test_c3_actual_recess_identity_depth_and_negative_claim(self):
        plan=self.engraving_plan();body=self.build(plan)
        # Independent glyph topology: B and 8 have two counters each.
        # At half recess depth: stock outline + 2 ink outlines + 4 counters.
        z=plan['engravings'][0]['origin_mm'][2]-plan['engravings'][0]['depth_mm']/2
        self.assertEqual(len(body.Shape.slice(self.App.Vector(0,0,1),z)),7)
        card=self.card_for(dict(id='glyph',metric='engraving',index=0,minimum_removed_mm3=1,depth_tolerance_mm=.01))
        result=self.run_judge(body,card,plan=plan)
        self.assertStatus(result,'PASS')
        self.assertGreater(result['checks'][0]['measured']['removed_mm3'],1)
        false_plan=copy.deepcopy(plan);false_plan['engravings'][0]['text']='A0'
        self.assertStatus(self.run_judge(body,card,plan=false_plan),'FAIL')
        deeper=copy.deepcopy(plan);deeper['engravings'][0]['depth_mm']=1.2
        self.assertStatus(self.run_judge(body,card,plan=deeper),'FAIL')
        baseline=self.doc.getObject('Engraving0').Base.Shape
        through=baseline.cut(self.Part.makeBox(20,12,4,self.App.Vector(10,8,0)))
        self.assertTrue(through.isValid())
        self.assertStatus(self.run_judge(through,card,plan=plan,baseline_shape=baseline),'FAIL')

    def test_c3_operative_width_thickness_text_height_depth_after_fcstd_reopen(self):
        plan=self.engraving_plan();body=self.build(plan)
        saved=self.work/'engraved.FCStd';self.doc.saveAs(str(saved))
        reopened=self.App.openDocument(str(saved));self.addCleanup(self.close_document,reopened.Name)
        base=reopened.getObject('ContourExtrude');feature=reopened.getObject('Engraving0')
        original=feature.Shape.Volume
        for name,value in (('Text','A0'),('Height',4.5),('Depth',.9)):
            before=feature.Shape.Volume;setattr(feature,name,value);reopened.recompute()
            self.assertTrue(feature.Shape.isValid());self.assertEqual(len(feature.Shape.Solids),1)
            self.assertNotAlmostEqual(feature.Shape.Volume,before,places=5,msg=name)
        self.assertNotAlmostEqual(feature.Shape.Volume,original,places=5)
        base.Width=36;base.Thickness=5;feature.Origin=self.App.Vector(12,10,5);reopened.recompute()
        self.assertAlmostEqual(base.Shape.BoundBox.XLength,36,places=5)
        self.assertAlmostEqual(base.Shape.BoundBox.ZLength,5,places=5)
        step=self.work/'edited.step';feature.Shape.exportStep(str(step))
        imported=self.Part.Shape();imported.read(str(step))
        self.assertTrue(imported.isValid());self.assertEqual(len(imported.Solids),1)
        self.assertAlmostEqual(imported.Volume,feature.Shape.Volume,places=5)
    def test_c3_unsupported_glyph_cannot_retain_stale_valid_shape(self):
        body=self.build(self.engraving_plan())
        feature=self.doc.getObject('Engraving0')
        self.assertFalse(feature.Shape.isNull())
        feature.Text='Ω'
        self.doc.recompute()
        self.assertTrue(feature.Shape.isNull(),'failed glyph recompute must clear prior geometry')
        text=_module('cad_verify_v4_text')
        with self.assertRaises(ValueError):
            text.text_outline(self.manifest,'dev_font','Ω',5)


    def test_c3_nonhorizontal_declared_axis_angle_recess(self):
        plan=copy.deepcopy(self.plan);plan['thickness_mm']=12
        # On the lower Y side, glyph XY is mapped to global XZ, local -Z into +Y.
        plan['engravings']=[dict(font_id='dev_font',text='B8',height_mm=4,depth_mm=.6,
            origin_mm=[12,4,3],rotation_axis=[1,0,0],rotation_deg=90)]
        body=self.build(plan)
        card=self.card_for(dict(id='vertical-glyph',metric='engraving',index=0,minimum_removed_mm3=.5,depth_tolerance_mm=.01))
        self.assertStatus(self.run_judge(body,card,plan=plan),'PASS')
    def test_consumer_fake_model_to_real_native_compile_and_independent_reimport(self):
        import json
        supervisor=_module('cad_verify_v4_s1')
        request=self.work/'request.txt'
        request.write_text('Extrude the declared independent analytic contour to width 34 mm and thickness 4 mm.',encoding='utf-8')
        observed=[]
        def fake_model(request_text,runtime_data,*,purpose,timeout):
            observed.append((purpose,runtime_data))
            self.assertGreater(timeout,0)
            # Acceptance is CLI-only, never input to this callback.
            def contains_acceptance(value):
                if isinstance(value,dict):
                    return any(k in ('criteria','linear_tolerance_mm','maximum_uncovered_mm2') or contains_acceptance(v) for k,v in value.items())
                return isinstance(value,list) and any(contains_acceptance(v) for v in value)
            self.assertFalse(contains_acceptance(runtime_data))
            return json.dumps(self.plan,allow_nan=False)
        run=self.work/'consumer'
        summary,code=supervisor.request(request,self.root/'card.json',run,
            manifest_path=self.manifest,prepared_path=self.root/'prepared.json',model=fake_model)
        self.assertEqual(code,0,summary)
        self.assertEqual(summary['status'],'PASS',summary)
        self.assertEqual(summary['evidence_mode'],'unit_mock')
        self.assertEqual(summary['physical_model_attempts'],0)
        self.assertEqual(summary['live_calls'],0)
        self.assertTrue(observed)
        self.assertEqual(summary['result']['verification']['status'],'PASS')
        imported=self.Part.Shape();imported.read(str(run/'candidate-1/model.step'))
        expected=(34*22-(4-math.pi)*9)*4
        self.assertAlmostEqual(imported.Volume,expected,places=5)
        self.assertTrue(imported.isValid());self.assertEqual(len(imported.Solids),1)
        card=self.card_for(dict(id='volume',metric='volume',expected_mm3=expected,tolerance_mm3=.0001),
                           dict(id='bounds',metric='bounds',expected_mm=[4,38,4,26,0,4]))
        self.assertStatus(self.run_judge(imported,card),'PASS')
        self.assertTrue((run/'candidate-1/model.FCStd').is_file())
        self.assertTrue((run/'candidate-1-verify/verify-result.json').is_file())


if __name__=='__main__':
    unittest.main()
