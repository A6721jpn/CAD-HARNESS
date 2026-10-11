"""Authorized offline FreeCAD smokes, always in fresh -mvp1 directories."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import cad_agent, cad_run, cad_run_probes
from tools.fixtures.cad_mvp_build import SUITE_INPUTS, HELD_OUT, typed_spec


def run(prefix, group="all"):
    if not prefix.endswith("-mvp1"):
        raise ValueError("mvp_suffix_required")
    manifest = cad_agent.new_run_dir(ROOT, prefix)
    rows = []
    if group in ("all", "legacy"):
        for case, task, filename, passing in (
                ("A-good", cad_run_probes.TASK_A, "cad_run_a_build.py", True),
                ("A-broken", cad_run_probes.TASK_A, "cad_run_a_broken_mvp.py", False),
                ("B-good", cad_run_probes.TASK_B, "cad_run_b_build.py", True),
                ("B-broken", cad_run_probes.TASK_B, "cad_run_b_broken_mvp.py", False)):
            out = manifest / (case + "-mvp1")
            args = cad_run.parser().parse_args(["--script", str(ROOT / "tools/fixtures" / filename),
                                               "--out-dir", str(out), "--task", task, "--timeout-s", "300"])
            result, code = cad_run.run_attempt(args)
            row = {"case":case,"expected_pass":passing,"pass":result["probe_pass"],"exit":code,
                   "volume_mm3":(result.get("measurements") or {}).get("volume_mm3"),
                   "out_dir":out.relative_to(ROOT).as_posix(),"failed_phase":result["failed_phase"],
                   "ok":code == (0 if passing else 1) and result["probe_pass"] is passing}
            rows.append(row)
            print(json.dumps(row), flush=True)
            if result["failed_phase"] == "launch":
                break  # A sandbox launch failure requires supervisor execution, never escalation.
    inputs = list(SUITE_INPUTS) if group in ("all", "suite") else []
    if group in ("all", "held-out"):
        inputs += list(HELD_OUT)
    if not any(row["failed_phase"] == "launch" for row in rows):
        for case in inputs:
            gold = (ROOT / "design/cad-harness-mvp/eval-v1" / (case + ".json") if case.startswith("P")
                    else ROOT / "tools/fixtures/mvp" / (case + ".gold.json"))
            report, code = cad_agent.run_mvp_driver(prefix + "-" + case + "-mvp1", "NEVER-CALL-MODEL",
                                                   json.dumps(typed_spec(case)), gold, mode="typed")
            result = report["attempts"][-1]["result"] if report["attempts"] else {}
            row = {"case":case,"expected_pass":True,"pass":result.get("probe_pass"),"exit":code,
                   "volume_mm3":(result.get("measurements") or {}).get("volume_mm3"),
                   "gold_volume_mm3":json.loads(gold.read_text(encoding="utf-8"))["volume"]["target_mm3"],
                   "verification_pass":result.get("verification_pass"),"llm_calls":report["llm_calls"],
                   "wall_ms":report["wall_ms"],"out_dir":report["final_out_dir"],
                   "failed_phase":result.get("failed_phase"),"message_code":report["message_code"],
                   "ok":code == 0 and result.get("verification_pass") is True and report["llm_calls"] == 0}
            rows.append(row)
            print(json.dumps(row), flush=True)
            if result.get("failed_phase") == "launch":
                break
    with (manifest / "smoke-summary.json").open("x",encoding="utf-8") as output:
        json.dump({"measured_at":datetime.now(timezone.utc).isoformat(),"rows":rows},output,indent=2)
    return 0 if rows and all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",required=True)
    parser.add_argument("--group",choices=("all","legacy","suite","held-out"),default="all")
    args = parser.parse_args()
    raise SystemExit(run(args.run,args.group))
