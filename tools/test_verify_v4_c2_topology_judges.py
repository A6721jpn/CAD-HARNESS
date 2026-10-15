"""Independent ORIGINAL-mask C-R8v3 consumer controls; no fitter/helper imports.

Host: python -B -m unittest tools.test_verify_v4_c2_topology_judges.C2TopologyDeclarationHostTests tools.test_verify_v4_c2_topology_judges.C2TopologyJudgesHostTests
Native: set CAD_VERIFY_C2_TOPOLOGY_NATIVE=1 under pinned Python 3.11.14 /
FreeCAD 1.1.4, then python -B -m unittest tools.test_verify_v4_c2_topology_judges.C2TopologyJudgesNativeTests
All images and native shapes are independently authored temporary DEV data.
"""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

from tools import cad_verify_v4_judges as judges
from tools import cad_verify_v4_ledger as ledger

NUMERIC = all(importlib.util.find_spec(name) is not None for name in ('numpy', 'PIL', 'shapely'))
NATIVE = (NUMERIC and os.environ.get('CAD_VERIFY_C2_TOPOLOGY_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
CONNECTIVITY = dict(foreground=4, background=8, pinch='remove_locally')


def polygon_loop(points, role='outer'):
    points = [list(point) for point in points]
    return dict(role=role, segments=[dict(kind='line', p0=point, p1=points[(i+1) % len(points)])
                                    for i, point in enumerate(points)])


def rectangle(x0, y0, x1, y1, role='outer'):
    return polygon_loop([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], role)


def circle(x, y, radius):
    points = [[x+radius*math.cos(i*math.pi/4), y+radius*math.sin(i*math.pi/4)]
              for i in range(8)]
    return dict(role='outer', segments=[dict(kind='arc', p0=points[2*i],
                pm=points[2*i+1], p1=points[(2*i+2) % 8]) for i in range(4)])


def region_loops(region, role='outer'):
    pieces = list(region.geoms) if hasattr(region, 'geoms') else [region]
    loops = []
    for piece in pieces:
        loops.append(polygon_loop(list(piece.exterior.coords)[:-1], role))
        loops.extend(polygon_loop(list(ring.coords)[:-1], 'hole') for ring in piece.interiors)
    return loops


def fill(mask, x, y, width, height, value=True):
    # Independently authored coordinates are original integer cell vertices, y-up.
    mask[mask.shape[0]-y-height:mask.shape[0]-y, x:x+width] = value


def contact(x, y, labels):
    return dict(vertex_pixels=[x, y], incident_components=labels, clearance_mm_lower=1e6)


class C2TopologyDeclarationHostTests(unittest.TestCase):
    def test_only_explicit_v2_connectivity_activates_digital_oracle(self):
        value = dict(recipe=dict(curve_fit=dict(method='source_bounded_biarc_v2'),
                                 topology=dict(connectivity=copy.deepcopy(CONNECTIVITY))))
        self.assertTrue(judges._digital_v2(value))
        for connectivity in (None, {}, dict(foreground=8, background=4, pinch='remove_locally'),
                             dict(CONNECTIVITY, extra=True), dict(CONNECTIVITY, pinch='bridge'),
                             dict(CONNECTIVITY, foreground=4.), dict(CONNECTIVITY, background=8.)):
            bad = copy.deepcopy(value)
            bad['recipe']['topology']['connectivity'] = connectivity
            with self.subTest(connectivity=connectivity), self.assertRaisesRegex(ValueError, 'v2_connectivity'):
                judges._digital_v2(bad)
        for method in ('periodic_cubic_biarc_v1', 'other', None):
            historical = copy.deepcopy(value)
            historical['recipe']['curve_fit']['method'] = method
            self.assertFalse(judges._digital_v2(historical))
        self.assertFalse(judges._digital_v2(dict(provenance=dict(kind='independent_analytic_source'))))

    def test_positive_overlap_assignment_is_complete_weighted_and_deterministic(self):
        self.assertEqual(judges._positive_overlap_matching([[100., 1.], [2., .1]]), [0, 1])
        self.assertEqual(judges._positive_overlap_matching([[0., 1.], [1., 0.]]), [1, 0])
        self.assertEqual(judges._positive_overlap_matching([[1., 1.], [1., 1.]]), [0, 1])
        self.assertIsNone(judges._positive_overlap_matching([[0., 1.], [0., 2.]]))
        self.assertEqual(judges._positive_overlap_matching([]), [])


class _IndependentFixtures:
    def setUp(self):
        import numpy as np
        from PIL import Image
        from shapely.geometry import box
        self.np, self.Image, self.box = np, Image, box
        temporary = tempfile.TemporaryDirectory(prefix='cad-c2-topology-oracle-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.sequence = 0

    def fixture(self, mask, loops, openings, pixel_mm=1.):
        self.sequence += 1
        image = self.work / ('mask-%d.png' % self.sequence)
        rgba = self.np.full((*mask.shape, 4), 255, dtype=self.np.uint8)
        rgba[mask, :3] = 0
        self.Image.fromarray(rgba, 'RGBA').save(image)
        manifest = self.work / ('inputs-%d.json' % self.sequence)
        manifest.write_text(json.dumps(dict(schema='cad-harness.inputs.v4c', profile='c-s1',
            evidence_mode='independent_dev', assets=dict(image=dict(kind='image', role='checker',
                path=image.name, sha256=ledger.file_sha(image), bytes=image.stat().st_size)))), encoding='utf-8')
        foreground = dict(channel='luminance', polarity='dark', threshold=127)
        record = dict(asset_id='image', units='mm', loops=copy.deepcopy(loops),
            source_image_sha256=ledger.file_sha(image),
            pixel_to_mm=dict(scale_mm_per_pixel=pixel_mm, origin_mm=[0., 0.],
                             image_height_pixels=int(mask.shape[0])),
            recipe=dict(curve_fit=dict(method='source_bounded_biarc_v2'),
                topology=dict(components='preserve', holes='preserve', islands='preserve',
                              connectivity=copy.deepcopy(CONNECTIVITY)),
                foreground=foreground, alpha=dict(policy='threshold', threshold=128)),
            reports=dict(pinch_openings=copy.deepcopy(openings)))
        geometry, _ = judges.planar_geometry(record, 1e-5)
        record['nominal_width_mm'] = geometry.bounds[2]-geometry.bounds[0]
        registration = dict(origin_mm=[0., mask.shape[0]*pixel_mm],
                            pixel_size_mm=[pixel_mm, pixel_mm], y_direction=-1)
        common = dict(contour_id='image', leg='image_to_contour', curve_tolerance_mm=1e-5,
            mask_asset_id='image', registration=registration, foreground=dict(foreground, alpha_min=128))
        card = dict(schema='cad-harness.judge-card.v4c', profile='c-s1', source='independent_dev',
            linear_tolerance_mm=1e-5, criteria=[
                dict(common, id='image_iou', metric='image_iou', minimum_iou=.90),
                dict(common, id='image_hausdorff', metric='boundary_hausdorff', maximum_mm=1.5,
                     sampling_step_mm=.1)])
        plan = dict(family='contour_extrude', contour_id='image', width_mm=record['nominal_width_mm'],
                    thickness_mm=3., origin_mm=[0., 0., 0.])
        return dict(manifest=manifest, record=record, mask=mask, card=card, plan=plan,
                    packet=dict(assets=dict(image=record)))

    def image_judgement(self, fixture):
        # These consumer-facing image criteria require no CAD object or native imports.
        return judges.judge(fixture['plan'], fixture['manifest'], fixture['packet'], object(), fixture['card'])

    def diagonal(self, gap=.1):
        mask = self.np.zeros((28, 28), dtype=bool)
        fill(mask, 2, 2, 10, 10)
        fill(mask, 12, 12, 10, 10)
        loops = [polygon_loop([(2, 2), (12, 2), (12, 12-gap), (12-gap, 12), (2, 12)]),
                 polygon_loop([(12, 12+gap), (12+gap, 12), (22, 12), (22, 22), (12, 22)])]
        return self.fixture(mask, loops, [contact(12, 12, [1, 2])])

    def pinched_hole(self):
        mask = self.np.zeros((16, 16), dtype=bool)
        fill(mask, 2, 2, 10, 10)
        fill(mask, 6, 6, 1, 1, False)
        fill(mask, 7, 7, 1, 1, False)
        void = self.box(6, 6, 7, 7).union(self.box(7, 7, 8, 8)).union(
            self.box(6.95, 6.95, 7.05, 7.05))
        loops = [rectangle(2, 2, 12, 12)] + region_loops(void, 'hole')
        return self.fixture(mask, loops, [contact(7, 7, [1])])


@unittest.skipUnless(NUMERIC, 'requires host numpy / Pillow / Shapely; no native launch')
class C2TopologyJudgesHostTests(_IndependentFixtures, unittest.TestCase):
    def test_tiny_original_piece_can_grow_but_cannot_disappear(self):
        mask = self.np.zeros((48, 64), dtype=bool)
        fill(mask, 4, 4, 32, 32)
        fill(mask, 48, 8, 1, 1)
        value = self.fixture(mask, [rectangle(1, 1, 9, 9), circle(12.125, 2.125, .30)], [], .25)
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['checks'][0]['evidence']['source_topology'], dict(components=2, holes=0))
        value['record']['loops'].pop()
        value['record']['topology'] = dict(source=dict(components=1, holes=0),
                                          output=dict(components=1, holes=0))
        value['record']['reports']['source_topology'] = dict(components=1, holes=0)
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'FAIL', result)
        # The omitted singleton is less than one tenth of a percent of source area.
        self.assertGreater(result['checks'][0]['measured']['nominal'], .99)

    def test_diagonal_piece_contacts_are_locally_opened_not_merged(self):
        value = self.diagonal()
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'PASS', result)
        evidence = result['checks'][0]['evidence']['pinch_openings']
        self.assertTrue(evidence['listing_matches'])
        self.assertTrue(evidence['cleared'])
        self.assertGreater(evidence['openings'][0]['clearance_mm_lower'], 0.)
        self.assertLess(evidence['openings'][0]['clearance_mm_lower'], .1)
        # An arbitrarily large report is not used as the distance certificate.
        self.assertEqual(value['record']['reports']['pinch_openings'][0]['clearance_mm_lower'], 1e6)
        for loops in ([rectangle(2, 2, 12, 12), rectangle(12, 12, 22, 22)],
                      [rectangle(2, 2, 12, 12)],
                      region_loops(self.box(2, 2, 12, 12).union(self.box(12, 12, 22, 22)).union(
                          self.box(11.9, 11.9, 12.1, 12.1)))):
            value['record']['loops'] = loops
            result = self.image_judgement(value)
            self.assertEqual(result['status'], 'FAIL', result)

    def test_bounded_growth_may_overlap_original_neighbor_with_a_perfect_bijection(self):
        mask = self.np.zeros((16, 16), dtype=bool)
        fill(mask, 2, 2, 10, 10)
        fill(mask, 12, 12, 1, 1)
        grown_parent = self.box(2, 2, 12, 12).union(self.box(11.9, 11.9, 12.8, 12.8)).difference(
            self.box(11.95, 11.95, 12.8, 12.05))
        loops = region_loops(grown_parent) + [circle(13.1, 13.1, .30)]
        value = self.fixture(mask, loops, [contact(12, 12, [1, 2])])
        _, _, source = judges._mask_region(value['manifest'], value['card']['criteria'][0], digital=True)
        candidate, _ = judges.planar_geometry(value['record'], 1e-5)
        target = list(candidate.geoms)
        # Both original pieces favor the large output; historical greedy matching
        # would reject despite a retained, separated, overlapping tiny output.
        self.assertIsNone(judges._overlap_correspondence(source['components'], target))
        self.assertTrue(judges._digital_nesting_matches(source, candidate))
        self.assertEqual(self.image_judgement(value)['status'], 'PASS')

    def test_missing_forged_duplicate_or_malformed_contacts_never_accept(self):
        mutations = [lambda r: r['reports'].pop('pinch_openings'),
            lambda r: r['reports'].update(pinch_openings=[]),
            lambda r: r['reports']['pinch_openings'][0].update(vertex_pixels=[11, 12]),
            lambda r: r['reports']['pinch_openings'][0].update(incident_components=[1]),
            lambda r: r['reports']['pinch_openings'][0].update(incident_components=[2, 1]),
            lambda r: r['reports']['pinch_openings'][0].update(vertex_pixels=[12., 12]),
            lambda r: r['reports']['pinch_openings'][0].update(clearance_mm_lower=float('nan')),
            lambda r: r['reports']['pinch_openings'][0].update(clearance_mm_lower=0.),
            lambda r: r['reports']['pinch_openings'][0].update(extra='forged'),
            lambda r: r['reports']['pinch_openings'].append(copy.deepcopy(r['reports']['pinch_openings'][0]))]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = self.diagonal()
                mutation(value['record'])
                self.assertEqual(self.image_judgement(value)['status'], 'FAIL')

    def test_bg8_pinched_hole_is_one_void_despite_two_geos_interiors(self):
        value = self.pinched_hole()
        criterion = value['card']['criteria'][0]
        original, _, analysis = judges._mask_region(value['manifest'], criterion, digital=True)
        self.assertEqual(judges._topology(original), dict(components=1, holes=2))
        self.assertEqual(analysis['topology'], dict(components=1, holes=1))
        self.assertAlmostEqual(original.area, 98.)
        self.assertEqual(analysis['component_parents'], [0])
        self.assertEqual(analysis['hole_parents'], [1])
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['checks'][0]['evidence']['source_topology'], dict(components=1, holes=1))
        value['record']['loops'] = [rectangle(2, 2, 12, 12)]
        self.assertEqual(self.image_judgement(value)['status'], 'FAIL')
        value['record']['loops'] += [rectangle(6.05, 6.05, 6.95, 6.95, 'hole'),
                                    rectangle(7.05, 7.05, 7.95, 7.95, 'hole')]
        self.assertEqual(self.image_judgement(value)['status'], 'FAIL')

    def test_contact_inside_material_fails_despite_matching_counts_overlap_and_fidelity(self):
        from shapely.affinity import translate
        value = self.pinched_hole()
        hole = self.box(6, 6, 7, 7).union(self.box(7, 7, 8, 8)).union(
            self.box(6.95, 6.95, 7.05, 7.05))
        value['record']['loops'] = [rectangle(2, 2, 12, 12)] + region_loops(
            translate(hole, xoff=.15, yoff=-.15), 'hole')
        _, _, source = judges._mask_region(value['manifest'], value['card']['criteria'][0], digital=True)
        candidate, _ = judges.planar_geometry(value['record'], 1e-5)
        self.assertTrue(judges._digital_nesting_matches(source, candidate))
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertGreater(result['checks'][0]['measured']['lower'], .90)
        self.assertLess(result['checks'][1]['measured']['upper_mm'], 1.5)
        self.assertFalse(result['checks'][0]['evidence']['pinch_openings']['cleared'])

    def test_positive_clearance_has_no_added_physical_gap_tolerance(self):
        value = self.diagonal(gap=1e-6)
        value['card']['linear_tolerance_mm'] = .5
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertLess(result['checks'][0]['evidence']['pinch_openings']['openings'][0][
            'clearance_mm_lower'], 1e-6)
        _, _, source = judges._mask_region(value['manifest'], value['card']['criteria'][0], digital=True)
        material, _ = judges.planar_geometry(value['record'], 1e-5)
        self.assertFalse(judges._pinch_openings(value['record'], source, material, 1e-5)['cleared'])

    def test_bg8_exterior_contact_does_not_create_a_source_hole(self):
        mask = self.np.zeros((8, 8), dtype=bool)
        fill(mask, 2, 2, 4, 4)
        fill(mask, 2, 2, 1, 1, False)
        fill(mask, 3, 3, 1, 1, False)
        removed = self.box(2, 2, 3, 3).union(self.box(3, 3, 4, 4)).union(
            self.box(2.95, 2.95, 3.05, 3.05))
        candidate = self.box(2, 2, 6, 6).difference(removed)
        value = self.fixture(mask, region_loops(candidate), [contact(3, 3, [1])])
        result = self.image_judgement(value)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['checks'][0]['evidence']['source_topology'], dict(components=1, holes=0))
        # Historical strict closed-set counting is not silently switched to v2.
        value['record']['recipe']['curve_fit']['method'] = 'periodic_cubic_biarc_v1'
        value['record']['recipe']['topology'].pop('connectivity')
        self.assertEqual(self.image_judgement(value)['status'], 'FAIL')

    def test_fixed_frame_nested_island_forest_and_empty_contact_report(self):
        mask = self.np.zeros((24, 24), dtype=bool)
        fill(mask, 2, 2, 16, 16)
        fill(mask, 5, 5, 10, 10, False)
        fill(mask, 7, 7, 2, 2)
        fill(mask, 21, 2, 2, 2)
        loops = [rectangle(2, 2, 18, 18), rectangle(5, 5, 15, 15, 'hole'),
                 rectangle(7, 7, 9, 9), rectangle(21, 2, 23, 4)]
        value = self.fixture(mask, loops, [])
        self.assertEqual(self.image_judgement(value)['status'], 'PASS')
        _, _, source = judges._mask_region(value['manifest'], value['card']['criteria'][0], digital=True)
        self.assertEqual(source['topology'], dict(components=3, holes=1))
        self.assertEqual(sorted(source['component_parents']), [0, 0, 1])
        value['record']['reports'].pop('pinch_openings')
        self.assertEqual(self.image_judgement(value)['status'], 'FAIL')
        value['record']['reports']['pinch_openings'] = []
        value['record']['loops'][2] = rectangle(19, 7, 21, 9)
        self.assertEqual(self.image_judgement(value)['status'], 'FAIL')


