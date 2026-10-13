"""VERIFY v2: new frozen holdout, separate completion cohort; aggregate launches nothing."""
import argparse
import ast
from collections import Counter
import csv
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
    from . import cad_verify_v2_agent as agent
    from .cad_spec_probe import read_json
    from .cad_verify_v2_guard import Guard, Fault, Stop, q_score, Budget
else:
    import cad_agent, cad_run, cad_run_probes, cad_spec, eval_mvp, eval_verify
    import cad_verify_v2_agent as agent
    from cad_spec_probe import read_json
    from cad_verify_v2_guard import Guard, Fault, Stop, q_score, Budget

ROOT=Path(__file__).resolve().parents[1]
DESIGN="design/cad-harness-verify-v2"
CODE=tuple(dict.fromkeys((*eval_verify.CODE,
    "tools/cad_verify_v2_probe.py", "tools/cad_verify_v2_guard.py", "tools/cad_verify_v2_agent.py",
    "tools/eval_verify_v2.py", "tools/smoke_verify_v2.py", "tools/fixtures/verify_v2_native.py",
    "tools/test_verify_v2.py", "tools/test_verify_v2_native.py", "tools/test_support.py",
    "design/cad-harness-verify/gold-schema.json")))
GROUPS=("dev","legacy","mvp","geometry","q","completion","fault")
CAPS={"source":4,"spec":3,"ask":1,"completion":4,"offline":0,"mvp":3}
sha=eval_verify.sha
write_json=eval_verify.write_json
result_pass=eval_verify.result_pass
gates=eval_verify.gates
wilson=eval_verify.wilson


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


def freeze(root=ROOT,version="verify-v2-phase2-uncommitted",implementation_commit="pending_supervisor",plan_commit="pending_supervisor",codex=None,runner=None):
    """Never overwrite; reviewed commit identities are supplied by the supervisor."""
    root=Path(root).resolve(); base=root/DESIGN
    eval_mvp.valid_name(version)
    names=set(CODE)
    names.update(p.relative_to(root).as_posix() for p in (root/"design/cad-harness-mvp/eval-v1").glob("*.json"))
    names.update(DESIGN+"/"+n for n in ("PLAN-V2-CONSENSUS.md","run-order.json"))
    for part in ("test","dev"):
        names.update(p.relative_to(root).as_posix() for p in (base/part).rglob("*") if p.is_file())
    refs=read_json((base/"dev/v1-references.json").read_text(encoding="utf-8"))
    names.update(refs["files"])
    hashes={n:sha(safe_file(root,n).read_bytes()) for n in sorted(names)}
    if any(hashes[n]!=expected for n,expected in refs["files"].items()): raise Stop("v1_dev_reference_changed")
    if implementation_commit!="pending_supervisor" and not re.fullmatch(r"[0-9a-f]{7,40}",implementation_commit):
        raise ValueError("implementation_commit_required")
    if plan_commit!="pending_supervisor" and not re.fullmatch(r"[0-9a-f]{7,40}",plan_commit):
        raise ValueError("plan_commit_required")
    value=dict(schema="cad-harness.verify-sha.v2",profile="verify-v2",version=version,created_at=cad_agent.utc(),
        local_commit=implementation_commit,plan_commit=plan_commit,files=hashes,
        cli=cli_identity(codex,runner) if codex else None,
        agents_sha256=cad_agent.agents_identity(root),settings=dict(model=cad_agent.MODEL,effort=cad_agent.EFFORT,
            disabled=list(cad_agent.DISABLED),sandbox="read-only"))
    if version.startswith("verify-v2-reviewed-") and not value["cli"]: raise Stop("reviewed_cli_freeze_required")
    validate_order(read_json((base/"run-order.json").read_text(encoding="utf-8")))
    write_json(base/"SHA256.json",value)
    return value


def verify_frozen(root,manifest):
    if manifest.get("schema")!="cad-harness.verify-sha.v2" or manifest.get("profile")!="verify-v2":
        raise Stop("verify_v2_manifest_contract")
    for name,expected in manifest["files"].items():
        if sha(safe_file(root,name).read_bytes())!=expected: raise Stop("sha_mismatch:"+name)
    if cad_agent.agents_identity(root)!=manifest["agents_sha256"]: raise Stop("inherited_agents_changed")
    settings=dict(model=cad_agent.MODEL,effort=cad_agent.EFFORT,disabled=list(cad_agent.DISABLED),sandbox="read-only")
    if settings!=manifest["settings"]: raise Stop("model_settings_changed")
    cli=manifest.get("cli")
    if cli and sha(Path(cli["path"]).read_bytes())!=cli["sha256"]: raise Stop("cli_sha_mismatch")


