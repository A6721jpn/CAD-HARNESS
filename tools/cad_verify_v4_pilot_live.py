"""Authorized complete U1-U5 cycles and append-only external user-verdict intake.

No custodian preparation, raster read, renderer, or model call occurs on import.
The public rubric remains a draft; an external preregistration is required.
"""
import math
import json
from pathlib import Path
import re
import os
import socket
import stat
import time
from datetime import datetime, timezone

if __package__:
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_model_judge as judge
    from .cad_verify_guard import Stop
else:
    import cad_verify_v4_ledger as ledger, cad_verify_v4_model_judge as judge
    from cad_verify_guard import Stop

ROSTER = ("U1", "U2", "U3", "U4", "U5")
MODEL = dict(judge.MODEL)
RESERVATIONS = {"pilot": 40}
PROFILES = {"U1": "c-s1", "U2": "c-s1", "U3": "c-s3", "U4": "c-s2", "U5": "c-s1"}
PRIMARY_FAMILIES = {"U1": "C1", "U2": "C1", "U3": "C5", "U4": "C4", "U5": "C2"}
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ENTRY_KEYS = {"id", "family", "profile", "stratum", "request", "input_manifest", "prepared", "card", "context", "images"}


def _fail(reason):
    raise ValueError("pilot_live:" + reason)


def _sha(value):
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def validate_registration(registration):
    """Validate an operational execution index, not an invented private bundle schema."""
    if not isinstance(registration, dict) or registration.get("phase") != "pilot":
        _fail("registration_phase")
    entries, files = registration.get("entries"), registration.get("files")
    if (not isinstance(entries, list) or len(entries) != len(ROSTER) or not isinstance(files, dict)
            or [item.get("id") if isinstance(item, dict) else None for item in entries] != list(ROSTER)
            or registration.get("order") != list(ROSTER)):
        _fail("immutable_full_roster_required")
    if (registration.get("budget") != RESERVATIONS or registration.get("generator") != MODEL
            or registration.get("judge") != MODEL or type(registration["budget"]["pilot"]) is not int):
        _fail("model_or_shared_40_budget")
    for entry in entries:
        if (set(entry) != _ENTRY_KEYS or not isinstance(entry["images"], list)
                or entry["profile"] != PROFILES[entry["id"]]
                or any(not isinstance(entry[key], str) or not entry[key].strip() for key in ("family", "stratum"))
                or any(not isinstance(entry[key], str) or entry[key] not in files
                       for key in ("request", "input_manifest", "prepared", "card", "context"))
                or any(not isinstance(key, str) or key not in files for key in entry["images"])
                or len(entry["images"]) != len(set(entry["images"]))):
            _fail("entry_structure")
        if any(files[key].get("role") != "judge_image" for key in entry["images"]):
            _fail("image_not_approved")
    rubric = registration.get("rubric")
    if (not isinstance(rubric, dict) or set(rubric) != {"file", "preregistration"}
            or any(not isinstance(value, str) or value not in files for value in rubric.values())
            or rubric["file"] == rubric["preregistration"]):
        _fail("external_preregistration_required")
    cycle = registration.get("cycle")
    if (not isinstance(cycle, dict) or set(cycle) != {"kind", "previous_manifest_sha256", "retry_authorization"}
            or cycle["kind"] not in ("initial", "retry")):
        _fail("cycle_structure")
    if cycle["kind"] == "initial":
        if cycle["previous_manifest_sha256"] is not None or cycle["retry_authorization"] is not None:
            _fail("initial_cycle_cannot_borrow_history")
    elif (not _sha(cycle["previous_manifest_sha256"])
          or not isinstance(cycle["retry_authorization"], str) or cycle["retry_authorization"] not in files):
        _fail("separate_retry_authorization_required")
    custody = registration.get("custody")
    if (not isinstance(custody, dict) or set(custody) != {"bundle", "contour", "prepared", "commitment", "asset_id"}
            or custody["bundle"] != "pilot-v4" or custody["asset_id"] != "logo"
            or any(not isinstance(custody[key], str) or custody[key] not in files
                   for key in ("contour", "prepared", "commitment"))
            or entries[-1]["prepared"] != custody["prepared"]):
        _fail("u5_bound_pilot_v4_custody_required")
    return registration


def _bindings(registration):
    excluded = {registration["rubric"]["preregistration"], registration["cycle"]["retry_authorization"]}
    return {key: record["sha256"] for key, record in registration["files"].items() if key not in excluded}


