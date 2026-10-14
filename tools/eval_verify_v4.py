"""VERIFY v4 ledger, recorded requests, immutable freeze and authorized holdout."""
import argparse
import csv
import json
from pathlib import Path

if __package__:
    from . import cad_agent, cad_verify_v3_agent, cad_verify_v4_agent as agent
    from . import cad_verify_v4_ledger as ledger, eval_verify_v3 as v3
    from . import cad_verify_v4_freeze as freezing, cad_verify_v4_live as live, cad_verify_v4_pilot as pilot
    from .cad_verify_guard import CLARIFICATION_FIELDS, Stop
else:
    import cad_agent, cad_verify_v3_agent, cad_verify_v4_agent as agent
    import cad_verify_v4_ledger as ledger, eval_verify_v3 as v3
    import cad_verify_v4_freeze as freezing, cad_verify_v4_live as live, cad_verify_v4_pilot as pilot
    from cad_verify_guard import CLARIFICATION_FIELDS, Stop

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design/cad-harness-verify-v4"


def contract_text(root=ROOT):
    schema = (Path(root)/"design/cad-harness-mvp/build-schema.json").read_text(encoding="utf-8")
    source = ("Return only complete Python source defining build(doc) and returning its Body. "
              "Allowed imports: FreeCAD, Part, Sketcher, math. No file, shell, network, document lifecycle, save or probe operations.")
    return ("# Existing output contracts (verbatim)\n\n## Spec\n" + cad_agent.spec_contract(schema)
            + "\n\n## Compiler capabilities\n" + cad_verify_v3_agent.CAPABILITY_CONTRACT
            + "\n\n## Clarification\nVERIFY clarification contract: needs_clarification is a list of necessary missing field IDs only, "
              "never natural-language questions or invented values. Allowed field IDs: "
            + ", ".join(CLARIFICATION_FIELDS) + ".\n\n## Source\n" + source
            + "\n\n## Repair\nRetain this output path for CAD repair; no unsupported or clarification fallback.\n"
            + cad_verify_v3_agent.REPAIR_CONTRACT + "\n")


def preflight(policy=DESIGN/"policy.json", *, root=ROOT):
    policy = ledger.read_json(policy)
    if policy.get("schema") != "cad-harness.policy.v4" or policy.get("live_authorized_calls") != 0:
        raise Stop("p12_policy_must_be_offline")
    if policy != ledger.read_json(Path(root)/"design/cad-harness-verify-v4/policy.json"):
        raise Stop("policy_override_not_skill_bound")
    if policy.get("route_caps") != v3.CAPS:
        raise Stop("route_cap_drift")
    if policy.get("quota") != dict(consult_percent=55, stop_percent=60, max_snapshot_age_s=300):
        raise Stop("quota_policy_drift")
    folder = Path(root)/"skills/cad-harness-v4"
    if (folder/"modeling.md").read_bytes() != (Path(root)/"skills/freecad-modeling/SKILL.md").read_bytes():
        raise Stop("modeling_prose_drift")
    if (folder/"contracts.md").read_text(encoding="utf-8") != contract_text(root):
        raise Stop("output_contract_drift")
    skill = agent.bundle(root)
    return dict(status="offline_ready", live_calls=0, live_cad_runs=0,
                skill_sha256=ledger.sha(skill), policy_sha256=ledger.sha(json.dumps(policy, sort_keys=True).encode()),
                manifest="not_frozen", holdout="not_run", pilot="not_run",
                overload_robustness="UNVERIFIED", pending=policy["pending_live_decisions"])


def cost_csv(path, journal):
    fields = ("episode_id", "attempt_id", "operation", "charged", "provider_rejected", "wall_s",
              *ledger.USAGE_KEYS, "price", "price_missing_reason")
    with Path(path).open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for event in ledger.rows(journal):
            if event["event"] != "attempt_finished":
                continue
            row = {k: event.get(k) for k in fields}
            row.update((event.get("usage") or {}).get("values", {}))
            row.update(price=(event.get("price") or {}).get("amount"),
                       price_missing_reason=(event.get("price") or {}).get("missing_reason"))
            writer.writerow(row)


def replay_summary(document):
    if not isinstance(document.get("groups"), dict) or not isinstance(document.get("summary"), dict):
        raise ValueError("recorded_aggregate_contract")
    rows = sorted((row for group in document["groups"].values() for row in group),
                  key=lambda row: row["sequence"])
    order = dict(entries=[row["manifest_entry"] for row in rows])
    expected = v3.expected_order()
    actual = [(r["group"], r["case"], r["round"], r["route"], r["min_calls"], r["max_calls"])
              for r in order["entries"]]
    if actual != expected:
        raise ValueError("recorded_order_binding")
    old = document["summary"]
    result = v3.summarize(rows, order, stopped=old["stop_reason"],
                          versions_consistent=old["versions_consistent"], deadline_ok=old["deadline_ok"])
    return dict(schema="cad-harness.aggregate-replay.v4", evidence_mode="historical_replay",
                summary=result, identical_summary=result == old,
                fresh_holdout="not_run", pilot="not_run", overload_robustness="UNVERIFIED",
                live_calls=0, live_cad_runs=0)


