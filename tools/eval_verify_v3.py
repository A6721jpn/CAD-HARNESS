"""VERIFY v3: new frozen holdout, separate completion cohort; aggregate launches nothing."""
import argparse
import ast
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import time

if __package__:
    from . import cad_agent, cad_run, cad_run_probes, cad_spec, eval_mvp, eval_verify
    from . import cad_verify_v3_agent as agent, cad_verify_v3_probe as probe
    from .cad_spec_probe import read_json
    from .cad_verify_v3_guard import Guard, Fault, Stop, q_score, Budget
else:
    import cad_agent, cad_run, cad_run_probes, cad_spec, eval_mvp, eval_verify
    import cad_verify_v3_agent as agent, cad_verify_v3_probe as probe
    from cad_spec_probe import read_json
    from cad_verify_v3_guard import Guard, Fault, Stop, q_score, Budget

ROOT=Path(__file__).resolve().parents[1]
DESIGN="design/cad-harness-verify-v3"
CODE=tuple(dict.fromkeys((*eval_verify.CODE,
    "tools/cad_verify_v3_probe.py", "tools/cad_verify_v3_guard.py", "tools/cad_verify_v3_agent.py",
    "tools/eval_verify_v3.py", "tools/smoke_verify_v3.py", "tools/fixtures/verify_v3_native.py",
    "tools/test_verify_v3.py", "tools/test_support.py",
    "design/cad-harness-verify-v3/gold-schema.json", "tools/cad_verify_v2_probe.py", "tools/cad_verify_v3_diagnostics.py",
    "design/cad-harness-verify-v3/call-cap.md", "design/cad-harness-verify-v3/native-controls-handoff.md")))
GROUPS=("dev","legacy","mvp","geometry","q","completion","fault")
CAPS={"source":4,"spec":3,"ask":1,"completion":4,"offline":0,"mvp":3}
SOLFIX_VERSION='verify-v3-reviewed-r1-solfix'
RESUME_DEADLINE='none (user decision 17:08)'
SOLFIX_CODE=frozenset(('tools/cad_verify_v3_agent.py','tools/cad_verify_v3_guard.py','tools/eval_verify_v3.py','tools/test_verify_v3.py'))
SOLFIX_DOCS=frozenset(DESIGN+'/'+n for n in ('SOLFIX-CONSENSUS.md','SOLFIX-BRIEF.md','SOL-FAILURE.md','solfix-codex.md'))
RERUN2_IDS=frozenset(('geometry-G5-r1','geometry-G1-r2'))
RERUN2_SPENT=105
sha=eval_verify.sha
write_json=eval_verify.write_json
result_pass=eval_verify.result_pass
gates=eval_verify.gates
wilson=eval_verify.wilson


def require_controls(root,*,dev_only=False):
    """Gemini's independent controls are a required pre-freeze handoff, not stubs."""
    root=Path(root).resolve()
    names=['tools/fixtures/verify_v3_native.py',DESIGN+'/dev/native-matrix.json',DESIGN+'/dev/D1/gold.json']
    if not dev_only:
        for c in ('G1','G2','G3','G4','G5','G6','S3','A4','C4','C5','F4','F5','F6'):
            names.extend(DESIGN+'/test/'+c+'/'+n for n in ('positive.py','negative.py','offline.json'))
        names.extend(DESIGN+'/test/'+c+'/fault.json' for c in ('F4','F5','F6'))
        names.extend((DESIGN+'/test/F4/candidate.py',DESIGN+'/test/F5/candidate.py',DESIGN+'/test/F6/candidate.json'))
    missing=[name for name in names if not safe_file(root,name).is_file()]
    if missing:raise Stop('independent_native_controls_pending:'+','.join(missing))
    matrix=read_json((root/DESIGN/'dev/native-matrix.json').read_text(encoding='utf-8'))
    if matrix.get('schema')!='cad-harness.verify-dev-matrix.v3' or matrix.get('author')!='gemini':raise Stop('independent_dev_matrix_contract')
    names=[entry['source'] for entry in matrix.get('entries',[])]
    for edit in matrix.get('parameter_edits',[]):
        folder=safe_file(root,edit['folder'])
        if not folder.is_relative_to(root/DESIGN/'dev'):raise Stop('parameter_edit_must_use_new_dev')
        names.extend((edit['source'],edit['folder']+'/gold.json'))
    missing=[name for name in names if not safe_file(root,name).is_file()]
    if missing:raise Stop('independent_native_controls_pending:'+','.join(missing))


def expected_order():
    entries=[]
    def add(group,case,round_,route,minimum,maximum):
        entries.append((group,case,round_,route,minimum,maximum))
    for c,r,n in (('D1','source',2),('D2','spec',1),('D3','ask',1)):add('dev',c,1,r,n,n)
    for c in ('A-good','A-broken','B-good','B-broken'):add('legacy',c,1,'offline',0,0)
    for c in ('P1','P2','P4','P5','P3'):
        for r in (1,2):add('mvp',c,r,'mvp',1,3)
    for r in (1,2):
        for c in ('G1','G2','G3','G4','G5','G6','S3'):
            source=c in ('G1','G2','G3','G4','G5');add('geometry',c,r,'source' if source else 'spec',2 if source else 1,4 if source else 3)
    for c in ('G6','S3'):add('geometry',c,3,'spec',1,3)
    for r in (4,5):add('geometry','S3',r,'spec',1,3)
    for r in (1,2,3):add('q','A4',r,'spec',1,3)
    for r in range(1,6):
        for c in ('A5','A6'):add('q',c,r,'ask',1,1)
    for r in (1,2,3):
        for c in ('C4','C5'):add('completion',c,r,'completion',2,4)
    for r in (1,2):
        for c in ('F4','F5','F6'):add('fault',c,r,'spec' if c=='F6' else 'source',2 if c=='F6' else 3,3 if c=='F6' else 4)
    return entries


def data_check(root=ROOT):
    """Read-only Phase 2 byte/schema/rubric/order checks. No manifest or reports."""
    root=Path(root).resolve();order=read_json((root/DESIGN/'run-order.json').read_text(encoding='utf-8'));validate_order(order)
    seen=set()
    for e in order['entries']:
        if e['group'] in ('legacy','mvp') or e['case'] in seen:continue
        seen.add(e['case']);gold,raw,rubric,answer=inputs(root,e)
        if gold:
            g=probe.load_gold(gold)
            payload=raw+b'\n'+answer if answer is not None else raw
            if g['description'].encode()!=payload:raise Stop('gold_payload_binding:'+e['case'])
        if rubric:
            for label,expected in (('positive',1),('negative',0)):
                value=rubric[label];first=dict(kind='needs_clarification',fields=agent.clarification(value),raw=value)
                if q_score(first,False,e['case'],rubric)[0]!=expected:raise Stop('rubric_control:'+e['case'])
    for f,b in (('F4','G1'),('F5','G5'),('F6','G6')):
        if (root/DESIGN/'test'/f/'description.txt').read_bytes()!=(root/DESIGN/'test'/b/'description.txt').read_bytes():
            raise Stop('fault_description_binding')
    return dict(cases=len(seen),episodes=len(order['entries']),planned_calls=order['planned_calls'],max_calls=order['max_calls'],sol_calls=0,cad_attempts=0)


def safe_file(root,name):
    p=root/name
    if not isinstance(name,str) or not p.resolve().is_relative_to(root) or p.resolve()!=p:
        raise Stop("linked_or_external_file:"+str(name))
    return p


def cli_identity(codex,runner=None):
    executable=Path(shutil.which(codex) or codex).resolve()
    if not executable.is_file(): raise Stop("cli_executable_missing")
    completed=(runner or subprocess.run)([str(executable),"--version"],capture_output=True,text=True,encoding="utf-8",
        errors="replace",shell=False,stdin=subprocess.DEVNULL,timeout=30)
    if completed.returncode!=0 or not completed.stdout.strip(): raise Stop("cli_version_failed")
    return dict(path=str(executable),sha256=sha(executable.read_bytes()),version=cad_agent.clean(completed.stdout.strip()))


def freeze(root=ROOT,version="verify-v3-phase2-uncommitted",implementation_commit="pending_supervisor",plan_commit="pending_supervisor",codex=None,runner=None):
    """Never overwrite; reviewed commit identities are supplied by the supervisor."""
    root=Path(root).resolve(); base=root/DESIGN
    eval_mvp.valid_name(version)
    names=set(CODE)
    if version==SOLFIX_VERSION:names.update(SOLFIX_DOCS)
    names.update(p.relative_to(root).as_posix() for p in (root/"design/cad-harness-mvp/eval-v1").glob("*.json"))
    names.update(DESIGN+"/"+n for n in ("PLAN-V3-CONSENSUS.md","run-order.json"))
    for part in ("test","dev"):
        names.update(p.relative_to(root).as_posix() for p in (base/part).rglob("*") if p.is_file())
    require_controls(root)
    data_check(root)
    hashes={n:sha(safe_file(root,n).read_bytes()) for n in sorted(names)}
    if implementation_commit!="pending_supervisor" and not re.fullmatch(r"[0-9a-f]{7,40}",implementation_commit):
        raise ValueError("implementation_commit_required")
    if plan_commit!="pending_supervisor" and not re.fullmatch(r"[0-9a-f]{7,40}",plan_commit):
        raise ValueError("plan_commit_required")
    value=dict(schema="cad-harness.verify-sha.v3",profile="verify-v3",version=version,created_at=cad_agent.utc(),
        local_commit=implementation_commit,plan_commit=plan_commit,files=hashes,
        cli=cli_identity(codex,runner) if codex else None,
        agents_sha256=cad_agent.agents_identity(root),settings=dict(model=cad_agent.MODEL,effort=cad_agent.EFFORT,
            disabled=list(cad_agent.DISABLED),sandbox="read-only"))
    if version.startswith("verify-v3-reviewed-") and not value["cli"]: raise Stop("reviewed_cli_freeze_required")
    if version==SOLFIX_VERSION:
        original=read_json((base/'SHA256.run-r1.json').read_text(encoding='utf-8'))
        transition(root,original,value)
    validate_order(read_json((base/"run-order.json").read_text(encoding="utf-8")))
    write_json(base/"SHA256.json",value)
    return value


def verify_frozen(root,manifest):
    if manifest.get("schema")!="cad-harness.verify-sha.v3" or manifest.get("profile")!="verify-v3":
        raise Stop("verify_v3_manifest_contract")
    for name,expected in manifest["files"].items():
        if sha(safe_file(root,name).read_bytes())!=expected: raise Stop("sha_mismatch:"+name)
    if cad_agent.agents_identity(root)!=manifest["agents_sha256"]: raise Stop("inherited_agents_changed")
    settings=dict(model=cad_agent.MODEL,effort=cad_agent.EFFORT,disabled=list(cad_agent.DISABLED),sandbox="read-only")
    if settings!=manifest["settings"]: raise Stop("model_settings_changed")
    cli=manifest.get("cli")
    if cli and sha(Path(cli["path"]).read_bytes())!=cli["sha256"]: raise Stop("cli_sha_mismatch")


