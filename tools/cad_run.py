"""Synchronous CAD runner with fixed task probes; no automatic retries."""
import argparse
import ast
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import uuid

if __package__:
    from .cad_run_probes import SPECS, TASK_A
else:
    from cad_run_probes import SPECS, TASK_A

ROOT = Path(__file__).resolve().parents[1]
FREECAD_DIR = Path("C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311")
TASK = TASK_A
EVENT_KEYS = ("schema", "cad_run_id", "attempt_id", "event_seq", "ts", "phase", "event",
              "status", "recipe", "script_sha256", "owned_pid", "cad_exit_code",
              "message_code", "artifact_rel", "data")
DATA_KEYS = {"stderr_bytes", "stderr_sha256", "removed_warning_lines", "predicate",
             "cleanup_action", "window_scan", "worker_ts"}
PRIVATE = re.compile(
    r"[a-z]:[\\/](?:users|documents and settings)[\\/]|/(?:home|users)/"
    r"|(?:api[_-]?key|authorization|password|secret|token)\s*[:=]", re.I)


def scrub(line):
    return "[redacted line]\n" if PRIVATE.search(line) else line


def judge_stub():
    return {"enabled": False, "invoked": False, "decision": None, "usage": None}


def known_launch_rule(text):
    for code, pattern in (("rule_path", r"\bPATH\b"),
                          ("rule_execution_policy", r"ExecutionPolicy|execution[ _-]?policy|実行ポリシー"),
                          ("rule_cim", r"\bCIM\b")):
        if re.search(pattern, text, re.I):
            return code
    return None


def new_result(task_id=TASK):
    fields = ("cad_run_id", "attempt_id", "recipe", "script_sha256", "source_sha256",
              "status", "failed_phase", "code_owner", "next_actor", "cad_exit_code",
              "script_completed", "probe_pass", "probe_status", "cleanup_status",
              "removed_warning_lines", "measurements", "predicate_diff", "timeout_s")
    return {"schema": "cad-harness.cad_run.v0", "task_id": task_id, "geometry_ok": None,
            "timings_ms": dict.fromkeys(("build", "recompute", "probe", "save")),
            **dict.fromkeys(fields), "artifacts": {}}


def fail(result, phase, code, owner="harness", actor="human"):
    result["status"] = "failed"
    if result["failed_phase"] is None:
        result.update(failed_phase=phase, code_owner=owner, message_code=code, next_actor=actor)


class Events:
    def __init__(self, out, result):
        self.result, self.sequence = result, 0
        self.stream = (out / "events.jsonl").open("x", encoding="utf-8")

    def emit(self, phase, event, status, code=None, artifact=None, data=None):
        self.sequence += 1
        row = dict.fromkeys(EVENT_KEYS)
        row.update(schema="cad-harness.cad_run.event.v0",
                   cad_run_id=self.result["cad_run_id"], attempt_id=self.result["attempt_id"],
                   event_seq=self.sequence, ts=datetime.now(timezone.utc).isoformat(),
                   phase=phase, event=event, status=status, recipe=self.result["recipe"],
                   script_sha256=self.result["script_sha256"],
                   owned_pid=self.result.get("owned_pid"),
                   cad_exit_code=self.result["cad_exit_code"], message_code=code,
                   artifact_rel=artifact, data={"worker_ts": None, **{k: v for k, v in (data or {}).items() if k in DATA_KEYS}})
        self.stream.write(json.dumps(row, allow_nan=False) + "\n")
        self.stream.flush()


class InputError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError("invalid_arguments")


def parser():
    p = Parser(prog="cad_run", description=__doc__)
    p.add_argument("--script", required=True, help="UTF-8 .py defining build(doc)")
    p.add_argument("--out-dir", required=True, help="New directory below reports/cad-run")
    p.add_argument("--timeout-s", required=True, type=int, help="Positive CAD runtime limit")
    p.add_argument("--recipe", choices=("freecadcmd", "console"), default="freecadcmd")
    p.add_argument("--task", choices=tuple(SPECS), default=TASK)
    return p


