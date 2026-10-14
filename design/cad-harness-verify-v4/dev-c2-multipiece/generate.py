"""Independent ring, nested material island and separated disk native evidence.

Run --out NEW_DIRECTORY using pinned FreeCAD Python. No live calls or fallback.
"""
from __future__ import annotations
import argparse
import importlib.util
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import cad_verify_v4_ledger as ledger

_spec = importlib.util.spec_from_file_location('c2_independent_source_utilities',
    Path(__file__).resolve().parents[1]/'dev-c2-production/generate.py')
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
DEV_CONTROLS = base.DEV_CONTROLS


def author_sources(out):
    import numpy as np
    from PIL import Image
    out = Path(out)
    rows, cols = np.indices((160, 160))
    rgb = np.stack(((17*cols+3*rows)%256, (11*rows+5*cols)%256,
                    (cols+23*rows)%256), axis=-1).astype(np.uint8)
    def predicate(x, y):
        main = (x-64)**2+(y-84)**2
        return ((main <= 36**2) & (main >= 18**2)) | (main <= 8**2) | ((x-116)**2+(y-36)**2 <= 12**2)
    count = np.zeros((160, 160), dtype=np.uint16)
    for iy in range(8):
        for ix in range(8):
            count += predicate(cols+(ix+.5)/8, rows+(iy+.5)/8)
    alpha = ((count.astype(np.uint32)*255+32)//64).astype(np.uint8)
    rgba = np.concatenate((rgb, alpha[:, :, None]), axis=-1)
    paths = {}
    def save(name, value):
        path = out/(name+'.png')
        Image.fromarray(value, 'RGBA').save(path)
        paths[name] = path
    save('ring', rgba)
    invisible = rgba.copy()
    invisible[alpha == 0, :3] = 255-invisible[alpha == 0, :3]
    save('invisible_rgb', invisible)
    padded = np.zeros((192, 208, 4), dtype=np.uint8)
    padded[:, :, :3] = [251, 19, 103]
    padded[11:171, 23:183] = rgba
    save('padded_ring', padded)
    sharp = rgba.copy()
    sharp[8:12, 8:12, 3] = 255
    save('small_sharp', sharp)
    return paths


def build_bare(doc):
    """Three ordinary CPP Sketcher/Pad bodies linked by a CPP compound."""
    import FreeCAD as App
    import Part
    import Sketcher
    bodies, pads = [], []
    for name, center, radii in (
        ('Annulus', (18.75, 18.75), (18.75, 9.375)),
        ('NestedIsland', (18.75, 18.75), (25/6,)),
        ('SeparatedDisk', (275/6, 43.75), (6.25,))):
        body = doc.addObject('PartDesign::Body', name)
        sketch = body.newObject('Sketcher::SketchObject', name+'Circles')
        for radius in radii:
            index = sketch.addGeometry(Part.Circle(App.Vector(*center, 0), App.Vector(0, 0, 1), radius), False)
            sketch.addConstraint(Sketcher.Constraint('Block', index))
        pad = body.newObject('PartDesign::Pad', name+'Pad')
        pad.Profile, pad.Length = sketch, 3.
        body.Tip = pad
        bodies.append(body)
        pads.append(pad)
    compound = doc.addObject('Part::Compound', 'IndependentMultipiece')
    compound.Links = bodies
    doc.recompute()
    return compound, [dict(kind='scalar', object=pad.Name, property='Length', delta=.01) for pad in pads]


def _save(doc, output, out, probes):
    out = ledger.new_directory(out)
    doc.recompute()
    shape = output.Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 3 or shape.Volume <= 0:
        raise ValueError('independent_dev_invalid_three_piece_native_output')
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
            extensions[cls.__module__] = dict(module=cls.__module__, **base._record(Path(source).absolute()))
    bundle = dict(schema='cad-harness.artifact-bundle.v4', profile='c-s1', evidence_mode='independent_dev',
        native=base._record(native), step=base._record(step), output_object=output.Name,
        probes=probes, extensions=list(extensions.values()))
    path = out/'artifacts.json'
    ledger.write_json(path, bundle)
    return path


def generate(out):
    App = base._native()
    from tools import cad_verify_v4_s1 as facade
    from tools import cad_verify_v4_c2_recipe as registry
    from tools import cad_verify_v4_contours as contours
    from tools import cad_verify_v4_compile as compiler
    from tools import cad_verify_v4_plans as plans
    out = ledger.new_directory(facade.safe_path(out))
    production = registry.load()
    sources = author_sources(out)
    manifest = base.write_manifest(out, sources)
    contour = contours.prepare_contour(manifest, 'ring', production['recipe'], out/'production-contour')
    if contour['topology']['source']['components'] != 3:
        raise ValueError('independent_source_requires_three_components')
    prepared = out/'prepared.json'
    packet = dict(schema='cad-harness.prepared.v4c', profile='c-s1',
        source_manifest_sha256=ledger.file_sha(manifest), assets={'ring': contour})
    ledger.write_json(prepared, packet)
    card, context = out/'card.json', out/'context.json'
    card_value = base._card(contour)
    plans.validate_judge_card(card_value, profile='c-s1')
    ledger.write_json(card, card_value)
    ledger.write_json(context, dict(schema='cad-harness.artifact-context.v4', profile='c-s1', family='C2',
        manifest_sha256=ledger.file_sha(manifest), prepared_sha256=ledger.file_sha(prepared),
        card_sha256=ledger.file_sha(card), reference=None, engravings=[],
        contour=dict(contour_id='ring', scale=1., origin_mm=[0, 0, 0], thickness_mm=3.)))
    plan = dict(schema='cad-harness.plan.v4c', profile='c-s1', family='contour_extrude',
        contour_id='ring', width_mm=contour['nominal_width_mm'], thickness_mm=3.,
        origin_mm=[0, 0, 0], references=[], engravings=[])
    plans.validate_plan(plan, manifest, packet, profile='c-s1')
    ledger.write_json(out/'harness-plan.json', plan)
    ledger.write_json(out/'expected.json', dict(evidence_mode='independent_dev',
        source_authoring=dict(canvas_pixels=[160, 160], supersampling=[8, 8],
            annulus_center_pixels=[64, 84], outer_radius_pixels=36, inner_radius_pixels=18,
            island_radius_pixels=8, separated_center_pixels=[116, 36], separated_radius_pixels=12),
        bare_analytic=dict(global_scale_mm_per_pixel=50/96, image_y_up_datum_pixels=[28, 40],
            components=3, holes=1, thickness_mm=3.), dev_uncertainty=DEV_CONTROLS,
        production_recipe={key: production[key] for key in ('path', 'sha256', 'canonical_sha256')},
        production_registration={key: production['registration'][key] for key in ('path', 'sha256', 'bytes')}))
    bundles = {}
    for arm in ('bare', 'harness'):
        doc = App.newDocument('C2Multipiece'+arm)
        try:
            if arm == 'bare':
                output, probes = build_bare(doc)
            else:
                output = compiler.build_plan(doc, plan, manifest, packet)
                feature = next(obj for obj in doc.Objects if 'Thickness' in obj.PropertiesList
                    and 'Proxy' in obj.PropertiesList and obj.Proxy is not None)
                probes = [dict(kind='scalar', object=feature.Name, property='Thickness', delta=.01)]
            bundles[arm] = str(_save(doc, output, out/arm, probes))
        finally:
            App.closeDocument(doc.Name)
    result = dict(schema='cad-harness.c2-multipiece-fixtures.v4c', evidence_mode='independent_dev', live_calls=0,
        manifest_path=str(manifest), prepared_path=str(prepared), recipe_path=production['path'],
        card_path=str(card), context_path=str(context), bare_bundle_path=bundles['bare'],
        harness_bundle_path=bundles['harness'], fixture_paths={key: str(path) for key, path in sources.items()})
    ledger.write_json(out/'fixtures.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    print(json.dumps(generate(parser.parse_args().out), sort_keys=True))