def validate_order(order):
    entries=order["entries"]
    expected=Counter({("dev","D1"):1,("dev","D2"):1,("dev","D3"):1,
        **{("legacy",c):1 for c in ("A-good","A-broken","B-good","B-broken")},
        **{("mvp",c):2 for c in eval_mvp.ORDER},**{("geometry",c):2 for c in ("G1","G2","G3","G4","G5")},
        ("geometry","G6"):3,("geometry","S3"):5,("q","A4"):3,("q","A5"):5,("q","A6"):5,
        ("completion","C4"):3,("completion","C5"):3,**{("fault",c):2 for c in ("F4","F5","F6")}})
    if (order.get("schema")!="cad-harness.verify-order.v3" or order.get("profile")!="verify-v3"
            or len(entries)!=60 or len({e["id"] for e in entries})!=60
            or [e["sequence"] for e in entries]!=list(range(1,61))
            or Counter((e["group"],e["case"]) for e in entries)!=expected
            or sum(e["min_calls"] for e in entries)!=83 or order.get("planned_calls")!=83
            or sum(e["max_calls"] for e in entries)!=163 or order.get("max_calls")!=163
            or sum(e["scored"] for e in entries)!=51 or order.get("core_count")!=51 or order.get("completion_count")!=6):
        raise Stop("verify_v3_order_contract")
    aliases={**{f"G{i}":f"V{i}" for i in range(1,7)},"S3":"S1","A4":"Q1","A5":"Q2","A6":"Q3",
             "F4":"F1","F5":"F2","F6":"F3"}
    for e in entries:
        eval_mvp.valid_name(e["id"])
        if e["route"] not in CAPS or e["group"] not in GROUPS: raise Stop("order_route_contract")
        cap=3 if e["group"]=="mvp" else CAPS[e["route"]]
        if not 0<=e["min_calls"]<=e["max_calls"]<=cap: raise Stop("order_call_contract")
        excluded=e["group"] in ("dev","completion")
        if e["scored"] is excluded or e["bar_class"]!=(None if excluded else aliases.get(e["case"],e["case"])):
            raise Stop("order_class_contract")
    actual=[tuple(e[k] for k in ('group','case','round','route','min_calls','max_calls')) for e in entries]
    if actual!=expected_order():raise Stop('signed_order_or_cap_mismatch')


def load(root,reviewed=True):
    base=root/DESIGN
    manifest=read_json((base/"SHA256.json").read_text(encoding="utf-8"))
    order=read_json((base/"run-order.json").read_text(encoding="utf-8"))
    verify_frozen(root,manifest); validate_order(order)
    if reviewed and (not manifest["version"].startswith("verify-v3-reviewed-")
            or not manifest.get("cli")
            or any(not re.fullmatch(r"[0-9a-f]{7,40}",manifest.get(k,"")) for k in ("local_commit","plan_commit"))):
        raise Stop("supervisor_reviewed_freeze_required")
    return manifest,order


def paths(root,prefix):
    eval_mvp.valid_name(prefix)
    p=root/"reports/cad-run"/(prefix+"-verify-v3-suite-mvp1")
    if p.resolve()!=p: raise ValueError("linked_suite_path")
    return p


def run_name(prefix,entry): return prefix+"-"+entry["id"]+"-mvp1"


def driver_path(root,name):
    if name.endswith(('-mvp1-resume1','-mvp1-rerun2')):
        eval_mvp.valid_name(name)
        return safe_file(root,'reports/cad-run/'+name)
    return eval_mvp.run_path(root,name)


def inputs(root,entry):
    group,case=entry["group"],entry["case"]
    if group=="mvp":
        s=eval_mvp.suite(root)[case]
        return s["path"],s["gold"]["description"].encode("utf-8"),None,None
    base=root/DESIGN/"test"/case
    if group=="dev": base=root/DESIGN/"dev"/case
    raw=(base/"description.txt").read_bytes()
    if entry.get('description_sha256')!=sha(raw):raise Stop('order_description_binding')
    if raw.startswith(b"\xef\xbb\xbf") or raw.endswith(b"\n") or b"\r" in raw: raise Stop("description_bytes_contract")
    rubric=read_json((base/"rubric.json").read_text(encoding="utf-8")) if entry["first_response"] or group=="completion" else None
    gold=base/"gold.json" if (base/"gold.json").is_file() else None
    answer=None
    if group=="completion":
        answer=(base/"answer.txt").read_bytes()
        if answer.startswith(b"\xef\xbb\xbf") or answer.endswith(b"\n") or b"\r" in answer: raise Stop("answer_bytes_contract")
        expected=dict(schema="cad-harness.verify-completion-binding.v3",case_id=case,description_sha256=sha(raw),
            answer_sha256=sha(answer),completion_input_sha256=sha(raw+b"\n"+answer),separator_hex="0a")
        if read_json((base/"binding.json").read_text(encoding="utf-8"))!=expected: raise Stop("completion_sha_binding")
        if any(entry.get(k)!=expected[k] for k in ('answer_sha256','completion_input_sha256')):raise Stop('order_answer_binding')
    if rubric and (rubric["case_id"]!=case or rubric["description_sha256"]!=sha(raw)): raise Stop("rubric_binding")
    return gold,raw,rubric,answer


def harness_failure(report):
    code=str(report.get("message_code") or "")
    if code.startswith("harness") or "unsupported_probe" in code:
        return "harness:"+code
    return eval_verify.harness_failure(report)


def empty_row(entry,name,reason=None):
    row=eval_verify.empty_row(entry,name,reason)
    row.update(parse_repairs=0,repair_calls=0,repair_eligible=False,natural_repair_eligible=False,
               completion_reached=False,initial_q_score=None,initial_critical_invention=False,
               post_answer_first_attempt_pass=False,repair_success=False,
               episode_stop_reason=None,manifest_entry=dict(entry))
    return row


def first_response(final):
    """Re-derive Q gates from the actual first final file, including invalid raw values."""
    first=dict(kind="invalid",sha256=cad_agent.digest(final))
    try:
        raw=cad_spec.read_json(cad_agent.strip_final_fence(final,"json","spec")); first["raw"]=raw
        if isinstance(raw,dict) and set(raw)=={"unsupported"}:
            if isinstance(raw["unsupported"],list) and raw["unsupported"] and all(isinstance(x,str) and x for x in raw["unsupported"]):
                first["kind"]="unsupported"
        elif isinstance(raw,dict) and set(raw)=={"needs_clarification"}:
            first["fields"]=agent.clarification(raw); first["kind"]="needs_clarification"
        else:
            spec=cad_spec.validate_spec(raw); first["kind"]="spec"
            b=spec.get("regions",[{}])[0].get("bounds",[]) if spec.get("regions") else []
            first["binding_defaults_ok"]=len(b)==6 and abs(b[0]+b[1])<1e-9 and abs(b[2]+b[3])<1e-9 and b[4]==0
    except ValueError: pass
    return first


def check_calls(report,entry,raw,answer,where):
    calls=report["calls"]; n=report["llm_calls"]; attempts=report["attempts"]
    solfix=report.get('provider_policy')==agent.PROVIDER_POLICY
    slot_calls=[c for c in calls if not solfix or c.get('slot_consumed') is True]
    if (type(n) is not int or n!=len(slot_calls) or not 0<=n<=entry["max_calls"]
            or type(report["cad_attempts"]) is not int or report["cad_attempts"]!=len(attempts)
            or len(attempts)>(3 if entry["group"]=="mvp" else 0 if entry["group"]=="dev" or entry["route"]=="ask" else 2)):
        raise ValueError("budget_binding")
    purposes=Counter(c.get("purpose",c.get("kind")) for c in slot_calls)
    if solfix:
        if report.get('logical_calls')!=len(slot_calls):raise ValueError('logical_call_binding')
        if (report.get('transport_attempts')!=len(calls) or report.get('provider_rejected_attempts')!=len(calls)-n
                or report.get('provider_wait_s')!=sum(c.get('backoff_s',0) for c in calls)):raise ValueError('provider_counter_binding')
        check_transport(report,where)
    if entry["group"]!="mvp":
        if any(p not in ("question","interpretation","source","parse_repair","repair") or count>1 for p,count in purposes.items()):
            raise ValueError("purpose_budget_binding")
        if report["budget_counts"]!={p:purposes[p] for p in ("question","interpretation","source","parse_repair","repair")}:
            raise ValueError("purpose_counter_binding")
        if entry["group"]=="dev" and (purposes["repair"] or purposes["parse_repair"]): raise ValueError("preview_budget_binding")
        if purposes["parse_repair"]!=report["parse_repairs"] or purposes["repair"]!=report["repair_calls"]:
            raise ValueError("repair_counter_binding")
    generation_closed=False; repair_seen=False
    for index,c in enumerate(calls):
        snapshot=c.get("quota_snapshot")
        expected=sha(raw+b"\n"+answer) if answer is not None and (c.get('purpose')!='question' if solfix else index>0) else sha(raw)
        if (c.get("prompt_sha256")!=expected or not snapshot or snapshot["decision"]!="allow"
                or not 0<=snapshot["age_s"]<=300 or not 0<=snapshot["used_percent"]<55):
            raise ValueError("call_quota_or_payload_binding")
        if entry["group"]!="mvp":
            purpose=c["purpose"]
            if c.get("invoked") is not True or c.get("call")!=index+1 or c.get("stage") not in ("initial","repair"):
                raise ValueError("real_call_binding")
            if purpose=="repair":
                repair_seen=True
                if c["stage"]!="repair" or not report["repair_eligible"]: raise ValueError("repair_stage_binding")
            if c["stage"]=="repair" and (not repair_seen or purpose not in ("repair","parse_repair")):
                raise ValueError("generation_after_cad")
            if generation_closed and c["stage"]=="initial": raise ValueError("stage_regression")
            generation_closed |= c["stage"]=="repair"
            cap=180 if purpose=="repair" else 60 if purpose=="parse_repair" else 450
            if not 0<c["timeout_s"]<=cap or not 0<=c["elapsed_s"]<900: raise ValueError("call_time_binding")
            if solfix or c['kind']=='source' or c['stage']=='repair':
                artifacts=c.get('context_artifacts')
                if not artifacts or set(artifacts)!={'prompt','context'}:raise ValueError('context_artifacts_missing')
                for key,item in artifacts.items():
                    path=where.parents[2]/item['path']
                    if path.resolve()!=path or not path.is_relative_to(where):raise ValueError('context_artifact_path')
                    if sha(path.read_bytes())!=item['sha256'] or item['sha256']!=c[key+'_sha256']:raise ValueError('context_artifact_hash')
    return purposes


def check_transport(report,where):
    root=where.parents[2];previous={};accepted=0;seed=report.get('prior_provider_attempts',0)
    for c in report['calls']:
        logical=c.get('logical_call');attempt=c.get('transport_attempt')
        if logical!=accepted+1 or type(attempt) is not int or attempt<1:raise ValueError('transport_order_binding')
        prior=previous.get(logical)
        if prior:
            if not prior['provider_rejected'] or attempt!=prior['transport_attempt']+1 or any(c[k]!=prior[k] for k in ('kind','purpose','stage','argv_sha256','prompt_sha256','context_sha256')):raise ValueError('provider_retry_binding')
            if prior.get('backoff_s')!=agent.PROVIDER_WAIT_S or prior.get('wait_requested_s')!=agent.PROVIDER_WAIT_S:raise ValueError('provider_backoff_binding')
        elif attempt!=(seed+1 if logical==1 else 1):raise ValueError('provider_seed_binding')
        artifacts=c.get('transport_artifacts')
        if not artifacts or set(artifacts)!={'stdout','stderr'}:raise ValueError('transport_capture_missing')
        for item in (*artifacts.values(),c['provider_artifact']):
            p=safe_file(root,item['path'])
            if not p.is_relative_to(where) or sha(p.read_bytes())!=item['sha256']:raise ValueError('transport_artifact_binding')
        for item in artifacts.values():
            size=min(item['full_bytes'],16384)
            path=safe_file(root,item['path'])
            if path.stat().st_size!=item['bytes'] or not max(0,size-3)<=item['bytes']<=size:raise ValueError('transport_capture_limit')
            path.read_text(encoding='utf-8')
        summary=read_json(safe_file(root,c['provider_artifact']['path']).read_text(encoding='utf-8'))
        if summary!=c['provider_summary'] or c.get('provider_rejected')!=summary['provider_rejected']:raise ValueError('provider_classification_binding')
        if summary.get('source')=='stdout' and summary['full_sha256']!=artifacts['stdout']['full_sha256']:raise ValueError('provider_stream_hash_binding')
        if summary.get('source')=='rollout' and summary.get('session_id')!=c.get('session_id'):raise ValueError('provider_session_binding')
        if summary['provider_rejected'] and (not summary.get('parse_complete',True) or summary['assistant_output'] or not summary['error_infos'] or not set(summary['error_infos'])<=agent.PROVIDER_ALLOWLIST or c.get('slot_consumed')):raise ValueError('provider_allowlist_binding')
        if not summary['provider_rejected'] and not c.get('slot_consumed'):raise ValueError('provider_slot_binding')
        if c['slot_consumed']:accepted+=1
        previous[logical]=c


