"""B2: trusted A-only driver; Sol returns source and cad_run owns CAD."""
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
import time
import uuid

if __package__:
    from . import cad_run
else:
    import cad_run

ROOT = Path(__file__).resolve().parents[1]
MODEL, EFFORT, MAX_ATTEMPTS = "gpt-6.1-sol", "xhigh", 3
DISABLED = ("shell_tool", "unified_exec", "code_mode_host", "multi_agent", "apps",
            "plugins", "browser_use", "computer_use", "image_generation", "view_image")
USAGE_KEYS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
              "output_tokens", "reasoning_output_tokens")
FEEDBACK_KEYS = ("failed_phase", "probe_status", "predicate_diff", "next_actor",
                 "measurements", "message_code", "error_type")
# Shape text from docs/runbook-A-box-pocket-fillet-cadrun.md section 1; no examples.
PROMPT = """モデル / effort: gpt-6.1-sol / xhigh。
ホスト: DPC-019。CADはFreeCAD 1.1.4のみ。SolidWorksとFusionは起動しない。LPC-017ではCADを実行しない。
単位mm、新規ドキュメント、単一ソリッドボディで次を作る。
1) 直方体。幅40 mm（X）×奥行30 mm（Y）×高さ20 mm（Z）。PartDesignのBody上で、XYスケッチの中心矩形をPad長さ20 mmとする（片方向。貫通や対称の二重化はしない）。
2) 上面中央に20×15 mm、深さ5 mmの非貫通矩形ポケット。上面スケッチの中心矩形をPocket長さ5 mmとする。Through allではない。壁はスケッチ法線方向（垂直）。
3) 一定半径R=3 mmのフィレットを上面外周の4辺だけに適用する。ポケット内側のエッジには絶対にフィレットしない。
4) 追加フィーチャなし。最終も単一ソリッドボディ。
寸法・体積・表面積・面数はFreeCAD上で実際に読めた値だけ記録する。読めなければnull。理論値を実測として書かない。実在しないマクロは作ったことにしない。
返答はbuild(doc)を定義する完全なUTF-8 Pythonソースだけ。Markdownの説明や実行コマンドは返さない。
利用モジュールはFreeCAD、Part、Sketcher、math。必要な補助関数は定義してよい。
build(doc)は渡された文書に形状を作り、PartDesignのBodyを返す。作成中のrecomputeは使ってよい。
新規文書作成・Probe・保存・close・プロセス回収・CAD実行はdriver/cad_runが担当する。
シェル、調査、FreeCADの直接起動、ファイルやネットワーク操作を行わない。秘密や個人パスを書かない。
fixture、evidence、既存reports、他runの解答を参照・コピーしない。
"""


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean(value):
    if isinstance(value, str):
        return "".join(cad_run.scrub(line) for line in value.splitlines(keepends=True))
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean(item) for item in value]
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
            or type(result.get("cad_exit_code")) is not int or result["cad_exit_code"] != 0):
        return "cad_not_settled"
    if result.get("failed_phase") == "build" and not (
            result.get("predicate_diff") or result.get("measurements")):
        return "diagnostic_insufficient"
    return None


