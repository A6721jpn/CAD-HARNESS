"""Generate independent paired native evidence for the neutral checker.

No model/provider calls. Each bare model uses independent_native_models (only
FreeCAD/Part/Sketcher/math), never the harness constructors. Shared source data,
cards and measurement context are authored before either candidate is built.
"""
import argparse
import copy
import importlib.util
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools import cad_verify_v4_ledger as ledger, cad_verify_v4_inputs as inputs
from tools import cad_verify_v4_compile as compiler, cad_verify_v4_plans as plans
from tools import cad_verify_v4_s2_edit as editor, cad_verify_v4_s3_rebuild as rebuild
from tools import cad_verify_v4_s1 as facade


def _load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _record(path):
    return dict(path=str(path),sha256=ledger.file_sha(path),bytes=path.stat().st_size)


def _save(doc,body,out,profile,probes):
    out = ledger.new_directory(out)
    doc.recompute()
    compiler.check_document(doc,body)
    doc.saveAs(str(out/'part.FCStd'))
    body.Shape.exportStep(str(out/'part.step'))
    extensions = {}
    for obj in doc.Objects:
        if 'Proxy' in obj.PropertiesList and obj.Proxy is not None:
            cls = type(obj.Proxy)
            source = Path(inspect.getsourcefile(cls)).absolute()
            extensions[cls.__module__] = dict(module=cls.__module__,**_record(source))
    bundle = dict(schema='cad-harness.artifact-bundle.v4',profile=profile,evidence_mode='independent_dev',
                  native=_record(out/'part.FCStd'),step=_record(out/'part.step'),output_object=body.Name,
                  probes=probes,extensions=list(extensions.values()))
    ledger.write_json(out/'artifacts.json',bundle)
    return out/'artifacts.json'


def _context(family,profile,manifest,prepared,card,**data):
    return dict(schema='cad-harness.artifact-context.v4',profile=profile,family=family,
                manifest_sha256=ledger.file_sha(manifest),prepared_sha256=ledger.file_sha(prepared),
                card_sha256=ledger.file_sha(card),reference=data.get('reference'),contour=data.get('contour'),
                engravings=data.get('engravings',[]))


def _card(*criteria):
    return dict(schema='cad-harness.judge-card.v4c',profile='c-s1',source='independent_dev',
                linear_tolerance_mm=1e-5,criteria=list(criteria))


def _native_gate():
    return dict(id='native',metric='native_roundtrip',maximum_bounds_difference_mm=1e-5,
                maximum_volume_difference_mm3=.01,require_editable=True)


def _spec(x,y,z,pockets=None):
    return dict(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world',
                regions=[dict(bounds=[0,x,0,y,0,z])],pockets=pockets or [],holes=[],finish=None)


