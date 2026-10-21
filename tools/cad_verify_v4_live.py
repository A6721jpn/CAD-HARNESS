"""Manifest-authorized v4 transport. Importing this module launches nothing."""
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
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
        prior = authorization.get("prior_counted_calls")
        if type(prior) is not int or not 0 <= prior <= 163:
            raise Stop("live_manifest_authorization_required")
        self.manifest, self.check_identity = manifest, check_identity
        self.clock = clock or WallClock()
        self.journal, self.deadline = journal, None
        self.calls, self.call_budget = prior, 163
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
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=30, check=False)
                process.kill()
                process.wait(timeout=30)
            except BaseException as exc:
                raise OSError("owned_process_cleanup_failed") from exc
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


class _ModelTimeout(subprocess.TimeoutExpired):
    """Keep typed evidence while excluding private argv from driver error codes."""
    def __str__(self):
        return "model_timeout"


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
        try:
            return self._invoke(argv, **kwargs)
        except subprocess.TimeoutExpired:
            raise
        except OSError:
            # Submission, parsing, journaling and storage failures are not model
            # timeouts merely because they happened while servicing a model call.
            self.fatal = self.fatal or "transport_or_capture_interrupted"
            raise

    def _invoke(self, argv, **kwargs):
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
                if not (model and isinstance(exc, subprocess.TimeoutExpired)):
                    self.fatal = "transport_or_capture_interrupted"
            finally:
                capture_errors = []
                for key, capture in captures.items():
                    try:
                        artifacts[key] = capture.finish()
                        if failure and self.fatal:
                            artifacts[key].update(complete=False, missing_reason="transport_or_capture_interrupted")
                    except BaseException as exc:
                        capture_errors.append(exc)
                if capture_errors:
                    self.fatal = "transport_or_capture_interrupted"
                    raise OSError("capture_finish_failed") from capture_errors[0]
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
            capture_metadata = {key: dict(tail=captures[key].tail, full_sha256=value["sha256"],
                                          full_bytes=value["bytes"])
                                for key, value in artifacts.items()}
            if model and (not failure or isinstance(failure, subprocess.TimeoutExpired)):
                if result["models"] and result["models"] != [self.manifest["generator"]["model"]]:
                    self.fatal = "generator_identity_changed"
                    raise OSError(self.fatal)
                if result["assistant_ends"] > 1:
                    self.fatal = "unexpected_hidden_model_retry"
                    raise OSError(self.fatal)
            if failure:
                if model and isinstance(failure, subprocess.TimeoutExpired) and not self.fatal:
                    timed_out = _ModelTimeout(failure.cmd, failure.timeout,
                        output=captures["stdout"].tail.decode("utf-8", errors="replace"),
                        stderr=captures["stderr"].tail.decode("utf-8", errors="replace"))
                    timed_out.transport_capture = capture_metadata
                    timed_out.provider_summary = result["summary"]
                    timed_out.exec_metadata = (None, [dict(event_index=0, values=usage["values"])])
                    raise timed_out from failure
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
            completed.transport_capture = capture_metadata
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
                          ("design/cad-harness-mvp/build-schema.json", (Path(root)/"design/cad-harness-mvp/build-schema.json").read_bytes()),
                          ("design/cad-harness-mvp/eval-v1/schema.json", (Path(root)/"design/cad-harness-mvp/eval-v1/schema.json").read_bytes()),
                          ("design/cad-harness-verify-v3/gold-schema.json", (Path(root)/"design/cad-harness-verify-v3/gold-schema.json").read_bytes())):
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


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _unlinked(path, *, directory=False):
    path = Path(path).absolute()
    if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
           for p in (path, *path.parents)):
        raise Stop("continuation_linked_input")
    if not (path.is_dir() if directory else path.is_file()):
        raise Stop("continuation_input_missing")
    return path.resolve()


def _bound_file(path, digest, evidence):
    path = _unlinked(path)
    if not _digest(digest) or ledger.file_sha(path) != digest:
        raise Stop("continuation_file_hash_mismatch")
    evidence[str(path)] = digest
    return path


def _prefix_destination(run_dir, *protected):
    destination = Path(run_dir).absolute()
    if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
           for p in (destination, *destination.parents)):
        raise Stop("continuation_linked_output")
    destination = destination.resolve()
    if any(destination.is_relative_to(Path(path).resolve()) for path in protected):
        raise Stop("continuation_output_inside_historical_input")


def _prior_rows(document, entries):
    if (not isinstance(document, dict)
            or document.get("schema") != "cad-harness.holdout-results.v4"
            or not isinstance(document.get("groups"), dict)):
        raise Stop("continuation_prior_summary_contract")
    flattened = [row for group in document["groups"].values() for row in group]
    if (len(flattened) != 60 or any(not isinstance(row, dict) for row in flattened)
            or len({row.get("id") for row in flattened}) != 60):
        raise Stop("continuation_prior_rows_contract")
    by_id = {row["id"]: row for row in flattened}
    ordered = []
    for entry in entries:
        row = by_id.get(entry["id"])
        if (row is None or _canonical(row.get("manifest_entry")) != _canonical(entry)
                or _canonical({key: row.get(key) for key in entry}) != _canonical(entry)):
            raise Stop("continuation_prior_row_order_binding")
        ordered.append(row)
    if len({row.get("run") for row in ordered}) != 60:
        raise Stop("continuation_prior_run_identity")
    return ordered


