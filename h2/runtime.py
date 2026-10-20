"""Subprocess boundaries for Codex and the unchanged CAD runner."""
import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

TOKEN_KEYS = ("input", "cached_input", "uncached_input", "output", "reasoning", "total")


def elapsed(start):
    return round((time.perf_counter() - start) * 1000, 3)


def token_usage(usage):
    usage = usage if isinstance(usage, dict) else {}
    result = {}
    for key in TOKEN_KEYS:
        value = usage.get(key + "_tokens", usage.get(key))
        if key == "cached_input" and value is None:
            value = usage.get("input_tokens_details", {}).get("cached_tokens")
        if key == "reasoning" and value is None:
            value = usage.get("reasoning_output_tokens")
            if value is None:
                value = usage.get("output_tokens_details", {}).get("reasoning_tokens")
        result[key] = value if type(value) is int and value >= 0 else None
    result["uncached_input"] = (result["input"] - result["cached_input"]
                                if result["input"] is not None and result["cached_input"] is not None
                                and result["cached_input"] <= result["input"] else None)
    if result["total"] is None and result["input"] is not None and result["output"] is not None:
        # Cached input and reasoning are subsets, not additional tokens.
        result["total"] = result["input"] + result["output"]
    return result


def sum_tokens(calls):
    return {key: (sum(c["tokens"][key] for c in calls)
                  if all(c["tokens"][key] is not None for c in calls) else None)
            for key in TOKEN_KEYS}


def parse_events(stdout):
    final, usage, completed = None, None, False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                final = item.get("text")
        if event.get("type") == "turn.completed":
            usage, completed = event.get("usage"), True
    if not completed or not isinstance(final, str):
        raise ValueError("Codex did not return a completed turn with an agent message")
    return final, token_usage(usage)


def reported_model(stdout, explicit_model=None):
    """Distinguish runtime model evidence from an explicitly selected CLI model."""
    models = set()
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") not in (
                "thread.started", "turn.started", "turn.completed", "response.created", "response.completed"):
            continue
        metadata = [event]
        if isinstance(event.get("response"), dict):
            metadata.append(event["response"])
        for item in metadata:
            value = item.get("model", item.get("model_id"))
            if isinstance(value, str) and value.strip():
                models.add(value)
    if len(models) == 1:
        return {"model": models.pop(), "model_source": "runtime_events", "model_reason": None}
    if not models and explicit_model:
        return {"model": explicit_model, "model_source": "explicit_cli_argument",
                "model_reason": "runtime_model_not_reported; explicit -m selection recorded"}
    return {"model": None, "model_source": None,
            "model_reason": "conflicting_runtime_models" if models else "model_not_reported_in_runtime_events"}


def extract_code(text):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if len(blocks) != 1:
        raise ValueError("Expected exactly one Python block")
    code = blocks[0].strip() + "\n"
    tree = ast.parse(code)
    if not any(isinstance(node, ast.FunctionDef) and node.name == "build" for node in tree.body):
        raise ValueError("Python block must define build(doc)")
    return code


def extract_json(text):
    blocks = re.findall(r"```(?:json)?\s*\n(.*?)```", text, re.S)
    return json.loads(blocks[0] if len(blocks) == 1 else text)


class CodexClient:
    def __init__(self, executable=None):
        self.executable = executable or shutil.which("codex.exe") or shutil.which("codex") or "codex"

    def __call__(self, prompt, *, effort, model, log_dir):
        log_dir.mkdir(parents=True)
        work = log_dir / "empty-workdir"
        work.mkdir()
        (log_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        command = [self.executable, "exec", "--json", "--sandbox", "read-only",
                   "--skip-git-repo-check", "--ephemeral", "-C", str(work),
                   "-c", 'approval_policy="never"', "-c", f'model_reasoning_effort="{effort}"']
        if model:
            command += ["-m", model]
        command.append("-")
        (log_dir / "command.json").write_text(json.dumps(command), encoding="utf-8")
        start = time.perf_counter()
        process = subprocess.run(command, input=prompt, text=True, encoding="utf-8",
                                 errors="replace", capture_output=True, timeout=900)
        (log_dir / "events.jsonl").write_text(process.stdout, encoding="utf-8")
        (log_dir / "stderr.txt").write_text(process.stderr, encoding="utf-8")
        wall_ms = elapsed(start)
        # Parse even on failure when possible so measured usage is preserved.
        try:
            final, tokens = parse_events(process.stdout)
            error = None
        except ValueError as exc:
            final, tokens, error = "", token_usage(None), str(exc)
        if process.returncode:
            error = f"codex exit={process.returncode}: {error or 'failed'}"
        return {"text": final, "tokens": tokens, "wall_ms": wall_ms,
                "exit_code": process.returncode, "error": error, **reported_model(process.stdout, model)}


class CadRunner:
    def __init__(self, root):
        self.root = Path(root)

    def __call__(self, script, out_dir, task):
        command = [sys.executable, str(self.root / "tools" / "cad_run.py"),
                   "--script", str(script), "--out-dir", str(out_dir),
                   "--timeout-s", "300", "--recipe", "freecadcmd", "--task", task]
        start = time.perf_counter()
        process = subprocess.run(command, cwd=self.root, text=True, encoding="utf-8",
                                 errors="replace", capture_output=True, timeout=360)
        # cad_run's contract is one result JSON on stdout.
        try:
            result = json.loads(process.stdout)
            if not isinstance(result, dict) or "probe_status" not in result:
                raise ValueError("Missing CAD result fields")
        except (ValueError, TypeError):
            result = {"status": "failed", "probe_status": None, "next_actor": "human",
                      "message_code": "unreadable_cad_result"}
        return {"result": result, "wall_ms": elapsed(start), "exit_code": process.returncode,
                "stdout": process.stdout, "stderr": process.stderr}
