"""Independent host declaration/hash/projection controls; no CAD or model calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools import cad_verify_v4_c2_recipe as production
from tools import cad_verify_v4_inputs as inputs
from tools import cad_verify_v4_ledger as ledger
from tools import cad_verify_v4_plans as plans


def square(x, y, size, role='outer', parent=None):
    points = [[x, y], [x + size, y], [x + size, y + size], [x, y + size]]
    result = dict(role=role, segments=[dict(kind='line', p0=p, p1=points[(i + 1) % 4])
                                      for i, p in enumerate(points)])
    if parent is not None:
        result['parent'] = parent
    return result


def record():
    # This synthetic host record is not a v2 source-fit certificate.
    recipe = ledger.read_json(
        production.ROOT / 'design/cad-harness-verify-v4/c2-production-recipe-cycle2.json')
    loops = [square(0, 0, 30), square(5, 5, 20, 'hole', 0),
             square(10, 10, 5, parent=1), square(40, 40, 10)]
    topology = dict(components=3, holes=1, euler_characteristic=2)
    result = dict(schema='cad-harness.contour.v4c', profile='c-s1', asset_id='image',
        source_image_sha256='a' * 64, source_manifest_sha256='b' * 64,
        decoded_rgba_sha256='c' * 64, mask_sha256='d' * 64, recipe_sha256='e' * 64,
        record_sha256='f' * 64, units='mm', bounds_mm=[0, 50, 0, 50], nominal_width_mm=50,
        pixel_to_mm=dict(scale_mm_per_pixel=1, origin_mm=[0, 0], image_height_pixels=50,
            y_axis='up', pixel_convention='closed unit cells; centers at (col+0.5,row+0.5)'),
        loops=loops, source_loops=copy.deepcopy(loops),
        source_mask=dict(width=50, height=50, encoding='row-runs', rows=[[[0, 30]]]),
        recipe=recipe, topology=dict(source=copy.deepcopy(topology), output=copy.deepcopy(topology)),
        reports=dict(minimum_radius_mm=0, source_boundary_hausdorff_upper_mm=0),
        provenance={key: 'independent host fixture' for key in ('decoder', 'luminance',
            'threshold_comparison', 'extraction', 'simplification', 'rounding', 'hash_encoding', 'source_checks')},
        approximation=dict(flatten_tolerance_mm=.01, flatten_error_bound_mm=0,
            source_deviation_upper_mm=0, deviation_method='independent host fixture'))
    return result


def rehash(value):
    value['recipe_sha256'] = inputs.canonical_sha(value['recipe'])
    value['mask_sha256'] = inputs.canonical_sha(value['source_mask'])
    value['record_sha256'] = inputs.canonical_sha({k: v for k, v in value.items() if k != 'record_sha256'})


class MultiPieceHostTests(unittest.TestCase):
    def test_declared_source_count_and_model_projection(self):
        value = record()
        self.assertEqual(inputs.contour_solid_count(value), 3)
        packet = dict(schema='cad-harness.prepared.v4c', profile='c-s1',
                      source_manifest_sha256='b' * 64, assets={'image': value})
        projection = inputs.model_inputs(packet)['assets']['image']
        self.assertEqual(projection['loops'], value['loops'])
        self.assertEqual(projection['topology'], value['topology'])
        self.assertNotIn('recipe', projection)

    def test_fake_counts_and_invalid_hierarchies_reject(self):
        mutations = [lambda r: r['topology']['source'].update(components=4),
                     lambda r: r['topology']['output'].update(components=True),
                     lambda r: r['loops'][2].update(parent=0),
                     lambda r: r['loops'][1].update(parent=2),
                     lambda r: r['loops'][3].update(parent=2),
                     lambda r: r['recipe']['topology'].update(components=3),
                     lambda r: r['recipe']['topology'].update(islands='reject')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = record()
                mutation(value)
                with self.assertRaises(ValueError):
                    inputs.contour_solid_count(value)
        for value in (None, {}, {'schema': 'cad-harness.step-facts.v4c'}):
            with self.assertRaises(ValueError):
                inputs.contour_solid_count(value)

    def test_strict_raster_and_analytic_stay_single(self):
        value = record()
        value['recipe']['topology'] = dict(components=1, holes='preserve', islands='reject')
        with self.assertRaises(ValueError):
            inputs.contour_solid_count(value)
        value['loops'] = value['loops'][:2]
        value['source_loops'] = copy.deepcopy(value['loops'])
        counts = dict(components=1, holes=1, euler_characteristic=0)
        value['topology'] = dict(source=counts, output=copy.deepcopy(counts))
        self.assertEqual(inputs.contour_solid_count(value), 1)
        analytic = {key: copy.deepcopy(value[key]) for key in ('schema', 'profile', 'asset_id',
            'units', 'bounds_mm', 'nominal_width_mm', 'loops', 'pixel_to_mm', 'source_image_sha256')}
        analytic.update(source_sha256='a' * 64, source_image_asset_id='image',
                        topology=dict(components=1, holes=1), provenance=dict(kind='independent_analytic_source'))
        self.assertEqual(inputs.contour_solid_count(analytic), 1)
        analytic['loops'].append(square(40, 40, 10))
        analytic['topology']['components'] = 2
        with self.assertRaises(ValueError):
            inputs.contour_solid_count(analytic)

    def test_hash_closed_prepared_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / 'independent.png'
            image.write_bytes(b'\x89PNG\r\n\x1a\nindependent host signature fixture')
            manifest = root / 'inputs.json'
            manifest.write_text(json.dumps(dict(schema='cad-harness.inputs.v4c', profile='c-s1',
                evidence_mode='independent_dev', assets={'image': dict(kind='image', role='checker', path=image.name,
                    sha256=ledger.file_sha(image), bytes=image.stat().st_size)})), encoding='utf-8')
            value = record()
            value.update(source_image_sha256=ledger.file_sha(image), source_manifest_sha256=ledger.file_sha(manifest))
            rehash(value)
            packet = dict(schema='cad-harness.prepared.v4c', profile='c-s1',
                          source_manifest_sha256=ledger.file_sha(manifest), assets={'image': value})
            self.assertEqual(inputs.contour_solid_count(inputs.verify_prepared(packet, manifest)['assets']['image']), 3)
            value['loops'][3]['segments'][0]['p0'][0] += 1
            with self.assertRaisesRegex(ValueError, 'prepared_contour_record_mismatch'):
                inputs.verify_prepared(packet, manifest)



if __name__ == '__main__':
    unittest.main()