def _prior_costs(path, manifest, entries):
    authorization = manifest.get("authorization")
    if (not isinstance(authorization, dict)
            or type(authorization.get("charged_calls")) is not int
            or authorization["charged_calls"] != 163
            or type(authorization.get("prior_counted_calls")) is not int
            or not 0 <= authorization["prior_counted_calls"] <= 20
            or "continuation" in authorization):
        raise Stop("continuation_prior_authorization_contract")
    events = list(ledger.rows(path))
    starts, ends = {}, {}
    allowed = {entry["id"] for entry in entries[:18]}
    for event in events:
        kind = event["event"]
        if kind in ("episode_started", "episode_finished", "attempt_started", "attempt_finished"):
            if event.get("episode_id") not in allowed:
                raise Stop("continuation_prior_activity_after_prefix")
        if kind not in ("attempt_started", "attempt_finished"):
            continue
        target = starts if kind == "attempt_started" else ends
        key = event.get("attempt_id")
        if not isinstance(key, str) or not key or key in target:
            raise Stop("continuation_prior_attempt_identity")
        target[key] = event
    for key, end in ends.items():
        start = starts.get(key)
        if (start is None or any(start.get(k) != end.get(k)
                                 for k in ("episode_id", "operation"))
                or end.get("operation") not in ("model", "cad")):
            raise Stop("continuation_prior_attempt_binding")
        if end["operation"] == "model":
            charged = end.get("charged")
            if charged is not None and type(charged) is not bool:
                raise Stop("continuation_prior_charge_contract")
            if charged is False and end.get("provider_rejected") is not True:
                raise Stop("continuation_prior_charge_contract")
    if any(start.get("operation") not in ("model", "cad") for start in starts.values()):
        raise Stop("continuation_prior_attempt_binding")
    costs = ledger.summarize(path)
    prior = authorization["prior_counted_calls"] + costs["conservative_reserved_calls"]
    if prior != 20:
        raise Stop("continuation_prior_count_must_equal_20")
    return events, costs


def _saved_attempt(event, start, prior, request, manifest, evidence, *, timeout_attempt=None):
    submitted_path = safe_input(prior, event["attempt_id"]+"/submitted.json")
    _bound_file(submitted_path, start.get("submitted_sha256"), evidence)
    submitted = ledger.read_json(submitted_path)
    if (submitted.get("request_sha256") != ledger.sha(request)
            or submitted.get("skill_sha256") != manifest.get("skill_sha256")
            or not isinstance(submitted.get("files"), dict) or not submitted["files"]):
        raise Stop("continuation_saved_submission_binding")
    for name, digest in submitted["files"].items():
        path = Path(name)
        if not path.is_absolute() or ".." in path.parts or not path.absolute().is_relative_to(prior):
            raise Stop("continuation_saved_submission_escape")
        _bound_file(path, digest, evidence)
    streams = event.get("streams")
    if not isinstance(streams, dict) or set(streams) != {"stdout", "stderr"}:
        raise Stop("continuation_saved_stream_missing")
    historical_timeout = event["attempt_id"] == timeout_attempt
    for name, stream in streams.items():
        if not isinstance(stream, dict) or not isinstance(stream.get("path"), str):
            raise Stop("continuation_saved_stream_missing")
        path = Path(stream["path"])
        if (not path.is_absolute() or ".." in path.parts or not path.absolute().is_relative_to(prior)
                or path != prior/event["attempt_id"]/(name+".bin")):
            raise Stop("continuation_saved_stream_escape")
        if historical_timeout:
            if (stream.get("complete") is not False
                    or stream.get("missing_reason") != "transport_or_capture_interrupted"):
                raise Stop("continuation_saved_timeout_history")
        elif stream.get("complete") is not True:
            raise Stop("continuation_saved_stream_incomplete")
        path = _bound_file(path, stream.get("sha256"), evidence)
        if type(stream.get("bytes")) is not int or path.stat().st_size != stream["bytes"]:
            raise Stop("continuation_saved_stream_size")
    return submitted


def _saved_episode(entry, card, base, prior, manifest, events, evidence, *,
                   sequence=18, timeout_attempt=None, score_row=True):
    episode = _unlinked(prior/("episode-%03d" % sequence), directory=True)
    where = episode/"reports/cad-run/request-mvp1"
    driver_path = _unlinked(where/"driver-run.json")
    evidence[str(driver_path)] = ledger.file_sha(driver_path)
    report = ledger.read_json(driver_path)
    request = safe_input(base, entry["request"]).read_bytes()
    gold = safe_input(base, card["gold"])
    identity = {
        "schema": "cad-harness.cad_agent.verify3", "run_id": "request-mvp1",
        "mode": "description", "probe_profile": "verify-v3", "route": entry["route"],
        "preview": entry["group"] == "dev", "task_id": ledger.read_json(gold)["case_id"],
        "description_sha256": ledger.sha(request), "input_sha256": ledger.sha(request),
        "gold_sha256": ledger.file_sha(gold),
    }
    if any(report.get(key) != value for key, value in identity.items()):
        raise Stop("continuation_saved_driver_binding")
    for key, name in (("compiler_sha256", "tools/cad_spec.py"),
                      ("probe_sha256", "tools/cad_verify_v3_probe.py"),
                      ("shared_probe_sha256", "tools/cad_verify_probe.py")):
        if report.get(key) != manifest["files"].get(name):
            raise Stop("continuation_saved_source_binding")
    for name, digest in manifest["files"].items():
        if name.startswith("tools/") and name.endswith(".py"):
            _bound_file(safe_input(episode, name), digest, evidence)
    for key, name in (("skill_sha256", "skills/freecad-modeling/SKILL.md"),
                      ("schema_sha256", "design/cad-harness-mvp/build-schema.json")):
        path = safe_input(episode, name)
        if report.get(key) != ledger.sha(path.read_text(encoding="utf-8").encode("utf-8")):
            raise Stop("continuation_saved_source_binding")
        expected = manifest.get("skill_sha256") if key == "skill_sha256" else manifest["files"].get(name)
        _bound_file(path, expected, evidence)
    for name in ("design/cad-harness-mvp/eval-v1/schema.json",
                 "design/cad-harness-verify-v3/gold-schema.json"):
        _bound_file(safe_input(episode, name), manifest["files"].get(name), evidence)
    episode_events = [event for event in events if event.get("episode_id") == entry["id"]]
    finished = [event for event in episode_events if event["event"] == "episode_finished"]
    if len(finished) != 1:
        raise Stop("continuation_saved_timing_missing")
    timing = {key: finished[0].get(key) for key in ("wall_s", "active_s")}
    if (any(type(value) not in (int, float) or not math.isfinite(value) or value < 0
            for value in timing.values()) or timing["active_s"] > timing["wall_s"]):
        raise Stop("continuation_saved_timing_invalid")
    ended = [event for event in episode_events if event["event"] == "attempt_finished"]
    started = [event for event in episode_events if event["event"] == "attempt_started"]
    if {event["attempt_id"] for event in started} != {event["attempt_id"] for event in ended}:
        raise Stop("continuation_saved_attempt_unfinished")
    for event in ended:
        start = next(item for item in started if item["attempt_id"] == event["attempt_id"])
        _saved_attempt(event, start, prior, request, manifest, evidence,
                       timeout_attempt=timeout_attempt)
    cad_results = [ledger.read_json(event["streams"]["stdout"]["path"])
                   for event in ended if event["operation"] == "cad"]
    if cad_results != [attempt["result"] for attempt in report.get("attempts", [])]:
        raise Stop("continuation_saved_cad_ledger_binding")
    if sum(event.get("charged") is not False for event in ended if event["operation"] == "model") != report.get("llm_calls"):
        raise Stop("continuation_saved_model_ledger_binding")
    v3.check_calls(report, entry, request, None, where)
    validate_report(entry, card, base, episode, report)
    if v3.harness_failure(report):
        raise Stop("continuation_saved_harness_failure")
    # Include all saved report/artifact bytes, not just the successful CAD files.
    # evidence_sha256 is the canonical hash of this absolute-path/digest mapping.
    for path in sorted(where.rglob("*")):
        if path.is_file():
            path = _unlinked(path)
            evidence[str(path)] = ledger.file_sha(path)
    report["_rubric"] = card.get("rubric")
    row = score_episode(entry, report, entry["id"], **timing) if score_row else report
    return row, dict(episode_sequence=sequence, driver_sha256=evidence[str(driver_path)],
                     **timing, row_sha256=None)


