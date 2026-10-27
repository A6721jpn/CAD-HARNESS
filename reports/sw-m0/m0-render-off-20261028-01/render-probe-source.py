"""Zero-model M0 control: only owned document view refresh is disabled.

Original fixture, feature calls, native edit and neutral judge are unchanged.
Never launches/quits SolidWorks, never changes application/registry preferences.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base,sw_h0_cad as cad


def worker(out):
    class RenderingOffSession(base.Session):
        def adopt(self,doc):
            result=super().adopt(doc)
            view=doc.ActiveView
            if view is None:raise RuntimeError('owned_model_view_missing')
            view.EnableGraphicsUpdate=False
            if bool(view.EnableGraphicsUpdate):raise RuntimeError('owned_view_refresh_disable_unverified')
            self.events.write(json.dumps(dict(event='owned_view_refresh_disabled',at=base.utc()))+'\n')
            return result
    # This worker process has no concurrent callers. The on-disk M0 is unedited.
    base.Session=RenderingOffSession
    return base.com_worker(out)


def run(name):
    out=base.output_path(name);out.mkdir(parents=True,exist_ok=False)
    lock=base.OUTPUTS/'session.lock'
    with lock.open('x',encoding='utf-8') as file:
        json.dump(dict(scope='M0-owned-view-render-isolation',at=base.utc(),pid=os.getpid(),out=str(out)),file)
    started=time.perf_counter();unsafe=True
    result=dict(scope='M0-owned-view-render-isolation',status='FAIL',paid_model_calls=0,
        out=str(out),started_at=base.utc(),only_change='owned IModelView.EnableGraphicsUpdate=False',
        source_sha256={name:base.digest(ROOT/name) for name in
            ('tools/sw_m0.py','tools/sw_m0_probe.py','tools/sw_m0_render_probe.py','tools/cad_spec_probe.py')})
    try:
        code,pid,_=cad.child([str(base.SW_PYTHON),'-B',str(Path(__file__).resolve()),'--worker',str(out)],
            out,'com',300,SW=True)
        result.update(com_exit=code,client_pid=pid)
        com=json.loads((out/'com-result.json').read_text(encoding='utf-8'))
        unsafe=bool(com.get('COM_state_unknown') or str(com.get('error','')).startswith('STOP_')
            or 'STOP_' in str(com.get('cleanup_error','')) or com.get('final_documents')!=0)
        result.update(SW_pid=com.get('solidworks_pid'),SW_revision=com.get('solidworks_revision'),
            COM_state_unknown=unsafe,initial_documents=com.get('initial_documents'),
            final_documents=com.get('final_documents'))
        if code or com['status']!='PASS':raise RuntimeError('render_isolation_COM_failed')
        code,_,_=cad.child(cad.sdk('tools.sw_m0_probe',out),out,'judge',300)
        judge=json.loads((out/'judge-result.json').read_text(encoding='utf-8'))
        result.update(judge_exit=code,neutral_checks=judge)
        if code==0 and judge['status']=='PASS' and com.get('final_documents')==0:
            result['status']='PASS'
    except BaseException as exc:
        if str(exc).startswith('STOP_SW_'):unsafe=True
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(manual_recovery_required=unsafe,finished_at=base.utc(),
            total_seconds=time.perf_counter()-started)
        base.save_json(out/'result.json',result)
        if not unsafe:lock.unlink()
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--out');action.add_argument('--worker')
    args=parser.parse_args()
    raise SystemExit(worker(base.output_path(args.worker)) if args.worker else run(args.out))
