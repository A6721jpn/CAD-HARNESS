"""Independent alpha-only C2 sources and paired production-path native evidence.

Run with pinned FreeCAD Python: generate.py --out NEW_DIRECTORY. The bare arm
is an independently specified Sketcher annulus and Pad, never fitted from or
constructed by the harness. Both arms share the actual production preparation,
fixed C-D fidelity card and one immutable neutral measurement registration.
All numerical/area controls below are labelled independent DEV uncertainty,
not user tolerances, manufacturing promises, or pilot-derived settings.
"""
from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import cad_verify_v4_ledger as ledger

DEV_CONTROLS = dict(
    source='independently_selected_dev_uncertainty_not_user_tolerances',
    linear_tolerance_mm=1e-5,
    curve_tolerance_mm=1e-4,
    sampling_step_mm=.02,
    angular_tolerance_rad=1e-6,
    tool_radius_mm=.25,
    maximum_uncovered_mm2=.1,
    area_uncertainty_mm2=1e-5,
    buffer_segments=128,
    require_connected=False,
    connectivity_claim='none; annulus is outside the convex erosion certificate',
    native_bounds_difference_mm=1e-5,
    native_volume_difference_mm3=.01,
)


def _native():
    import FreeCAD as App
    if sys.version_info[:3] != (3, 11, 14) or tuple(App.Version()[:3]) != ('1', '1', '4'):
        raise ValueError('requires_pinned_freecad_python_3_11_14_FreeCAD_1_1_4')
    return App


def _record(path):
    return dict(path=str(path), sha256=ledger.file_sha(path), bytes=path.stat().st_size)