def validate_bound_inputs(registration, path_for_id):
    """Called only after the common authorization gate; reads authenticated released IDs."""
    validate_registration(registration)
    rubric = ledger.read_json(path_for_id(registration["rubric"]["file"]))
    if (not isinstance(rubric, dict) or rubric.get("schema") != "cad-harness.pilot-rubric.v4"
            or not isinstance(rubric.get("tasks"), list)
            or [task.get("id") if isinstance(task, dict) else None for task in rubric["tasks"]] != list(ROSTER)):
        _fail("rubric_full_roster_required")
    prereg = ledger.read_json(path_for_id(registration["rubric"]["preregistration"]))
    expected = {"schema", "status", "authority", "authority_evidence", "trial_id", "cycle_id",
                "rubric_sha256", "input_sha256", "acknowledges_draft_rubric", "previous_manifest_sha256"}
    if (not isinstance(prereg, dict) or set(prereg) != expected
            or prereg["schema"] != "cad-harness.pilot-preregistration.v1" or prereg["status"] != "approved"
            or prereg["authority"] not in ("user", "authorized_custodian")
            or not isinstance(prereg["authority_evidence"], str)
            or prereg["authority_evidence"] not in registration["files"]
            or prereg["authority_evidence"] == registration["rubric"]["preregistration"]
            or prereg["trial_id"] != registration["trial_id"] or prereg["cycle_id"] != registration["cycle_id"]
            or prereg["rubric_sha256"] != registration["files"][registration["rubric"]["file"]]["sha256"]
            or prereg["input_sha256"] != _bindings(registration)
            or type(prereg["acknowledges_draft_rubric"]) is not bool
            or ((rubric.get("status") == "draft" or rubric.get("preregistered") is not True)
                and prereg["acknowledges_draft_rubric"] is not True)
            or prereg["previous_manifest_sha256"] != registration["cycle"]["previous_manifest_sha256"]):
        _fail("external_preregistration_binding")
    if registration["cycle"]["kind"] == "retry":
        approval = ledger.read_json(path_for_id(registration["cycle"]["retry_authorization"]))
        if (not isinstance(approval, dict) or set(approval) != {"schema", "status", "trial_id", "cycle_id",
                "previous_manifest_sha256", "budget", "fresh_quota_required", "authority_evidence"}
                or approval["schema"] != "cad-harness.pilot-retry-authorization.v1"
                or approval["status"] != "approved" or approval["trial_id"] != registration["trial_id"]
                or approval["cycle_id"] != registration["cycle_id"] or approval["budget"] != RESERVATIONS
                or approval["previous_manifest_sha256"] != registration["cycle"]["previous_manifest_sha256"]
                or approval["fresh_quota_required"] is not True
                or approval["authority_evidence"] != prereg["authority_evidence"]):
            _fail("separate_retry_authorization_binding")
    custody = registration["custody"]
    # Public commitment metadata is authenticated, never discovered from a
    # private tree or replaced by a source-code whitelist of geometry hashes.
    commitment = Path(path_for_id(custody["commitment"])).read_text(encoding="utf-8")
    section = re.search(r"(?ms)^## Pilot v4[^\n]*\n(.*?)(?=^## Pilot v[0-9]|\Z)", commitment)
    if section is None:
        _fail("u5_pilot_v4_public_commitment")
    for key, name in (("contour", "native/contour.json"), ("prepared", "native/prepared.json")):
        rows = re.findall(r"(?m)^\|\s*" + re.escape(name) + r"\s*\|\s*([0-9]+)\s*\|\s*`([0-9a-f]{64})`\s*\|", section[1])
        if len(rows) != 1:
            _fail("u5_public_commitment_metadata")
        size, digest = rows[0]
        bound = registration["files"][custody[key]]
        if bound["sha256"] != digest or bound["bytes"] != int(size):
            _fail("u5_pilot_v4_" + key + "_binding")
    contour = ledger.read_json(path_for_id(custody["contour"]))
    prepared = ledger.read_json(path_for_id(custody["prepared"]))
    if (not isinstance(contour, dict) or contour.get("schema") != "cad-harness.contour.v4c"
            or contour.get("asset_id") != custody["asset_id"] or contour.get("units") != "mm"
            or not isinstance(prepared, dict) or prepared.get("schema") != "cad-harness.prepared.v4c"
            or prepared.get("assets", {}).get(custody["asset_id"]) != contour):
        _fail("u5_typed_contour_intake")
    original_section = re.search(r"(?ms)^## Pilot inputs\s*\n(.*?)(?=^## |\Z)", commitment)
    if original_section is None:
        _fail("committed_original_inputs_required")
    originals = {}
    for name in ("requests.md", "U1.step", "U2.step", "U3.step", "U4.step", "U5_logo.png"):
        rows = re.findall(r"(?m)^\|\s*" + re.escape(name) + r"\s*\|\s*([0-9]+)\s*\|\s*`([0-9a-f]{64})`\s*\|",
                          original_section[1])
        if len(rows) != 1:
            _fail("committed_original_input_metadata")
        size, digest = rows[0]
        originals[name] = dict(sha256=digest, bytes=int(size))
        if not any(all(record[key] == originals[name][key] for key in ("sha256", "bytes"))
                   for record in registration["files"].values()):
            _fail("committed_original_input_missing:" + name)
    if __package__:
        from . import cad_verify_v4_family_live as families
    else:
        import cad_verify_v4_family_live as families
    for entry in registration["entries"]:
        families._card_requirements(dict(entry, family=PRIMARY_FAMILIES[entry["id"]]),
                                    ledger.read_json(path_for_id(entry["card"])))
        if entry["id"] != "U5":
            manifest = ledger.read_json(path_for_id(entry["input_manifest"]))
            references = [asset for asset in manifest.get("assets", {}).values()
                          if asset.get("kind") == "step" and asset.get("role") == "reference"]
            expected = originals[entry["id"]+".step"]
            if not references or any(any(asset.get(key) != expected[key] for key in ("sha256", "bytes"))
                                     for asset in references):
                _fail("committed_original_step_mismatch:" + entry["id"])
    for task in rubric["tasks"]:
        task_rubric(rubric, task["id"])
    return registration


def task_rubric(rubric, record_id):
    """Keep every public task gate; visual-only items cannot become numeric waivers."""
    task = next((task for task in rubric["tasks"] if task["id"] == record_id), None)
    if task is None or not isinstance(task.get("pass"), list) or not task["pass"]:
        _fail("task_rubric_missing")
    items = []
    for number, item in enumerate(task["pass"], 1):
        if not isinstance(item, dict) or not isinstance(item.get("item"), str):
            _fail("task_rubric_item")
        items.append(dict(id=f"gate-{number}", criterion=json.dumps(item, ensure_ascii=False, allow_nan=False),
                          visual=item.get("judgment") == "qualitative"))
    visual = task.get("astra_user_visual")
    if not isinstance(visual, list) or not visual:
        _fail("user_visual_rubric_missing")
    for number, item in enumerate(visual, 1):
        if not isinstance(item, dict) or not isinstance(item.get("item"), str):
            _fail("task_visual_item")
        items.append(dict(id=f"visual-{number}", criterion=json.dumps(item, ensure_ascii=False, allow_nan=False),
                          visual=True))
    return judge.validate_rubric(dict(schema=judge.RUBRIC_SCHEMA, id=record_id, items=items))


def _stop_reason(exc):
    reason = str(exc)
    if reason in ("budget_exhausted", "insufficient_call_budget", "pool_call_limit", "trial_call_budget_exhausted"):
        return "budget_exhausted"
    if reason in ("quota_stop", "quota_hard_stop", "quota_soft_stop"):
        return "quota_stop"
    return None