def check_attempts(root,entry,report,where,gold):
    for index,a in enumerate(report["attempts"]):
        out=safe_file(root,a["out_dir"])
        if not out.is_relative_to(where): raise ValueError("attempt_path_binding")
        r=read_json((out/"result.json").read_text(encoding="utf-8"))
        if r!=a["result"] or sha((out/"input.py").read_bytes())!=a["source_sha256"]:
            raise ValueError("attempt_result_binding")
        profile="mvp-v1" if entry["group"]=="mvp" else "verify-v3"
        if (r.get("schema")!="cad-harness.cad_run.v0" or r.get("probe_profile")!=profile or r.get("task_id")!=entry["case"]
                or r.get("script_sha256")!=a["source_sha256"] or r.get("gold_sha256")!=sha(gold.read_bytes())
                or sha((out/"gold.json").read_bytes())!=r["gold_sha256"]): raise ValueError("attempt_gold_binding")
        if profile=="verify-v3":
            statuses=r.get('stage_statuses');measurements=r.get('stage_measurements')
            if not isinstance(statuses,dict) or set(statuses)!={'build','geometry','editability','export','reimport'} or not isinstance(measurements,dict) or set(measurements)!=set(statuses):
                raise ValueError('phase_status_binding')
            if any(v not in ('pass','fail','not_reached') for v in statuses.values()):raise ValueError('phase_status_value')
            for stage,flag in (('geometry','geometry_ok'),('editability','editability_ok')):
                expected='pass' if r.get(flag) is True else 'fail' if r.get(flag) is False else 'not_reached'
                if statuses[stage]!=expected:raise ValueError('phase_gate_binding')
            if any(measurements[k] is not None for k,v in statuses.items() if v=='not_reached'):raise ValueError('unexecuted_measurement')
            if (r.get('geometry_ok') is False or r.get('editability_ok') is False) and (statuses['export']!='not_reached' or statuses['reimport']!='not_reached'):
                raise ValueError('pre_export_phase_binding')
            if a.get("stage")!=("initial" if index==0 else "repair") or a.get("attempt")!=index+1:
                raise ValueError("cad_stage_binding")
            if not 0<=a["started_elapsed_s"]<=a["ended_elapsed_s"]<=report["wall_ms"]/1000:
                raise ValueError("cad_time_binding")
            if index and r.get("timeout_s",91)>90: raise ValueError("repair_cad_limit")
            limit=90 if index else 300
            if not 0<a["build_timeout_s"]<=limit or not 0<a["reimport_timeout_s"]<=limit:
                raise ValueError("cad_timeout_binding")
        if result_pass(r):
            if set(r.get("artifact_sha256",{}))!={"model.FCStd","model.step"}: raise ValueError("artifact_hashes_missing")
            for filename,expected in r["artifact_sha256"].items():
                if sha((out/filename).read_bytes())!=expected: raise ValueError("artifact_sha_changed")
            if read_json((out/"verify-result.json").read_text(encoding="utf-8"))!=r["verification"]:
                raise ValueError("artifact_report_binding")


def fault_source_sha(injected):
    # solfix-a2: mirror the driver, which re-extracts the injected source (source_from_final) before CAD;
    # with a CRLF fixture checkout that pass drops the final CR, so hashing the raw injection falsely failed (F4-r1).
    return sha(cad_agent.source_from_final(injected).encode("utf-8"))


def check_fault(root,entry,report,where):
    actual=report["fault"]; rule=Fault(root/DESIGN/"test"/entry["case"]/"fault.json")
    if actual["fault_id"]!=rule.record["fault_id"]: raise ValueError("fault_id_binding")
    if not actual["injected"]:
        if actual["reached"] or actual["established"] or actual["detected"]: raise ValueError("fault_not_reached_binding")
        return actual
    attempts=report["attempts"]
    if not actual["reached"] or not attempts: raise ValueError("fault_injection_binding")
    first=attempts[0]; kind=rule.rule["kind"]
    c=next((c for c in reversed(report["calls"]) if c["stage"]=="initial" and c["kind"]==kind),None)
    if not c: raise ValueError("fault_call_binding")
    final=(where/("last-c%d.txt"%c["call"])).read_text(encoding="utf-8")
    original=cad_agent.source_from_final(final) if kind=="source" else cad_spec.validate_spec(
        cad_spec.read_json(cad_agent.strip_final_fence(final,"json","spec")))
    injected=rule.inject(kind,original)
    if any(actual.get(k)!=rule.record.get(k) for k in ("reached","injected","original_sha256","injected_sha256","candidate_sha256")):
        raise ValueError("fault_candidate_binding")
    if kind=="source":
        if first["source_sha256"]!=fault_source_sha(injected): raise ValueError("fault_source_binding")
    else:
        path=where/("build-spec-c%d.json"%c["call"])
        if read_json(path.read_text(encoding="utf-8"))!=injected or first["source_sha256"]!=sha(cad_spec.compile_spec(injected).encode("utf-8")):
            raise ValueError("fault_spec_binding")
    rule.observe(first["result"],c["call"])
    if any(actual.get(k)!=rule.record.get(k) for k in ("observed","actual_call","established","detected")):
        raise ValueError("fault_observation_binding")
    return actual


def record(root,entry,name):
    row=empty_row(entry,name); where=driver_path(root,name)
    try:
        report=read_json((where/"driver-run.json").read_text(encoding="utf-8"))
        gold,raw,rubric,answer=inputs(root,entry); is_mvp=entry["group"]=="mvp"
        if (report.get("schema")!=("cad-harness.cad_agent.mvp1" if is_mvp else "cad-harness.cad_agent.verify3")
                or report.get("task_id")!=entry["case"] or report.get("run_id")!=name or report.get("mode")!="description"
                or report.get("description_sha256")!=sha(raw) or report.get("gold_sha256")!=(sha(gold.read_bytes()) if gold else None)):
            raise ValueError("driver_binding")
        if not is_mvp and (report.get("probe_profile")!="verify-v3" or report.get("route")!=entry["route"]
                or report.get("preview")!=(entry["group"]=="dev")): raise ValueError("driver_profile_binding")
        if not is_mvp:
            settings=Budget(entry["max_calls"],preview=entry["group"]=="dev").settings()
            if entry["route"]=="ask": settings.update(max_cad_attempts=0,parse_calls=0,repair_calls=0)
            if any(report["settings"].get(k)!=v for k,v in settings.items()): raise ValueError("stage_settings_binding")
        wall=report["wall_ms"]/1000
        if not math.isfinite(wall) or wall<0: raise ValueError("wall_contract")
        purposes=check_calls(report,entry,raw,answer,where)
        row.update(completed=True,wall_s=wall,sol_calls=report["llm_calls"],cad_attempts=report["cad_attempts"],
            tokens=eval_mvp.provider_tokens(report),driver_identity={k:report.get(k) for k in (*eval_mvp.IDENTITY,"shared_probe_sha256")},
            first_response=report.get("first_response"),stop_reason=harness_failure(report),
            parse_repairs=purposes["parse_repair"],repair_calls=purposes["repair"],
            call_kinds=[c.get("purpose",c.get("kind")) for c in report["calls"]])
        row['call_stages']=[c.get('stage') for c in report['calls']]
        if report.get('provider_policy')==agent.PROVIDER_POLICY:
            row.update(provider_rejected_attempts=sum(c.get('provider_rejected',False) for c in report['calls']),
                logical_calls=report['logical_calls'])
            message=report.get('message_code') or ''
            provider_partial=row['provider_rejected_attempts'] and any(k in message for k in ('deadline','quota_','reservation','sha_','insufficient_call_budget'))
            if provider_partial:
                timed=message in ('episode_stage_deadline_exceeded','episode_deadline_exceeded','repair_time_reservation_lost')
                check_attempts(root,entry,report,where,gold)
                # A rejected later call must not erase an already observed
                # question or CAD/fault measurement from this partial episode.
                if report.get('first_response'):
                    final_text=(where/('last-c%d.txt'%report.get('first_response_call',1))).read_text(encoding='utf-8')
                    first=first_response(final_text);actual=report['first_response']
                    if any(actual.get(k)!=v for k,v in first.items()) or actual.get('sha256')!=sha(final_text.encode('utf-8')):raise ValueError('first_response_binding')
                    row['first_response']=first
                    if entry['route']=='ask' or entry['group']=='completion':
                        score,invention=q_score(first,False,entry['case'],rubric)
                        row.update(initial_q_score=score,initial_critical_invention=invention,q_score=score,critical_invention=invention)
                    if entry['group']=='completion':
                        if (report.get('answer_sha256')!=sha(answer) or report.get('completion_input_sha256')!=sha(raw+b'\n'+answer)
                                or report.get('initial_q_score')!=score or report.get('initial_critical_invention')!=invention
                                or read_json((where/'first-response.json').read_text(encoding='utf-8'))!=actual):raise ValueError('completion_report_binding')
                        row['completion_reached']=report.get('completion_reached') is True
                attempts=report['attempts']
                if attempts:
                    first_result,last_result=attempts[0]['result'],attempts[-1]['result']
                    row.update(initial=gates(first_result),final=gates(last_result),initial_stage_statuses=first_result.get('stage_statuses'),
                        final_stage_statuses=last_result.get('stage_statuses'),post_answer_first_attempt_pass=entry['group']=='completion' and result_pass(first_result),
                        repair_eligible=report['repair_eligible'],natural_repair_eligible=report['repair_eligible'] and entry['group'] in ('geometry','q','completion'))
                    if entry['group']=='fault':row['fault']=check_fault(root,entry,report,where)
                row.update(completed=False,passed=False,stop_reason=None if timed else row['stop_reason'] or message,
                    episode_stop_reason=message if timed else None,failure_class='timeout' if timed else row['stop_reason'] or message)
                return row
        if report.get("message_code")=="repair_time_reservation_lost":
            row["episode_stop_reason"]="repair_time_reservation_lost"
        if not report["calls"]:
            row.update(completed=False,failure_class=row["stop_reason"] or "not_invoked"); return row
        if entry["first_response"] or entry["group"]=="completion":
            final=(where/('last-c%d.txt'%report.get('first_response_call',1))).read_text(encoding="utf-8")
            first=first_response(final)
            actual=report.get("first_response") or {}
            if any(actual.get(k)!=v for k,v in first.items()) or actual.get("sha256")!=sha(final.encode("utf-8")):
                raise ValueError("first_response_binding")
            row["first_response"]=first
        check_attempts(root,entry,report,where,gold)
        attempts=report["attempts"]; first=attempts[0]["result"] if attempts else {}; final=attempts[-1]["result"] if attempts else {}
        if report.get("status")=="ok" and not result_pass(final): row["stop_reason"]="harness:false_pass"
        if attempts: row.update(initial=gates(first),final=gates(final),
            initial_stage_statuses=first.get('stage_statuses'),final_stage_statuses=final.get('stage_statuses'))
        row['post_answer_first_attempt_pass']=entry['group']=='completion' and result_pass(first)
        row['repair_success']=row['repair_calls']==1 and report.get('status')=='ok' and result_pass(final)
        if not is_mvp and (report.get('repair_invoked')!=(row['repair_calls']==1) or report.get('repair_success')!=row['repair_success']):raise ValueError('repair_result_binding')
        source=report.get("unsupported_to_source") is True
        if not is_mvp:
            decisions=[]
            for c in report['calls']:
                if c['kind']!='spec':continue
                path=where/('last-c%d.txt'%c['call'])
                if not path.is_file():continue
                try:
                    value=cad_spec.read_json(cad_agent.strip_final_fence(path.read_text(encoding='utf-8'),'json','spec'))
                    _,_,decision=agent.interpretation(value,source_enabled=entry['route']=='source' and c['stage']=='initial')
                    decisions.append(dict(call=c['call'],**decision))
                except ValueError:pass
            if report.get('interpretations')!=decisions:raise ValueError('interpretation_capability_binding')
            origins=[d['unsupported_origin'] for d in decisions if d['unsupported_origin'] is not None]
            origin=origins[-1] if origins else None
            if report.get('unsupported_origin')!=origin or source and origin is None:raise ValueError('unsupported_origin_binding')
            row['unsupported_origin']=origin
        route=True if is_mvp else (source and all(a["result"].get("generator")=="agent" for a in attempts)) if entry["route"]=="source" else (
            not source and all(a["result"].get("generator")=="compiler" for a in attempts))
        row.update(route_ok=route,unsupported_to_source=source)
        passed=report.get("status")=="ok" and result_pass(final) and route and wall<900 and not row["stop_reason"]
        if not is_mvp:
            eligible=bool(attempts and attempts[0]["ended_elapsed_s"]<=450 and not result_pass(first)
                and cad_agent.repair_reason(first) is None and not eval_verify.harness_failure(dict(attempts=[attempts[0]])))
            if report["repair_eligible"]!=eligible and not row["stop_reason"]: raise ValueError("repair_eligibility_binding")
            row["repair_eligible"]=eligible
            row["repair_not_attempted_reason"]=report.get("repair_not_attempted_reason")
            if eligible and not row["repair_calls"] and not row["stop_reason"] and not row["episode_stop_reason"]:
                row["stop_reason"]="harness:repair_not_invoked"
            row["natural_repair_eligible"]=eligible and entry["group"] in ("geometry","q","completion")
        if entry["route"]=="ask" or entry["group"]=="completion":
            score,invention=q_score(row["first_response"],False,entry["case"],rubric)
            row.update(initial_q_score=score,initial_critical_invention=invention,q_score=score,critical_invention=invention)
            if entry["route"]=="ask":
                passed=score==1 and not invention and report.get('logical_calls',len(report['calls']))==1 and not attempts and wall<450
                row["route_ok"]=None
            else:
                if (report.get("answer_sha256")!=sha(answer) or report.get("completion_input_sha256")!=sha(raw+b"\n"+answer)
                        or report.get("initial_q_score")!=score or report.get("initial_critical_invention")!=invention):
                    raise ValueError("completion_report_binding")
                if read_json((where/"first-response.json").read_text(encoding="utf-8"))!=report["first_response"]:
                    raise ValueError("completion_first_artifact_binding")
                reached=report.get("completion_reached") is True
                actual_start=any(c["purpose"]=="interpretation" and c["invoked"] for c in report["calls"])
                if reached!=actual_start or reached and not (score and not invention) or (not reached and (report.get('logical_calls',len(report['calls']))!=1 or attempts)):
                    raise ValueError("completion_answer_gate_binding")
                row.update(completion_reached=reached,completion_not_reached_reason=report.get("completion_not_reached_reason"))
                passed &= reached
        elif entry["case"]=="A4":
            row["q_score"],row["critical_invention"]=q_score(row["first_response"],passed,entry["case"])
            passed &= row["q_score"]==1
        if entry["group"]=="fault":
            row["fault"]=check_fault(root,entry,report,where)
            passed &= all(row["fault"].get(k) is True for k in ("reached","injected","established","detected")) and row["repair_calls"]==1
        if entry["group"]=="dev":
            passed=report.get("status")=="preview" and route and not attempts and wall<450 if entry["route"]!="ask" else passed
            row["preview_kind"]=report.get("preview_kind")
        if is_mvp:
            row["mvp_record"]=eval_mvp.record(root,entry["case"],name,eval_mvp.suite(root)[entry["case"]])
            passed &= row["mvp_record"]["passed"]
        row["passed"]=bool(passed and not row["stop_reason"])
        row["failure_class"]=None if row["passed"] else row["stop_reason"] or (
            "timeout" if row["episode_stop_reason"] else
            "initial_question" if entry["route"]=="ask" or entry["group"]=="completion" and not row["completion_reached"] else
            "fault_not_reached" if entry["group"]=="fault" and not (row["fault"] or {}).get("reached") else final.get('failure_class_v3') or eval_mvp.failure_class(report,final))
        if row["stop_reason"] or row["episode_stop_reason"]: row["completed"]=False
    except FileNotFoundError as exc:
        row.update(passed=False,completed=False,stop_reason="harness:missing_report_or_artifact" if (where/"driver-run.json").is_file() else None,
                   failure_class="missing_report",error=str(exc))
    except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError) as exc:
        row.update(passed=False,completed=False,stop_reason="harness:report_binding",failure_class="protocol",error=str(exc))
    return row


