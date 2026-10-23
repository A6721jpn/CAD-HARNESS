"""Read-only mechanical failure classification, never raw gold or measurements."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.sw_m1_inputs import private_path

REASONS={'requires_valid_closed_single_solids','native_uncertainty_exhausts_distance_budget',
    'native_distance_unavailable','actual_boundary_closestpoint_lower_exceeds_target',
    'no_whole_boundary_upper_certificate_at_target','both_entire_boundaries_contained_in_guarded_offset_shells'}
SCHEMA_CODES={'count','required','unknown_field','positive','minimum','oneOf','const','enum','finite','type'}
FIELDS={'pockets','holes','finish','regions','steps','center_xy','schema','family','units','frame',
    'kind','sharp','top_z','depth','size','edges','diameter','z','bounds','through','axis'}


def classify(root):
    rows=[]
    for folder in sorted(private_path(root).glob('case-*')):
        if not (folder/'judge-private.json').is_file():continue
        data=json.loads((folder/'judge-private.json').read_text(encoding='utf-8'))
        public=data['public']
        if public.get('SW_editability')=='PASS_ONE_PARAMETER_CHANGE_REBUILD_RESTORE' and public.get('status')=='PASS':continue
        edit=data.get('SW_operational_edit',{});restore=edit.get('restore',{})
        line=data.get('traceback','').splitlines()[-1:] or ['']
        code=line[0].rsplit(':',1)[-1].strip()
        fields=[word for word in re.split(r'[^A-Za-z_]+',line[0]) if word in FIELDS]
        rows.append(dict(sequence=public['sequence'],profile=public['profile'],geometry=public['geometry'],
            schema_failure=code if code in SCHEMA_CODES else None,schema_fields=fields,
            edit_changed_robustly=edit.get('changed_symmetric_volume_mm3',0)>edit.get('uncertainty_mm3',float('inf')),
            restored_original_geometry=edit.get('restored_original_geometry',{}).get('passed'),
            restore_status=restore.get('status'),
            restore_reason=restore.get('reason') if restore.get('reason') in REASONS else None,
            restore_offset_trial_states=[t.get('contained') for t in restore.get('trials',[])],
            restore_planar_error_type=restore.get('planar_alternative_error_type')))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args()
    try:
        for row in classify(a.run):print(json.dumps(row))
    except Exception as e:
        print(json.dumps({'status':'FAIL','error_type':type(e).__name__}));raise SystemExit(1)