def generate(value):
    import FreeCAD as App
    import Part
    if sys.version_info[:3] != (3,11,14) or tuple(App.Version()[:3]) != ('1','1','4'):
        raise ValueError('requires_pinned_freecad_python')
    out = ledger.new_directory(facade.safe_path(value))
    bare = _load('independent_native_models',Path(__file__).with_name('independent_native_models.py'))
    source1 = _load('independent_integrated_source1',ROOT/'design/cad-harness-verify-v4/dev-c-s1/generate.py')
    source2 = _load('independent_integrated_source2',ROOT/'design/cad-harness-verify-v4/dev-c-s2/generate.py')
    source3 = _load('independent_integrated_source3',ROOT/'design/cad-harness-verify-v4/dev-c-s3/generate.py')
    s1 = source1.generate(out/'source-s1')
    s2 = source2.generate(out/'source-s2')
    s3 = source3.generate(out/'source-s3')
    # The independent full stock is a private-to-checker baseline, not candidate
    # history or a candidate-derived filling of the engraved recess.
    baseline = s1/'checker-stock.step'
    Part.makeBox(20,20,4).exportStep(str(baseline))
    manifest1 = ledger.read_json(s1/'manifest.json')
    manifest1['assets']['checker_stock'] = dict(kind='step',role='checker',path=baseline.name,
                                               sha256=ledger.file_sha(baseline),bytes=baseline.stat().st_size)
    m1 = s1/'integrated-inputs.json'
    ledger.write_json(m1,manifest1)
    recipe1 = dict(schema='cad-harness.step-recipe.v4c',profile='c-s1',source_axes=['X','Y','Z'],
                   source_units='mm',signature_precision_mm=1e-6)
    ledger.write_json(s1/'step-recipe.json',recipe1)
    prepared1 = ledger.read_json(s1/'prepared.json')
    prepared1['source_manifest_sha256'] = ledger.file_sha(m1)
    for asset in ('reference_box','checker_stock'):
        packet = inputs.inspect_step(m1,asset,recipe1,s1/(asset+'-integrated-facts.json'))
        prepared1['assets'].update(packet['assets'])
    p1 = s1/'integrated-prepared.json'
    ledger.write_json(p1,prepared1)
    source_faces = [f['id'] for f in prepared1['assets']['reference_box']['faces']]
    card1 = _card(dict(id='solid',metric='solid_valid'),
        dict(id='bounds',metric='bounds',expected_mm=[0,28,0,20,0,6]),
        dict(id='volume',metric='volume',expected_mm3=3120,tolerance_mm3=.0001),
        dict(id='source_clearance',metric='reference_clearance',asset_id='reference_box',face_ids=source_faces,
             translation_mm=[0,0,20],rotation_axis=[0,0,1],rotation_deg=0,minimum_gap_mm=13.99,strict_separation=True),
        _native_gate())
    plan1 = dict(schema='cad-harness.plan.v4c',profile='c-s1',family='reference_fixture',
        build_spec=_spec(28,20,6,[dict(bounds=[8,18,6,14],top_z=6,depth=3)]),
        references=[dict(asset_id='reference_box',translation_mm=[0,0,20],rotation_axis=[0,0,1],rotation_deg=0)],engravings=[])
    glyph = dict(font_id='dev_font',text='B8',height_mm=4,depth_mm=.5,origin_mm=[4,5,4],
                 rotation_axis=[0,0,1],rotation_deg=0)
    card3 = _card(dict(id='solid',metric='solid_valid'),
        dict(id='bounds',metric='bounds',expected_mm=[0,20,0,20,0,4]),
        dict(id='glyph',metric='engraving',index=0,minimum_removed_mm3=1,depth_tolerance_mm=.01),_native_gate())
    plan3 = dict(schema='cad-harness.plan.v4c',profile='c-s1',family='reference_fixture',
                 build_spec=_spec(20,20,4),references=[],engravings=[glyph])
    cases = []
    for family,profile,manifest,prepared,card,plan,data in (
        ('C1','c-s1',m1,p1,card1,plan1,dict(reference=dict(asset_id='reference_box',source_sha256=manifest1['assets']['reference_box']['sha256']))),
        ('C2','c-s1',m1,p1,ledger.read_json(s1/'card.json'),ledger.read_json(s1/'plan.json'),
            dict(contour=dict(contour_id='analytic_contour',scale=1.,origin_mm=[0,0,0],thickness_mm=4.))),
        ('C3','c-s1',m1,p1,card3,plan3,dict(engravings=[dict(glyph,baseline_asset_id='checker_stock')])),
        ('C4','c-s2',s2/'manifest.json',s2/'prepared.json',ledger.read_json(s2/'card.json'),ledger.read_json(s2/'plan.json'),
            dict(reference=dict(asset_id='featured_plate',source_sha256=ledger.read_json(s2/'manifest.json')['assets']['featured_plate']['sha256']))),
        ('C5','c-s3',s3/'manifest.json',s3/'prepared.json',ledger.read_json(s3/'g1_pair-card.json'),ledger.read_json(s3/'g1_pair-plan.json'),
            dict(reference={key:copy.deepcopy(ledger.read_json(s3/'g1_pair-plan.json')[key]) for key in ('asset_id','source_sha256','grid')}))):
        case_dir = ledger.new_directory(out/family)
        card_path,context_path = case_dir/'card.json',case_dir/'context.json'
        ledger.write_json(card_path,card)
        ledger.write_json(context_path,_context(family,profile,manifest,prepared,card_path,**data))
        packet = ledger.read_json(prepared)
        plans.validate_plan(plan,manifest,packet,profile=profile)
        plans.validate_judge_card(card,profile=profile)
        bundles = {}
        for arm in ('bare','harness'):
            doc = App.newDocument(family+arm)
            try:
                if arm == 'harness':
                    constructor = {'c-s1':compiler,'c-s2':editor,'c-s3':rebuild}[profile]
                    body = constructor.build_plan(doc,plan,manifest,packet)
                    if family=='C1':
                        probes=[]
                    elif family=='C2':
                        probes=[dict(kind='scalar',object='ContourExtrude',property='Thickness',delta=.01)]
                    elif family=='C3':
                        probes=[dict(kind='scalar',object='Engraving0',property='Depth',delta=.01)]
                    elif family=='C4':
                        probes=[dict(kind='scalar',object='DirectEdit',property='OffsetDistance',delta=.01)]
                    else:
                        feature = next(o for o in doc.Objects if 'PoleOffsets' in o.PropertiesList)
                        data = json.loads(feature.SurfaceData)
                        rows,columns = len(data['poles']),len(data['poles'][0])
                        editable = (rows//2)*columns+columns//2
                        probes=[dict(kind='vector_list',object=feature.Name,property='PoleOffsets',index=editable,delta_mm=[0,0,.001])]
                    ledger.write_json(case_dir/'harness-plan.json',plan)
                elif family=='C1':
                    body = bare.fixture(doc);probes=[]
                elif family=='C2':
                    body = bare.contour(doc);probes=[]
                elif family=='C3':
                    body = bare.engraving(doc,inputs.resolve_asset(manifest,'dev_font','font')['path']);probes=[]
                elif family=='C4':
                    shape = Part.Shape();shape.read(str(s2/'featured_plate.step'))
                    body = bare.imported_edit(doc,shape);probes=[]
                else:
                    shape = Part.Shape();shape.read(str(s3/'g1_pair.step'))
                    body = bare.rebuilt_surface(doc,shape)
                    probes=[dict(kind='scalar',object='AnalyticBlend',property='InteriorLift',delta=.001)]
                bundles[arm] = str(_save(doc,body,case_dir/arm,profile,probes))
            finally:
                App.closeDocument(doc.Name)
        cases.append(dict(family=family,profile=profile,input_manifest_path=str(manifest),prepared_path=str(prepared),
                          card_path=str(card_path),context_path=str(context_path),**{arm+'_bundle_path':path for arm,path in bundles.items()}))
    result = dict(schema='cad-harness.neutral-fixtures.v4',evidence_mode='independent_dev',live_calls=0,cases=cases,
                  recipes=[str(s1/'step-recipe.json'),str(s1/'rounding-recipe.json'),str(s2/'step-recipe.json'),str(s3/'step-recipe.json')])
    ledger.write_json(out/'fixtures.json',result)
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    args = parser.parse_args()
    print(generate(args.out))