def legacy_record(root,entry,name):
    row=eval_verify.legacy_record(root,entry,name)
    row.update(parse_repairs=0,repair_calls=0,repair_eligible=False,natural_repair_eligible=False,manifest_entry=dict(entry))
    if row["completed"]:
        result=read_json((eval_mvp.run_path(root,name)/"result.json").read_text(encoding="utf-8"))
        row["failure_class"]=None if row["passed"] else row.get("stop_reason") or "legacy_regression"
        row["native_result"]=result
    return row


def run(prefix,snapshot,call_budget=163,codex=None,root=ROOT,runner=None,clock=None,now=None):
    root=Path(root).resolve(); guard=Guard(snapshot,call_budget=call_budget,clock=clock,now=now)
    manifest,order=load(root)
    if manifest["version"].endswith("-aggfix"): raise Stop("aggfix_no_live_run")
    if manifest['version']==SOLFIX_VERSION:raise Stop('solfix_requires_resume')
    directory=paths(root,prefix)
    executable=manifest["cli"]["path"]
    if codex and Path(shutil.which(codex) or codex).resolve()!=Path(executable): raise Stop("cli_path_changed")
    process_runner=runner or subprocess.run
    def bound_runner(argv,**kwargs):
        completed=process_runner(argv,**kwargs)
        if len(argv)>1 and argv[1]=="--version" and (completed.returncode!=0 or cad_agent.clean(completed.stdout.strip())!=manifest["cli"]["version"]):
            raise Stop("cli_version_changed")
        return completed
    names=[run_name(prefix,e) for e in order["entries"]]
    if directory.exists() or any(eval_mvp.run_path(root,n).exists() for n in names): raise ValueError("prefix_exists")
    guard.check_versions=lambda:verify_frozen(root,manifest)
    directory.mkdir(parents=True,exist_ok=False)
    digest=sha((root/DESIGN/"SHA256.json").read_bytes())
    write_json(directory/"plan.json",dict(profile="verify-v3",version=manifest["version"],entries=order["entries"],
        sha_manifest=digest,started_at=cad_agent.utc(),started_monotonic=guard.started,deadline_monotonic=guard.deadline))
    rows=[]; stopped="insufficient_planned_call_budget" if call_budget<order["planned_calls"] else None
    dev_calls=0
    with (directory/"progress.jsonl").open("x",encoding="utf-8",newline="\n") as progress:
        for e,name in zip(order["entries"],names):
            row=empty_row(e,name,stopped); tick=guard.clock()
            if stopped is None:
                try:
                    guard.before_episode(max(e["max_calls"],sum(x["min_calls"] for x in order["entries"][e["sequence"]-1:])))
                    group=e["group"]
                    if group=="legacy":
                        is_a=e["case"].startswith("A-"); good=e["case"].endswith("good")
                        filename="cad_run_"+("a" if is_a else "b")+("_build.py" if good else "_broken_mvp.py")
                        args=cad_run.parser().parse_args(["--script",str(root/"tools/fixtures"/filename),"--out-dir",str(eval_mvp.run_path(root,name)),
                            "--task",cad_run_probes.TASK_A if is_a else cad_run_probes.TASK_B,"--timeout-s",str(math.floor(min(300,guard.remaining())))])
                        cad_run.run_attempt(args,root=root); row=legacy_record(root,e,name)
                    else:
                        gold,raw,rubric,answer=inputs(root,e)
                        if group=="mvp":
                            report,_=cad_agent.run_mvp_driver(name,executable,raw.decode("utf-8"),gold,
                                root=root,runner=bound_runner,clock=guard.clock,evaluation=True,guard=guard,max_calls=e["max_calls"])
                        else:
                            fault=Fault(root/DESIGN/"test"/e["case"]/"fault.json") if group=="fault" else None
                            report,_=agent.run_driver(name,executable,raw.decode("utf-8"),gold,root=root,runner=bound_runner,
                                guard=guard,route=e["route"],max_calls=e["max_calls"],rubric=rubric,
                                answer=answer.decode("utf-8") if answer is not None else None,fault=fault,preview=group=="dev")
                        if group=="dev": dev_calls+=report["llm_calls"]
                        row=record(root,e,name)
                    guard.remaining(reserve=0); verify_frozen(root,manifest)
                    if row.get("stop_reason"): stopped=row["stop_reason"]
                except (OSError,ValueError,KeyError,TypeError) as exc:
                    stopped=str(exc); row.update(passed=False,stop_reason=stopped,failure_class=stopped)
            timed_episode=bool(row.get("episode_stop_reason"))
            row["observed_wall_s"]=guard.clock()-tick if row["completed"] or timed_episode else None
            if row["completed"] or timed_episode: row["wall_s"]=max(row["wall_s"] or 0,row["observed_wall_s"])
            row["ended_elapsed_s"]=guard.clock()-guard.started
            if row["ended_elapsed_s"]>=10800: row["passed"]=False
            rows.append(row); progress.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n"); progress.flush()
            print(json.dumps({"id":e["id"],"completed":row["completed"],"passed":row["passed"],"stop_reason":stopped}),flush=True)
    document=dict(schema="cad-harness.verify-run.v3",profile="verify-v3",prefix=prefix,version=manifest["version"],
        local_commit=manifest["local_commit"],plan_commit=manifest["plan_commit"],created_at=cad_agent.utc(),
        started_monotonic=guard.started,deadline_monotonic=guard.deadline,wall_s=guard.clock()-guard.started,
        stop_reason=stopped,rows=rows,real_calls=guard.calls,dev_calls=dev_calls,quota_snapshots=guard.snapshots,
        frozen_sha256=manifest["files"],sha_manifest=digest,call_budget=call_budget)
    write_json(directory/"suite-run.json",document)
    return document


def transition(root,original,current):
    """The reviewed amendment permits four code files, never CAD/gold/order changes."""
    if (original.get('schema')!='cad-harness.verify-sha.v3' or original.get('profile')!='verify-v3'
            or original.get('version')!='verify-v3-reviewed-r1' or current['version']!=SOLFIX_VERSION
            or any(original[k]!=current[k] for k in ('cli','settings','agents_sha256','plan_commit'))):raise Stop('resume_manifest_identity')
    old,new=original['files'],current['files']
    if set(old)-set(new) or set(new)-set(old)!=SOLFIX_DOCS:raise Stop('resume_manifest_file_set')
    changed={n for n in old if old[n]!=new[n]}
    if not changed<=SOLFIX_CODE or not changed:raise Stop('resume_code_change_allowlist')
    verify_frozen(root,current)
    return sorted(changed)


def original_binding(root,prefix,manifest_path,current,order):
    archive=safe_file(root,Path(manifest_path).as_posix()) if not Path(manifest_path).is_absolute() else Path(manifest_path)
    if archive.resolve()!=archive or not archive.is_relative_to(root/DESIGN) or archive.name!='SHA256.run-r1.json':raise Stop('original_manifest_archive_path')
    old=read_json(archive.read_text(encoding='utf-8'));changed=transition(root,old,current)
    directory=paths(root,prefix);observed=read_json((directory/'suite-run.json').read_text(encoding='utf-8'))
    plan=read_json((directory/'plan.json').read_text(encoding='utf-8'));digest=sha(archive.read_bytes())
    if (observed['schema']!='cad-harness.verify-run.v3' or observed['prefix']!=prefix or observed['version']!=old['version']
            or observed['sha_manifest']!=digest or plan['sha_manifest']!=digest or plan['version']!=old['version']
            or observed['frozen_sha256']!=old['files'] or plan['entries']!=order['entries']
            or observed['started_monotonic']!=plan['started_monotonic'] or observed['deadline_monotonic']!=plan['deadline_monotonic']
            or observed['real_calls']!=54 or observed['call_budget']!=163 or abs(observed['deadline_monotonic']-observed['started_monotonic']-10800)>1e-6
            or [r['id'] for r in observed['rows']]!=[e['id'] for e in order['entries']]):raise Stop('original_suite_binding')
    for e,row in zip(order['entries'],observed['rows']):
        if row['manifest_entry']!=e or row['run']!=run_name(prefix,e) or row['completed']!=(e['sequence']<=46):raise Stop('original_resume_eligibility')
        if e['sequence']>=48 and (row['sol_calls'] is not None or driver_path(root,row['run']).exists()):raise Stop('resume_started_row')
    if observed['rows'][46]['id']!='q-A5-r5' or observed['rows'][46]['sol_calls']!=1:raise Stop('resume_A5_binding')
    return old,observed,plan,archive,changed


