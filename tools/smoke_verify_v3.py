"""Sol-free v3 checks; independent native controls must arrive before measurement."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import cad_agent,cad_run,cad_spec,eval_verify,eval_verify_v3 as evaluation
from tools.cad_verify_v3_guard import Fault,Stop


def smoke(prefix,dev_only=False):
    evaluation.require_controls(ROOT,dev_only=dev_only)
    evaluation.data_check(ROOT)
    base=ROOT/evaluation.DESIGN
    matrix_path=base/'dev/native-matrix.json'
    if not matrix_path.is_file():raise Stop('independent_dev_native_matrix_pending:'+str(matrix_path))
    matrix=json.loads(matrix_path.read_text(encoding='utf-8'))
    if matrix.get('schema')!='cad-harness.verify-dev-matrix.v3' or matrix.get('author')!='gemini':raise Stop('independent_dev_matrix_contract')
    if not prefix.endswith('-mvp1'):raise ValueError('mvp_suffix_required')
    directory=cad_agent.new_run_dir(ROOT,prefix);rows=[];stopped=None

    def attempt(folder,source,variant,expected,fault=None,generator='agent'):
        out=directory/(folder.name+'-'+variant+'-mvp1')
        args=cad_run.parser().parse_args(['--script',str(source),'--out-dir',str(out),'--task',folder.name,
            '--timeout-s','300','--recipe','freecadcmd','--probe-profile','verify-v3','--generator',generator,'--gold',str(folder/'gold.json')])
        result,code=cad_run.run_attempt(args)
        native=((result.get('measurements') or {}).get('editability') or {}).get('native_valid')
        passing=expected['geometry'] and expected['editability']
        ok=(result.get('geometry_ok') is expected['geometry'] and result.get('editability_ok') is expected['editability']
            and native is True and result.get('probe_pass') is passing and code==(0 if passing else 1)
            and result.get('cad_exit_code')==0 and result.get('script_completed') is True
            and result.get('document_closed') is True and result.get('cleanup_status')=='exited'
            and (not passing or eval_verify.result_pass(result)))
        if fault:
            fault.observe(result,1);ok &= all(fault.record.get(k) for k in ('reached','injected','established','detected'))
        row=dict(case=folder.name,variant=variant,ok=bool(ok),expected=expected,geometry=result.get('geometry_ok'),
            editability=result.get('editability_ok'),measurements=result.get('measurements'),predicate_details=result.get('predicate_details'),
            stage_statuses=result.get('stage_statuses'),fault=fault.record if fault else None,out_dir=out.relative_to(ROOT).as_posix(),sol_calls=0)
        rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
        if not ok:raise Stop('native_control_disagreement:'+folder.name+'/'+variant+'; derive frozen description first; no gold edits; restart whole batch after authorized dev/fixture fix')
    try:
        # Dev rules are calibrated before any holdout measurement.
        required_positive={'direct_depth','radius_difference','diameter_difference','revolved_profile','annular_cut','construction_depth','expression_radius','symmetric_half_width'}
        required_negative={'uncontrolled_bottom','wrong_role','wrong_width','connected_unrelated','disconnected_loop','disconnected_ray','unused_sketch','inactive','reference','origin_only_depth','inoperative_property'}
        entries=matrix.get('entries',[])
        if {e['id'] for e in entries if e['expected']==dict(geometry=True,editability=True)}!=required_positive or {e['id'] for e in entries if e['expected']==dict(geometry=True,editability=False)}!=required_negative:
            raise Stop('dev_matrix_coverage_contract')
        for e in entries:
            source=evaluation.safe_file(ROOT,e['source']);attempt(base/'dev/D1',source,e['id'],e['expected'])
        # Gemini declares the native edit/anchor; Codex authors its analytic dev
        # gold before measurement. Neither original gold nor holdout is edited.
        edits=matrix.get('parameter_edits',[])
        if {(e['role'],e['delta_mm']) for e in edits}!={('groove_depth',.5),('groove_width',1)}:raise Stop('dev_parameter_edit_contract')
        for e in edits:
            folder=evaluation.safe_file(ROOT,e['folder']);source=evaluation.safe_file(ROOT,e['source'])
            if not folder.is_relative_to(base/'dev'):raise Stop('parameter_edit_must_use_new_dev')
            attempt(folder,source,'parameter-edit-'+e['role'],dict(geometry=True,editability=True))
        if not dev_only:
            for c in ('G1','G2','G3','G4','G5','G6','S3','A4','C4','C5','F4','F5','F6'):
                folder=base/'test'/c;offline=json.loads((folder/'offline.json').read_text(encoding='utf-8'))
                if offline.get('positive')!=dict(geometry=True,editability=True) or offline.get('negative')==dict(geometry=True,editability=True):raise Stop('offline_expectation_contract:'+c)
                if any(type(offline[label].get(k)) is not bool for label in ('positive','negative') for k in ('geometry','editability')):raise Stop('offline_expectation_type:'+c)
                for label in ('positive','negative'):attempt(folder,folder/(label+'.py'),label,offline[label])
            for c in ('F4','F5','F6'):
                folder=base/'test'/c;fault=Fault(folder/'fault.json')
                if c=='F6':
                    candidate=json.loads((folder/'candidate.json').read_text());candidate['holes'][0]['diameter']=6
                    candidate=cad_spec.validate_spec(candidate);injected=cad_spec.compile_spec(fault.inject('spec',candidate))
                else:injected=fault.inject('source',(folder/'positive.py').read_text(encoding='utf-8'))
                source=directory/(c+'-injected.py');source.write_bytes(injected.encode())
                expected=json.loads((folder/'offline.json').read_text())['negative']
                attempt(folder,source,'fault-injected',expected,fault,'compiler' if c=='F6' else 'agent')
    except (OSError,ValueError,KeyError,TypeError) as exc:stopped=str(exc)
    with (directory/'smoke-summary.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(measured_at=datetime.now(timezone.utc).isoformat(),sol_calls=0,dev_only=dev_only,rows=rows,stop_reason=stopped),stream,ensure_ascii=False,allow_nan=False,indent=2)
    return 0 if rows and not stopped and all(r['ok'] for r in rows) else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-only',action='store_true');p.add_argument('--run');p.add_argument('--dev-only',action='store_true');a=p.parse_args()
    try:
        if a.data_only:
            if a.run or a.dev_only:raise ValueError('data_only_conflict')
            print(json.dumps(evaluation.data_check(ROOT)));return 0
        if not a.run:raise ValueError('run_required')
        return smoke(a.run,a.dev_only)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps(dict(status='stopped',message_code=str(exc))));return 2
if __name__=='__main__':raise SystemExit(main())
