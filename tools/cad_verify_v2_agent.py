"""Explicit VERIFY v2 driver. No changes to the MVP/v1 generation loops."""
import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

if __package__:
    from . import cad_agent as agent, cad_spec, cad_verify_v2_probe as probe, eval_verify
    from .cad_verify_guard import clarification, CLARIFICATION_FIELDS, QUESTIONS, q_score
    from .cad_verify_v2_guard import Budget, Stop
else:
    import cad_agent as agent, cad_spec, cad_verify_v2_probe as probe, eval_verify
    from cad_verify_guard import clarification, CLARIFICATION_FIELDS, QUESTIONS, q_score
    from cad_verify_v2_guard import Budget, Stop


def feedback(target, candidate, result):
    """Keep live failed checks; large reachability proof stays in the CAD report."""
    measured = json.loads(json.dumps(result.get("measurements")))
    if measured and isinstance(measured.get("editability"), dict):
        measured["editability"].pop("dimension_evidence", None)
    details = result.get("predicate_details") or {}
    observed = {key: result.get(key) for key in agent.FEEDBACK_KEYS if key not in ("measurements", "predicate_details")}
    observed.update(measurements=measured, predicate_details={key: value for key, value in details.items() if key != "checks"})
    observed["predicate_details"]["checks"] = [row for row in details.get("checks", []) if row.get("passed") is False]
    return {"source" if target == "source" else "build_spec": candidate, "result": observed}


