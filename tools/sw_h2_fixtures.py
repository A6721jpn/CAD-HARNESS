"""Fresh analytic developer fixtures; no original60, pilot or model data imports.

Only IDs, commitments and control outcomes are public. Gold remains fixture
(not human-confirmed), and is consumed mechanically by native controls/judges.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import secrets
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_h0_runtime as runtime,sw_h0_cad as cad,cad_spec
from tools import cad_verify_v4_ledger as ledger,cad_verify_v3_probe as gold_probe
from tools.sw_m1_inputs import private_path
from tools.cad_verify_guard import Stop

PUBLIC=ROOT/'reports/sw-h2'
# More work inside the existing 64-hole family after repeated baseline ceilings.
# Synthetic design settings, not changed original cards or tolerances.
LEVELS=((27,7),(29,11),(31,13),(33,17),(35,19))
RADIUS_MM=(30,40)
CONTROL_SOURCES=('tools/sw_m0.py','tools/sw_m1_build.py','tools/sw_m1_judge.py',
    'tools/sw_m0_distance.py','tools/sw_m1_distance.py','tools/sw_h0_cad.py','tools/sw_h0_worker.py','tools/sw_h0_verify.py',
    'tools/cad_spec.py','tools/cad_spec_probe.py','tools/cad_verify_probe.py','tools/cad_verify_v3_probe.py',
    'tools/sw_h2_fixtures.py','design/cad-harness-verify-v3/gold-schema.json',
    'design/cad-harness-mvp/build-schema.json','design/cad-harness-verify-v4/policy.json')


def folder(experiment):
    if re.fullmatch(r'[A-Za-z0-9_-]{1,64}',experiment) is None:raise Stop('H2_experiment_name')
    return private_path(runtime.PRIVATE/('h2-'+experiment))


def clockwise_y_points(center,radius,count,start_deg):
    return [[center[0]+radius*math.sin(math.radians(start_deg+360*i/count)),
             center[1]+radius*math.cos(math.radians(start_deg+360*i/count))] for i in range(count)]


def make_case(seed,key,level):
    rng=random.Random(int.from_bytes(hashlib.sha256(seed+key.encode()).digest(),'big'))
    radius=rng.randint(*RADIUS_MM);width=4*radius+rng.randint(20,28);depth=4*radius+rng.randint(18,26)
    height=rng.randint(14,24);x0=rng.randint(-70,-20);y0=rng.randint(-50,-10);z0=rng.choice((-7,-3,2,6))
    sx,sy=rng.randint(-3,3),rng.randint(-3,3)
    center=[x0+width/2+sx,y0+depth/2+sy]
    pw,pd,pdepth=rng.randint(8,12),rng.randint(8,12),rng.randint(2,5)
    diameter=rng.choice((4,5));count,angle=LEVELS[level-1]
    bbox=[x0,x0+width,y0,y0+depth,z0,z0+height]
    pockets=[dict(bounds=[center[0]-pw/2,center[0]+pw/2,center[1]-pd/2,center[1]+pd/2],
                  top_z=z0+height,depth=pdepth,sharp=True)]
    holes=[dict(center_xy=p,diameter=diameter,z=[z0,z0+height],through=True)
           for p in clockwise_y_points(center,radius,count,angle)]
    if level==1:
        origin=f'({x0} mm, {y0} mm, {z0} mm)';size=f'{width} mm by {depth} mm by {height} mm'
    else:
        origin=f'({x0/10:g} cm, {y0} mm, {z0} mm)';size=f'{width} mm by {depth/10:g} cm by {height/10:g} cm'
    request=(f'Create one editable solid rectangular plate. World XYZ minimum corner is {origin}. '
        f'Its full X, Y and Z dimensions are respectively {size}. '
        f'On the top face make one sharp rectangular non-through pocket, X width {pw} mm, Y width {pd} mm, depth {pdepth} mm from that top face. '
        f'The pocket center is at half the full X dimension plus ({sx}) mm from the minimum-X face, '
        f'and half the full Y dimension plus ({sy}) mm from the minimum-Y face. '
        f'Create {count} vertical through holes of diameter {diameter} mm. Their pitch-circle diameter is {2*radius} mm, '
        f'centered on the pocket center. The first hole is {angle} degrees clockwise from the world +Y direction, '
        f'and the remaining holes are equally spaced clockwise around the complete circle. '
        'Every hole goes through the full plate thickness. No fillets, chamfers or other machining. '
        'All positions are world coordinates; convert the supplied units consistently.')
    params=dict(profile='rect_prism',bbox=bbox,pockets=copy.deepcopy(pockets),holes=copy.deepcopy(holes),finish=None)
    gold=dict(schema='cad-harness.verify-gold.v3',case_id=key,description=request,
        description_sha256=ledger.sha(request.encode()),units='mm',frame='world',profile='rect_prism',parameters=params,
        tolerances=dict(linear_mm=.01,axis=1e-6,volume_relative=1e-4),bbox=bbox,
        volume=dict(target_mm3=width*depth*height-pw*pd*pdepth-count*math.pi*(diameter/2)**2*height,
            relative=1e-4,formula='W*D*H - pocket_width*pocket_length*pocket_depth - N*pi*(hole_diameter/2)^2*H'),
        regions=[],sections=[],steps=[],holes=holes,pockets=pockets,finish=None,
        editability=dict(required=True,key_dimensions_mm=[height],
            roles=[dict(role='plate_height',target_mm=height,relation='native_primary')]),
        provenance=dict(authority='fixture',confirmed=False,version=1,
            decision='Independent synthetic developer fixture; not a human-supplied pilot or original60 task',
            source='sw_h2_fixtures.py sealed-seed author'))
    spec=dict(schema='cad-harness.build-spec.v1',family='rect_prism',units='mm',frame='world',
        regions=[dict(bounds=copy.deepcopy(bbox))],pockets=copy.deepcopy(pockets),holes=copy.deepcopy(holes),finish=None)
    for p in spec['pockets']:p.pop('sharp')
    for h in spec['holes']:h.pop('through')
    return request,gold,cad_spec.validate_spec(spec)


def create(experiment):
    out=folder(experiment);out.mkdir(parents=True,exist_ok=False)
    seed=secrets.token_bytes(32);(out/'seed.bin').write_bytes(seed)
    entries=[]
    for role in ('development','holdout'):
        for level in range(1,6):
            key='H2'+('D' if role=='development' else 'H')+str(level)
            request,gold,spec=make_case(seed,key,level)
            case=out/key;case.mkdir()
            (case/'request.txt').write_bytes(request.encode())
            ledger.write_json(case/'gold.json',gold);ledger.write_json(case/'control-spec.json',spec)
            gold_probe.load_gold(case/'gold.json')
            entries.append(dict(id=key,case=key,sequence=len(entries)+1,group='geometry',round=1,route='spec',
                min_calls=1,max_calls=3,profile='rect_prism',card={},selected=True,role=role,level=level,
                gold_path=str(case/'gold.json'),gold_sha256=ledger.file_sha(case/'gold.json'),
                request_path=str(case/'request.txt'),request_sha256=ledger.sha(request.encode()),
                control_spec_path=str(case/'control-spec.json')))
    ledger.write_json(out/'pack.json',dict(schema='harness2.solidworks.fresh-fixtures.v1',experiment=experiment,entries=entries))
    files={str(p.relative_to(out)):ledger.file_sha(p) for p in out.rglob('*') if p.is_file()}
    seal=dict(schema='harness2.solidworks.fixture-seal.v1',experiment=experiment,files=files,
        factory_sha256=ledger.file_sha(Path(__file__)),created_at=ledger.utc(),original60_reused=False)
    ledger.write_json(out/'seal.json',seal)
    pub=PUBLIC/experiment;pub.mkdir(parents=True,exist_ok=False)
    public=dict(experiment=experiment,development_ids=[e['id'] for e in entries if e['role']=='development'],
        sealed_holdout_count=5,seed_commitment=ledger.sha(seed),seal_sha256=ledger.file_sha(out/'seal.json'),
        factory_sha256=seal['factory_sha256'],original60_reused=False,live_model_calls=0)
    ledger.write_json(pub/'fixtures-public.json',public)
    return public


def admitted(experiment):
    out=folder(experiment);seal=ledger.read_json(out/'seal.json')
    if seal['schema']!='harness2.solidworks.fixture-seal.v1' or seal['experiment']!=experiment:
        raise Stop('H2_fixture_seal_identity')
    if ledger.file_sha(Path(__file__))!=seal['factory_sha256']:raise Stop('H2_fixture_factory_changed')
    for name,digest in seal['files'].items():
        path=private_path(out/name)
        if not path.is_relative_to(out) or ledger.file_sha(path)!=digest:raise Stop('H2_sealed_fixture_changed')
    packet=ledger.read_json(out/'pack.json')
    for entry in packet['entries']:
        gold=gold_probe.load_gold(entry['gold_path'])
        if gold['provenance']['authority']!='fixture' or gold['provenance']['confirmed'] is not False:
            raise Stop('H2_fixture_not_synthetic')
        entry['gold']=gold
    return out,seal,packet['entries']


def controls(experiment):
    out,seal,entries=admitted(experiment)
    proof=out/'native-controls';proof.mkdir(exist_ok=False)
    lock=ROOT/'reports/sw-m0/session.lock';unsafe=True
    with lock.open('x') as file:json.dump(dict(scope='H2-native-controls',experiment=experiment,pid=os.getpid()),file)
    rows=[];source={name:ledger.file_sha(ROOT/name) for name in CONTROL_SOURCES}
    try:
        for entry in entries:
            spec=cad_spec.loads_spec(Path(entry['control_spec_path']).read_text(encoding='utf-8'))
            case=proof/entry['id'];case.mkdir()
            for label,candidate in (('positive',spec),('negative',copy.deepcopy(spec))):
                if label=='negative':candidate['pockets'][0]['depth']+=.1
                script=case/(label+'.py');script.write_text(cad.compile_candidate(candidate),encoding='utf-8')
                result=cad.run_candidate(candidate,entry,case/label,script,cad_timeout=300,reimport_timeout=90,total_timeout=450)
                if result.get('next_actor')=='human':raise Stop('H2_native_control_backend_stopped')
                okay=result['status']=='ok' if label=='positive' else result['geometry_ok'] is False
                rows.append(dict(id=entry['id'],role=entry['role'],control=label,passed=okay))
                print(json.dumps(rows[-1]),flush=True)
                if not okay:raise Stop('H2_native_control_mismatch')
        if any(ledger.file_sha(ROOT/name)!=digest for name,digest in source.items()):
            raise Stop('H2_control_source_changed')
        unsafe=False
    finally:
        if not unsafe:lock.unlink()
    result=dict(status='PASS',experiment=experiment,rows=rows,live_model_calls=0,
        seal_sha256=ledger.file_sha(out/'seal.json'),factory_sha256=seal['factory_sha256'],
        source_sha256=source)
    ledger.write_json(proof/'proof.json',result)
    ledger.write_json(PUBLIC/experiment/'native-controls-public.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('create','controls'));parser.add_argument('--experiment',required=True)
    args=parser.parse_args()
    try:
        result=create(args.experiment) if args.action=='create' else controls(args.experiment)
        print(json.dumps(result),flush=True)
    except Exception as exc:
        print(json.dumps(dict(status='STOPPED',error_type=type(exc).__name__,
            reason=str(exc) if isinstance(exc,Stop) else 'H2_fixture_author_failure')),flush=True)
        raise SystemExit(2)
