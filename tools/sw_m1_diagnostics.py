"""Read-only mechanical failure classification, never raw gold or measurements."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.sw_m1_inputs import private_path
from tools import sw_m0 as base

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


def audit(roots):
    """Only hashes/owned-session metadata; no COM, no raw geometry export."""
    pids=set();native={};steps={};golds={};sessions=0;cases=0;safe=True
    for root in roots:
        for folder in sorted(private_path(root).glob('case-*')):
            if not (folder/'com-result.json').is_file():continue
            com=json.loads((folder/'com-result.json').read_text(encoding='utf-8'))
            job=json.loads((folder/'job.json').read_text(encoding='utf-8'))
            # Authorized input gold is outside the private OUTPUT directory.
            cases+=1;golds[Path(job['gold_path'])]=job['gold_sha256']
            provenance=folder/'reuse-provenance-private.json'
            neutral_reuse=provenance.is_file() and not json.loads(provenance.read_text())['redo_owned_edit_only']
            if not neutral_reuse:
                sessions+=1;pids.add(com['pid'])
                safe &= (com['status']=='PASS' and com['initial_documents']==0 and
                         com['final_documents']==0 and not com.get('COM_state_unknown') and not com.get('stop'))
            safe &= com['original_native_unchanged']
            native[private_path(com['native']['path'])]=com['native']['sha256']
            records=[com[k] for k in ('before_step','reopened_step','negative_step') if k in com]
            records += [com['edit'][k] for k in ('changed_step','restored_step') if k in com.get('edit',{})]
            for item in records:steps[private_path(item['path'])]=item['sha256']
    native_ok=all(base.digest(p)==h for p,h in native.items())
    step_ok=all(base.digest(p)==h for p,h in steps.items())
    gold_ok=all(base.digest(p)==h for p,h in golds.items())
    safe=bool(safe and cases and sessions and len(pids)==1)
    return dict(status='PASS' if safe and native_ok and step_ok and gold_ok else 'FAIL',
        paid_model_calls=0,case_evidence_records=cases,owned_COM_sessions=sessions,
        SW_pids=sorted(pids),all_initial_and_final_documents_zero_and_state_known=safe,
        native_files_checked=len(native),all_native_hashes_unchanged=native_ok,
        STEP_files_checked=len(steps),all_STEP_hashes_match=step_ok,
        gold_files_checked=len(golds),all_gold_hashes_unchanged=gold_ok)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',nargs='+');p.add_argument('--audit',action='store_true');p.add_argument('--public');a=p.parse_args()
    try:
        if a.audit:
            result=audit(a.run)
            if a.public:
                path=Path(a.public).absolute()
                if not path.is_relative_to(ROOT/'reports/sw-m1') or '..' in path.parts:raise ValueError('public_audit_path')
                base.save_json(path,result)
            print(json.dumps(result))
            if result['status']!='PASS':raise SystemExit(1)
        else:
            if len(a.run)!=1 or a.public:raise ValueError('single_private_classification_run_required')
            for row in classify(a.run[0]):print(json.dumps(row))
    except Exception as e:
        print(json.dumps({'status':'FAIL','error_type':type(e).__name__}));raise SystemExit(1)
