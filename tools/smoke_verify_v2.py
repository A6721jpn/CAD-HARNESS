"""Fresh native VERIFY v2 controls; no Sol, stop at the first disagreement."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import cad_agent, cad_run, cad_spec, cad_verify_v2_probe, eval_verify
from tools.cad_verify_guard import Fault, q_score

BASE = ROOT / "design/cad-harness-verify-v2/test"


def smoke(prefix):
    if not prefix.endswith("-mvp1"):
        raise ValueError("mvp_suffix_required")
    directory = cad_agent.new_run_dir(ROOT, prefix)
    rows, stopped = [], None

    def attempt(folder, source, variant, expected, fault=None, kind="agent"):
        tick = time.monotonic()
        out = directory / (folder.name+"-"+variant+"-mvp1")
        args = cad_run.parser().parse_args(["--script", str(source), "--out-dir", str(out), "--task", folder.name,
            "--timeout-s", "300", "--probe-profile", "verify-v2", "--generator", kind, "--gold", str(folder/"gold.json")])
        result, code = cad_run.run_attempt(args)
        measured = result.get("measurements") or {}
        native = (measured.get("editability") or {}).get("native_valid")
        wanted_pass = expected["geometry"] and expected["editability"]
        ok = (result.get("geometry_ok") is expected["geometry"] and result.get("editability_ok") is expected["editability"]
              and native is True and result.get("probe_pass") is wanted_pass and code == (0 if wanted_pass else 1)
              and result.get("cad_exit_code") == 0 and result.get("script_completed") is True
              and result.get("document_closed") is True and result.get("cleanup_status") == "exited"
              and (not wanted_pass or eval_verify.result_pass(result)))
        if fault:
            fault.observe(result, 1)
            ok &= fault.record["reached"] and fault.record["injected"] and fault.record["established"] and fault.record["detected"]
            if fault.rule["kind"] == "source":
                ok &= result["script_sha256"] == fault.record["injected_sha256"]
        gold = cad_verify_v2_probe.load_gold(folder/"gold.json")
        row = dict(case=folder.name, variant=variant, ok=bool(ok), geometry=result.get("geometry_ok"),
            editability=result.get("editability_ok"), native_valid=native, reimport=result.get("verification_pass"),
            measured_volume_mm3=measured.get("volume_mm3"), scoped_volume_mm3=measured.get("scoped_volume_mm3"),
            expected_volume_mm3=gold["volume"]["target_mm3"], expected=expected, wall_s=time.monotonic()-tick,
            out_dir=out.relative_to(ROOT).as_posix(), failed_phase=result.get("failed_phase"),
            fault=fault.record if fault else None)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if not ok:
            raise ValueError("fixture_gold_disagreement:"+folder.name+"/"+variant)

    try:
        for folder in sorted(BASE.iterdir()):
            if not (folder/"positive.py").is_file():
                continue
            controls = json.loads((folder/"offline.json").read_text(encoding="utf-8"))
            for variant in ("positive", "negative"):
                attempt(folder, folder/(variant+".py"), variant, controls[variant])
        for mode in ("decoy", "reference", "inactive"):
            attempt(BASE/"W5", BASE/"W5"/("pcd-"+mode+".py"), "pcd-"+mode,
                    dict(geometry=True, editability=False))
        for case in ("K1", "K2", "K3"):
            folder = BASE/case
            fault = Fault(folder/"fault.json")
            if case == "K3":
                wrong = json.loads((folder/"candidate.json").read_text(encoding="utf-8"))
                original = json.loads(json.dumps(wrong)); original["holes"][0]["diameter"] = 5
                source = directory/"K3-compiler-positive.py"
                source.write_bytes(cad_spec.compile_spec(original).encode("utf-8"))
                attempt(folder, source, "compiler-positive", dict(geometry=True, editability=True), kind="compiler")
                injected = cad_spec.compile_spec(fault.inject("spec", original))
            else:
                injected = fault.inject("source", (folder/"positive.py").read_text(encoding="utf-8"))
            source = directory/(case+"-injected.py")
            source.write_bytes(injected.encode("utf-8"))
            expected = json.loads((folder/"offline.json").read_text(encoding="utf-8"))["negative"]
            attempt(folder, source, "fault-injected", expected, fault, "compiler" if case == "K3" else "agent")
        for case in ("A2", "A3", "C2", "C3"):
            rubric = json.loads((BASE/case/"rubric.json").read_text(encoding="utf-8"))
            for variant in ("positive", "negative"):
                raw = rubric[variant]
                first = dict(kind="needs_clarification", fields=raw["needs_clarification"], raw=raw)
                score, _ = q_score(first, False, case, rubric)
                ok = score == (1 if variant == "positive" else 0)
                row = dict(case=case, variant=variant, q_score=score, sol_calls=0, cad_attempts=0, ok=ok)
                rows.append(row); print(json.dumps(row), flush=True)
                if not ok: raise ValueError("rubric_disagreement:"+case)
    except (OSError, ValueError) as exc:
        stopped = str(exc)
    finally:
        with (directory/"smoke-summary.json").open("x", encoding="utf-8") as output:
            json.dump(dict(measured_at=datetime.now(timezone.utc).isoformat(), sol_calls=0, rows=rows, stop_reason=stopped),
                      output, ensure_ascii=False, indent=2, allow_nan=False)
    return 0 if rows and not stopped and all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    raise SystemExit(smoke(parser.parse_args().run))