def _prefix_material(sealed_input, prior_run, *, prior_manifest_sha256,
                     prior_summary_sha256, prior_ledger_sha256, cohort_sha256, root=ROOT):
    prior = _unlinked(prior_run, directory=True)
    evidence = {}
    references = dict(prior_manifest_sha256=prior_manifest_sha256,
                      prior_summary_sha256=prior_summary_sha256,
                      prior_ledger_sha256=prior_ledger_sha256, cohort_sha256=cohort_sha256)
    paths = {}
    for key, name in (("prior_manifest_sha256", "manifest.json"),
                      ("prior_summary_sha256", "summary.json"),
                      ("prior_ledger_sha256", "ledger.jsonl"), ("cohort_sha256", "cohort.json")):
        paths[name] = _bound_file(prior/name, references[key], evidence)
    sealed = _bound_file(sealed_input, cohort_sha256, evidence)
    manifest = ledger.read_json(paths["manifest.json"])
    if manifest.get("schema") != "cad-harness.manifest.v4":
        raise Stop("continuation_prior_manifest_contract")
    commitment = manifest["commitment"]
    _bound_file(commitment["path"], commitment["sha256"], evidence)
    cohort = load_cohort(sealed, manifest)
    if ledger.read_json(paths["cohort.json"]) != cohort:
        raise Stop("continuation_prior_cohort_binding")
    rows = _prior_rows(ledger.read_json(paths["summary.json"]), cohort["entries"])
    events, costs = _prior_costs(paths["ledger.jsonl"], manifest, cohort["entries"])
    entry = cohort["entries"][17]
    card = ledger.read_json(safe_input(sealed.parent, entry["acceptance"]))
    row, recovery = _saved_episode(entry, card, sealed.parent, prior, manifest, events, evidence)
    tokens = rows[17].get("tokens")
    episode_cost = costs["per_episode"].get(entry["id"])
    if (not isinstance(tokens, dict) or set(tokens) != set(ledger.USAGE_KEYS)
            or episode_cost is None
            or tokens != {key: value["total"] for key, value in episode_cost["tokens"].items()}):
        raise Stop("continuation_saved_token_binding")
    row["tokens"] = tokens
    recovery.update(row_sha256=ledger.sha(_canonical(row)), evidence_sha256=ledger.sha(_canonical(evidence)))
    prefix = dict(schema="cad-harness.holdout-prefix.v4", prefix_count=18, prior_counted_calls=20,
                  **references, prior_run_dir=str(prior), prefix17_sha256=ledger.sha(_canonical(rows[:17])),
                  rows=rows[:17]+[row], recovery=recovery)
    return prefix, dict(schema="cad-harness.holdout-prefix-evidence.v4", files=evidence,
                        prior_costs=costs, prior_cost_scope="original_segment_only",
                        inherited_before_prior_segment=manifest["authorization"]["prior_counted_calls"])


def recover_prefix(sealed_input, prior_run, run_dir, *, prior_manifest_sha256,
                   prior_summary_sha256, prior_ledger_sha256, cohort_sha256, root=ROOT):
    """Recover only saved 18; preserve 1–17 and never execute or claim anything."""
    prefix, evidence = _prefix_material(sealed_input, prior_run,
        prior_manifest_sha256=prior_manifest_sha256, prior_summary_sha256=prior_summary_sha256,
        prior_ledger_sha256=prior_ledger_sha256, cohort_sha256=cohort_sha256, root=root)
    _prefix_destination(run_dir, prior_run, Path(sealed_input).parent)
    out = ledger.new_directory(run_dir)
    ledger.write_json(out/"prefix.json", prefix)
    ledger.write_json(out/"evidence.json", evidence)
    return dict(status="RECOVERED", prefix_path=str(out/"prefix.json"),
                prefix_sha256=ledger.file_sha(out/"prefix.json"), prefix_count=18,
                prior_counted_calls=20, live_calls=0, live_cad_runs=0)


def _continuation_authorization(manifest):
    authorization = manifest.get("authorization")
    continuation = authorization.get("continuation") if isinstance(authorization, dict) else None
    fields = {"schema", "prefix_count", "prefix_path", "prefix_sha256",
              "prior_manifest_sha256", "prior_summary_sha256", "prior_ledger_sha256", "cohort_sha256"}
    if (not isinstance(continuation, dict) or set(continuation) != fields
            or continuation["schema"] != "cad-harness.holdout-continuation.v4"
            or type(continuation["prefix_count"]) is not int
            or type(authorization.get("charged_calls")) is not int or authorization["charged_calls"] != 163
            or type(authorization.get("prior_counted_calls")) is not int
            or (continuation["prefix_count"], authorization["prior_counted_calls"]) not in ((18, 20), (59, 88))
            or not isinstance(continuation["prefix_path"], str) or not continuation["prefix_path"]
            or not Path(continuation["prefix_path"]).is_absolute()
            or any(not _digest(continuation[key]) for key in fields if key.endswith("sha256"))):
        raise Stop("continuation_authorization_contract")
    return continuation