def original_artifacts(root,prefix,order,suffix=''):
    directories=[safe_file(root,paths(root,prefix).relative_to(root).as_posix()+suffix),
        *(driver_path(root,run_name(prefix,e)+suffix) for e in order['entries'])]
    return {p.relative_to(root).as_posix():sha(safe_file(root,p.relative_to(root).as_posix()).read_bytes()) for d in directories if d.exists() for p in d.rglob('*') if p.is_file()}


def historical_provider(root,row):
    report=read_json((driver_path(root,row['run'])/'driver-run.json').read_text(encoding='utf-8'))
    c=report['calls'][-1];summary=agent.rollout_summary(c.get('session_id'))
    where=driver_path(root,row['run'])
    if (not summary or not summary['provider_rejected'] or c.get('exit')==0
            or (where/('last-c%d.txt'%c['call'])).exists()):raise Stop('original_provider_evidence_missing:'+row['id'])
    return dict(id=row['id'],run=row['run'],call=c['call'],session_id=c['session_id'],summary=summary,
        driver_sha256=sha((where/'driver-run.json').read_bytes()),original_score_preserved=row['completed'])


def resume(prefix,snapshot,run_manifest,codex=None,root=ROOT,runner=None,clock=None,now=None,sleeper=None):
    root=Path(root).resolve();manifest,order=load(root)
    old,observed,plan,archive,changed=original_binding(root,prefix,run_manifest,manifest,order)
    guard=Guard(snapshot,clock=clock,now=now);guard.inherit(observed,no_deadline=True)
    # UTC/monotonic correspondence authenticates the inherited clock across reboot.
    elapsed=(guard.now()-datetime.fromisoformat(plan['started_at'])).total_seconds()
    if abs(elapsed-(guard.clock()-guard.started))>60:raise Stop('resume_host_clock_changed')
    selected=order['entries'][46:];names=[run_name(prefix,e)+'-resume1' for e in selected]
    directory=safe_file(root,paths(root,prefix).relative_to(root).as_posix()+'-resume1')
    if directory.exists() or any(driver_path(root,n).exists() for n in names):raise Stop('resume_prefix_exists')
    # Locate the two completed source failures by frozen ID rather than guessed indexes.
    annotations=[historical_provider(root,next(r for r in observed['rows'] if r['id']==id_)) for id_ in ('q-A5-r5','geometry-G5-r1','geometry-G1-r2')]
    prior=read_json((driver_path(root,observed['rows'][46]['run'])/'driver-run.json').read_text(encoding='utf-8'))
    ended=observed['rows'][46]['ended_elapsed_s']
    if type(ended) not in (int,float) or not 0<=ended<10800:raise Stop('original_A5_time_binding')
    waited=guard.clock()-guard.started-ended;additional_wait=0
    while waited<agent.PROVIDER_WAIT_S:
        delay=min(60,agent.PROVIDER_WAIT_S-waited,guard.remaining())
        (sleeper or time.sleep)(delay);additional_wait+=delay
        waited=guard.clock()-guard.started-ended
    executable=manifest['cli']['path']
    if codex and Path(shutil.which(codex) or codex).resolve()!=Path(executable):raise Stop('cli_path_changed')
    def bound_runner(argv,**kwargs):
        completed=(runner or agent.bounded_run)(argv,**kwargs)
        if len(argv)>1 and argv[1]=='--version' and (completed.returncode or cad_agent.clean(completed.stdout.strip())!=manifest['cli']['version']):raise Stop('cli_version_changed')
        return completed
    preserved=original_artifacts(root,prefix,order);digest=sha((root/DESIGN/'SHA256.json').read_bytes())
    bindings=dict(original_sha_manifest=sha(archive.read_bytes()),sha_manifest=digest,
        original_suite_sha256=sha((paths(root,prefix)/'suite-run.json').read_bytes()),original_plan_sha256=sha((paths(root,prefix)/'plan.json').read_bytes()),
        original_artifacts=preserved,code_changes=changed,original_provider_attempts=annotations,
        deadline=RESUME_DEADLINE,deadline_ok=True,original_deadline_monotonic=observed['deadline_monotonic'])
    guard.check_versions=lambda:verify_frozen(root,manifest)
    directory.mkdir(parents=True,exist_ok=False)
    write_json(directory/'plan.json',dict(profile='verify-v3',segment=2,prefix=prefix,version=manifest['version'],entries=selected,
        started_monotonic=guard.started,deadline_monotonic=guard.deadline,inherited_calls=54,call_budget=163,**bindings))
    rows=[];stopped=None;segment_start=guard.clock();initial_calls=guard.calls
    with (directory/'progress.jsonl').open('x',encoding='utf-8',newline='\n') as progress:
        for e,name in zip(selected,names):
            row=empty_row(e,name,stopped);tick=guard.clock()
            if stopped is None:
                try:
                    guard.before_episode(max(e['max_calls'],sum(x['min_calls'] for x in selected if x['sequence']>=e['sequence'])))
                    gold,raw,rubric,answer=inputs(root,e);fault=Fault(root/DESIGN/'test'/e['case']/'fault.json') if e['group']=='fault' else None
                    report,_=agent.run_driver(name,executable,raw.decode('utf-8'),gold,root=root,runner=bound_runner,guard=guard,
                        route=e['route'],max_calls=e['max_calls'],rubric=rubric,answer=answer.decode('utf-8') if answer is not None else None,
                        fault=fault,provider_retry=True,sleeper=sleeper,prior_provider_attempts=1 if e['sequence']==47 else 0,
                        prior_call_identity=prior['calls'][0] if e['sequence']==47 else None)
                    if e['sequence']==47 and report['calls']:
                        if any(report['calls'][0][k]!=prior['calls'][0][k] for k in ('kind','purpose','context_sha256','prompt_sha256')):raise Stop('resume_A5_payload_binding')
                    row=record(root,e,name);guard.remaining(reserve=0);verify_frozen(root,manifest)
                    if row.get('stop_reason'):stopped=row['stop_reason']
                except (OSError,ValueError,KeyError,TypeError) as exc:
                    stopped=str(exc);row.update(passed=False,stop_reason=stopped,failure_class=stopped)
            timed=bool(row.get('episode_stop_reason'))
            row['observed_wall_s']=guard.clock()-tick if row['completed'] or timed else None
            if row['completed'] or timed:row['wall_s']=max(row['wall_s'] or 0,row['observed_wall_s'])
            row['ended_elapsed_s']=guard.clock()-guard.started;row['original_run']=run_name(prefix,e);row['segment']=2
            rows.append(row);progress.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');progress.flush()
            print(json.dumps(dict(id=e['id'],completed=row['completed'],passed=row['passed'],stop_reason=stopped)),flush=True)
    if original_artifacts(root,prefix,order)!=preserved:raise Stop('original_artifacts_changed')
    document=dict(schema='cad-harness.verify-resume.v3',profile='verify-v3',segment=2,prefix=prefix,version=manifest['version'],
        local_commit=manifest['local_commit'],plan_commit=manifest['plan_commit'],created_at=cad_agent.utc(),
        started_monotonic=guard.started,deadline_monotonic=guard.deadline,segment_started_monotonic=segment_start,
        segment_wall_s=guard.clock()-segment_start,wall_s=guard.clock()-guard.started,stop_reason=stopped,rows=rows,
        inherited_calls=54,real_calls=guard.calls-initial_calls,total_real_calls=guard.calls,call_budget=163,quota_snapshots=guard.snapshots,
        frozen_sha256=manifest['files'],prior_backoff_elapsed_s=waited,additional_provider_wait_s=additional_wait,**bindings)
    write_json(directory/'suite-run.json',document)
    return document


def rerun2_ids(ids):
    requested=ids.split(',') if isinstance(ids,str) else list(ids)
    if len(requested)!=2 or set(requested)!=RERUN2_IDS:raise Stop('rerun2_id_allowlist')
    return RERUN2_IDS


def rerun2_source(root,prefix,run_manifest,manifest,order):
    """Bind the existing aggregate; do not reconstruct or re-score its other rows."""
    _,first,_,archive,_=original_binding(root,prefix,run_manifest,manifest,order)
    matches=[]
    for candidate in (root/'reports').glob('aggregate-verify-v3-*-solfix.json'):
        candidate=safe_file(root,candidate.relative_to(root).as_posix())
        document=read_json(candidate.read_text(encoding='utf-8'))
        if document.get('prefix')==prefix:matches.append((candidate,document))
    if len(matches)!=1:raise Stop('rerun2_base_aggregate_required')
    path,base=matches[0];rows=[r for group in GROUPS for r in base['groups'][group]]
    original_sha=sha(archive.read_bytes())
    if (base.get('schema')!='cad-harness.verify-aggregate.v3' or base.get('profile')!='verify-v3'
            or base.get('version')!=manifest['version'] or base.get('plan_commit')!=manifest['plan_commit']
            or base.get('real_calls')!=84 or not all(base['summary'].get(k) is True for k in ('valid_suite','complete','versions_consistent'))
            or base['summary'].get('stop_reason') is not None or len(rows)!=60
            or [r['id'] for r in rows]!=[e['id'] for e in order['entries']]
            or any(r['manifest_entry']!=e for r,e in zip(rows,order['entries']))
            or len(base['segments'])!=2 or base['segments'][0]['sha_manifest']!=original_sha
            or base['segments'][0]['suite_sha256']!=sha((paths(root,prefix)/'suite-run.json').read_bytes())):
        raise Stop('rerun2_base_binding')
    old_files=base['frozen_sha256'];new_files=manifest['files']
    if (set(old_files)!=set(new_files) or {p for p in old_files if old_files[p]!=new_files[p]}
            - {'tools/eval_verify_v3.py','tools/test_verify_v3.py'}):raise Stop('rerun2_code_change_allowlist')
    resumed=safe_file(root,paths(root,prefix).relative_to(root).as_posix()+'-resume1')
    second=read_json((resumed/'suite-run.json').read_text(encoding='utf-8'))
    if (base['segments'][1]['suite_sha256']!=sha((resumed/'suite-run.json').read_bytes())
            or base['sha_manifest']!=second['sha_manifest'] or old_files!=second['frozen_sha256']):raise Stop('rerun2_resume_binding')
    annotations={a['id']:a for a in base['historical_provider_attempts'] if a.get('original_score_preserved') is True
        and a.get('summary',{}).get('provider_rejected') is True}
    if set(annotations)!=RERUN2_IDS:raise Stop('rerun2_provider_allowlist')
    for row in rows:
        if row['id'] not in RERUN2_IDS:continue
        if (not row['completed'] or row['passed'] or row['failure_class']!='interpretation' or row.get('segment')!=1
                or row['run']!=run_name(prefix,row['manifest_entry'])
                or historical_provider(root,row)!=annotations[row['id']]):raise Stop('rerun2_original_failure_binding')
    preserved={**original_artifacts(root,prefix,order),**original_artifacts(root,prefix,order,'-resume1')}
    for p in (path,path.with_suffix('.csv')):
        preserved[p.relative_to(root).as_posix()]=sha(safe_file(root,p.relative_to(root).as_posix()).read_bytes())
    return first,base,dict(original_sha_manifest=original_sha,
        base_aggregate=dict(path=path.relative_to(root).as_posix(),sha256=sha(path.read_bytes())),original_artifacts=preserved)


def verify_rerun2_artifacts(root,preserved):
    if any(sha(safe_file(root,p).read_bytes())!=digest for p,digest in preserved.items()):raise Stop('rerun2_original_artifacts_changed')


