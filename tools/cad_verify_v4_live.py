"""Manifest-authorized v4 transport. Importing this module launches nothing."""
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

if __package__:
    from . import cad_agent, cad_verify_v4_agent as agent, cad_verify_v4_ledger as ledger
    from . import cad_verify_v4_freeze as freezing, eval_verify_v3 as v3
    from . import cad_verify_v3_agent, eval_verify, cad_run
    from .cad_verify_guard import Stop, quota_snapshot
    from .cad_verify_v3_guard import Fault, q_score
else:
    import cad_agent, cad_verify_v4_agent as agent, cad_verify_v4_ledger as ledger
    import cad_verify_v4_freeze as freezing, eval_verify_v3 as v3
    import cad_verify_v3_agent, eval_verify, cad_run
    from cad_verify_guard import Stop, quota_snapshot
    from cad_verify_v3_guard import Fault, q_score

ROOT = Path(__file__).resolve().parents[1]
# A per-invocation overlay, never a mutation of the operator's configuration.
OMP_CONFIG = {
    "autoResume": False, "externalThinking": False,
    "retry": {"enabled": False, "maxRetries": 0, "modelFallback": False,
              "usageAwareFallback": False, "waitForUsageReset": False},
    "compaction": {"enabled": False, "asyncEnabled": False, "autoContinue": False},
    "advisor": {"enabled": False}, "recap": {"enabled": False},
    "composer": {"predictions": False}, "memories": {"enabled": False},
    "autolearn": {"enabled": False, "autoContinue": False}, "branchSummary": {"enabled": False},
    "magicKeywords": {"enabled": False}, "mcp": {"enableProjectConfig": False},
    "model": {"loopGuard": {"enabled": False}, "toolCallLoopGuard": {"enabled": False}},
    "startup": {"checkUpdate": False}, "git": {"enabled": False},
    "snapcompact": {"systemPrompt": "none"},
}


class WallClock:
    def __call__(self):
        return time.monotonic()

    def utc(self):
        return ledger.utc()


class LiveGuard:
    """No suite deadline. Slots are reserved before invocation, never after it."""
    def __init__(self, manifest, check_identity, *, clock=None, journal=None):
        authorization = manifest.get("authorization")
        if not isinstance(authorization, dict) or authorization.get("charged_calls") != 163:
            raise Stop("live_manifest_authorization_required")
        self.manifest, self.check_identity = manifest, check_identity
        self.clock = clock or WallClock()
        self.journal, self.deadline = journal, None
        self.calls, self.call_budget = 0, 163
        self.episode_start, self.episode_cap = 0, 0
        self.stop_reason = None

    def remaining(self, reserve=30):
        return math.inf

    def check(self):
        try:
            self.check_identity()
            snapshot = quota_snapshot(self.manifest["quota_snapshot"],
                                      datetime.fromisoformat(self.clock.utc()))
            if self.journal:
                self.journal.append("quota_checked", **snapshot)
            if snapshot["decision"] != "allow":
                raise Stop(snapshot["decision"])
            return snapshot
        except (OSError, ValueError, KeyError) as exc:
            self.stop_reason = str(exc)
            raise

    def before_run(self, minimum_calls=0):
        self.check()
        if self.calls + minimum_calls > self.call_budget:
            self.stop_reason = "insufficient_call_budget"
            raise Stop(self.stop_reason)

    def before_episode(self, maximum):
        self.before_run(maximum)
        self.episode_start, self.episode_cap = self.calls, maximum

    def before_call(self):
        self.before_run(1)
        if self.calls-self.episode_start >= self.episode_cap:
            self.stop_reason = "episode_call_limit"
            raise Stop(self.stop_reason)
        self.calls += 1
        return self.check()


def stream_process(argv, captures, *, cwd, timeout):
    """Drain both raw pipes to disk; a timeout/cancellation kills owned children."""
    errors = []
    with subprocess.Popen(argv, cwd=str(cwd), stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False) as process:
        def drain(key):
            try:
                with getattr(process, key) as pipe:
                    for raw in iter(lambda: pipe.read(8192), b""):
                        captures[key].feed(raw)
            except BaseException as exc:
                errors.append(exc)
                process.kill()
        threads = [threading.Thread(target=drain, args=(key,), daemon=True)
                   for key in ("stdout", "stderr")]
        for thread in threads:
            thread.start()
        try:
            process.wait(timeout=timeout)
        except BaseException:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=30, check=False)
            process.kill()
            process.wait(timeout=30)
            raise
        finally:
            for thread in threads:
                thread.join(timeout=30)
            if any(thread.is_alive() for thread in threads):
                raise OSError("capture_drain_did_not_finish")
        if errors:
            raise OSError("capture_stream_failed") from errors[0]
        return process.returncode


