"""Offline VERIFY v4 journal, complete stream capture and nullable accounting."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import time
import uuid

if __package__:
    from . import cad_agent, cad_verify_v3_agent
else:
    import cad_agent, cad_verify_v3_agent

SCHEMA = "cad-harness.ledger.v4"
USAGE_KEYS = cad_agent.USAGE_KEYS
BOOT_ID = str(uuid.uuid4())  # Process clock identity, never an inferred OS boot time.
TAIL_BYTES = 16384


def utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return cad_agent.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, ensure_ascii=False, allow_nan=False, indent=2)
        file.write("\n")


def new_directory(path):
    path = Path(path).absolute()
    if path.exists() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("output_exists_or_linked")
    if any((p / "driver-run.json").exists() or (p / "suite-run.json").exists()
           for p in path.parents):
        raise ValueError("output_inside_historical_run")
    path.mkdir(parents=True, exist_ok=False)
    return path


class Journal:
    def __init__(self, path, run_id, phase, *, clock=time.monotonic, now=utc):
        self.path = Path(path)
        self.run_id, self.phase, self.clock, self.now = run_id, phase, clock, now
        self.sequence = 0
        self.file = self.path.open("x", encoding="utf-8", newline="\n")

    def append(self, event, **fields):
        self.sequence += 1
        row = dict(schema=SCHEMA, event=event, event_id=self.sequence,
                   run_id=self.run_id, phase=self.phase, recorded_at=self.now(),
                   monotonic_s=self.clock(), boot_id=BOOT_ID, **fields)
        self.file.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        self.file.flush()
        return row

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


def rows(path):
    with Path(path).open(encoding="utf-8") as file:
        for line in file:
            row = cad_agent.loads(line)
            if row.get("schema") != SCHEMA:
                raise ValueError("ledger_schema")
            yield row


def nullable_total(values, *, money=False):
    values = list(values)
    known = [v for v in values if v is not None]
    subtotal = sum((Decimal(str(v)) for v in known), Decimal(0)) if money else sum(known)
    convert = (lambda v: str(v)) if money else (lambda v: v)
    return dict(total=convert(subtotal) if values and len(known) == len(values) else None,
                known_subtotal=convert(subtotal), expected=len(values), known=len(known),
                missing=len(values)-len(known),
                missing_reason="no_observations" if not values else
                "missing_contributions" if len(known) != len(values) else None)


def unknown_usage(reason="usage_not_recorded"):
    return dict(values=dict.fromkeys(USAGE_KEYS),
                missing_reasons=dict.fromkeys(USAGE_KEYS, reason), sources=[])


def usage_totals(events):
    """Per-turn deltas are deduplicated; a session total supersedes its deltas."""
    sessions = defaultdict(lambda: {"delta": {}, "cumulative": None})
    conflict = False
    for index, event in enumerate(events or []):
        if not isinstance(event, dict) or not isinstance(event.get("values"), dict):
            conflict = True
            continue
        session = event.get("session_id") or "attempt"
        mode = event.get("mode", "delta")
        values = {k: event["values"].get(k) for k in USAGE_KEYS}
        for key, value in values.items():
            if value is not None and (type(value) is not int or value < 0):
                values[key] = None
        if mode == "cumulative":
            prior = sessions[session]["cumulative"]
            if prior and any(values[k] is not None and prior[k] is not None
                             and values[k] < prior[k] for k in USAGE_KEYS):
                conflict = True
            sessions[session]["cumulative"] = values
        elif mode == "delta":
            identity = str(event.get("event_id", event.get("event_index", index)))
            prior = sessions[session]["delta"].get(identity)
            if prior is not None and prior != values:
                conflict = True
            sessions[session]["delta"][identity] = values
        else:
            conflict = True
    if conflict:
        return unknown_usage("usage_identity_or_semantics_conflict")
    selected = []
    for session in sessions.values():
        selected.extend([session["cumulative"]] if session["cumulative"] is not None
                        else session["delta"].values())
    result = unknown_usage()
    for key in USAGE_KEYS:
        result["values"][key] = nullable_total(v[key] for v in selected)["total"]
        result["missing_reasons"][key] = (None if result["values"][key] is not None
                                           else "usage_field_not_recorded")
    result["sources"] = [dict(session_id=e.get("session_id"),
                              event_id=e.get("event_id", e.get("event_index", i)),
                              mode=e.get("mode", "delta")) for i, e in enumerate(events or [])]
    return result


def usage_from_stream(path):
    """Read bounded lines, retaining usage events rather than the entire stream."""
    events, session, complete = [], None, True
    with Path(path).open("rb") as file:
        index = 0
        while True:
            line = file.readline(1048577)
            if not line:
                break
            if len(line) > 1048576:
                complete = False
                while line and not line.endswith(b"\n"):
                    line = file.readline(1048577)
                continue
            try:
                event = cad_agent.loads(line.decode("utf-8"))
            except UnicodeError:
                complete = False
                index += 1
                continue
            except ValueError:
                if b'"turn.completed"' in line or b'"token_count"' in line:
                    complete = False
                index += 1
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "thread.started":
                session = event.get("thread_id")
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                events.append(dict(session_id=session, event_id=event.get("turn_id", index),
                                   mode="delta", values=event["usage"]))
            payload = event.get("payload") or {}
            if isinstance(payload, dict) and payload.get("type") == "token_count":
                info = payload.get("info") or {}
                if isinstance(info.get("total_token_usage"), dict):
                    events.append(dict(session_id=session, event_id=index, mode="cumulative",
                                       values=info["total_token_usage"]))
            index += 1
    return usage_totals(events) if complete else unknown_usage("usage_stream_parse_incomplete")


def price(usage, source=None, *, identity=None):
    result = dict(amount=None, currency=None, status="unknown", missing_reason="no_user_rate_source",
                  source=None, source_sha256=None, categories=None)
    if source is None:
        return result
    raw = Path(source).read_bytes()
    card = cad_agent.loads(raw.decode("utf-8-sig"))
    result.update(source=card.get("source"), source_sha256=sha(raw), currency=card.get("currency"),
                  product=card.get("product"), model=card.get("model"), tier=card.get("tier"),
                  effective_date=card.get("effective_date"))
    required = ("source", "effective_date", "currency", "product", "model", "tier", "categories")
    if card.get("provided_by_user") is not True or any(not card.get(k) for k in required):
        result["missing_reason"] = "rate_provenance_incomplete"
        return result
    if not identity or any(identity.get(k) != card[k] for k in ("product", "model", "tier")):
        result["missing_reason"] = "rate_product_model_tier_mismatch"
        return result
    total, categories = Decimal(0), []
    try:
        for category in card["categories"]:
            quantity = Decimal(0)
            if not category.get("fields"):
                raise ValueError("rate_category_fields")
            for key, coefficient in category["fields"].items():
                if key not in USAGE_KEYS or usage["values"][key] is None:
                    raise ValueError("required_billing_quantity_unknown")
                quantity += Decimal(str(coefficient)) * usage["values"][key]
            rate = Decimal(str(category["rate_per_million"]))
            if not rate.is_finite() or not quantity.is_finite() or rate < 0 or quantity < 0:
                raise ValueError("invalid_billing_quantity_or_rate")
            amount = quantity * rate / Decimal(1000000)
            categories.append(dict(name=category["name"], quantity=str(quantity),
                                   rate_per_million=str(rate), amount=str(amount)))
            total += amount
    except (KeyError, TypeError, ValueError, InvalidOperation):
        result["missing_reason"] = "invalid_or_missing_billing_category"
        return result
    result.update(amount=str(total), status="verified_rate_estimate", missing_reason=None,
                  categories=categories)
    return result


class StreamCapture:
    """Archive exact bytes with bounded provider-parser/display memory."""
    def __init__(self, path, *, parse=False):
        self.path = Path(path)
        self.file = self.path.open("xb")
        self.digest = hashlib.sha256()
        self.size, self.tail = 0, b""
        self.parser = cad_verify_v3_agent.StreamCapture(parse=parse)
        import codecs
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def feed(self, raw):
        if not isinstance(raw, bytes):
            raise TypeError("capture_requires_bytes")
        self.file.write(raw)
        self.digest.update(raw)
        self.size += len(raw)
        self.tail = (self.tail + raw)[-TAIL_BYTES:]
        decoded = self.decoder.decode(raw)
        if "\ufffd" in decoded:
            self.parser.complete = False
        self.parser.feed(decoded)

    def finish(self):
        try:
            self.file.flush()
            decoded = self.decoder.decode(b"", final=True)
            if "\ufffd" in decoded:
                self.parser.complete = False
            self.parser.feed(decoded)
            self.parser.finish()
        finally:
            self.file.close()
        return dict(path=str(self.path), sha256=self.digest.hexdigest(), bytes=self.size,
                    complete=True, missing_reason=None)


def summarize(path):
    events = list(rows(path))
    starts = {e["attempt_id"]: e for e in events if e["event"] == "attempt_started"}
    ends = {e["attempt_id"]: e for e in events if e["event"] == "attempt_finished"}
    attempts = [ends.get(key, dict(start, charged=None, usage=unknown_usage("unfinished_attempt"),
                                  price=price(unknown_usage()))) for key, start in starts.items()]
    model = [e for e in attempts if e.get("operation") == "model"]
    retained = [e for e in model if e.get("retained_segment") is True]
    archived = [e for e in model if e.get("retained_segment") is False]
    def costs(selected):
        currencies = {e.get("price", {}).get("currency") for e in selected
                      if e.get("price", {}).get("amount") is not None}
        money = nullable_total((e.get("price", {}).get("amount") for e in selected), money=True)
        if len(currencies) > 1:
            money.update(total=None, known_subtotal=None, missing_reason="mixed_currencies")
        return dict(charged_calls=nullable_total(e.get("charged") for e in selected),
                    tokens={k: nullable_total(e.get("usage", unknown_usage())["values"][k]
                                              for e in selected) for k in USAGE_KEYS},
                    price=money, currency=next(iter(currencies)) if len(currencies) == 1 else None)
    episodes = [e for e in events if e["event"] == "episode_finished"]
    run = next((e for e in reversed(events) if e["event"] == "run_finished"), {})
    work_starts = {e["work_id"]: e for e in events if e["event"] == "work_started"}
    work_ends = {e["work_id"]: e for e in events if e["event"] == "work_finished"}
    work_streams = [stream for e in work_ends.values() for stream in (e.get("streams") or {}).values()]
    work_elapsed = nullable_total(e.get("wall_s") for e in work_ends.values())
    if work_starts.keys() - work_ends.keys():
        work_elapsed.update(total=None, missing_reason="unfinished_deterministic_work")
    captured = sum(stream.get("complete") is True for attempt in attempts
                   for stream in (attempt.get("streams") or {}).values())
    return dict(schema="cad-harness.ledger-summary.v4", physical_model_attempts=len(model),
                conservative_reserved_calls=sum(e.get("charged") is not False for e in model),
                exempt_overload_attempts=sum(e.get("provider_rejected") is True for e in model),
                cad_attempts=sum(e.get("operation") == "cad" for e in attempts),
                unfinished_attempts=len(starts.keys()-ends.keys()),
                capture=dict(expected=2*len(attempts), complete=captured,
                             missing_or_partial=2*len(attempts)-captured),
                all_work=costs(model), retained_segments=costs(retained), archived_work=costs(archived),
        per_episode={e["episode_id"]: dict(costs([a for a in model if a.get("episode_id") == e["episode_id"]]),
                                          wall_s=e.get("wall_s"), active_s=e.get("active_s"),
                                          wall_missing_reason=None if e.get("wall_s") is not None else "episode_endpoints_unknown")
                             for e in episodes},
                operational_wall_s=run.get("wall_s"), active_s=run.get("active_s"),
                wall_missing_reason=run.get("wall_missing_reason", "run_not_finished"),
                wait_s=nullable_total(e.get("actual_s") for e in events if e["event"] == "wait_finished"),
                event_counts=dict(Counter(e["event"] for e in events)),
                deterministic_work=dict(
                    started=len(work_starts), finished=len(work_ends),
                    unfinished=len(work_starts.keys()-work_ends.keys()), wall_s=work_elapsed,
                    by_kind=dict(Counter(e["work_kind"] for e in work_starts.values())),
                    statuses=dict(Counter(e.get("status", "INCOMPLETE") for e in work_ends.values())),
                    capture=dict(expected=2*len(work_starts),
                                 complete=sum(s.get("complete") is True for s in work_streams),
                                 missing_or_partial=2*len(work_starts)-sum(s.get("complete") is True for s in work_streams))),
                full_cost_known=bool(model and costs(model)["price"]["total"] is not None))


def historical_stream(root, item):
    if not item or not item.get("path"):
        return dict(path=None, sha256=None, bytes=None, complete=False, missing_reason="not_captured")
    candidate = Path(root) / item["path"]
    if not candidate.is_file():
        return dict(path=None, sha256=None, bytes=None, complete=False, missing_reason="artifact_missing")
    actual_sha = file_sha(candidate)
    size = candidate.stat().st_size
    full = (actual_sha == item.get("full_sha256", item.get("sha256"))
            and size == item.get("full_bytes", item.get("bytes", size)))
    return dict(path=str(candidate), sha256=actual_sha, bytes=size if full else None,
                complete=full, missing_reason=None if full else "historical_tail_only",
                captured_bytes=size, declared_full_bytes=item.get("full_bytes"))


def backfill(source_root, run_dir, *, aggregate=None, rate_source=None):
    """Read v3 records only; create a distinct, informational v4 ledger."""
    source_root = Path(source_root).resolve()
    aggregate = Path(aggregate) if aggregate else source_root.parent / "aggregate-verify-v3-host-reviewed-r1-solfix-rerun2.json"
    document = read_json(aggregate) if aggregate.is_file() else None
    retained = {r["run"] for rs in document.get("groups", {}).values() for r in rs} if document else set()
    if document and document.get("original_partial", {}).get("run"):
        retained.add(document["original_partial"]["run"])
    # Retained-segment expenditure includes superseded rows within those segments.
    # The final selected scoring rows alone undercount the segment's accepted calls.
    binding, bindings, visited = document, [], set()
    while binding and binding.get("base_aggregate"):
        reference = binding["base_aggregate"]
        path = (source_root.parents[1]/reference["path"]).resolve()
        if not path.is_relative_to(source_root.parents[1]) or path in visited:
            raise ValueError("historical_aggregate_binding_path")
        if file_sha(path) != reference["sha256"]:
            raise ValueError("historical_aggregate_binding_sha")
        visited.add(path)
        bindings.append(reference)
        binding = read_json(path)
        retained.update(r["run"] for rs in binding.get("groups", {}).values() for r in rs)
        if binding.get("original_partial", {}).get("run"):
            retained.add(binding["original_partial"]["run"])
    out = new_directory(run_dir)
    seen, imported = {}, []
    with Journal(out / "ledger.jsonl", out.name, "historical_v3") as journal:
        journal.append("run_started", evidence_mode="historical", source_root=str(source_root))
        for report_path in sorted(source_root.glob("*verify-v3*/driver-run.json")):
            report = read_json(report_path)
            episode = report_path.parent.name
            imported.append(dict(path=str(report_path), sha256=sha(report_path.read_bytes())))
            journal.append("episode_started", episode_id=episode, source=str(report_path),
                           started_at=report.get("started_at"), route=report.get("route"),
                           identity={k: report.get(k) for k in ("skill_sha256", "cli_version", "probe_sha256")})
            for index, call in enumerate(report.get("calls", []), 1):
                if call.get("invoked", True) is not True:
                    continue
                key = (call.get("session_id"), call.get("started_at"), call.get("argv_sha256"))
                # Do not deduplicate unidentifiable calls by a tuple of nulls.
                if any(key) and key in seen:
                    journal.append("attempt_alias", episode_id=episode, source_call=index, attempt_id=seen[key])
                    continue
                attempt = episode + ":model:" + str(index)
                if any(key):
                    seen[key] = attempt
                base = dict(episode_id=episode, attempt_id=attempt, operation="model",
                            logical_call_id=call.get("logical_call", index),
                            retry_parent_id=episode+":model:"+str(index-1) if call.get("transport_attempt", 1) > 1 else None,
                            route=report.get("route"), purpose=call.get("purpose", call.get("kind")),
                            stage=call.get("stage"), retained_segment=episode in retained,
                            source=str(report_path), source_call=index)
                journal.append("attempt_started", **base, started_at=call.get("started_at"))
                usage = usage_totals(call.get("usage"))
                streams = {k: historical_stream(source_root.parents[1], (call.get("transport_artifacts") or {}).get(k))
                           for k in ("stdout", "stderr")}
                if all(v is None for v in usage["values"].values()) and streams["stdout"]["complete"]:
                    usage = usage_from_stream(streams["stdout"]["path"])
                exempt = call.get("provider_rejected") is True and call.get("slot_consumed") is False
                identity = dict(product=report.get("product"), model=report.get("settings", {}).get("model"),
                                tier=report.get("tier"))
                journal.append("attempt_finished", **base, charged=not exempt, provider_rejected=exempt,
                               provider_billing_status=None, billing_missing_reason="invoice_not_recorded",
                               ended_at=call.get("ended_at"), wall_s=call.get("wall_ms", 0)/1000 if call.get("wall_ms") is not None else None,
                               usage=usage, price=price(usage, rate_source, identity=identity), streams=streams,
                               session_id=call.get("session_id"), error=(call.get("provider_summary") or {}).get("error_infos"),
                               request_sha256=call.get("prompt_sha256"), context_sha256=call.get("context_sha256"),
                               argv_sha256=call.get("argv_sha256"), exit_code=call.get("exit"))
                if call.get("wait_requested_s") is not None:
                    journal.append("wait_finished", episode_id=episode, attempt_id=attempt,
                                   requested_s=call["wait_requested_s"], actual_s=call.get("backoff_s"))
            for index, attempt in enumerate(report.get("attempts", []), 1):
                base = dict(episode_id=episode, attempt_id=episode+":cad:"+str(index), operation="cad")
                journal.append("attempt_started", **base)
                journal.append("attempt_finished", **base, result=attempt.get("result"),
                               wall_s=attempt.get("wall_ms", 0)/1000 if attempt.get("wall_ms") is not None else None)
            journal.append("episode_finished", episode_id=episode, started_at=report.get("started_at"),
                           ended_at=report.get("ended_at"), wall_s=report.get("wall_ms", 0)/1000 if report.get("wall_ms") is not None else None,
                           status=report.get("status"), retained_segment=episode in retained)
        for suite in sorted(source_root.glob("*verify-v3*/suite-run.json")):
            value = read_json(suite)
            journal.append("interruption_observed", source=str(suite), source_sha256=sha(suite.read_bytes()),
                           stop_reason=value.get("stop_reason"), duration_s=None,
                           missing_reason="interruption_endpoints_not_recorded")
        journal.append("run_finished", wall_s=None, active_s=None,
                       wall_missing_reason="historical_operational_boundaries_not_recorded")
    summary = summarize(out / "ledger.jsonl")
    summary.update(evidence_mode="historical_backfill", live_calls=0, live_cad_runs=0)
    summary["historical_reconciliation"] = dict(
        aggregate=str(aggregate) if document else None,
        aggregate_sha256=sha(aggregate.read_bytes()) if document else None,
        expected_retained_calls=document.get("real_calls") if document else None,
        expected_total_calls=document.get("total_charged_calls") if document else None,
        retained_matches=summary["retained_segments"]["charged_calls"]["total"] == document.get("real_calls") if document else None,
        total_matches=summary["all_work"]["charged_calls"]["total"] == document.get("total_charged_calls") if document else None,
        imported=imported, bound_base_aggregates=bindings)
    write_json(out / "summary.json", summary)
    return summary
