"""Run stdlib unittest with the current interpreter; preserve raw output and exit code."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = ROOT / "tests" / "evidence"
    evidence.mkdir(exist_ok=True)
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True)
    (evidence / "unittest.stdout.log").write_bytes(result.stdout)
    (evidence / "unittest.stderr.log").write_bytes(result.stderr)
    metadata = {"command": command, "cwd": str(ROOT), "python_version": sys.version,
                "returncode": result.returncode, "scope": "A1 contracts only; no FreeCAD/CAD execution"}
    (evidence / "invocation.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
