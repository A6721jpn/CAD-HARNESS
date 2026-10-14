"""Independent authored S2 development geometry, never pilot/holdout-derived.

Run under the pinned native Python with --out NEW_DIRECTORY. Analytic expected
volumes are calculated from source dimensions, not candidate editor output.
"""
import argparse
import copy
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
import cad_verify_v4_ledger as ledger


def _safe_output(value):
    path = Path(value).absolute()
    if any(p.casefold().rstrip(' .') in ('pilot-user','v4-holdout-private') for p in path.parts):
        raise ValueError('forbidden_data_path')
    for ancestor in (path,*path.parents):
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            continue
        if ancestor.is_symlink() or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('output_link_or_reparse_point')
    return ledger.new_directory(path)


def selection(face):
    return {key:copy.deepcopy(face[key]) for key in ('signature','adjacent_face_ids')} | {'face_id':face['id']}


def smooth_roof():
    """Extruded cubic B-spline roof; integral height is (7+9+8+7)/4."""
    import FreeCAD as App
    import Part
    curve = Part.BSplineCurve()
    curve.buildFromPolesMultsKnots([App.Vector(0,0,7),App.Vector(6,0,9),
        App.Vector(12,0,8),App.Vector(18,0,7)],[4,4],[0.,1.],False,3)
    wire = Part.Wire([Part.makeLine(App.Vector(0,0,0),App.Vector(18,0,0)),
        Part.makeLine(App.Vector(18,0,0),App.Vector(18,0,7)),curve.toShape().reversed(),
        Part.makeLine(App.Vector(0,0,7),App.Vector(0,0,0))])
    return Part.Face(wire).extrude(App.Vector(0,12,0))


