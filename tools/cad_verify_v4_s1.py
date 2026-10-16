"""Opt-in capability-stage facade; development evidence never authorizes a trial.

All native execution is owned, stdin-closed, captured and separately verified.
No provider launcher, ambient attachment discovery or acceptance defaults live here.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time
import zipfile

if __package__:
    from . import cad_run, cad_agent, cad_verify_v4_agent as agent
    from . import cad_verify_v4_freeze as freezing, cad_verify_v4_ledger as ledger
    from . import cad_verify_v4_live as live
    from . import cad_verify_v4_runtime as runtime_binding
    from . import cad_verify_v4_c2_recipe as c2_recipe
    from .cad_verify_guard import Stop
    from .cad_verify_v3_guard import Budget
else:
    import cad_run, cad_agent, cad_verify_v4_agent as agent
    import cad_verify_v4_freeze as freezing, cad_verify_v4_ledger as ledger
    import cad_verify_v4_live as live
    import cad_verify_v4_runtime as runtime_binding
    import cad_verify_v4_c2_recipe as c2_recipe
    from cad_verify_guard import Stop
    from cad_verify_v3_guard import Budget

ROOT = Path(__file__).resolve().parents[1]
DESIGN = "design/cad-harness-verify-v4"
PROFILE = "c-s1"
PHASE_MODELS = {
    "holdout": {"model": "openai-codex/gpt-6.1-sol", "thinking": "xhigh"},
    "pilot": {"model": "openai-codex/gpt-6-astra", "thinking": "max"},
}
JUDGE = dict(model="openai-codex/gpt-6-astra", thinking="max", authorization=None,
             user_visual_authoritative=True, same_model_as_pilot_generator=True)
PENDING = [
    "S2 and S3 implementation and reviews; S1 is not final v4 readiness",
    "final code/skill/recipe/judge lock before independent fresh family authoring",
    "fresh family cohorts, custody, controls, counts, pass gates and separate call/model-judge budgets",
    "C-Q4 through C-Q8 acceptance/measurement conventions and C-U5 consensus defaults",
    "final execution freeze binding complete U1-U5 roster and all approved cards/commitments",
    "Astra Max judging then authoritative user visual verdict; same-model pilot judge caveat",
]
STAGES = {
    "c-s1": dict(policy="capability-policy.json", label="S1", schema_prefix="", pending=PENDING),
    "c-s2": dict(policy="policy-c-s2.json", label="S2", schema_prefix="s2-",
                 pending=["S1/S2 external reviews and S3 implementation/review"] + PENDING[1:]),
    "c-s3": dict(policy="policy-c-s3.json", label="S3", schema_prefix="s3-",
                 pending=["S1/S2/S3 external reviews",
                          "final code/skill/recipe/judge lock before independent fresh family authoring",
                          "fresh family cohorts, custody, controls, pass gates and separate call/model-judge budgets",
                          "remaining acceptance/measurement consensus and C-U5 defaults",
                          "final execution freeze binding complete U1-U5 roster and approved cards/commitments",
                          "all five pilot inputs; Astra Max judgement and authoritative user visual verdict"]),
}


def _stage(profile):
    if not isinstance(profile, str) or profile not in STAGES:
        raise ValueError("unknown_capability_profile")
    return STAGES[profile]

FORBIDDEN = {"pilot-user", "v4-holdout-private"}


def safe_path(value, *, regular=False):
    """Reject forbidden names before touching the filesystem, and all links."""
    text = os.fspath(value)
    if not isinstance(text, str) or "\x00" in text:
        raise ValueError("s1_path_type")
    if any(part.casefold().rstrip(" .") in FORBIDDEN for part in text.replace("\\", "/").split("/")):
        raise Stop("s1_forbidden_input")
    path = Path(text).absolute()
    for candidate in reversed((path, *path.parents)):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("s1_link_or_reparse_point")
    path = path.resolve(strict=False)
    if any(part.casefold().rstrip(" .") in FORBIDDEN for part in path.parts):
        raise Stop("s1_forbidden_input")
    if regular and not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("s1_regular_file_required")
    return path


def _modules():
    if __package__:
        from . import cad_verify_v4_inputs, cad_verify_v4_plans
    else:
        import cad_verify_v4_inputs, cad_verify_v4_plans
    return cad_verify_v4_inputs, cad_verify_v4_plans


def preflight(root=ROOT, *, policy_path=None, profile=PROFILE):
    stage = _stage(profile)
    root = safe_path(root)
    policy = ledger.read_json(root / DESIGN / stage["policy"])
    if policy_path is not None and ledger.read_json(safe_path(policy_path, regular=True)) != policy:
        raise Stop("s1_policy_override_not_bound")
    if policy.get("profile") != profile or policy.get("live_authorized_calls") != 0:
        raise Stop("s1_policy_not_offline")
    skill = agent.bundle(root, profile=profile)
    c2_recipe.load(root)
    names = ("input-manifest", "prepared-inputs", "capability-plan", "judge-card",
             "judge-result", "capability-manifest")
    names += ("step-facts", "step-recipe") if profile in ("c-s2", "c-s3") else ("contour",)
    for name in names:
        schema = ledger.read_json(root / DESIGN / "schemas" / (stage["schema_prefix"] + name + ".schema.json"))
        if not isinstance(schema, dict) or not (schema.get("type") == "object" or isinstance(schema.get("oneOf"), list)):
            raise ValueError("s1_schema_contract:" + name)
    snapshot = root / DESIGN / "original-profile-snapshot.zip"
    verify_original_snapshot(snapshot)
    return dict(schema="cad-harness.preflight.v4c", profile=profile, status="offline_ready",
                implementation_stage=stage["label"], skill_sha256=ledger.sha(skill),
                policy_sha256=ledger.file_sha(root / DESIGN / stage["policy"]),
                original_profile_snapshot_sha256=ledger.file_sha(snapshot),
                live_calls=0, live_cad_runs=0, holdout="not_run", pilot="not_run",
                final_v4_ready=False, pending_final_freeze=list(stage["pending"]),
                **_prior_snapshot(root, profile))


def verify_original_snapshot(path, *, stage=None):
    """Audit archive bytes without executing or extracting the original profile."""
    path = safe_path(path, regular=True)
    with zipfile.ZipFile(path) as archive:
        metadata = json.loads(archive.read("snapshot.json"))
        files = metadata.get("files")
        expected_schema = "cad-harness.stage-snapshot.v4c" if stage else "cad-harness.original-snapshot.v4"
        if (metadata.get("schema") != expected_schema or not isinstance(files, dict)
                or stage is not None and metadata.get("profile") != stage):
            raise ValueError("original_snapshot_contract")
        if set(archive.namelist()) != set(files) | {"snapshot.json"}:
            raise ValueError("original_snapshot_file_set")
        for name, digest in files.items():
            parts = name.replace("\\", "/").split("/")
            if not parts or any(p in ("", ".", "..") or p.casefold() in FORBIDDEN for p in parts):
                raise ValueError("original_snapshot_path")
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError("original_snapshot_hash")
    return metadata


def _prior_snapshot(root, profile):
    if profile == "c-s1":
        return {}
    prior = "c-s2" if profile == "c-s3" else "c-s1"
    path = safe_path(root / DESIGN / (prior[2:] + "-profile-snapshot.zip"), regular=True)
    verify_original_snapshot(path, stage=prior)
    if profile == "c-s3":
        verify_original_snapshot(safe_path(root / DESIGN / "s1-profile-snapshot.zip", regular=True),
                                 stage="c-s1")
    return dict(prior_stage_snapshot_sha256=ledger.file_sha(path))


def _hashes(directory):
    root = safe_path(directory)
    result = {}
    for path in sorted(root.rglob("*")):
        safe_path(path)
        if path.is_file():
            result[path.relative_to(root).as_posix()] = ledger.file_sha(path)
    return result


def native_work(operation, out, journal, *, timeout=300, process=None, profile=PROFILE, **fields):
    """Run a data-only worker job; raw streams survive both success and failure."""
    _stage(profile)
    if profile in ("c-s2", "c-s3") and operation not in ("prepare-step", "compile", "verify", "identity", "artifact-verify", "admission-control", "render-evidence"):
        raise ValueError("s2_worker_operation")
    if operation not in ("prepare-step", "contour", "text", "compile", "verify", "identity", "artifact-verify", "admission-control", "render-evidence"):
        raise ValueError("s1_worker_operation")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("s1_worker_timeout")
    mode = "independent_dev"
    owner = getattr(process, "__self__", None)
    if owner is not None:
        import importlib
        session_type = importlib.import_module(("tools." if __package__ else "") + "cad_verify_v4_trials").TrialSession
        if isinstance(session_type, type) and isinstance(owner, session_type):
            mode = owner.mode
    out = ledger.new_directory(safe_path(out))
    job = dict(operation=operation, out=str(out), **fields)
    if profile != PROFILE:
        job["profile"] = profile
    for key in ("manifest", "prepared", "plan", "card", "context", "bundle"):
        if key in job:
            job[key] = str(safe_path(job[key], regular=True))
    if "candidate_dir" in job:
        job["candidate_dir"] = str(safe_path(job["candidate_dir"]))
    execution_snapshot = None
    if operation == "artifact-verify":
        if "runtime_binding" in job:
            raise ValueError("artifact_runtime_binding_is_collector_owned")
        import importlib
        adapter = importlib.import_module(("tools." if __package__ else "") + "cad_verify_v4_artifacts")
        _, _, extensions = adapter.load_bundle(job["bundle"], profile=profile)
        execution_snapshot = runtime_binding.capture(ROOT, extension_paths=extensions.values())
        runtime_path = out.parent / (out.name + ".runtime.json")
        ledger.write_json(runtime_path, execution_snapshot)
        job["runtime_binding"] = str(runtime_path)
    job_path = out.parent / (out.name + ".job.json")
    ledger.write_json(job_path, job)
    argv = live.trusted_worker_argv(job_path, root=ROOT)
    work_id = "work-%06d" % (journal.sequence + 1)
    inputs = {key: ledger.file_sha(value) for key, value in job.items()
              if key in ("manifest", "prepared", "plan", "card", "context", "bundle", "runtime_binding")}
    code_bindings = implementation_bindings(ROOT, profile=profile)
    journal.append("work_started", work_id=work_id, work_kind=operation, profile=profile,
                   inputs=inputs, code_bindings=code_bindings, submitted_sha256=ledger.file_sha(job_path),
                   argv=argv, cwd=str(ROOT), stdin="DEVNULL", evidence_mode=mode)
    captures = {key: ledger.StreamCapture(out.parent / (out.name + "." + key + ".bin"))
                for key in ("stdout", "stderr")}
    tick, failure, code = time.monotonic(), None, None
    try:
        code = (process or live.stream_native_process)(argv, captures, cwd=ROOT, timeout=timeout)
    except BaseException as exc:
        failure = exc
    streams = {}
    for key, capture in captures.items():
        streams[key] = capture.finish()
        if failure:
            streams[key].update(complete=False, missing_reason="native_work_interrupted")
    result_path = out / ("verify-result.json" if operation == "verify" else "result.json")
    result, parse_error = None, None
    try:
        if result_path.exists():
            result = ledger.read_json(safe_path(result_path, regular=True))
            if not isinstance(result, dict) or result.get("status") not in ("PASS", "FAIL", "UNVERIFIED"):
                raise ValueError("s1_worker_result_contract")
            if result.get("profile") != profile:
                raise ValueError("native_result_profile_mismatch")
            if (result["status"] == "FAIL" and result.get("error_type") in
                    {"ImportError", "ModuleNotFoundError", "OSError", "PermissionError", "FileNotFoundError", "MemoryError"}):
                raise ValueError("s1_native_environment_failure:" + result["error_type"])
            if process is None:
                native = getattr(captures["stdout"], "native_evidence", None)
                if (not isinstance(native, dict) or native.get("owned_pid") != result.get("owned_pid")
                        or native.get("cleanup_status") != "exited"
                        or result.get("gui_up") != 0 or result.get("document_closed") is not True):
                    raise ValueError("s1_owned_headless_cleanup_evidence")
            if implementation_bindings(ROOT, profile=profile) != code_bindings:
                raise ValueError("s1_native_implementation_changed_during_work")
            if execution_snapshot is not None:
                runtime_binding.verify(execution_snapshot, root=ROOT, extension_paths=extensions.values())
                record = dict(path=str(runtime_path), sha256=ledger.file_sha(runtime_path), bytes=runtime_path.stat().st_size)
                if result.get("runtime_binding") != record or ledger.read_json(runtime_path) != execution_snapshot:
                    raise ValueError("artifact_execution_runtime_binding_mismatch")
        else:
            parse_error = "native_result_missing"
    except (OSError, ValueError, TypeError) as exc:
        parse_error = str(exc)
    if not failure and not parse_error and (code not in (0, 1) or result is None
            or (code == 0) != (result["status"] == "PASS")):
        parse_error = "s1_native_worker_exit_status_mismatch"
    journal.append("work_finished", work_id=work_id, work_kind=operation, profile=profile,
                   wall_s=time.monotonic()-tick, exit_code=code, streams=streams,
                   outputs=_hashes(out), status=result["status"] if result and not failure and not parse_error else "INCOMPLETE",
                   failure=str(failure) if failure else parse_error, live_calls=0,
                   native_evidence=getattr(captures["stdout"], "native_evidence", None), evidence_mode=mode)
    if failure:
        raise OSError("s1_native_work_interrupted") from failure
    if (code not in (0, 1) or parse_error or result is None
            or (code == 0) != (result["status"] == "PASS")):
        raise ValueError(parse_error or "s1_native_worker_failed:%s" % code)
    return result


def _manifest_inputs(manifest_path, prepared_path=None, *, profile=PROFILE, execution=None):
    inputs, _ = _modules()
    _stage(profile)
    manifest_path = safe_path(manifest_path, regular=True)
    manifest = inputs.load_manifest(manifest_path)
    if manifest["profile"] != profile:
        raise ValueError("capability_input_profile_mismatch")
    if execution is None:
        if manifest.get("evidence_mode") != "independent_dev":
            raise Stop("s1_implementation_accepts_independent_dev_only")
    else:
        import importlib
        scopes = importlib.import_module(("tools." if __package__ else "") + "cad_verify_v4_trials")
        if not isinstance(execution, (scopes.PlanExecution, scopes.TrialSession)):
            raise Stop("s1_authorized_execution_scope_required")
        execution.admitted_inputs(manifest)
    prepared = inputs.verify_prepared(safe_path(prepared_path, regular=True), manifest_path) if prepared_path else None
    return manifest_path, manifest, prepared


def prepare(operation, manifest_path, run_dir, *, asset_id=None, recipe_path=None,
            font_id=None, text=None, height_mm=None, process=None, profile=PROFILE):
    manifest_path, _, _ = _manifest_inputs(manifest_path, profile=profile)
    fields = dict(manifest=str(manifest_path))
    if profile in ("c-s2", "c-s3") and operation != "prepare-step":
        raise ValueError("s2_preparation_operation")
    if operation in ("prepare-step", "contour"):
        if not isinstance(asset_id, str) or not asset_id or recipe_path is None:
            raise ValueError("s1_preparation_asset_recipe_required")
        recipe = ledger.read_json(safe_path(recipe_path, regular=True))
        _modules()[1].validate_document(recipe, "step-recipe" if operation == "prepare-step" else "contour-recipe",
                                        profile=profile)
        fields.update(asset_id=asset_id, recipe=recipe)
    elif operation == "text":
        fields.update(font_id=font_id, text=text, height_mm=height_mm)
    else:
        raise ValueError("s1_preparation_operation")
    out = ledger.new_directory(safe_path(run_dir))
    with ledger.Journal(out / "ledger.jsonl", out.name, profile[2:] + "-development") as journal:
        tick = time.monotonic()
        journal.append("run_started", profile=profile, evidence_mode="independent_dev", live_calls=0)
        try:
            result = native_work(operation, out / "native", journal, process=process, profile=profile, **fields)
        except BaseException as exc:
            journal.append("run_finished", wall_s=time.monotonic()-tick, active_s=time.monotonic()-tick,
                           stop_reason=str(exc), live_calls=0)
            raise
        journal.append("run_finished", wall_s=time.monotonic()-tick, active_s=time.monotonic()-tick,
                       stop_reason=None, live_calls=0)
    summary = dict(schema="cad-harness.preparation.v4c", profile=profile,
                   evidence_mode="independent_dev", status=result["status"],
                   result_path=str(out / "native/result.json"), result=result,
                   live_calls=0, live_cad_runs=0, native_work=1, holdout="not_run", pilot="not_run")
    ledger.write_json(out / "summary.json", summary)
    return summary


def merge_prepared(manifest_path, packet_paths, output_path, *, profile=PROFILE):
    """Combine immutable prepared packets only after rechecking every source."""
    manifest_path, _, _ = _manifest_inputs(manifest_path, profile=profile)
    inputs, _ = _modules()
    assets = {}
    for path in packet_paths:
        packet = inputs.verify_prepared(safe_path(path, regular=True), manifest_path)
        if set(assets) & set(packet["assets"]):
            raise ValueError("s1_duplicate_prepared_asset")
        assets.update(packet["assets"])
    if not assets:
        raise ValueError("s1_prepared_packets_required")
    result = dict(schema="cad-harness.prepared.v4c", profile=profile,
                  source_manifest_sha256=ledger.file_sha(manifest_path), assets=assets)
    inputs.verify_prepared(result, manifest_path)
    ledger.write_json(safe_path(output_path), result)
    return result


def compile_candidate(manifest_path, prepared_path, plan_path, card_path, run_dir, *,
                      candidate_dir=None, process=None, journal=None, timeout=300, budget=None, profile=PROFILE,
                      execution=None):
    manifest_path, _, prepared = _manifest_inputs(manifest_path, prepared_path, profile=profile, execution=execution)
    _, plans = _modules()
    plan_path, card_path = safe_path(plan_path, regular=True), safe_path(card_path, regular=True)
    plans.validate_plan(ledger.read_json(plan_path), manifest_path, prepared, profile=profile)
    plans.validate_judge_card(ledger.read_json(card_path), profile=profile)
    if budget is None:
        budget = Budget(4)
        if candidate_dir is None:
            budget.cad()
    if journal is None:
        out = ledger.new_directory(safe_path(run_dir))
        with ledger.Journal(out / "ledger.jsonl", out.name, profile[2:] + "-development") as own:
            tick = time.monotonic()
            own.append("run_started", profile=profile, evidence_mode="independent_dev", live_calls=0)
            try:
                result = compile_candidate(manifest_path, prepared_path, plan_path, card_path,
                                           out / "candidate", candidate_dir=candidate_dir,
                                           process=process, journal=own, timeout=timeout, budget=budget, profile=profile,
                                           execution=execution)
            except BaseException as exc:
                own.append("run_finished", wall_s=time.monotonic()-tick,
                           active_s=time.monotonic()-tick, stop_reason=str(exc), live_calls=0)
                raise
            own.append("run_finished", wall_s=time.monotonic()-tick,
                       active_s=time.monotonic()-tick, stop_reason=None, live_calls=0)
        ledger.write_json(out / "summary.json", result)
        return result
    fields = dict(manifest=str(manifest_path), prepared=str(safe_path(prepared_path, regular=True)),
                  plan=str(plan_path), card=str(card_path))
    if candidate_dir is None:
        build = native_work("compile", run_dir, journal, process=process, profile=profile,
                            timeout=min(timeout, budget.cad_timeout()), **fields)
        if build["status"] != "PASS":
            return dict(schema="cad-harness.candidate.v4c", profile=profile, status=build["status"],
                        compile=build, verification=None, live_calls=0, native_work=1,
                        evidence_mode="independent_dev", holdout="not_run", pilot="not_run")
        source = safe_path(run_dir)
    else:
        source = safe_path(candidate_dir)
        build = ledger.read_json(safe_path(source / "result.json", regular=True))
    verify_out = safe_path(str(run_dir) + "-verify")
    verification_timeout = (budget.verification_timeout() if execution is not None
                            else min(90 if budget.stage == "repair" else 300, budget.remaining()))
    verify = native_work("verify", verify_out, journal, process=process, profile=profile,
                         timeout=min(timeout, verification_timeout), candidate_dir=str(source), **fields)
    budget.remaining()
    return dict(schema="cad-harness.candidate.v4c", profile=profile, status=verify["status"],
                compile=build, verification=verify, candidate_dir=str(source),
                live_calls=0, native_work=1 if candidate_dir is not None else 2,
                evidence_mode="independent_dev", holdout="not_run", pilot="not_run",
                final_v4_ready=False)


def repair_observations(result, *, profile=PROFILE):
    """Send measured diagnostics, never checker targets, cards or file locations."""
    absent = object()
    denied = ("target", "expected", "path", "card", "recipe", "mask", "source", "search_extent")
    def numeric(value):
        if value is None or type(value) in (bool, int, float):
            return value
        if isinstance(value, list):
            return [item for child in value if (item := numeric(child)) is not absent]
        if isinstance(value, dict):
            return {key: item for key, child in value.items()
                    if isinstance(key, str) and not any(word in key.casefold() for word in denied)
                    and (item := numeric(child)) is not absent}
        return absent
    def visible(value):
        item = numeric(value)
        return None if item is absent else item
    checks = []
    verification = result.get("verification") or {}
    judgement = verification.get("judgement") or {}
    for row in judgement.get("checks", []):
        checks.append(dict(id=row["id"], metric=row["metric"], status=row["status"],
                           measured=visible(row.get("measured")), uncertainty=visible(row.get("uncertainty"))))
    compiled = result.get("compile") or {}
    import re
    native_error = compiled.get("error", "")
    error_code = native_error if isinstance(native_error, str) and re.fullmatch(r"[a-z][a-z0-9_]{1,100}", native_error) else None
    geometry = {key: value for key, value in (compiled.get("measurements") or {}).items()
                if key in ("bounds_mm", "volume_mm3", "solids")}
    return dict(schema="cad-harness.observations.v4c", profile=profile,
                status=result["status"], geometry=visible(geometry), checks=checks,
                compile_failed=compiled.get("status") == "FAIL",
                compile_error_code=error_code,
                verification_available=bool(verification))


class PlanReplay:
    """Explicit fake-model responses; no physical attempt, billing or provider claim."""
    def __init__(self, path, request_raw, prepared_path, *, profile=PROFILE):
        _stage(profile)
        document = ledger.read_json(safe_path(path, regular=True))
        required = {"schema", "profile", "request_sha256", "prepared_sha256", "responses"}
        if (not isinstance(document, dict) or set(document) != required
                or document.get("schema") != "cad-harness.plan-replay.v4c"
                or document.get("profile") != profile
                or document.get("request_sha256") != ledger.sha(request_raw)
                or document.get("prepared_sha256") != ledger.file_sha(prepared_path)
                or not isinstance(document.get("responses"), list)):
            raise ValueError("s1_replay_binding")
        for row in document["responses"]:
            if (not isinstance(row, dict) or set(row) != {"purpose", "text"}
                    or row["purpose"] not in ("source", "parse_repair", "repair")
                    or not isinstance(row["text"], str)):
                raise ValueError("s1_replay_response")
        self.responses = iter(document["responses"])

    def __call__(self, request, runtime_data, *, purpose, timeout):
        row = next(self.responses, None)
        if row is None or row["purpose"] != purpose:
            raise ValueError("s1_replay_exhausted_or_out_of_order")
        return row["text"]


def request(request_path, card_path, run_dir, *, manifest_path, prepared_path,
            replay=None, model=None, selection=None, process=None, root=ROOT, profile=PROFILE, execution=None):
    """Typed plan route using the existing P1/R1/CAD2/active-time invariants."""
    if replay is None and model is None:
        raise Stop("s1_development_replay_required_no_live_authorization")
    if replay is not None and model is not None:
        raise ValueError("s1_replay_or_injected_model_not_both")
    request_path, manifest_path, prepared_path, card_path = (
        safe_path(path, regular=True) for path in (request_path, manifest_path, prepared_path, card_path))
    input_hashes = {path: ledger.file_sha(path) for path in
                    (request_path, manifest_path, prepared_path, card_path)}
    def check_request_inputs():
        if any(ledger.file_sha(safe_path(path, regular=True)) != digest for path, digest in input_hashes.items()):
            raise Stop("s1_request_inputs_changed")
    manifest_path, _, prepared = _manifest_inputs(manifest_path, prepared_path, profile=profile, execution=execution)
    inputs, plans = _modules()
    request_raw = request_path.read_bytes()
    request_text = request_raw.decode("utf-8")
    plans.validate_judge_card(ledger.read_json(card_path), profile=profile)
    adapter = agent.PlanSkillAdapter(agent.bundle(root, profile=profile), request_text,
                                     manifest_path, prepared, selection)
    model = model if model is not None else PlanReplay(replay, request_raw, prepared_path, profile=profile)
    out = ledger.new_directory(safe_path(run_dir))
    budget = execution.budget if execution is not None else Budget(4)
    active_clock = execution.clock if execution is not None else time.monotonic
    mode = execution.mode if execution is not None else "unit_mock"
    response_count, result, error = 0, None, None
    with ledger.Journal(out / "ledger.jsonl", out.name,
                        profile[2:] + ("-authorized" if execution is not None else "-development")) as journal:
        tick = time.monotonic()
        active_tick = active_clock()
        journal.append("run_started", profile=profile, evidence_mode=mode, live_calls=0,
                       skill_sha256=ledger.sha(agent.bundle(root, profile=profile)),
                       request_sha256=input_hashes[request_path], input_manifest_sha256=input_hashes[manifest_path],
                       prepared_sha256=input_hashes[prepared_path], card_sha256=input_hashes[card_path])
        def generate(purpose, observations=None):
            nonlocal response_count
            check_request_inputs()
            data = dict(target="plan", stage="parse_repair" if purpose == "parse_repair" else budget.stage,
                        inputs=adapter.inputs, selection=adapter.selection)
            if observations is not None:
                data["observations"] = repair_observations(observations, profile=profile) if purpose == "repair" else observations
            adapter.context(data)
            if inputs.model_inputs(prepared, manifest_path) != adapter.inputs:
                raise ValueError("plan_runtime_provenance")
            timeout = budget.sol_timeout(purpose)
            budget.call(purpose)
            envelope = dict(request=request_text, runtime_data=data)
            number = response_count + 1
            ledger.write_json(out / ("payload-%d.json" % number), envelope)
            started, active_started = time.monotonic(), active_clock()
            text = model(request_text, data, purpose=purpose, timeout=timeout)
            if not isinstance(text, str):
                raise ValueError("s1_model_response_text_required")
            if active_clock()-active_started > timeout:
                raise Stop("s1_model_response_timeout")
            response_count = number
            with (out / ("response-%d.txt" % number)).open("x", encoding="utf-8", newline="") as file:
                file.write(text)
            journal.append("model_response" if execution is not None else "replay_response", profile=profile, purpose=purpose,
                           response_index=number, wall_s=time.monotonic()-started,
                           active_s=active_clock()-active_started,
                           payload_sha256=ledger.file_sha(out / ("payload-%d.json" % number)),
                           response_sha256=ledger.sha(text.encode("utf-8")),
                           evidence_mode=mode, physical_model_attempt=mode == "live",
                           live_calls=1 if mode == "live" else 0)
            return text
        def parse(text):
            try:
                return plans.validate_plan(cad_agent.loads(text), manifest_path, prepared, profile=profile)
            except (ValueError, KeyError, TypeError) as exc:
                if budget.counts["parse_repair"]:
                    raise
                repaired = generate("parse_repair", {"invalid_response": text, "error": str(exc)})
                return plans.validate_plan(cad_agent.loads(repaired), manifest_path, prepared, profile=profile)
        try:
            plan = parse(generate("source"))
            for attempt in ((1,) if execution is not None and budget.one_attempt else (1, 2)):
                plan_path = out / ("plan-%d.json" % attempt)
                ledger.write_json(plan_path, plan)
                check_request_inputs()
                budget.cad()
                result = compile_candidate(manifest_path, prepared_path, plan_path, card_path,
                                           out / ("candidate-%d" % attempt), journal=journal,
                                           process=process, timeout=budget.cad_timeout(), budget=budget, profile=profile,
                                           execution=execution)
                check_request_inputs()
                if result["status"] == "PASS" or attempt == 2 or (execution is not None and budget.one_attempt):
                    break
                budget.begin_repair()
                plan = parse(generate("repair", result))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            error = str(exc)
        journal.append("run_finished", wall_s=time.monotonic()-tick,
                       active_s=active_clock()-active_tick, stop_reason=error,
                       live_calls=execution.live_calls if execution is not None else 0)
    value = dict(schema="cad-harness.request.v4c", profile=profile,
                 evidence_mode=mode, status=result["status"] if result and not error else (
                     execution.error_status(error) if execution is not None else "INCOMPLETE"),
                 request_sha256=ledger.sha(request_raw), result=result, stop_reason=error,
                 replayed_responses=response_count if execution is None else 0,
                 physical_model_attempts=execution.physical_attempts if execution is not None else 0,
                 live_calls=execution.live_calls if execution is not None else 0,
                 live_cad_runs=budget.attempts if mode == "live" else 0,
                 cad_attempts=budget.attempts, settings=budget.settings(),
                 holdout="not_run", pilot="not_run", final_v4_ready=False,
                 costs=ledger.summarize(out / "ledger.jsonl"))
    ledger.write_json(out / "summary.json", value)
    return value, 0 if value["status"] == "PASS" else 1


def implementation_bindings(root=ROOT, *, profile=PROFILE):
    root = safe_path(root)
    _stage(profile)
    files = freezing.bindings(root)
    files.update(c2_recipe.bindings(root))
    names = ["capability-policy.json", "PLAN-V4-ADDENDUM-C.md", "original-profile-snapshot.zip",
             "dev-c2-production/generate.py", "dev-c2-multipiece/generate.py"]
    if profile == "c-s2":
        names += ["policy-c-s2.json", "s1-profile-snapshot.zip", "dev-c-s2/generate.py"]
    if profile == "c-s3":
        names += ["policy-c-s3.json", "s1-profile-snapshot.zip", "s2-profile-snapshot.zip",
                  "dev-c-s3/generate.py"]
    for name in names:
        path = safe_path(root / DESIGN / name, regular=True)
        files[path.relative_to(root).as_posix()] = ledger.file_sha(path)
    for path in sorted((root / DESIGN / "schemas").glob("*.json")):
        path = safe_path(path, regular=True)
        files[path.relative_to(root).as_posix()] = ledger.file_sha(path)
    return dict(sorted(files.items()))


def implementation_lock(run_dir, *, root=ROOT, manifest_path=None, prepared_path=None,
                        card_path=None, recipe_paths=(), process=None, profile=PROFILE):
    """Stage development lock only, never partial/final trial authorization."""
    root = safe_path(root)
    readiness = preflight(root, profile=profile)
    dev = {}
    if manifest_path is not None:
        manifest_path, _, _ = _manifest_inputs(manifest_path, prepared_path, profile=profile)
        dev["input_manifest"] = dict(path=str(manifest_path), sha256=ledger.file_sha(manifest_path))
        if prepared_path is not None:
            prepared_path = safe_path(prepared_path, regular=True)
            dev["prepared"] = dict(path=str(prepared_path), sha256=ledger.file_sha(prepared_path))
    elif prepared_path is not None:
        raise ValueError("s1_prepared_requires_input_manifest")
    if card_path is not None:
        card_path = safe_path(card_path, regular=True)
        _modules()[1].validate_judge_card(ledger.read_json(card_path), profile=profile)
        dev["judge_card"] = dict(path=str(card_path), sha256=ledger.file_sha(card_path))
    recipes = {}
    import re
    for value in recipe_paths:
        path = safe_path(value, regular=True)
        recipe_id = path.stem
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", recipe_id):
            raise ValueError("s1_recipe_id_not_canonical")
        if recipe_id in recipes:
            raise ValueError("s1_recipe_id_duplicate")
        recipe = ledger.read_json(path)
        kinds = {"cad-harness.step-recipe.v4c": "step-recipe",
                 "cad-harness.contour-recipe.v4c": "contour-recipe"}
        kind = kinds.get(recipe.get("schema")) if isinstance(recipe, dict) else None
        if kind is None:
            raise ValueError("s1_recipe_schema")
        _modules()[1].validate_document(recipe, kind, profile=profile)
        recipes[recipe_id] = dict(path=str(path), sha256=ledger.file_sha(path))
    out = ledger.new_directory(safe_path(run_dir))
    with ledger.Journal(out / "ledger.jsonl", out.name, profile[2:] + "-implementation-lock") as journal:
        identity = native_work("identity", out / "runtime", journal, process=process, profile=profile)
    if identity["status"] != "PASS":
        raise Stop("s1_native_runtime_identity_unverified")
    value = dict(schema="cad-harness.capability-manifest.v4c", profile=profile,
                 stage="implementation", status="offline_locked", authorization=None,
                 freeze_dir=str(out), files=implementation_bindings(root, profile=profile),
                 skill_sha256=readiness["skill_sha256"], policy_sha256=readiness["policy_sha256"],
                 host=freezing._host(), runtime=identity,
                 original_profile_snapshot=dict(path=DESIGN + "/original-profile-snapshot.zip",
                                                sha256=readiness["original_profile_snapshot_sha256"]),
                 generators=json.loads(json.dumps(PHASE_MODELS)), judge=dict(JUDGE), recipes=recipes,
                 dev=dev, pending_final_freeze=list(_stage(profile)["pending"]), final_v4_ready=False)
    if profile in ("c-s2", "c-s3"):
        prior = "c-s2" if profile == "c-s3" else "c-s1"
        value["prior_stage_snapshot"] = dict(profile=prior, path=DESIGN + "/" + prior[2:] + "-profile-snapshot.zip",
                                             sha256=readiness["prior_stage_snapshot_sha256"])
    ledger.write_json(out / "SHA256.json", value)
    value["sha256_file"] = ledger.file_sha(out / "SHA256.json")
    _modules()[1].validate_document(value, "capability", profile=profile)
    ledger.write_json(out / "manifest.json", value)
    return value


def verify_implementation_lock(manifest_path, *, root=ROOT, profile=None):
    path = safe_path(manifest_path, regular=True)
    value = ledger.read_json(path)
    profile = value.get("profile") if profile is None and isinstance(value, dict) else profile
    _stage(profile)
    _modules()[1].validate_document(value, "capability", profile=profile)
    required = {"schema", "profile", "stage", "status", "authorization", "freeze_dir", "files",
                "skill_sha256", "policy_sha256", "host", "runtime", "original_profile_snapshot",
                "generators", "judge", "recipes", "dev", "pending_final_freeze", "final_v4_ready", "sha256_file"}
    if profile in ("c-s2", "c-s3"):
        required.add("prior_stage_snapshot")
    if (not isinstance(value, dict) or set(value) != required
            or value.get("schema") != "cad-harness.capability-manifest.v4c"
            or value.get("profile") != profile or value.get("stage") != "implementation"
            or value.get("status") != "offline_locked" or value.get("authorization") is not None
            or value.get("final_v4_ready") is not False or value.get("generators") != PHASE_MODELS
            or value.get("judge") != JUDGE
            or value.get("freeze_dir") != str(path.parent) or path.name != "manifest.json"):
        raise Stop("s1_implementation_manifest_contract")
    sha_path = safe_path(path.parent / "SHA256.json", regular=True)
    payload = {key: item for key, item in value.items() if key != "sha256_file"}
    if ledger.file_sha(sha_path) != value["sha256_file"] or ledger.read_json(sha_path) != payload:
        raise Stop("s1_implementation_sha_mismatch")
    if value["files"] != implementation_bindings(root, profile=profile):
        raise Stop("s1_implementation_file_binding_mismatch")
    ready = preflight(root, profile=profile)
    if (value["host"] != freezing._host() or value["skill_sha256"] != ready["skill_sha256"]
            or value["policy_sha256"] != ready["policy_sha256"]):
        raise Stop("s1_implementation_identity_mismatch")
    if profile in ("c-s2", "c-s3"):
        prior = "c-s2" if profile == "c-s3" else "c-s1"
        if value["prior_stage_snapshot"] != dict(profile=prior,
                path=DESIGN + "/" + prior[2:] + "-profile-snapshot.zip",
                sha256=ready["prior_stage_snapshot_sha256"]):
            raise Stop("prior_stage_snapshot_changed")
    for collection in (value["recipes"], value["dev"]):
        if not isinstance(collection, dict):
            raise Stop("s1_implementation_dependency_contract")
        for record in collection.values():
            if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
                raise Stop("s1_implementation_dependency_contract")
            if ledger.file_sha(safe_path(record["path"], regular=True)) != record["sha256"]:
                raise Stop("s1_implementation_dependency_changed")
    if "input_manifest" in value["dev"]:
        _manifest_inputs(value["dev"]["input_manifest"]["path"],
                         value["dev"].get("prepared", {}).get("path"), profile=profile)
    runtime = value["runtime"]
    if not isinstance(runtime, dict) or runtime.get("status") != "PASS":
        raise Stop("s1_runtime_identity_contract")
    # Worker identity is an artifact, with binaries bound as explicit records.
    pinned = safe_path(cad_run.FREECAD_DIR)
    dependency_files = runtime.get("runtime", {}).get("files")
    if not isinstance(dependency_files, dict) or not dependency_files:
        raise Stop("s1_runtime_dependency_files_missing")
    for name, digest in dependency_files.items():
        binary = safe_path(name, regular=True)
        if not binary.is_relative_to(pinned) or ledger.file_sha(binary) != digest:
            raise Stop("s1_runtime_dependency_changed")
    return value


def run_development(replay_path, run_dir, *, profile=PROFILE):
    """Execute a declared independent-dev mock batch, not a pilot/holdout."""
    _stage(profile)
    replay_path = safe_path(replay_path, regular=True)
    document = ledger.read_json(replay_path)
    if (not isinstance(document, dict)
            or set(document) != {"schema", "profile", "evidence_mode", "entries"}
            or document.get("schema") != "cad-harness.plan-batch-replay.v4c"
            or document.get("profile") != profile
            or document.get("evidence_mode") != "independent_dev"
            or not isinstance(document.get("entries"), list) or not document["entries"]):
        raise ValueError("s1_development_batch_contract")
    entries, identifiers = [], set()
    base = replay_path.parent
    for row in document["entries"]:
        required = {"id", "request", "card", "input_manifest", "prepared", "replay"}
        if (not isinstance(row, dict) or not required <= set(row)
                or set(row) - required - {"selection"} or not isinstance(row["id"], str)
                or not row["id"] or row["id"] in identifiers):
            raise ValueError("s1_development_entry_contract")
        identifiers.add(row["id"])
        entry = {"id": row["id"]}
        names = {key: row[key] for key in sorted(set(row) - {"id"})}
        for name in names.values():
            if (not isinstance(name, str) or not name or ":" in name
                    or Path(name).is_absolute()
                    or any(part in ("", ".", "..") for part in name.replace("\\", "/").split("/"))):
                raise ValueError("s1_development_entry_path")
        for key, name in names.items():
            path = safe_path(base / name, regular=True)
            if not path.is_relative_to(base):
                raise ValueError("s1_development_entry_outside_bundle")
            entry[key] = path
        _manifest_inputs(entry["input_manifest"], entry["prepared"], profile=profile)
        entries.append(entry)
    out = ledger.new_directory(safe_path(run_dir))
    rows = []
    with ledger.Journal(out / "ledger.jsonl", out.name, profile[2:] + "-development") as journal:
        tick = time.monotonic()
        journal.append("run_started", profile=profile, evidence_mode="unit_mock", live_calls=0)
        for index, entry in enumerate(entries, 1):
            journal.append("episode_started", episode_id=entry["id"], route="plan")
            started = time.monotonic()
            try:
                selection = ledger.read_json(entry["selection"]) if "selection" in entry else None
                value, _ = request(entry["request"], entry["card"], out / ("episode-%03d" % index),
                                   manifest_path=entry["input_manifest"], prepared_path=entry["prepared"],
                                   replay=entry["replay"], selection=selection, profile=profile)
                rows.append(dict(id=entry["id"], status=value["status"],
                                 summary_path=str(out / ("episode-%03d/summary.json" % index))))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                rows.append(dict(id=entry["id"], status="INCOMPLETE", reason=str(exc)))
            journal.append("episode_finished", episode_id=entry["id"], status=rows[-1]["status"],
                           wall_s=time.monotonic()-started, active_s=time.monotonic()-started)
        journal.append("run_finished", wall_s=time.monotonic()-tick,
                       active_s=time.monotonic()-tick, stop_reason=None)
    value = dict(schema="cad-harness.development-batch.v4c", profile=profile,
                 status="PASS" if all(row["status"] == "PASS" for row in rows) else "INCOMPLETE",
                 evidence_mode="unit_mock", entries=rows, physical_model_attempts=0,
                 live_calls=0, holdout="not_run", pilot="not_run", final_v4_ready=False)
    ledger.write_json(out / "summary.json", value)
    return value
