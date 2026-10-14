"""Generate exclusive independent S1 development assets under pinned FreeCAD Python.

The raster is sampled from an analytic signed-distance rounded rectangle. The
reference STEP uses FreeCAD box solids; the oracle contour is analytic arcs,
not fitted from the raster and not exported by the candidate compiler.
Run: <FreeCAD>/bin/python.exe generate.py --out NEW_DIRECTORY
"""
import argparse
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import cad_verify_v4_ledger as ledger


def rounded_rectangle(x0=4., y0=4., width=34., height=22., radius=3.):
    x1, y1 = x0+width, y0+height
    k=radius/math.sqrt(2)
    points=[([x0+radius,y0],[x1-radius,y0]),([x1,y0+radius],[x1,y1-radius]),
            ([x1-radius,y1],[x0+radius,y1]),([x0,y1-radius],[x0,y0+radius])]
    arcs=[([x1-radius,y0],[x1-radius+k,y0+radius-k],[x1,y0+radius]),
          ([x1,y1-radius],[x1-radius+k,y1-radius+k],[x1-radius,y1]),
          ([x0+radius,y1],[x0+radius-k,y1-radius+k],[x0,y1-radius]),
          ([x0,y0+radius],[x0+radius-k,y0+radius-k],[x0+radius,y0])]
    segments=[]
    for (a,b),(p,m,q) in zip(points,arcs):
        segments.extend([dict(kind='line',p0=a,p1=b),dict(kind='arc',p0=p,pm=m,p1=q)])
    return dict(schema='cad-harness.contour.v4c',profile='c-s1',asset_id='analytic_contour',
        units='mm',bounds_mm=[x0,x1,y0,y1],nominal_width_mm=width,
        loops=[dict(role='outer',segments=segments)],
        topology=dict(components=1,holes=0))


def _safe_output(path):
    p=Path(path).absolute()
    if any(x.lower() in ('pilot-user','v4-holdout-private') for x in p.parts):
        raise ValueError('forbidden_data_path')
    for ancestor in (p,*p.parents):
        try:
            info=ancestor.lstat()
        except FileNotFoundError:
            continue
        if ancestor.is_symlink() or getattr(info,'st_file_attributes',0) & 0x400:
            raise ValueError('output_link_or_reparse_point')
    return ledger.new_directory(p)