def trusted_worker_argv(job_path, *, root=ROOT):
    """An isolated trusted program, not source supplied by a generator."""
    root, job_path = Path(root).absolute(), Path(job_path).absolute()
    worker = root / "tools/cad_verify_v4_worker.py"
    if worker.is_symlink() or not worker.is_file() or not job_path.is_file():
        raise Stop("trusted_worker_binding_missing")
    native_bin = Path(cad_run.FREECAD_DIR) / "bin"
    bootstrap = ("import runpy,sys;sys.path[:0]="
                 + repr([str(root), str(native_bin)])
                 + ";runpy.run_module('tools.cad_verify_v4_worker',run_name='__main__')")
    return [str(native_bin / "python.exe"), "-I", "-B", "-c", bootstrap, "--job", str(job_path)]


def stream_native_process(argv, captures, *, cwd, timeout):
    """Reuse owned-handle cleanup and PID-only window inspection for native work."""
    if "--job" not in argv:
        raise Stop("trusted_worker_job_required")
    job_path = Path(argv[argv.index("--job")+1])
    if list(argv) != trusted_worker_argv(job_path, root=cwd):
        raise Stop("untrusted_native_invocation")
    job = ledger.read_json(job_path)
    out = Path(job["out"])
    ready_path = out.parent / (out.name + ".ready.json")
    if ready_path.exists():
        raise Stop("native_ready_evidence_exists")
    process = subprocess.Popen(argv, cwd=str(cwd), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    errors, threads = [], []
    evidence = dict(owned_pid=process.pid, stdin="DEVNULL", ready=None,
                    window_scan=None, cleanup_status="not_started")
    for capture in captures.values():
        capture.native_evidence = evidence
    def drain(key):
        try:
            with getattr(process, key) as pipe:
                for raw in iter(lambda: pipe.read(8192), b""):
                    captures[key].feed(raw)
        except BaseException as exc:
            errors.append(exc)
    for key in ("stdout", "stderr"):
        thread = threading.Thread(target=drain, args=(key,), daemon=True)
        thread.start()
        threads.append(thread)
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None:
            if ready_path.exists() and evidence["ready"] is None:
                ready = ledger.read_json(ready_path)
                evidence["ready"] = ready
                if (ready.get("owned_pid") != process.pid or ready.get("gui_up") != 0
                        or list(ready.get("freecad_version", []))[:3] != ["1", "1", "4"]):
                    raise Stop("native_runtime_identity_mismatch")
            scan = cad_run.window_scan(process.pid)
            evidence["window_scan"] = scan
            if scan["state"] != "no_windows":
                raise Stop("native_window_or_scan_failure:" + scan["state"])
            if errors:
                raise OSError("native_capture_stream_failed")
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(argv, timeout)
            try:
                process.wait(timeout=min(0.05, max(0.001, deadline-time.monotonic())))
            except subprocess.TimeoutExpired:
                pass
        if evidence["ready"] is None and ready_path.exists():
            evidence["ready"] = ledger.read_json(ready_path)
        ready = evidence["ready"]
        if (not isinstance(ready, dict) or ready.get("owned_pid") != process.pid
                or ready.get("gui_up") != 0
                or list(ready.get("freecad_version", []))[:3] != ["1", "1", "4"]):
            raise Stop("native_ready_evidence_missing_or_invalid")
        evidence["cleanup_status"] = "exited"
        return process.returncode
    except BaseException:
        ready = evidence.get("ready") or {}
        evidence.update(cad_run.cleanup(process, ready.get("gui_up"), scan=cad_run.window_scan,
                                       blocked=(evidence.get("window_scan") or {}).get("state") not in (None, "no_windows")))
        raise
    finally:
        for thread in threads:
            thread.join(timeout=30 if process.poll() is not None else 0.1)
        if process.poll() is not None:
            if any(thread.is_alive() for thread in threads):
                raise OSError("native_capture_drain_incomplete")
            if errors:
                raise OSError("native_capture_stream_failed") from errors[0]


def omp_result(path):
    """Decode documented print JSON messages, not prose-matched error strings."""
    parser = cad_verify_v3_agent.StreamCapture(parse=True)
    finals, usages, error_codes, identity = [], [], set(), set()
    output, complete, failed = False, True, False
    assistant_ends = 0

    def inspect(value):
        nonlocal output, complete
        if isinstance(value, dict):
            code = value.get("codex_error_info")
            if isinstance(code, str):
                error_codes.add(code)
            if value.get("type") in ("text_delta", "text_start", "text_end") and (
                    value.get("delta") or value.get("text")):
                output = True
            if value.get("role") == "assistant":
                content = value.get("content", [])
                if not isinstance(content, list):
                    complete = False
                    content = []
                for block in content:
                    if not isinstance(block, dict):
                        complete = False
                    elif block.get("type") in ("text", "output_text") and block.get("text"):
                        output = True
            for child in value.values():
                if isinstance(child, (dict, list)):
                    inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    with Path(path).open("rb") as file:
        index = 0
        while True:
            raw = file.readline(1048577)
            if not raw:
                break
            if len(raw) > 1048576:
                complete = False
                while raw and not raw.endswith(b"\n"):
                    raw = file.readline(1048577)
                continue
            try:
                text = raw.decode("utf-8")
                event = cad_agent.loads(text)
            except (UnicodeError, ValueError):
                complete = False
                continue
            if not isinstance(event, dict):
                complete = False
                continue
            parser.event(text)
            inspect(event)
            message = event.get("message")
            if event.get("type") == "message_end" and isinstance(message, dict) and message.get("role") == "assistant":
                assistant_ends += 1
                content = message.get("content", [])
                if not isinstance(content, list) or any(
                        not isinstance(b, dict) or b.get("type") in ("text", "output_text")
                        and not isinstance(b.get("text"), str) for b in content):
                    complete, failed = False, True
                else:
                    finals.append("".join(b["text"] for b in content if b.get("type") in ("text", "output_text")))
                failed |= message.get("stopReason") in ("error", "aborted")
                if isinstance(message.get("provider"), str) and isinstance(message.get("model"), str):
                    identity.add(message["provider"]+"/"+message["model"])
                usage = message.get("usage")
                if isinstance(usage, dict):
                    names = {"input_tokens": "input", "cached_input_tokens": "cacheRead",
                             "cache_write_input_tokens": "cacheWrite", "output_tokens": "output",
                             "reasoning_output_tokens": "reasoning"}
                    usages.append(dict(event_id=index, session_id=event.get("sessionId"), mode="delta",
                                       values={k: usage.get(k, usage.get(alias)) for k, alias in names.items()}))
            index += 1
    summary = parser.summary()
    output |= summary["assistant_output"]
    error_codes.update(summary["error_infos"])
    summary.update(assistant_output=output, error_infos=sorted(error_codes), parse_complete=complete,
                   provider_rejected=bool(complete and error_codes == {"server_overloaded"} and not output))
    return dict(final="".join(finals) if finals and not failed and complete else None,
                usage=ledger.usage_totals(usages), summary=summary, models=sorted(identity),
                assistant_ends=assistant_ends)


class LiveSkillAdapter(agent.SkillAdapter):
    def exec_argv(self, codex, work, last, prompt, context=None):
        # This is the driver's typed internal envelope, not a launched Codex CLI.
        if prompt != self.request:
            if not prompt.startswith(self.request+"\n"):
                raise ValueError("request_bytes_changed")
            data = cad_agent.loads(context.split(agent.MARKER, 1)[1]) if agent.MARKER in context else {}
            data["answer"] = prompt[len(self.request)+1:]
            context = self.context(data)
        return [codex, "exec", "-o", str(last),
                "developer_instructions="+json.dumps(context, ensure_ascii=False), self.request]


class LiveTransport:
    def __init__(self, manifest, journal, out, request, skill, guard, *, root=ROOT,
                 wall=None, process=stream_process, sleep=time.sleep, prompt_files=()):
        self.manifest, self.journal, self.out = manifest, journal, Path(out)
        self.request, self.skill, self.guard, self.root = request, skill, guard, Path(root)
        self.wall, self.process, self.sleep = wall or WallClock(), process, sleep
        self.evidence_mode = "live" if process is stream_process else "unit_mock"
        self.clock = agent.ActiveClock(self.wall)
        self.sequence, self.logical_call = 0, 0
        self.episode, self.route, self.scored = None, None, False
        self.driver_reserves = True
        self.fatal = None
        self.last_attempt = None
        self.recoveries = 0
        self.retry_parent = None
        self.prompt_files = tuple(Path(path) for path in prompt_files)

    def wait_provider(self, row, budget=None, guard=None, logical_deadline=None, sleeper=None):
        tick = self.wall()
        self.journal.append("wait_started", episode_id=self.episode, attempt_id=self.last_attempt, requested_s=600)
        try:
            while self.wall()-tick < 600:
                before = self.wall()
                try:
                    self.guard.check()
                    self.sleep(min(60, max(0, 600-(self.wall()-tick))))
                finally:
                    self.clock.exclude(self.wall()-before)
        finally:
            actual = self.wall()-tick
            self.journal.append("wait_finished", episode_id=self.episode, attempt_id=self.last_attempt,
                                requested_s=600, actual_s=actual, completed=actual >= 600)
            if row is not None:
                row.update(wait_requested_s=600, backoff_s=actual)

    def __call__(self, argv, **kwargs):
        if len(argv) > 1 and argv[1] == "--version":
            return subprocess.CompletedProcess(argv, 0, self.manifest["generator"]["version"], "")
        model = len(argv) > 1 and argv[1] == "exec"
        folder = self.out / ("logical-%04d" % (self.logical_call+1)) if model else None
        final_path, data = None, {}
        if model:
            if not self.driver_reserves:
                self.guard.before_call()
            self.logical_call += 1
            folder.mkdir()
            context = json.loads(next(a.split("=", 1)[1] for a in argv if a.startswith("developer_instructions=")))
            if agent.MARKER in context:
                data = cad_agent.loads(context.split(agent.MARKER, 1)[1])
            final_path = Path(argv[argv.index("-o")+1])
            payload = folder/"payload.json"
            ledger.write_json(payload, dict(request=self.request, runtime_data=data))
            configuration = folder/"config.json"
            ledger.write_json(configuration, OMP_CONFIG)
            actual = [self.manifest["generator"]["omp"], "--print", "--mode", "json",
                      "--model", self.manifest["generator"]["model"],
                      "--thinking", self.manifest["generator"]["thinking"],
                      "--no-tools", "--no-lsp", "--no-pty", "--no-extensions", "--no-skills",
                      "--no-rules", "--no-title", "--no-session", "--no-prewalk",
                      "--config", str(configuration), "--system-prompt", self.skill.decode("utf-8"), "@"+str(payload)]
            actual.extend("@"+str(path) for path in self.prompt_files)
            cwd = Path(kwargs["cwd"])
            content_hashes = {str(p): ledger.file_sha(p) for p in (payload, configuration, *self.prompt_files)}
        else:
            actual = list(argv)
            if "--script" not in actual or "--out-dir" not in actual:
                raise Stop("invalid_cad_command")
            cwd = Path(kwargs.get("cwd", self.root))
            script = actual[actual.index("--script")+1]
            content_hashes = {script: ledger.file_sha(script)}
            # The isolated checker root contains byte-identical frozen tooling.
            checker_root = Path(actual[2]).resolve().parents[1]
            for name, digest in self.manifest["files"].items():
                if name.startswith("tools/") and name.endswith(".py"):
                    content_hashes[str(checker_root/name)] = digest
        timeout = kwargs.get("timeout", 450)
        active_deadline = self.clock()+timeout
        while True:
            self.guard.check()
            if any(ledger.file_sha(p) != digest for p, digest in content_hashes.items()):
                self.fatal = "submitted_payload_changed"
                raise Stop(self.fatal)
            self.sequence += 1
            attempt_id = "attempt-%04d" % self.sequence
            self.last_attempt = attempt_id
            capture_dir = self.out/attempt_id
            capture_dir.mkdir()
            submitted = dict(argv=actual, cwd=str(cwd), stdin="DEVNULL", files=content_hashes,
                             request_sha256=ledger.sha(self.request.encode("utf-8")),
                             skill_sha256=ledger.sha(self.skill), model=self.manifest["generator"]["model"] if model else None,
                             environment={"OMP_PROFILE": os.environ.get("OMP_PROFILE")})
            ledger.write_json(capture_dir/"submitted.json", submitted)
            base = dict(episode_id=self.episode, attempt_id=attempt_id, operation="model" if model else "cad",
                        route=self.route, stage=data.get("stage", "initial"), retained_segment=self.scored,
                        logical_call_id=self.logical_call if model else None, retry_parent_id=self.retry_parent,
                        evidence_mode=self.evidence_mode, manifest_sha256=self.manifest.get("manifest_sha256"))
            self.journal.append("attempt_started", **base, submitted_sha256=ledger.file_sha(capture_dir/"submitted.json"))
            captures = {key: ledger.StreamCapture(capture_dir/(key+".bin"), parse=key == "stdout")
                        for key in ("stdout", "stderr")}
            tick, failure, code, artifacts = self.wall(), None, None, {}
            try:
                code = self.process(actual, captures, cwd=cwd, timeout=max(0.001, active_deadline-self.clock()))
            except BaseException as exc:
                failure = exc
                self.fatal = "transport_or_capture_interrupted"
            finally:
                for key, capture in captures.items():
                    artifacts[key] = capture.finish()
                    if failure:
                        artifacts[key].update(complete=False, missing_reason="transport_or_capture_interrupted")
            result = omp_result(artifacts["stdout"]["path"]) if model else None
            if model:
                result["summary"]["full_sha256"] = artifacts["stdout"]["sha256"]
            exempt = bool(model and not failure and result["summary"]["provider_rejected"])
            elapsed = self.wall()-tick
            if exempt:
                self.clock.exclude(elapsed)
            usage = result["usage"] if model and not failure else ledger.unknown_usage("transport_or_capture_incomplete") if model else None
            self.journal.append("attempt_finished", **base, wall_s=elapsed, active_s=0 if exempt else elapsed,
                                charged=not exempt if model else None, provider_rejected=exempt,
                                usage=usage, price=ledger.price(usage) if usage else None, streams=artifacts,
                                provider_summary=result["summary"] if model else None, exit_code=code,
                                provider_billing_status=None, billing_missing_reason="invoice_not_provided",
                                error=type(failure).__name__ if failure else None)
            if failure:
                raise OSError(self.fatal) from failure
            if exempt:
                self.retry_parent = attempt_id
                try:
                    self.wait_provider({})
                except BaseException:
                    # Only rejected attempts occurred for this reserved slot.
                    self.guard.calls -= 1
                    raise
                continue
            if model:
                if self.retry_parent and code == 0 and result["final"] is not None:
                    self.recoveries += 1
                self.retry_parent = None
                if result["models"] and result["models"] != [self.manifest["generator"]["model"]]:
                    self.fatal = "generator_identity_changed"
                    raise OSError(self.fatal)
                if result["assistant_ends"] > 1:
                    self.fatal = "unexpected_hidden_model_retry"
                    raise OSError(self.fatal)
                if result["final"] is not None:
                    final_path.write_bytes(result["final"].encode("utf-8"))
                completed = subprocess.CompletedProcess(actual, code,
                    captures["stdout"].tail.decode("utf-8", errors="replace"),
                    captures["stderr"].tail.decode("utf-8", errors="replace"))
                completed.provider_summary = result["summary"]
                completed.exec_metadata = (None, [dict(event_index=0, values=usage["values"])])
            else:
                # Only the structured CAD report is needed by the existing driver.
                with Path(artifacts["stdout"]["path"]).open(encoding="utf-8") as file:
                    report = json.load(file)
                completed = subprocess.CompletedProcess(actual, code, json.dumps(report),
                    captures["stderr"].tail.decode("utf-8", errors="replace"))
            completed.transport_capture = {key: dict(tail=captures[key].tail, full_sha256=value["sha256"], full_bytes=value["bytes"])
                                           for key, value in artifacts.items()}
            return completed


def safe_input(base, name):
    if not isinstance(name, str) or Path(name).is_absolute() or ".." in Path(name).parts:
        raise Stop("holdout_path_escape")
    path = Path(base)/name
    if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()) for p in (path, *path.parents)):
        raise Stop("holdout_linked_input")
    path = path.resolve()
    if not path.is_relative_to(Path(base).resolve()) or not path.is_file():
        raise Stop("holdout_input_missing_or_escape")
    return path


