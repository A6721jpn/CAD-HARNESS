"""Independent analytical S3 development shapes/cards; no pilot/holdout input.

Source graphs use author-chosen polynomial coefficients and exact Bernstein
conversion. They are constructed without importing the reconstruction/judges.
The non-G2 pair has a known nonzero second-jet jump but unchanged position/first
jet. The four-cell case independently exercises both grid directions.
"""
import argparse
import copy
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import cad_verify_v4_ledger as ledger


WIDTH_PER_CELL = 14.0
LENGTH_PER_CELL = 18.0
DEPTH = 9.0
BUMP = 0.48


def polynomial_coefficients(i, j, v_cells, bump):
    """z=4+.12U²+.035UV+.08V² + bump*(U-1)²*V²*(H-V)² on right cells."""
    coefficients = {(0, 0): 4 + .12*i*i + .035*i*j + .08*j*j,
        (1, 0): .24*i + .035*j, (2, 0): .12,
        (0, 1): .035*i + .16*j, (1, 1): .035, (0, 2): .08}
    if i == 1 and bump:
        for degree, coefficient in ((2, v_cells**2), (3, -2*v_cells), (4, 1)):
            for power in range(degree + 1):
                key = (2, power)
                coefficients[key] = coefficients.get(key, 0.) + bump*coefficient*math.comb(degree, power)*j**(degree-power)
    return coefficients


def roof_patch(i, j=0, v_cells=1, bump=BUMP, reverse_u=False, swap_uv=False):
    import FreeCAD as App
    import Part
    pu, pv = 3, 4
    coefficients = polynomial_coefficients(i, j, v_cells, bump)
    poles = []
    for a in range(pu + 1):
        row = []
        for b in range(pv + 1):
            z = sum(value*math.comb(a, u)/math.comb(pu, u)*math.comb(b, v)/math.comb(pv, v)
                    for (u, v), value in coefficients.items() if u <= a and v <= b)
            row.append(App.Vector(WIDTH_PER_CELL*(i + a/pu), LENGTH_PER_CELL*(j + b/pv), z))
        poles.append(row)
    if reverse_u:
        poles.reverse()
    if swap_uv:
        poles = [list(row) for row in zip(*poles)]
        pu, pv = pv, pu
    surface = Part.BSplineSurface()
    surface.buildFromPolesMultsKnots(poles, [pu + 1, pu + 1], [pv + 1, pv + 1],
                                   [0., 1.], [0., 1.], False, False, pu, pv)
    face = surface.toShape()
    if face.normalAt(.5, .5).z < 0:
        face.reverse()
    return face


def roof_solid(v_cells=1, bump=BUMP, reparameterized=False):
    import FreeCAD as App
    solids = []
    for i in range(2):
        for j in range(v_cells):
            face = roof_patch(i, j, v_cells, bump, reverse_u=reparameterized and i == 1,
                              swap_uv=reparameterized and i == 1)
            solids.append(face.extrude(App.Vector(0, 0, -DEPTH)))
    result = solids[0]
    for solid in solids[1:]:
        result = result.fuse(solid)
    if result.Volume < 0:
        result.reverse()
    if result.isNull() or not result.isValid() or len(result.Solids) != 1 or result.Volume <= 0:
        raise ValueError('independent_roof_source_invalid')
    return result


def _safe_output(value):
    inputs = __import__('cad_verify_v4_inputs')
    path = Path(value).absolute()
    inputs._lexical(path)
    for ancestor in (path, *path.parents):
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            continue
        if ancestor.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('fixture_output_link_or_reparse_point')
    return ledger.new_directory(path)


def _selection(face, reverse=False, swap=False):
    return dict(face_id=face['id'], signature=face['signature'],
                adjacent_face_ids=copy.deepcopy(face['adjacent_face_ids']),
                swap_uv=swap, reverse_u=reverse, reverse_v=False)


def _card(v_cells=1):
    # Independent SOURCE Bernstein control hull, not candidate/fitter output.
    # The four-cell perturbation has an interior maximum, so corner heights
    # alone are not an enclosure. Spatial slack only locates the intended
    # roof; actual deviation/continuity still use their separate fixed bounds.
    heights = [p.z for i in range(2) for j in range(v_cells)
               for row in roof_patch(i, j, v_cells).Surface.getPoles() for p in row]
    top_max = max(heights)
    maximum = .08 if v_cells == 1 else .6
    bounds = [0., 28., 0., LENGTH_PER_CELL*v_cells, min(heights), top_max]
    region = [0., 28., 0., LENGTH_PER_CELL*v_cells, 3.8, top_max + maximum + .2]
    patch = dict(bounds_mm=bounds, domain_uv='native_full',
                 chart_uv=[0., 2., 0., float(v_cells)], swap_uv=False, reverse_u=False, reverse_v=False)
    common = dict(output_region_mm=region, selection_tolerance_mm=1.,
                  output_patches=[patch], resources=dict(max_depth=18, max_cells=65536))
    seams = [dict(a=dict(patch=0, axis='u', value=1., range=[0., float(v_cells)], reverse=False),
                  b=dict(patch=0, axis='u', value=1., range=[0., float(v_cells)], reverse=False))]
    if v_cells > 1:
        seams.append(dict(a=dict(patch=0, axis='v', value=1., range=[0., 2.], reverse=False),
                          b=dict(patch=0, axis='v', value=1., range=[0., 2.], reverse=False)))
    # None of these numerical contracts is a user tolerance. The four-cell
    # source is independently more distorted (bump factor up to .48 mm).
    return dict(schema='cad-harness.judge-card.v4c', profile='c-s3', source='independent_dev',
        numerical_uncertainty_mm=1e-5, criteria=[
            dict(id='solid', metric='solid_valid', expected_solids=1),
            dict(id='merge_faces', metric='face_count', scope='full', relation='delta',
                 correspondence='spatial_fixed_frame', expected_delta=1-2*v_cells),
            dict(id='deviation', metric='surface_deviation', maximum_mm=maximum, **copy.deepcopy(common)),
            dict(id='G1', metric='g1_continuity', maximum_position_mm=.0004,
                 maximum_normal_sin=.0002, seams=copy.deepcopy(seams), **copy.deepcopy(common)),
            dict(id='G2', metric='g2_continuity', maximum_position_mm=.0004,
                 maximum_normal_sin=.0002, maximum_curvature_per_mm=.00002,
                 seams=copy.deepcopy(seams), **copy.deepcopy(common)),
            dict(id='native', metric='native_roundtrip', maximum_bounds_difference_mm=.0001,
                 maximum_volume_difference_mm3=.1, require_editable=True)])