def validate_order(order):
    entries=order["entries"]
    expected=Counter({("dev","V1"):1,("dev","V6"):1,("dev","Q2"):1,
        **{("legacy",c):1 for c in ("A-good","A-broken","B-good","B-broken")},
        **{("mvp",c):2 for c in eval_mvp.ORDER},**{("geometry",c):2 for c in ("W1","W2","W3","W4","W5")},
        ("geometry","W6"):3,("geometry","S2"):5,("q","A1"):3,("q","A2"):5,("q","A3"):5,
        ("completion","C2"):3,("completion","C3"):3,**{("fault",c):2 for c in ("K1","K2","K3")}})
    if (order.get("schema")!="cad-harness.verify-order.v2" or order.get("profile")!="verify-v2"
            or len(entries)!=60 or len({e["id"] for e in entries})!=60
            or [e["sequence"] for e in entries]!=list(range(1,61))
            or Counter((e["group"],e["case"]) for e in entries)!=expected
            or sum(e["min_calls"] for e in entries)!=83 or order.get("planned_calls")!=83
            or sum(e["max_calls"] for e in entries)!=163 or order.get("max_calls")!=163
            or sum(e["scored"] for e in entries)!=51 or order.get("core_count")!=51 or order.get("completion_count")!=6):
        raise Stop("verify_v2_order_contract")
    aliases={**{f"W{i}":f"V{i}" for i in range(1,7)},"S2":"S1","A1":"Q1","A2":"Q2","A3":"Q3",
             "K1":"F1","K2":"F2","K3":"F3"}
    for e in entries:
        eval_mvp.valid_name(e["id"])
        if e["route"] not in CAPS or e["group"] not in GROUPS: raise Stop("order_route_contract")
        cap=3 if e["group"]=="mvp" else CAPS[e["route"]]
        if not 0<=e["min_calls"]<=e["max_calls"]<=cap: raise Stop("order_call_contract")
        excluded=e["group"] in ("dev","completion")
        if e["scored"] is excluded or e["bar_class"]!=(None if excluded else aliases.get(e["case"],e["case"])):
            raise Stop("order_class_contract")


def load(root,reviewed=True):
    base=root/DESIGN
    manifest=read_json((base/"SHA256.json").read_text(encoding="utf-8"))
    order=read_json((base/"run-order.json").read_text(encoding="utf-8"))
    verify_frozen(root,manifest); validate_order(order)
    if reviewed and (not manifest["version"].startswith("verify-v2-reviewed-")
            or not manifest.get("cli")
            or any(not re.fullmatch(r"[0-9a-f]{7,40}",manifest.get(k,"")) for k in ("local_commit","plan_commit"))):
        raise Stop("supervisor_reviewed_freeze_required")
    return manifest,order


def paths(root,prefix):
    eval_mvp.valid_name(prefix)
    p=root/"reports/cad-run"/(prefix+"-verify-v2-suite-mvp1")
    if p.resolve()!=p: raise ValueError("linked_suite_path")
    return p


def run_name(prefix,entry): return prefix+"-"+entry["id"]+"-mvp1"


def inputs(root,entry):
    group,case=entry["group"],entry["case"]
    if group=="mvp":
        s=eval_mvp.suite(root)[case]
        return s["path"],s["gold"]["description"].encode("utf-8"),None,None
    base=root/DESIGN/"test"/case
    if group=="dev":
        refs=read_json((root/DESIGN/"dev/v1-references.json").read_text(encoding="utf-8"))
        base=safe_file(root,refs["preview_cases"][case])
    raw=(base/"description.txt").read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or raw.endswith(b"\n") or b"\r" in raw: raise Stop("description_bytes_contract")
    rubric=read_json((base/"rubric.json").read_text(encoding="utf-8")) if entry["first_response"] or group=="completion" else None
    gold=base/"gold.json" if (base/"gold.json").is_file() else None
    answer=None
    if group=="completion":
        answer=(base/"answer.txt").read_bytes()
        if answer.startswith(b"\xef\xbb\xbf") or answer.endswith(b"\n") or b"\r" in answer: raise Stop("answer_bytes_contract")
        expected=dict(schema="cad-harness.verify-completion-binding.v2",case_id=case,description_sha256=sha(raw),
            answer_sha256=sha(answer),completion_input_sha256=sha(raw+b"\n"+answer),separator_hex="0a")
        if read_json((base/"binding.json").read_text(encoding="utf-8"))!=expected: raise Stop("completion_sha_binding")
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
    if (type(n) is not int or n!=len(calls) or not 0<=n<=entry["max_calls"]
            or type(report["cad_attempts"]) is not int or report["cad_attempts"]!=len(attempts)
            or len(attempts)>(3 if entry["group"]=="mvp" else 0 if entry["group"]=="dev" or entry["route"]=="ask" else 2)):
        raise ValueError("budget_binding")
    purposes=Counter(c.get("purpose",c.get("kind")) for c in calls)
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
        expected=sha(raw+b"\n"+answer) if answer is not None and index>0 else sha(raw)
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
    return purposes