def load_cohort(path, manifest):
    path = Path(path).resolve()
    commitment = ledger.read_json(manifest["commitment"]["path"])
    if commitment.get("schema") != "cad-harness.holdout-commitment.v4" or commitment.get("cohort_sha256") != ledger.file_sha(path):
        raise Stop("holdout_commitment_mismatch")
    cohort = ledger.read_json(path)
    if cohort.get("schema") != "cad-harness.holdout.v4" or not isinstance(cohort.get("files"), dict) or not cohort["files"]:
        raise Stop("holdout_schema")
    for name, digest in cohort["files"].items():
        if ledger.file_sha(safe_input(path.parent, name)) != digest:
            raise Stop("holdout_file_hash_mismatch")
    entries = cohort.get("entries", [])
    expected = v3.expected_order()
    actual = [(e["group"], e["case"], e["round"], e["route"], e["min_calls"], e["max_calls"]) for e in entries]
    if actual != expected or [e.get("sequence") for e in entries] != list(range(1, 61)) or len({e["id"] for e in entries}) != 60:
        raise Stop("holdout_frozen_order_or_strata")
    v3.validate_order(dict(schema="cad-harness.verify-order.v3", profile="verify-v3",
                           entries=entries, planned_calls=83, max_calls=163,
                           core_count=51, completion_count=6))
    for entry in entries:
        for key in ("request", "acceptance"):
            if entry.get(key) not in cohort["files"]:
                raise Stop("holdout_unbound_entry")
        card = ledger.read_json(safe_input(path.parent, entry["acceptance"]))
        if card.get("schema") != "cad-harness.acceptance.v4" or card.get("request_sha256") != cohort["files"][entry["request"]] or card.get("route") != entry["route"]:
            raise Stop("holdout_acceptance_binding")
        for key in ("gold", "script", "fault"):
            if card.get(key) and card[key] not in cohort["files"]:
                raise Stop("holdout_unbound_checker_input")
        if entry["group"] == "fault":
            fault = ledger.read_json(safe_input(path.parent, card["fault"]))
            candidate = (Path(card["fault"]).parent/fault["candidate"]).as_posix()
            if candidate not in cohort["files"]:
                raise Stop("holdout_unbound_fault_candidate")
        if entry["route"] != "ask" and entry["route"] != "offline" and not card.get("gold"):
            raise Stop("holdout_gold_required")
    return cohort