def generate(out):
    import FreeCAD as App
    import Part
    import cad_verify_v4_inputs as inputs
    if sys.version_info[:3] != (3,11,14) or tuple(App.Version()[:3]) != ('1','1','4'):
        raise ValueError('requires_pinned_freecad_python')
    out = _safe_output(out)
    box = Part.makeBox(18,12,7)
    plate = box.cut(Part.makeCylinder(1,2,App.Vector(4,4,0)))
    tilted = Part.Face(Part.makePolygon([App.Vector(-10,-10,7),App.Vector(30,-10,11),
        App.Vector(30,30,11),App.Vector(-10,30,7),App.Vector(-10,-10,7)]))
    undersized = Part.Face(Part.makePolygon([App.Vector(8,5,8.8),App.Vector(10,5,9),
        App.Vector(10,7,9),App.Vector(8,7,8.8),App.Vector(8,5,8.8)]))
    rotated = plate.copy()
    rotated.rotate(App.Vector(0,0,0),App.Vector(1,2,3),31)
    rotated.translate(App.Vector(8,-4,3))
    geometries = {'box':box,'featured_plate':plate,'rotated_plate':rotated,
                  'cylinder':Part.makeCylinder(5,9),'tilted_plane':tilted,'undersized_plane':undersized,
                  'smooth_roof':smooth_roof(),'ambiguous':Part.makeCompound([box,box.copy()])}
    assets = {}
    for asset_id,shape in geometries.items():
        path = out/(asset_id+'.step')
        shape.exportStep(str(path))
        assets[asset_id] = dict(kind='step',role='reference',path=path.name,
            sha256=ledger.file_sha(path),bytes=path.stat().st_size)
    manifest = dict(schema='cad-harness.inputs.v4c',profile='c-s2',evidence_mode='independent_dev',assets=assets)
    ledger.write_json(out/'manifest.json',manifest)
    recipe = dict(schema='cad-harness.step-recipe.v4c',profile='c-s2',source_axes=['X','Y','Z'],
                  source_units='mm',signature_precision_mm=1e-6)
    ledger.write_json(out/'step-recipe.json',recipe)
    packet = None
    for asset_id in geometries:
        item = inputs.inspect_step(out/'manifest.json',asset_id,recipe,out/(asset_id+'-facts.json'))
        if packet is None:
            packet = item
        else:
            packet['assets'].update(item['assets'])
    ledger.write_json(out/'prepared.json',packet)
    def make_plan(asset_id, face, operation):
        return dict(schema='cad-harness.plan.v4c',profile='c-s2',family='step_direct_edit',asset_id=asset_id,
            source_sha256=assets[asset_id]['sha256'],selection=selection(face),operation=operation,kernel_tolerance_mm=1e-6)
    plans = {}
    for asset_id in ('box','featured_plate'):
        top = next(f for f in packet['assets'][asset_id]['faces'] if f['surface_type']=='Plane' and abs(f['center_mm'][2]-7)<1e-6)
        for suffix,distance in [('out',1.),('in',-1.)]:
            plans[asset_id+'_'+suffix] = make_plan(asset_id,top,dict(kind='offset',distance_mm=distance,reconnect='extend_intersect_trim'))
        plans[asset_id+'_replace'] = make_plan(asset_id,top,dict(kind='replace',
            replacement_asset_id='tilted_plane',replacement_source_sha256=assets['tilted_plane']['sha256'],
            replacement_selection=selection(packet['assets']['tilted_plane']['faces'][0]),
            reconnect='extend_intersect_trim',extension_limit_mm=3.))
    cylinder_face = next(f for f in packet['assets']['cylinder']['faces'] if f['surface_type']=='Cylinder')
    for suffix,distance in [('out',1.),('in',-1.)]:
        plans['cylinder_'+suffix] = make_plan('cylinder',cylinder_face,dict(kind='offset',distance_mm=distance,reconnect='extend_intersect_trim'))
    smooth_face = next(f for f in packet['assets']['smooth_roof']['faces'] if f['surface_type']!='Plane')
    for suffix,distance in [('out',.5),('in',-.5)]:
        plans['smooth_roof_'+suffix] = make_plan('smooth_roof',smooth_face,
            dict(kind='offset',distance_mm=distance,reconnect='extend_intersect_trim'))
    # Top face selection in a fully oblique global frame, not an axis-aligned box.
    top_center = App.Vector(9,6,7)
    transform = App.Placement(App.Vector(8,-4,3),App.Rotation(App.Vector(1,2,3),31))
    top_center = transform.multVec(top_center)
    rotated_top = next(f for f in packet['assets']['rotated_plate']['faces'] if math.dist(f['center_mm'],list(top_center))<1e-6)
    plans['rotated_plate_out'] = make_plan('rotated_plate',rotated_top,dict(kind='offset',distance_mm=1.,reconnect='extend_intersect_trim'))
    for name,plan in plans.items():
        ledger.write_json(out/(name+'-plan.json'),plan)
    ledger.write_json(out/'plan.json',plans['featured_plate_out'])
    ledger.write_json(out/'replacement-plan.json',plans['featured_plate_replace'])
    expected = {'source':'independent_analytic_dimensions','box':{'original_volume_mm3':1512.,'out_volume_mm3':1728.,'in_volume_mm3':1296.,'replace_volume_mm3':1922.4,'faces':6},
        'featured_plate':{'original_volume_mm3':1512.-2*math.pi,'out_volume_mm3':1728.-2*math.pi,
            'in_volume_mm3':1296.-2*math.pi,'replace_volume_mm3':1922.4-2*math.pi,'faces':8},
        'cylinder':{'original_volume_mm3':225*math.pi,'out_volume_mm3':324*math.pi,'in_volume_mm3':144*math.pi,'faces':3},
        'smooth_roof':{'original_volume_mm3':1674.,'faces':6,
            'roof_control_points_mm':[[0,0,7],[6,0,9],[12,0,8],[18,0,7]],
            'offset_convention':'signed local outward normal; no global distribution certificate from samples'},
        'replacement_plane':{'equation':'z=8+0.1*x','z_min_mm':8.,'z_max_mm':9.8},
        'preserved_cavity':{'radius_mm':1.,'depth_mm':2.,'center_mm':[4.,4.,0.]}}
    ledger.write_json(out/'expected.json',expected)
    # DEV-ONLY authored numerical contracts, never adopted user tolerances:
    # the convex 18x12x<=10 outer prism is contained by a 1032 mm² box
    # boundary; the blind R1/depth2 cavity adds net 4*pi mm². At 1e-6 mm
    # construction tolerance, two boundaries give <0.00209 mm³ first-order
    # volume uncertainty. A finite 0.01 mm³ dev roundtrip limit leaves explicit
    # numerical headroom, independent of candidate-measured discrepancies.
    # Each clipped 4x4x2.5 ROI has area <=72+4*pi mm²; two copies contribute
    # <0.000170 mm³ at 1e-6 mm. Declare 0.0003 mm³ numerical uncertainty
    # including roundoff/headroom, without changing its 0.001 mm³ acceptance.
    card = dict(schema='cad-harness.judge-card.v4c',profile='c-s2',source='independent_dev',numerical_uncertainty_mm=1e-5,criteria=[
        dict(id='solid',metric='solid_valid',expected_solids=1),
        dict(id='faces',metric='face_count',scope='full',relation='equal',correspondence='spatial_fixed_frame',expected_count=8),
        dict(id='width',metric='unchanged_dimension',definition='axis_extent',axis='X',tolerance_mm=.001),
        dict(id='length',metric='unchanged_dimension',definition='axis_extent',axis='Y',tolerance_mm=.001),
        dict(id='cavity_roi',metric='preserved_region',region_mm=[2,6,2,6,0,2.5],maximum_symmetric_difference_mm3=.001,volume_uncertainty_mm3=.0003),
        dict(id='native',metric='native_roundtrip',maximum_bounds_difference_mm=1e-5,maximum_volume_difference_mm3=.01,require_editable=True)])
    bottom = next(f for f in packet['assets']['featured_plate']['faces'] if f['surface_type']=='Plane' and abs(f['center_mm'][2])<1e-6)
    top = plans['featured_plate_out']['selection']['face_id']
    thickness = dict(id='wall',metric='thickness_distribution',scope='continuous',convention='directed_material_chord',
        direction=[0,0,1],domain=dict(origin_mm=[8,2,0],u=[1,0,0],v=[0,1,0],size_mm=[8,8]),
        opposed_sets=dict(a=dict(source_face_ids=[bottom['id']],output_region_mm=[7.9,16.1,1.9,10.1,-.1,.1]),
                          b=dict(source_face_ids=[top],output_region_mm=[7.9,16.1,1.9,10.1,7.9,8.1])),
        expected_range_mm=[8,8],tolerance_mm=.001,samples=[3,3],ray_length_mm=30)
    card['criteria'].insert(-1,thickness)
    ledger.write_json(out/'card.json',card)
    replacement_card = copy.deepcopy(card)
    replacement_thickness = next(c for c in replacement_card['criteria'] if c['metric']=='thickness_distribution')
    replacement_thickness.update(scope='sampled',expected_range_mm=[8.8,9.6])
    replacement_thickness['opposed_sets']['b']['output_region_mm']=[7.9,16.1,1.9,10.1,7.9,9.9]
    ledger.write_json(out/'replacement-card.json',replacement_card)
    # Independent smooth fixture contract: the cubic B-spline lies in its
    # control-height hull [7,9]; a +/-0.5 mm normal offset has vertical
    # displacement <=0.5 mm. This sampled scope claims no global certificate.
    smooth_card = copy.deepcopy(card)
    smooth_bottom = next(f for f in packet['assets']['smooth_roof']['faces']
        if f['surface_type']=='Plane' and abs(f['center_mm'][2])<1e-6)
    smooth_top = plans['smooth_roof_out']['selection']['face_id']
    for criterion in smooth_card['criteria']:
        if criterion['metric']=='face_count':
            criterion['expected_count']=6
        elif criterion['metric']=='preserved_region':
            criterion['id']='lower_roi'
        elif criterion['metric']=='thickness_distribution':
            criterion.update(scope='sampled',expected_range_mm=[6.5,9.5])
            criterion['opposed_sets']['a']['source_face_ids']=[smooth_bottom['id']]
            criterion['opposed_sets']['b']=dict(source_face_ids=[smooth_top],
                output_region_mm=[7.9,16.1,1.9,10.1,6.4,9.6])
    ledger.write_json(out/'smooth-card.json',smooth_card)
    return out


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    print(generate(parser.parse_args().out))