def author_sources(out):
    """Author deterministic RGBA data from independent analytic pixel geometry.

    Eight-by-eight area supersampling is an offline source-authoring convention,
    not a hidden contour fitter. Alpha zero deliberately carries coloured RGB.
    This helper is also used by guarded native tests, without constructing CAD.
    """
    import numpy as np
    from PIL import Image

    out = Path(out)
    rows, cols = np.indices((128, 128))
    rgb = np.stack(((17*cols + 3*rows) % 256,
                    (11*rows + 5*cols) % 256,
                    (cols + 23*rows) % 256), axis=-1).astype(np.uint8)

    def coverage(predicate):
        count = np.zeros((128, 128), dtype=np.uint16)
        for iy in range(8):
            for ix in range(8):
                x, y = cols + (ix+.5)/8, rows + (iy+.5)/8
                count += predicate(x, y)
        return ((count.astype(np.uint32)*255 + 32)//64).astype(np.uint8)

    def save(name, alpha, colour=None):
        rgba = np.empty((*alpha.shape, 4), dtype=np.uint8)
        rgba[:, :, :3] = rgb if colour is None else colour
        rgba[:, :, 3] = alpha
        path = out/(name+'.png')
        Image.fromarray(rgba, 'RGBA').save(path)
        return path, rgba

    paths = {}
    ring_alpha = coverage(lambda x, y: (((x-64)**2 + (y-64)**2 <= 48**2)
                                       & ((x-64)**2 + (y-64)**2 >= 20**2)))
    paths['ring'], ring = save('ring', ring_alpha)
    invisible = ring[:, :, :3].copy()
    invisible[ring_alpha == 0] = 255-invisible[ring_alpha == 0]
    paths['invisible_rgb'], _ = save('invisible-rgb', ring_alpha, invisible)
    paths['ellipse'], _ = save('ellipse', coverage(
        lambda x, y: ((x-64)/44)**2 + ((y-64)/28)**2 <= 1))

    def rounded(x, y):
        qx, qy = np.abs(x-64)-34, np.abs(y-64)-22
        return (np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
                + np.minimum(np.maximum(qx, qy), 0)-10 <= 0)

    paths['rounded_rectangle'], _ = save('rounded-rectangle', coverage(rounded))
    sharp = np.zeros((128, 128), dtype=np.uint8)
    sharp[24:104, 16:112] = 255
    sharp[24:64, 56:72] = 0  # Exact concave and convex right angles, not rounding.
    paths['sharp'], _ = save('sharp', sharp)
    threshold = np.zeros_like(sharp)
    threshold[32:96, 32:96] = 128
    threshold[32:96, 24:32] = 127
    threshold[32:96, 96:104] = 129
    paths['threshold'], _ = save('threshold', threshold)
    paths['empty'], _ = save('empty', np.zeros_like(sharp))
    island = ring_alpha.copy()
    island[2:6, 2:6] = 255
    paths['island'], _ = save('island', island)
    diagonal = np.zeros_like(sharp)
    diagonal[40:48, 40:48] = 255
    diagonal[48:56, 48:56] = 255
    paths['diagonal'], _ = save('diagonal', diagonal)
    padded = np.zeros((160, 176, 4), dtype=np.uint8)
    padded[:, :, :3] = [251, 19, 103]
    padded[11:139, 23:151] = ring
    paths['padded_ring'] = out/'padded-ring.png'
    Image.fromarray(padded, 'RGBA').save(paths['padded_ring'])
    return paths


def write_manifest(out, paths):
    manifest = Path(out)/'manifest.json'
    assets = {key: dict(kind='image', role='checker', **dict(_record(path), path=path.name))
              for key, path in paths.items()}
    ledger.write_json(manifest, dict(schema='cad-harness.inputs.v4c', profile='c-s1',
                                    evidence_mode='independent_dev', assets=assets))
    return manifest


def _card(contour):
    transform = contour['pixel_to_mm']
    scale = transform['scale_mm_per_pixel']
    source_registration = dict(
        origin_mm=[transform['origin_mm'][0],
                   transform['origin_mm'][1]+transform['image_height_pixels']*scale],
        pixel_size_mm=[scale, scale], y_direction=-1)
    criteria = [
        dict(id='solid', metric='solid_valid'),
        dict(id='final_height', metric='unchanged_dimension', axis='Y', expected_mm=50.),
        dict(id='thickness', metric='unchanged_dimension', axis='Z', expected_mm=3.),
        dict(id='actual_min_radius', metric='min_radius', contour_id='ring', minimum_mm=.25,
             angular_tolerance_rad=DEV_CONTROLS['angular_tolerance_rad'], projection_z_mm=1.5),
        dict(id='actual_tool_access', metric='tool_access', contour_id='ring', projection_z_mm=1.5,
             **{key: DEV_CONTROLS[key] for key in ('tool_radius_mm', 'maximum_uncovered_mm2',
                'area_uncertainty_mm2', 'curve_tolerance_mm', 'buffer_segments', 'require_connected')}),
        dict(id='native', metric='native_roundtrip',
             maximum_bounds_difference_mm=DEV_CONTROLS['native_bounds_difference_mm'],
             maximum_volume_difference_mm3=DEV_CONTROLS['native_volume_difference_mm3'],
             require_editable=True),
    ]
    for leg, iou, distance in (('image_to_contour', .90, 1.5), ('contour_to_output', .92, 1.)):
        base = dict(leg=leg, contour_id='ring', curve_tolerance_mm=DEV_CONTROLS['curve_tolerance_mm'])
        if leg == 'image_to_contour':
            base.update(mask_asset_id='ring', registration=source_registration,
                        foreground=dict(channel='alpha', polarity='light', threshold=128, alpha_min=0))
        else:
            base['projection_z_mm'] = 1.5
        criteria.append(dict(base, id=leg+'_iou', metric='image_iou', minimum_iou=iou))
        criteria.append(dict(base, id=leg+'_hausdorff', metric='boundary_hausdorff',
                             maximum_mm=distance, sampling_step_mm=DEV_CONTROLS['sampling_step_mm']))
    return dict(schema='cad-harness.judge-card.v4c', profile='c-s1', source='independent_dev',
                linear_tolerance_mm=DEV_CONTROLS['linear_tolerance_mm'], criteria=criteria)


def build_bare(doc):
    """Ordinary C++ Sketcher+Pad; no harness plan, proxy, or contour input."""
    import FreeCAD as App
    import Part
    import Sketcher

    body = doc.addObject('PartDesign::Body', 'IndependentAnnulus')
    sketch = body.newObject('Sketcher::SketchObject', 'AnalyticCircles')
    for radius in (25., 25.*20/48):
        index = sketch.addGeometry(Part.Circle(App.Vector(25, 25, 0), App.Vector(0, 0, 1), radius), False)
        sketch.addConstraint(Sketcher.Constraint('Block', index))
    pad = body.newObject('PartDesign::Pad', 'OrdinaryPad')
    pad.Profile, pad.Length = sketch, 3.
    body.Tip = pad
    doc.recompute()
    return body


def _save(doc, body, out, probes):
    out = ledger.new_directory(out)
    doc.recompute()
    shape = body.Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError('independent_dev_invalid_native_output')
    native, step = out/'part.FCStd', out/'part.step'
    doc.saveAs(str(native))
    shape.exportStep(str(step))
    extensions = {}
    for obj in doc.Objects:
        if 'Proxy' in obj.PropertiesList and obj.Proxy is not None:
            cls = type(obj.Proxy)
            source = inspect.getsourcefile(cls)
            if source is None:
                raise ValueError('serialized_proxy_source_unavailable')
            extensions[cls.__module__] = dict(module=cls.__module__, **_record(Path(source).absolute()))
    bundle = dict(schema='cad-harness.artifact-bundle.v4', profile='c-s1', evidence_mode='independent_dev',
                  native=_record(native), step=_record(step), output_object=body.Name,
                  probes=probes, extensions=list(extensions.values()))
    path = out/'artifacts.json'
    ledger.write_json(path, bundle)
    return path


def generate(out):
    """Generate a fresh source/preparation and two judge-artifacts-ready bundles."""
    from tools import cad_verify_v4_s1 as facade
    from tools import cad_verify_v4_c2_recipe as registry
    from tools import cad_verify_v4_contours as contours
    from tools import cad_verify_v4_compile as compiler
    from tools import cad_verify_v4_plans as plans

    App = _native()
    out = ledger.new_directory(facade.safe_path(out))
    production = registry.load()
    sources = author_sources(out)
    manifest = write_manifest(out, sources)
    # This MUST use actual production preparation. No analytic contour fallback.
    contour = contours.prepare_contour(manifest, 'ring', production['recipe'], out/'production-contour')
    prepared = out/'prepared.json'
    ledger.write_json(prepared, dict(schema='cad-harness.prepared.v4c', profile='c-s1',
                                    source_manifest_sha256=ledger.file_sha(manifest), assets={'ring': contour}))
    card, context = out/'card.json', out/'context.json'
    card_value = _card(contour)
    plans.validate_judge_card(card_value, profile='c-s1')
    ledger.write_json(card, card_value)
    ledger.write_json(context, dict(schema='cad-harness.artifact-context.v4', profile='c-s1', family='C2',
        manifest_sha256=ledger.file_sha(manifest), prepared_sha256=ledger.file_sha(prepared),
        card_sha256=ledger.file_sha(card), reference=None, engravings=[],
        contour=dict(contour_id='ring', scale=1., origin_mm=[0, 0, 0], thickness_mm=3.)))
    plan = dict(schema='cad-harness.plan.v4c', profile='c-s1', family='contour_extrude',
                contour_id='ring', width_mm=contour['nominal_width_mm'], thickness_mm=3.,
                origin_mm=[0, 0, 0], references=[], engravings=[])
    packet = ledger.read_json(prepared)
    plans.validate_plan(plan, manifest, packet, profile='c-s1')
    ledger.write_json(out/'harness-plan.json', plan)
    ledger.write_json(out/'expected.json', dict(
        evidence_mode='independent_dev', source_authoring=dict(canvas_pixels=[128, 128],
        supersampling=[8, 8], annulus_center_pixels=[64, 64], outer_radius_pixels=48,
        inner_radius_pixels=20, rgb_under_zero_alpha='deliberately coloured; semantically ignored'),
        bare_analytic=dict(center_mm=[25, 25], outer_radius_mm=25., inner_radius_mm=25.*20/48,
                           thickness_mm=3.),
        fixed_C_D_fidelity=dict(image_to_contour=dict(minimum_iou=.90, maximum_hausdorff_mm=1.5),
                               contour_to_output=dict(minimum_iou=.92, maximum_hausdorff_mm=1.)),
        dev_uncertainty=DEV_CONTROLS,
        production_recipe=dict(path=production['path'], sha256=production['sha256'],
                               canonical_sha256=production['canonical_sha256']),
        production_registration={key: production['registration'][key] for key in ('path', 'sha256', 'bytes')}))
    bundles = {}
    for arm in ('bare', 'harness'):
        doc = App.newDocument('C2Production'+arm)
        try:
            if arm == 'bare':
                body, probes = build_bare(doc), []
            else:
                body = compiler.build_plan(doc, plan, manifest, packet)
                feature = next(obj for obj in doc.Objects if 'Thickness' in obj.PropertiesList
                               and 'Proxy' in obj.PropertiesList and obj.Proxy is not None)
                probes = [dict(kind='scalar', object=feature.Name, property='Thickness', delta=.01)]
            bundles[arm] = str(_save(doc, body, out/arm, probes))
        finally:
            App.closeDocument(doc.Name)
    result = dict(schema='cad-harness.c2-production-fixtures.v4c', evidence_mode='independent_dev', live_calls=0,
                  manifest_path=str(manifest), prepared_path=str(prepared), recipe_path=production['path'],
                  card_path=str(card), context_path=str(context), bare_bundle_path=bundles['bare'],
                  harness_bundle_path=bundles['harness'], fixture_paths={key: str(path) for key, path in sources.items()})
    ledger.write_json(out/'fixtures.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    print(json.dumps(generate(parser.parse_args().out), sort_keys=True))