def _historical_prefix18(prior, manifest, sealed, cohort, retained, evidence):
    """Authenticate the admitted 18 and its originals without rescoring its rows."""
    continuation = _continuation_authorization(manifest)
    if continuation["prefix_count"] != 18:
        raise Stop("continuation_final_requires_original18")
    audit = _unlinked(prior/"continuation", directory=True)
    path = _bound_file(audit/"prefix.json", continuation["prefix_sha256"], evidence)
    prefix = ledger.read_json(path)
    if (not isinstance(prefix, dict) or type(prefix.get("prefix_count")) is not int
            or prefix["prefix_count"] != 18 or type(prefix.get("prior_counted_calls")) is not int
            or prefix["prior_counted_calls"] != 20
            or not isinstance(prefix.get("rows"), list) or len(prefix["rows"]) != 18
            or _canonical(prefix["rows"]) != _canonical(retained[:18])
            or not isinstance(prefix.get("prior_run_dir"), str)
            or not Path(prefix["prior_run_dir"]).is_absolute()):
        raise Stop("continuation_original18_binding")
    old = _unlinked(prefix["prior_run_dir"], directory=True)
    old_evidence = {}
    references = {key: continuation[key] for key in
                  ("prior_manifest_sha256", "prior_summary_sha256", "prior_ledger_sha256", "cohort_sha256")}
    for key, name in (("prior_manifest_sha256", "manifest.json"),
                      ("prior_summary_sha256", "summary.json"),
                      ("prior_ledger_sha256", "ledger.jsonl"), ("cohort_sha256", "cohort.json")):
        _bound_file(old/name, references[key], old_evidence)
        _bound_file(audit/("prior-"+name), references[key], evidence)
    _bound_file(sealed, references["cohort_sha256"], old_evidence)
    historical = ledger.read_json(old/"manifest.json")
    if historical.get("schema") != "cad-harness.manifest.v4":
        raise Stop("continuation_prior_manifest_contract")
    if (_canonical(historical.get("commitment")) != _canonical(manifest.get("commitment"))
            or ledger.read_json(old/"cohort.json") != cohort
            or load_cohort(sealed, historical) != cohort):
        raise Stop("continuation_original18_cohort_binding")
    _bound_file(historical["commitment"]["path"], historical["commitment"]["sha256"], old_evidence)
    original_rows = _prior_rows(ledger.read_json(old/"summary.json"), cohort["entries"])
    events, costs = _prior_costs(old/"ledger.jsonl", historical, cohort["entries"])
    entry = cohort["entries"][17]
    card = ledger.read_json(safe_input(sealed.parent, entry["acceptance"]))
    _, recovery = _saved_episode(entry, card, sealed.parent, old, historical, events,
                                  old_evidence, score_row=False)
    tokens = prefix["rows"][17].get("tokens")
    episode_cost = costs["per_episode"].get(entry["id"])
    if (episode_cost is None or not isinstance(tokens, dict)
            or tokens != {key: value["total"] for key, value in episode_cost["tokens"].items()}
            or tokens != original_rows[17].get("tokens")):
        raise Stop("continuation_saved_token_binding")
    recovery.update(row_sha256=ledger.sha(_canonical(prefix["rows"][17])),
                    evidence_sha256=ledger.sha(_canonical(old_evidence)))
    expected = dict(schema="cad-harness.holdout-prefix.v4", prefix_count=18, prior_counted_calls=20,
                    **references, prior_run_dir=str(old),
                    prefix17_sha256=ledger.sha(_canonical(original_rows[:17])),
                    rows=original_rows[:17]+[prefix["rows"][17]], recovery=recovery)
    expected_evidence = dict(schema="cad-harness.holdout-prefix-evidence.v4", files=old_evidence,
                             prior_costs=costs, prior_cost_scope="original_segment_only",
                             inherited_before_prior_segment=historical["authorization"]["prior_counted_calls"])
    proof_path = _unlinked(audit/"evidence.json")
    if (_canonical(prefix) != _canonical(expected)
            or _canonical(ledger.read_json(proof_path)) != _canonical(expected_evidence)):
        raise Stop("continuation_original18_evidence_binding")
    evidence[str(proof_path)] = ledger.file_sha(proof_path)
    _bound_file(audit/"driver-run.json", recovery["driver_sha256"], evidence)
    evidence.update(old_evidence)
    return expected_evidence, str(old)


def _saved_argument(argv, option):
    if (not isinstance(argv, list) or any(not isinstance(value, str) for value in argv)
            or argv.count(option) != 1 or argv.index(option)+1 >= len(argv)):
        raise Stop("continuation_saved_argv_binding")
    return argv[argv.index(option)+1]