def _fatal(value):
    """Fatal evidence is irreversible, including every historical handover."""
    if isinstance(value, dict):
        if any(value.get(key) is True for key in ("critical_dimension_error", "critical_error", "fabrication")):
            return True
        if value.get("critical") is True and value.get("status") == "FAIL":
            return True
        return any(_fatal(item) for item in value.values() if isinstance(item, (dict, list)))
    return isinstance(value, list) and any(_fatal(item) for item in value)


def _has_judgment(record):
    model = record.get("judge")
    verdict = model.get("verdict") if isinstance(model, dict) else None
    if (not isinstance(verdict, dict)
            or set(verdict) != {"schema", "rubric_id", "items", "critical_dimension_error", "fabrication"}
            or verdict["schema"] != judge.VERDICT_SCHEMA or verdict["rubric_id"] != record.get("id")
            or not isinstance(verdict["items"], list) or not verdict["items"]
            or any(type(verdict[key]) is not bool for key in ("critical_dimension_error", "fabrication"))):
        return False
    seen = set()
    for item in verdict["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "status", "reason"}
                or not isinstance(item["id"], str) or not item["id"] or item["id"] in seen
                or item["status"] not in ("PASS", "FAIL", "UNVERIFIED")
                or not isinstance(item["reason"], str) or not item["reason"].strip()):
            return False
        seen.add(item["id"])
    return True


def evaluate_record(record, user_verdict=None, correction=None, history=()):
    """Human-final visuals never waive native numerical or historical fatal gates."""
    if _fatal(record) or _fatal(list(history)) or _fatal(user_verdict):
        return "FAIL"
    worker_status = record.get("worker_status")
    if worker_status == "INCOMPLETE":
        return "INCOMPLETE"
    first = record.get("first_handover")
    if not isinstance(first, dict) or not record.get("artifact_bundle"):
        return worker_status if worker_status != "PASS" and isinstance(worker_status, str) else "UNVERIFIED"
    initial_native = judge._deterministic_status(record.get("artifact_verdict"))
    model = record.get("judge") or {}
    if user_verdict is None:
        return "FAIL" if initial_native == "FAIL" or model.get("status") == "FAIL" else "UNVERIFIED"
    if (user_verdict["visual_status"] == "FAIL" or not user_verdict["first_handover_accepted"]
            or user_verdict["correction_elapsed_s"] > 300):
        return "FAIL"
    if not _has_judgment(record) or any(item["status"] == "UNVERIFIED" for item in model["verdict"]["items"]):
        return "UNVERIFIED"
    native = initial_native
    if user_verdict["correction_elapsed_s"] > 0:
        if isinstance(correction, dict) and correction.get("elapsed_s", math.inf) > 300:
            return "FAIL"
        if not isinstance(correction, dict) or correction.get("status") not in ("PASS", "FAIL"):
            return "UNVERIFIED"
        native = judge._deterministic_status(correction.get("native_verdict"))
    elif correction is not None or first.get("status") != "PASS":
        return "FAIL" if first.get("status") == "FAIL" else "UNVERIFIED"
    if native == "FAIL":
        return "FAIL"
    if native != "PASS" or user_verdict["visual_status"] != "PASS":
        return "UNVERIFIED"
    # An ordinary valid Astra visual FAIL is retained, but the actual user's
    # visual decision is final. No second model judgment is made.
    return "PASS"


def _cycle_status(records):
    statuses = [record["status"] for record in records]
    if all(item == "PASS" for item in statuses):
        return "PASS"
    if "INCOMPLETE" in statuses:
        return "INCOMPLETE"
    if "FAIL" in statuses:
        return "FAIL"
    if any(item not in ("PASS", "UNVERIFIED") for item in statuses):
        return "ERROR"
    return "UNVERIFIED"


def run(manifest_path, authorization_path, run_dir, *, process=None, native_process=None,
        wall=None, sleep=None, verifier=None):
    if __package__:
        from . import cad_verify_v4_trials as trials
    else:
        import cad_verify_v4_trials as trials
    with trials.TrialSession(manifest_path, authorization_path, run_dir, phase="pilot", process=process,
                             native_process=native_process, wall=wall, sleep=sleep, verifier=verifier) as session:
        registration = session.registration
        validate_bound_inputs(registration, session.path)
        rubric = ledger.read_json(session.path(registration["rubric"]["file"]))
        records, stopped, unstarted_status = [], None, "NOT_RUN"
        for entry in registration["entries"]:
            record = dict(id=entry["id"], worker_status="UNVERIFIED", status="UNVERIFIED",
                          artifact_verdict=None, first_handover=None, artifact_bundle=None,
                          judge=None, user_verdict=None, stop_reason=stopped)
            if stopped:
                record.update(worker_status=unstarted_status, status=unstarted_status)
                records.append(record)
                continue
            try:
                session.check()
                # Only the bound typed driver is used. In particular, no preparation
                # or image-to-contour entry point exists in the generator path.
                generated = session.execute_plan(entry, session.out / entry["id"], pool="pilot", **MODEL,
                                                 max_calls=3, one_attempt=True)
                record.update(worker_status=generated["status"], artifact_verdict=generated.get("artifact_verdict"),
                              first_handover=generated.get("first_handover"), artifact_bundle=generated.get("artifact_bundle"),
                              native_cad_intervals=generated.get("native_cad_intervals"),
                              driver_result=generated.get("driver_result"), error=generated.get("error"),
                              stop_reason=generated.get("stop_reason"))
                reason = _stop_reason(Stop(generated.get("stop_reason") or ""))
                if reason:
                    stopped = reason
                    unstarted_status = "INCOMPLETE"
                    record.update(worker_status="INCOMPLETE", stop_reason=reason)
                fatal = getattr(session, "fatal", None)
                if fatal:
                    stopped = fatal
                    record["stop_reason"] = fatal
                if record["first_handover"] and record["artifact_bundle"] and not stopped:
                    record["judge"] = session.judge(entry["id"], session.path(entry["request"]).read_bytes().decode("utf-8"),
                        record["artifact_verdict"], task_rubric(rubric, entry["id"]), pool="pilot",
                        images=(tuple(generated["images"]) + tuple(session.path(key) for key in entry["images"]))
                        if generated.get("images") else ())
                record["status"] = evaluate_record(record)
            except BaseException as exc:
                reason = _stop_reason(exc)
                stopped = reason or str(exc) or type(exc).__name__
                if reason:
                    unstarted_status = "INCOMPLETE"
                    record.update(worker_status="INCOMPLETE", status="INCOMPLETE", stop_reason=reason)
                else:
                    status = "INTERRUPTED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "ERROR"
                    record.update(worker_status=status, status=status, stop_reason=stopped,
                                  error=dict(type=type(exc).__name__, message=str(exc)))
                session.event("pilot_record_error", record=record)
            records.append(record)
            session.event("pilot_record_finished", record=record)
        value = dict(schema="cad-harness.pilot-trial.v1", trial_id=registration["trial_id"],
                     cycle_id=registration["cycle_id"], manifest_sha256=ledger.file_sha(manifest_path),
                     evidence_mode=session.mode, roster=list(ROSTER), denominator=5, records=records,
                     status=_cycle_status(records), same_model_caveat=judge.SAME_MODEL_CAVEAT,
                     rubric_sha256=registration["files"][registration["rubric"]["file"]]["sha256"],
                     user_visual_required=True, final_v4_ready=False, accounting=session.summary(), stop_reason=stopped)
        ledger.write_json(session.out / "summary.json", value)
        return value


