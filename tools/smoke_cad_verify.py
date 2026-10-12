"""No-model, fresh-output manual native VERIFY smokes; stop at the first mismatch."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import cad_agent, cad_run, cad_spec, cad_verify_probe
from tools.cad_verify_guard import q_score


def smoke(prefix,partition="all"):
    if not prefix.endswith("-mvp1"): raise ValueError("mvp_suffix_required")
    directory=cad_agent.new_run_dir(ROOT,prefix)
    base=ROOT/"design/cad-harness-verify"
    rows=[]; stopped=None
    groups=("dev","test") if partition=="all" else (partition,)
    try:
        for group in groups:
            for case_dir in sorted((base/group).iterdir()):
                if not case_dir.is_dir() or not (case_dir/"positive.py").is_file(): continue
                gold=cad_verify_probe.load_gold(case_dir/"gold.json")
                for variant in ("positive","negative"):
                    tick=time.monotonic()
                    out=directory/(group+"-"+case_dir.name+"-"+variant+"-mvp1")
                    args=cad_run.parser().parse_args(["--script",str(case_dir/(variant+".py")),"--out-dir",str(out),
                          "--task",gold["case_id"],"--timeout-s","300","--probe-profile","verify-v1", "--gold",str(case_dir/"gold.json")])
                    result,code=cad_run.run_attempt(args)
                    passing=variant=="positive"
                    native=(result.get("measurements") or {}).get("editability",{}).get("native_valid")
                    expected_edit=json.loads((case_dir/"offline.json").read_text(encoding="utf-8"))[variant]["editability"]
                    ok=(result.get("geometry_ok") is passing and native is True and result.get("editability_ok") is expected_edit
                        and result.get("probe_pass") is passing and code==(0 if passing else 1)
                        and result.get("document_closed") is True and result.get("cleanup_status")=="exited"
                        and result.get("cad_exit_code")==0 and (not passing or result.get("verification_pass") is True))
                    row=dict(partition=group,case=case_dir.name,variant=variant,expected_geometry=passing,ok=ok,
                             geometry=result.get("geometry_ok"),editability=result.get("editability_ok"),reimport=result.get("verification_pass"),
                             native_valid=native,
                             volume_mm3=(result.get("measurements") or {}).get("volume_mm3"),
                             scoped_volume_mm3=(result.get("measurements") or {}).get("scoped_volume_mm3"),
                             gold_volume_mm3=gold["volume"]["target_mm3"],wall_s=time.monotonic()-tick,
                             out_dir=out.relative_to(ROOT).as_posix(),failure_class=result.get("failed_phase"))
                    rows.append(row); print(json.dumps(row),flush=True)
                    if not ok:
                        stopped="fixture_gold_disagreement:"+group+"/"+case_dir.name+"/"+variant
                        return 1
            for case_dir in sorted((base/group).iterdir()):
                if not (case_dir/"rubric.json").is_file(): continue
                rubric=json.loads((case_dir/"rubric.json").read_text(encoding="utf-8"))
                if "required_fields" not in rubric: continue
                for variant in ("positive","negative"):
                    fields=rubric[variant]["needs_clarification"]
                    score,_=q_score(dict(kind="needs_clarification",fields=fields,raw=rubric[variant]),False,case_dir.name,rubric)
                    ok=score==(1 if variant=="positive" else 0)
                    row=dict(partition=group,case=case_dir.name,variant=variant,q_score=score,cad_attempts=0,sol_calls=0,ok=ok)
                    rows.append(row); print(json.dumps(row),flush=True)
                    if not ok:
                        stopped="rubric_disagreement"; return 1
        if "test" in groups:
            for case in ("F1","F2","F3"):
                folder=base/"test"/case
                gold=cad_verify_probe.load_gold(folder/"gold.json")
                rule=json.loads((folder/"fault.json").read_text(encoding="utf-8"))
                candidate=folder/("candidate.py" if case!="F3" else "manual-negative.py")
                sources=[("positive",base/"test"/rule["base_case"]/"positive.py"),("injected",candidate)]
                if case=="F3":
                    compiled=directory/"F3-injected-spec.py"
                    with compiled.open("x",encoding="utf-8") as f:
                        f.write(cad_spec.compile_spec(cad_spec.loads_spec((folder/"candidate.json").read_text(encoding="utf-8"))))
                    sources.append(("injected-spec",compiled))
                for variant,source in sources:
                    out=directory/(case+"-"+variant+"-mvp1")
                    args=cad_run.parser().parse_args(["--script",str(source),"--out-dir",str(out),"--task",case,
                         "--timeout-s","300","--probe-profile","verify-v1","--gold",str(folder/"gold.json"),
                         "--generator","compiler" if variant=="injected-spec" else "agent"])
                    result,code=cad_run.run_attempt(args); passing=variant=="positive"
                    native=(result.get("measurements") or {}).get("editability",{}).get("native_valid")
                    ok=(result.get("geometry_ok") is passing and native is True and (not passing or result.get("editability_ok") is True)
                        and code==(0 if passing else 1) and result.get("document_closed") is True
                        and result.get("cleanup_status")=="exited" and result.get("cad_exit_code")==0
                        and ((result.get("verification_pass") is True) if passing else
                             rule["expected_predicate"] in result.get("predicate_diff",[])))
                    row=dict(partition="test",case=case,variant=variant,geometry=result.get("geometry_ok"),editability=result.get("editability_ok"),
                             native_valid=native,reimport=result.get("verification_pass"),out_dir=out.relative_to(ROOT).as_posix(),ok=ok,
                             volume_mm3=(result.get("measurements") or {}).get("volume_mm3"))
                    rows.append(row); print(json.dumps(row),flush=True)
                    if not ok:
                        stopped="fault_fixture_disagreement:"+case+"/"+variant; return 1
        return 0
    finally:
        with (directory/"smoke-summary.json").open("x",encoding="utf-8") as f:
            json.dump(dict(measured_at=datetime.now(timezone.utc).isoformat(),rows=rows,stop_reason=stopped,sol_calls=0),f,indent=2)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--run",required=True)
    p.add_argument("--partition",choices=("all","dev","test"),default="all")
    args=p.parse_args(); raise SystemExit(smoke(args.run,args.partition))