def _final_costs(path, manifest, entries, base, evidence):
    """All activity in this immutable segment is exactly 19–59 and settled."""
    events = list(ledger.rows(path))
    selected = entries[18:59]
    allowed = {entry["id"]: entry for entry in selected}
    starts, ends, episode_starts, episode_ends = {}, {}, [], []
    run_ids = {event.get("run_id") for event in events}
    if len(run_ids) != 1 or None in run_ids:
        raise Stop("continuation_final_ledger_identity")
    for number, event in enumerate(events, 1):
        if (type(event.get("event_id")) is not int or event["event_id"] != number
                or event.get("phase") != "holdout"
                or event.get("episode_id") is not None and event["episode_id"] not in allowed):
            raise Stop("continuation_final_ledger_identity")
        kind = event["event"]
        if kind == "episode_started":
            episode_starts.append(event.get("episode_id"))
        elif kind == "episode_finished":
            episode_ends.append(event.get("episode_id"))
        elif kind in ("attempt_started", "attempt_finished"):
            target = starts if kind == "attempt_started" else ends
            key = event.get("attempt_id")
            if (not isinstance(key, str) or re.fullmatch(r"attempt-[0-9]{4,}", key) is None
                    or key in target or event.get("episode_id") not in allowed):
                raise Stop("continuation_prior_attempt_identity")
            target[key] = event
        elif kind in ("work_started", "work_finished"):
            raise Stop("continuation_final_unexpected_work")
    expected_ids = [entry["id"] for entry in selected]
    if episode_starts != expected_ids or episode_ends != expected_ids:
        raise Stop("continuation_final_episode_order")
    run_ends = [event for event in events if event["event"] == "run_finished"]
    if len(run_ends) != 1 or run_ends[0].get("stop_reason") != "transport_or_capture_interrupted":
        raise Stop("continuation_final_run_stop_binding")
    run_starts = [event for event in events if event["event"] == "run_started"]
    if (len(run_starts) != 1
            or run_starts[0].get("manifest_sha256") != manifest.get("manifest_sha256")
            or run_starts[0].get("cohort_sha256") != ledger.file_sha(path.parent/"cohort.json")
            or _canonical(run_starts[0].get("continuation")) != _canonical(manifest["authorization"]["continuation"])
            or type(run_starts[0].get("prefix_count")) is not int or run_starts[0]["prefix_count"] != 18
            or type(run_starts[0].get("prior_counted_calls")) is not int
            or run_starts[0]["prior_counted_calls"] != 20):
        raise Stop("continuation_final_run_start_binding")
    if starts.keys() != ends.keys():
        raise Stop("continuation_saved_attempt_unfinished")
    if list(starts) != ["attempt-%04d" % number for number in range(1, len(starts)+1)]:
        raise Stop("continuation_prior_attempt_identity")
    failed = [event for event in ends.values() if event.get("error") is not None]
    if (len(failed) != 1 or failed[0].get("error") != "TimeoutExpired"
            or failed[0].get("episode_id") != entries[58]["id"]
            or failed[0].get("operation") != "model" or failed[0].get("stage") != "repair"
            or list(ends)[-1] != failed[0]["attempt_id"]):
        raise Stop("continuation_saved_final_timeout_required")
    timeout = failed[0]
    logical_call, retry_parent = 1, None
    for key, end in ends.items():
        start = starts[key]
        episode_begin = next(event for event in events if event["event"] == "episode_started"
                             and event["episode_id"] == end["episode_id"])
        episode_end = next(event for event in events if event["event"] == "episode_finished"
                           and event["episode_id"] == end["episode_id"])
        entry = allowed[end["episode_id"]]
        if (start["event_id"] >= end["event_id"]
                or not episode_begin["event_id"] < start["event_id"] < end["event_id"] < episode_end["event_id"]
                or any(start.get(field) != end.get(field) for field in (
                    "episode_id", "operation", "route", "stage", "retained_segment",
                    "logical_call_id", "retry_parent_id", "evidence_mode", "manifest_sha256"))
                or end.get("operation") not in ("model", "cad")
                or end.get("route") != entry["route"]
                or end.get("retained_segment") is not (entry["group"] not in ("dev", "completion"))
                or end.get("evidence_mode") not in ("live", "unit_mock")
                or not _digest(manifest.get("manifest_sha256"))
                or end.get("manifest_sha256") != manifest["manifest_sha256"]
                or any(type(end.get(field)) not in (int, float)
                       or not math.isfinite(end[field]) or end[field] < 0 for field in ("wall_s", "active_s"))
                or end["active_s"] > end["wall_s"]):
            raise Stop("continuation_prior_attempt_binding")
        request = safe_input(base, entry["request"]).read_bytes()
        submitted = _saved_attempt(end, start, path.parent, request, manifest, evidence,
                                   timeout_attempt=timeout["attempt_id"])
        if end["operation"] == "model":
            summary = end.get("provider_summary")
            if (type(end.get("charged")) is not bool or type(end.get("provider_rejected")) is not bool
                    or end["charged"] is end["provider_rejected"]
                    or not isinstance(summary, dict)
                    or summary.get("provider_rejected") is not end["provider_rejected"]
                    or submitted.get("model") != manifest.get("generator", {}).get("model")
                    or not isinstance(submitted.get("argv"), list)
                    or submitted["argv"][:1] != [manifest.get("generator", {}).get("omp")]
                    or not isinstance(end.get("usage"), dict)
                    or set(end["usage"].get("values", {})) != set(ledger.USAGE_KEYS)):
                raise Stop("continuation_prior_charge_contract")
            if (type(end.get("logical_call_id")) is not int or end["logical_call_id"] != logical_call
                    or end.get("retry_parent_id") != retry_parent):
                raise Stop("continuation_saved_logical_call_binding")
            retry_parent = key if end["provider_rejected"] else None
            logical_call += end["charged"]
            argv = submitted["argv"]
            if (_saved_argument(argv, "--model") != submitted["model"]
                    or _saved_argument(argv, "--thinking") != manifest["generator"]["thinking"]):
                raise Stop("continuation_saved_argv_binding")
            payloads = [value[1:] for value in argv if value.startswith("@")]
            configuration = _saved_argument(argv, "--config")
            if (not payloads or payloads[0] not in submitted["files"]
                    or configuration not in submitted["files"]):
                raise Stop("continuation_saved_submission_binding")
            payload = ledger.read_json(payloads[0])
            if (payload.get("request") != request.decode("utf-8")
                    or not isinstance(payload.get("runtime_data"), dict)
                    or payload["runtime_data"].get("stage", "initial") != end.get("stage")
                    or _canonical(ledger.read_json(configuration)) != _canonical(OMP_CONFIG)):
                raise Stop("continuation_saved_submission_binding")
            decoded = omp_result(end["streams"]["stdout"]["path"])
            decoded["summary"]["full_sha256"] = end["streams"]["stdout"]["sha256"]
            if (_canonical(decoded["summary"]) != _canonical(summary)
                    or decoded["models"] and decoded["models"] != [submitted["model"]]
                    or key != timeout["attempt_id"] and _canonical(end["usage"]) != _canonical(decoded["usage"])
                    or decoded["assistant_ends"] > 1):
                raise Stop("continuation_saved_provider_binding")
    costs = ledger.summarize(path)
    if (costs["unfinished_attempts"] != 0 or costs["conservative_reserved_calls"] != 68
            or manifest["authorization"]["prior_counted_calls"] + costs["conservative_reserved_calls"] != 88):
        raise Stop("continuation_prior_count_must_equal_88")
    return events, costs, timeout