def setup_episode(out, skill, root):
    for name, content in (("skills/freecad-modeling/SKILL.md", skill),
                          ("design/cad-harness-mvp/build-schema.json", (Path(root)/"design/cad-harness-mvp/build-schema.json").read_bytes())):
        target = Path(out)/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for source in sorted((Path(root)/"tools").rglob("*.py")):
        target = Path(out)/source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def execute_episode(entry, card, base, out, transport, *, root=ROOT):
    text = safe_input(base, entry["request"]).read_bytes().decode("utf-8")
    transport.episode, transport.route, transport.scored = entry["id"], entry["route"], entry["group"] not in ("dev", "completion")
    transport.request = text
    transport.guard.before_episode(entry["max_calls"])
    setup_episode(out, transport.skill, root)
    name = "request-mvp1"
    gold = safe_input(base, card["gold"]) if card.get("gold") else None
    if entry["route"] == "offline":
        target = Path(out)/"reports/cad-run/legacy-mvp1"
        argv = [sys.executable, "-B", str(Path(out)/"tools/cad_run.py"),
                "--script", str(safe_input(base, card["script"])), "--out-dir", str(target),
                "--timeout-s", "300", "--task", card["task"], "--recipe", "freecadcmd"]
        if gold:
            argv += ["--gold", str(gold), "--probe-profile", "mvp-v1", "--end-to-end-s", "450"]
        result = cad_agent.loads(transport(argv, cwd=str(out), timeout=450).stdout)
        expected = entry["case"].endswith("good")
        settled = result.get("document_closed") is True and result.get("cleanup_status") == "exited" and result.get("cad_exit_code") == 0
        if not settled or result.get("probe_status") == "exception":
            transport.fatal = "harness:legacy_runtime"
        return dict(status="ok" if settled and result.get("probe_pass") is expected else "failed",
                    message_code=transport.fatal, attempts=[dict(result=result)], calls=[], llm_calls=0,
                    parse_repairs=0, repair_calls=0), 0
    adapter = LiveSkillAdapter(transport.skill, text)
    if entry["route"] == "mvp":
        package = (__package__+".") if __package__ else ""
        spec = importlib.util.spec_from_file_location(package+"_verify_v4_mvp", cad_agent.__file__)
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        core.developer_context, core.exec_argv = adapter.developer_context, adapter.exec_argv
        transport.driver_reserves = False
        try:
            return core.run_mvp_driver(name, transport.manifest["generator"]["omp"], text, gold,
                                       root=Path(out), runner=transport, clock=transport.clock,
                                       evaluation=True, max_calls=entry["max_calls"])
        finally:
            transport.driver_reserves = True
    transport.driver_reserves = True
    core = agent.adapted_driver(adapter, transport)
    return core(name, transport.manifest["generator"]["omp"], text, gold, root=Path(out),
                runner=transport, clock=transport.clock, guard=transport.guard,
                route=entry["route"], max_calls=entry["max_calls"], rubric=card.get("rubric"),
                answer=card.get("answer"), preview=entry["group"] == "dev", provider_retry=True,
                fault=Fault(safe_input(base, card["fault"])) if card.get("fault") else None)


