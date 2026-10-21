"""Exclusive, offline VERIFY v4 freezes; authorization is supplied evidence only.

SHA256.json binds the complete manifest payload. Neither commitment references nor
quota snapshots are opened, and the only executable invocation is omp --version.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess

if __package__:
    from . import cad_verify_v4_agent as agent, cad_verify_v4_ledger as ledger
    from . import cad_run
    from .cad_verify_guard import Stop
else:
    import cad_verify_v4_agent as agent, cad_verify_v4_ledger as ledger
    import cad_run
    from cad_verify_guard import Stop

ROOT = Path(__file__).resolve().parents[1]
DESIGN = "design/cad-harness-verify-v4"
MODEL = "openai-codex/gpt-6.1-sol"
THINKING = "xhigh"
REQUIRED_HOST = "DPC-019"
REQUIRED_FREECAD = "1.1.4"
FIXED_FILES = (
    "skills/freecad-modeling/SKILL.md",
    "design/cad-harness-mvp/build-schema.json",
    "design/cad-harness-mvp/eval-v1/schema.json",
    "design/cad-harness-verify-v3/gold-schema.json",
    *(DESIGN + "/" + name for name in (
        "policy.json", "ledger.schema.json", "pilot-rubric.json",
        "PLAN-V4-CONSENSUS.md", "DECISIONS.md", "PLAN-V4-UPDATE-U1.md")),
)
LIMITS = dict(
    route_caps=dict(source=4, spec=3, ask=1, completion=4, offline=0, mvp=3),
    active_budgets_s=dict(episode=900, initial=450, repair=450, repair_sol=180,
                          parse_repair=60, initial_cad=300, repair_cad=90,
                          repair_reimport=90, cleanup=30),
    slots=dict(parse_repair_shared=1, repair=1, cad=2),
    quota=dict(consult_percent=55, stop_percent=60, max_snapshot_age_s=300),
    proposed_reservations=dict(holdout=163, pilot=40, total=203, borrowing=False),
)


def _path(path):
    path = Path(path).absolute()
    if any(part.casefold().rstrip(" .") in ("v4-holdout-private", "pilot-user") for part in path.parts):
        raise Stop("private_holdout_path_forbidden")
    if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()) for p in (path, *path.parents)):
        raise Stop("linked_freeze_path")
    resolved = path.resolve()
    if any(part.casefold().rstrip(" .") in ("v4-holdout-private", "pilot-user") for part in resolved.parts):
        raise Stop("private_holdout_path_forbidden")
    return resolved


def _repo_file(root, name):
    path = _path(root / name)
    if not path.is_relative_to(root) or not path.is_file():
        raise Stop("freeze_binding_missing_or_external:" + str(name))
    return path


def _file_sha(path):
    try:
        return ledger.file_sha(path)
    except OSError as error:
        raise Stop("freeze_file_unreadable:" + str(path)) from error


def _read_json(path):
    try:
        return ledger.read_json(path)
    except OSError as error:
        raise Stop("freeze_json_unreadable:" + str(path)) from error


def _same(left, right):
    # JSON types matter: True is not the numeric limit 1.
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def bindings(root=ROOT):
    """Enumerate the required set independently of any supplied manifest map."""
    root = _path(root)
    names = set(FIXED_FILES)
    for folder, python_only in (("tools", True), ("skills/cad-harness-v4", False)):
        base = _path(root / folder)
        if not base.is_dir():
            raise Stop("freeze_binding_directory_missing:" + folder)
        for path in base.rglob("*"):
            if path.is_symlink():
                raise Stop("linked_freeze_binding")
            if path.is_file() and (not python_only or path.suffix == ".py"):
                names.add(path.relative_to(root).as_posix())
    required_skill = {"skills/cad-harness-v4/" + name
                      for name in ("SKILL.md", "modeling.md", "contracts.md")}
    if not required_skill <= names or not any(name.startswith("tools/") for name in names):
        raise Stop("freeze_binding_set_empty_or_incomplete")
    return {name: _file_sha(_repo_file(root, name)) for name in sorted(names)}


def _policy(root, policy_path):
    canonical = _repo_file(root, DESIGN + "/policy.json")
    policy_path = _path(policy_path)
    policy = _read_json(policy_path)
    if not isinstance(policy, dict) or not _same(policy, _read_json(canonical)):
        raise Stop("policy_override_not_skill_bound")
    if (policy.get("schema") != "cad-harness.policy.v4"
            or type(policy.get("live_authorized_calls")) is not int
            or policy["live_authorized_calls"] != 0
            or policy.get("phase") != "p12_offline_only"
            or policy.get("host") != REQUIRED_HOST
            or policy.get("freecad") != REQUIRED_FREECAD
            or policy.get("headless_only") is not True
            or any(not _same(policy.get(key), value) for key, value in LIMITS.items())):
        raise Stop("freeze_policy_drift")
    clock = policy.get("clock")
    holdout = policy.get("holdout")
    overload = policy.get("overload")
    if (not isinstance(clock, dict)
            or clock.get("exclude_verified_rejected_attempt_and_backoff_from_active") is not True
            or clock.get("include_all_wall_time") is not True
            or clock.get("suite_wall_deadline_s") is not None
            or clock.get("live_confirmation") is not None
            or not isinstance(holdout, dict)
            or any(not _same(holdout.get(k), v) for k, v in dict(items=60, core=51, segments=1,
                                                               resume=False, retake=False).items())
            or not _same(overload, dict(code="server_overloaded", structured_only=True,
                                       requires_no_output=True, wait_s=600, retry_cap=None,
                                       accepted_call_charge=0, pr_charge=0, identical_resend=True))):
        raise Stop("freeze_policy_drift")
    if (_repo_file(root, "skills/cad-harness-v4/modeling.md").read_bytes()
            != _repo_file(root, "skills/freecad-modeling/SKILL.md").read_bytes()):
        raise Stop("modeling_prose_drift")
    return _file_sha(canonical)


def _binary_version(path):
    """Read Windows PE version resources; never execute a CAD process."""
    if not hasattr(ctypes, "WinDLL"):
        return None
    try:
        api = ctypes.WinDLL("version", use_last_error=True)
        api.GetFileVersionInfoSizeW.argtypes = (wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD))
        api.GetFileVersionInfoSizeW.restype = wintypes.DWORD
        api.GetFileVersionInfoW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID)
        api.GetFileVersionInfoW.restype = wintypes.BOOL
        api.VerQueryValueW.argtypes = (wintypes.LPCVOID, wintypes.LPCWSTR,
                                      ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.UINT))
        api.VerQueryValueW.restype = wintypes.BOOL
        size = api.GetFileVersionInfoSizeW(str(path), None)
        if not size:
            return None
        data = ctypes.create_string_buffer(size)
        if not api.GetFileVersionInfoW(str(path), 0, size, data):
            return None
        pointer, length = wintypes.LPVOID(), wintypes.UINT()
        if not api.VerQueryValueW(data, "\\", ctypes.byref(pointer), ctypes.byref(length)) or length.value < 52:
            return None
        info = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32 * 13)).contents
        if info[0] != 0xFEEF04BD:
            return None
        high, low = (info[4], info[5]) if info[4] or info[5] else (info[2], info[3])
        return ".".join(str(v) for v in (high >> 16, high & 0xFFFF, low >> 16))
    except (OSError, AttributeError, ValueError):
        return None


def _freecad():
    identity = dict(recipe="freecadcmd", executable=None, version=None, sha256=None)
    executable = _path(cad_run.FREECAD_DIR / "bin/freecadcmd.exe")
    if executable.is_file():
        identity.update(executable=str(executable), version=_binary_version(executable),
                        sha256=_file_sha(executable))
    return identity


def _require_live_freecad(host):
    freecad = host["freecad"]
    if (freecad["executable"] is None or freecad["version"] != REQUIRED_FREECAD
            or freecad["sha256"] is None):
        raise Stop("live_freecad_identity_missing_or_wrong_version")


def _host():
    return dict(hostname=socket.gethostname(), system=platform.system(),
                release=platform.release(), version=platform.version(), machine=platform.machine(),
                required_host=REQUIRED_HOST, required_freecad=REQUIRED_FREECAD, freecad=_freecad())


def _executable(omp):
    if not isinstance(omp, str) or not omp:
        raise ValueError("omp_executable_name")
    resolved = shutil.which(omp)
    if resolved is None:
        candidate = Path(omp)
        resolved = str(candidate.resolve()) if candidate.is_file() else None
    identity = dict(omp=None, version=None, sha256=None)
    if resolved is None:
        return identity
    executable = _path(resolved)
    identity["omp"] = str(executable)
    try:
        identity["sha256"] = ledger.file_sha(executable)
    except OSError:
        pass  # An unreadable binary has an unknown hash, not an invented identity.
    try:
        result = subprocess.run([str(executable), "--version"], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                shell=False, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            identity["version"] = result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return identity


def _quota_path(value):
    if value is None:
        return None
    if not isinstance(value, (str, Path)) or not Path(value).is_absolute():
        raise ValueError("quota_snapshot_must_be_absolute")
    # A binding only: never read the snapshot here.
    return str(Path(value))


def _authorization(value, commitment_sha256, model, quota_snapshot):
    if value is None:
        return
    if (not isinstance(value, dict)
            or value.get("schema") != "cad-harness.live-authorization.v4"
            or value.get("phase") != "holdout"
            or type(value.get("charged_calls")) is not int or value["charged_calls"] != 163
            or type(value.get("prior_counted_calls")) is not int
            or not 0 <= value["prior_counted_calls"] <= 163
            or value.get("clock_confirmation") is not True
            or value.get("model") != model or model != MODEL
            or value.get("host") != REQUIRED_HOST
            or value.get("independent_control_validation") is not True
            or value.get("holdout_commitment_sha256") != commitment_sha256
            or not isinstance(value.get("quota_snapshot"), str)
            or _quota_path(value["quota_snapshot"]) != quota_snapshot):
        raise Stop("live_authorization_contract")
    if "continuation" in value:
        continuation = value["continuation"]
        digests = ("prefix_sha256", "prior_manifest_sha256", "prior_summary_sha256",
                   "prior_ledger_sha256", "cohort_sha256")
        if (not isinstance(continuation, dict)
                or set(continuation) != {"schema", "prefix_count", "prefix_path", *digests}
                or continuation["schema"] != "cad-harness.holdout-continuation.v4"
                or type(continuation["prefix_count"]) is not int or continuation["prefix_count"] != 18
                or not isinstance(continuation["prefix_path"], str) or not continuation["prefix_path"]
                or not Path(continuation["prefix_path"]).is_absolute()
                or any(not _digest(continuation[key]) for key in digests)
                or value["prior_counted_calls"] != 20):
            raise Stop("live_authorization_contract")
        # Frozen references only: private prefix bytes are admitted by the live runner.


def freeze(policy_path, commitment_path, run_dir, *, root=ROOT, generator_model=MODEL,
           thinking=THINKING, omp="omp", quota_snapshot=None, host=None, authorization_path=None):
    """Freeze public bytes without releasing inputs or making model/CAD calls."""
    root = _path(root)
    if generator_model != MODEL or thinking != THINKING:
        raise Stop("generator_settings_drift")
    policy_sha256 = _policy(root, policy_path)
    files = bindings(root)
    skill_sha256 = ledger.sha(agent.bundle(root))
    commitment_path = _path(commitment_path)
    commitment = dict(path=str(commitment_path), sha256=_file_sha(commitment_path))
    identity = _host()
    if host is not None and host not in (identity["hostname"], identity):
        raise Stop("host_override_not_actual")
    authorization = _read_json(_path(authorization_path)) if authorization_path is not None else None
    if authorization_path is not None and authorization is None:
        raise Stop("live_authorization_contract")
    if quota_snapshot is None and isinstance(authorization, dict):
        quota_snapshot = authorization.get("quota_snapshot")
    quota_snapshot = _quota_path(quota_snapshot)
    _authorization(authorization, commitment["sha256"], generator_model, quota_snapshot)
    generator = dict(model=generator_model, thinking=thinking, **_executable(omp))
    if authorization is not None:
        if identity["hostname"] != REQUIRED_HOST:
            raise Stop("live_host_mismatch")
        if generator["omp"] is None or generator["version"] is None:
            raise Stop("live_executable_identity_missing")
        _require_live_freecad(identity)
    out = ledger.new_directory(_path(run_dir))
    manifest = dict(schema="cad-harness.manifest.v4", freeze_dir=str(out), files=files, skill_sha256=skill_sha256,
                    policy_sha256=policy_sha256, host=identity, commitment=commitment,
                    generator=generator, authorization=authorization, quota_snapshot=quota_snapshot,
                    limits=json.loads(json.dumps(LIMITS)))
    ledger.write_json(out / "SHA256.json", _sha_payload(manifest))
    manifest["sha256_file"] = ledger.file_sha(out / "SHA256.json")
    ledger.write_json(out / "manifest.json", manifest)
    return manifest


def _sha_payload(manifest):
    return dict(schema="cad-harness.sha256.v4", **{k: v for k, v in manifest.items()
                                                 if k not in ("schema", "sha256_file")})


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def verify(manifest_path, *, root=ROOT, check_host=True):
    """Verify the whole binding set; offline manifests never become authorization."""
    manifest_path = _path(manifest_path)
    root = _path(root)
    manifest = _read_json(manifest_path)
    if isinstance(manifest, dict) and manifest.get("schema") == "cad-harness.capability-manifest.v4c":
        return verify_implementation(manifest_path, root=root)
    required = {"schema", "files", "skill_sha256", "policy_sha256", "host", "commitment",
                "generator", "authorization", "quota_snapshot", "sha256_file", "limits", "freeze_dir"}
    if (not isinstance(manifest, dict) or set(manifest) != required
            or manifest.get("schema") != "cad-harness.manifest.v4"
            or not isinstance(manifest.get("files"), dict) or not manifest["files"]
            or any(not isinstance(k, str) or not _digest(v) for k, v in manifest["files"].items())
            or any(not _digest(manifest.get(k)) for k in ("skill_sha256", "policy_sha256", "sha256_file"))):
        raise Stop("manifest_contract")
    if (not isinstance(manifest["freeze_dir"], str)
            or manifest["freeze_dir"] != str(manifest_path.parent)
            or manifest_path.name != "manifest.json"):
        raise Stop("manifest_original_directory_required")
    sha_path = _path(manifest_path.parent / "SHA256.json")
    if (_file_sha(sha_path) != manifest["sha256_file"]
            or not _same(_read_json(sha_path), _sha_payload(manifest))):
        raise Stop("sha_manifest_mismatch")
    if manifest["files"] != bindings(root):
        raise Stop("file_set_binding_mismatch")
    if manifest["skill_sha256"] != ledger.sha(agent.bundle(root)):
        raise Stop("skill_binding_mismatch")
    if manifest["policy_sha256"] != _policy(root, root / DESIGN / "policy.json"):
        raise Stop("policy_binding_mismatch")
    if not _same(manifest["limits"], LIMITS):
        raise Stop("frozen_limits_mismatch")
    commitment = manifest["commitment"]
    if (not isinstance(commitment, dict) or set(commitment) != {"path", "sha256"}
            or not isinstance(commitment.get("path"), str) or not Path(commitment["path"]).is_absolute()
            or not _digest(commitment.get("sha256"))):
        raise Stop("commitment_contract")
    if _file_sha(_path(commitment["path"])) != commitment["sha256"]:
        raise Stop("commitment_binding_mismatch")
    generator = manifest["generator"]
    if (not isinstance(generator, dict) or set(generator) != {"model", "thinking", "omp", "version", "sha256"}
            or generator.get("model") != MODEL or generator.get("thinking") != THINKING
            or (generator.get("omp") is not None
                and (not isinstance(generator["omp"], str) or not Path(generator["omp"]).is_absolute()))
            or (generator.get("version") is not None
                and (not isinstance(generator["version"], str) or not generator["version"].strip()))
            or (generator.get("sha256") is not None and not _digest(generator["sha256"]))):
        raise Stop("generator_contract")
    executable = _executable(generator["omp"] or "omp")
    if any(generator[key] != executable[key] for key in ("omp", "version", "sha256")):
        raise Stop("executable_binding_mismatch")
    quota_snapshot = _quota_path(manifest["quota_snapshot"])
    _authorization(manifest["authorization"], commitment["sha256"], generator["model"], quota_snapshot)
    host = manifest["host"]
    expected_host = _host()
    if (not isinstance(host, dict) or set(host) != set(expected_host)
            or any(not isinstance(v, str) or not v for k, v in host.items() if k != "freecad")
            or host.get("required_host") != REQUIRED_HOST or host.get("required_freecad") != REQUIRED_FREECAD):
        raise Stop("host_contract")
    freecad = host.get("freecad")
    if (not isinstance(freecad, dict) or set(freecad) != {"recipe", "executable", "version", "sha256"}
            or freecad.get("recipe") != "freecadcmd"
            or (freecad.get("executable") is not None
                and (not isinstance(freecad["executable"], str) or not Path(freecad["executable"]).is_absolute()))
            or (freecad.get("version") is not None
                and (not isinstance(freecad["version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", freecad["version"])))
            or (freecad.get("sha256") is not None and not _digest(freecad["sha256"]))):
        raise Stop("freecad_identity_contract")
    live = manifest["authorization"] is not None
    if (check_host or live) and host != expected_host:
        raise Stop("host_binding_mismatch")
    if live:
        if host["hostname"] != REQUIRED_HOST or expected_host["hostname"] != REQUIRED_HOST:
            raise Stop("live_host_mismatch")
        if generator["omp"] is None or generator["version"] is None:
            raise Stop("live_executable_identity_missing")
        _require_live_freecad(host)
    return manifest


def claim(manifest_path, run_dir):
    """Exclusively claim a manifest once; its frozen bytes remain unchanged."""
    manifest_path = _path(manifest_path)
    run_dir = _path(run_dir)
    manifest = _read_json(manifest_path)
    if (not isinstance(manifest, dict) or manifest.get("schema") != "cad-harness.manifest.v4"
            or manifest.get("freeze_dir") != str(manifest_path.parent) or manifest_path.name != "manifest.json"):
        raise Stop("manifest_original_directory_required")
    sha_path = _path(manifest_path.parent / "SHA256.json")
    if (_file_sha(sha_path) != manifest.get("sha256_file")
            or not _same(_read_json(sha_path), _sha_payload(manifest))):
        raise Stop("sha_manifest_mismatch")
    marker = manifest_path.parent / "manifest.claim.json"
    value = dict(schema="cad-harness.manifest-claim.v4", manifest_path=str(manifest_path),
                 manifest_sha256=_file_sha(manifest_path), run_dir=str(run_dir))
    try:
        ledger.write_json(marker, value)
    except FileExistsError as error:
        raise Stop("manifest_already_claimed") from error
    return value


def freeze_implementation(run_dir, *, root=ROOT, manifest_path=None, prepared_path=None,
                          card_path=None, recipe_paths=(), process=None, profile="c-s1"):
    """Offline capability-stage lock; original authorization is never reinterpreted."""
    if __package__:
        from . import cad_verify_v4_s1
    else:
        import cad_verify_v4_s1
    return cad_verify_v4_s1.implementation_lock(
        run_dir, root=root, manifest_path=manifest_path, prepared_path=prepared_path,
        card_path=card_path, recipe_paths=recipe_paths, process=process, profile=profile)


def verify_implementation(manifest_path, *, root=ROOT):
    if __package__:
        from . import cad_verify_v4_s1
    else:
        import cad_verify_v4_s1
    return cad_verify_v4_s1.verify_implementation_lock(manifest_path, root=root)