def _final_prefix_material(sealed_input, prior_run, *, prior_manifest_sha256,
                           prior_summary_sha256, prior_ledger_sha256, cohort_sha256, root=ROOT):
    prior = _unlinked(prior_run, directory=True)
    evidence = {}
    references = dict(prior_manifest_sha256=prior_manifest_sha256,
                      prior_summary_sha256=prior_summary_sha256,
                      prior_ledger_sha256=prior_ledger_sha256, cohort_sha256=cohort_sha256)
    for key, name in (("prior_manifest_sha256", "manifest.json"),
                      ("prior_summary_sha256", "summary.json"),
                      ("prior_ledger_sha256", "ledger.jsonl"), ("cohort_sha256", "cohort.json")):
        _bound_file(prior/name, references[key], evidence)
    sealed = _bound_file(sealed_input, cohort_sha256, evidence)
    manifest = ledger.read_json(prior/"manifest.json")
    if manifest.get("schema") != "cad-harness.manifest.v4":
        raise Stop("continuation_prior_manifest_contract")
    _continuation_authorization(manifest)
    _bound_file(manifest["commitment"]["path"], manifest["commitment"]["sha256"], evidence)
    cohort = load_cohort(sealed, manifest)
    if ledger.read_json(prior/"cohort.json") != cohort:
        raise Stop("continuation_prior_cohort_binding")
    rows = _prior_rows(ledger.read_json(prior/"summary.json"), cohort["entries"])
    unstarted = v3.empty_row(cohort["entries"][59], cohort["entries"][59]["id"],
                             "transport_or_capture_interrupted")
    if _canonical(rows[59]) != _canonical(unstarted):
        raise Stop("continuation_final60_not_unstarted")
    inherited, original_run = _historical_prefix18(prior, manifest, sealed, cohort, rows, evidence)
    policy_name = freezing.DESIGN+"/policy.json"
    policy_path = _bound_file(Path(root)/policy_name, manifest.get("policy_sha256"), evidence)
    policy = ledger.read_json(policy_path)
    if (manifest.get("files", {}).get(policy_name) != manifest["policy_sha256"]
            or _canonical(manifest.get("limits")) != _canonical(freezing.LIMITS)
            or any(_canonical(policy.get(key)) != _canonical(value) for key, value in freezing.LIMITS.items())):
        raise Stop("continuation_saved_policy_binding")
    events, costs, timeout = _final_costs(prior/"ledger.jsonl", manifest, cohort["entries"], sealed.parent, evidence)
    for entry, row in zip(cohort["entries"][18:58], rows[18:58]):
        finished = next(event for event in events if event["event"] == "episode_finished"
                        and event["episode_id"] == entry["id"])
        if (finished.get("status") != "completed" or row.get("stop_reason") is not None
                or type(row.get("completed")) is not bool or type(row.get("passed")) is not bool
                or row.get("completed") is False and row.get("passed") is not False
                or row.get("completed") is not True and row.get("episode_stop_reason") not in (
                    "episode_stage_deadline_exceeded", "episode_deadline_exceeded",
                    "repair_time_reservation_lost", "deadline_exceeded")):
            raise Stop("continuation_prior_nonterminal_row")
        if (any(type(row.get(key)) not in (int, float) or not math.isfinite(row[key])
                or type(finished.get(key)) not in (int, float) or not math.isfinite(finished[key])
                or not 0 <= row[key] <= finished[key] for key in ("wall_s", "active_s"))
                or row["active_s"] > row["wall_s"] or finished["active_s"] > finished["wall_s"]):
            raise Stop("continuation_saved_timing_binding")
        episode_cost = costs["per_episode"].get(entry["id"])
        episode_attempts = [event for event in events if event["event"] == "attempt_finished"
                            and event["episode_id"] == entry["id"]]
        if (episode_cost is None
                or type(row.get("sol_calls")) is not int or type(row.get("cad_attempts")) is not int
                or row.get("tokens") != {key: value["total"] for key, value in episode_cost["tokens"].items()}
                or row.get("sol_calls") != sum(event["operation"] == "model" and event["charged"]
                                               for event in episode_attempts)
                or row.get("cad_attempts") != sum(event["operation"] == "cad" for event in episode_attempts)
                or row.get("sol_calls", math.inf) > entry["max_calls"]):
            raise Stop("continuation_saved_retained_cost_binding")
    entry = cohort["entries"][58]
    card = ledger.read_json(safe_input(sealed.parent, entry["acceptance"]))
    report, recovery = _saved_episode(entry, card, sealed.parent, prior, manifest, events, evidence,
                                      sequence=59, timeout_attempt=timeout["attempt_id"], score_row=False)
    settings = v3.Budget(entry["max_calls"]).settings()
    settings.update(model=cad_agent.MODEL, effort=cad_agent.EFFORT, disabled=list(cad_agent.DISABLED),
                    sandbox="read-only", skip_git_repo_check=True)
    if (_canonical(report.get("settings")) != _canonical(settings)
            or report.get("cli_version") != cad_agent.clean(manifest["generator"]["version"].strip())):
        raise Stop("continuation_saved_driver_identity")
    for event, attempt in zip((item for item in events if item["event"] == "attempt_finished"
                               and item.get("episode_id") == entry["id"] and item["operation"] == "cad"),
                              report.get("attempts", [])):
        submitted = ledger.read_json(prior/event["attempt_id"]/"submitted.json")
        argv = submitted.get("argv")
        source = _saved_argument(argv, "--script")
        if (submitted["files"].get(source) != attempt["source_sha256"]
                or Path(_saved_argument(argv, "--out-dir")) != prior/"episode-059"/attempt["out_dir"]
                or Path(_saved_argument(argv, "--gold")) != safe_input(sealed.parent, card["gold"])
                or _saved_argument(argv, "--task") != report["task_id"]):
            raise Stop("continuation_saved_cad_submission_binding")
    calls = report.get("calls", [])
    ended = [event for event in events if event["event"] == "attempt_finished"
             and event.get("episode_id") == entry["id"]]
    model_events = [event for event in ended if event["operation"] == "model"]
    final_call = calls[-1] if calls else {}
    repair_budget = policy["active_budgets_s"]["repair_sol"]
    finished = next(event for event in events if event["event"] == "episode_finished"
                    and event["episode_id"] == entry["id"])
    if (report.get("status") != "failed" or report.get("message_code") != "transport_or_capture_interrupted"
            or finished.get("status") != "incomplete"
            or report.get("repair_invoked") is not True or report.get("repair_calls") != 1
            or report.get("repair_eligible") is not True
            or report.get("llm_calls") != 3 or report.get("cad_attempts") != 1
            or len(ended) != 4 or len(model_events) != 3 or len(calls) != 3
            or ended[-1]["attempt_id"] != timeout["attempt_id"]
            or final_call.get("purpose") != "repair" or final_call.get("stage") != "repair"
            or type(final_call.get("timeout_s")) not in (int, float) or final_call["timeout_s"] != repair_budget
            or final_call.get("error_type") != "OSError"
            or final_call.get("provider_summary", {}).get("transport_error") != "OSError"
            or any(event.get("provider_rejected") is not False for event in model_events)
            or any(call.get("provider_rejected") is not False for call in calls)
            or any("server_overloaded" in event["provider_summary"].get("error_infos", []) for event in model_events)
            or _canonical(timeout["usage"]) != _canonical(ledger.unknown_usage("transport_or_capture_incomplete"))
            or timeout["wall_s"] < repair_budget or timeout["active_s"] != timeout["wall_s"]
            or recovery["active_s"] >= policy["active_budgets_s"]["episode"]
            or report.get("wall_ms", math.inf) >= 1000*policy["active_budgets_s"]["episode"]):
        raise Stop("continuation_saved_final_repair_binding")
    for logical, (call, event) in enumerate(zip(calls, model_events), 1):
        if (call.get("logical_call") != logical
                or event.get("logical_call_id") != model_events[0]["logical_call_id"]+logical-1
                or call.get("stage") != event.get("stage")
                or call.get("slot_consumed") is not True):
            raise Stop("continuation_saved_model_ledger_binding")
        # The old fatal wrapper discarded TimeoutExpired's capture attachments.
        # Authenticate that loss exactly; do not invent/promote historical bytes.
        for name, artifact in call["transport_artifacts"].items():
            raw = event["streams"][name]
            if event["attempt_id"] == timeout["attempt_id"]:
                if (artifact["bytes"] != 0 or artifact["full_bytes"] != 0
                        or artifact["full_sha256"] != ledger.sha(b"")):
                    raise Stop("continuation_saved_timeout_driver_capture")
            elif artifact["full_sha256"] != raw["sha256"] or artifact["full_bytes"] != raw["bytes"]:
                raise Stop("continuation_saved_driver_stream_binding")
    endpoints = {key: recovery[key] for key in ("wall_s", "active_s")}
    original = rows[58]
    timing = {key: original.get(key) for key in endpoints}
    if (any(type(value) not in (int, float) or not math.isfinite(value)
            or not 0 <= value <= endpoints[key] for key, value in timing.items())
            or timing["active_s"] > timing["wall_s"]):
        raise Stop("continuation_saved_timing_binding")
    row = score_episode(entry, report, entry["id"], **timing)
    tokens = rows[58].get("tokens")
    episode_cost = costs["per_episode"].get(entry["id"])
    if (not isinstance(tokens, dict) or set(tokens) != set(ledger.USAGE_KEYS) or episode_cost is None
            or tokens != {key: value["total"] for key, value in episode_cost["tokens"].items()}):
        raise Stop("continuation_saved_token_binding")
    row["tokens"] = tokens
    changed = {key for key in set(original) | set(row) if _canonical(original.get(key)) != _canonical(row.get(key))}
    if (row.get("completed") is not True or row.get("passed") is not False
            or original.get("completed") is not False or original.get("passed") is not False
            or original.get("stop_reason") != "transport_or_capture_interrupted"
            or changed != {"completed", "stop_reason"}):
        raise Stop("continuation_saved_score_cannot_settle_failed_timeout")
    recovery.update(error_type="TimeoutExpired", repair_unfinished=True,
                    **timing, original_score_times=timing, episode_finished_times=endpoints,
                    original_timeout_s=final_call["timeout_s"], original_call_elapsed_s=final_call["elapsed_s"],
                    original_report_wall_ms=report["wall_ms"], original_row=original,
                    original_row_sha256=ledger.sha(_canonical(original)),
                    raw_capture_flags={name: {key: stream.get(key) for key in ("complete", "missing_reason")}
                                       for name, stream in timeout["streams"].items()},
                    row_sha256=ledger.sha(_canonical(row)), evidence_sha256=ledger.sha(_canonical(evidence)))
    prefix = dict(schema="cad-harness.holdout-prefix.v4", prefix_count=59, prior_counted_calls=88,
                  **references, prior_run_dir=str(prior), prefix58_sha256=ledger.sha(_canonical(rows[:58])),
                  rows=rows[:58]+[row], recovery=recovery)
    return prefix, dict(schema="cad-harness.holdout-prefix-evidence.v4", files=evidence,
                        prior_costs=costs, prior_cost_scope="original_segment_only",
                        inherited_before_prior_segment=20, inherited_costs=inherited,
                        historical_run_dirs=[original_run])