@unittest.skipUnless(NATIVE, 'set CAD_VERIFY_C2_TOPOLOGY_NATIVE=1 under pinned Python 3.11.14 / FreeCAD 1.1.4; no discovery launch')
class C2TopologyJudgesNativeTests(_IndependentFixtures, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')
        cls.App, cls.Part = App, Part

    def native_shape(self, loops):
        wires = []
        for loop in loops:
            edges = []
            for segment in loop['segments']:
                point = lambda key: self.App.Vector(*segment[key], 0.)
                edges.append(self.Part.makeLine(point('p0'), point('p1')) if segment['kind'] == 'line'
                             else self.Part.Arc(point('p0'), point('pm'), point('p1')).toShape())
            wires.append(self.Part.Wire(edges))
        face = self.Part.makeFace(wires, 'Part::FaceMakerBullseye')
        shape = face.extrude(self.App.Vector(0., 0., 3.))
        self.assertTrue(shape.isValid())
        return shape

    def output_judgement(self, fixture, shape):
        criteria = [dict(id='output_iou', metric='image_iou', leg='contour_to_output',
                        contour_id='image', curve_tolerance_mm=1e-5, projection_z_mm=1.5,
                        minimum_iou=.92),
                    dict(id='output_hausdorff', metric='boundary_hausdorff', leg='contour_to_output',
                        contour_id='image', curve_tolerance_mm=1e-5, projection_z_mm=1.5,
                        maximum_mm=1., sampling_step_mm=.1)]
        card = dict(schema='cad-harness.judge-card.v4c', profile='c-s1', source='independent_dev',
                    linear_tolerance_mm=1e-5, criteria=criteria)
        return judges.judge(fixture['plan'], fixture['manifest'], fixture['packet'], shape, card)

    def test_native_shared_vertex_tolerance_is_enclosed_not_json_authorized(self):
        # Independently authored almost-rectangular wire. OCCT joins the two
        # endpoints within its native tolerance; its curve evaluations differ.
        points = [self.App.Vector(x, y, 0.) for x, y in ((0, 0), (10, 0), (10, 8), (0, 8))]
        edges = [self.Part.makeLine(points[0], points[1]),
                 self.Part.makeLine(self.App.Vector(10+5e-8, 0, 0), points[2]),
                 self.Part.makeLine(points[2], points[3]),
                 self.Part.makeLine(points[3], points[0])]
        shape = self.Part.Face(self.Part.Wire(edges)).extrude(self.App.Vector(0, 0, 3))
        self.assertTrue(shape.isValid())
        record = judges._shape_record(shape, 1.5)
        region, error = judges.planar_geometry(record, 1e-5)
        self.assertLessEqual(abs(region.area-80.), 36*error+math.pi*error**2)
        self.assertEqual(judges.minimum_radius(record, 1e-6)['minimum_mm'], 0.)
        # Native provenance cannot be acquired by serializing the same points.
        plain = json.loads(json.dumps(record))
        with self.assertRaises(ValueError):
            judges.planar_geometry(plain, 1e-5)
        with self.assertRaises(ValueError):
            judges.minimum_radius(plain, 1e-6)

    def test_positional_vertex_tolerance_does_not_bend_a_native_circle(self):
        shape = self.Part.makeCylinder(.3, 3.)
        shape.fixTolerance(2e-6)
        record = judges._shape_record(shape, 1.5)
        measured = judges.minimum_radius(record, 1e-6)
        self.assertAlmostEqual(measured['minimum_mm'], .3, places=12)
        self.assertEqual(measured['sharp_corners'], 0)
        self.assertGreater(measured['native_error_mm'], 1e-6)

    def test_retained_grown_singleton_native_and_step_and_dropped_control(self):
        mask = self.np.zeros((48, 64), dtype=bool)
        fill(mask, 4, 4, 32, 32)
        fill(mask, 48, 8, 1, 1)
        value = self.fixture(mask, [rectangle(1, 1, 9, 9), circle(12.125, 2.125, .30)], [], .25)
        shape = self.native_shape(value['record']['loops'])
        self.assertEqual(len(shape.Solids), 2)
        self.assertEqual(self.output_judgement(value, shape)['status'], 'PASS')
        step_path = self.work / 'retained.step'
        shape.exportStep(str(step_path))
        step = self.Part.Shape()
        step.read(str(step_path))
        self.assertTrue(step.isValid())
        self.assertEqual(len(step.Solids), 2)
        self.assertEqual(self.output_judgement(value, step)['status'], 'PASS')
        dropped = max(shape.Solids, key=lambda solid: solid.Volume)
        self.assertEqual(self.output_judgement(value, dropped)['status'], 'FAIL')

    def test_diagonal_opening_native_and_actual_merged_control(self):
        value = self.diagonal()
        shape = self.native_shape(value['record']['loops'])
        self.assertEqual(len(shape.Solids), 2)
        self.assertGreater(shape.Solids[0].distToShape(shape.Solids[1])[0], 0.)
        self.assertEqual(self.output_judgement(value, shape)['status'], 'PASS')
        bridge = self.Part.makeBox(.4, .4, 3., self.App.Vector(11.8, 11.8, 0.))
        merged = shape.fuse(bridge)
        self.assertTrue(merged.isValid())
        self.assertEqual(self.output_judgement(value, merged)['status'], 'FAIL')
        value['record']['reports']['pinch_openings'] = []
        self.assertEqual(self.output_judgement(value, shape)['status'], 'FAIL')

    def test_contact_certificate_uses_the_one_declared_output_registration(self):
        value = self.diagonal()
        factor, offset = 1.25, (3., 4.)
        transformed = copy.deepcopy(value['record']['loops'])
        for loop in transformed:
            for segment in loop['segments']:
                for key in ('p0', 'pm', 'p1'):
                    if key in segment:
                        segment[key] = [factor*segment[key][i]+offset[i] for i in range(2)]
        value['plan']['width_mm'] *= factor
        value['plan']['origin_mm'] = [*offset, 0.]
        shape = self.native_shape(transformed)
        result = self.output_judgement(value, shape)
        self.assertEqual(result['status'], 'PASS', result)
        lower = result['checks'][0]['evidence']['pinch_openings']['openings'][0]['clearance_mm_lower']
        self.assertGreater(lower, .08)
        self.assertLess(lower, .09)
        value['plan']['origin_mm'] = [0., 0., 0.]
        self.assertEqual(self.output_judgement(value, shape)['status'], 'FAIL')

    def test_bg8_hole_native_and_filled_or_uncleared_controls(self):
        from shapely.affinity import translate
        value = self.pinched_hole()
        good = self.native_shape(value['record']['loops'])
        self.assertEqual(self.output_judgement(value, good)['status'], 'PASS')
        filled = self.Part.makeBox(10., 10., 3., self.App.Vector(2., 2., 0.))
        self.assertEqual(self.output_judgement(value, filled)['status'], 'FAIL')
        void = self.box(6, 6, 7, 7).union(self.box(7, 7, 8, 8)).union(
            self.box(6.95, 6.95, 7.05, 7.05))
        shifted = self.native_shape([rectangle(2, 2, 12, 12)] + region_loops(
            translate(void, xoff=.15, yoff=-.15), 'hole'))
        result = self.output_judgement(value, shifted)
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertGreater(result['checks'][0]['measured']['lower'], .92)
        self.assertFalse(result['checks'][0]['evidence']['pinch_openings']['cleared'])


if __name__ == '__main__':
    unittest.main()
