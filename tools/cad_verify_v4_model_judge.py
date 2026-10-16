"""One-shot, manifest-authorized Astra adjudication; importing performs no work."""
import re

if __package__:
    from . import cad_verify_v4_ledger as ledger
    from .cad_verify_guard import Stop
else:
    import cad_verify_v4_ledger as ledger
    from cad_verify_guard import Stop

MODEL = {"model": "openai-codex/gpt-6-astra", "thinking": "max"}
RUBRIC_SCHEMA = "cad-harness.model-rubric.v1"
VERDICT_SCHEMA = "cad-harness.model-verdict.v1"
RESULT_SCHEMA = "cad-harness.model-judgment.v1"
SAME_MODEL_CAVEAT = ("Pilot generation and Astra judgment use the same model, "
                     "openai-codex/gpt-6-astra/max; the user's visual verdict remains authoritative.")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


def _fail(reason):
    raise ValueError("model_judge:" + reason)


def validate_rubric(rubric):
    if (not isinstance(rubric, dict) or set(rubric) != {"schema", "id", "items"}
            or rubric.get("schema") != RUBRIC_SCHEMA or not isinstance(rubric.get("id"), str)
            or not _ID.fullmatch(rubric["id"]) or not isinstance(rubric.get("items"), list)
            or not rubric["items"]):
        _fail("rubric_structure")
    seen = set()
    for item in rubric["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "criterion", "visual"}
                or not isinstance(item["id"], str) or not _ID.fullmatch(item["id"])
                or item["id"] in seen or not isinstance(item["criterion"], str)
                or not item["criterion"].strip() or type(item["visual"]) is not bool):
            _fail("rubric_item")
        seen.add(item["id"])
    return rubric


def _deterministic_status(value):
    """A favorable language verdict cannot erase a nested native/numeric failure."""
    if not isinstance(value, dict):
        return "UNVERIFIED"
    statuses = []
    failed = False

    history = value.get("handover_history", [])
    if (not isinstance(history, list) or any(not isinstance(item, dict) for item in history)
            or ("handover_history" in value and not isinstance(value.get("result"), dict))):
        return "UNVERIFIED"

    def visit(node, historical=False):
        nonlocal failed
        if isinstance(node, dict):
            for key, item in node.items():
                if key == "status" and isinstance(item, str) and not historical:
                    statuses.append(item)
                elif key in ("critical_dimension_error", "fabrication") and item is True:
                    failed = True
                elif isinstance(item, (dict, list)):
                    visit(item, historical or (node is value and key == "handover_history"))
        elif isinstance(node, list):
            for item in node:
                visit(item, historical)
    visit(value)
    if failed or "FAIL" in statuses:
        return "FAIL"
    if value.get("status") != "PASS" or any(item not in ("PASS", "ok") for item in statuses):
        return "UNVERIFIED"
    return "PASS"


def _parse_verdict(text, rubric):
    document = ledger.cad_agent.loads(text)
    if (not isinstance(document, dict)
            or set(document) != {"schema", "rubric_id", "items", "critical_dimension_error", "fabrication"}
            or document["schema"] != VERDICT_SCHEMA or document["rubric_id"] != rubric["id"]
            or type(document["critical_dimension_error"]) is not bool
            or type(document["fabrication"]) is not bool
            or not isinstance(document["items"], list)):
        _fail("verdict_structure")
    expected = {item["id"] for item in rubric["items"]}
    seen = set()
    for item in document["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "status", "reason"}
                or not isinstance(item["id"], str) or item["id"] not in expected or item["id"] in seen
                or item["status"] not in ("PASS", "FAIL", "UNVERIFIED")
                or not isinstance(item["reason"], str) or not item["reason"].strip()):
            _fail("verdict_item")
        seen.add(item["id"])
    if seen != expected:
        _fail("verdict_missing_items")
    return document