def rerun2_driver(name,*args,root=ROOT,**kwargs):
    """Adapt the new directory suffix without changing the driver's accepted names.

    Execute under a fresh supported name, then relocate only this new directory
    and its report path metadata. All captured payloads/CAD artifacts stay intact.
    """
    execution=name+'-mvp1';source=driver_path(root,execution);target=driver_path(root,name)
    if any(p.exists() or p.is_symlink() for p in (source,target)):raise Stop('rerun2_prefix_exists')
    report,code=agent.run_driver(execution,*args,root=root,**kwargs)
    old=source.relative_to(root).as_posix();new=target.relative_to(root).as_posix()
    def relocate(value):
        if not value.startswith(old+'/'):raise Stop('rerun2_driver_path_binding')
        return new+value[len(old):]
    report.update(execution_run=execution,run_id=name)
    for c in report['calls']:
        artifacts=[*c.get('context_artifacts',{}).values(),*c.get('transport_artifacts',{}).values()]
        if c.get('provider_artifact'):artifacts.append(c['provider_artifact'])
        for item in artifacts:item['path']=relocate(item['path'])
    for attempt in report.get('attempts',[]):attempt['out_dir']=relocate(attempt['out_dir'])
    if report.get('final_out_dir'):report['final_out_dir']=relocate(report['final_out_dir'])
    source.rename(target)
    (target/'driver-run.json').write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    return report,code


def rerun2_record(root,entry,name,manifest):
    row=record(root,entry,name)
    report=read_json((driver_path(root,name)/'driver-run.json').read_text(encoding='utf-8'))
    identity=row.get('driver_identity') or {}
    if (report.get('provider_policy')!=agent.PROVIDER_POLICY or report.get('prior_provider_attempts')!=0
            or report.get('execution_run')!=name+'-mvp1' or identity.get('cli_version')!=manifest['cli']['version']
            or identity.get('agents_sha256')!=manifest['agents_sha256']
            or any((identity.get('settings') or {}).get(k)!=v for k,v in manifest['settings'].items())):
        raise Stop('rerun2_driver_identity')
    for key,path in (('skill_sha256','skills/freecad-modeling/SKILL.md'),('schema_sha256','design/cad-harness-mvp/build-schema.json'),
            ('compiler_sha256','tools/cad_spec.py'),('probe_sha256','tools/cad_verify_v3_probe.py'),('shared_probe_sha256','tools/cad_verify_probe.py')):
        if identity.get(key)!=manifest['files'][path]:raise Stop('rerun2_driver_identity')
    return row


def rerun(prefix,ids,snapshot,run_manifest,codex=None,root=ROOT,runner=None,clock=None,now=None,sleeper=None):
    requested=rerun2_ids(ids);root=Path(root).resolve()
    directory=safe_file(root,paths(root,prefix).relative_to(root).as_posix()+'-rerun2')
    targets=[directory,*(driver_path(root,run_name(prefix,dict(id=id_))+suffix) for id_ in requested for suffix in ('-rerun2','-rerun2-mvp1'))]
    if any(p.exists() or p.is_symlink() for p in targets):raise Stop('rerun2_prefix_exists')
    manifest,order=load(root);first,base,bindings=rerun2_source(root,prefix,run_manifest,manifest,order)
    selected=[e for e in order['entries'] if e['id'] in requested]
    if len(selected)!=2:raise Stop('rerun2_id_allowlist')
    guard=Guard(snapshot,clock=clock,now=now);guard.inherit({**first,'real_calls':RERUN2_SPENT},no_deadline=True)
    guard.check_versions=lambda:verify_frozen(root,manifest)
    guard.before_episode(sum(e['max_calls'] for e in selected))
    executable=manifest['cli']['path']
    if codex and Path(shutil.which(codex) or codex).resolve()!=Path(executable):raise Stop('cli_path_changed')
    def bound_runner(argv,**kwargs):
        completed=(runner or agent.bounded_run)(argv,**kwargs)
        if len(argv)>1 and argv[1]=='--version' and (completed.returncode or cad_agent.clean(completed.stdout.strip())!=manifest['cli']['version']):raise Stop('cli_version_changed')
        return completed
    bindings.update(sha_manifest=sha((root/DESIGN/'SHA256.json').read_bytes()),inherited_calls=RERUN2_SPENT,call_budget=163,
        deadline_monotonic=None,deadline=RESUME_DEADLINE)
    directory.mkdir(parents=True,exist_ok=False)
    write_json(directory/'plan.json',dict(profile='verify-v3',prefix=prefix,version=manifest['version'],entries=selected,**bindings))
    rows=[];stopped=None;started=guard.clock()
    with (directory/'progress.jsonl').open('x',encoding='utf-8',newline='\n') as progress:
        for index,e in enumerate(selected):
            name=run_name(prefix,e)+'-rerun2';row=empty_row(e,name,stopped);tick=guard.clock()
            if stopped is None:
                try:
                    guard.before_episode(sum(x['max_calls'] for x in selected[index:]))
                    gold,raw,rubric,answer=inputs(root,e)
                    rerun2_driver(name,executable,raw.decode('utf-8'),gold,root=root,runner=bound_runner,guard=guard,
                        route=e['route'],max_calls=e['max_calls'],rubric=rubric,answer=answer,provider_retry=True,sleeper=sleeper)
                    row=rerun2_record(root,e,name,manifest);verify_frozen(root,manifest)
                    if row.get('stop_reason'):stopped=row['stop_reason']
                except (OSError,ValueError,KeyError,TypeError) as exc:
                    stopped=str(exc);row.update(passed=False,stop_reason=stopped,failure_class=stopped)
            if row['completed'] or row.get('episode_stop_reason'):row['wall_s']=max(row['wall_s'] or 0,guard.clock()-tick)
            row.update(original_run=run_name(prefix,e),segment='rerun2',ended_elapsed_s=guard.clock()-guard.started)
            rows.append(row);progress.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');progress.flush()
            print(json.dumps(dict(id=e['id'],completed=row['completed'],passed=row['passed'],stop_reason=stopped)),flush=True)
    verify_rerun2_artifacts(root,bindings['original_artifacts'])
    document=dict(schema='cad-harness.verify-rerun.v3',profile='verify-v3',prefix=prefix,version=manifest['version'],
        created_at=cad_agent.utc(),local_commit=manifest['local_commit'],plan_commit=manifest['plan_commit'],
        frozen_sha256=manifest['files'],rows=rows,real_calls=guard.calls-RERUN2_SPENT,total_real_calls=guard.calls,
        quota_snapshots=guard.snapshots,wall_s=guard.clock()-started,stop_reason=stopped,**bindings)
    write_json(directory/'suite-run.json',document)
    return document


def token_totals(rows):
    return {k:sum(r["tokens"][k] for r in rows) if rows and all(r["tokens"][k] is not None for r in rows) else None
            for k in cad_agent.USAGE_KEYS}


def metric(rows,success="passed"):
    m=eval_verify.metric(rows,success)
    walls=sorted(r["wall_s"] for r in rows if r.get("wall_s") is not None)
    m.update(wall_s=dict(median=statistics.median(walls) if walls else None,
        p95=walls[max(0,math.ceil(.95*len(walls))-1)] if walls else None,maximum=max(walls) if walls else None),
        sol_calls=sum(r["sol_calls"] or 0 for r in rows),cad_attempts=sum(r["cad_attempts"] or 0 for r in rows),
        parse_repairs=sum(r.get("parse_repairs",0) for r in rows),repair_calls=sum(r.get("repair_calls",0) for r in rows),
        provider_tokens=token_totals(rows),failure_classes=dict(Counter(r["failure_class"] for r in rows if not r["passed"])))
    return m


def conditional(rows,key="passed"):
    success=sum(bool(r.get(key)) for r in rows)
    return dict(successes=success,denominator=len(rows),rate=success/len(rows) if rows else None,
                wilson95=wilson(success,len(rows),all(r["completed"] for r in rows)))


def summarize(rows,order,stopped=None,versions_consistent=True,deadline_ok=True):
    core=[r for r in rows if r["scored"]]; dev=[r for r in rows if r["group"]=="dev"]
    parts={c:metric([r for r in core if r["case"]==c]) for c in dict.fromkeys(r["case"] for r in core)}
    passed=lambda c:parts.get(c,{}).get("successes",0)
    fault=[r for r in core if r["group"]=="fault"]
    fmetrics={k:{**conditional([{**r,"value":bool((r.get("fault") or {}).get(k))} for r in fault],"value"),
                 "planned":len(fault),"completed":sum(r["completed"] for r in fault)} for k in ("reached","established","detected")}
    fmetrics["final_all_gate_pass"]=metric(fault)
    fmetrics["pass_per_established"]=conditional([r for r in fault if (r.get("fault") or {}).get("established")])
    if not all(r["completed"] for r in fault): fmetrics["pass_per_established"]["wilson95"]=None
    kinds={"source" if r["case"] in ("F4","F5") else "spec" for r in fault if r["passed"] and r.get("repair_calls")==1}
    fbar=len(fault)==6 and all(fmetrics[k]["successes"]==6 for k in ("established","detected")) and sum(r["passed"] for r in fault)>=4 and all(passed(c)>=1 for c in ("F4","F5","F6")) and kinds=={"source","spec"}
    mvp=[r for r in core if r["group"]=="mvp"]; legacy=[r for r in core if r["group"]=="legacy"]
    mbar=len(mvp)==10 and sum(r["passed"] for r in mvp)>=8 and all(passed(c)>=1 for c in eval_mvp.ORDER)
    lbar=len(legacy)==4 and all(r["passed"] for r in legacy)
    thresholds=dict(source=sum(passed(c) for c in ("G1","G2","G3","G4","G5"))>=8 and all(passed(c)>=1 for c in ("G1","G2","G3","G4","G5")),
        complex=passed("G6")>=2,stock=passed("S3")>=4,defaults=passed("A4")>=2,
        ambiguity=passed("A5")>=4 and passed("A6")>=4 and sum(r["critical_invention"] for r in core if r["case"] in ("A5","A6"))==0,
        faults=fbar,mvp=mbar,legacy=lbar)
    completion={}
    for c in ("C4","C5"):
        rs=[r for r in rows if r["group"]=="completion" and r["case"]==c]
        correct=[r for r in rs if r["initial_q_score"]==1 and not r["initial_critical_invention"]]
        cm=conditional(correct)
        if not all(r["completed"] for r in rs): cm["wilson95"]=None
        completion[c]=dict(completion=metric(rs),initial_correct_question=metric(rs,"initial_q_score"),
            post_answer_first_attempt=metric(rs,'post_answer_first_attempt_pass'),
            conditional_completion=cm,not_reached=sum(not r["completion_reached"] for r in rs))
    valid=[r["id"] for r in rows]==[e["id"] for e in order["entries"]] and len({r["run"] for r in rows})==60
    natural=[r for r in core if r.get("natural_repair_eligible")]
    nmetric=conditional(natural)
    if not all(r["completed"] for r in core): nmetric["wilson95"]=None
    crepair=conditional([r for r in rows if r["group"]=="completion" and r.get("natural_repair_eligible")])
    if not all(r["completed"] for r in rows if r["group"]=="completion"): crepair["wilson95"]=None
    fallback_origins=dict(Counter(r.get('unsupported_origin') for r in core if r.get('unsupported_to_source')))
    return dict(valid_suite=valid,complete=all(r["completed"] for r in rows),core_complete=len(core)==51 and all(r["completed"] for r in core),
        fallback_origins=fallback_origins,
        versions_consistent=versions_consistent,deadline_ok=deadline_ok,stop_reason=stopped,thresholds=thresholds,
        bar_met=bool(valid and len(core)==51 and all(r["completed"] for r in core) and versions_consistent and deadline_ok and not stopped and all(thresholds.values())),
        per_part=parts,completion=completion,dev=dict(metric=metric(dev),scored=False),fault=fmetrics,
        natural_repair={**nmetric,"eligible":len(natural),"invoked":sum(r["repair_calls"]>0 for r in natural)},
        completion_repair=crepair,
        parse_repair_calls=sum(r.get("parse_repairs",0) for r in rows),repair_calls=sum(r.get("repair_calls",0) for r in rows))