def recover_final_prefix(sealed_input, prior_run, run_dir, *, prior_manifest_sha256,
                         prior_summary_sha256, prior_ledger_sha256, cohort_sha256, root=ROOT):
    """Settle only saved 59 from immutable history; never execute or claim."""
    prefix, evidence = _final_prefix_material(sealed_input, prior_run,
        prior_manifest_sha256=prior_manifest_sha256, prior_summary_sha256=prior_summary_sha256,
        prior_ledger_sha256=prior_ledger_sha256, cohort_sha256=cohort_sha256, root=root)
    _prefix_destination(run_dir, prior_run, Path(sealed_input).parent,
                        *evidence["historical_run_dirs"])
    out = ledger.new_directory(run_dir)
    ledger.write_json(out/"prefix.json", prefix)
    ledger.write_json(out/"evidence.json", evidence)
    return dict(status="RECOVERED", prefix_path=str(out/"prefix.json"),
                prefix_sha256=ledger.file_sha(out/"prefix.json"), prefix_count=59,
                prior_counted_calls=88, live_calls=0, live_cad_runs=0)


def _admit_continuation(manifest, sealed_input, *, root=ROOT):
    authorization = manifest["authorization"]
    if "continuation" not in authorization:
        return None
    continuation = _continuation_authorization(manifest)
    path = _bound_file(continuation["prefix_path"], continuation["prefix_sha256"], {})
    raw = path.read_bytes()
    prefix = ledger.read_json(path)
    references = {key: continuation[key] for key in
                  ("prior_manifest_sha256", "prior_summary_sha256", "prior_ledger_sha256", "cohort_sha256")}
    if (not isinstance(prefix, dict) or type(prefix.get("prefix_count")) is not int
            or type(prefix.get("prior_counted_calls")) is not int
            or not isinstance(prefix.get("prior_run_dir"), str) or not prefix["prior_run_dir"]
            or not Path(prefix["prior_run_dir"]).is_absolute()):
        raise Stop("continuation_prefix_contract")
    material = _final_prefix_material if continuation["prefix_count"] == 59 else _prefix_material
    expected, evidence = material(sealed_input, prefix["prior_run_dir"], root=root, **references)
    if continuation["prefix_count"] == 59:
        historical = ledger.read_json(Path(prefix["prior_run_dir"])/"manifest.json")
        if any(_canonical(manifest.get(key)) != _canonical(historical.get(key))
               for key in ("commitment", "policy_sha256", "limits", "skill_sha256")):
            raise Stop("continuation_current_policy_binding")
        proof = ledger.read_json(_unlinked(path.parent/"evidence.json"))
        if _canonical(proof) != _canonical(evidence):
            raise Stop("continuation_prefix_evidence_binding")
    # Canonical bytes distinguish booleans from integers and bind every proof/row field.
    if _canonical(prefix) != _canonical(expected) or ledger.sha(raw) != continuation["prefix_sha256"]:
        raise Stop("continuation_prefix_binding")
    return dict(prefix=expected, raw=raw, evidence=evidence, authorization=continuation)