def record_user_verdict(run_dir, verdict_path, evidence_path):
    """Intake an externally supplied user verdict without rewriting historical output.

    This records the external attribution; it does not authenticate a user or
    manufacture adoption. The operator must supply the actual user-message evidence.
    One exclusive receipt per record prevents a favorable replacement/re-score.
    """
    root = Path(run_dir)
    summary_path = root / "summary.json"
    summary = ledger.read_json(summary_path)
    if (summary.get("schema") != "cad-harness.pilot-trial.v1" or summary.get("roster") != list(ROSTER)
            or summary.get("evidence_mode") not in ("live", "unit_mock")
            or [record.get("id") for record in summary.get("records", [])] != list(ROSTER)):
        _fail("user_verdict_requires_complete_cycle")
    verdict = ledger.read_json(verdict_path)
    fields = {"schema", "authority", "source_id", "evidence_sha256", "trial_id", "cycle_id", "manifest_sha256",
              "record_id", "handover_sha256", "visual_status", "first_handover_accepted",
              "correction_elapsed_s", "correction_proof", "critical_dimension_error", "fabrication"}
    if (not isinstance(verdict, dict) or set(verdict) != fields
            or verdict["schema"] != "cad-harness.pilot-user-verdict.v1" or verdict["authority"] != "user"
            or not isinstance(verdict["source_id"], str) or not verdict["source_id"].strip()
            or verdict["evidence_sha256"] != ledger.file_sha(evidence_path)
            or any(verdict[key] != summary[key] for key in ("trial_id", "cycle_id", "manifest_sha256"))
            or verdict["record_id"] not in ROSTER or not _sha(verdict["handover_sha256"])
            or verdict["visual_status"] not in ("PASS", "FAIL", "UNVERIFIED")
            or any(type(verdict[key]) is not bool for key in ("first_handover_accepted", "critical_dimension_error", "fabrication"))
            or type(verdict["correction_elapsed_s"]) not in (int, float)
            or not math.isfinite(verdict["correction_elapsed_s"]) or verdict["correction_elapsed_s"] < 0):
        _fail("external_user_verdict_binding")
    record = next(item for item in summary["records"] if item["id"] == verdict["record_id"])
    # Canonical hashing binds the first handover plus its exact artifact references,
    # and does not trust a caller's chosen "current" replacement artifact.
    handover_sha = handover_sha256(record)
    if handover_sha != verdict["handover_sha256"]:
        _fail("user_verdict_first_handover_binding")
    correction, history = _user_correction(root, summary, record, verdict)
    receipts = root / "user-verdicts"
    if any(path.is_symlink() for path in (root, *root.parents, receipts)):
        _fail("user_verdict_linked_output")
    receipts.mkdir(exist_ok=True)
    destination = receipts / verdict["record_id"]
    destination.mkdir(exist_ok=False)
    evidence = Path(evidence_path).read_bytes()
    verdict_bytes = Path(verdict_path).read_bytes()
    if ledger.sha(evidence) != verdict["evidence_sha256"]:
        _fail("user_evidence_changed_during_intake")
    with (destination / "evidence.bin").open("xb") as file:
        file.write(evidence)
    with (destination / "verdict.json").open("xb") as file:
        file.write(verdict_bytes)
    receipt = dict(schema="cad-harness.pilot-user-receipt.v1", verdict=verdict,
                   verdict_file_sha256=ledger.sha(verdict_bytes), evidence_sha256=ledger.sha(evidence),
                   summary_sha256=ledger.file_sha(summary_path), status=evaluate_record(record, verdict, correction, history),
                   handover_history=_handover_history(record, history),
                   evidence_mode=summary["evidence_mode"],
                   attribution="external_user_evidence_supplied_by_operator", recorded_at=ledger.utc())
    ledger.write_json(destination / "receipt.json", receipt)
    return dict(receipt=receipt, cycle=user_results(root))


