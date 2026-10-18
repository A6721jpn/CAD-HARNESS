"""Capture unmodified FreeCAD stdout/stderr. Run with any host Python 3.

Usage: python a0/probes/run_datum_link_joint_probe.py <new-output-directory>
FreeCAD's exit code alone does not indicate that the probe passed.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

exe = Path(r"C:\Users\NGGmo\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe")
probe = Path(__file__).with_name("datum_link_joint_probe.py").resolve()
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
env = dict(os.environ, A0_DATUM_PROBE_DIR=str(out), A0_DATUM_PROBE_MODE="create")
command = [str(exe), str(probe)]
completed = subprocess.run(command, env=env, capture_output=True, timeout=180)
(out / "stdout.log").write_bytes(completed.stdout)
(out / "stderr.log").write_bytes(completed.stderr)
(out / "invocation.json").write_text(json.dumps({"command": command,
    "environment": {key: env[key] for key in ("A0_DATUM_PROBE_DIR", "A0_DATUM_PROBE_MODE")},
    "exit_code": completed.returncode}, indent=2) + "\n", encoding="utf-8")
result = json.loads((out / "result.json").read_text(encoding="utf-8"))
print(json.dumps({"exit_code": completed.returncode, "statuses": {
    key: value["status"] for key, value in result["stages"].items()}}, indent=2))
