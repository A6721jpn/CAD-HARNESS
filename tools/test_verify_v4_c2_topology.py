"""Independent synthetic paired-adjacency C2 controls; no protected inputs or live calls.

Native geometry cases require CAD_VERIFY_C2_TOPOLOGY_NATIVE=1, numeric dependencies,
and pinned Python 3.11.14 / FreeCAD 1.1.4. Fixtures, raster labeling, nesting and
material-clearance observations are authored here, not imported from the fitter.
This module does not claim the locked stress gate or actual-output checker PASS.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

if __package__:
    from . import cad_verify_v4_contours as contours
    from . import cad_verify_v4_plans as plans
else:
    import cad_verify_v4_contours as contours
    import cad_verify_v4_plans as plans


NUMERIC = all(importlib.util.find_spec(name) is not None
              for name in ('numpy', 'scipy', 'shapely', 'PIL'))
NATIVE = (NUMERIC and os.environ.get('CAD_VERIFY_C2_TOPOLOGY_NATIVE') == '1'
          and sys.version_info[:3] == (3, 11, 14)
          and importlib.util.find_spec('FreeCAD') is not None)
NATIVE_REASON = ('set CAD_VERIFY_C2_TOPOLOGY_NATIVE=1 with numeric dependencies '
                 'under pinned Python 3.11.14 / FreeCAD 1.1.4')


def recipe():
    """Explicit independently authored policy, not a registry/hash echo."""
    return dict(schema='cad-harness.contour-recipe.v4c', profile='c-s1',
        foreground=dict(channel='alpha', polarity='light', threshold=128),
        alpha=dict(policy='ignore'), scale=dict(canonical_height_mm=50., origin_mm=[3., -7.]),
        simplify=dict(allowed=False), rounding=dict(allowed=False),
        curve_fit=dict(method='source_bounded_biarc_v2', maximum_error_mm=1.5,
            minimum_iou=.90, minimum_radius_mm=.25, smoothing_rms_mm=.2,
            sample_spacing_mm=.4, biarc_error_mm=.02, maximum_fit_passes=8),
        limits=dict(max_deviation_mm=1.5, approximation_tolerance_mm=.005),
        topology=dict(components='preserve', holes='preserve', islands='preserve',
            connectivity=dict(foreground=4, background=8, pinch='remove_locally')))


def historical_recipe():
    value = recipe()
    value['topology'].pop('connectivity')
    value['curve_fit'] = dict(method='periodic_cubic_biarc_v1', maximum_error_pixels=1.,
        tangent_span_pixels=4., corner_angle_degrees=60., smoothing_rms_pixels=.2,
        sample_spacing_pixels=1., biarc_error_pixels=.1, maximum_fit_passes=4)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def reclose(record):
    """Bypass digest rejection so tampering must fail semantic admission."""
    record['recipe_sha256'] = digest(record['recipe'])
    record['record_sha256'] = digest({k: v for k, v in record.items() if k != 'record_sha256'})
    return record


class PairedTopologyRecipeAdmission(unittest.TestCase):
    def test_exact_connectivity_is_required_only_by_v2(self):
        for value in (recipe(), historical_recipe()):
            self.assertEqual(plans.validate_document(value, 'contour-recipe'), value)
            self.assertEqual(contours.validate_recipe(value), value)
        invalid = []
        missing = recipe()
        missing['topology'].pop('connectivity')
        invalid.append(missing)
        for field, value in (('foreground', 8), ('background', 4),
                             ('pinch', 'fill'), ('extra', 1), ('foreground', True)):
            bad = recipe()
            bad['topology']['connectivity'][field] = value
            invalid.append(bad)
        for field in ('foreground', 'background', 'pinch'):
            bad = recipe()
            bad['topology']['connectivity'].pop(field)
            invalid.append(bad)
        bad = historical_recipe()
        bad['topology']['connectivity'] = recipe()['topology']['connectivity']
        invalid.append(bad)
        for bad in invalid:
            for validator in (lambda r: plans.validate_document(r, 'contour-recipe'),
                              contours.validate_recipe):
                with self.subTest(policy=bad['topology'], validator=validator):
                    with self.assertRaises(ValueError):
                        validator(bad)

    def test_connectivity_does_not_replace_strict_or_preserve_policies(self):
        strict = recipe()
        strict['topology'].update(components=1, islands='reject')
        self.assertEqual(plans.validate_document(strict, 'contour-recipe'), strict)
        self.assertEqual(contours.validate_recipe(strict), strict)
        for components, islands in ((1, 'preserve'), ('preserve', 'reject')):
            bad = recipe()
            bad['topology'].update(components=components, islands=islands)
            with self.assertRaises(ValueError):
                plans.validate_document(bad, 'contour-recipe')
            with self.assertRaises(ValueError):
                contours.validate_recipe(bad)


def label_cells(mask, foreground, diagonal):
    """Independent row-major flood fill, without scipy or production tracing."""
    height, width = len(mask), len(mask[0])
    labels = [[0] * width for _ in range(height)]
    moves = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    groups = {}
    for row in range(height):
        for col in range(width):
            if mask[row][col] != foreground or labels[row][col]:
                continue
            label = len(groups) + 1
            groups[label] = []
            queue = deque([(row, col)])
            labels[row][col] = label
            while queue:
                r, c = queue.popleft()
                groups[label].append((r, c))
                for dr, dc in moves:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width
                            and mask[rr][cc] == foreground and not labels[rr][cc]):
                        labels[rr][cc] = label
                        queue.append((rr, cc))
    return labels, groups


def adjacency_observations(mask):
    """Source forest derives from two independent adjacency partitions."""
    fg, foreground = label_cells(mask, True, False)
    bg, background = label_cells(mask, False, True)
    height, width = len(mask), len(mask[0])
    exterior = {bg[r][c] for r in range(height) for c in range(width)
                if r in (0, height-1) or c in (0, width-1)}
    if len(exterior) != 1 or 0 in exterior:
        raise AssertionError('fixtures require a transparent image border')
    root = ('hole', exterior.pop())
    graph = {('outer', label): set() for label in foreground}
    graph.update({('hole', label): set() for label in background})
    for label, cells in foreground.items():
        a = ('outer', label)
        for row, col in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row+dr, col+dc
                if 0 <= rr < height and 0 <= cc < width and bg[rr][cc]:
                    b = ('hole', bg[rr][cc])
                    graph[a].add(b)
                    graph[b].add(a)
    seen = {root}
    def visit(node, parent):
        children = []
        for child in sorted(graph[node] - {parent}):
            if child in seen:
                raise AssertionError('source region adjacency is not a forest')
            seen.add(child)
            children.append(visit(child, node))
        return node[0], tuple(sorted(children))
    signature = visit(root, None)[1]
    if seen != set(graph):
        raise AssertionError('unreachable source region')
    contacts = {}
    for row in range(1, height):
        for col in range(1, width):
            nw, ne = fg[row-1][col-1], fg[row-1][col]
            sw, se = fg[row][col-1], fg[row][col]
            if (nw and se and not ne and not sw) or (ne and sw and not nw and not se):
                contacts[(col, height-row)] = sorted({v for v in (nw, ne, sw, se) if v})
    return foreground, signature, contacts, len(background)-1


def loop_forest(loops):
    children = {i: [] for i in range(len(loops))}
    roots = []
    for i, loop in enumerate(loops):
        parent = loop.get('parent')
        if parent is None:
            roots.append(i)
        else:
            if type(parent) is not int or not 0 <= parent < i:
                raise AssertionError('invalid immediate parent')
            if loops[parent]['role'] == loop['role']:
                raise AssertionError('nonalternating forest')
            children[parent].append(i)
    def visit(index):
        return loops[index]['role'], tuple(sorted(visit(i) for i in children[index]))
    return tuple(sorted(visit(i) for i in roots))


@unittest.skipUnless(NATIVE, NATIVE_REASON)
class PairedTopologyNativeGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import FreeCAD as App
        if tuple(App.Version()[:3]) != ('1', '1', '4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='cad-c2-paired-topology-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sequence = 0

    def fixture(self, name):
        size = 192 if name == 'singleton' else 160
        if name == 'chain':
            size = 384
        def material(row, col):
            if name == 'diagonal':
                return ((12 <= row < 64 and 12 <= col < 64)
                        or (64 <= row < 136 and 64 <= col < 136))
            if name == 'chain':
                return ((40 <= row < 340 and 40 <= col < 340)
                        or (row, col) in ((38, 38), (39, 39)))
            if name == 'singleton':
                return ((col+.5-90)**2+(row+.5-96)**2 <= 76**2
                        or (row, col) == (96, 169))
            if name == 'pinched-hole':
                return (12 <= row < 148 and 12 <= col < 148
                        and not ((40 <= row < 72 and 40 <= col < 72)
                                 or (72 <= row < 108 and 72 <= col < 108)))
            if name == 'nested':
                return ((8 <= row < 152 and 8 <= col < 152
                         and not (28 <= row < 132 and 28 <= col < 132))
                        or (48 <= row < 112 and 48 <= col < 112
                            and not (62 <= row < 98 and 62 <= col < 98))
                        or (72 <= row < 88 and 72 <= col < 88))
            raise AssertionError('unknown synthetic fixture')
        return [[material(row, col) for col in range(size)] for row in range(size)]

    def prepare(self, mask, value=None):
        from PIL import Image
        self.sequence += 1
        image = Image.new('RGBA', (len(mask[0]), len(mask)))
        # Opaque and transparent cells deliberately have unrelated colored RGB.
        image.putdata([(19+(col % 31), 213-(row % 47), 93,
                        255 if mask[row][col] else 0)
                       for row in range(len(mask)) for col in range(len(mask[0]))])
        path = self.root / ('fixture-%d.png' % self.sequence)
        image.save(path)
        manifest = self.root / ('manifest-%d.json' % self.sequence)
        manifest.write_text(json.dumps(dict(schema='cad-harness.inputs.v4c', profile='c-s1',
            evidence_mode='independent_dev', assets={'source': dict(kind='image', role='checker',
                path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size)})), encoding='utf-8')
        return contours.prepare_contour(manifest, 'source', value or recipe(),
                                        self.root / ('prepared-%d' % self.sequence))

    def observe(self, mask, record):
        from shapely.geometry import LineString, Polygon, box
        from shapely.ops import unary_union
        labels, signature, contacts, holes = adjacency_observations(mask)
        transform = record['pixel_to_mm']
        scale, (ox, oy) = transform['scale_mm_per_pixel'], transform['origin_mm']
        height = len(mask)
        def cell(row, col):
            return box(ox+col*scale, oy+(height-row-1)*scale,
                       ox+(col+1)*scale, oy+(height-row)*scale)
        source_pieces = {label: unary_union([cell(row, col) for row, col in cells])
                         for label, cells in labels.items()}
        source = unary_union(list(source_pieces.values()))
        rings, error = contours.flatten_loops(record, .001)
        ring_polygons = [Polygon(ring) for ring in rings]
        boundaries = [LineString(ring) for ring in rings]
        for i, polygon in enumerate(ring_polygons):
            self.assertTrue(polygon.is_valid)
            self.assertTrue(boundaries[i].is_simple)
            for j in range(i):
                self.assertGreater(boundaries[i].distance(boundaries[j]), 2*error)
            containers = [j for j, other in enumerate(ring_polygons)
                          if j != i and other.contains(polygon)]
            parent = min(containers, key=lambda j: ring_polygons[j].area) if containers else None
            self.assertEqual(record['loops'][i].get('parent'), parent)
        pieces = [Polygon(rings[i], [rings[j] for j, loop in enumerate(record['loops'])
                  if loop['role'] == 'hole' and loop.get('parent') == i])
                  for i, loop in enumerate(record['loops']) if loop['role'] == 'outer']
        candidate = unary_union(pieces)
        self.assertTrue(candidate.is_valid)
        self.assertEqual(len(pieces), len(labels))
        for i, piece in enumerate(pieces):
            self.assertGreater(piece.area, 0.)
            for earlier in pieces[:i]:
                self.assertGreater(piece.distance(earlier), 2*error)
        labels_in_order = sorted(source_pieces)
        edges = {}
        for label, original in source_pieces.items():
            overlaps = [original.intersection(piece).area for piece in pieces]
            edges[label] = sorted((i for i, piece in enumerate(pieces)
                if overlaps[i] > 0 and
                original.boundary.hausdorff_distance(piece.boundary)+error <= 1.5),
                key=lambda i: (-overlaps[i], i))
        def assign(position, used):
            if position == len(labels_in_order):
                return {}
            label = labels_in_order[position]
            for index in edges[label]:
                if index not in used:
                    remainder = assign(position+1, used | {index})
                    if remainder is not None:
                        return {label: index, **remainder}
            return None
        matching = assign(0, set())
        self.assertIsNotNone(matching, 'every original piece needs a distinct overlapping bounded output')
        correspondence = matching
        self.assertEqual(loop_forest(record['source_loops']), signature)
        self.assertEqual(loop_forest(record['loops']), signature)
        expected = dict(components=len(labels), holes=holes,
                        euler_characteristic=len(labels)-holes)
        self.assertEqual(record['topology'], dict(source=expected, output=expected))
        self.assertAlmostEqual(candidate.bounds[3]-candidate.bounds[1], 50., delta=.002)
        self.assertAlmostEqual(candidate.bounds[0], 3., delta=.002)
        self.assertAlmostEqual(candidate.bounds[1], -7., delta=.002)
        exact_bounds = contours.geometry_bounds(record)
        self.assertAlmostEqual(exact_bounds[3]-exact_bounds[2], 50., places=9)
        self.assertGreaterEqual(contours.minimum_radius(record), .25)
        self.assertLessEqual(source.boundary.hausdorff_distance(candidate.boundary)+error, 1.5)
        # These envelopes bound chord error for observation ONLY, never repair geometry.
        inner, outer = candidate.buffer(-error), candidate.buffer(error)
        self.assertGreaterEqual(source.intersection(inner).area/source.union(outer).area, .90)
        self.assertLessEqual(record['reports']['source_boundary_hausdorff_upper_mm'], 1.5)
        source_lines = []
        for loop in record['source_loops']:
            for segment in loop['segments']:
                self.assertEqual(segment['kind'], 'line')
                source_lines.append(LineString([segment['p0'], segment['p1']]))
        source_boundary = unary_union(source_lines)
        self.assertLessEqual(source.boundary.hausdorff_distance(source_boundary), 1e-8)
        committed = [[False] * len(mask[0]) for _ in mask]
        for row, runs in enumerate(record['source_mask']['rows']):
            for start, stop in runs:
                committed[row][start:stop] = [True] * (stop-start)
        self.assertEqual(committed, mask)
        self.assertEqual(record['source_mask']['height'], len(mask))
        self.assertEqual(record['source_mask']['width'], len(mask[0]))
        reports = record['reports']['pinch_openings']
        self.assertEqual(len(reports), len(contacts))
        self.assertEqual({tuple(item['vertex_pixels']): item['incident_components']
                          for item in reports}, contacts)
        from shapely.geometry import Point
        for item in reports:
            self.assertEqual(set(item), {'vertex_pixels', 'incident_components', 'clearance_mm_lower'})
            self.assertEqual(item['incident_components'], sorted(set(item['incident_components'])))
            self.assertTrue(all(type(label) is int and label > 0 for label in item['incident_components']))
            x, y = item['vertex_pixels']
            self.assertTrue(type(x) is int and type(y) is int)
            point = Point(ox+x*scale, oy+y*scale)
            self.assertFalse(candidate.covers(point))
            distance = candidate.distance(point)
            self.assertGreater(distance-error, 0.)
            clearance = item['clearance_mm_lower']
            self.assertTrue(math.isfinite(clearance))
            self.assertGreater(clearance, 0.)
            self.assertLessEqual(clearance, distance+error)
        self.assertEqual(plans.validate_document(record, 'contour'), record)
        self.assertEqual(contours.validate_contour(copy.deepcopy(record)), record)
        return source_pieces, pieces, correspondence, candidate

    def test_diagonal_squares_are_retained_with_original_contact_cleared(self):
        mask = self.fixture('diagonal')
        record = self.prepare(mask)
        self.observe(mask, record)
        self.assertEqual(record['topology']['source']['components'], 2)
        self.assertEqual(len(record['reports']['pinch_openings']), 1)
        self.assertEqual(len(record['reports']['pinch_openings'][0]['incident_components']), 2)

    def test_sub_radius_singleton_near_body_survives_bounded_outward_fit(self):
        mask = self.fixture('singleton')
        record = self.prepare(mask)
        source, pieces, correspondence, _ = self.observe(mask, record)
        smallest = min(source, key=lambda label: source[label].area)
        self.assertLess(source[smallest].area, math.pi*.25**2)
        self.assertGreater(pieces[correspondence[smallest]].area, source[smallest].area)
        self.assertEqual(record['reports']['pinch_openings'], [])

    def test_adjacent_singletons_grow_separately_and_keep_padding_invariance(self):
        mask = self.fixture('chain')
        record = self.prepare(mask)
        source, pieces, correspondence, material = self.observe(mask, record)
        self.assertEqual(len(pieces), 3)
        for label, original in source.items():
            if original.area < math.pi*.25**2:
                self.assertGreater(pieces[correspondence[label]].area, original.area)
        padded = [[False] * (len(mask[0])+17) for _ in range(len(mask)+21)]
        for row, cells in enumerate(mask):
            padded[row+8][6:6+len(cells)] = cells
        shifted = self.prepare(padded)
        other = self.observe(padded, shifted)[3]
        self.assertLessEqual(material.boundary.hausdorff_distance(other.boundary), 1e-8)

    def test_diagonally_connected_background_is_one_pinched_hole(self):
        mask = self.fixture('pinched-hole')
        record = self.prepare(mask)
        self.observe(mask, record)
        self.assertEqual(record['topology']['source']['holes'], 1)
        self.assertEqual(len(record['reports']['pinch_openings']), 1)
        self.assertEqual(len(record['reports']['pinch_openings'][0]['incident_components']), 1)

    def test_nested_islands_keep_full_alternating_adjacency_forest(self):
        mask = self.fixture('nested')
        record = self.prepare(mask)
        self.observe(mask, record)
        self.assertEqual(record['topology']['source']['components'], 3)
        self.assertEqual(record['topology']['source']['holes'], 2)
        self.assertEqual(record['reports']['pinch_openings'], [])

    def test_padding_changes_registration_not_material_or_clearance(self):
        mask = self.fixture('diagonal')
        padded = [[False] * (len(mask[0])+19) for _ in range(len(mask)+23)]
        for row, cells in enumerate(mask):
            padded[row+9][7:7+len(cells)] = cells
        original, shifted = self.prepare(mask), self.prepare(padded)
        a = self.observe(mask, original)[3]
        b = self.observe(padded, shifted)[3]
        self.assertLessEqual(a.boundary.hausdorff_distance(b.boundary), 1e-8)
        scale = original['pixel_to_mm']['scale_mm_per_pixel']
        self.assertAlmostEqual(scale, shifted['pixel_to_mm']['scale_mm_per_pixel'], places=10)
        for axis, pixels in ((0, 7), (1, 14)):
            self.assertAlmostEqual(shifted['pixel_to_mm']['origin_mm'][axis],
                original['pixel_to_mm']['origin_mm'][axis]-pixels*scale, places=8)
        old, new = original['reports']['pinch_openings'][0], shifted['reports']['pinch_openings'][0]
        self.assertEqual(new['vertex_pixels'], [old['vertex_pixels'][0]+7, old['vertex_pixels'][1]+14])
        self.assertAlmostEqual(old['clearance_mm_lower'], new['clearance_mm_lower'], places=8)

    def assert_tamper_rejected(self, record, mutations):
        for name, mutate in mutations:
            bad = copy.deepcopy(record)
            mutate(bad)
            reclose(bad)
            with self.subTest(tamper=name), self.assertRaises(ValueError):
                contours.validate_contour(bad)

    def test_reclosed_contact_reports_cannot_authorize_unsafe_material(self):
        record = self.prepare(self.fixture('diagonal'))
        def contact_field(field, value):
            return lambda r: r['reports']['pinch_openings'][0].update({field: value})
        self.assert_tamper_rejected(record, [
            ('missing report', lambda r: r['reports'].pop('pinch_openings')),
            ('omitted contact', lambda r: r['reports'].update(pinch_openings=[])),
            ('duplicate contact', lambda r: r['reports']['pinch_openings'].append(
                copy.deepcopy(r['reports']['pinch_openings'][0]))),
            ('zero clearance', contact_field('clearance_mm_lower', 0.)),
            ('overstated clearance', contact_field('clearance_mm_lower', 1000000.)),
            ('unreported vertex', contact_field('vertex_pixels', [1, 1])),
            ('invented component', contact_field('incident_components', [999])),
            ('unsorted labels', lambda r: r['reports']['pinch_openings'][0]['incident_components'].reverse()),
            ('contact restored in final material', lambda r: r.update(loops=copy.deepcopy(r['source_loops']))),
            ('piece dropped', lambda r: r['loops'].pop()),
            ('frame changed', lambda r: r['pixel_to_mm']['origin_mm'].__setitem__(0, 4.))])

    def test_reclosed_same_counts_cannot_replace_nested_forest(self):
        record = self.prepare(self.fixture('nested'))
        island = next(i for i, loop in enumerate(record['loops'])
                      if loop['role'] == 'outer' and loop.get('parent') is not None)
        self.assert_tamper_rejected(record, [
            ('island made root', lambda r: r['loops'][island].pop('parent')),
            ('source forest changed', lambda r: r['source_loops'][island].pop('parent')),
            ('fabricated no-contact report', lambda r: r['reports'].update(pinch_openings=[dict(
                vertex_pixels=[1, 1], incident_components=[1], clearance_mm_lower=.1)]))])

    def test_v1_still_refuses_diagonal_source_contacts(self):
        with self.assertRaises(ValueError):
            self.prepare(self.fixture('diagonal'), historical_recipe())


if __name__ == '__main__':
    unittest.main()