def generate(out):
    import FreeCAD as App
    import Part
    import numpy as np
    from PIL import Image
    if sys.version_info[:3] != (3,11,14) or tuple(App.Version()[:3]) != ('1','1','4'):
        raise ValueError('requires_pinned_freecad_python')
    out=_safe_output(out)
    expected=ledger.read_json(Path(__file__).with_name('expected.json'))
    ledger.write_json(out/'expected.json',expected)
    box=Part.makeBox(18,12,7)
    box.exportStep(str(out/'reference-box.step'))
    # Coincident duplicate solids deliberately expose non-unique source face identities.
    Part.makeCompound([box,box.copy()]).exportStep(str(out/'ambiguous-reference.step'))
    rr=expected['rounded_rectangle'];mask=rr['mask']
    rows,cols=np.indices((mask['height'],mask['width']))
    x=(cols+.5)*mask['pixel_size_mm'];y=30-(rows+.5)*mask['pixel_size_mm']
    qx=np.abs(x-21)-(17-3);qy=np.abs(y-15)-(11-3)
    signed=np.hypot(np.maximum(qx,0),np.maximum(qy,0))+np.minimum(np.maximum(qx,qy),0)-3
    rgba=np.full((mask['height'],mask['width'],4),255,dtype=np.uint8)
    rgba[signed<=0,:3]=0
    Image.fromarray(rgba).save(out/'rounded-mask.png')
    rectangle=np.full_like(rgba,255);rectangle[16:104,16:152,:3]=0
    Image.fromarray(rectangle).save(out/'rectangle-mask.png')
    wide_hole=rectangle.copy();wide_hole[40:80,64:104,:3]=255
    Image.fromarray(wide_hole).save(out/'wide-hole-mask.png')
    diagonal=np.full_like(rgba,255);diagonal[40,40,:3]=0;diagonal[41,41,:3]=0
    Image.fromarray(diagonal).save(out/'diagonal-mask.png')
    nonopaque=rectangle.copy();nonopaque[40,40,3]=128
    Image.fromarray(nonopaque).save(out/'nonopaque-mask.png')
    recipe=dict(schema='cad-harness.contour-recipe.v4c',profile='c-s1',
        foreground=dict(channel='luminance',polarity='dark',threshold=127),
        alpha=dict(policy='require-opaque'),scale=dict(mm_per_pixel=.25,origin_mm=[0,0]),
        simplify=dict(allowed=False),rounding=dict(allowed=True,radius_mm=3),
        limits=dict(max_deviation_mm=1.3,approximation_tolerance_mm=.005),
        topology=dict(components=1,holes='preserve',islands='reject'))
    ledger.write_json(out/'rounding-recipe.json',recipe)
    # Independent hard negatives: disconnected island, hole, and inverse foreground.
    island=rgba.copy();island[4:8,4:8,:3]=0
    Image.fromarray(island).save(out/'island-mask.png')
    hole=rgba.copy();hole[52:68,76:92,:3]=255
    Image.fromarray(hole).save(out/'hole-mask.png')
    Image.fromarray(255-rgba[:,:,:3]).save(out/'inverse-mask.png')
    record=rounded_rectangle()
    raw={k:record[k] for k in ('profile','units','bounds_mm','nominal_width_mm','loops')}
    raw.update(schema='cad-harness.contour-source.v4c',source_image_asset_id='rounded_mask')
    ledger.write_json(out/'analytic-contour.json',raw)
    record['source_sha256']=ledger.file_sha(out/'analytic-contour.json')
    record['source_image_asset_id']='rounded_mask'
    record['source_image_sha256']=ledger.file_sha(out/'rounded-mask.png')
    record['provenance']=dict(kind='independent_analytic_source')
    record['pixel_to_mm']=dict(scale_mm_per_pixel=.25,origin_mm=[0,0],image_height_pixels=120,
        y_axis='up',pixel_convention='closed unit cells; centers at (col+0.5,row+0.5)')
    font=ROOT/'skills/cad-harness-v4/fonts/DejaVuSansMono.ttf'
    license_path=ROOT/'skills/cad-harness-v4/fonts/LICENSE_DEJAVU'
    shutil.copyfile(font,out/'DejaVuSansMono.ttf')
    shutil.copyfile(license_path,out/'LICENSE_DEJAVU')
    assets={}
    entries=[('reference_box','step','reference','reference-box.step'),
             ('ambiguous_reference','step','reference','ambiguous-reference.step'),
             ('rounded_mask','image','checker','rounded-mask.png'),
             ('rectangle_mask','image','checker','rectangle-mask.png'),
             ('wide_hole_mask','image','checker','wide-hole-mask.png'),
             ('diagonal_mask','image','checker','diagonal-mask.png'),
             ('nonopaque_mask','image','checker','nonopaque-mask.png'),
             ('island_mask','image','checker','island-mask.png'),
             ('hole_mask','image','checker','hole-mask.png'),
             ('inverse_mask','image','checker','inverse-mask.png'),
             ('analytic_contour','contour','contour','analytic-contour.json'),
             ('dev_font','font','font','DejaVuSansMono.ttf'),
             ('font_license','license','license','LICENSE_DEJAVU')]
    for key,kind,role,name in entries:
        p=out/name
        assets[key]=dict(kind=kind,role=role,path=name,sha256=ledger.file_sha(p),bytes=p.stat().st_size)
    assets['dev_font'].update(license_asset_id='font_license',glyphs='B8A0')
    manifest=dict(schema='cad-harness.inputs.v4c',profile='c-s1',evidence_mode='independent_dev',assets=assets)
    ledger.write_json(out/'manifest.json',manifest)
    packet=dict(schema='cad-harness.prepared.v4c',profile='c-s1',source_manifest_sha256=ledger.file_sha(out/'manifest.json'),assets={'analytic_contour':record})
    ledger.write_json(out/'prepared.json',packet)
    plan=dict(schema='cad-harness.plan.v4c',profile='c-s1',family='contour_extrude',
        contour_id='analytic_contour',width_mm=34,thickness_mm=4,origin_mm=[0,0,0],references=[],engravings=[])
    ledger.write_json(out/'plan.json',plan)
    criteria=[dict(id='solid',metric='solid_valid'),dict(id='bounds',metric='bounds',expected_mm=rr['bounds_mm']),
        dict(id='volume',metric='volume',expected_mm3=(34*22-(4-math.pi)*9)*4,tolerance_mm3=.0001),
        dict(id='unchanged_z',metric='unchanged_dimension',axis='Z',expected_mm=4),
        dict(id='radius',metric='min_radius',contour_id='analytic_contour',minimum_mm=2.99,angular_tolerance_rad=1e-6),
        dict(id='tool',metric='tool_access',contour_id='analytic_contour',tool_radius_mm=1,
            maximum_uncovered_mm2=.1,area_uncertainty_mm2=.00001,curve_tolerance_mm=.0001,buffer_segments=128,require_connected=True),
        dict(id='native',metric='native_roundtrip',maximum_bounds_difference_mm=.00001,
            maximum_volume_difference_mm3=.0001,require_editable=True)]
    for leg in ('image_to_contour','contour_to_output'):
        base=dict(leg=leg,contour_id='analytic_contour',curve_tolerance_mm=.0001)
        if leg=='image_to_contour':
            base.update(mask_asset_id='rounded_mask',registration=dict(origin_mm=[0,30],pixel_size_mm=[.25,.25],y_direction=-1),foreground=mask['foreground'])
        else:base['projection_z_mm']=2
        criteria.append(dict(base,id=leg+'_iou',metric='image_iou',minimum_iou=.96 if leg=='image_to_contour' else .999))
        criteria.append(dict(base,id=leg+'_hausdorff',metric='boundary_hausdorff',maximum_mm=.4 if leg=='image_to_contour' else .02,sampling_step_mm=.02))
    card=dict(schema='cad-harness.judge-card.v4c',profile='c-s1',source='independent_dev',linear_tolerance_mm=.00001,criteria=criteria)
    ledger.write_json(out/'card.json',card)
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    print(generate(args.out))
