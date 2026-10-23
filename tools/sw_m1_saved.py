"""Checksum-bound continuation from existing owned M1 CAD, no regeneration."""
import copy
import json
from pathlib import Path
import shutil

from tools import sw_m0 as base
from tools.sw_m1_inputs import private_path


class CustodyError(ValueError):
    pass


def record(path):
    path=private_path(path)
    return {'path':str(path),'sha256':base.digest(path),'bytes':path.stat().st_size}


def context(root,public,inputs):
    root=private_path(root);public=Path(public).absolute()
    if not public.is_relative_to(base.ROOT/'reports/sw-m1') or '..' in public.parts:
        raise CustodyError('reuse_public_path')
    manifest=json.loads((public/'manifest.json').read_text(encoding='utf-8'))
    summary=json.loads((public/'summary.json').read_text(encoding='utf-8'))
    rows=json.loads((public/'rows.json').read_text(encoding='utf-8'))
    if (json.loads((root/'input-packet.json').read_text(encoding='utf-8'))!=inputs
            or base.digest(root/'input-packet.json')!=manifest['input_packet_sha256']
            or manifest['scope']!='mechanical_gold_portability_only_not_model_evaluation'
            or summary['status']!='COMPLETE' or len(rows)!=60):
        raise CustodyError('saved_run_binding')
    for name in ('tools/cad_verify_probe.py','tools/cad_verify_v3_probe.py',
                 'tools/cad_verify_v4_s3_judges.py','tools/sw_m0_distance.py'):
        if base.digest(base.ROOT/name)!=manifest['source_sha256'][name]:
            raise CustodyError('original_judges_changed')
    for old,entry in zip(rows,inputs['entries']):
        if any(old.get(k)!=entry[k] for k in ('sequence','group','route','profile')):
            raise CustodyError('saved_case_order')
    return {'root':root,'rows':rows,'summary':summary,'source_manifest_sha256':base.digest(public/'manifest.json'),
            'source_sha256':manifest['source_sha256']}


def prepare(entry,out,source,redo_edit):
    """Verify original job/gold/native/STEP bytes BEFORE any COM or copying."""
    source=private_path(source);out=private_path(out)
    job=json.loads((source/'job.json').read_text(encoding='utf-8'))
    com=json.loads((source/'com-result.json').read_text(encoding='utf-8'))
    keys=('sequence','group','route','profile','gold','gold_path','gold_sha256','card','card_sha256')
    if (any(job.get(k)!=entry.get(k) for k in keys) or private_path(job['out'])!=source
            or base.digest(entry['gold_path'])!=entry['gold_sha256']):
        raise CustodyError('original_job_gold_binding')
    if (com['status']!='PASS' or com.get('stop') or com.get('COM_state_unknown')
            or not com['original_native_unchanged'] or com['final_documents']!=0):
        raise CustodyError('original_native_state_not_safe')
    files={'positive.sldprt':com['native'],'before-reopen.step':com['before_step'],
           'reopened.step':com['reopened_step']}
    for key,name in (('changed_step','edited.step'),('restored_step','restored.step')):
        if key in com.get('edit',{}):files[name]=com['edit'][key]
    if 'negative_step' in com:files['negative.step']=com['negative_step']
    for name,item in files.items():
        path=source/name
        if private_path(item['path'])!=path or base.digest(path)!=item['sha256']:
            raise CustodyError('original_artifact_hash')
    for name in files:
        # New edit artifacts must come only from the new owned edit-copy, not the
        # original edit copy. The original/native and baseline STEP remain exact.
        if redo_edit and name in ('edited.step','restored.step'):continue
        shutil.copyfile(source/name,out/name)
    base.save_json(out/('com-source.json' if redo_edit else 'com-result.json'),com)
    base.save_json(out/'reuse-provenance-private.json',{
        'source_job_sha256':base.digest(source/'job.json'),
        'source_com_sha256':base.digest(source/'com-result.json'),
        'artifacts':files,'new_native_generation':False,'redo_owned_edit_only':redo_edit})
    return com


def consumed_parameter(plan,native_features):
    """Rectangles: last finite pocket before through holes; finish if present."""
    if plan['profile'] in ('rect_prism','rect_stack') and not plan.get('finish'):
        regions=plan.get('regions') or [dict(bounds=plan['bbox'])]
        index=len(regions)+len(plan.get('pockets',[]))-1
        feature=native_features['features'][index]
        prefix='M1_Cut_' if plan.get('pockets') else 'M1_Boss_'
        if not feature['name'].startswith(prefix):raise CustodyError('consumed_feature_identity')
        return 'D1@'+feature['name']
    return native_features['edit_parameter']


def copied_native_result(out,plan):
    old=json.loads((out/'com-source.json').read_text(encoding='utf-8'))
    features=copy.deepcopy(old['native_features'])
    features['edit_parameter']=consumed_parameter(plan,features)
    return dict(native_features=features,native=record(out/'positive.sldprt'),
        before_step=record(out/'before-reopen.step'),reopened_step=record(out/'reopened.step'),
        new_native_generation=False,source_native_sha256=old['native']['sha256'])