def preflight(args, root=ROOT):
    if args.task not in SPECS:
        raise InputError("invalid_task")
    if args.timeout_s <= 0:
        raise InputError("invalid_timeout")
    script = Path(args.script)
    script = script if script.is_absolute() else root / script
    raw = script.read_bytes()
    text = raw.decode("utf-8-sig")
    tree = ast.parse(text)
    if script.suffix.lower() != ".py" or not any(
            isinstance(n, ast.FunctionDef) and n.name == "build" for n in tree.body):
        raise InputError("build_required")
    if PRIVATE.search(text):
        raise InputError("private_input")
    source_hash = next((n.value.value for n in tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "SOURCE_SHA256" for t in n.targets)
                        and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)), None)
    out = Path(args.out_dir)
    if ".." in out.parts:
        raise InputError("parent_path")
    out = Path(os.path.abspath(out if out.is_absolute() else root / out))
    allowed = root.resolve() / "reports" / "cad-run"
    if not out.is_relative_to(allowed) or out == allowed or out.resolve() != out:
        raise InputError("output_root")
    if out.exists() or out.is_symlink():
        raise InputError("output_exists")
    return out, raw, source_hash


def window_scan(pid):
    """Inspect titles only after matching the PID; send no window messages."""
    if os.name != "nt":
        return {"state": "scan_failed"}
    try:
        user = ctypes.WinDLL("user32", use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
        user.GetWindowThreadProcessId.restype = wintypes.DWORD
        user.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        user.GetWindowTextW.restype = ctypes.c_int
        user.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
        user.GetWindowTextLengthW.restype = ctypes.c_int
        user.EnumWindows.argtypes = (callback_type, wintypes.LPARAM)
        user.EnumWindows.restype = wintypes.BOOL
        user.EnumChildWindows.argtypes = (wintypes.HWND, callback_type, wintypes.LPARAM)
        user.EnumChildWindows.restype = wintypes.BOOL
        owned, recovery, failed = [], False, False
        def visit(hwnd, unused):
            nonlocal recovery, failed
            owner = wintypes.DWORD()
            thread = user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value != pid:
                return True  # Unrelated or vanished windows cannot fail this PID's scan.
            if not thread:
                failed = True
                return True
            owned.append(hwnd)
            ctypes.set_last_error(0)
            length = user.GetWindowTextLengthW(hwnd)
            if not length and ctypes.get_last_error():
                failed = True
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            ctypes.set_last_error(0)
            copied = user.GetWindowTextW(hwnd, title, len(title))
            failed |= not copied and bool(ctypes.get_last_error())
            recovery |= "ドキュメントの復旧" in title.value
            return True
        callback = callback_type(visit)
        if not user.EnumWindows(callback, 0):
            return {"state": "scan_failed"}
        for hwnd in list(owned):
            user.EnumChildWindows(hwnd, callback, 0)
        state = "scan_failed" if failed else "recovery" if recovery else "windows" if owned else "no_windows"
        return {"state": state, "count": len(owned)}
    except Exception:
        return {"state": "scan_failed"}


def cleanup(proc, gui_up, scan=window_scan, wait_s=1, blocked=False):
    detail = {"cleanup_status": "not_started", "cleanup_action": "none", "window_scan": None}
    if proc is None:
        return detail
    if proc.poll() is not None:
        detail["cleanup_status"] = "exited"
        return detail
    if blocked:
        detail["cleanup_status"] = "cleanup_pending"
        return detail
    inspected = scan(proc.pid)
    detail.update(cleanup_status="cleanup_pending", window_scan=inspected)
    if not getattr(proc, "_handle", None) or gui_up not in (None, 0) or inspected["state"] != "no_windows":
        return detail
    try:
        # Popen.terminate uses the retained Windows handle, not a PID found by name.
        proc.terminate()
        detail["cleanup_action"] = "forced_own_headless_exit"
        proc.wait(timeout=wait_s)
        detail["cleanup_status"] = "exited"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return detail


def capture(stream, path, state):
    try:
        prefix = stream.peek(2)[:2] if hasattr(stream, "peek") else b""
        encoding = "utf-16" if prefix in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
        with io.TextIOWrapper(stream, encoding=encoding, errors="replace") as reader:
            with path.open("x", encoding="utf-8") as output:
                for line in reader:
                    if "'Midplane' property" in line:
                        state["warnings"] += 1
                    state["launch_rule"] = state.get("launch_rule") or known_launch_rule(line)
                    output.write(scrub(line))
                    output.flush()
    except Exception:
        state["failed"] = True


def merge_worker(result, worker, proc):
    if (worker.get("schema") != "cad-harness.cad_run.worker.v0"
            or worker.get("attempt_id") != result["attempt_id"]
            or worker.get("script_sha256") != result["script_sha256"]
            or worker.get("owned_pid") != proc.pid
            or worker.get("task_id", TASK) != result["task_id"]):
        raise ValueError("worker_protocol")
    fields = ("script_completed", "measurements", "predicate_diff", "reference", "document_closed")
    result.update({k: worker.get(k) for k in fields})
    result["timings_ms"] = worker.get("timings_ms", dict.fromkeys(("build", "recompute", "probe", "save")))
    if result["failed_phase"] is None:
        result.update(probe_pass=worker.get("probe_pass"), probe_status=worker.get("probe_status"))
    for key in ("error_type", "save_error_type", "close_error_type"):
        if key in worker:
            result[key] = worker[key]
    if worker.get("status") != "ok":
        fail(result, worker.get("failed_phase") or "build", "worker_failed",
             worker.get("code_owner") or "harness", worker.get("next_actor") or "human")
    if not worker.get("document_closed"):
        fail(result, "cleanup", "document_close_failed")
    if worker.get("status") == "ok" and (not result["script_completed"]
            or result["probe_pass"] is not True or result["probe_status"] != "pass"):
        fail(result, "probe" if result["script_completed"] else "build", "worker_incomplete")


def run_attempt(args, root=ROOT, popen=subprocess.Popen, scan=window_scan):
    try:
        out, raw, source_hash = preflight(args, root)
        out.mkdir(parents=True, exist_ok=False)
    except InputError:
        raise
    except (ValueError, OSError, UnicodeError, SyntaxError) as exc:
        raise InputError(type(exc).__name__) from exc
    result = new_result(args.task)
    result.update(cad_run_id=uuid.uuid4().hex, attempt_id=uuid.uuid4().hex,
                  recipe=args.recipe, script_sha256=hashlib.sha256(raw).hexdigest(),
                  source_sha256=source_hash, timeout_s=args.timeout_s, status="ok",
                  script_completed=False, probe_status="not_run")
    events, proc, threads = Events(out, result), None, []
    gui_up, consumed, timed_out = None, 0, False
    launch_resolved, capture_state = False, {"warnings": 0, "failed": False, "launch_rule": None}
    try:
        (out / "input.py").write_bytes(raw)
        cfg = '<?xml version="1.0" encoding="UTF-8"?><FCParameters><FCParamGroup Name="Root"/></FCParameters>'
        for name in ("user.cfg", "system.cfg"):
            (out / name).write_text(cfg, encoding="utf-8")
        (out / "request.json").write_text(json.dumps(
            {"task_id": args.task, "attempt_id": result["attempt_id"], "script_sha256": result["script_sha256"]}), encoding="utf-8")
        events.emit("preflight", "preflight_finished", "ok")
        exe = FREECAD_DIR / ("bin/freecadcmd.exe" if args.recipe == "freecadcmd" else "FreeCAD.exe")
        if not exe.is_file():
            fail(result, "launch", "missing_executable")
        else:
            argv = [str(exe)]
            if args.recipe == "console":
                argv.append("--console")
            argv += ["--user-cfg", str(out / "user.cfg"), "--system-cfg", str(out / "system.cfg"),
                     str(root / "tools" / "cad_run_freecad.py")]
            events.emit("launch", "launch_started", "pending", code="direct_recipe_v0")
            proc = popen(argv, cwd=str(out), stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            result["owned_pid"] = proc.pid
            (out / "owned-pid.json").write_text(json.dumps({"pid": proc.pid}), encoding="utf-8")
            for stream, name in ((proc.stdout, "stdout.txt"), (proc.stderr, "stderr.txt")):
                thread = threading.Thread(target=capture, args=(stream, out / name, capture_state), daemon=True)
                thread.start()
                threads.append(thread)
            events.emit("launch", "launch_finished", "pending")
            deadline = time.monotonic() + args.timeout_s
            while True:
                notifications = out / "worker-events.jsonl"
                if notifications.is_file():
                    text = notifications.read_text(encoding="utf-8")
                    lines = text.splitlines()
                    if text and not text.endswith("\n"):
                        lines = lines[:-1]
                    for line in lines[consumed:]:
                        message = json.loads(line)
                        if message["kind"] == "ready":
                            if message["owned_pid"] != proc.pid:
                                raise ValueError("owned_pid_mismatch")
                            gui_up = message.get("gui_up")
                            if not launch_resolved:
                                events.emit("launch", "launch_finished", "ok", code="worker_ready")
                                launch_resolved = True
                        elif message["kind"] == "event":
                            events.emit(message["phase"], message["event"], message["status"],
                                        data={**(message.get("data") or {}), "worker_ts": message.get("ts")})
                        consumed += 1
                if proc.poll() is not None:
                    break
                inspected = scan(proc.pid)
                if inspected["state"] == "recovery":
                    fail(result, "dialog", "recovery_dialog")
                    events.emit("cleanup", "dialog_detected", "pending", data={"window_scan": inspected})
                    break
                if gui_up not in (None, 0):
                    fail(result, "cleanup", "runtime_state_unknown")
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    fail(result, "build" if gui_up == 0 else "launch", "timeout")
                    break
                time.sleep(0.05)
    except Exception as exc:
        capture_state["launch_rule"] = capture_state["launch_rule"] or known_launch_rule(str(exc))
        fail(result, "launch" if proc is None else "build", "harness_" + type(exc).__name__)
    finally:
        recovered = cleanup(proc, gui_up, scan, min(1, args.timeout_s),
                            blocked=result["failed_phase"] in ("dialog", "cleanup"))
        result["cleanup_status"] = recovered["cleanup_status"]
        result["cad_exit_code"] = proc.poll() if proc is not None else None
        for thread in threads:
            thread.join(timeout=min(1, args.timeout_s))
        report = out / "worker-result.json"
        if proc is not None and report.is_file():
            try:
                worker = json.loads(report.read_text(encoding="utf-8"),
                                    parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite")))
                merge_worker(result, worker, proc)
            except Exception:
                fail(result, "build", "invalid_worker_result")
        elif proc is not None:
            fail(result, "launch", "missing_worker_result")
        if type(result["cad_exit_code"]) is int and result["cad_exit_code"] != 0:
            fail(result, "build" if gui_up == 0 else "launch", "cad_nonzero")
        if timed_out or recovered["cleanup_action"] != "none" or recovered["cleanup_status"] not in ("exited", "not_started"):
            fail(result, "cleanup", "cleanup_incomplete")
        if capture_state["failed"] or any(t.is_alive() for t in threads):
            fail(result, "cleanup", "capture_incomplete")
        result["removed_warning_lines"] = capture_state["warnings"]
        events.emit("cleanup", "cleanup_finished",
                    "ok" if result["cleanup_status"] == "exited" else "pending",
                    data={k: recovered[k] for k in ("cleanup_action", "window_scan")})
        if result["failed_phase"] == "launch":
            if capture_state["launch_rule"]:
                result["message_code"] = capture_state["launch_rule"]
            elif result.get("message_code") != "missing_executable":
                judge_stub()
                events.emit("j1", "j1_skipped", "skipped", code="disabled")
        launch_known = proc is None or launch_resolved or type(result["cad_exit_code"]) is int
        if launch_known and (result["failed_phase"] == "launch" or not launch_resolved):
            events.emit("launch", "launch_finished",
                        "failed" if result["failed_phase"] == "launch" or result["cad_exit_code"] != 0 else "ok",
                        code=result.get("message_code"))
        for name in ("stderr.txt", "stdout.txt", "model.FCStd", "input.py", "worker-result.json",
                     "worker-events.jsonl", "owned-pid.json", "request.json", "user.cfg", "system.cfg"):
            if (out / name).is_file():
                result["artifacts"][name] = name
        stderr = out / "stderr.txt"
        if stderr.is_file():
            data = stderr.read_bytes()
            events.emit("build", "build_finished", "ok" if result["script_completed"] else "failed",
                        artifact=stderr.name, data={"stderr_bytes": len(data),
                        "stderr_sha256": hashlib.sha256(data).hexdigest(),
                        "removed_warning_lines": result["removed_warning_lines"]})
        events.emit("run", "run_finished", result["status"])
        events.stream.close()
        result["artifacts"].update({"events.jsonl": "events.jsonl", "result.json": "result.json"})
        (out / "result.json").write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
    return result, 0 if result["status"] == "ok" else 1


def main(argv=None):
    args = None
    try:
        args = parser().parse_args(argv)
        result, code = run_attempt(args)
    except InputError as exc:
        result, code = new_result(getattr(args, "task", TASK)), 2
        result.update(status="input_error", failed_phase="preflight",
                      code_owner="harness", next_actor="human", probe_status="not_run", message_code=str(exc))
    except Exception as exc:
        result, code = new_result(getattr(args, "task", TASK)), 1
        result.update(status="failed", failed_phase="cleanup", code_owner="harness",
                      next_actor="human", message_code=type(exc).__name__)
    print(json.dumps(result, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