def run_driver(name, codex, input_text, gold_path, *, root=agent.ROOT, runner=None, clock=None,
               route="spec", max_calls=None, rubric=None, answer=None, fault=None, guard=None, preview=False):
    if route not in ("source", "spec", "ask", "completion") or not name.endswith("-mvp1"):
        raise ValueError("verify_v2_options")
    if route == "completion" and (not isinstance(answer, str) or not rubric or preview):
        raise ValueError("verify_v2_answer_contract")
    if route == "ask" and not rubric:
        raise ValueError("verify_v2_rubric_required")
    cap = 4 if route in ("source", "completion") else 1 if route == "ask" else 3
    max_calls = cap if max_calls is None else max_calls
    if not 1 <= max_calls <= cap:
        raise ValueError("verify_v2_call_contract")
    root = Path(root).resolve()
    budget = Budget(max_calls, clock or (guard.clock if guard else None), preview)
    if guard: guard.before_episode(max_calls)
    gold_path = Path(gold_path).resolve() if gold_path else None
    gold = probe.load_gold(gold_path) if gold_path else None
    completion_text = input_text+"\n"+answer if answer is not None else None
    if route != "ask":
        if gold is None or gold["description"] != (completion_text if route == "completion" else input_text):
            raise ValueError("description_gold_identity")
        if not preview and (gold["provenance"]["authority"] != "human" or gold["provenance"]["confirmed"] is not True):
            raise ValueError("eval_human_gold_required")
    if rubric and rubric.get("description_sha256") != agent.digest(input_text):
        raise ValueError("rubric_description_binding")
    runner = runner or subprocess.run
    out = agent.new_run_dir(root, name)
    report = dict(schema="cad-harness.cad_agent.verify2", run_id=name, mode="description", probe_profile="verify-v2",
        task_id=gold["case_id"] if gold else rubric["case_id"], description_sha256=agent.digest(input_text),
        input_sha256=agent.digest(input_text), gold_sha256=hashlib.sha256(gold_path.read_bytes()).hexdigest() if gold else None,
        started_at=agent.utc(), status="failed", message_code=None, calls=[], attempts=[], first_response=None,
        unsupported_to_source=False, final_out_dir=None, geometry_ok=None, route=route, preview=preview,
        repair_eligible=False, repair_not_attempted_reason=None, fault=fault.record if fault else None)
    if answer is not None:
        report.update(answer_sha256=agent.digest(answer), completion_input_sha256=agent.digest(completion_text),
                      completion_reached=False, initial_q_score=None, initial_critical_invention=False)
    target, previous, candidate, last_spec = "spec", None, None, None
    prompt = input_text

    def invoke(purpose):
        nonlocal prompt, previous
        budget.check_call(purpose)
        timeout = budget.sol_timeout(purpose)
        contract = agent.spec_contract(schema_text) if target == "spec" else (
            "Return only complete Python source defining build(doc) and returning its Body. "
            "Allowed imports: FreeCAD, Part, Sketcher, math. No file, shell, network, document lifecycle, save or probe operations.")
        if target == "spec":
            contract += ("\nVERIFY clarification contract: needs_clarification is a list of necessary missing field IDs only, "
                "never natural-language questions or invented values. Allowed field IDs: "+", ".join(CLARIFICATION_FIELDS)+".")
        if budget.stage == "repair": contract += "\nRetain this output path for CAD repair; no unsupported or clarification fallback."
        context = agent.developer_context(skill, contract, previous)
        row = dict(call=budget.calls+1, kind=target, purpose=purpose, stage=budget.stage,
            context_sha256=agent.digest(context), prompt_sha256=agent.digest(prompt), started_at=agent.utc(), usage=None,
            timeout_s=timeout, elapsed_s=budget.clock()-budget.started)
        parent = Path(tempfile.gettempdir()).resolve()
        if parent.is_relative_to(root): raise ValueError("exec_temp_inside_repository")
        tick = budget.clock()
        try:
            with tempfile.TemporaryDirectory(prefix="cad-verify-v2-", dir=parent) as directory:
                work = Path(directory); last = work/"last.txt"
                argv = agent.exec_argv(codex, work, last, prompt, context)
                snapshot = guard.before_call() if guard else None
                budget.call(purpose)
                if guard: row["quota_snapshot"] = snapshot
                row["invoked"] = True
                report["calls"].append(row)
                if route == "completion" and purpose == "interpretation":
                    report["completion_reached"] = True
                completed = runner(argv, cwd=str(work),
                    capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False,
                    stdin=subprocess.DEVNULL, timeout=timeout)
                row["exit"] = completed.returncode
                row["session_id"], row["usage"] = agent.exec_metadata(completed.stdout)
                if completed.returncode != 0 or not last.is_file(): raise ValueError("exec_nonzero_or_missing_final")
                final = last.read_text(encoding="utf-8-sig")
                if str(work).lower() in final.lower() or work.as_posix().lower() in final.lower(): raise ValueError("private_source")
                (out/("last-c%d.txt" % budget.calls)).write_bytes(agent.clean(final).encode("utf-8"))
                return final
        finally:
            row.update(ended_at=agent.utc(), wall_ms=(budget.clock()-tick)*1000)

    def parse(final):
        if target == "source":
            value = agent.source_from_final(final)
            agent.cad_run.source_contract(ast.parse(value))
            return "source", value, None
        raw = cad_spec.read_json(agent.strip_final_fence(final, "json", "spec"))
        if isinstance(raw, dict) and set(raw) == {"unsupported"}:
            if not isinstance(raw["unsupported"], list) or not raw["unsupported"] or any(not isinstance(s, str) or not s for s in raw["unsupported"]):
                raise ValueError("unsupported_contract")
            return "unsupported", raw, raw
        if isinstance(raw, dict) and set(raw) == {"needs_clarification"}:
            clarification(raw)
            return "needs_clarification", raw, raw
        return "spec", cad_spec.validate_spec(raw), raw

    try:
        skill = (root/"skills/freecad-modeling/SKILL.md").read_text(encoding="utf-8")
        schema_text = (root/"design/cad-harness-mvp/build-schema.json").read_text(encoding="utf-8")
        report.update(skill_sha256=agent.digest(skill), schema_sha256=agent.digest(schema_text),
            compiler_sha256=hashlib.sha256(Path(cad_spec.__file__).read_bytes()).hexdigest(),
            probe_sha256=hashlib.sha256(Path(probe.__file__).read_bytes()).hexdigest(),
            shared_probe_sha256=hashlib.sha256(Path(probe.v1.__file__).read_bytes()).hexdigest(),
            agents_sha256=agent.agents_identity(root), settings={**budget.settings(), "model": agent.MODEL,
                "effort": agent.EFFORT, "disabled": list(agent.DISABLED), "sandbox": "read-only", "skip_git_repo_check": True})
        if route == "ask":
            report["settings"].update(max_cad_attempts=0, parse_calls=0, repair_calls=0)
        version = runner([codex, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                         shell=False, stdin=subprocess.DEVNULL, timeout=budget.remaining())
        if version.returncode != 0: raise ValueError("cli_version_failed")
        report["cli_version"] = agent.clean(version.stdout.strip())
        purpose = "question" if route in ("ask", "completion") else "interpretation"
        while True:
            final = invoke(purpose)
            budget.remaining()
            initial = budget.calls == 1
            if initial: report["first_response"] = dict(kind="invalid", sha256=agent.digest(final))
            try:
                kind, candidate, raw = parse(final)
                if initial:
                    first = report["first_response"]
                    first.update(kind=kind, raw=raw)
                    if kind == "spec":
                        bounds = candidate.get("regions", [{}])[0].get("bounds", []) if candidate.get("regions") else []
                        first["binding_defaults_ok"] = len(bounds) == 6 and abs(bounds[0]+bounds[1]) < 1e-9 and abs(bounds[2]+bounds[3]) < 1e-9 and bounds[4] == 0
                    if kind == "needs_clarification": first["fields"] = clarification(candidate)
                if route == "ask":
                    if kind == "needs_clarification":
                        report["questions"] = [QUESTIONS.get(f, f) for f in report["first_response"]["fields"]]
                    report.update(status="first_response", message_code="first_response_stop")
                    break
                if route == "completion" and initial:
                    score, invention = q_score(report["first_response"], False, report["task_id"], rubric)
                    report.update(initial_q_score=score, initial_critical_invention=invention)
                    (out/"first-response.json").write_bytes(json.dumps(report["first_response"], ensure_ascii=False).encode("utf-8"))
                    if not score or invention:
                        report.update(message_code="completion_initial_question_miss", completion_not_reached_reason="initial_question_miss")
                        break
                    report.update(questions=[QUESTIONS.get(f, f) for f in report["first_response"]["fields"]])
                    prompt, previous, purpose = completion_text, None, "interpretation"
                    continue
                if kind == "needs_clarification":
                    report.update(message_code="completion_additional_question" if route == "completion" else "clarification_stop")
                    break
                if kind == "unsupported":
                    if budget.stage == "repair" or route != "source": raise ValueError("unsupported_route")
                    report["unsupported_to_source"] = True
                    target, previous, purpose = "source", None, "source"
                    continue
                if fault:
                    candidate = fault.inject(target, candidate)
                    if target == "spec": candidate = cad_spec.validate_spec(candidate)
                    else:
                        candidate = agent.source_from_final(candidate)
                        agent.cad_run.source_contract(ast.parse(candidate))
            except ValueError as exc:
                if initial and report["first_response"].get("raw") is None and target == "spec":
                    try: report["first_response"]["raw"] = cad_spec.read_json(agent.strip_final_fence(final, "json", "spec"))
                    except ValueError: pass
                if route == "ask":
                    report.update(status="first_response", message_code=str(exc)); break
                if route == "completion" and initial:
                    _, invention = q_score(report["first_response"], False, report["task_id"], rubric)
                    report.update(initial_q_score=0, initial_critical_invention=invention,
                        completion_not_reached_reason="invalid_initial_question", message_code=str(exc))
                    (out/"first-response.json").write_bytes(json.dumps(report["first_response"], ensure_ascii=False).encode("utf-8"))
                    break
                if str(exc) in ("private_source", "unsupported_route") or preview or budget.counts["parse_repair"]:
                    raise
                invalid = agent.invalid_feedback(final, str(exc))
                previous, purpose = ({**previous, **invalid} if budget.stage == "repair" else invalid), "parse_repair"
                continue
            if preview:
                report.update(status="preview", message_code="confirmation_required", preview_kind=target)
                (out/("preview-source.py" if target == "source" else "preview-spec.json")).write_text(
                    candidate if target == "source" else cad_spec.canonical(candidate), encoding="utf-8")
                break
            if target == "spec":
                canonical = cad_spec.canonical(candidate)
                if canonical == last_spec: raise ValueError("unchanged_spec")
                last_spec = canonical
                (out/("build-spec-c%d.json" % budget.calls)).write_text(canonical, encoding="utf-8")
                source = cad_spec.compile_spec(candidate)
            else: source = candidate
            timeout = math.floor(budget.cad_timeout())
            if timeout < 1: raise Stop("episode_stage_deadline_exceeded")
            source_path = out/("input-a%d.py" % (budget.attempts+1))
            source_path.write_bytes(source.encode("utf-8"))
            cad_out = out/("a%d-mvp1" % (budget.attempts+1))
            argv = [sys.executable, "-B", str(root/"tools/cad_run.py"), "--script", str(source_path),
                "--out-dir", str(cad_out), "--timeout-s", str(timeout), "--recipe", "freecadcmd", "--probe-profile", "verify-v2",
                "--gold", str(gold_path), "--task", report["task_id"], "--generator", "compiler" if target == "spec" else "agent",
                "--end-to-end-s", str(budget.remaining()), "--verification-timeout-s", "90" if budget.stage == "repair" else "300"]
            tick = budget.clock()
            budget.cad()
            completed = runner(argv, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace",
                               shell=False, stdin=subprocess.DEVNULL, timeout=budget.remaining(reserve=0))
            result = agent.loads(completed.stdout)
            if (not isinstance(result, dict) or result.get("schema") != "cad-harness.cad_run.v0"
                    or result.get("task_id") != report["task_id"] or result.get("probe_profile") != "verify-v2"
                    or result.get("script_sha256") != agent.digest(source) or result.get("gold_sha256") != report["gold_sha256"]
                    or agent.loads((cad_out/"result.json").read_text(encoding="utf-8")) != result):
                raise ValueError("invalid_cad_result")
            report["attempts"].append(dict(attempt=budget.attempts, stage=budget.stage, source_sha256=agent.digest(source),
                out_dir=cad_out.relative_to(root).as_posix(), wall_ms=(budget.clock()-tick)*1000,
                started_elapsed_s=tick-budget.started, ended_elapsed_s=budget.clock()-budget.started,
                build_timeout_s=timeout, reimport_timeout_s=90 if budget.stage == "repair" else 300, result=agent.clean(result)))
            report.update(final_out_dir=report["attempts"][-1]["out_dir"], geometry_ok=result.get("geometry_ok"))
            if budget.clock() > min(budget.deadline, budget.stage_deadline):
                raise Stop("episode_stage_deadline_exceeded")
            if fault:
                fault.observe(result, budget.calls)
                if fault.record.get("observed") and not fault.record.get("detected"):
                    raise ValueError("fault_false_pass" if result.get("geometry_ok") is True else "fault_detection_mismatch")
            problem = eval_verify.harness_failure(report)
            if problem: raise ValueError(problem)
            if completed.returncode == 0:
                if not eval_verify.result_pass(result): raise ValueError("invalid_cad_success")
                report.update(status="ok", message_code="completed"); break
            reason = agent.repair_reason(result)
            if reason: raise ValueError(reason)
            if budget.attempts != 1:
                report.update(message_code="cad_repair_failed"); break
            report["repair_eligible"] = True
            budget.begin_repair()
            previous, purpose = feedback(target, candidate, result), "repair"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["message_code"] = agent.clean(str(exc)) or type(exc).__name__
    finally:
        report.update(ended_at=agent.utc(), wall_ms=(budget.clock()-budget.started)*1000,
            llm_calls=budget.calls, cad_attempts=budget.attempts, budget_counts=budget.counts,
            parse_repairs=budget.counts["parse_repair"], repair_calls=budget.counts["repair"])
        if route == "completion" and not report["completion_reached"]:
            report.setdefault("completion_not_reached_reason", report["message_code"] or "initial_question_not_accepted")
        if report["repair_eligible"] and budget.counts["repair"] == 0:
            reason = report["message_code"] or "repair_slot_not_used"
            report["repair_not_attempted_reason"] = reason
            if not any(s in reason for s in ("quota_", "sha_", "agents", "deadline", "reservation", "budget")):
                report["message_code"] = "harness_repair_not_invoked:"+reason
        if report["wall_ms"] >= 900000:
            report.update(status="failed", message_code="episode_deadline_exceeded")
        if guard:
            report["shared_deadline_remaining_s"] = max(0, guard.deadline-guard.clock())
            if guard.clock() >= guard.deadline: report.update(status="failed", message_code="shared_deadline_exceeded")
        with (out/"driver-run.json").open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False)
    return report, 0 if report["status"] in ("ok", "preview", "first_response") else 1
