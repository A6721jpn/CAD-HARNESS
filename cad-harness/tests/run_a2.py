"""Run native A2 tests and independent FreeCADCmd reload processes, preserving raw logs.

Usage: python cad-harness/tests/run_a2.py [new-evidence-directory]
Each run uses a new directory, so earlier failures and binary artifacts survive.
"""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

EXE = Path(r"C:\Users\NGGmo\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe")
HERE = Path(__file__).resolve().parent


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "evidence/a2" / stamp
    out.mkdir(parents=True, exist_ok=False)
    summary = {"passed": False, "invocations": [],
               "scope": "A1 regression plus A2 native generation, B-Rep measurement and separate-process reload/edit",
               "geometry_validation_note": "A1 ranges imply e > D/2, W > D and L-2e > D. Invalid geometry examples (including e <= D/2) are rejected by A1 range checks before geometric checks."}
    for stage, length in (("build", ""), ("reopen-L100", "100"), ("reopen-L140", "140"), ("reopen-L160", "160")):
        env = dict(os.environ, A2_OUTPUT=str(out), A2_STAGE=stage, A2_LENGTH=length, PYTHONDONTWRITEBYTECODE="1")
        command = [str(EXE), str(HERE / "a2_worker.py")]
        invocation = {"stage": stage, "command": command, "cwd": str(HERE.parent),
                      "environment": {k: env[k] for k in ("A2_OUTPUT", "A2_STAGE", "A2_LENGTH")}}
        try:
            process = subprocess.run(command, env=env, cwd=HERE.parent, capture_output=True, timeout=180)
            invocation["returncode"] = process.returncode
            stdout, stderr = process.stdout, process.stderr
        except subprocess.TimeoutExpired as exc:
            invocation["error"] = "timeout after 180 seconds"
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
        except OSError as exc:
            invocation["error"] = str(exc)
            stdout, stderr = b"", b""
        (out / (stage + ".stdout.log")).write_bytes(stdout)
        (out / (stage + ".stderr.log")).write_bytes(stderr)
        path = out / (stage + ".json")
        report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        invocation["passed"] = (invocation.get("returncode") == 0 and report.get("passed") is True
                                and report.get("tests_run", 0) > 0 and not report.get("skipped", []))
        summary["invocations"].append(invocation)
        print(json.dumps(invocation), flush=True)
        if not invocation["passed"]:
            break
    summary["passed"] = len(summary["invocations"]) == 4 and all(i["passed"] for i in summary["invocations"])
    (out / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Evidence: " + str(out))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