def score_episode(entry, report, name, *, wall_s, active_s):
    """The v3 success, route, clarification, fault and native-result predicates."""
    row = v3.empty_row(entry, name)
    attempts = report.get("attempts", [])
    initial = attempts[0]["result"] if attempts else {}
    final = attempts[-1]["result"] if attempts else {}
    first = report.get("first_response")
    source = report.get("unsupported_to_source") is True
    route = True if entry["route"] in ("mvp", "offline") else (
        source and all(a["result"].get("generator") == "agent" for a in attempts)
        if entry["route"] == "source" else
        not source and all(a["result"].get("generator") == "compiler" for a in attempts))
    passed = report.get("status") == "ok" and eval_verify.result_pass(final) and route and active_s < 900
    if entry["route"] == "offline":
        passed = report.get("status") == "ok"
    score, invention = None, False
    if entry["route"] == "ask" or entry["group"] == "completion":
        score, invention = q_score(first, False, entry["case"], report.get("_rubric"))
        if entry["route"] == "ask":
            passed = score == 1 and not invention and report.get("logical_calls", len(report.get("calls", []))) == 1 and not attempts and active_s < 450
        else:
            passed &= report.get("completion_reached") is True
    elif entry["case"] == "A4":
        score, invention = q_score(first, passed, entry["case"])
        passed &= score == 1
    if entry["group"] == "fault":
        passed &= all((report.get("fault") or {}).get(k) is True for k in
                      ("reached", "injected", "established", "detected")) and report.get("repair_calls") == 1
    if entry["group"] == "dev" and entry["route"] != "ask":
        passed = report.get("status") == "preview" and route and not attempts and active_s < 450
    episode_stop = report.get("message_code") in (
        "episode_stage_deadline_exceeded", "episode_deadline_exceeded",
        "repair_time_reservation_lost", "deadline_exceeded")
    row.update(completed=not episode_stop, passed=bool(passed and not episode_stop),
               wall_s=wall_s, active_s=active_s, route_ok=route,
               initial=eval_verify.gates(initial) if attempts else None,
               final=eval_verify.gates(final) if attempts else None,
               sol_calls=report.get("llm_calls", 0), cad_attempts=len(attempts),
               parse_repairs=report.get("parse_repairs", 0), repair_calls=report.get("repair_calls", 0),
               repair_eligible=report.get("repair_eligible", False),
               natural_repair_eligible=report.get("repair_eligible", False) and entry["group"] in ("geometry", "q", "completion"),
               repair_success=report.get("repair_calls") == 1 and report.get("status") == "ok" and eval_verify.result_pass(final),
               fault=report.get("fault"), unsupported_to_source=source, unsupported_origin=report.get("unsupported_origin"),
               critical_invention=invention, q_score=score,
               initial_q_score=score if entry["route"] == "ask" or entry["group"] == "completion" else None,
               initial_critical_invention=invention,
               completion_reached=report.get("completion_reached", False),
               post_answer_first_attempt_pass=entry["group"] == "completion" and eval_verify.result_pass(initial),
               episode_stop_reason=report.get("message_code") if episode_stop else None,
               failure_class=None if passed else report.get("message_code"))
    return row