def run_holdout(manifest_path, sealed_input, run_dir, *, root=ROOT, process=stream_process,
                wall=None, sleep=time.sleep):
    # No input, output directory or executable is touched before this authorization gate.
    manifest = freezing.verify(manifest_path, root=root)
    if not manifest.get("authorization"):
        raise Stop("live_manifest_authorization_required")
    manifest["manifest_sha256"] = ledger.file_sha(manifest_path)
    if "continuation" in manifest["authorization"]:
        _continuation_authorization(manifest)
    cohort = load_cohort(sealed_input, manifest)
    admitted = _admit_continuation(manifest, sealed_input, root=root)
    prefix_count = admitted["prefix"]["prefix_count"] if admitted else 0
    prior_count = manifest["authorization"]["prior_counted_calls"]
    if admitted:
        _prefix_destination(run_dir, admitted["prefix"]["prior_run_dir"],
                            Path(sealed_input).parent, Path(admitted["authorization"]["prefix_path"]).parent,
                            *admitted["evidence"].get("historical_run_dirs", []))
    out = ledger.new_directory(run_dir)
    freezing.claim(manifest_path, out)
    ledger.write_json(out/"manifest.json", manifest)
    ledger.write_json(out/"cohort.json", cohort)
    if admitted:
        audit = ledger.new_directory(out/"continuation")
        (audit/"prefix.json").write_bytes(admitted["raw"])
        ledger.write_json(audit/"evidence.json", admitted["evidence"])
        prior = Path(admitted["prefix"]["prior_run_dir"])
        for name in ("manifest.json", "summary.json", "ledger.jsonl", "cohort.json"):
            (audit/("prior-"+name)).write_bytes((prior/name).read_bytes())
        if prefix_count == 59:
            history = ledger.new_directory(audit/"original18")
            for name in ("prefix.json", "evidence.json", "prior-manifest.json", "prior-summary.json",
                         "prior-ledger.jsonl", "prior-cohort.json", "driver-run.json"):
                (history/name).write_bytes((prior/"continuation"/name).read_bytes())
        driver = prior/("episode-%03d" % prefix_count)/"reports/cad-run/request-mvp1/driver-run.json"
        (audit/"driver-run.json").write_bytes(driver.read_bytes())
    wall = wall or WallClock()
    started = wall()
    rows, stop_reason = list(admitted["prefix"]["rows"]) if admitted else [], None
    skill = agent.bundle(root)
    with ledger.Journal(out/"ledger.jsonl", out.name, "holdout", clock=wall, now=wall.utc) as journal:
        guard = LiveGuard(manifest, lambda: freezing.verify(manifest_path, root=root), clock=wall, journal=journal)
        transport = LiveTransport(manifest, journal, out, "", skill, guard, root=root, wall=wall, process=process, sleep=sleep)
        active_started = transport.clock()
        continuation_fields = {}
        if admitted:
            continuation_fields = dict(continuation=admitted["authorization"], prefix_count=prefix_count,
                                       prior_counted_calls=prior_count, cost_scope="current_segment_only")
        journal.append("run_started", manifest_sha256=manifest["manifest_sha256"],
                       cohort_sha256=ledger.file_sha(sealed_input), evidence_mode=transport.evidence_mode,
                       **continuation_fields)
        try:
            for index, entry in enumerate(cohort["entries"][prefix_count:], prefix_count):
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
    for row in rows[prefix_count:]:
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
    if admitted:
        new_calls = costs["conservative_reserved_calls"]
        result.update(continuation=dict(
            authorization=admitted["authorization"], prefix_evidence="continuation/evidence.json",
            prior_run_dir=admitted["prefix"]["prior_run_dir"], prefix_count=prefix_count,
            remaining_count=60-prefix_count, cost_scope="current_segment_only",
            prior_costs_path="continuation/evidence.json",
            prior_ledger_path="continuation/prior-ledger.jsonl",
            prior_counted_calls=prior_count, new_counted_calls=new_calls,
            cumulative_counted_calls=prior_count+new_calls))
        costs.update(cost_scope="current_segment_only", prior_counted_calls=prior_count,
                     new_counted_calls=new_calls, cumulative_counted_calls=prior_count+new_calls)
    ledger.write_json(out/"summary.json", result)
    return result