def generate(out):
    import FreeCAD as App
    import cad_verify_v4_inputs as inputs
    if sys.version_info[:3] != (3, 11, 14) or tuple(App.Version()[:3]) != ('1', '1', '4'):
        raise ValueError('requires_pinned_freecad_python')
    out = _safe_output(out)
    shapes = {'g1_pair': roof_solid(), 'g2_pair': roof_solid(bump=0.),
              'four_patch': roof_solid(v_cells=2), 'reparameterized_pair': roof_solid(reparameterized=True)}
    assets = {}
    for name, shape in shapes.items():
        path = out / (name + '.step')
        shape.exportStep(str(path))
        assets[name] = dict(kind='step', role='reference', path=path.name, sha256=ledger.file_sha(path), bytes=path.stat().st_size)
    manifest = dict(schema='cad-harness.inputs.v4c', profile='c-s3', evidence_mode='independent_dev', assets=assets)
    ledger.write_json(out / 'manifest.json', manifest)
    recipe = dict(schema='cad-harness.step-recipe.v4c', profile='c-s3', source_axes=['X', 'Y', 'Z'],
                  source_units='mm', signature_precision_mm=1e-6)
    ledger.write_json(out / 'step-recipe.json', recipe)
    prepared = None
    for name in shapes:
        packet = inputs.inspect_step(out / 'manifest.json', name, recipe, out / (name + '-facts.json'))
        if prepared is None:
            prepared = packet
        else:
            prepared['assets'].update(packet['assets'])
    ledger.write_json(out / 'prepared.json', prepared)
    plans = {}
    for name in shapes:
        cells = 2 if name == 'four_patch' else 1
        candidates = [f for f in prepared['assets'][name]['faces']
                      if f['surface_type'] == 'BSplineSurface' and f['normal'] is not None and f['normal'][2] > .8]
        if len(candidates) != 2*cells:
            raise ValueError('independent_source_top_atlas_incomplete')
        grid = []
        for i in range(2):
            row = []
            for j in range(cells):
                face = next(f for f in candidates if abs(f['center_mm'][0] - WIDTH_PER_CELL*(i + .5)) < 1. and
                            abs(f['center_mm'][1] - LENGTH_PER_CELL*(j + .5)) < 1.)
                # Reparameterized source: reverse U before swapping U/V in the
                # fixture; normalized reconstruction swaps back then reverses U.
                row.append(_selection(face, reverse=name == 'reparameterized_pair' and i == 1,
                                      swap=name == 'reparameterized_pair' and i == 1))
            grid.append(row)
        plan = dict(schema='cad-harness.plan.v4c', profile='c-s3', family='surface_rebuild', asset_id=name,
            source_sha256=assets[name]['sha256'], grid=grid, continuity='G2',
            fit_tolerance_mm=.05 if cells == 1 else .8, kernel_tolerance_mm=1e-6, max_degree=6, max_poles=4096)
        plans[name] = plan
        ledger.write_json(out / (name + '-plan.json'), plan)
        ledger.write_json(out / (name + '-card.json'), _card(cells))
    ledger.write_json(out / 'plan.json', plans['g1_pair'])
    ledger.write_json(out / 'card.json', _card())
    ledger.write_json(out / 'expected.json', dict(source='independent_analytic_polynomial',
        formula='z=4+.12U^2+.035UV+.08V^2 + .48*(U-1)^2*V^2*(H-V)^2 on U>=1',
        cell_xy_mm=[WIDTH_PER_CELL, LENGTH_PER_CELL], extrusion_mm=DEPTH,
        pair_source_volume_mm3=2*WIDTH_PER_CELL*LENGTH_PER_CELL*DEPTH,
        pair_seam_g1=True, pair_seam_g2=False,
        second_u_jet_jump_at_pair_midpoint_mm=2*BUMP/16,
        physical_xx_second_derivative_jump_per_mm=2*BUMP/16/WIDTH_PER_CELL**2,
        independent_development_only=True))
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    print(generate(parser.parse_args().out))