def check_attempts(root,entry,report,where,gold):
    for index,a in enumerate(report["attempts"]):
        out=safe_file(root,a["out_dir"])
        if not out.is_relative_to(where): raise ValueError("attempt_path_binding")
        r=read_json((out/"result.json").read_text(encoding="utf-8"))
        if r!=a["result"] or sha((out/"input.py").read_bytes())!=a["source_sha256"]:
            raise ValueError("attempt_result_binding")
        profile="mvp-v1" if entry["group"]=="mvp" else "verify-v2"
        if (r.get("schema")!="cad-harness.cad_run.v0" or r.get("probe_profile")!=profile or r.get("task_id")!=entry["case"]
                or r.get("script_sha256")!=a["source_sha256"] or r.get("gold_sha256")!=sha(gold.read_bytes())
                or sha((out/"gold.json").read_bytes())!=r["gold_sha256"]): raise ValueError("attempt_gold_binding")
        if profile=="verify-v2":
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
        if first["source_sha256"]!=sha(injected.encode("utf-8")): raise ValueError("fault_source_binding")
    else:
        path=where/("build-spec-c%d.json"%c["call"])
        if read_json(path.read_text(encoding="utf-8"))!=injected or first["source_sha256"]!=sha(cad_spec.compile_spec(injected).encode("utf-8")):
            raise ValueError("fault_spec_binding")
    rule.observe(first["result"],c["call"])
    if any(actual.get(k)!=rule.record.get(k) for k in ("observed","actual_call","established","detected")):
        raise ValueError("fault_observation_binding")
    return actual