def aggregate_resumed(prefix,suffix,run_manifest,root=ROOT,clock=None):
    """Read-only reconstruction; each observation keeps its own frozen identity."""
    root=Path(root).resolve();manifest,order=load(root);eval_mvp.valid_name(suffix)
    if not suffix.endswith('-solfix'):raise Stop('resume_aggregate_new_suffix_required')
    outputs=[root/'reports'/('aggregate-verify-v3-'+suffix+ext) for ext in ('.json','.csv')]
    if any(p.exists() or p.is_symlink() or p.resolve()!=p for p in outputs):raise Stop('aggregate_exists_or_linked')
    old,first,first_plan,archive,changed=original_binding(root,prefix,run_manifest,manifest,order)
    directory=safe_file(root,paths(root,prefix).relative_to(root).as_posix()+'-resume1')
    second=read_json((directory/'suite-run.json').read_text(encoding='utf-8'));plan=read_json((directory/'plan.json').read_text(encoding='utf-8'))
    digest=sha((root/DESIGN/'SHA256.json').read_bytes());selected=order['entries'][46:]
    expected=dict(original_sha_manifest=sha(archive.read_bytes()),sha_manifest=digest,
        original_suite_sha256=sha((paths(root,prefix)/'suite-run.json').read_bytes()),
        original_plan_sha256=sha((paths(root,prefix)/'plan.json').read_bytes()),code_changes=changed,
        started_monotonic=first['started_monotonic'],deadline_monotonic=None,inherited_calls=54,call_budget=163,
        deadline=RESUME_DEADLINE,deadline_ok=True,original_deadline_monotonic=first['deadline_monotonic'])
    if (second.get('schema')!='cad-harness.verify-resume.v3' or second.get('profile')!='verify-v3' or second.get('segment')!=2
            or second.get('prefix')!=prefix or second.get('version')!=manifest['version'] or plan.get('version')!=manifest['version']
            or plan.get('entries')!=selected or second.get('frozen_sha256')!=manifest['files']
            or any(second.get(k)!=v or plan.get(k)!=v for k,v in expected.items())
            or second['original_artifacts']!=plan['original_artifacts'] or original_artifacts(root,prefix,order)!=second['original_artifacts']
            or [r['id'] for r in second['rows']]!=[e['id'] for e in selected]):raise Stop('resume_segment_binding')
    if second['original_provider_attempts']!=plan['original_provider_attempts']:raise Stop('historical_provider_binding')
    for annotation in second['original_provider_attempts']:
        source=next(r for r in first['rows'] if r['id']==annotation['id'])
        if annotation!=historical_provider(root,source):raise Stop('historical_provider_evidence_changed')
    if {a['id'] for a in second['original_provider_attempts']}!={'q-A5-r5','geometry-G5-r1','geometry-G1-r2'}:raise Stop('historical_provider_set')
    consistent=True;rows=[];resumed_calls=0;providers=[]
    for e in order['entries']:
        is_second=e['sequence']>=47
        saved=second['rows'][e['sequence']-47] if is_second else first['rows'][e['sequence']-1]
        identity_manifest=manifest if is_second else old
        name=run_name(prefix,e)+('-resume1' if is_second else '')
        if saved['run']!=name or saved['manifest_entry']!=e:raise Stop('resume_run_order_binding')
        if is_second and (saved.get('original_run')!=run_name(prefix,e) or saved.get('segment')!=2):raise Stop('resume_row_origin_binding')
        has_driver=(driver_path(root,name)/'driver-run.json').is_file()
        row=(legacy_record(root,e,name) if e['group']=='legacy' else record(root,e,name)) if saved['completed'] or has_driver else empty_row(e,name,saved.get('stop_reason'))
        row['wall_s']=max(row.get('wall_s') or 0,saved.get('wall_s') or 0) if row['completed'] or row.get('episode_stop_reason') else None
        row['ended_elapsed_s']=saved.get('ended_elapsed_s');row['segment']=2 if is_second else 1
        if saved['passed']!=row['passed'] or saved['completed']!=row['completed']:consistent=False
        ended=row['ended_elapsed_s']
        if row['completed'] and (type(ended) not in (int,float) or not math.isfinite(ended) or ended<0
                or not is_second and ended>=10800):consistent=False;row['passed']=False
        if is_second:resumed_calls+=row['sol_calls'] or 0
        identity=row.get('driver_identity')
        if identity:
            consistent &= identity.get('cli_version')==identity_manifest['cli']['version'] and identity.get('agents_sha256')==identity_manifest['agents_sha256']
            for key,path in (('skill_sha256','skills/freecad-modeling/SKILL.md'),('schema_sha256','design/cad-harness-mvp/build-schema.json'),
                    ('compiler_sha256','tools/cad_spec.py'),('probe_sha256','tools/cad_spec_probe.py' if e['group']=='mvp' else 'tools/cad_verify_v3_probe.py')):
                consistent &= identity.get(key)==identity_manifest['files'][path]
            if e['group']!='mvp':consistent &= identity.get('shared_probe_sha256')==identity_manifest['files']['tools/cad_verify_probe.py']
            consistent &= all((identity.get('settings') or {}).get(k)==v for k,v in identity_manifest['settings'].items())
        if is_second and has_driver:
            report=read_json((driver_path(root,name)/'driver-run.json').read_text(encoding='utf-8'))
            if report.get('provider_policy')!=agent.PROVIDER_POLICY:raise Stop('resume_provider_policy_binding')
            if e['sequence']==47 and report.get('prior_provider_attempts')!=1:raise Stop('resume_A5_attempt_binding')
            if e['sequence']==47 and report['calls']:
                prior=read_json((driver_path(root,first['rows'][46]['run'])/'driver-run.json').read_text(encoding='utf-8'))['calls'][0]
                if any(report['calls'][0][k]!=prior[k] for k in ('kind','purpose','context_sha256','prompt_sha256')):raise Stop('resume_A5_payload_binding')
            if e['sequence']!=47 and report.get('prior_provider_attempts')!=0:raise Stop('resume_unstarted_attempt_binding')
            providers.extend(dict(id=e['id'],run=name,**c) for c in report['calls'] if c['provider_rejected'])
        rows.append(row)
    if sum(r['sol_calls'] or 0 for r in first['rows'])!=54:raise Stop('original_spent_call_binding')
    real_calls=54+resumed_calls
    consistent &= resumed_calls==second['real_calls'] and real_calls==second['total_real_calls'] and real_calls<=163
    now=(clock or time.monotonic)()
    end=second['segment_started_monotonic']+second['segment_wall_s']
    consistent &= (second['segment_started_monotonic']>=first['started_monotonic']+first['wall_s']
        and abs((end-first['started_monotonic'])-second['wall_s'])<=1e-6 and second['segment_wall_s']>=0 and end<=now)
    # Segment 1's saved time evidence is fixed; segment 2 has no suite deadline.
    first_deadline_ok=first.get('deadline_ok',first['wall_s']<first['deadline_monotonic']-first['started_monotonic'])
    deadline_ok=first_deadline_ok
    stopped=second.get('stop_reason') or next((r.get('stop_reason') for r in rows if r.get('stop_reason')),None)
    summary=summarize(rows,order,stopped,consistent,deadline_ok);groups={g:[r for r in rows if r['group']==g] for g in GROUPS}
    document=dict(schema='cad-harness.verify-aggregate.v3',profile='verify-v3',prefix=prefix,version=manifest['version'],
        local_commit=manifest['local_commit'],plan_commit=manifest['plan_commit'],created_at=cad_agent.utc(),sha_manifest=digest,
        frozen_sha256=manifest['files'],summary=summary,groups=groups,per_suite={g:metric(rs) for g,rs in groups.items()},
        provider_tokens={g:token_totals(rs) for g,rs in groups.items()},real_calls=real_calls,inherited_calls=54,resumed_calls=resumed_calls,
        provider_policy=agent.PROVIDER_POLICY,provider_rejected_attempts=providers,provider_wait_s=sum(c.get('backoff_s',0) for c in providers),
        provider_rejected_attempt_count=len(providers),transport_attempts=real_calls+len(providers),
        historical_provider_attempts=second['original_provider_attempts'],original_partial=first['rows'][46],
        segments=[dict(segment=1,version=old['version'],sha_manifest=expected['original_sha_manifest'],suite_sha256=expected['original_suite_sha256'],
            original_stop_reason=first['stop_reason'],wall_s=first['wall_s'],real_calls=54,completed_preserved=46,
            deadline_monotonic=first['deadline_monotonic'],deadline_ok=first_deadline_ok),
            dict(segment=2,version=manifest['version'],sha_manifest=digest,suite_sha256=sha((directory/'suite-run.json').read_bytes()),
                wall_s=second['segment_wall_s'],real_calls=resumed_calls,stop_reason=second['stop_reason'],
                deadline=RESUME_DEADLINE,deadline_monotonic=None,deadline_ok=True)],
        started_monotonic=first['started_monotonic'],deadline_monotonic=None,deadline=RESUME_DEADLINE,
        original_deadline_monotonic=first['deadline_monotonic'],
        interval_scope='Signed segmented recovery: original 46 scores preserved; A5-r5 scored only from segment 2. Each segment binds its own manifest. New provider rejections are unscored and uncharged; historical spent54 is inherited conservatively. C/dev remain outside bar_met.')
    return write_segmented_aggregate(outputs,document,rows)


def write_segmented_aggregate(outputs,document,rows):
    write_json(outputs[0],document)
    fields=('group','case','bar_class','id','run','segment','scored','completed','passed','wall_s','sol_calls','cad_attempts','parse_repairs','repair_calls',
        'failure_class','episode_stop_reason','stop_reason',*cad_agent.USAGE_KEYS)
    with outputs[1].open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in rows:writer.writerow({k:row['tokens'].get(k) if k in cad_agent.USAGE_KEYS else row.get(k) for k in fields})
    return document


