"""Independent bare-shape/context controls; no constructor or live calls.

Native cases require CAD_VERIFY_ARTIFACT_NATIVE=1 under pinned FreeCAD Python.
Host admission cases never launch CAD. All source/geometry is temporary dev data.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from tools import cad_verify_v4_artifact_judges as adapter
from tools import cad_verify_v4_inputs as inputs, cad_verify_v4_ledger as ledger

NATIVE = (os.environ.get('CAD_VERIFY_ARTIFACT_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
REASON = 'set CAD_VERIFY_ARTIFACT_NATIVE=1 under pinned FreeCAD Python; no discovery launch'


def card_for(profile, *criteria):
    card = dict(schema='cad-harness.judge-card.v4c', profile=profile,
                source='independent_dev', criteria=list(criteria))
    card['linear_tolerance_mm' if profile == 'c-s1' else 'numerical_uncertainty_mm'] = 1e-5
    return card


class ContextFixtures:
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cad-neutral-independent-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifest = self.root / 'manifest.json'
        self.prepared_path = self.root / 'prepared.json'
        self.card_path = self.root / 'card.json'

    def record(self, path, kind, role, **extra):
        return dict(kind=kind, role=role, path=path.name, sha256=ledger.file_sha(path),
                    bytes=path.stat().st_size, **extra)

    def save_inputs(self, profile, assets):
        ledger.write_json(self.manifest, dict(schema='cad-harness.inputs.v4c', profile=profile,
                          evidence_mode='independent_dev', assets=assets))

    def measurement_packet(self, profile):
        manifest = inputs.load_manifest(self.manifest)
        steps = [key for key, record in manifest['assets'].items() if record['kind'] == 'step']
        if steps and hasattr(self, 'Part'):
            recipe = dict(schema='cad-harness.step-recipe.v4c', profile=profile,
                          source_axes=['X','Y','Z'],source_units='mm',signature_precision_mm=1e-6)
            return inputs.inspect_step(self.manifest, steps[0], recipe, self.prepared_path)
        packet = dict(schema='cad-harness.prepared.v4c', profile=profile,
                      source_manifest_sha256=ledger.file_sha(self.manifest), assets={})
        if steps:
            # Schema/provenance admission only; these host bytes are never native
            # evidence. Native controls above use actual inspect_step instead.
            asset_id = steps[0]
            digest = manifest['assets'][asset_id]['sha256']
            manifest_digest = packet['source_manifest_sha256']
            packet['assets'][asset_id] = dict(schema='cad-harness.step-facts.v4c',profile=profile,
                asset_id=asset_id,source_sha256=digest,units='mm',bounds_mm=[0,1,0,1,0,0],
                topology=dict(solids=0,shells=0,faces=1,edges=4),
                frame=dict(source_axes=['X','Y','Z'],source_units='mm',import_units='mm',
                    axis_transform='identity',thickness_mm=None,
                    thickness_reason='requires_explicit_face_pair_not_bbox'),
                faces=[dict(id='Face1',signature='1'*64,ambiguous=False,surface_type='Plane',
                    area_mm2=1.,center_mm=[.5,.5,0],bounds_mm=[0,1,0,1,0,0],
                    normal=[0,0,1],normal_kind='constant',normal_reason=None)],
                coverage=dict(complete=True,missing_reasons=[]),recipe_sha256='2'*64,
                provenance=dict(manifest_sha256_before=manifest_digest,manifest_sha256_after=manifest_digest,
                    asset_sha256_before=digest,asset_sha256_after=digest,
                    importer='FreeCAD.Part.Shape.read',freecad_version='host-admission-only'))
        return packet

    def context(self, family, prepared, card, reference=None, contour=None, engravings=None):
        self._context_sequence = getattr(self, '_context_sequence', 0) + 1
        self.prepared_path = self.root / ('bound-prepared-%d.json' % self._context_sequence)
        self.card_path = self.root / ('bound-card-%d.json' % self._context_sequence)
        ledger.write_json(self.prepared_path, prepared)
        ledger.write_json(self.card_path, card)
        return dict(schema='cad-harness.artifact-context.v4', profile=card['profile'], family=family,
                    manifest_sha256=ledger.file_sha(self.manifest),
                    prepared_sha256=ledger.file_sha(self.prepared_path), card_sha256=ledger.file_sha(self.card_path),
                    reference=reference, contour=contour, engravings=engravings or [])

    def admit(self, context):
        return adapter.validate_context(context, self.manifest, self.prepared_path, self.card_path)


class ContextAdmission(ContextFixtures, unittest.TestCase):
    def setUp(self):
        super().setUp()
        source = self.root / 'checker.step'
        source.write_bytes(b'ISO-10303-21;\n/* host admission fixture, no native geometry */\nEND-ISO-10303-21;')
        self.save_inputs('c-s1', {'checker': self.record(source, 'step', 'checker')})
        self.prepared = self.measurement_packet('c-s1')
        self.card = card_for('c-s1', dict(id='solid', metric='solid_valid'))
        self.value = self.context('C1', self.prepared, self.card)

    def test_strict_measurement_data_and_copy(self):
        admitted = self.admit(self.value)
        admitted['family'] = 'C2'
        self.assertEqual(self.value['family'], 'C1')
        for key, value in (('plan', {}), ('constructor_module', 'anything'), ('PoleOffsets', []),
                           ('feature_name', 'anything'), ('fit_tolerance_mm', .1)):
            bad = dict(self.value, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.admit(bad)
        for key, value in (('profile', 'c-s2'), ('family', 'C5'), ('prepared_sha256', '0'*64),
                           ('card_sha256', '0'*64), ('manifest_sha256', '0'*64)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.admit(dict(self.value, **{key: value}))

    def test_changed_bound_file_and_in_memory_measurements_rejected(self):
        admitted = self.admit(self.value)
        bad_card = copy.deepcopy(self.card)
        bad_card['criteria'][0]['id'] = 'different'
        with self.assertRaisesRegex(ValueError, 'supplied_prepared_or_card'):
            adapter.judge(admitted, self.manifest, self.prepared, object(), bad_card)
        admitted['engravings'].append({})
        with self.assertRaisesRegex(ValueError, 'frozen_measurements'):
            adapter.judge(admitted, self.manifest, self.prepared, object(), self.card)
        admitted = self.admit(self.value)
        self.card_path.write_text(json.dumps(bad_card), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'card_sha256'):
            adapter.judge(admitted, self.manifest, self.prepared, object(), self.card)

    def test_missing_card_measurements_and_bad_source_bytes_rejected(self):
        card = card_for('c-s1', dict(id='glyph', metric='engraving', index=0,
                                   minimum_removed_mm3=1., depth_tolerance_mm=.01))
        value = self.context('C3', self.prepared, card)
        with self.assertRaisesRegex(ValueError, 'engraving_missing'):
            self.admit(value)
        value = self.context('C1', self.prepared, self.card)
        (self.root / 'checker.step').write_bytes(b'changed source')
        with self.assertRaises(ValueError):
            self.admit(value)


@unittest.skipUnless(NATIVE, REASON)
class BareGeometry(ContextFixtures, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App, cls.Part = App, Part

    def source(self, profile, shape):
        path = self.root / 'source.step'
        shape.exportStep(str(path))
        self.save_inputs(profile, {'source': self.record(path, 'step', 'reference')})
        recipe = dict(schema='cad-harness.step-recipe.v4c', profile=profile,
                      source_axes=['X', 'Y', 'Z'], source_units='mm', signature_precision_mm=1e-6)
        prepared = inputs.inspect_step(self.manifest, 'source', recipe, self.prepared_path)
        reference = dict(asset_id='source', source_sha256=ledger.file_sha(path))
        actual = self.Part.Shape()
        actual.read(str(path))
        return prepared, reference, actual

    def assert_shape_status(self, context, prepared, card, shape, expected):
        admitted = self.admit(context)
        result = adapter.judge(admitted, self.manifest, prepared, shape, card)
        self.assertEqual(result['status'], expected, result)
        self.assertEqual([row['id'] for row in result['checks']], [row['id'] for row in card['criteria']])
        return result

    def test_c1_ordinary_sketch_pad_and_step_same_card(self):
        import Sketcher
        source = self.root / 'checker.step'
        self.Part.makeBox(1, 1, 1).exportStep(str(source))
        self.save_inputs('c-s1', {'checker': self.record(source, 'step', 'checker')})
        prepared = self.measurement_packet('c-s1')
        card = card_for('c-s1', dict(id='solid', metric='solid_valid'),
                        dict(id='bounds', metric='bounds', expected_mm=[0,12,0,8,0,3]),
                        dict(id='volume', metric='volume', expected_mm3=288., tolerance_mm3=.001))
        context = self.context('C1', prepared, card)
        doc = self.App.newDocument('IndependentOrdinary')
        try:
            body = doc.addObject('PartDesign::Body', 'BareBody')
            sketch = body.newObject('Sketcher::SketchObject', 'Rectangle')
            points = [(0,0), (12,0), (12,8), (0,8)]
            for a,b in zip(points, points[1:]+points[:1]):
                sketch.addGeometry(self.Part.LineSegment(self.App.Vector(*a,0), self.App.Vector(*b,0)), False)
            pad = body.newObject('PartDesign::Pad', 'Pad')
            pad.Profile, pad.Length = sketch, 3
            doc.recompute()
            fcstd = self.root / 'ordinary.FCStd'
            doc.saveAs(str(fcstd))
        finally:
            self.App.closeDocument(doc.Name)
        reopened = self.App.openDocument(str(fcstd))
        try:
            body = reopened.getObject('BareBody')
            self.assert_shape_status(context, prepared, card, body, 'PASS')
            step = self.root / 'ordinary.step'
            body.Shape.exportStep(str(step))
            imported = self.Part.Shape()
            imported.read(str(step))
            self.assert_shape_status(context, prepared, card, imported, 'PASS')
            self.assert_shape_status(context, prepared, card, self.Part.makeBox(12,8,2), 'FAIL')
        finally:
            self.App.closeDocument(reopened.Name)

    def test_c2_fixed_registration_rejects_translation_scale_and_missing_hole(self):
        from PIL import Image
        image = self.root / 'mask.png'
        mask = Image.new('RGB', (12,8), 'black')
        mask.paste('white',(4,2,8,6))
        mask.save(image)
        loops = []
        for role, points in [('outer', [[0,0],[12,0],[12,8],[0,8]]),
                             ('hole', [[4,2],[4,6],[8,6],[8,2]])]:
            loops.append(dict(role=role, segments=[dict(kind='line',p0=a,p1=b)
                         for a,b in zip(points, points[1:]+points[:1])]))
        original = dict(schema='cad-harness.contour-source.v4c', profile='c-s1', units='mm',
                        bounds_mm=[0,12,0,8], nominal_width_mm=12., loops=loops,
                        source_image_asset_id='mask')
        contour_path = self.root / 'outline.json'
        ledger.write_json(contour_path, original)
        self.save_inputs('c-s1', {'outline': self.record(contour_path,'contour','contour'),
                                'mask': self.record(image,'image','checker')})
        record = dict(schema='cad-harness.contour.v4c', profile='c-s1', asset_id='outline',
                      source_sha256=ledger.file_sha(contour_path), source_image_asset_id='mask',
                      source_image_sha256=ledger.file_sha(image), units='mm', bounds_mm=[0,12,0,8],
                      nominal_width_mm=12., loops=loops, topology=dict(components=1,holes=1),
                      pixel_to_mm=dict(scale_mm_per_pixel=1.,origin_mm=[0,0],image_height_pixels=8,
                          y_axis='up',pixel_convention='closed unit cells; centers at (col+0.5,row+0.5)'),
                      provenance=dict(kind='independent_analytic_source'))
        prepared = self.measurement_packet('c-s1')
        prepared['assets']['outline'] = record
        card = card_for('c-s1', dict(id='contour', metric='boundary_hausdorff', leg='contour_to_output',
                    contour_id='outline', projection_z_mm=1.5, maximum_mm=.03,
                    sampling_step_mm=.01, curve_tolerance_mm=.0001))
        registration = dict(contour_id='outline', scale=1., origin_mm=[2,3,0], thickness_mm=3.)
        context = self.context('C2', prepared, card, contour=registration)
        outer = self.Part.makeBox(12,8,3,self.App.Vector(2,3,0))
        good = outer.cut(self.Part.makeBox(4,4,3,self.App.Vector(6,5,0)))
        self.assert_shape_status(context, prepared, card, good, 'PASS')
        shifted = good.copy(); shifted.translate(self.App.Vector(.3,0,0))
        self.assert_shape_status(context, prepared, card, shifted, 'FAIL')
        scaled = good.copy(); scaled.scale(1.2)
        self.assert_shape_status(context, prepared, card, scaled, 'FAIL')
        self.assert_shape_status(context, prepared, card, outer, 'FAIL')
        wrong = copy.deepcopy(context); wrong['contour']['origin_mm'][0] += .2
        self.assert_shape_status(wrong, prepared, card, good, 'FAIL')
        source_card = card_for('c-s1', dict(id='source_fidelity',metric='image_iou',leg='image_to_contour',
            contour_id='outline',mask_asset_id='mask',registration=dict(origin_mm=[0,8],pixel_size_mm=[1,1],y_direction=-1),
            foreground=dict(channel='luminance',polarity='dark',threshold=127,alpha_min=255),minimum_iou=.82,curve_tolerance_mm=.0001))
        source_context = self.context('C2',prepared,source_card)
        self.assert_shape_status(source_context,prepared,source_card,self.Part.makeBox(1,1,1),'PASS')

    def make_test_font(self):
        from fontTools.fontBuilder import FontBuilder
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        font = FontBuilder(1000, isTTF=True)
        font.setupGlyphOrder(['.notdef','O'])
        font.setupCharacterMap({ord('O'):'O'})
        pen = TTGlyphPen(None)
        for points in ([(0,0),(1000,0),(1000,1000),(0,1000)],
                       [(250,250),(250,750),(750,750),(750,250)]):
            pen.moveTo(points[0])
            for point in points[1:]: pen.lineTo(point)
            pen.closePath()
        font.setupGlyf({'.notdef':TTGlyphPen(None).glyph(),'O':pen.glyph()})
        font.setupHorizontalMetrics({'.notdef':(1000,0),'O':(1000,0)})
        font.setupHorizontalHeader(ascent=1000,descent=0)
        font.setupNameTable({'familyName':'IndependentSquareInk','styleName':'Regular',
                            'uniqueFontIdentifier':'IndependentSquareInk','fullName':'IndependentSquareInk',
                            'psName':'IndependentSquareInk'})
        font.setupOS2(sTypoAscender=1000,sTypoDescender=0,usWinAscent=1000,usWinDescent=0)
        font.setupPost(); font.setupMaxp()
        path = self.root / 'own-square.ttf'; font.save(str(path))
        license_path = self.root / 'own-license.txt'
        license_path.write_text('Independent test font authored here; unrestricted test use.',encoding='utf-8')
        return path, license_path

    def test_c3_registered_glyph_baseline_depth_and_source_controls(self):
        baseline = self.Part.makeBox(12,8,3)
        baseline_path = self.root / 'baseline.step'; baseline.exportStep(str(baseline_path))
        wrong_path = self.root / 'wrong.step'
        self.Part.makeBox(12,8,3,self.App.Vector(30,0,0)).exportStep(str(wrong_path))
        uncertified_path = self.root / 'wire-baseline.step'
        self.Part.makeLine(self.App.Vector(0,0,3),self.App.Vector(12,0,3)).exportStep(str(uncertified_path))
        font, license_path = self.make_test_font()
        self.save_inputs('c-s1', {'baseline':self.record(baseline_path,'step','checker'),
            'wrong':self.record(wrong_path,'step','checker'),
            'wire':self.record(uncertified_path,'step','checker'),
            'font':self.record(font,'font','font',license_asset_id='license',glyphs='O'),
            'license':self.record(license_path,'license','license')})
        prepared = self.measurement_packet('c-s1')
        engraving = dict(font_id='font',text='O',height_mm=4.,depth_mm=.5,origin_mm=[2,2,3],
                         rotation_axis=[0,0,1],rotation_deg=0.,baseline_asset_id='baseline')
        card = card_for('c-s1',dict(id='glyph',metric='engraving',index=0,
                                  minimum_removed_mm3=5.9,depth_tolerance_mm=.02))
        context = self.context('C3',prepared,card,engravings=[engraving])
        def recess(depth):
            outer = self.Part.makeBox(4,4,depth,self.App.Vector(2,2,3-depth))
            inner = self.Part.makeBox(2,2,depth,self.App.Vector(3,3,3-depth))
            return baseline.cut(outer.cut(inner))
        good = recess(.5)
        self.assert_shape_status(context,prepared,card,good,'PASS')
        self.assert_shape_status(context,prepared,card,baseline,'FAIL')
        self.assert_shape_status(context,prepared,card,recess(.9),'FAIL')
        filled_counter = baseline.cut(self.Part.makeBox(4,4,.5,self.App.Vector(2,2,2.5)))
        self.assert_shape_status(context,prepared,card,filled_counter,'FAIL')
        wrong = copy.deepcopy(context); wrong['engravings'][0]['baseline_asset_id']='wrong'
        self.assert_shape_status(wrong,prepared,card,good,'FAIL')
        wrong = copy.deepcopy(context); wrong['engravings'][0]['origin_mm'][0]=8
        self.assert_shape_status(wrong,prepared,card,good,'FAIL')
        uncertified = copy.deepcopy(context); uncertified['engravings'][0]['baseline_asset_id']='wire'
        self.assert_shape_status(uncertified,prepared,card,good,'UNVERIFIED')
        missing = copy.deepcopy(context); missing['engravings'][0]['baseline_asset_id']='absent'
        with self.assertRaises(ValueError): self.admit(missing)
        changed = copy.deepcopy(context); changed['engravings'][0]['text']='Q'
        with self.assertRaisesRegex(ValueError,'glyph_coverage'): self.admit(changed)

    def test_c4_source_thickness_and_wrong_ordinary_output(self):
        prepared, reference, original = self.source('c-s2',self.Part.makeBox(12,8,4))
        faces = prepared['assets']['source']['faces']
        bottom = min(faces,key=lambda f:f['center_mm'][2])['id']
        top = max(faces,key=lambda f:f['center_mm'][2])['id']
        criterion = dict(id='wall',metric='thickness_distribution',scope='continuous',
            convention='directed_material_chord',direction=[0,0,1],
            domain=dict(origin_mm=[1,1,0],u=[1,0,0],v=[0,1,0],size_mm=[10,6]),
            opposed_sets=dict(a=dict(source_face_ids=[bottom],output_region_mm=[0,12,0,8,-.1,.1]),
                              b=dict(source_face_ids=[top],output_region_mm=[0,12,0,8,4.4,4.6])),
            expected_range_mm=[4.5,4.5],tolerance_mm=.001,samples=[3,3],ray_length_mm=30.)
        card = card_for('c-s2',criterion)
        context = self.context('C4',prepared,card,reference=reference)
        self.assert_shape_status(context,prepared,card,self.Part.makeBox(12,8,4.5),'PASS')
        # The entire wrong slab is selected, making wrong thickness certifiably FAIL.
        wrong_card = copy.deepcopy(card)
        wrong_card['criteria'][0]['opposed_sets']['b']['output_region_mm'][4:] = [4.9,5.1]
        wrong_context = self.context('C4',prepared,wrong_card,reference=reference)
        self.assert_shape_status(wrong_context,prepared,wrong_card,self.Part.makeBox(12,8,5),'FAIL')
        wrong_source = copy.deepcopy(reference); wrong_source['source_sha256']='0'*64
        value = self.context('C4',prepared,card,reference=wrong_source)
        with self.assertRaisesRegex(ValueError,'immutable_reference'): self.admit(value)

    def test_c5_selected_polynomial_atlas_and_uncertified_plane(self):
        surface = self.Part.BSplineSurface()
        poles = [[self.App.Vector(12*i/3,8*j/3,3) for j in range(4)] for i in range(4)]
        surface.buildFromPolesMultsKnots(poles,[4,4],[4,4],[0.,1.],[0.,1.],False,False,3,3)
        source_shape = surface.toShape().extrude(self.App.Vector(0,0,-3))
        prepared, reference, actual = self.source('c-s3',source_shape)
        selected = max(prepared['assets']['source']['faces'],key=lambda f:f['center_mm'][2])
        cell = {key:selected[key] for key in ('signature','adjacent_face_ids')}
        cell.update(face_id=selected['id'],swap_uv=False,reverse_u=False,reverse_v=False)
        reference['grid']=[[cell]]
        mapping = dict(bounds_mm=selected['bounds_mm'],domain_uv='native_full',chart_uv=[0.,1.,0.,1.],
                       swap_uv=False,reverse_u=False,reverse_v=False)
        card = card_for('c-s3',dict(id='surface',metric='surface_deviation',maximum_mm=.02,
            output_region_mm=[0,12,0,8,2.9,3.1],selection_tolerance_mm=1e-5,
            output_patches=[mapping],resources=dict(max_depth=12,max_cells=12000)))
        context = self.context('C5',prepared,card,reference=reference)
        self.assert_shape_status(context,prepared,card,actual,'PASS')
        plane = self.Part.makeBox(12,8,3)
        self.assert_shape_status(context,prepared,card,plane,'UNVERIFIED')
        shifted = actual.copy(); shifted.translate(self.App.Vector(0,0,.3))
        result = adapter.judge(self.admit(context),self.manifest,prepared,shifted,card)
        self.assertNotEqual(result['status'],'PASS',result)
        bad = copy.deepcopy(context); bad['reference']['grid'][0][0]['signature']='0'*64
        with self.assertRaisesRegex(ValueError,'atlas_source_selector'): self.admit(bad)
        bad = copy.deepcopy(context); bad['reference']['grid'][0].append(copy.deepcopy(cell))
        with self.assertRaisesRegex(ValueError,'duplicate_atlas_face'): self.admit(bad)
        bad = copy.deepcopy(context); bad['reference']['grid'][0][0]['adjacent_face_ids']=[]
        with self.assertRaisesRegex(ValueError,'atlas_source_selector'): self.admit(bad)


if __name__ == '__main__':
    unittest.main()