def record(root,entry,name):
    row=empty_row(entry,name); where=eval_mvp.run_path(root,name)
    try:
        report=read_json((where/"driver-run.json").read_text(encoding="utf-8"))
        gold,raw,rubric,answer=inputs(root,entry); is_mvp=entry["group"]=="mvp"
        if (report.get("schema")!=("cad-harness.cad_agent.mvp1" if is_mvp else "cad-harness.cad_agent.verify2")
                or report.get("task_id")!=entry["case"] or report.get("run_id")!=name or report.get("mode")!="description"
                or report.get("description_sha256")!=sha(raw) or report.get("gold_sha256")!=(sha(gold.read_bytes()) if gold else None)):
            raise ValueError("driver_binding")
        if not is_mvp and (report.get("probe_profile")!="verify-v2" or report.get("route")!=entry["route"]
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
        if report.get("message_code")=="repair_time_reservation_lost":
            row["episode_stop_reason"]="repair_time_reservation_lost"
        if not report["calls"]:
            row.update(completed=False,failure_class=row["stop_reason"] or "not_invoked"); return row
        if entry["first_response"] or entry["group"]=="completion":
            final=(where/"last-c1.txt").read_text(encoding="utf-8")
            first=first_response(final)
            actual=report.get("first_response") or {}
            if any(actual.get(k)!=v for k,v in first.items()) or actual.get("sha256")!=sha(final.encode("utf-8")):
                raise ValueError("first_response_binding")
            row["first_response"]=first
        check_attempts(root,entry,report,where,gold)
        attempts=report["attempts"]; first=attempts[0]["result"] if attempts else {}; final=attempts[-1]["result"] if attempts else {}
        if report.get("status")=="ok" and not result_pass(final): row["stop_reason"]="harness:false_pass"
        if attempts: row.update(initial=gates(first),final=gates(final))
        source=report.get("unsupported_to_source") is True
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
                passed=score==1 and not invention and len(report["calls"])==1 and not attempts and wall<450
                row["route_ok"]=None
            else:
                if (report.get("answer_sha256")!=sha(answer) or report.get("completion_input_sha256")!=sha(raw+b"\n"+answer)
                        or report.get("initial_q_score")!=score or report.get("initial_critical_invention")!=invention):
                    raise ValueError("completion_report_binding")
                if read_json((where/"first-response.json").read_text(encoding="utf-8"))!=report["first_response"]:
                    raise ValueError("completion_first_artifact_binding")
                reached=report.get("completion_reached") is True
                actual_start=any(c["purpose"]=="interpretation" and c["invoked"] for c in report["calls"])
                if reached!=actual_start or reached and not (score and not invention) or (not reached and (len(report["calls"])!=1 or attempts)):
                    raise ValueError("completion_answer_gate_binding")
                row.update(completion_reached=reached,completion_not_reached_reason=report.get("completion_not_reached_reason"))
                passed &= reached
        elif entry["case"]=="A1":
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
            "fault_not_reached" if entry["group"]=="fault" and not (row["fault"] or {}).get("reached") else eval_mvp.failure_class(report,final))
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
    manifest,order=load(root); directory=paths(root,prefix)
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
    write_json(directory/"plan.json",dict(profile="verify-v2",version=manifest["version"],entries=order["entries"],
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
    document=dict(schema="cad-harness.verify-run.v2",profile="verify-v2",prefix=prefix,version=manifest["version"],
        local_commit=manifest["local_commit"],plan_commit=manifest["plan_commit"],created_at=cad_agent.utc(),
        started_monotonic=guard.started,deadline_monotonic=guard.deadline,wall_s=guard.clock()-guard.started,
        stop_reason=stopped,rows=rows,real_calls=guard.calls,dev_calls=dev_calls,quota_snapshots=guard.snapshots,
        frozen_sha256=manifest["files"],sha_manifest=digest,call_budget=call_budget)
    write_json(directory/"suite-run.json",document)
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
    kinds={"source" if r["case"] in ("K1","K2") else "spec" for r in fault if r["passed"] and r.get("repair_calls")==1}
    fbar=len(fault)==6 and all(fmetrics[k]["successes"]==6 for k in ("established","detected")) and sum(r["passed"] for r in fault)>=4 and all(passed(c)>=1 for c in ("K1","K2","K3")) and kinds=={"source","spec"}
    mvp=[r for r in core if r["group"]=="mvp"]; legacy=[r for r in core if r["group"]=="legacy"]
    mbar=len(mvp)==10 and sum(r["passed"] for r in mvp)>=8 and all(passed(c)>=1 for c in eval_mvp.ORDER)
    lbar=len(legacy)==4 and all(r["passed"] for r in legacy)
    thresholds=dict(source=sum(passed(c) for c in ("W1","W2","W3","W4","W5"))>=8 and all(passed(c)>=1 for c in ("W1","W2","W3","W4","W5")),
        complex=passed("W6")>=2,stock=passed("S2")>=4,defaults=passed("A1")>=2,
        ambiguity=passed("A2")>=4 and passed("A3")>=4 and sum(r["critical_invention"] for r in core if r["case"] in ("A2","A3"))==0,
        faults=fbar,mvp=mbar,legacy=lbar)
    completion={}
    for c in ("C2","C3"):
        rs=[r for r in rows if r["group"]=="completion" and r["case"]==c]
        correct=[r for r in rs if r["initial_q_score"]==1 and not r["initial_critical_invention"]]
        cm=conditional(correct)
        if not all(r["completed"] for r in rs): cm["wilson95"]=None
        completion[c]=dict(completion=metric(rs),initial_correct_question=metric(rs,"initial_q_score"),
            conditional_completion=cm,not_reached=sum(not r["completion_reached"] for r in rs))
    valid=[r["id"] for r in rows]==[e["id"] for e in order["entries"]] and len({r["run"] for r in rows})==60
    natural=[r for r in core if r.get("natural_repair_eligible")]
    nmetric=conditional(natural)
    if not all(r["completed"] for r in core): nmetric["wilson95"]=None
    crepair=conditional([r for r in rows if r["group"]=="completion" and r.get("natural_repair_eligible")])
    if not all(r["completed"] for r in rows if r["group"]=="completion"): crepair["wilson95"]=None
    return dict(valid_suite=valid,complete=all(r["completed"] for r in rows),core_complete=len(core)==51 and all(r["completed"] for r in core),
        versions_consistent=versions_consistent,deadline_ok=deadline_ok,stop_reason=stopped,thresholds=thresholds,
        bar_met=bool(valid and len(core)==51 and all(r["completed"] for r in core) and versions_consistent and deadline_ok and not stopped and all(thresholds.values())),
        per_part=parts,completion=completion,dev=dict(metric=metric(dev),scored=False),fault=fmetrics,
        natural_repair={**nmetric,"eligible":len(natural),"invoked":sum(r["repair_calls"]>0 for r in natural)},
        completion_repair=crepair,
        parse_repair_calls=sum(r.get("parse_repairs",0) for r in rows),repair_calls=sum(r.get("repair_calls",0) for r in rows))


def aggregate(prefix,suffix,root=ROOT,clock=None):
    root=Path(root).resolve(); manifest,order=load(root); directory=paths(root,prefix); eval_mvp.valid_name(suffix)
    outputs=[root/"reports"/("aggregate-verify-v2-"+suffix+ext) for ext in (".json",".csv")]
    if any(p.exists() or p.is_symlink() or p.resolve()!=p for p in outputs): raise ValueError("aggregate_exists_or_linked")
    observed=read_json((directory/"suite-run.json").read_text(encoding="utf-8"))
    plan=read_json((directory/"plan.json").read_text(encoding="utf-8"))
    digest=sha((root/DESIGN/"SHA256.json").read_bytes())
    if (observed["schema"]!="cad-harness.verify-run.v2" or observed["profile"]!="verify-v2" or observed["prefix"]!=prefix
            or observed["version"]!=manifest["version"] or observed["sha_manifest"]!=digest or plan["sha_manifest"]!=digest
            or plan["entries"]!=order["entries"] or [r["id"] for r in observed["rows"]]!=[e["id"] for e in order["entries"]]
            or observed["started_monotonic"]!=plan["started_monotonic"] or observed["deadline_monotonic"]!=plan["deadline_monotonic"]
            or observed["deadline_monotonic"]-observed["started_monotonic"]!=10800): raise ValueError("suite_record_binding")
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
                         ("compiler_sha256","tools/cad_spec.py"),("probe_sha256","tools/cad_spec_probe.py" if is_mvp else "tools/cad_verify_v2_probe.py")):
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
    doc=dict(schema="cad-harness.verify-aggregate.v2",profile="verify-v2",prefix=prefix,version=manifest["version"],
        local_commit=manifest["local_commit"],plan_commit=manifest["plan_commit"],created_at=cad_agent.utc(),sha_manifest=digest,
        frozen_sha256=manifest["files"],summary=summary,groups=groups,per_suite={g:metric(rs) for g,rs in groups.items()},
        provider_tokens={g:token_totals(rs) for g,rs in groups.items()},real_calls=real_calls,
        interval_scope="Completed fixed cohorts/parts only. C and dev are outside bar_met; v1 reports are never re-scored.")
    write_json(outputs[0],doc)
    fields=("group","case","bar_class","id","run","scored","completed","passed","route_ok","q_score","critical_invention",
        "completion_reached","initial_q_score","wall_s","sol_calls","cad_attempts","parse_repairs","repair_calls","repair_eligible",
        "failure_class","episode_stop_reason","stop_reason",*cad_agent.USAGE_KEYS)
    with outputs[1].open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({k:row["tokens"].get(k) if k in cad_agent.USAGE_KEYS else row.get(k) for k in fields})
    return doc


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); subs=parser.add_subparsers(dest="command",required=True)
    f=subs.add_parser("freeze"); f.add_argument("--version",default="verify-v2-phase2-uncommitted")
    f.add_argument("--implementation-commit",default="pending_supervisor"); f.add_argument("--plan-commit",default="pending_supervisor")
    f.add_argument("--codex",help="Hash the reviewed CLI executable and record --version; never generates")
    r=subs.add_parser("run"); r.add_argument("--prefix",required=True); r.add_argument("--quota-snapshot",required=True)
    r.add_argument("--call-budget",type=int,default=163); r.add_argument("--codex")
    a=subs.add_parser("aggregate"); a.add_argument("--prefix",required=True); a.add_argument("--suffix",required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="freeze":
            result=freeze(version=args.version,implementation_commit=args.implementation_commit,plan_commit=args.plan_commit,codex=args.codex)
            print(json.dumps({"files":len(result["files"]),"version":result["version"],"local_commit":result["local_commit"]})); return 0
        if args.command=="run":
            result=run(args.prefix,args.quota_snapshot,args.call_budget,args.codex)
            print(json.dumps({"completed":sum(r["completed"] for r in result["rows"]),"planned":len(result["rows"]),"stop_reason":result["stop_reason"]}))
            return 0 if not result["stop_reason"] else 1
        result=aggregate(args.prefix,args.suffix); print(json.dumps(result["summary"],allow_nan=False))
        return 0 if result["summary"]["bar_met"] else 1
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        print(json.dumps({"status":"stopped","message_code":str(exc)})); return 2


if __name__=="__main__": raise SystemExit(main())