def handover_sha256(record):
    import json
    value = dict(first_handover=record.get("first_handover"), artifact_bundle=record.get("artifact_bundle"))
    return ledger.sha(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8"))


def user_results(run_dir):
    """Re-evaluate the complete same-cycle roster from immutable intake receipts."""
    root = Path(run_dir)
    summary = ledger.read_json(root / "summary.json")
    if (summary.get("schema") != "cad-harness.pilot-trial.v1" or summary.get("roster") != list(ROSTER)
            or summary.get("evidence_mode") not in ("live", "unit_mock")
            or [record.get("id") for record in summary.get("records", [])] != list(ROSTER)):
        _fail("user_results_complete_cycle_required")
    summary_sha = ledger.file_sha(root / "summary.json")
    records = []
    for record in summary["records"]:
        folder = root / "user-verdicts" / record["id"]
        path = folder / "receipt.json"
        verdict = None
        correction, history = None, _check_history(root, record["id"])[0]
        if path.exists():
            receipt = ledger.read_json(path)
            if (receipt.get("schema") != "cad-harness.pilot-user-receipt.v1"
                    or receipt.get("summary_sha256") != summary_sha
                    or receipt.get("verdict_file_sha256") != ledger.file_sha(folder / "verdict.json")
                    or receipt.get("evidence_sha256") != ledger.file_sha(folder / "evidence.bin")
                    or receipt.get("verdict") != ledger.read_json(folder / "verdict.json")
                    or receipt["verdict"].get("record_id") != record["id"]
                    or receipt["verdict"].get("handover_sha256") != handover_sha256(record)):
                _fail("user_receipt_binding")
            verdict = receipt["verdict"]
            correction, history = _user_correction(root, summary, record, verdict)
        records.append(dict(id=record["id"], status=evaluate_record(record, verdict, correction, history),
                            user_verdict_received=verdict is not None, judge=record.get("judge"),
                            handover_history=_handover_history(record, history)))
    return dict(schema="cad-harness.pilot-user-results.v1", trial_id=summary["trial_id"],
                cycle_id=summary["cycle_id"], manifest_sha256=summary["manifest_sha256"],
                summary_sha256=summary_sha, denominator=5, records=records, status=_cycle_status(records),
                evidence_mode=summary["evidence_mode"], final_v4_ready=False, same_model_caveat=judge.SAME_MODEL_CAVEAT)


def _regular(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            _fail("correction_link_or_reparse")
    if not path.is_file():
        _fail("correction_regular_file_required")
    return path


def _file(path):
    path = _regular(path)
    return dict(path=str(path), sha256=ledger.file_sha(path), bytes=path.stat().st_size)


def _verify_file(record):
    if (not isinstance(record, dict) or set(record) != {"path", "sha256", "bytes"}
            or not _sha(record.get("sha256")) or type(record.get("bytes")) is not int):
        _fail("correction_file_record")
    actual = _file(record["path"])
    if actual != record:
        _fail("correction_bound_file_changed")
    return Path(actual["path"])


def _system_boot_id():
    if os.name == "nt":
        import ctypes
        class TimeOfDay(ctypes.Structure):
            _fields_ = [("boot", ctypes.c_longlong), ("current", ctypes.c_longlong),
                        ("bias", ctypes.c_longlong), ("zone", ctypes.c_ulong),
                        ("reserved", ctypes.c_ulong), ("boot_bias", ctypes.c_ulonglong),
                        ("sleep_bias", ctypes.c_ulonglong)]
        value = TimeOfDay()
        status = ctypes.WinDLL("ntdll").NtQuerySystemInformation(3, ctypes.byref(value), ctypes.sizeof(value), None)
        if status != 0 or value.boot <= 0:
            _fail("correction_system_boot_identity_unavailable")
        return "windows-boot-filetime:" + str(value.boot)
    path = Path("/proc/sys/kernel/random/boot_id")
    if not path.is_file():
        _fail("correction_system_boot_identity_unavailable")
    return "linux-boot-id:" + path.read_text(encoding="ascii").strip()


def _stamp(*, mode, wall=None):
    mocked = mode == "unit_mock" and wall is not None
    clock = wall if mocked else time.monotonic
    before = clock()
    utc = wall.utc() if mocked and callable(getattr(wall, "utc", None)) else ledger.utc()
    after = clock()
    boot = getattr(wall, "boot_id", None) if mocked else None
    boot = boot() if callable(boot) else boot
    boot = boot or _system_boot_id()
    implementation = time.get_clock_info("monotonic").implementation
    if mocked:
        implementation = "unit_mock:" + str(getattr(wall, "implementation", implementation))
    if (type(before) not in (int, float) or type(after) not in (int, float)
            or not math.isfinite(before) or not math.isfinite(after) or after < before
            or not isinstance(boot, str) or not boot):
        _fail("correction_clock_invalid")
    parsed = datetime.fromisoformat(utc.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        _fail("correction_utc_timezone_required")
    return dict(utc=parsed.astimezone(timezone.utc).isoformat(), monotonic_before_s=before,
                monotonic_after_s=after, boot_id=boot, host=socket.gethostname(),
                implementation=implementation)


def _elapsed(start, end):
    if any(start.get(key) != end.get(key) for key in ("boot_id", "host", "implementation")):
        _fail("correction_clock_identity_changed")
    utc_start = datetime.fromisoformat(start["utc"])
    utc_end = datetime.fromisoformat(end["utc"])
    elapsed = end["monotonic_after_s"] - start["monotonic_before_s"]
    utc_elapsed = (utc_end - utc_start).total_seconds()
    if elapsed < 0 or utc_elapsed < 0 or end["monotonic_before_s"] < start["monotonic_after_s"]:
        _fail("correction_clock_backward")
    # A clock-consistency guard, not a relaxation of the 300-second gate.
    # Both complete raw stamps are retained; wall-clock jumps are refused.
    uncertainty = (start["monotonic_after_s"] - start["monotonic_before_s"]
                   + end["monotonic_after_s"] - end["monotonic_before_s"])
    if abs(elapsed - utc_elapsed) > 1.0 + uncertainty:
        _fail("correction_clock_inconsistent")
    return max(elapsed, utc_elapsed)


def _original(run_dir, record_id):
    if record_id not in ROSTER:
        _fail("correction_record_id")
    root = Path(run_dir).absolute()
    path = _regular(root / "summary.json")
    summary = ledger.read_json(path)
    if (summary.get("schema") != "cad-harness.pilot-trial.v1" or summary.get("roster") != list(ROSTER)
            or summary.get("evidence_mode") not in ("live", "unit_mock")
            or [row.get("id") for row in summary.get("records", [])] != list(ROSTER)):
        _fail("correction_complete_original_cycle_required")
    return root, summary, summary["records"][ROSTER.index(record_id)]


def _correction_binding(session, manifest_path, authorization_path, run_dir, record_id):
    root, summary, record = _original(run_dir, record_id)
    if (summary["manifest_sha256"] != ledger.file_sha(manifest_path)
            or any(summary[key] != session.registration[key] for key in ("trial_id", "cycle_id"))):
        _fail("correction_original_trial_binding")
    entry = next(row for row in session.registration["entries"] if row["id"] == record_id)
    return dict(trial_id=summary["trial_id"], cycle_id=summary["cycle_id"], record_id=record_id,
                manifest=_file(manifest_path), authorization=_file(authorization_path),
                summary=_file(root / "summary.json"), handover_sha256=handover_sha256(record),
                entry=entry, source_files=session.registration["files"],
                integrated_lock=session.manifest["integrated_lock"]), record


def _validation_session(manifest_path, authorization_path, out, run_dir, **kwargs):
    if __package__:
        from . import cad_verify_v4_trials as trials
    else:
        import cad_verify_v4_trials as trials
    return trials.TrialSession(manifest_path, authorization_path, out, phase="pilot",
                               validation_of=run_dir, **kwargs)


def _bundle_module():
    if __package__:
        from . import cad_verify_v4_artifacts as artifacts
    else:
        import cad_verify_v4_artifacts as artifacts
    return artifacts


def _snapshot_bundle(bundle_path, out, *, profile):
    """Preserve submitted bytes, changing only collector-owned path references."""
    artifacts = _bundle_module()
    original = _file(bundle_path)
    value, files, extensions = artifacts.load_bundle(bundle_path, profile=profile)
    out = ledger.new_directory(out)
    raw = Path(bundle_path).read_bytes()
    if ledger.sha(raw) != original["sha256"]:
        _fail("correction_submission_changed")
    with (out / "submitted-bundle.json").open("xb") as file:
        file.write(raw)
    source_artifacts = {}
    for key, source in {**files, **{"extension:" + name: path for name, path in extensions.items()}}.items():
        source_record = _file(source)
        data = source.read_bytes()
        if ledger.sha(data) != source_record["sha256"] or len(data) != source_record["bytes"]:
            _fail("correction_submission_changed")
        source_artifacts[key] = source_record
        # Frozen tools.* dependencies cannot be relocated under their reserved
        # module name; their exact integrated-lock bytes remain bound in place.
        if key.startswith("extension:tools."):
            target = source
        else:
            target = out / (source.name if key in ("native", "step")
                            else "extensions/" + key.removeprefix("extension:").replace(".", "/") + ".py")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as file:
                file.write(data)
        if key in ("native", "step"):
            value[key] = _file(target)
        else:
            name = key.removeprefix("extension:")
            target_record = next(item for item in value["extensions"] if item["module"] == name)
            target_record.update(_file(target))
    if _file(bundle_path) != original:
        _fail("correction_submission_changed")
    ledger.write_json(out / "bundle.json", value)
    submission = dict(original_bundle=original, archived_bundle=_file(out / "submitted-bundle.json"),
                      source_artifacts=source_artifacts)
    snapshot = _file(out / "bundle.json")
    _verify_snapshot(snapshot, submission, profile=profile)
    return snapshot, submission


def _verify_snapshot(snapshot, submission, *, profile):
    value, files, extensions = _bundle_module().load_bundle(_verify_file(snapshot), profile=profile)
    original = ledger.read_json(_verify_file(submission["archived_bundle"]))
    if any(submission["archived_bundle"][key] != submission["original_bundle"][key] for key in ("sha256", "bytes")):
        _fail("correction_archived_submission_binding")
    for key in ("schema", "profile", "evidence_mode", "output_object", "probes"):
        if value[key] != original[key]:
            _fail("correction_snapshot_not_byte_preserving")
    actual = {**files, **{"extension:" + name: path for name, path in extensions.items()}}
    declared = {key: original[key] for key in ("native", "step")}
    declared.update({"extension:" + item["module"]: item for item in original["extensions"]})
    if set(actual) != set(submission["source_artifacts"]) or set(actual) != set(declared):
        _fail("correction_snapshot_dependencies")
    for key, path in actual.items():
        record = _file(path)
        if any(record[field] != submission["source_artifacts"][key][field]
               or record[field] != declared[key][field] for field in ("sha256", "bytes")):
            _fail("correction_snapshot_not_byte_preserving")


def begin_correction(manifest_path, authorization_path, run_dir, record_id, *, process=None, wall=None, verifier=None):
    """Start one exclusive elapsed timer before the first human edit; never reset it."""
    root, _, original = _original(run_dir, record_id)
    if not original.get("first_handover") or not original.get("artifact_bundle"):
        _fail("correction_actual_handover_required")
    if (root / "user-verdicts" / record_id / "receipt.json").exists():
        _fail("correction_user_verdict_already_final")
    folder = root / "corrections" / record_id
    if (folder / "start.json").exists():
        _fail("correction_timer_already_started")
    with _validation_session(manifest_path, authorization_path, folder / "begin-validation", root,
                             process=process, wall=wall, verifier=verifier) as session:
        binding, record = _correction_binding(session, manifest_path, authorization_path, root, record_id)
        session.check()
        if (not isinstance(record["artifact_bundle"], str)
                or _file(record["artifact_bundle"])["sha256"] != record["first_handover"].get("artifact_bundle_sha256")):
            _fail("correction_original_bundle_binding")
        snapshot, submission = _snapshot_bundle(record["artifact_bundle"], folder / "first-handover",
                                                 profile=binding["entry"]["profile"])
        timer = dict(schema="cad-harness.pilot-correction-start.v1", binding=binding,
                     first_handover_snapshot=dict(artifact_bundle=snapshot, submission=submission),
                     started=_stamp(mode=session.mode, wall=wall), evidence_mode=session.mode, live_calls=0)
        ledger.write_json(folder / "start.json", timer)
        session.event("human_correction_started", record_id=record_id, timer=timer)
    return dict(timer=timer, timer_file=_file(folder / "start.json"))


def _inventory(root):
    root = Path(root)
    return {path.relative_to(root).as_posix(): _file(path) for path in sorted(root.rglob("*")) if path.is_file()}


def _check_history(root, record_id):
    folder = Path(root) / "corrections" / record_id / "checks"
    history, latest = [], None
    if not folder.exists():
        return history, latest
    for path in sorted(folder.glob("check-*.claim.json")):
        claim = ledger.read_json(_regular(path))
        completed = path.with_name(path.name.replace(".claim.json", ".json"))
        if not completed.is_file():
            _fail("correction_check_incomplete")
        index = ledger.read_json(_regular(completed))
        proof = ledger.read_json(_verify_file(index["proof"]))
        if (proof.get("check_id") != claim.get("check_id") or index.get("check_id") != claim.get("check_id")
                or proof.get("timer", {}).get("sha256") != claim.get("timer_sha256")
                or proof.get("submission", {}).get("original_bundle") != claim.get("artifact_bundle")):
            _fail("correction_history_binding")
        for item in proof.get("native_evidence", {}).values():
            _verify_file(item)
        _verify_file(proof["session_ledger"])
        _verify_snapshot(proof["artifact_bundle"], proof["submission"], profile=proof["binding"]["entry"]["profile"])
        history.append(proof)
        latest = index["proof"]
    return history, latest


def check_correction(manifest_path, authorization_path, run_dir, record_id, artifact_bundle, out_dir, *,
                     process=None, native_process=None, wall=None, verifier=None):
    """Neutral same-card native verification only; no constructor, generation or re-score."""
    root, _, _ = _original(run_dir, record_id)
    if (root / "user-verdicts" / record_id / "receipt.json").exists():
        _fail("correction_user_verdict_already_final")
    folder = root / "corrections" / record_id
    timer_path = _regular(folder / "start.json")
    timer = ledger.read_json(timer_path)
    if timer.get("schema") != "cad-harness.pilot-correction-start.v1":
        _fail("correction_timer_required")
    checks = folder / "checks"
    checks.mkdir(exist_ok=True)
    lock_path = folder / "checking.lock"
    with lock_path.open("x", encoding="ascii") as lock:
        lock.write("exclusive human correction verification\n")
    try:
        number = len(list(checks.glob("check-*.claim.json"))) + 1
        check_id = "check-%06d" % number
        claim_path = checks / (check_id + ".claim.json")
        ledger.write_json(claim_path, dict(check_id=check_id, timer_sha256=ledger.file_sha(timer_path),
                                          artifact_bundle=_file(artifact_bundle), out_dir=str(Path(out_dir).absolute())))
        out = ledger.new_directory(Path(out_dir).absolute())
        result, error, bundle = None, None, None
        with _validation_session(manifest_path, authorization_path, out / "validation", root,
                                 process=process, native_process=native_process, wall=wall, verifier=verifier) as session:
            binding, record = _correction_binding(session, manifest_path, authorization_path, root, record_id)
            if binding != timer["binding"] or session.mode != timer["evidence_mode"]:
                _fail("correction_timer_original_binding")
            before = _stamp(mode=session.mode, wall=wall)
            remaining = 300 - _elapsed(timer["started"], before)
            if remaining <= 0:
                _fail("correction_elapsed_expired")
            bundle, submission = _snapshot_bundle(artifact_bundle, out / "submitted-artifacts",
                                                   profile=binding["entry"]["profile"])
            session.check()
            before = _stamp(mode=session.mode, wall=wall)
            remaining = 300 - _elapsed(timer["started"], before)
            if remaining <= 0:
                _fail("correction_elapsed_expired")
            session.event("human_correction_check_started", record_id=record_id, check_id=check_id,
                          artifact_bundle=bundle, remaining_elapsed_s=remaining)
            try:
                result = session.check_artifacts(binding["entry"], bundle["path"], out / "native-check", timeout=remaining)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                error = dict(type=type(exc).__name__, message=str(exc))
                result = dict(status="ERROR", error=error)
                session.event("human_correction_worker_failed", record_id=record_id, error=error)
            after = _stamp(mode=session.mode, wall=wall)
            elapsed = _elapsed(timer["started"], after)
            accounting = session.summary()
            if any(accounting.get(key, 0) for key in ("logical_calls", "physical_attempts", "live_calls")):
                _fail("correction_model_calls_forbidden")
            session.event("human_correction_check_finished", record_id=record_id, check_id=check_id,
                          status=result.get("status"), elapsed_s=elapsed, live_calls=0)
        evidence = _inventory(out / "native-check") if (out / "native-check").exists() else {}
        final_stamp = _stamp(mode=session.mode, wall=wall)
        elapsed = _elapsed(timer["started"], final_stamp)
        proof = dict(schema="cad-harness.pilot-correction-proof.v1", check_id=check_id, binding=binding,
                     timer=_file(timer_path), before=before, native_finished=after, finished=final_stamp, elapsed_s=elapsed,
                     status=result["status"] if elapsed <= 300 else "EXPIRED", native_verdict=result,
                     artifact_bundle=bundle, submission=submission, first_handover_snapshot=timer["first_handover_snapshot"],
                     native_evidence=evidence, session_ledger=_file(out / "validation/ledger.jsonl"),
                     error=error, evidence_mode=session.mode, live_calls=0)
        ledger.write_json(out / "correction-proof.json", proof)
        reference = _file(out / "correction-proof.json")
        ledger.write_json(checks / (check_id + ".json"), dict(check_id=check_id, proof=reference))
        return dict(proof=proof, proof_file=reference)
    finally:
        lock_path.unlink()


def _validated_correction(root, summary, record, reference):
    proof = ledger.read_json(_verify_file(reference))
    if proof.get("schema") != "cad-harness.pilot-correction-proof.v1" or proof.get("live_calls") != 0:
        _fail("correction_native_proof_required")
    binding = proof.get("binding", {})
    if (any(binding.get(key) != summary[key] for key in ("trial_id", "cycle_id"))
            or binding.get("record_id") != record["id"] or binding.get("handover_sha256") != handover_sha256(record)
            or binding.get("manifest", {}).get("sha256") != summary["manifest_sha256"]
            or binding.get("summary") != _file(Path(root) / "summary.json")):
        _fail("correction_proof_original_binding")
    timer = ledger.read_json(_verify_file(proof["timer"]))
    if timer.get("binding") != binding or proof["timer"] != _file(Path(root) / "corrections" / record["id"] / "start.json"):
        _fail("correction_proof_timer_binding")
    first_snapshot = timer["first_handover_snapshot"]
    _verify_snapshot(first_snapshot["artifact_bundle"], first_snapshot["submission"], profile=binding["entry"]["profile"])
    if proof.get("first_handover_snapshot") != first_snapshot:
        _fail("correction_first_handover_snapshot_binding")
    manifest = ledger.read_json(_verify_file(binding["manifest"]))
    registration = manifest.get("registration_data")
    if (not isinstance(registration, dict) or binding.get("source_files") != registration.get("files")
            or binding.get("integrated_lock") != manifest.get("integrated_lock")
            or binding.get("entry") not in registration.get("entries", [])):
        _fail("correction_proof_frozen_sources")
    elapsed = _elapsed(timer["started"], proof["finished"])
    if elapsed != proof.get("elapsed_s") or elapsed > 300:
        _fail("correction_proof_expired")
    _verify_file(binding["authorization"])
    _verify_file(binding["integrated_lock"])
    _verify_snapshot(proof["artifact_bundle"], proof["submission"], profile=binding["entry"]["profile"])
    if proof.get("status") != proof.get("native_verdict", {}).get("status"):
        _fail("correction_native_status_binding")
    evidence = proof.get("native_evidence")
    if not isinstance(evidence, dict):
        _fail("correction_native_evidence_missing")
    for item in evidence.values():
        _verify_file(item)
    session_rows = list(ledger.rows(_verify_file(proof["session_ledger"])))
    if not session_rows or session_rows[-1].get("event") != "run_finished":
        _fail("correction_session_ledger_not_closed")
    if proof.get("status") == "PASS":
        required = {"ledger.jsonl", "summary.json", "native/result.json", "native.stdout.bin", "native.stderr.bin",
                    "native.job.json", "native.runtime.json"}
        if not required <= evidence.keys() or ledger.read_json(evidence["summary.json"]["path"]) != proof["native_verdict"]:
            _fail("correction_native_proof_incomplete")
        rows = list(ledger.rows(evidence["ledger.jsonl"]["path"]))
        work = [row for row in rows if row.get("event") == "work_finished" and row.get("work_kind") == "artifact-verify"]
        if (not rows or rows[-1].get("event") != "run_finished" or len(work) != 1
                or work[0].get("status") != "PASS" or work[0].get("failure") is not None
                or any(not stream.get("complete") for stream in work[0].get("streams", {}).values())
                or set(work[0].get("streams", {})) != {"stdout", "stderr"}):
            _fail("correction_native_work_unverified")
        started = [row for row in rows if row.get("event") == "work_started" and row.get("work_kind") == "artifact-verify"]
        if (len(started) != 1 or started[0].get("work_id") != work[0].get("work_id")
                or started[0].get("submitted_sha256") != evidence["native.job.json"]["sha256"]
                or work[0].get("exit_code") != 0 or started[0].get("stdin") != "DEVNULL"):
            _fail("correction_native_job_binding")
        for key in ("stdout", "stderr"):
            stream = work[0]["streams"][key]
            if any(stream.get(field) != evidence["native." + key + ".bin"][field] for field in ("path", "sha256", "bytes")):
                _fail("correction_native_stream_binding")
        native = proof["native_verdict"].get("result", {})
        if (ledger.read_json(evidence["native/result.json"]["path"]) != native
                or native.get("document_closed") is not True or native.get("gui_up") != 0
                or native.get("runtime_binding") != evidence["native.runtime.json"]):
            _fail("correction_native_closed_result_binding")
        if proof["evidence_mode"] == "live":
            owned = work[0].get("native_evidence") or {}
            if owned.get("owned_pid") != native.get("owned_pid") or owned.get("cleanup_status") != "exited":
                _fail("correction_native_owned_cleanup_binding")
        expected = {key + "_sha256": binding["source_files"][binding["entry"][identity]]["sha256"]
                    for key, identity in (("manifest", "input_manifest"), ("prepared", "prepared"),
                                          ("card", "card"), ("context", "context"))}
        expected["bundle_sha256"] = proof["artifact_bundle"]["sha256"]
        if native.get("bindings") != expected:
            _fail("correction_native_same_card_binding")
        job = ledger.read_json(evidence["native.job.json"]["path"])
        if (job.get("operation") != "artifact-verify" or job.get("profile", "c-s1") != binding["entry"]["profile"]
                or Path(job["bundle"]).absolute() != Path(proof["artifact_bundle"]["path"])):
            _fail("correction_native_job_binding")
        if (any(started[0].get("inputs", {}).get(key.removesuffix("_sha256")) != value for key, value in expected.items())
                or started[0].get("inputs", {}).get("runtime_binding") != evidence["native.runtime.json"]["sha256"]):
            _fail("correction_native_frozen_input_binding")
        for artifact in native.get("artifacts", {}).values():
            _verify_file(artifact)
        if set(native.get("artifacts", {})) != {"native", "step"}:
            _fail("correction_final_artifacts_missing")
    history, latest = _check_history(root, record["id"])
    if latest != reference:
        _fail("correction_proof_not_latest")
    return proof, history


def _user_correction(root, summary, record, verdict):
    reference = verdict["correction_proof"]
    history, latest = _check_history(root, record["id"])
    if verdict["correction_elapsed_s"] == 0:
        if reference is not None or latest is not None:
            _fail("correction_no_edit_path_cannot_hide_checks")
        return None, history
    if reference is None:
        _fail("correction_positive_elapsed_requires_native_proof")
    return _validated_correction(root, summary, record, reference)


def _handover_history(record, corrections):
    return [dict(kind="first", first_handover=record.get("first_handover"), worker_status=record.get("worker_status"),
                 error=record.get("error"), stop_reason=record.get("stop_reason"),
                 artifact_bundle=record.get("artifact_bundle"), artifact_verdict=record.get("artifact_verdict"),
                 judge=record.get("judge"), snapshot=corrections[0]["first_handover_snapshot"] if corrections else None)] + [
        dict(kind="human_correction", check_id=item["check_id"], status=item["status"],
             artifact_bundle=item["artifact_bundle"], native_verdict=item["native_verdict"],
             elapsed_s=item["elapsed_s"]) for item in corrections]