def validate_report(entry, card, base, out, report):
    if entry["route"] == "offline":
        return
    gold = safe_input(base, card["gold"]) if card.get("gold") else None
    where = Path(out)/"reports/cad-run/request-mvp1"
    v3.check_attempts(Path(out), entry, report, where, gold)
    if report.get("status") == "ok" and (not report["attempts"] or not eval_verify.result_pass(report["attempts"][-1]["result"])):
        raise Stop("harness:false_pass")
    if entry["route"] == "ask" or entry["group"] == "completion" or entry["case"] == "A4":
        number = report.get("first_response_call", 1)
        artifact = where/("last-c%d.txt" % number)
        if artifact.is_file():
            observed = v3.first_response(artifact.read_text(encoding="utf-8"))
            if any(report.get("first_response", {}).get(k) != value for k, value in observed.items()):
                raise Stop("harness:first_response_binding")


def run_holdout(manifest_path, sealed_input, run_dir, *, root=ROOT, process=stream_process,
                wall=None, sleep=time.sleep):
    # No input, output directory or executable is touched before this authorization gate.
    manifest = freezing.verify(manifest_path, root=root)
    if not manifest.get("authorization"):
        raise Stop("live_manifest_authorization_required")
    manifest["manifest_sha256"] = ledger.file_sha(manifest_path)
    cohort = load_cohort(sealed_input, manifest)
    out = ledger.new_directory(run_dir)
    freezing.claim(manifest_path, out)
    ledger.write_json(out/"manifest.json", manifest)
    ledger.write_json(out/"cohort.json", cohort)
    wall = wall or WallClock()
    started = wall()
    rows, stop_reason = [], None
    skill = agent.bundle(root)
    with ledger.Journal(out/"ledger.jsonl", out.name, "holdout", clock=wall, now=wall.utc) as journal:
        guard = LiveGuard(manifest, lambda: freezing.verify(manifest_path, root=root), clock=wall, journal=journal)
        transport = LiveTransport(manifest, journal, out, "", skill, guard, root=root, wall=wall, process=process, sleep=sleep)
        active_started = transport.clock()
        journal.append("run_started", manifest_sha256=manifest["manifest_sha256"], cohort_sha256=ledger.file_sha(sealed_input), evidence_mode=transport.evidence_mode)
        try:
            for index, entry in enumerate(cohort["entries"]):
                # No score/model output is printed while the one fixed cohort runs.
                if stop_reason:
                    rows.append(v3.empty_row(entry, entry["id"], stop_reason))
                    continue
                tick, active_tick = wall(), transport.clock()
                journal.append("episode_started", episode_id=entry["id"], route=entry["route"])
                try:
                    guard.before_run(max(entry["max_calls"], sum(e["min_calls"] for e in cohort["entries"][index:])))
                    # Recheck the committed bytes before use, not just once at launch.
                    load_cohort(sealed_input, manifest)
                    card = ledger.read_json(safe_input(Path(sealed_input).parent, entry["acceptance"]))
                    episode_out = out/("episode-%03d" % entry["sequence"])
                    report, code = execute_episode(entry, card, Path(sealed_input).parent,
                                                   episode_out, transport, root=root)
                    validate_report(entry, card, Path(sealed_input).parent, episode_out, report)
                    report["_rubric"] = card.get("rubric")
                    row = score_episode(entry, report, entry["id"], wall_s=wall()-tick, active_s=transport.clock()-active_tick)
                    problem = v3.harness_failure(report)
                    stop_reason = transport.fatal or guard.stop_reason or (
                        None if row["episode_stop_reason"] else problem)
                    if stop_reason:
                        row.update(completed=False, passed=False, stop_reason=stop_reason)
                    rows.append(row)
                except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
                    stop_reason = str(exc)
                    rows.append(v3.empty_row(entry, entry["id"], stop_reason))
                journal.append("episode_finished", episode_id=entry["id"], wall_s=wall()-tick,
                               active_s=transport.clock()-active_tick, status="incomplete" if stop_reason else "completed")
        except KeyboardInterrupt:
            stop_reason = "operator_cancelled"
            for entry in cohort["entries"][len(rows):]:
                rows.append(v3.empty_row(entry, entry["id"], stop_reason))
        journal.append("run_finished", wall_s=wall()-started, active_s=transport.clock()-active_started,
                       wall_missing_reason=None, stop_reason=stop_reason)
    costs = ledger.summarize(out/"ledger.jsonl")
    for row in rows:
        episode_cost = costs["per_episode"].get(row["id"])
        if episode_cost:
            row["tokens"] = {k: value["total"] for k, value in episode_cost["tokens"].items()}
    summary = v3.summarize(rows, dict(entries=cohort["entries"]), stopped=stop_reason)
    result = dict(schema="cad-harness.holdout-results.v4", status="COMPLETE" if summary["complete"] and not stop_reason else "INCOMPLETE",
                  evidence_mode=transport.evidence_mode,
                  fresh_holdout="not_run" if transport.evidence_mode != "live" else "complete" if summary["complete"] and not stop_reason else "incomplete",
                  summary=summary, groups={g: [r for r in rows if r["group"] == g] for g in v3.GROUPS},
                  costs=costs, generator=manifest["generator"],
                  overload_robustness="VERIFIED" if transport.evidence_mode == "live" and transport.recoveries else "UNVERIFIED",
                  pilot="not_run", stop_reason=stop_reason)
    ledger.write_json(out/"summary.json", result)
    return result