def aggregate_rerun2(prefix,suffix,root=ROOT,clock=None,run_manifest=None):
    root=Path(root).resolve();eval_mvp.valid_name(suffix)
    if not suffix.endswith('-rerun2'):raise Stop('rerun2_aggregate_new_suffix_required')
    outputs=[root/'reports'/('aggregate-verify-v3-'+suffix+ext) for ext in ('.json','.csv')]
    if any(p.exists() or p.is_symlink() or p.resolve()!=p for p in outputs):raise Stop('aggregate_exists_or_linked')
    manifest,order=load(root)
    _,base,bindings=rerun2_source(root,prefix,run_manifest or root/DESIGN/'SHA256.run-r1.json',manifest,order)
    directory=safe_file(root,paths(root,prefix).relative_to(root).as_posix()+'-rerun2')
    saved=read_json((directory/'suite-run.json').read_text(encoding='utf-8'))
    plan=read_json((directory/'plan.json').read_text(encoding='utf-8'))
    selected=[e for e in order['entries'] if e['id'] in RERUN2_IDS]
    digest=sha((root/DESIGN/'SHA256.json').read_bytes())
    expected={**bindings,'sha_manifest':digest,'inherited_calls':RERUN2_SPENT,'call_budget':163,
        'deadline_monotonic':None,'deadline':RESUME_DEADLINE}
    if (saved.get('schema')!='cad-harness.verify-rerun.v3' or saved.get('profile')!='verify-v3'
            or saved.get('prefix')!=prefix or plan.get('prefix')!=prefix
            or saved.get('version')!=manifest['version'] or plan.get('version')!=manifest['version']
            or saved.get('frozen_sha256')!=manifest['files'] or plan.get('entries')!=selected
            or [r['id'] for r in saved['rows']]!=[e['id'] for e in selected]
            or any(saved.get(k)!=v or plan.get(k)!=v for k,v in expected.items())):raise Stop('rerun2_suite_binding')
    replacements={};providers=list(base.get('provider_rejected_attempts',[]));attempts=0;consistent=base['summary']['versions_consistent']
    for e,original in zip(selected,saved['rows']):
        name=run_name(prefix,e)+'-rerun2'
        if (original['run']!=name or original['manifest_entry']!=e or original.get('original_run')!=run_name(prefix,e)
                or original.get('segment')!='rerun2'):raise Stop('rerun2_row_binding')
        has_driver=(driver_path(root,name)/'driver-run.json').is_file()
        row=rerun2_record(root,e,name,manifest) if has_driver else empty_row(e,name,original.get('stop_reason'))
        if row['passed']!=original['passed'] or row['completed']!=original['completed']:consistent=False
        if row['completed'] or row.get('episode_stop_reason'):row['wall_s']=max(row['wall_s'] or 0,original.get('wall_s') or 0)
        row.update(original_run=run_name(prefix,e),segment='rerun2',ended_elapsed_s=original.get('ended_elapsed_s'))
        replacements[e['id']]=row
        if has_driver:
            report=read_json((driver_path(root,name)/'driver-run.json').read_text(encoding='utf-8'))
            attempts+=len(report['calls'])
            providers.extend(dict(id=e['id'],run=name,**c) for c in report['calls'] if c['provider_rejected'])
    calls=sum(r['sol_calls'] or 0 for r in replacements.values())
    if (type(saved['real_calls']) is not int or not 0<=saved['real_calls']<=sum(e['max_calls'] for e in selected)
            or saved['total_real_calls']!=RERUN2_SPENT+saved['real_calls'] or saved['total_real_calls']>163):raise Stop('rerun2_call_budget_binding')
    consistent &= calls==saved['real_calls']
    rows=[];substituted=[]
    for group in GROUPS:
        for original in base['groups'][group]:
            row=replacements.get(original['id'],original);rows.append(row)
            if original['id'] in replacements:substituted.append(dict(id=original['id'],original=original,replacement=row))
    stopped=saved.get('stop_reason') or next((r.get('stop_reason') for r in rows if r.get('stop_reason')),None)
    groups={g:[r for r in rows if r['group']==g] for g in GROUPS}
    document={**base,'created_at':cad_agent.utc(),'local_commit':manifest['local_commit'],'sha_manifest':digest,
        'frozen_sha256':manifest['files'],'base_aggregate':bindings['base_aggregate'],'substituted_rows':substituted,
        'groups':groups,'summary':summarize(rows,order,stopped,consistent,base['summary']['deadline_ok']),
        'per_suite':{g:metric(rs) for g,rs in groups.items()},'provider_tokens':{g:token_totals(rs) for g,rs in groups.items()},
        'real_calls':base['real_calls']+saved['real_calls'],'rerun2_calls':saved['real_calls'],
        'total_charged_calls':saved['total_real_calls'],'archived_charged_calls':RERUN2_SPENT-base['real_calls'],
        'provider_rejected_attempts':providers,'provider_rejected_attempt_count':len(providers),
        'provider_wait_s':sum(c.get('backoff_s',0) for c in providers),'transport_attempts':base['transport_attempts']+attempts,
        'segments':[*base['segments'],dict(segment='rerun2',version=manifest['version'],sha_manifest=digest,
            suite_sha256=sha((directory/'suite-run.json').read_bytes()),wall_s=saved['wall_s'],real_calls=saved['real_calls'],
            stop_reason=saved['stop_reason'],deadline=RESUME_DEADLINE,deadline_monotonic=None)],
        'interval_scope':'User decision 2026-10-14 08:58 JST: substitute only geometry-G5-r1 and geometry-G1-r2. Original rows remain in substituted_rows; the other 58 rows are copied unchanged from the bound two-segment aggregate. C/dev remain outside bar_met.'}
    verify_rerun2_artifacts(root,bindings['original_artifacts'])
    return write_segmented_aggregate(outputs,document,rows)


def aggregate(prefix,suffix,root=ROOT,clock=None,run_manifest=None,rerun2=False):
    if rerun2:return aggregate_rerun2(prefix,suffix,root,clock,run_manifest)
    if run_manifest is not None:return aggregate_resumed(prefix,suffix,run_manifest,root,clock)
    root=Path(root).resolve(); manifest,order=load(root); directory=paths(root,prefix); eval_mvp.valid_name(suffix)
    outputs=[root/"reports"/("aggregate-verify-v3-"+suffix+ext) for ext in (".json",".csv")]
    if any(p.exists() or p.is_symlink() or p.resolve()!=p for p in outputs): raise ValueError("aggregate_exists_or_linked")
    observed=read_json((directory/"suite-run.json").read_text(encoding="utf-8"))
    plan=read_json((directory/"plan.json").read_text(encoding="utf-8"))
    digest=sha((root/DESIGN/"SHA256.json").read_bytes())
    if (observed["schema"]!="cad-harness.verify-run.v3" or observed["profile"]!="verify-v3" or observed["prefix"]!=prefix
            or observed["version"]!=manifest["version"] or observed["sha_manifest"]!=digest or plan["sha_manifest"]!=digest
            or plan['version']!=manifest['version']
            or plan["entries"]!=order["entries"] or [r["id"] for r in observed["rows"]]!=[e["id"] for e in order["entries"]]
            or observed["started_monotonic"]!=plan["started_monotonic"] or observed["deadline_monotonic"]!=plan["deadline_monotonic"]
            or abs((observed["deadline_monotonic"]-observed["started_monotonic"])-10800)>1e-6): raise ValueError("suite_record_binding")
    consistent=observed["frozen_sha256"]==manifest["files"]
    rows=[]
    for e,original in zip(order["entries"],observed["rows"]):
        name=run_name(prefix,e)
        if original["run"]!=name or original["manifest_entry"]!=e: raise ValueError("run_order_binding")
        # A stopped episode can contain real calls even when it is not a completed observation.
        row=(legacy_record(root,e,name) if e["group"]=="legacy" else record(root,e,name)) if original["completed"] or (eval_mvp.run_path(root,name)/"driver-run.json").is_file() else empty_row(e,name,original.get("stop_reason"))
        row["wall_s"]=max(row.get("wall_s") or 0,original.get("wall_s") or 0) if row["completed"] or row.get("episode_stop_reason") else None
        row["ended_elapsed_s"]=original.get("ended_elapsed_s")
        if row["completed"] and original.get("ended_elapsed_s",10801)>=10800: row["passed"]=False
        if original["passed"]!=row["passed"] or original["completed"]!=row["completed"]: consistent=False
        rows.append(row)
    identities=[r["driver_identity"] for r in rows if r.get("driver_identity")]
    versions={i.get("cli_version") for i in identities}
    consistent &= versions=={manifest["cli"]["version"]}
    for row in rows:
        identity=row.get("driver_identity")
        if not identity: continue
        is_mvp=row["group"]=="mvp"
        for key,path in (("skill_sha256","skills/freecad-modeling/SKILL.md"),("schema_sha256","design/cad-harness-mvp/build-schema.json"),
                         ("compiler_sha256","tools/cad_spec.py"),("probe_sha256","tools/cad_spec_probe.py" if is_mvp else "tools/cad_verify_v3_probe.py")):
            consistent &= identity.get(key)==manifest["files"][path]
        if not is_mvp: consistent &= identity.get("shared_probe_sha256")==manifest["files"]["tools/cad_verify_probe.py"]
        consistent &= identity.get("agents_sha256")==manifest["agents_sha256"]
        settings=identity.get("settings") or {}
        consistent &= all(settings.get(k)==v for k,v in manifest["settings"].items())
    real_calls=sum(r["sol_calls"] or 0 for r in rows)
    consistent &= real_calls==observed["real_calls"] and real_calls<=observed["call_budget"]<=163
    if sum(r["sol_calls"] or 0 for r in rows if r["group"]=="dev")!=observed["dev_calls"]: consistent=False
    deadline_ok=(clock or time.monotonic)()<observed["deadline_monotonic"] and observed["wall_s"]<10800
    stopped=observed.get("stop_reason") or next((r["stop_reason"] for r in rows if r.get("stop_reason")),None)
    summary=summarize(rows,order,stopped,consistent,deadline_ok)
    groups={g:[r for r in rows if r["group"]==g] for g in GROUPS}
    doc=dict(schema="cad-harness.verify-aggregate.v3",profile="verify-v3",prefix=prefix,version=manifest["version"],
        local_commit=manifest["local_commit"],plan_commit=manifest["plan_commit"],created_at=cad_agent.utc(),sha_manifest=digest,
        frozen_sha256=manifest["files"],summary=summary,groups=groups,per_suite={g:metric(rs) for g,rs in groups.items()},
        provider_tokens={g:token_totals(rs) for g,rs in groups.items()},real_calls=real_calls,
        interval_scope="Completed fixed cohorts/parts only. C and dev are outside bar_met; v1 reports are never re-scored.")
    write_json(outputs[0],doc)
    fields=("group","case","bar_class","id","run","scored","completed","passed","route_ok","q_score","critical_invention",
        "unsupported_origin","post_answer_first_attempt_pass","repair_success",
        "completion_reached","initial_q_score","wall_s","sol_calls","cad_attempts","parse_repairs","repair_calls","repair_eligible",
        "failure_class","episode_stop_reason","stop_reason",*cad_agent.USAGE_KEYS)
    with outputs[1].open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({k:row["tokens"].get(k) if k in cad_agent.USAGE_KEYS else row.get(k) for k in fields})
    return doc


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); subs=parser.add_subparsers(dest="command",required=True)
    f=subs.add_parser("freeze"); f.add_argument("--version",default="verify-v3-phase2-uncommitted")
    f.add_argument("--implementation-commit",default="pending_supervisor"); f.add_argument("--plan-commit",default="pending_supervisor")
    f.add_argument("--codex",help="Hash the reviewed CLI executable and record --version; never generates")
    r=subs.add_parser("run"); r.add_argument("--prefix",required=True); r.add_argument("--quota-snapshot",required=True)
    r.add_argument("--call-budget",type=int,default=163); r.add_argument("--codex")
    r=subs.add_parser('resume');r.add_argument('--prefix',required=True);r.add_argument('--run-manifest',required=True)
    r.add_argument('--quota-snapshot',required=True);r.add_argument('--codex')
    r=subs.add_parser('rerun');r.add_argument('--prefix',required=True);r.add_argument('--ids',required=True)
    r.add_argument('--run-manifest',required=True);r.add_argument('--quota-snapshot',required=True);r.add_argument('--codex')
    a=subs.add_parser("aggregate"); a.add_argument("--prefix",required=True); a.add_argument("--suffix",required=True)
    a.add_argument('--run-manifest')
    a.add_argument('--rerun2',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.command=="freeze":
            result=freeze(version=args.version,implementation_commit=args.implementation_commit,plan_commit=args.plan_commit,codex=args.codex)
            print(json.dumps({"files":len(result["files"]),"version":result["version"],"local_commit":result["local_commit"]})); return 0
        if args.command=="run":
            result=run(args.prefix,args.quota_snapshot,args.call_budget,args.codex)
            print(json.dumps({"completed":sum(r["completed"] for r in result["rows"]),"planned":len(result["rows"]),"stop_reason":result["stop_reason"]}))
            return 0 if not result["stop_reason"] else 1
        if args.command=='resume':
            result=resume(args.prefix,args.quota_snapshot,args.run_manifest,args.codex)
            print(json.dumps(dict(segment=2,completed=sum(r['completed'] for r in result['rows']),planned=len(result['rows']),
                real_calls=result['total_real_calls'],stop_reason=result['stop_reason'])))
            return 0 if not result['stop_reason'] else 1
        if args.command=='rerun':
            result=rerun(args.prefix,args.ids,args.quota_snapshot,args.run_manifest,args.codex)
            print(json.dumps(dict(completed=sum(r['completed'] for r in result['rows']),planned=len(result['rows']),
                real_calls=result['total_real_calls'],stop_reason=result['stop_reason'])))
            return 0 if not result['stop_reason'] else 1
        result=aggregate(args.prefix,args.suffix,run_manifest=args.run_manifest,rerun2=args.rerun2); print(json.dumps(result["summary"],allow_nan=False))
        return 0 if result["summary"]["bar_met"] else 1
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        print(json.dumps({"status":"stopped","message_code":str(exc)})); return 2


if __name__=="__main__": raise SystemExit(main())
