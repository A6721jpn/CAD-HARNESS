"""Offline adapters around the unchanged VERIFY v3 driver and predicates.

There is deliberately no subprocess/network/CAD launcher in this module.
"""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess

if __package__:
    from . import cad_agent, cad_verify_v3_agent as v3, cad_verify_v4_ledger as ledger
    from .cad_verify_guard import Stop
else:
    import cad_agent, cad_verify_v3_agent as v3, cad_verify_v4_ledger as ledger
    from cad_verify_guard import Stop

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/cad-harness-v4"
POLICY = ROOT / "design/cad-harness-verify-v4/policy.json"
RUNTIME_KEYS = frozenset(("target", "stage", "observations", "answer"))
MARKER = "\n<runtime_data>\n"


def bundle(root=ROOT, *, profile="original"):
    root = Path(root)
    folder = root / "skills/cad-harness-v4"
    if profile == "c-s1":
        policy = ledger.read_json(root / "design/cad-harness-verify-v4/capability-policy.json")
        if (policy.get("schema") != "cad-harness.capability-policy.v4c"
                or policy.get("profile") != profile or policy.get("stage") != "implementation"
                or type(policy.get("live_authorized_calls")) is not int or policy["live_authorized_calls"] != 0
                or policy.get("provider_calls_allowed") is not False
                or policy.get("model_calls_allowed") is not False
                or policy.get("s2_features_allowed") is not False or policy.get("final_v4_ready") is not False
                or policy.get("families") != ["reference_fixture", "contour_extrude"]):
            raise ValueError("capability_policy_not_offline")
        parts = [(folder / name).read_bytes()
                 for name in ("c-s1.md", "modeling.md", "contracts-c-s1.md")]
        parts.append(json.dumps(policy, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8"))
        return b"\n".join(parts)
    if profile != "original":
        raise ValueError("capability_profile")
    policy = ledger.read_json(root / "design/cad-harness-verify-v4/policy.json")
    text = (folder / "SKILL.md").read_text(encoding="utf-8")
    embedded = text.split("<!-- policy:start -->\n", 1)[1].split("\n<!-- policy:end -->", 1)[0]
    if cad_agent.loads(embedded) != policy:
        raise ValueError("skill_policy_drift")
    parts = [(folder / name).read_bytes() for name in ("SKILL.md", "modeling.md", "contracts.md")]
    return b"\n".join(parts)


class ReplayClock:
    def __init__(self, started_at="2000-01-01T00:00:00+00:00"):
        self.value = 0.0
        self.origin = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        if self.origin.tzinfo is None:
            raise ValueError("replay_clock_timezone")

    def __call__(self):
        return self.value

    def advance(self, seconds):
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("replay_elapsed_s")
        self.value += seconds

    def utc(self):
        return (self.origin + timedelta(seconds=self.value)).isoformat()


class ActiveClock:
    def __init__(self, wall):
        self.wall, self.excluded_s = wall, 0.0

    def __call__(self):
        return self.wall() - self.excluded_s

    def exclude(self, seconds):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("invalid_unavailable_interval")
        self.excluded_s += seconds


class OfflineGuard:
    """Same v3 driver guard interface; quota observations are explicitly mocked."""
    def __init__(self, maximum, clock, quota):
        self.call_budget, self.calls = maximum, 0
        self.clock, self.quota = clock, quota
        self.deadline = None

    def remaining(self, reserve=30):
        return math.inf

    def check(self):
        record = self.quota()
        if not isinstance(record, dict) or record.get("decision") != "allow":
            raise Stop((record or {}).get("decision", "quota_snapshot_missing_or_invalid"))
        return record

    def before_episode(self, maximum):
        if maximum > self.call_budget-self.calls:
            raise Stop("insufficient_call_budget")

    def before_call(self):
        if self.calls >= self.call_budget:
            raise Stop("insufficient_call_budget")
        record = self.check()
        self.calls += 1
        return record


class RecordedRuntime:
    """Only replays explicit files. A CAD step copies previously saved artifacts."""
    def __init__(self, path):
        path = Path(path).resolve()
        self.base, self.document = path.parent, ledger.read_json(path)
        if self.document.get("schema") != "cad-harness.replay.v4":
            raise ValueError("replay_schema")
        if self.document.get("evidence_mode") != "recorded":
            raise ValueError("replay_must_be_labeled_recorded")
        self.steps = iter(self.document["steps"])
        self.clock = ReplayClock(self.document["started_at"])
        self.current = None
        self.billing_identity = self.document.get("billing_identity")

    def quota(self):
        # This is replay data, not a fresh observation of a real account.
        values = self.document.get("quota_percent")
        if type(values) not in (int, float) or not math.isfinite(values) or not 0 <= values <= 100:
            return dict(decision="quota_snapshot_missing_or_invalid", evidence_mode="recorded")
        return dict(decision="quota_hard_stop" if values >= 60 else "quota_soft_stop" if values >= 55 else "allow",
                    used_percent=values, evidence_mode="recorded", observed_at=self.clock.utc())

    def sleep(self, seconds):
        self.clock.advance(seconds)

    def file(self, name):
        path = (self.base / name).resolve()
        if not path.is_relative_to(self.base) or path.is_symlink():
            raise ValueError("replay_path_outside_bundle")
        return path

    def execute(self, operation, argv, **unused):
        step = next(self.steps, None)
        if not step or step.get("operation") != operation:
            raise OSError("replay_step_missing_or_out_of_order")
        self.current = step
        self.clock.advance(step["elapsed_s"])
        if operation == "cad":
            source = self.file(step["artifacts_dir"])
            target = Path(argv[argv.index("--out-dir")+1])
            if any(p.is_symlink() for p in source.rglob("*")):
                raise ValueError("linked_replay_artifact")
            shutil.copytree(source, target)
        return dict(returncode=step["returncode"],
                    stdout=self.file(step["stdout_path"]), stderr=self.file(step["stderr_path"]),
                    final=self.file(step["final_path"]).read_bytes() if step.get("final_path") else None)


def chunks(source):
    if isinstance(source, bytes):
        for index in range(0, len(source), 8192):
            yield source[index:index+8192]
    else:
        with Path(source).open("rb") as file:
            while True:
                raw = file.read(8192)
                if not raw:
                    return
                yield raw


class SkillAdapter:
    """Supply v4 instructions while keeping the frozen driver's state machine."""
    def __init__(self, skill, request):
        self.skill, self.request = skill.decode("utf-8"), request

    def __getattr__(self, name):
        return getattr(cad_agent, name)

    def developer_context(self, unused_skill, contract, previous=None):
        data = {}
        if contract.startswith("Return only complete Python source"):
            data["target"] = "source"
        if "Retain this output path for CAD repair" in contract:
            data["stage"] = "repair"
        if previous is not None:
            data["observations"] = previous
        return self.context(data)

    def context(self, data):
        if set(data)-RUNTIME_KEYS:
            raise ValueError("runtime_data_fields")
        if data.get("target") == "plan":
            raise ValueError("plan_target_requires_c_profile")
        return self.skill + (MARKER + json.dumps(data, ensure_ascii=False, allow_nan=False) if data else "")

    def exec_argv(self, codex, work, last, prompt, context=None):
        if prompt != self.request:
            if not prompt.startswith(self.request+"\n"):
                raise ValueError("request_bytes_changed")
            data = cad_agent.loads(context.split(MARKER, 1)[1]) if MARKER in context else {}
            data["answer"] = prompt[len(self.request)+1:]
            context = self.context(data)
        return cad_agent.exec_argv(codex, work, last, self.request, context)


class PlanSkillAdapter(SkillAdapter):
    """The C-profile envelope admits authenticated facts, never attachment I/O."""
    def __init__(self, skill, request, manifest_path, prepared, selection=None):
        super().__init__(skill, request)
        if __package__:
            from . import cad_verify_v4_inputs as inputs
        else:
            import cad_verify_v4_inputs as inputs
        self.prepared = inputs.verify_prepared(prepared, manifest_path)
        self.inputs = inputs.model_inputs(self.prepared, manifest_path)
        self.selection = self._selection([] if selection is None else selection)
        self._inputs_sha256 = ledger.sha(json.dumps(self.inputs, sort_keys=True, allow_nan=False).encode("utf-8"))
        self._selection_sha256 = ledger.sha(json.dumps(self.selection, sort_keys=True, allow_nan=False).encode("utf-8"))

    def _selection(self, values):
        if not isinstance(values, list):
            raise ValueError("selection_must_be_list")
        selected = []
        for item in values:
            if not isinstance(item, dict) or set(item) != {"asset_id", "face_id", "signature"}:
                raise ValueError("selection_fields")
            facts = self.prepared["assets"].get(item["asset_id"])
            matches = [face for face in (facts or {}).get("faces", [])
                       if face.get("id") == item["face_id"] and face.get("signature") == item["signature"]]
            if len(matches) != 1 or matches[0].get("ambiguous") is not False:
                raise ValueError("selection_unresolved_or_ambiguous")
            if item in selected:
                raise ValueError("selection_duplicate")
            selected.append(dict(item))
        return selected

    def context(self, data):
        if not isinstance(data, dict) or set(data) - (RUNTIME_KEYS | {"inputs", "selection"}):
            raise ValueError("runtime_data_fields")
        if data.get("target") != "plan" or data.get("stage", "initial") not in ("initial", "repair", "parse_repair"):
            raise ValueError("plan_runtime_stage_or_target")
        if (ledger.sha(json.dumps(data.get("inputs"), sort_keys=True, allow_nan=False).encode("utf-8")) != self._inputs_sha256
                or ledger.sha(json.dumps(data.get("selection", []), sort_keys=True, allow_nan=False).encode("utf-8")) != self._selection_sha256):
            raise ValueError("plan_runtime_provenance")
        return self.skill + MARKER + json.dumps(data, ensure_ascii=False, allow_nan=False)

    def developer_context(self, unused_skill=None, contract=None, previous=None):
        data = dict(target="plan", stage="initial", inputs=self.inputs, selection=self.selection)
        if previous is not None:
            data.update(stage="repair", observations=previous)
        return self.context(data)


class Transport:
    def __init__(self, runtime, journal, out, skill, request, rate_source=None, route="spec"):
        self.runtime, self.journal, self.out = runtime, journal, Path(out)
        self.clock = ActiveClock(runtime.clock)
        self.rate_source, self.sequence = rate_source, 0
        self.skill, self.request = skill, request
        self.last_attempt = None
        self.logical_call, self.retry_parent, self.route = 1, None, route

    def __call__(self, argv, **kwargs):
        if len(argv) > 1 and argv[1] == "--version":
            return subprocess.CompletedProcess(argv, 0, "OFFLINE RECORDED TRANSPORT", "")
        operation = "model" if len(argv) > 1 and argv[1] == "exec" else "cad"
        if operation == "cad" and ("--probe-profile" not in argv or "--script" not in argv):
            raise OSError("offline_transport_denied")
        self.sequence += 1
        attempt_id = "request:" + str(self.sequence)
        self.last_attempt = attempt_id
        context = next((arg.split("=", 1)[1] for arg in argv
                        if arg.startswith("developer_instructions=")), None)
        context = json.loads(context) if context else ""
        data = cad_agent.loads(context.split(MARKER, 1)[1]) if MARKER in context else {}
        purpose = ("parse_repair" if "error" in data.get("observations", {}) else
                   "repair" if data.get("stage") == "repair" else
                   "source" if data.get("target") == "source" else
                   "question" if self.logical_call == 1 and self.route in ("ask", "completion") else "interpretation")
        base = dict(episode_id="request", attempt_id=attempt_id, operation=operation,
                    evidence_mode="recorded_or_unit_mock", retained_segment=False,
                    logical_call_id=self.logical_call if operation == "model" else None,
                    retry_parent_id=self.retry_parent if operation == "model" else None,
                    route=self.route, stage=data.get("stage", "initial"),
                    purpose=purpose if operation == "model" else None)
        tick, started_at = self.runtime.clock(), self.runtime.clock.utc()
        folder = self.out / ("attempt-%04d" % self.sequence)
        folder.mkdir()
        payload = dict(argv=argv, request=self.request,
                       request_sha256=ledger.sha(self.request.encode("utf-8")),
                       skill_sha256=ledger.sha(self.skill))
        ledger.write_json(folder / "submitted.json", payload)
        self.journal.append("attempt_started", **base, started_at=started_at,
                            submitted_sha256=ledger.sha((folder / "submitted.json").read_bytes()),
                            argv_sha256=ledger.sha(json.dumps(argv, ensure_ascii=False).encode("utf-8")))
        captures = {key: ledger.StreamCapture(folder / (key+".bin"), parse=key == "stdout")
                    for key in ("stdout", "stderr")}
        artifacts, failure, reply = {}, None, None
        try:
            reply = self.runtime.execute(operation, argv, **kwargs)
            for key, capture in captures.items():
                for raw in chunks(reply[key]):
                    capture.feed(raw)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            failure = exc
            for key, capture in captures.items():
                partial = getattr(exc, key, None)
                if partial:
                    for raw in chunks(partial.encode("utf-8") if isinstance(partial, str) else partial):
                        capture.feed(raw)
        finally:
            for key, capture in captures.items():
                artifacts[key] = capture.finish()
                if failure:
                    artifacts[key].update(complete=False, missing_reason="transport_or_capture_interrupted")
        final = reply.get("final") if reply else None
        if operation == "model" and final is not None:
            Path(argv[argv.index("-o")+1]).write_bytes(final)
        summary = captures["stdout"].parser.summary(final)
        summary["full_sha256"] = artifacts["stdout"]["sha256"]
        exempt = bool(operation == "model" and not failure and summary["provider_rejected"])
        elapsed = self.runtime.clock()-tick
        if exempt:
            self.clock.exclude(elapsed)
            self.retry_parent = attempt_id
        elif operation == "model":
            self.logical_call += 1
            self.retry_parent = None
        usage = (ledger.unknown_usage("transport_or_capture_incomplete") if failure else
                 ledger.usage_from_stream(artifacts["stdout"]["path"])) if operation == "model" else None
        self.journal.append("attempt_finished", **base, started_at=started_at,
                            ended_at=self.runtime.clock.utc(), wall_s=elapsed,
                            active_s=0 if exempt else elapsed, charged=not exempt if operation == "model" else None,
                            provider_rejected=exempt, provider_summary=summary,
                            provider_billing_status=None, billing_missing_reason="invoice_not_provided",
                            usage=usage, price=ledger.price(usage, self.rate_source,
                                identity=getattr(self.runtime, "billing_identity", None)) if usage else None,
                            streams=artifacts, exit_code=reply.get("returncode") if reply else None,
                            error=type(failure).__name__ if failure else None)
        if failure:
            raise OSError("offline_transport_or_capture_failed:"+type(failure).__name__) from failure
        result = subprocess.CompletedProcess(argv, reply["returncode"],
                    captures["stdout"].tail.decode("utf-8", errors="replace"),
                    captures["stderr"].tail.decode("utf-8", errors="replace"))
        result.provider_summary = summary
        result.exec_metadata = (captures["stdout"].parser.session, captures["stdout"].parser.usage or None)
        result.transport_capture = {key: dict(tail=captures[key].tail,
                                            full_sha256=value["sha256"], full_bytes=value["bytes"])
                                    for key, value in artifacts.items()}
        return result

    def wait_provider(self, row, budget, guard, logical_deadline, sleeper=None):
        tick = self.runtime.clock()
        attempt = self.last_attempt
        row.update(wait_requested_s=600, backoff_s=0)
        self.journal.append("wait_started", episode_id="request", attempt_id=attempt, requested_s=600)
        try:
            while row["backoff_s"] < 600:
                if guard:
                    guard.check()
                before = self.runtime.clock()
                try:
                    self.runtime.sleep(min(60, 600-row["backoff_s"]))
                finally:
                    elapsed = self.runtime.clock()-before
                    self.clock.exclude(elapsed)
                    row["backoff_s"] += elapsed
        finally:
            self.journal.append("wait_finished", episode_id="request", attempt_id=attempt,
                                requested_s=600, actual_s=self.runtime.clock()-tick,
                                completed=row["backoff_s"] >= 600)


def adapted_driver(adapter, transport):
    # An isolated module gives the unchanged function private dependency bindings.
    # Never monkey-patch the imported v3 module or alter its source/bytecode.
    package = (__package__ + ".") if __package__ else ""
    spec = importlib.util.spec_from_file_location(package+"_verify_v4_core", v3.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.agent = adapter
    module.wait_provider = transport.wait_provider
    module.rollout_summary = lambda *args, **kwargs: None  # No account/session discovery in offline replay.
    return module.run_driver


def request(request_path, acceptance_path, run_dir, *, replay=None, runtime=None, root=ROOT, rate_source=None):
    if runtime is None and replay is None:
        raise Stop("p12_offline_only_replay_required")
    raw = Path(request_path).read_bytes()
    text = raw.decode("utf-8")
    if text.encode("utf-8") != raw:
        raise ValueError("request_utf8")
    card_path = Path(acceptance_path).resolve()
    card = ledger.read_json(card_path)
    if card.get("schema") != "cad-harness.acceptance.v4" or card.get("request_sha256") != ledger.sha(raw):
        raise ValueError("acceptance_request_binding")
    runtime = runtime or RecordedRuntime(replay)
    wall_start = runtime.clock()
    skill = bundle(root)
    out = ledger.new_directory(run_dir)
    # Minimal private filesystem expected by the existing driver. It is new output,
    # not a modification of either frozen skill or the repository's v3 files.
    for name, content in (("skills/freecad-modeling/SKILL.md", skill),
                          ("design/cad-harness-mvp/build-schema.json",
                           (Path(root)/"design/cad-harness-mvp/build-schema.json").read_bytes())):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    gold = (card_path.parent/card["gold"]).resolve() if card.get("gold") else None
    route = card["route"]
    maximum = card.get("max_calls", 4 if route in ("source", "completion") else 1 if route == "ask" else 3)
    with ledger.Journal(out / "ledger.jsonl", out.name, "offline_request", clock=runtime.clock, now=runtime.clock.utc) as journal:
        journal.append("run_started", evidence_mode="recorded_or_unit_mock", live_calls=0, live_cad_runs=0,
                       skill_sha256=ledger.sha(skill), acceptance_sha256=ledger.sha(card_path.read_bytes()))
        journal.append("episode_started", episode_id="request", route=route)
        transport = Transport(runtime, journal, out, skill, text, rate_source, route)
        guard = OfflineGuard(maximum, transport.clock, runtime.quota)
        core = adapted_driver(SkillAdapter(skill, text), transport)
        report, code = core("request-mvp1", "OFFLINE-REPLAY", text, gold, root=out,
                            runner=transport, clock=transport.clock, guard=guard, route=route,
                            max_calls=maximum, rubric=card.get("rubric"), answer=card.get("answer"),
                            preview=card.get("preview", False), provider_retry=True)
        journal.append("episode_finished", episode_id="request", status=report["status"],
                       wall_s=runtime.clock()-wall_start, active_s=transport.clock()-wall_start)
        journal.append("run_finished", wall_s=runtime.clock()-wall_start, active_s=transport.clock()-wall_start, wall_missing_reason=None)
    summary = ledger.summarize(out / "ledger.jsonl")
    summary.update(evidence_mode="recorded_or_unit_mock", live_calls=0, live_cad_runs=0,
                   driver_status=report["status"], driver_message=report["message_code"],
                   driver_report="reports/cad-run/request-mvp1/driver-run.json",
                   overload_robustness="UNVERIFIED", holdout="not_run", pilot="not_run")
    ledger.write_json(out / "summary.json", summary)
    return summary, code