def check_manifest(path):
    # A supplied commitment can be checked offline; this command never creates one.
    if path is None:
        return None
    path = Path(path)
    value = ledger.read_json(path)
    for name, digest in value.get("files", {}).items():
        candidate = (ROOT/name).resolve()
        if not candidate.is_relative_to(ROOT) or ledger.sha(candidate.read_bytes()) != digest:
            raise Stop("sha_manifest_mismatch")
    return ledger.sha(path.read_bytes())


def run_replay(roster, run_dir, phase):
    if roster is None:
        if phase != "pilot":
            raise Stop("p12_offline_only_replay_required")
        out = ledger.new_directory(run_dir)
        result = dict(schema="cad-harness.batch.v4", evidence_mode="offline",
                      pilot="not_run", reason="no_user_tasks_or_human_judge",
                      live_calls=0, live_cad_runs=0)
        ledger.write_json(out/"summary.json", result)
        return result
    roster = Path(roster).resolve()
    value = ledger.read_json(roster)
    if value.get("schema") != "cad-harness.replay-roster.v4":
        raise ValueError("replay_roster_schema")
    out = ledger.new_directory(run_dir)
    results, spent, stop_reason = [], 0, None
    maximum = 163 if phase == "holdout" else 40
    clock = agent.ReplayClock()
    with ledger.Journal(out/"ledger.jsonl", out.name, "offline_batch", clock=clock, now=clock.utc) as journal:
        journal.append("run_started", evidence_mode="offline_replay", live_calls=0, live_cad_runs=0)
        for index, item in enumerate(value["entries"], 1):
            def local(key):
                candidate = (roster.parent/item[key]).resolve()
                if not candidate.is_relative_to(roster.parent):
                    raise ValueError("replay_roster_path")
                return candidate
            card = ledger.read_json(local("acceptance"))
            route = card["route"]
            reservation = card.get("max_calls", v3.CAPS[route])
            if spent+reservation > maximum:
                stop_reason = "insufficient_call_budget"
                break
            child = out/("request-%03d" % index)
            result, code = agent.request(local("request"), local("acceptance"), child,
                                         replay=local("replay"))
            results.append(dict(index=index, exit_code=code, result=result))
            for event in ledger.rows(child/"ledger.jsonl"):
                if event["event"] in ("run_started", "run_finished"):
                    continue
                imported = {k: v for k, v in event.items() if k not in
                            ("schema", "event", "event_id", "run_id", "phase", "recorded_at", "monotonic_s", "boot_id")}
                for key in ("episode_id", "attempt_id", "retry_parent_id"):
                    if imported.get(key) is not None:
                        imported[key] = str(index)+":"+str(imported[key])
                journal.append(event["event"], **imported, source_ledger=str(child/"ledger.jsonl"),
                               source_event_id=event["event_id"], source_clock_id=event["boot_id"])
            charged = result["all_work"]["charged_calls"]["total"]
            clock.advance(result["operational_wall_s"])
            if result["unfinished_attempts"] or charged is None and result["physical_model_attempts"]:
                stop_reason = "incomplete_call_evidence"
                break
            spent += charged or 0
            message = result.get("driver_message") or ""
            if any(key in message for key in ("quota_", "offline_transport", "invalid_cad", "harness", "insufficient_call_budget")):
                stop_reason = message
                break
        journal.append("run_finished", wall_s=clock(), active_s=None,
                       wall_missing_reason=None, stop_reason=stop_reason)
    costs = ledger.summarize(out/"ledger.jsonl")
    cost_csv(out/"calls.csv", out/"ledger.jsonl")
    result = dict(schema="cad-harness.batch.v4", evidence_mode="offline_replay",
                  requested_phase=phase, fresh_holdout="not_run", pilot="not_run",
                  entries=results, planned=len(value["entries"]), unstarted=len(value["entries"])-len(results),
                  stop_reason=stop_reason, costs=costs, live_calls=0, live_cad_runs=0)
    ledger.write_json(out/"summary.json", result)
    return result


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    command = commands.add_parser("ledger", help="read old records; write a new informational ledger")
    command.add_argument("--source-root", required=True)
    command.add_argument("--history", choices=("v3",), required=True)
    command.add_argument("--aggregate")
    command.add_argument("--rate-source")
    command.add_argument("--run-dir", required=True)
    command = commands.add_parser("preflight", help="offline policy/skill equivalence, no executable probing")
    command.add_argument("--policy", default=str(DESIGN/"policy.json"))
    command = commands.add_parser("request", help="one request through the unchanged driver with recorded responses")
    command.add_argument("--request", required=True)
    command.add_argument("--acceptance", required=True)
    command.add_argument("--manifest")
    command.add_argument("--replay")
    command.add_argument("--rate-source")
    command.add_argument("--run-dir", required=True)
    command = commands.add_parser("run", help="recorded batch or frozen-manifest-authorized live holdout")
    command.add_argument("--phase", choices=("holdout", "pilot"), required=True)
    command.add_argument("--manifest")
    command.add_argument("--replay")
    command.add_argument("--sealed-input")
    command.add_argument("--tasks")
    command.add_argument("--run-dir", required=True)
    command = commands.add_parser("aggregate", help="re-evaluate recorded rows with existing v3 predicates")
    command.add_argument("--replay-aggregate")
    command.add_argument("--manifest")
    command.add_argument("--holdout")
    command.add_argument("--pilot", default="not_run")
    command.add_argument("--run-dir", required=True)
    command = commands.add_parser("freeze", help="bind public inputs; live authorization requires its own evidence file")
    command.add_argument("--policy", default=str(DESIGN/"policy.json"))
    command.add_argument("--holdout-commitment")
    command.add_argument("--authorization")
    command.add_argument("--generator-model", default="openai-codex/gpt-6.1-sol")
    command.add_argument("--thinking", default="xhigh")
    command.add_argument("--omp", default="omp")
    command.add_argument("--quota-snapshot")
    command.add_argument("--run-dir")
    command = commands.add_parser("pilot-bundle", help="freeze verbatim original context and declared attachments; never enroll or generate")
    command.add_argument("--source-jsonl", required=True)
    command.add_argument("--locator", required=True, type=int)
    command.add_argument("--request", required=True)
    command.add_argument("--attachments", required=True)
    command.add_argument("--conversation-id")
    command.add_argument("--run-dir", required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    attempted_live = False
    try:
        if args.command == "freeze":
            if not args.holdout_commitment or not args.run_dir:
                raise Stop("freeze_requires_public_commitment_and_run_dir")
            preflight(args.policy)
            value = freezing.freeze(args.policy, args.holdout_commitment, args.run_dir,
                                    generator_model=args.generator_model, thinking=args.thinking,
                                    omp=args.omp, quota_snapshot=args.quota_snapshot,
                                    authorization_path=args.authorization)
        elif args.command == "pilot-bundle":
            value = pilot.bundle(args.source_jsonl, args.locator, args.request, args.attachments,
                                 args.run_dir, conversation_id=args.conversation_id)
        elif args.command == "preflight":
            value = preflight(args.policy)
        elif args.command == "ledger":
            value = ledger.backfill(args.source_root, args.run_dir, aggregate=args.aggregate,
                                    rate_source=args.rate_source)
            cost_csv(Path(args.run_dir)/"calls.csv", Path(args.run_dir)/"ledger.jsonl")
        elif args.command == "request":
            preflight()
            check_manifest(args.manifest)
            value, code = agent.request(args.request, args.acceptance, args.run_dir,
                                        replay=args.replay, rate_source=args.rate_source)
            cost_csv(Path(args.run_dir)/"calls.csv", Path(args.run_dir)/"ledger.jsonl")
            print(json.dumps(value, ensure_ascii=True, allow_nan=False))
            return code
        elif args.command == "run":
            if args.sealed_input:
                if args.phase != "holdout" or not args.manifest or args.replay or args.tasks:
                    raise Stop("live_holdout_requires_only_frozen_manifest_and_sealed_input")
                attempted_live = True
                value = live.run_holdout(args.manifest, args.sealed_input, args.run_dir)
                cost_csv(Path(args.run_dir)/"calls.csv", Path(args.run_dir)/"ledger.jsonl")
            else:
                if args.tasks:
                    raise Stop("pilot_requires_frozen_enrollment_not_raw_tasks")
                preflight()
                check_manifest(args.manifest)
                value = run_replay(args.replay, args.run_dir, args.phase)
        else:
            source = args.replay_aggregate
            if source is None:
                raise Stop("p12_recorded_aggregate_required")
            check_manifest(args.manifest)
            value = replay_summary(ledger.read_json(source))
            value.update(source=str(Path(source).resolve()), source_sha256=ledger.sha(Path(source).read_bytes()))
            out = ledger.new_directory(args.run_dir)
            recorded = ledger.read_json(source)
            ordered = sorted((row for group in recorded["groups"].values() for row in group), key=lambda row: row["sequence"])
            v3.write_segmented_aggregate((out/"summary.json", out/"rows.csv"), value, ordered)
        # Keep the backfill's detailed provenance on disk, not in terminal output.
        display = {k: v for k, v in value.items() if k not in ("per_episode", "historical_reconciliation")}
        if isinstance(display.get("summary"), dict):
            display["summary"] = {k: display["summary"][k] for k in ("valid_suite", "complete", "thresholds", "bar_met")}
        print(json.dumps(display, ensure_ascii=True, allow_nan=False))
        return 1 if value.get("status") == "INCOMPLETE" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="failed", reason=str(exc),
                              live_calls=None if attempted_live else 0,
                              live_cad_runs=None if attempted_live else 0)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
