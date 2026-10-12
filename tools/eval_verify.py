"""Frozen VERIFY evaluation: run on the supervisor host; aggregate launches nothing."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time

if __package__:
    from . import cad_agent, cad_run, cad_run_probes, eval_mvp
    from .cad_spec_probe import read_json
    from .cad_verify_guard import Guard, Fault, Stop, q_score
else:
    import cad_agent, cad_run, cad_run_probes, eval_mvp
    from cad_spec_probe import read_json
    from cad_verify_guard import Guard, Fault, Stop, q_score

ROOT=Path(__file__).resolve().parents[1]
DESIGN="design/cad-harness-verify"
CODE=("tools/cad_agent.py","tools/cad_run.py","tools/cad_run_freecad.py","tools/cad_verify_freecad.py",
      "tools/cad_verify_probe.py","tools/cad_verify_guard.py","tools/cad_spec.py","tools/cad_spec_probe.py",
      "tools/cad_run_probes.py","tools/eval_mvp.py","tools/eval_verify.py","tools/smoke_cad_verify.py",
      "tools/fixtures/verify_native.py","tools/test_cad_verify.py","skills/freecad-modeling/SKILL.md",
      "design/cad-harness-mvp/build-schema.json","design/cad-harness-mvp/DECISION-01-acceptance-bar.md",
      "tools/fixtures/cad_run_a_build.py","tools/fixtures/cad_run_a_broken_mvp.py",
      "tools/fixtures/cad_run_b_build.py","tools/fixtures/cad_run_b_broken_mvp.py")


def sha(raw): return hashlib.sha256(raw).hexdigest()


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)


def freeze(root=ROOT):
    """Write once, before any live call; the supervisor then commits these files."""
    root=Path(root).resolve(); base=root/DESIGN
    paths=[root/name for name in CODE]
    paths += list((root/"design/cad-harness-mvp/eval-v1").glob("*.json"))
    paths += [base/"PLAN-CONSENSUS.md",base/"gold-schema.json",base/"run-order.json"]
    for part in ("test","dev"):
        paths += [p for p in (base/part).rglob("*") if p.is_file()]
    hashes={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(set(paths))}
    value=dict(schema="cad-harness.verify-sha.v1",plan_commit="f0e8953",created_at=cad_agent.utc(),
               files=hashes,agents_sha256=cad_agent.agents_identity(root),
               settings=dict(model=cad_agent.MODEL,effort=cad_agent.EFFORT,disabled=list(cad_agent.DISABLED),sandbox="read-only"),
               local_commit="pending_supervisor")
    write_json(base/"SHA256.json",value)
    return value


def verify_frozen(root,manifest):
    root=Path(root).resolve()
    for name,expected in manifest["files"].items():
        path=root/name
        if not path.resolve().is_relative_to(root) or sha(path.read_bytes()) != expected:
            raise Stop("sha_mismatch:"+name)
    if cad_agent.agents_identity(root) != manifest["agents_sha256"]:
        raise Stop("inherited_agents_changed")
    settings=dict(model=cad_agent.MODEL,effort=cad_agent.EFFORT,disabled=list(cad_agent.DISABLED),sandbox="read-only")
    if manifest["settings"] != settings: raise Stop("model_settings_changed")


def paths(root,prefix):
    prefix=eval_mvp.valid_name(prefix)
    root=Path(root).resolve()
    suite=root/"reports/cad-run"/(prefix+"-verify-suite-mvp1")
    if suite.resolve()!=suite: raise ValueError("linked_suite_path")
    return suite


def run_name(prefix,entry): return prefix+"-"+entry["id"]+"-mvp1"


def load(root):
    base=root/DESIGN
    manifest=read_json((base/"SHA256.json").read_text(encoding="utf-8"))
    order=read_json((base/"run-order.json").read_text(encoding="utf-8"))
    if manifest["schema"]!="cad-harness.verify-sha.v1" or order["schema"]!="cad-harness.verify-order.v1":
        raise ValueError("verify_manifest_contract")
    verify_frozen(root,manifest)
    return manifest,order


def result_pass(result):
    v=result.get("verification") or {}
    return (result.get("status")=="ok" and result.get("geometry_ok") is True and result.get("editability_ok") is True
        and result.get("probe_pass") is True and result.get("probe_status")=="pass" and result.get("script_completed") is True
        and result.get("document_closed") is True and result.get("cleanup_status")=="exited"
        and type(result.get("cad_exit_code")) is int and result["cad_exit_code"]==0
        and result.get("verification_pass") is True and result.get("verification_cleanup_status")=="exited"
        and type(result.get("verification_exit_code")) is int and result["verification_exit_code"]==0
        and v.get("verification_pass") is True and v.get("document_closed") is True
        and type(result.get("owned_pid")) is int and type(result.get("verification_pid")) is int
        and result["owned_pid"]!=result["verification_pid"])


def gates(result):
    return dict(geometry=result.get("geometry_ok"),editability=result.get("editability_ok"),
                reimport=result.get("verification_pass"),passed=result_pass(result))


def harness_failure(report):
    code=str(report.get("message_code") or "")
    if any(v in code for v in ("quota_","deadline","insufficient_call_budget")):
        return code
    if any(v in code for v in ("sha_","binding","invalid_cad","compiler_","cli_version","context_argv","exec_temp_","inherited_agents","fault_false_pass","fault_detection_mismatch")):
        return "harness:"+code
    for a in report.get("attempts",[]):
        r=a["result"]
        if (r.get("failed_phase") in ("launch","cleanup","verification","export") or r.get("probe_status")=="exception"
                or r.get("save_error_type") or r.get("export_error_type") or r.get("close_error_type")
                or r.get("code_owner")=="harness"
                or r.get("cleanup_status")!="exited" or r.get("document_closed") is not True):
            return "harness:"+str(r.get("message_code") or r.get("failed_phase") or "unsettled_cad")
    return None


def empty_row(entry,name,reason=None):
    return dict(**entry,run=name,completed=False,passed=False,initial=None,final=None,route_ok=None,
                failure_class="not_started",stop_reason=reason,wall_s=None,sol_calls=None,cad_attempts=None,
                q_score=None,critical_invention=False,fault=None,tokens=dict.fromkeys(cad_agent.USAGE_KEYS))


def record(root,entry,name):
    row=empty_row(entry,name); where=eval_mvp.run_path(root,name)
    try:
        report=read_json((where/"driver-run.json").read_text(encoding="utf-8"))
        case=entry["case"]; group=entry["group"]
        verify=group!="mvp"
        base=root/DESIGN/("dev" if group=="dev" else "test")/case
        text=(base/"description.txt").read_bytes() if verify else eval_mvp.suite(root)[case]["gold"]["description"].encode("utf-8")
        if (report.get("run_id")!=name or report.get("task_id")!=case or report.get("mode")!="description"
                or report.get("description_sha256")!=sha(text) or report.get("schema")!="cad-harness.cad_agent.mvp1"):
            raise ValueError("driver_binding")
        wall=report["wall_ms"]/1000
        if not math.isfinite(wall) or wall<0: raise ValueError("wall_contract")
        row.update(completed=True,wall_s=wall,sol_calls=report["llm_calls"],cad_attempts=report["cad_attempts"],
                   tokens=eval_mvp.provider_tokens(report),driver_identity={k:report.get(k) for k in eval_mvp.IDENTITY},
                   first_response=report.get("first_response"),fault=report.get("fault"),stop_reason=harness_failure(report),
                   parse_repairs=sum(c.get("purpose")=="parse_repair" for c in report["calls"]),
                   repair_calls=sum(c.get("purpose")=="repair" for c in report["calls"]),
                   call_kinds=[c.get("purpose",c.get("kind")) for c in report["calls"]])
        if row["sol_calls"]==0 and row["stop_reason"]:
            row.update(completed=False,failure_class=row["stop_reason"])
            return row
        if (len(report["calls"])!=row["sol_calls"] or len(report["attempts"])!=row["cad_attempts"]
                or not 1<=row["sol_calls"]<=entry["max_calls"] or row["cad_attempts"]>3):
            raise ValueError("budget_binding")
        for c in report["calls"]:
            snapshot=c.get("quota_snapshot")
            if (c.get("prompt_sha256")!=sha(text) or not snapshot or snapshot["decision"]!="allow"
                    or not 0<=snapshot["age_s"]<=300 or snapshot["used_percent"]>=55):
                raise ValueError("call_quota_or_prompt_binding")
        attempts=report["attempts"]
        for a in attempts:
            out=root/a["out_dir"]
            if not out.resolve().is_relative_to(where) or out.resolve()!=out:
                raise ValueError("attempt_path_binding")
            actual=read_json((out/"result.json").read_text(encoding="utf-8"))
            if actual != a["result"] or sha((out/"input.py").read_bytes())!=a["source_sha256"]:
                raise ValueError("attempt_result_binding")
            gold_path=(base/"gold.json") if verify else eval_mvp.suite(root)[case]["path"]
            if (actual.get("task_id")!=case or actual.get("script_sha256")!=a["source_sha256"]
                    or actual.get("gold_sha256")!=sha(gold_path.read_bytes())
                    or sha((out/"gold.json").read_bytes())!=actual["gold_sha256"]):
                raise ValueError("attempt_gold_binding")
            if result_pass(actual):
                if set(actual.get("artifact_sha256",{})) != {"model.FCStd","model.step"}:
                    raise ValueError("artifact_hashes_missing")
                for filename,expected in actual["artifact_sha256"].items():
                    if sha((out/filename).read_bytes())!=expected: raise ValueError("artifact_sha_changed")
                if read_json((out/"verify-result.json").read_text(encoding="utf-8")) != actual["verification"]:
                    raise ValueError("artifact_report_binding")
        result=attempts[-1]["result"] if attempts else {}
        if report.get("status")=="ok" and not result_pass(result): row["stop_reason"]="harness:false_pass"
        if attempts:
            row.update(initial=gates(attempts[0]["result"]),final=gates(result))
        source_path=report.get("unsupported_to_source") is True
        if group=="mvp": route=True
        elif case in ("V1","V2","V3","V4","V5","F1","F2","DV1","DV2","DV3","DV4","DV5"):
            route=source_path and any(a["result"].get("generator")=="agent" for a in attempts)
        else: route=not source_path and any(a["result"].get("generator")=="compiler" for a in attempts)
        row.update(route_ok=route,unsupported_to_source=source_path)
        row["passed"]=(report.get("status")=="ok" and result_pass(result) and route and wall<=900 and not row["stop_reason"])
        if group=="q" or case.startswith("DQ"):
            rubric=read_json((base/"rubric.json").read_text(encoding="utf-8"))
            row["q_score"],row["critical_invention"]=q_score(report.get("first_response"),row["passed"],case,
                                                             rubric if "required_fields" in rubric else None)
            if "required_fields" in rubric:
                row["passed"]=row["q_score"]==1 and row["sol_calls"]==1 and row["cad_attempts"]==0 and wall<=900
                row["route_ok"]=None
            else: row["passed"] &= row["q_score"]==1
        first=attempts[0]["result"] if attempts else {}
        row["natural_repair_eligible"]=bool(group!="fault" and attempts and not result_pass(first)
                                           and cad_agent.repair_reason(first) is None)
        row["failure_class"]=None if row["passed"] else eval_mvp.failure_class(report,result)
        if row["stop_reason"]: row["failure_class"]=row["stop_reason"]
        if group=="mvp":
            row["mvp_record"]=eval_mvp.record(root,case,name,eval_mvp.suite(root)[case])
    except FileNotFoundError:
        row["failure_class"]="missing_report"
    except (ValueError,KeyError,TypeError,OSError,AttributeError) as exc:
        row.update(passed=False,stop_reason="harness:report_binding",failure_class="protocol",error=str(exc))
    return row


def legacy_record(root,entry,name):
    row=empty_row(entry,name)
    path=eval_mvp.run_path(root,name)
    try:
        r=read_json((path/"result.json").read_text(encoding="utf-8"))
        expected=entry["case"].endswith("good")
        settled=r.get("document_closed") is True and r.get("cleanup_status")=="exited" and r.get("cad_exit_code")==0
        row.update(completed=True,passed=r.get("probe_pass") is expected and settled,
                   sol_calls=0,cad_attempts=1,initial=gates(r),final=gates(r),failure_class=None,
                   expected_geometry_pass=expected)
        if r.get("failed_phase")=="launch" or not settled or r.get("probe_status")=="exception":
            row.update(passed=False,stop_reason="harness:legacy_runtime")
    except (ValueError,OSError): row.update(stop_reason="harness:legacy_report",failure_class="missing_report")
    return row


def run(prefix,snapshot,call_budget=125,codex=None,root=ROOT,runner=None,clock=None):
    root=Path(root).resolve()
    guard=Guard(snapshot,call_budget=call_budget,clock=clock)
    manifest,order=load(root); directory=paths(root,prefix)
    names=[run_name(prefix,e) for e in order["entries"]]
    if directory.exists() or any(eval_mvp.run_path(root,n).exists() for n in names): raise ValueError("prefix_exists")
    guard.check_versions=lambda:verify_frozen(root,manifest)
    directory.mkdir(parents=True,exist_ok=False)
    write_json(directory/"plan.json",dict(entries=order["entries"],sha_manifest=sha((root/DESIGN/"SHA256.json").read_bytes()),
                                         started_at=cad_agent.utc(),started_monotonic=guard.started,deadline_monotonic=guard.deadline))
    rows=[]; stopped="insufficient_planned_call_budget" if call_budget<order["planned_calls"] else None; dev_calls=0
    with (directory/"progress.jsonl").open("x",encoding="utf-8") as progress:
        for e,name in zip(order["entries"],names):
            row=empty_row(e,name,stopped)
            tick=guard.clock()
            if stopped is None:
                try:
                    guard.before_run(sum(later["min_calls"] for later in order["entries"][e["sequence"]-1:]))
                    if e["group"]=="legacy":
                        is_a=e["case"].startswith("A-"); good=e["case"].endswith("good")
                        filename="cad_run_"+("a" if is_a else "b")+("_build.py" if good else "_broken_mvp.py")
                        args=cad_run.parser().parse_args(["--script",str(root/"tools/fixtures"/filename),"--out-dir",str(eval_mvp.run_path(root,name)),
                            "--task",cad_run_probes.TASK_A if is_a else cad_run_probes.TASK_B,"--timeout-s",str(math.floor(min(300,guard.remaining())))])
                        cad_run.run_attempt(args,root=root)
                        row=legacy_record(root,e,name)
                    else:
                        group=e["group"]; case=e["case"]
                        where=root/DESIGN/("dev" if group=="dev" else "test")/case
                        is_mvp=group=="mvp"
                        gold=eval_mvp.suite(root)[case]["path"] if is_mvp else where/"gold.json"
                        text=eval_mvp.suite(root)[case]["gold"]["description"] if is_mvp else (where/"description.txt").read_text(encoding="utf-8")
                        rubric=read_json((where/"rubric.json").read_text(encoding="utf-8")) if e.get("first_response") else None
                        max_calls=min(e["max_calls"],4-dev_calls) if group=="dev" else e["max_calls"]
                        if max_calls<e["min_calls"]: raise Stop("dev_call_budget_exceeded")
                        fault=Fault(where/"fault.json") if group=="fault" else None
                        report,code=cad_agent.run_mvp_driver(name,codex or ("codex.exe" if sys.platform=="win32" else "codex"),text,
                              gold if gold.is_file() else None,root=root,runner=runner,evaluation=group!="dev",
                              probe_profile="mvp-v1" if is_mvp else "verify-v1",first_response_only=e.get("first_response",False),
                              rubric=rubric,fault=fault,guard=guard,max_calls=max_calls)
                        if group=="dev": dev_calls+=report["llm_calls"]
                        row=record(root,e,name)
                    guard.remaining(reserve=0)
                    verify_frozen(root,manifest)
                    if row.get("stop_reason"): stopped=row["stop_reason"]
                except (OSError,ValueError) as exc:
                    stopped=str(exc)
                    row.update(passed=False,stop_reason=stopped,failure_class=stopped)
            row["observed_wall_s"]=guard.clock()-tick if row["completed"] else None
            if row["completed"]: row["wall_s"]=max(row["wall_s"] or 0,row["observed_wall_s"])
            row["ended_elapsed_s"]=guard.clock()-guard.started
            if row["ended_elapsed_s"]>=10800: row["passed"]=False
            rows.append(row)
            progress.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n"); progress.flush()
            print(json.dumps({"id":e["id"],"completed":row["completed"],"passed":row["passed"],"stop_reason":stopped}),flush=True)
    document=dict(schema="cad-harness.verify-run.v1",prefix=prefix,created_at=cad_agent.utc(),
                  started_monotonic=guard.started,deadline_monotonic=guard.deadline,wall_s=guard.clock()-guard.started,
                  stop_reason=stopped,rows=rows,real_calls=guard.calls,dev_calls=dev_calls,quota_snapshots=guard.snapshots,
                  frozen_sha256=manifest["files"],sha_manifest=sha((root/DESIGN/"SHA256.json").read_bytes()))
    write_json(directory/"suite-run.json",document)
    return document


def wilson(successes,total,complete=True):
    if not complete or not total: return None
    z=1.96; p=successes/total; denominator=1+z*z/total
    center=(p+z*z/(2*total))/denominator
    delta=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return [max(0,center-delta),min(1,center+delta)]


def metric(rows,success="passed"):
    done=sum(r["completed"] for r in rows)
    passes=sum(bool(r.get(success)) for r in rows)
    return dict(planned=len(rows),completed=done,successes=passes,wilson95=wilson(passes,len(rows),done==len(rows)))


def summarize(rows,stopped=None,versions_consistent=True,deadline_ok=True):
    bycase={c:[r for r in rows if r["case"]==c] for c in dict.fromkeys(r["case"] for r in rows)}
    parts={c:metric(v) for c,v in bycase.items()}
    frows=[r for r in rows if r["group"]=="fault"]
    fmetrics={key:dict(planned=len(frows),completed=sum(r["completed"] for r in frows),
                    successes=sum(bool((r.get("fault") or {}).get(key)) for r in frows),
                    wilson95=wilson(sum(bool((r.get("fault") or {}).get(key)) for r in frows),len(frows),all(r["completed"] for r in frows)))
              for key in ("reached","established","detected")}
    fmetrics["final_all_gate_pass"]=metric(frows)
    established=[r for r in frows if (r.get("fault") or {}).get("established")]
    fmetrics["pass_per_established"]={"successes":sum(r["passed"] for r in established),"denominator":len(established),
                                      "rate":sum(r["passed"] for r in established)/len(established) if established else None,
                                      "wilson95":wilson(sum(r["passed"] for r in established),len(established),all(r["completed"] for r in frows))}
    natural=[r for r in rows if r.get("natural_repair_eligible") and r["group"] in ("geometry","q")]
    natural_metric=dict(successes=sum(r["passed"] for r in natural),denominator=len(natural),
                        rate=sum(r["passed"] for r in natural)/len(natural) if natural else None)
    passed=lambda c:parts.get(c,{}).get("successes",0)
    counts=Counter(r["case"] for r in rows if r["group"] not in ("legacy","dev","mvp"))
    expected=Counter({**{c:2 for c in ("V1","V2","V3","V4","V5")},"V6":3,"S1":5,"Q1":3,"Q2":5,"Q3":5,"F1":2,"F2":2,"F3":2})
    valid=counts==expected and len({r["run"] for r in rows})==len(rows)
    mvp=[r.get("mvp_record",{}) for r in rows if r["group"]=="mvp"]
    mvp_bar=len(mvp)==10 and sum(bool(r.get("passed")) for r in mvp)>=8 and all(
        sum(bool(r.get("passed")) for r in mvp if r.get("case")==c)>=1 for c in eval_mvp.ORDER)
    legacy=[r for r in rows if r["group"]=="legacy"]
    complete=all(r["completed"] for r in rows)
    q_inventions=sum(r["critical_invention"] for r in rows if r["case"] in ("Q2","Q3"))
    real_repair_kinds={"source" if r["case"] in ("F1","F2") else "spec" for r in frows
                       if r["passed"] and (r.get("fault") or {}).get("established") and r.get("repair_calls",0)>0}
    fault_bar=(len(frows)==6 and fmetrics["established"]["successes"]==6 and fmetrics["detected"]["successes"]==6
               and sum(r["passed"] for r in frows)>=4 and all(passed(c)>=1 for c in ("F1","F2","F3"))
               and real_repair_kinds=={"source","spec"})
    walls=sorted(r["wall_s"] for r in rows if r.get("wall_s") is not None)
    times=dict(median=statistics.median(walls) if walls else None,p95=walls[max(0,math.ceil(.95*len(walls))-1)] if walls else None,
               maximum=max(walls) if walls else None)
    return dict(valid_suite=valid,complete=complete,versions_consistent=versions_consistent,deadline_ok=deadline_ok,
                stop_reason=stopped,per_part=parts,fault=fmetrics,natural_repair=natural_metric,
                parse_repair_calls=sum(r.get("parse_repairs",0) for r in rows),wall_s=times,
                critical_inventions=q_inventions,mvp_bar_met=mvp_bar,legacy_bar_met=len(legacy)==4 and all(r["passed"] for r in legacy),
                bar_met=bool(valid and complete and versions_consistent and deadline_ok and not stopped and mvp_bar
                    and len(legacy)==4 and all(r["passed"] for r in legacy)
                    and sum(passed(c) for c in ("V1","V2","V3","V4","V5"))>=8 and all(passed(c)>=1 for c in ("V1","V2","V3","V4","V5"))
                    and passed("V6")>=2 and passed("S1")>=4 and passed("Q1")>=2 and passed("Q2")>=4 and passed("Q3")>=4
                    and q_inventions==0 and fault_bar))


def aggregate(prefix,suffix,root=ROOT,clock=None):
    root=Path(root).resolve(); manifest,order=load(root); directory=paths(root,prefix)
    suffix=eval_mvp.valid_name(suffix)
    outputs=[root/"reports"/("aggregate-verify-v1-"+suffix+ext) for ext in (".json",".csv")]
    if any(p.exists() or p.is_symlink() or p.resolve()!=p for p in outputs): raise ValueError("aggregate_exists_or_linked")
    observed=read_json((directory/"suite-run.json").read_text(encoding="utf-8"))
    if (observed["schema"]!="cad-harness.verify-run.v1" or observed["prefix"]!=prefix
            or observed["sha_manifest"]!=sha((root/DESIGN/"SHA256.json").read_bytes())
            or [r["id"] for r in observed["rows"]] != [e["id"] for e in order["entries"]]):
        raise ValueError("suite_record_binding")
    rows=[]; consistent=observed["frozen_sha256"]==manifest["files"]
    for e,original in zip(order["entries"],observed["rows"]):
        name=run_name(prefix,e)
        if original["run"]!=name: raise ValueError("run_order_binding")
        row=(legacy_record(root,e,name) if e["group"]=="legacy" else record(root,e,name)) if original["completed"] else empty_row(e,name,original.get("stop_reason"))
        if original["completed"]:
            row["wall_s"]=max(row.get("wall_s") or 0,original.get("wall_s") or 0)
            if original.get("ended_elapsed_s",10801)>=10800: row["passed"]=False
            if original["passed"] != row["passed"]: consistent=False
        rows.append(row)
    identities=[r["driver_identity"] for r in rows if r.get("driver_identity")]
    cli_versions={v.get("cli_version") for v in identities}
    consistent &= len(cli_versions)==1 and None not in cli_versions
    for r in rows:
        ident=r.get("driver_identity")
        if not ident: continue
        profile="mvp" if r["group"]=="mvp" else "verify"
        probe_file="tools/cad_spec_probe.py" if profile=="mvp" else "tools/cad_verify_probe.py"
        consistent &= all(ident.get(k)==manifest["files"][p] for k,p in (
            ("skill_sha256","skills/freecad-modeling/SKILL.md"),("schema_sha256","design/cad-harness-mvp/build-schema.json"),
            ("compiler_sha256","tools/cad_spec.py"),("probe_sha256",probe_file)))
        consistent &= ident.get("agents_sha256")==manifest["agents_sha256"]
    deadline_ok=(clock or time.monotonic)()<observed["deadline_monotonic"] and observed["wall_s"]<10800
    stopped=observed.get("stop_reason") or next((r.get("stop_reason") for r in rows if r.get("stop_reason")),None)
    summary=summarize(rows,stopped,consistent,deadline_ok)
    groups={g:[r for r in rows if r["group"]==g] for g in ("geometry","q","fault","mvp","legacy","dev")}
    totals={g:{k:sum(r["tokens"][k] for r in rs) if rs and all(r["tokens"][k] is not None for r in rs) else None
                for k in cad_agent.USAGE_KEYS} for g,rs in groups.items()}
    doc=dict(schema="cad-harness.verify-aggregate.v1",created_at=cad_agent.utc(),prefix=prefix,
             summary=summary,groups=groups,provider_tokens=totals,frozen_sha256=manifest["files"],
             interval_scope="Completed fixed batches/parts only; no population JA/EN claim; groups are kept separate.")
    write_json(outputs[0],doc)
    fields=("group","case","id","run","completed","passed","route_ok","q_score","critical_invention","wall_s",
            "sol_calls","cad_attempts","failure_class","stop_reason",*cad_agent.USAGE_KEYS)
    with outputs[1].open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows: w.writerow({k:row["tokens"].get(k) if k in cad_agent.USAGE_KEYS else row.get(k) for k in fields})
    return doc


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("freeze",help="Write one SHA manifest before supervisor commit; never overwrite")
    r=sub.add_parser("run"); r.add_argument("--prefix",required=True); r.add_argument("--quota-snapshot",required=True)
    r.add_argument("--call-budget",type=int,default=125); r.add_argument("--codex")
    a=sub.add_parser("aggregate"); a.add_argument("--prefix",required=True); a.add_argument("--suffix",required=True)
    args=p.parse_args(argv)
    try:
        if args.command=="freeze": result=freeze(); print(json.dumps({"files":len(result["files"]),"local_commit":result["local_commit"]})); return 0
        if args.command=="run":
            result=run(args.prefix,args.quota_snapshot,args.call_budget,args.codex)
            print(json.dumps({"completed":sum(r["completed"] for r in result["rows"]),"planned":len(result["rows"]),"stop_reason":result["stop_reason"]}))
            return 0 if not result["stop_reason"] else 1
        result=aggregate(args.prefix,args.suffix); print(json.dumps(result["summary"],allow_nan=False))
        return 0 if result["summary"]["bar_met"] else 1
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"stopped","message_code":str(exc)})); return 2


if __name__=="__main__": raise SystemExit(main())