def run_driver(name, codex, root=ROOT, runner=None):
    runner = runner or subprocess.run
    started, clock = utc(), time.monotonic()
    out = new_run_dir(root, name)
    settings = {"model": MODEL, "effort": EFFORT, "disabled": list(DISABLED),
                "sandbox": "read-only", "skip_git_repo_check": True,
                "recipe": "freecadcmd", "timeout_s": 300}
    report = {"schema": "cad-harness.cad_agent.v0", "condition": "B2",
              "task_id": cad_run.TASK, "run_id": name, "started_at": started,
              "ended_at": None, "wall_ms": None, "status": "failed", "message_code": None,
              "attempts": [], "final_out_dir": None, "final_exit": None,
              "failed_phase": None, "probe_status": None, "geometry_ok": None}
    stream = (out / "events.jsonl").open("x", encoding="utf-8")
    sequence, previous, version = 0, None, None
    identity = agents_identity(root)

    def emit(event, number, status, data=None):
        nonlocal sequence
        sequence += 1
        row = {"schema": "cad-harness.cad_agent.event.v0", "run_id": name,
               "event_seq": sequence, "ts": utc(), "event": event,
               "attempt": number, "status": status, "data": clean(data or {})}
        stream.write(json.dumps(row, allow_nan=False) + "\n")
        stream.flush()

    try:
        for number in range(1, MAX_ATTEMPTS + 1):
            work, last = out / ("work-a%d" % number), out / ("last-a%d.txt" % number)
            work.mkdir()
            if number == 1:
                try:
                    info = runner([codex, "--version"], cwd=str(work), capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", shell=False, stdin=subprocess.DEVNULL)
                    if info.returncode == 0:
                        version = clean(info.stdout.strip()) or None
                except (OSError, subprocess.SubprocessError):
                    pass  # Version identification may be unavailable; record null.
            if any(work.iterdir()):
                raise ValueError("exec_work_not_empty")
            prompt = PROMPT
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
                generated = runner(exec_argv(codex, work, last, prompt), cwd=str(work),
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", shell=False, stdin=subprocess.DEVNULL)
                attempt["exec_exit"] = generated.returncode
                attempt["session_id"], attempt["usage"] = exec_metadata(generated.stdout)
                if last.is_file():
                    final = last.read_text(encoding="utf-8-sig")
                    last.write_text(clean(final), encoding="utf-8")
                else:
                    final = ""
                if generated.returncode != 0:
                    raise ValueError("exec_nonzero")
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
                                               "--timeout-s", "300", "--recipe", "freecadcmd"])
            cad_run.preflight(args, root)  # Also confirms fresh nested output is accepted.
            attempt["cad_run_started_at"] = utc()
            tick = time.monotonic()
            try:
                completed = runner([sys.executable, "-B", str(root / "tools" / "cad_run.py"),
                                    "--script", str(script), "--out-dir", str(cad_out),
                                    "--timeout-s", "300", "--recipe", "freecadcmd",
                                    "--task", cad_run.TASK], cwd=str(root), capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", shell=False, stdin=subprocess.DEVNULL)
                attempt["cad_run_exit"] = completed.returncode
                report.update(final_out_dir=attempt["out_dir"], final_exit=completed.returncode)
            finally:
                attempt.update(cad_run_ended_at=utc(), cad_run_wall_ms=(time.monotonic() - tick) * 1000)
                emit("cad_run_finished", number, "ok" if attempt["cad_run_exit"] == 0 else "failed",
                     {"exit": attempt["cad_run_exit"], "out_dir": attempt["out_dir"]})
            result = loads(completed.stdout)
            if (not isinstance(result, dict) or result.get("schema") != "cad-harness.cad_run.v0"
                    or result.get("task_id") != cad_run.TASK
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
        report.update(message_code=clean(str(exc)) or type(exc).__name__)
    finally:
        report.update(ended_at=utc(), wall_ms=(time.monotonic() - clock) * 1000)
        emit("run_finished", None, report["status"], {"message_code": report["message_code"]})
        stream.close()
        (out / "driver-run.json").write_text(json.dumps(report, allow_nan=False), encoding="utf-8")
    return report, 0 if report["status"] == "ok" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="New run ID (letters, digits, hyphen, underscore)")
    parser.add_argument("--codex", default="codex.exe" if os.name == "nt" else "codex",
                        help="Native Codex CLI executable; inherits CODEX_HOME")
    args = parser.parse_args(argv)
    if Path(args.codex).suffix.lower() in (".cmd", ".bat", ".ps1"):
        parser.error("use the native Codex executable")
    try:
        report, code = run_driver(args.run, args.codex)
    except (OSError, ValueError) as exc:
        report, code = {"schema": "cad-harness.cad_agent.v0", "status": "input_error",
                        "message_code": clean(str(exc)), "geometry_ok": None}, 2
    print(json.dumps(report, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