def adjudicate(session, record_id, request, deterministic, rubric, *, pool, images=()):
    """Consume at most one call, including malformed answers; never favorable-rescore.

    Images must already be admitted by TrialSession; paths are forwarded as actual
    multimodal inputs. Missing visual evidence does not trigger a text-only guess.
    """
    validate_rubric(rubric)
    if not isinstance(record_id, str) or not _ID.fullmatch(record_id):
        _fail("record_id")
    claims = getattr(session, "_astra_judge_claims", None)
    if claims is None:
        claims = set()
        session._astra_judge_claims = claims
    if record_id in claims:
        _fail("record_already_adjudicated")
    claims.add(record_id)
    images = tuple(images)
    result = dict(schema=RESULT_SCHEMA, record_id=record_id, rubric_id=rubric["id"],
                  status="UNVERIFIED", deterministic_status=_deterministic_status(deterministic),
                  verdict=None, reason=None, model=dict(MODEL), call_attempted=False,
                  evidence_mode=session.mode, same_model_caveat=SAME_MODEL_CAVEAT
                  if session.registration.get("phase") == "pilot" else None)
    if any(item["visual"] for item in rubric["items"]) and not images:
        result["reason"] = "approved_visual_evidence_missing"
    else:
        instructions = ("Judge exactly the registered rubric, once. Return only JSON conforming to "
                        + VERDICT_SCHEMA + ". No prose, markdown, missing items or extra keys. "
                        "For every rubric item return {id,status:PASS|FAIL|UNVERIFIED,reason}. "
                        "Top-level keys: schema,rubric_id,items,critical_dimension_error,fabrication. "
                        "Use actual attached approved images for visual items; missing or inconclusive "
                        "evidence is UNVERIFIED. Never waive numeric/native/critical failures.\n\n"
                        "VERBATIM REQUEST:\n" + request)
        data = dict(target="rubric_verdict", rubric=rubric, deterministic=deterministic,
                    output_schema=VERDICT_SCHEMA)
        result["call_attempted"] = True
        try:
            text = session.call(record_id, instructions, data, pool=pool, **MODEL,
                                purpose="judge", max_calls=1, images=images)
        except Stop as exc:
            if str(exc) != "trial_model_response_failed":
                raise
            # The shared transport retains actual process/error evidence. A
            # missing answer is not an opportunity for a second favorable call.
            result["call_error"] = str(exc)
            text = None
        result["response_sha256"] = ledger.sha(text.encode("utf-8")) if isinstance(text, str) else None
        try:
            verdict = _parse_verdict(text, rubric)
        except (ValueError, TypeError, KeyError, UnicodeError):
            result["reason"] = "malformed_or_missing_verdict"
        else:
            result["verdict"] = verdict
            statuses = [item["status"] for item in verdict["items"]]
            result["status"] = ("FAIL" if "FAIL" in statuses or verdict["critical_dimension_error"]
                                or verdict["fabrication"] else
                                "PASS" if all(value == "PASS" for value in statuses) else "UNVERIFIED")
    if result["deterministic_status"] == "FAIL":
        result.update(status="FAIL", reason="deterministic_failure_precedence")
    elif result["deterministic_status"] != "PASS" and result["status"] == "PASS":
        result.update(status="UNVERIFIED", reason="deterministic_evidence_unverified")
    session.event("model_judged", record_id=record_id, result=result)
    return result


def validate_registration(registration):
    if not isinstance(registration, dict) or registration.get("phase") != "judge":
        _fail("registration_phase")
    entries, files = registration.get("entries"), registration.get("files")
    if not isinstance(entries, list) or not entries or not isinstance(files, dict):
        _fail("registration_roster")
    if (registration.get("judge") != MODEL or registration.get("budget") != {"judge": len(entries)}
            or type(registration["budget"]["judge"]) is not int):
        _fail("registration_model_or_budget")
    seen = set()
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {"id", "request", "deterministic", "rubric", "images"}
                or not isinstance(entry["id"], str) or not _ID.fullmatch(entry["id"])
                or entry["id"] in seen or not isinstance(entry["images"], list)
                or any(not isinstance(key, str) or key not in files for key in
                       (entry["request"], entry["deterministic"], entry["rubric"], *entry["images"]))
                or len(entry["images"]) != len(set(entry["images"]))):
            _fail("registration_entry")
        for key in entry["images"]:
            if files[key].get("role") != "judge_image":
                _fail("image_not_approved")
        seen.add(entry["id"])
    if registration.get("order") != [entry["id"] for entry in entries]:
        _fail("registration_order")
    return registration


def validate_bound_inputs(registration, path_for_id):
    validate_registration(registration)
    for entry in registration["entries"]:
        rubric = validate_rubric(ledger.read_json(path_for_id(entry["rubric"])))
        deterministic = ledger.read_json(path_for_id(entry["deterministic"]))
        if not isinstance(deterministic, dict) or not isinstance(deterministic.get("status"), str):
            _fail("deterministic_record")
        if any(item["visual"] for item in rubric["items"]) and not entry["images"]:
            _fail("approved_visual_evidence_missing")
    return registration


def run(manifest_path, authorization_path, run_dir, *, process=None, native_process=None,
        wall=None, sleep=None, verifier=None):
    if __package__:
        from . import cad_verify_v4_trials as trials
    else:
        import cad_verify_v4_trials as trials
    with trials.TrialSession(manifest_path, authorization_path, run_dir, phase="judge", process=process,
                             native_process=native_process, wall=wall, sleep=sleep, verifier=verifier) as session:
        registration = session.registration
        validate_bound_inputs(registration, session.path)
        records, stopped, terminal_status = [], None, None
        for entry in registration["entries"]:
            record = None
            if stopped is None:
                try:
                    session.check()
                    record = adjudicate(session, entry["id"],
                        session.path(entry["request"]).read_bytes().decode("utf-8"),
                        ledger.read_json(session.path(entry["deterministic"])),
                        ledger.read_json(session.path(entry["rubric"])), pool="judge",
                        images=tuple(session.path(key) for key in entry["images"]))
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    stopped = str(exc)
                    terminal_status = ("INCOMPLETE" if stopped == "budget_exhausted"
                                       or stopped.startswith("quota_") else "FAIL")
                    record = dict(record_id=entry["id"], status=terminal_status, reason=stopped,
                                  error_type=type(exc).__name__)
                    session.event("judge_record_error", record=record)
            if record is None:
                record = dict(record_id=entry["id"], status="NOT_RUN", reason=stopped)
            records.append(record)
        statuses = [record["status"] for record in records]
        value = dict(schema="cad-harness.judge-trial.v1", trial_id=registration["trial_id"],
                     cycle_id=registration["cycle_id"], evidence_mode=session.mode, records=records,
                     denominator=len(registration["entries"]), stop_reason=stopped,
                     status=terminal_status or ("FAIL" if "FAIL" in statuses else
                         "PASS" if all(item == "PASS" for item in statuses) else "UNVERIFIED"),
                     accounting=session.summary(), final_v4_ready=False)
        ledger.write_json(session.out / "summary.json", value)
        return value
