"""Generic source-certified C2 controls; no CAD discovery launch or model calls.

Only newly authored temporary RGBA fixtures are used. Source behavior requires
CAD_VERIFY_C2_CYCLE3_NATIVE=1 under pinned Python 3.11.14 / FreeCAD 1.1.4 and the
existing raster-fit dependencies; host schema admission has no native dependency.
These tests do not claim the locked stress gate or actual-output CAD acceptance.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

if __package__:
    from . import cad_verify_v4_biarcs as biarcs
    from . import cad_verify_v4_contours as contours
    from . import cad_verify_v4_ledger as ledger
    from . import cad_verify_v4_plans as plans
else:
    import cad_verify_v4_contours as contours
    import cad_verify_v4_biarcs as biarcs
    import cad_verify_v4_ledger as ledger
    import cad_verify_v4_plans as plans


NUMERIC = all(importlib.util.find_spec(name) is not None
              for name in ('numpy', 'scipy', 'shapely', 'PIL'))
NATIVE = (NUMERIC and os.environ.get('CAD_VERIFY_C2_CYCLE3_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
NATIVE_REASON = 'set CAD_VERIFY_C2_CYCLE3_NATIVE=1 under pinned Python 3.11.14 / FreeCAD 1.1.4'


def recipe():
    """Independent physical-unit policy, not a production-registry echo."""
    return dict(schema='cad-harness.contour-recipe.v4c', profile='c-s1',
        foreground=dict(channel='alpha', polarity='light', threshold=128),
        alpha=dict(policy='ignore'), scale=dict(canonical_height_mm=50., origin_mm=[0., 0.]),
        simplify=dict(allowed=False), rounding=dict(allowed=False),
        curve_fit=dict(method='source_bounded_biarc_v2', maximum_error_mm=1.5,
            minimum_iou=.90, minimum_radius_mm=.25, smoothing_rms_mm=.2,
            sample_spacing_mm=.4, biarc_error_mm=.02, maximum_fit_passes=8),
        limits=dict(max_deviation_mm=1.5, approximation_tolerance_mm=.005),
        topology=dict(components='preserve', holes='preserve', islands='preserve',
            connectivity=dict(foreground=4, background=8, pinch='remove_locally')))


class CycleThreeRecipeAdmission(unittest.TestCase):
    def test_closed_v2_branch_and_nonproduction_canonical_height(self):
        value = recipe()
        value['scale']['canonical_height_mm'] = 37.
        self.assertEqual(plans.validate_document(value, 'contour-recipe'), value)
        self.assertEqual(contours.validate_recipe(value), value)
        mutations = [lambda r: r['curve_fit'].pop('maximum_error_mm'),
            lambda r: r['curve_fit'].update(maximum_error_pixels=1.),
            lambda r: r['curve_fit'].update(method='uncertified_pixel_fallback'),
            lambda r: r['scale'].update(mm_per_pixel=.5),
            lambda r: r.update(scale=dict(mm_per_pixel=.5, origin_mm=[0., 0.])),
            lambda r: r.update(simplify=dict(allowed=True, tolerance_mm=.1)),
            lambda r: r.update(rounding=dict(allowed=True, radius_mm=.25))]
        for mutation in mutations:
            value = recipe()
            mutation(value)
            for validator in (lambda r: plans.validate_document(r, 'contour-recipe'),
                              contours.validate_recipe):
                with self.subTest(mutation=mutation, validator=validator), self.assertRaises(ValueError):
                    validator(value)

    def test_physical_fields_reject_nonfinite_boolean_and_out_of_range(self):
        fields = ('maximum_error_mm', 'minimum_radius_mm', 'smoothing_rms_mm',
                  'sample_spacing_mm', 'biarc_error_mm', 'minimum_iou')
        for field in fields:
            for invalid in (0, -1, True, None, float('nan'), float('inf')):
                value = recipe()
                value['curve_fit'][field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    with self.assertRaises(ValueError):
                        plans.validate_document(value, 'contour-recipe')
                    with self.assertRaises(ValueError):
                        contours.validate_recipe(value)
        for field, invalid in (('minimum_iou', 1.01), ('maximum_fit_passes', True),
                               ('maximum_fit_passes', 0), ('maximum_fit_passes', 9),
                               ('maximum_fit_passes', 1.5)):
            value = recipe()
            value['curve_fit'][field] = invalid
            with self.subTest(field=field, invalid=invalid):
                with self.assertRaises(ValueError):
                    plans.validate_document(value, 'contour-recipe')
                with self.assertRaises(ValueError):
                    contours.validate_recipe(value)

    def test_source_bound_cannot_exceed_declared_mm_limit(self):
        value = recipe()
        value['curve_fit']['maximum_error_mm'] = 1.5001
        with self.assertRaises(ValueError):
            contours.validate_recipe(value)
        # The relation is semantic runtime admission, not a JSON-schema default.
        value = recipe()
        value['limits']['max_deviation_mm'] = .5
        with self.assertRaises(ValueError):
            contours.validate_recipe(value)

    def test_explicit_historical_pixel_branch_remains_available(self):
        value = recipe()
        value['topology'].pop('connectivity')
        value['curve_fit'] = dict(method='periodic_cubic_biarc_v1', maximum_error_pixels=1.,
            tangent_span_pixels=4., corner_angle_degrees=60., smoothing_rms_pixels=.2,
            sample_spacing_pixels=1., biarc_error_pixels=.1, maximum_fit_passes=4)
        value['scale'] = dict(mm_per_pixel=.5, origin_mm=[0., 0.])
        self.assertEqual(plans.validate_document(value, 'contour-recipe'), value)
        self.assertEqual(contours.validate_recipe(value), value)
        value['curve_fit']['maximum_error_mm'] = 1.5
        with self.assertRaises(ValueError):
            plans.validate_document(value, 'contour-recipe')
        with self.assertRaises(ValueError):
            contours.validate_recipe(value)


class CycleThreeRadiusBehavior(unittest.TestCase):
    def test_shallow_arc_join_is_certified_but_real_corner_still_fails(self):
        # Independent analytic circle. One shallow arc exposes the otherwise
        # irrelevant conditioning of its remote circumcentre.
        radius = 100000.
        angles = [0., 2.9 / radius, math.pi / 2, math.pi, 3 * math.pi / 2, 2 * math.pi]
        def point(angle):
            return [40 + radius * math.sin(angle),
                    10 + 2 * radius * math.sin(angle / 2) ** 2]
        segments = [dict(kind='arc', p0=point(a), pm=point((a+b)/2), p1=point(b))
                    for a, b in zip(angles, angles[1:])]
        segments[-1]['p1'] = list(segments[0]['p0'])
        record = dict(loops=[dict(role='outer', segments=segments)])
        self.assertAlmostEqual(contours.minimum_radius(record), radius, delta=.001)
        bad = copy.deepcopy(record)
        bad['loops'][0]['segments'][0]['pm'][1] += .00001
        self.assertEqual(contours.minimum_radius(bad), 0.)


@unittest.skipUnless(NUMERIC, 'requires numpy/scipy/shapely/Pillow')
class CycleThreeMaterialReachability(unittest.TestCase):
    @staticmethod
    def neck_fixture(half_width=.1):
        """Independent R=1 dumbbell; default 0.2-mm neck is NOT toolable."""
        segments, ring = [], [(2., half_width)]
        def line(end):
            segments.append(dict(kind='line', p0=list(ring[-1]), p1=list(end)))
            ring.append(end)
        def arc(center, start, stop, end):
            middle = (start+stop)/2
            segments.append(dict(kind='arc', p0=list(ring[-1]),
                pm=[center[0]+math.cos(middle), center[1]+math.sin(middle)], p1=list(end)))
            count = math.ceil(abs(stop-start)/.02)
            ring.extend((center[0]+math.cos(start+(stop-start)*i/count),
                         center[1]+math.sin(start+(stop-start)*i/count))
                        for i in range(1, count))
            ring.append(end)
        line((-2., half_width))
        arc((-2., 1+half_width), -math.pi/2, -math.pi, (-3., 1+half_width))
        line((-3., 24.))
        arc((-4., 24.), 0., math.pi/2, (-4., 25.))
        line((-9., 25.))
        arc((-9., 24.), math.pi/2, math.pi, (-10., 24.))
        line((-10., -24.))
        arc((-9., -24.), math.pi, 3*math.pi/2, (-9., -25.))
        line((-4., -25.))
        arc((-4., -24.), 3*math.pi/2, 2*math.pi, (-3., -24.))
        line((-3., -1-half_width))
        arc((-2., -1-half_width), math.pi, math.pi/2, (-2., -half_width))
        line((2., -half_width))
        arc((2., -1-half_width), math.pi/2, 0., (3., -1-half_width))
        line((3., -24.))
        arc((4., -24.), math.pi, 3*math.pi/2, (4., -25.))
        line((9., -25.))
        arc((9., -24.), -math.pi/2, 0., (10., -24.))
        line((10., 24.))
        arc((9., 24.), 0., math.pi/2, (9., 25.))
        line((4., 25.))
        arc((4., 24.), math.pi/2, math.pi, (3., 24.))
        line((3., 1+half_width))
        arc((2., 1+half_width), 0., -math.pi/2, (2., half_width))
        return dict(role='outer', segments=segments), ring[:-1]

    def test_minimum_radius_alone_cannot_admit_inaccessible_material(self):
        from shapely.geometry import Polygon
        loop, ring = self.neck_fixture()
        self.assertAlmostEqual(contours.minimum_radius(dict(loops=[loop])), 1., places=10)
        material = Polygon(ring)
        # Independent disk sweep, not a checker report or fitter result.
        swept = material.buffer(-.25, quad_segs=256).buffer(.25, quad_segs=256)
        self.assertGreater(material.difference(swept).area, .1)
        self.assertFalse(biarcs._material_reachable(material, .00005, .25, .02))

    def test_analytic_normal_proposals_make_a_thin_neck_toolable_within_source_bounds(self):
        from shapely.affinity import scale
        from shapely.geometry import Polygon
        loop, ring = self.neck_fixture()
        arcs = [biarcs._arc(tuple(segment['p0']), tuple(segment['p1']),
                           contours._tangent(segment, False))
                for segment in loop['segments']]
        policy = recipe()['curve_fit']
        for segments, candidate in biarcs._parallel_candidates(
                loop['segments'], arcs, policy, .265, 1.5):
            points, error = biarcs._flatten(candidate, .00005)
            shape = Polygon(points)
            if not shape.is_valid:
                continue
            factor = 50. / (shape.bounds[3]-shape.bounds[1])
            output = scale(shape, factor, factor, origin=(0., 0.))
            original = scale(Polygon(ring), factor, factor, origin=(0., 0.))
            swept = output.buffer(-.25, quad_segs=256).buffer(.25, quad_segs=256)
            if output.difference(swept).area > .1:
                continue
            self.assertGreaterEqual(contours.minimum_radius(
                dict(loops=[dict(loop, segments=segments)]))*factor, .25)
            self.assertGreaterEqual(original.intersection(output).area/original.union(output).area, .90)
            self.assertLessEqual(original.boundary.hausdorff_distance(output.boundary)+2*error*factor, 1.5)
            break
        else:
            self.fail('bounded analytic candidates never made the retained neck toolable')

    def test_actual_tool_is_not_curvature_construction_reserve(self):
        from shapely.geometry import Polygon
        loop, ring = self.neck_fixture(half_width=.26)
        self.assertAlmostEqual(contours.minimum_radius(dict(loops=[loop])), 1., places=10)
        material = Polygon(ring)
        self.assertTrue(biarcs._material_reachable(material, .00005, .25, .02))
        self.assertFalse(biarcs._material_reachable(material, .00005, .2862, .02))

    def test_partial_components_prune_material_walls_before_nested_choices(self):
        from shapely.affinity import translate
        from shapely.geometry import box
        # Independent rounded-rectangle fixture construction, not output repair.
        outer = box(1., 1., 19., 49.).buffer(1., quad_segs=128)
        near = box(1.2, 11., 4., 24.).buffer(1., quad_segs=128)
        far = box(11., 11., 14., 24.).buffer(1., quad_segs=128)
        source = [dict(role='outer'), dict(role='hole', parent=0), dict(role='hole', parent=0)]
        future = [None, near.buffer(1.5), far.buffer(1.5)]
        self.assertFalse(biarcs._material_layout_compatible(
            source, source[:2], [(outer, .00005), (near, .00005)], .25, .02, future,
            all_components=True))
        # Even an extremely generous future-hole envelope cannot erase the
        # positive material collars guaranteed by strict loop separation.
        self.assertFalse(biarcs._material_layout_compatible(
            source, source[:2], [(outer, .00005), (near, .00005)], .25, .02,
            [None, future[1], outer.buffer(1.5)], all_components=True))
        self.assertTrue(biarcs._material_layout_compatible(source, source[:2],
            [(outer, .00005), (translate(near, xoff=.6), .00005)], .25, .02, future,
            all_components=True))
        # Two same-parent holes leave a separate inaccessible material wall.
        self.assertFalse(biarcs._material_layout_compatible(source, source,
            [(outer, .00005), (translate(near, xoff=3.), .00005),
             (translate(far, xoff=-1.8), .00005)], .25, .02, future,
            all_components=True))

    def test_close_foreground_and_hole_island_void_gaps_are_not_material_walls(self):
        from shapely.affinity import translate
        from shapely.geometry import Point, box
        outer = box(1., 1., 19., 49.).buffer(1., quad_segs=128)
        pieces = [dict(role='outer'), dict(role='outer')]
        self.assertTrue(biarcs._material_layout_compatible(pieces, pieces,
            [(outer, .00005), (translate(outer, xoff=20.2), .00005)], .25, .02,
            [None, None], all_components=True))
        forest = [dict(role='outer'), dict(role='hole', parent=0),
                  dict(role='outer', parent=1)]
        hole = Point(10., 25.).buffer(2., quad_segs=128)
        island = Point(10., 25.).buffer(1.8, quad_segs=128)
        self.assertTrue(biarcs._material_layout_compatible(forest, forest,
            [(outer, .00005), (hole, .00005), (island, .00005)], .25, .02,
            [None, hole.buffer(1.5), None], all_components=True))

    def test_branch_constraints_distinguish_material_from_narrow_void(self):
        import numpy as np
        from scipy.spatial import cKDTree
        from shapely.geometry import Polygon, box
        ring = [(-.1, -5.), (.1, -5.), (.1, 5.), (-.1, 5.)]
        # Uniform perimeter samples, independently constructed. The same
        # opposed branches bound either material or a hole, never both.
        samples = []
        for a, b in zip(ring, ring[1:]+ring[:1]):
            count = round(math.dist(a, b)/.05)
            samples.extend((a[0]+(b[0]-a[0])*i/count, a[1]+(b[1]-a[1])*i/count)
                           for i in range(count))
        target = np.asarray(samples)
        distances, neighbours = cKDTree(target).query(target, k=64)
        solid = Polygon(ring)
        void = box(-5., -6., 5., 6.).difference(solid)
        self.assertTrue(biarcs._material_pairs(target, neighbours, distances,
            20.4, .25, .3, solid.buffer(1e-12)))
        self.assertFalse(biarcs._material_pairs(target, neighbours, distances,
            20.4, .25, .3, void.buffer(1e-12)))

    def test_thin_neck_and_interloop_wall_keep_fidelity_and_nested_forest(self):
        from shapely.affinity import scale
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        _, outer = self.neck_fixture()
        # A separate 0.2-mm wall lies between the outer and immediate hole;
        # the hole-to-island gap is void and must not acquire a tool-width rule.
        hole = []
        for center, start in (((-6.8, 5.), -math.pi/2), ((-6.8, 15.), 0.),
                              ((-8.8, 15.), math.pi/2), ((-8.8, 5.), math.pi)):
            hole.extend((center[0]+math.cos(start+math.pi*i/64),
                         center[1]+math.sin(start+math.pi*i/64)) for i in range(33))
        hole.reverse()
        island = [(-7.8+.75*math.cos(2*math.pi*i/128),
                   10+.75*math.sin(2*math.pi*i/128)) for i in range(128)]
        source = []
        for index, (role, ring) in enumerate((('outer', outer), ('hole', hole), ('outer', island))):
            loop = dict(role=role, segments=[
                dict(kind='line', p0=list(a), p1=list(b))
                for a, b in zip(ring, ring[1:]+ring[:1])])
            if index:
                loop['parent'] = index-1
            source.append(loop)
        original = copy.deepcopy(source)
        fitted = biarcs.fit_loops(source, recipe()['curve_fit'])
        self.assertEqual(source, original)
        self.assertEqual([(loop['role'], loop.get('parent')) for loop in fitted],
                         [('outer', None), ('hole', 0), ('outer', 1)])
        rings, error = contours.flatten_loops(dict(loops=fitted), .0002)
        before = unary_union([Polygon(outer, [hole]), Polygon(island)])
        after = unary_union([Polygon(rings[0], [rings[1]]), Polygon(rings[2])])
        self.assertTrue(after.is_valid)
        self.assertTrue(Polygon(rings[0]).contains(Polygon(rings[1])))
        self.assertTrue(Polygon(rings[1]).contains(Polygon(rings[2])))
        self.assertEqual(len(after.geoms), 2)
        # The same final registration applies to original and output geometry.
        factor = 50/(after.bounds[3]-after.bounds[1])
        before, after = (scale(region, xfact=factor, yfact=factor, origin=(0, 0))
                         for region in (before, after))
        error *= factor
        self.assertGreaterEqual(before.intersection(after.buffer(-error)).area /
                                before.union(after.buffer(error)).area, .90)
        self.assertLessEqual(before.boundary.hausdorff_distance(after.boundary)+error, 1.5)
        self.assertGreaterEqual(contours.minimum_radius(dict(loops=fitted))*factor, .25)
        swept = after.buffer(-.25, quad_segs=256).buffer(.25, quad_segs=256)
        self.assertLessEqual(after.difference(swept).area, .1)


@unittest.skipUnless(NATIVE, NATIVE_REASON)
class CycleThreeNativeSourceBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')

    def setUp(self):
        from PIL import Image
        self.temporary = tempfile.TemporaryDirectory(prefix='cad-c2-cycle3-generic-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sequence = 0
        self.Image = Image

    def manifest(self, name='disk', padded=False, multiple=False, narrow_slot=False):
        size = 256 if narrow_slot else 128
        cells = []
        for row in range(size):
            for col in range(size):
                x, y = col + .5, row + .5
                if narrow_slot:
                    foreground = ((x-128)**2+(y-128)**2 <= 112**2
                                  and not (127 <= col < 128 and 84 <= row < 172))
                elif multiple:
                    foreground = ((x-32)**2+(y-32)**2 <= 16**2
                                  or (x-88)**2+(y-88)**2 <= 24**2)
                else:
                    foreground = (x-64)**2+(y-64)**2 <= 42**2
                cells.append((23, 91, 177, 255 if foreground else 0))
        image = self.Image.new('RGBA', (size, size))
        image.putdata(cells)
        if padded:
            larger = self.Image.new('RGBA', (size+32, size+28), (214, 7, 43, 0))
            larger.paste(image, (13, 17))
            image = larger
        path = self.root / (name + '.png')
        image.save(path)
        manifest = self.root / (name + '-manifest.json')
        manifest.write_text(json.dumps(dict(schema='cad-harness.inputs.v4c', profile='c-s1',
            evidence_mode='independent_dev', assets={'source': dict(kind='image', role='checker',
                path=path.name, sha256=ledger.file_sha(path), bytes=path.stat().st_size)})), encoding='utf-8')
        return manifest

    def prepare(self, manifest, value=None):
        self.sequence += 1
        out = self.root / ('prepared-%d' % self.sequence)
        return contours.prepare_contour(manifest, 'source', value or recipe(), out)

    def test_source_iou_refines_measurement_without_changing_the_gate(self):
        value = recipe()
        value['curve_fit'].update(minimum_iou=.98, smoothing_rms_mm=.3, biarc_error_mm=.1)
        value['limits']['approximation_tolerance_mm'] = .1
        record = self.prepare(self.manifest(), value)
        self.assert_source_certificate(record)

    def measured_geometry(self, record):
        # Independently reconstruct ORIGINAL cell geometry from committed runs,
        # not source_loops or a source/contour report copied from the fitter.
        from shapely.geometry import Polygon, box
        from shapely.ops import unary_union
        transform = record['pixel_to_mm']
        scale, (ox, oy) = transform['scale_mm_per_pixel'], transform['origin_mm']
        height = record['source_mask']['height']
        cells = [box(ox+a*scale, oy+(height-row-1)*scale,
                     ox+b*scale, oy+(height-row)*scale)
                 for row, runs in enumerate(record['source_mask']['rows']) for a, b in runs]
        source = unary_union(cells)
        rings, error = contours.flatten_loops(record, .002)
        pieces = []
        for index, loop in enumerate(record['loops']):
            if loop['role'] == 'outer':
                holes = [rings[i] for i, child in enumerate(record['loops'])
                         if child['role'] == 'hole' and child.get('parent') == index]
                pieces.append(Polygon(rings[index], holes))
        candidate = unary_union(pieces)
        return source, candidate, error

    def assert_source_certificate(self, record):
        source, candidate, error = self.measured_geometry(record)
        fit = record['recipe']['curve_fit']
        self.assertTrue(candidate.is_valid)
        self.assertAlmostEqual(candidate.bounds[3]-candidate.bounds[1], 50., delta=.004)
        self.assertLessEqual(source.boundary.hausdorff_distance(candidate.boundary)+error,
                             fit['maximum_error_mm'])
        # Independent chord-error enclosure, not a persisted fitter IoU echo.
        inner, outer = candidate.buffer(-error), candidate.buffer(error)
        iou_lower = source.intersection(inner).area / source.union(outer).area
        self.assertGreaterEqual(iou_lower, fit['minimum_iou'])
        reported = record['reports']['source_boundary_hausdorff_upper_mm']
        self.assertGreaterEqual(reported, source.boundary.hausdorff_distance(candidate.boundary)-error)
        self.assertLessEqual(reported, fit['maximum_error_mm'])
        self.assertLessEqual(record['approximation']['source_deviation_upper_mm'],
                             fit['maximum_error_mm'])
        self.assertGreaterEqual(contours.minimum_radius(record), fit['minimum_radius_mm'])
        self.assertEqual(record['topology']['source'], record['topology']['output'])
        self.assertEqual(contours.validate_contour(copy.deepcopy(record)), record)

    def test_real_original_source_mm_certificate_and_determinism(self):
        manifest = self.manifest()
        first, second = self.prepare(manifest), self.prepare(manifest)
        self.assertEqual(first, second)
        self.assert_source_certificate(first)

    def test_padding_changes_only_source_registration_not_fitted_geometry(self):
        original = self.prepare(self.manifest())
        padded = self.prepare(self.manifest('padded', padded=True))
        for key in ('loops', 'source_loops'):
            self.assertEqual(len(original[key]), len(padded[key]))
            for before, after in zip(original[key], padded[key]):
                self.assertEqual(before['role'], after['role'])
                self.assertEqual(before.get('parent'), after.get('parent'))
                self.assertEqual(len(before['segments']), len(after['segments']))
                for a, b in zip(before['segments'], after['segments']):
                    self.assertEqual(a['kind'], b['kind'])
                    for point in ('p0', 'pm', 'p1'):
                        if point in a:
                            for axis in (0, 1):
                                self.assertAlmostEqual(a[point][axis], b[point][axis], places=8)
        scale = original['pixel_to_mm']['scale_mm_per_pixel']
        self.assertAlmostEqual(scale, padded['pixel_to_mm']['scale_mm_per_pixel'], places=10)
        # Added top17/bottom11 padding moves world-up source pixels +11.
        for axis, pixels in ((0, 13), (1, 11)):
            self.assertAlmostEqual(padded['pixel_to_mm']['origin_mm'][axis],
                original['pixel_to_mm']['origin_mm'][axis]-pixels*scale, places=8)
        self.assert_source_certificate(padded)

    def test_multiple_pieces_share_one_physical_registration(self):
        record = self.prepare(self.manifest('pieces', multiple=True))
        self.assertEqual(record['topology']['source']['components'], 2)
        self.assertEqual(len(record['loops']), 2)
        self.assert_source_certificate(record)
        source, candidate, error = self.measured_geometry(record)
        self.assertEqual(len(source.geoms), 2)
        self.assertEqual(len(candidate.geoms), 2)
        for before, after in zip(sorted(source.geoms, key=lambda g: g.centroid.x),
                                 sorted(candidate.geoms, key=lambda g: g.centroid.x)):
            self.assertLessEqual(before.boundary.hausdorff_distance(after.boundary)+error, 1.5)

    def test_narrow_source_hole_keeps_topology_within_physical_fit_budget(self):
        record = self.prepare(self.manifest('narrow-hole', narrow_slot=True))
        self.assertEqual(record['topology']['source']['holes'], 1)
        self.assertEqual(record['topology']['output']['holes'], 1)
        self.assert_source_certificate(record)

    def test_infeasible_original_source_budget_refuses_without_output(self):
        manifest = self.manifest()
        value = recipe()
        value['curve_fit'].update(maximum_error_mm=1e-8, maximum_fit_passes=1)
        out = self.root / 'refused'
        with self.assertRaises(ValueError):
            contours.prepare_contour(manifest, 'source', value, out)
        self.assertFalse(out.exists())

    def test_rehash_cannot_authorize_uncertified_geometry_or_mm_budget(self):
        record = self.prepare(self.manifest())
        for change in ('geometry', 'budget'):
            bad = copy.deepcopy(record)
            if change == 'geometry':
                for loop in bad['loops']:
                    for segment in loop['segments']:
                        for key in ('p0', 'pm', 'p1'):
                            if key in segment:
                                segment[key][0] += 2.
            else:
                bad['recipe']['curve_fit']['maximum_error_mm'] = 1e-8
            bad['recipe_sha256'] = contours._hash(bad['recipe'])
            bad['record_sha256'] = contours._hash({key: value for key, value in bad.items()
                                                  if key != 'record_sha256'})
            with self.subTest(change=change), self.assertRaises(ValueError):
                contours.validate_contour(bad)


if __name__ == '__main__':
    unittest.main()
