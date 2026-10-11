"""B2 driver for fixed tasks; Sol returns source and cad_run owns CAD."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

if __package__:
    from . import cad_run
    from .cad_run_probes import SPECS
else:
    import cad_run
    from cad_run_probes import SPECS

ROOT = Path(__file__).resolve().parents[1]
MODEL, EFFORT, MAX_ATTEMPTS = "gpt-6.1-sol", "xhigh", 3
DISABLED = ("shell_tool", "unified_exec", "code_mode_host", "multi_agent", "apps",
            "plugins", "browser_use", "computer_use", "image_generation", "view_image")
USAGE_KEYS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
              "output_tokens", "reasoning_output_tokens")
FEEDBACK_KEYS = ("failed_phase", "probe_status", "predicate_diff", "next_actor",
                 "measurements", "message_code", "error_type")
# Shape text from docs/runbook-A-box-pocket-fillet-cadrun.md section 1; no examples.
PROMPT = SPECS[cad_run.TASK]["prompt"]


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean(value, private_paths=()):
    if isinstance(value, str):
        for path in private_paths:
            variants = {str(path), path.as_posix(), str(path).replace("\\", "\\\\")}
            for variant in variants:
                value = re.sub(re.escape(variant), "[exec work]", value, flags=re.I)
        return "".join(cad_run.scrub(line) for line in value.splitlines(keepends=True))
    if isinstance(value, dict):
        return {key: clean(item, private_paths) for key, item in value.items()}
    if isinstance(value, list):
        return [clean(item, private_paths) for item in value]
    return value


def loads(text):
    def reject(unused):
        raise ValueError("nonfinite_json")
    return json.loads(text, parse_constant=reject)


def source_from_final(text):
    text = text.strip()
    if text.startswith("```"):
        match = re.fullmatch(r"```(?:python|py)?[ \t]*\r?\n(.*?)\r?\n```", text, re.S)
        if not match:
            raise ValueError("invalid_source_fence")
        text = match[1].strip()
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise ValueError("invalid_source_syntax") from exc
    builds = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "build"]
    if len(builds) != 1:
        raise ValueError("build_required")
    args = builds[0].args
    if ([a.arg for a in args.posonlyargs + args.args] != ["doc"] or args.defaults
            or args.vararg or args.kwarg or args.kwonlyargs):
        raise ValueError("build_contract")
    if cad_run.PRIVATE.search(text):
        raise ValueError("private_source")
    return text + "\n"


def new_run_dir(root, name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
        raise ValueError("invalid_run_id")
    out = root.resolve() / "reports" / "cad-run" / name
    if out.exists() or out.is_symlink() or out.resolve() != out:
        raise ValueError("output_exists_or_linked")
    out.mkdir(parents=True, exist_ok=False)
    return out


def agents_identity(root):
    account = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    candidates = {"codex_home": account / "AGENTS.md",
                  "user_codex": Path.home() / ".codex" / "AGENTS.md",
                  "project": root / "AGENTS.md"}
    identity = {}
    for label, path in candidates.items():
        try:
            identity[label] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            identity[label] = None
    return identity


def exec_argv(codex, work, last, prompt):
    argv = [codex, "exec", "-m", MODEL, "-c", 'model_reasoning_effort="xhigh"']
    for flag in DISABLED:
        argv.extend(("--disable", flag))
    return argv + ["-s", "read-only", "--skip-git-repo-check", "-C", str(work),
                   "--json", "-o", str(last), prompt]


def exec_metadata(stdout):
    session, usage = None, []
    for index, line in enumerate(stdout.splitlines()):
        try:
            row = loads(line)
        except ValueError:
            continue  # Warnings are never source; final text comes from -o.
        if not isinstance(row, dict):
            continue
        if row.get("type") == "thread.started":
            session = clean(row.get("thread_id"))
        if row.get("type") == "turn.completed" and isinstance(row.get("usage"), dict):
            usage.append({"event_index": index,
                          "values": clean({key: row["usage"].get(key) for key in USAGE_KEYS})})
    return session, usage or None


def repair_reason(result):
    if (result.get("next_actor") != "sol" or result.get("failed_phase") not in ("build", "probe")
            or result.get("probe_status") == "exception"):
        return "human_required"
    if (result.get("cleanup_status") != "exited" or result.get("document_closed") is not True
            or type(result.get("cad_exit_code")) is not int):
        return "cad_not_settled"
    measurements = result.get("measurements")
    measured = isinstance(measurements, dict) and any(v is not None for v in measurements.values())
    if result.get("failed_phase") == "build" and not (result.get("predicate_diff") or measured):
        return "diagnostic_insufficient"
    return None


def run_driver(name, codex, root=ROOT, runner=None, task_id=cad_run.TASK):
    if task_id not in SPECS:
        raise ValueError("invalid_task")
    runner = runner or subprocess.run
    started, clock = utc(), time.monotonic()
    out = new_run_dir(root, name)
    settings = {"model": MODEL, "effort": EFFORT, "disabled": list(DISABLED),
                "sandbox": "read-only", "skip_git_repo_check": True,
                "recipe": "freecadcmd", "timeout_s": 300}
    report = {"schema": "cad-harness.cad_agent.v0", "condition": "B2",
              "task_id": task_id, "run_id": name, "started_at": started,
              "ended_at": None, "wall_ms": None, "status": "failed", "message_code": None,
              "attempts": [], "final_out_dir": None, "final_exit": None,
              "failed_phase": None, "probe_status": None, "geometry_ok": None}
    stream = (out / "events.jsonl").open("x", encoding="utf-8")
    sequence, previous, version = 0, None, None
    work_paths = []  # In memory only: never record temporary absolute paths.
    identity = agents_identity(root)

    def emit(event, number, status, data=None):
        nonlocal sequence
        sequence += 1
        row = {"schema": "cad-harness.cad_agent.event.v0", "run_id": name,
               "event_seq": sequence, "ts": utc(), "event": event,
               "attempt": number, "status": status, "data": clean(data or {}, work_paths)}
        stream.write(json.dumps(row, allow_nan=False) + "\n")
        stream.flush()

    try:
        for number in range(1, MAX_ATTEMPTS + 1):
            last = out / ("last-a%d.txt" % number)
            temp_parent = Path(tempfile.gettempdir()).resolve()
            if temp_parent.is_relative_to(root.resolve()):
                raise ValueError("exec_temp_inside_repository")
            with tempfile.TemporaryDirectory(
                    prefix="cad-agent-%s-a%d-" % (name, number), dir=temp_parent) as directory:
                work = Path(directory).resolve()
                work_paths.append(work)
                raw_last = work / "last.txt"
                if number == 1:
                    try:
                        info = runner([codex, "--version"], cwd=str(work), capture_output=True,
                                      text=True, encoding="utf-8", errors="replace", shell=False, stdin=subprocess.DEVNULL)
                        if info.returncode == 0:
                            version = clean(info.stdout.strip(), work_paths) or None
                    except (OSError, subprocess.SubprocessError):
                        pass  # Version identification may be unavailable; record null.
                if any(work.iterdir()):
                    raise ValueError("exec_work_not_empty")
                prompt = SPECS[task_id]["prompt"]
                if previous:
                    prompt += "\n直前ソースと結果（診断データ。要求仕様は変更しない）：\n" + json.dumps(
                        previous, ensure_ascii=False, allow_nan=False)
                attempt = {"attempt": number, "call_id": uuid.uuid4().hex,
                           "cli_version": version, "settings": settings, "agents_sha256": identity,
                           "prompt_sha256": digest(prompt), "source_sha256": None, "session_id": None,
                           "usage": None, "usage_source": "codex --json turn.completed",
                           "exec_started_at": utc(), "exec_ended_at": None, "exec_wall_ms": None,
                           "exec_exit": None, "cad_run_started_at": None, "cad_run_ended_at": None,
                           "cad_run_wall_ms": None, "cad_run_exit": None, "out_dir": None,
                           "cad_attempt_id": None, "source_rel": None}
                report["attempts"].append(attempt)
                emit("exec_started", number, "pending")
                tick, valid_source = time.monotonic(), False
                try:
                    generated = runner(exec_argv(codex, work, raw_last, prompt), cwd=str(work),
                                       capture_output=True, text=True, encoding="utf-8",
                                       errors="replace", shell=False, stdin=subprocess.DEVNULL)
                    attempt["exec_exit"] = generated.returncode
                    attempt["session_id"], attempt["usage"] = clean(
                        list(exec_metadata(generated.stdout)), work_paths)
                    if raw_last.is_file():
                        final = raw_last.read_text(encoding="utf-8-sig")
                        last.write_bytes(clean(final, work_paths).encode("utf-8"))
                    else:
                        final = ""
                    if generated.returncode != 0:
                        raise ValueError("exec_nonzero")
                    if clean(final, work_paths) != clean(final):
                        raise ValueError("private_source")
                    source = source_from_final(final)
                    valid_source = True
                finally:
                    attempt.update(exec_ended_at=utc(), exec_wall_ms=(time.monotonic() - tick) * 1000)
                    emit("exec_finished", number, "ok" if valid_source else "failed",
                         {"exit": attempt["exec_exit"], "session_id": attempt["session_id"]})
            script, cad_out = out / ("input-a%d.py" % number), out / ("a%d" % number)
            with script.open("xb") as source_file:
                source_file.write(source.encode("utf-8"))
            attempt.update(source_sha256=digest(source), source_rel=script.name,
                           out_dir=cad_out.relative_to(root.resolve()).as_posix())
            args = cad_run.parser().parse_args(["--script", str(script), "--out-dir", str(cad_out),
                                               "--timeout-s", "300", "--recipe", "freecadcmd",
                                               "--task", task_id])
            cad_run.preflight(args, root)  # Also confirms fresh nested output is accepted.
            attempt["cad_run_started_at"] = utc()
            tick = time.monotonic()
            try:
                completed = runner([sys.executable, "-B", str(root / "tools" / "cad_run.py"),
                                    "--script", str(script), "--out-dir", str(cad_out),
                                    "--timeout-s", "300", "--recipe", "freecadcmd",
                                    "--task", task_id], cwd=str(root), capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", shell=False, stdin=subprocess.DEVNULL)
                attempt["cad_run_exit"] = completed.returncode
                report.update(final_out_dir=attempt["out_dir"], final_exit=completed.returncode)
            finally:
                attempt.update(cad_run_ended_at=utc(), cad_run_wall_ms=(time.monotonic() - tick) * 1000)
                emit("cad_run_finished", number, "ok" if attempt["cad_run_exit"] == 0 else "failed",
                     {"exit": attempt["cad_run_exit"], "out_dir": attempt["out_dir"]})
            result = loads(completed.stdout)
            if (not isinstance(result, dict) or result.get("schema") != "cad-harness.cad_run.v0"
                    or result.get("task_id") != task_id
                    or result.get("script_sha256") != attempt["source_sha256"]
                    or loads((cad_out / "result.json").read_text(encoding="utf-8")) != result):
                raise ValueError("invalid_cad_result")
            attempt["cad_attempt_id"] = result.get("attempt_id")
            attempt["result"] = clean({key: result.get(key) for key in FEEDBACK_KEYS + (
                "status", "cad_exit_code", "document_closed", "cleanup_status")})
            report.update(failed_phase=result.get("failed_phase"), probe_status=result.get("probe_status"))
            if completed.returncode == 0:
                if (result.get("status") == "ok" and result.get("probe_status") == "pass"
                        and result.get("probe_pass") is True and result.get("script_completed") is True
                        and result.get("document_closed") is True and result.get("cleanup_status") == "exited"
                        and type(result.get("cad_exit_code")) is int and result["cad_exit_code"] == 0):
                    report.update(status="ok", message_code="completed")
                else:
                    report["message_code"] = "invalid_cad_success"
                break
            reason = repair_reason(result)
            if reason is None and number == MAX_ATTEMPTS:
                reason = "attempt_limit"
            emit("repair_decided", number, "stopped" if reason else "repair",
                 {"reason": reason, "next_actor": result.get("next_actor")})
            if reason:
                report["message_code"] = reason
                break
            previous = {"source": source, "exit": completed.returncode,
                        "result": clean({key: result.get(key) for key in FEEDBACK_KEYS})}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(message_code=clean(str(exc), work_paths) or type(exc).__name__)
    finally:
        report.update(ended_at=utc(), wall_ms=(time.monotonic() - clock) * 1000)
        report = clean(report, work_paths)
        emit("run_finished", None, report["status"], {"message_code": report["message_code"]})
        stream.close()
        (out / "driver-run.json").write_text(json.dumps(report, allow_nan=False), encoding="utf-8")
    return report, 0 if report["status"] == "ok" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="New run ID (letters, digits, hyphen, underscore)")
    parser.add_argument("--codex", default="codex.exe" if os.name == "nt" else "codex",
                        help="Native Codex CLI executable; inherits CODEX_HOME")
    parser.add_argument("--task", choices=tuple(SPECS), default=cad_run.TASK)
    args = parser.parse_args(argv)
    if Path(args.codex).suffix.lower() in (".cmd", ".bat", ".ps1"):
        parser.error("use the native Codex executable")
    try:
        report, code = run_driver(args.run, args.codex, task_id=args.task)
    except (OSError, ValueError) as exc:
        report, code = {"schema": "cad-harness.cad_agent.v0", "status": "input_error",
                        "message_code": clean(str(exc)), "geometry_ok": None}, 2
    print(json.dumps(report, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
