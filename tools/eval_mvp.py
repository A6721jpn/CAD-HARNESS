"""Fixed DECISION-01 description evaluation; aggregation never launches a model."""
import argparse
from collections import Counter
from contextlib import ExitStack
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

if __package__:
    from . import cad_agent
    from .cad_spec_probe import load_gold, read_json
else:
    import cad_agent
    from cad_spec_probe import load_gold, read_json

ROOT = Path(__file__).resolve().parents[1]
ORDER = ("P1", "P2", "P4", "P5", "P3")
FILES = ("skills/freecad-modeling/SKILL.md", "design/cad-harness-mvp/build-schema.json",
         "design/cad-harness-mvp/eval-v1/schema.json", "tools/cad_agent.py", "tools/cad_spec.py",
         "tools/cad_spec_probe.py", "tools/cad_run.py", "tools/cad_run_freecad.py",
         "tools/cad_verify_freecad.py", "tools/cad_run_probes.py", "tools/eval_mvp.py")
CSV_FIELDS = ("case", "run", "passed", "geometry_ok", "reimport_ok", "editability_ok", "wall_s",
              "sol_calls", "cad_attempts", *cad_agent.USAGE_KEYS, "failure_class")
IDENTITY = ("skill_sha256", "schema_sha256", "compiler_sha256", "probe_sha256", "settings",
            "agents_sha256", "cli_version")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_name(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value or ""):
        raise ValueError("invalid_name")
    return value


def run_path(root, name):
    valid_name(name)
    if not name.endswith("-mvp1"):
        raise ValueError("run_suffix_required")
    path = root.resolve() / "reports/cad-run" / name
    if path.resolve() != path:
        raise ValueError("linked_run_path")
    return path


def plan(prefix):
    valid_name(prefix)
    return [(case, "%s-%s-r%d-mvp1" % (prefix, case, n)) for case in ORDER for n in (1, 2)]


def suite(root):
    specs = {}
    for case in ORDER:
        path = root / "design/cad-harness-mvp/eval-v1" / (case + ".json")
        gold = load_gold(path)
        if gold["case_id"] != case or gold["provenance"]["authority"] != "human" or not gold["provenance"]["confirmed"]:
            raise ValueError("unconfirmed_eval_gold")
        specs[case] = {"path": path, "gold": gold, "sha256": sha(path.read_bytes())}
    return specs


def provider_tokens(report):
    """Provider turn.completed values only; absent/partial totals remain null."""
    calls = report.get("calls", [])
    totals = dict.fromkeys(cad_agent.USAGE_KEYS)
    if not isinstance(calls, list) or not calls:
        return totals
    for key in totals:
        values, complete = [], True
        for call in calls:
            events = call.get("usage") if isinstance(call, dict) else None
            if not isinstance(events, list) or not events:
                complete = False
                continue
            for event in events:
                data = event.get("values") if isinstance(event, dict) else None
                value = data.get(key) if isinstance(data, dict) else None
                if type(value) is int and value >= 0:
                    values.append(value)
                else:
                    complete = False
        if complete and values:
            totals[key] = sum(values)
    return totals


def failure_class(report, result):
    code = str(report.get("message_code") or "")
    if "deadline" in code or "timeout" in code:
        return "timeout"
    if "call_limit" in code or "attempt_limit" in code:
        return "budget"
    if "compiler_native" in code:
        return "compiler_native"
    phase = result.get("failed_phase")
    if phase in ("launch", "dialog", "cleanup", "verification", "export"):
        return phase
    if result.get("save_error_type"):
        return "save"
    if result.get("verification_pass") is False:
        return "verification"
    if result.get("cleanup_status") not in (None, "exited"):
        return "cleanup"
    if phase == "probe":
        return "probe_exception" if result.get("probe_status") == "exception" else "geometry_or_editability"
    if phase == "build":
        return "build"
    if result.get("geometry_ok") is False or result.get("editability_ok") is False:
        return "geometry_or_editability"
    return "interpretation" if not report.get("attempts") else "driver"


def record(root, case, name, spec, elapsed=None, exit_code=None, launch_error=None):
    row = {"case": case, "run": name, "passed": False, "completed": False, "geometry_ok": None, "reimport_ok": None,
           "editability_ok": None, "wall_s": elapsed, "sol_calls": None, "cad_attempts": None,
           "tokens": dict.fromkeys(cad_agent.USAGE_KEYS), "failure_class": launch_error,
           "description_sha256": spec["gold"]["description_sha256"], "gold_sha256": spec["sha256"]}
    try:
        directory = run_path(root, name)
        report = read_json((directory / "driver-run.json").read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("invalid_driver_report")
        row.update(completed=True, tokens=provider_tokens(report), sol_calls=report.get("llm_calls"), cad_attempts=report.get("cad_attempts"),
                   driver_identity={key: report.get(key) for key in IDENTITY})
        if any(report.get(key) is None for key in IDENTITY):
            raise ValueError("missing_driver_version")
        wall = report.get("wall_ms")
        if type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0:
            raise ValueError("invalid_wall_time")
        row["wall_s"] = max(elapsed or 0, wall / 1000)
        if (report.get("schema") != "cad-harness.cad_agent.mvp1" or report.get("mode") != "description"
                or report.get("task_id") != case or report.get("run_id") != name
                or report.get("description_sha256") != row["description_sha256"]
                or report.get("gold_sha256") != spec["sha256"]):
            raise ValueError("eval_report_identity")
        for call in report.get("calls", []):
            if call.get("prompt_sha256") != row["description_sha256"]:
                raise ValueError("changed_description_payload")
        attempts = report.get("attempts")
        if not isinstance(attempts, list):
            raise ValueError("invalid_attempts")
        result = attempts[-1].get("result", {}) if attempts else {}
        if not isinstance(result, dict):
            raise ValueError("invalid_cad_result")
        if attempts:
            final = root / report["final_out_dir"]
            if final.resolve() != final or not final.is_relative_to(directory):
                raise ValueError("invalid_final_directory")
            if read_json((final / "result.json").read_text(encoding="utf-8")) != result:
                raise ValueError("cad_report_mismatch")
            if (result.get("schema") != "cad-harness.cad_run.v0" or result.get("probe_profile") != "mvp-v1"
                    or result.get("task_id") != case or result.get("gold_sha256") != spec["sha256"]):
                raise ValueError("cad_gold_identity")
        row.update(geometry_ok=result.get("geometry_ok"), editability_ok=result.get("editability_ok"))
        verified = result.get("verification") or {}
        if result.get("verification_pass") is not None:
            row["reimport_ok"] = (result.get("verification_pass") is True
                and type(result.get("verification_exit_code")) is int and result["verification_exit_code"] == 0
                and result.get("verification_cleanup_status") == "exited"
                and verified.get("document_closed") is True and verified.get("verification_pass") is True)
        valid_budget = (type(row["sol_calls"]) is int and 1 <= row["sol_calls"] <= 3
                        and type(row["cad_attempts"]) is int and 1 <= row["cad_attempts"] <= 3
                        and len(report["calls"]) == row["sol_calls"] and len(attempts) == row["cad_attempts"])
        row["passed"] = (not launch_error and exit_code in (None, 0) and report.get("status") == "ok"
            and row["geometry_ok"] is True and row["editability_ok"] is True and row["reimport_ok"] is True
            and result.get("status") == "ok" and result.get("probe_pass") is True
            and result.get("probe_status") == "pass" and result.get("script_completed") is True
            and result.get("document_closed") is True and result.get("cleanup_status") == "exited"
            and type(result.get("cad_exit_code")) is int and result["cad_exit_code"] == 0
            and valid_budget and row["wall_s"] <= 900)
        row["failure_class"] = None if row["passed"] else (launch_error or failure_class(report, result))
        if row["wall_s"] > 900:
            row["failure_class"] = "timeout"
        elif not valid_budget and (row["sol_calls"] > 3 or row["cad_attempts"] > 3):
            row["failure_class"] = "budget"
    except FileNotFoundError:
        row["failure_class"] = launch_error or "missing_report"
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        row["failure_class"] = launch_error or "protocol"
    return row


def summarize(rows):
    counts = Counter(row["case"] for row in rows)
    valid_suite = len(rows) == 10 and len({r["run"] for r in rows}) == 10 and counts == Counter({c:2 for c in ORDER})
    identities = [(row.get("driver_identity"),row.get("harness_sha256")) for row in rows if row.get("driver_identity")]
    consistent = bool(identities) and all(identity == identities[0] for identity in identities)
    per_part = {case:{"passes":sum(r["passed"] for r in rows if r["case"] == case),"runs":counts[case]} for case in ORDER}
    passes = sum(row["passed"] for row in rows)
    complete = all(row["completed"] for row in rows)
    tokens = {key:(sum(r["tokens"][key] for r in rows) if all(r["tokens"][key] is not None for r in rows) else None)
              for key in cad_agent.USAGE_KEYS}
    return {"pass_count":passes,"run_count":len(rows),"denominator":10,"per_part":per_part,
            "valid_suite":valid_suite,"complete":complete,"versions_consistent":consistent,"tokens":tokens,
            "bar_met":valid_suite and complete and consistent and passes >= 8 and all(p["passes"] >= 1 for p in per_part.values())}


def evaluate(prefix=None, suffix=None, aggregate_only=False, run_ids=None, root=ROOT, runner=None, clock=None):
    root, runner, clock = root.resolve(), runner or subprocess.run, clock or time.monotonic
    specs = suite(root)
    if run_ids:
        if not aggregate_only or prefix or len(run_ids) != 10 or len(set(run_ids)) != 10:
            raise ValueError("aggregate_requires_ten_distinct_run_ids")
        planned = []
        for name in run_ids:
            report = read_json((run_path(root,name)/"driver-run.json").read_text(encoding="utf-8"))
            if report.get("task_id") not in specs:
                raise ValueError("invalid_aggregate_case")
            planned.append((report["task_id"],name))
        if Counter(c for c,n in planned) != Counter({c:2 for c in ORDER}):
            raise ValueError("aggregate_requires_two_per_part")
    else:
        planned = plan(prefix)
    base = "aggregate-mvp-eval-v1" + ("-" + valid_name(suffix) if suffix else "")
    paths = [root / "reports" / (base + ext) for ext in (".json", ".csv")]
    if any(p.exists() or p.is_symlink() or p.resolve() != p for p in paths):
        raise ValueError("aggregate_exists_or_linked")
    if not aggregate_only:
        if any(run_path(root,n).exists() for c,n in planned):
            raise ValueError("run_exists")
        inputs = run_path(root,prefix + "-eval-inputs-mvp1")
        if inputs.exists():
            raise ValueError("input_directory_exists")
    frozen = {name:sha((root/name).read_bytes()) for name in FILES}
    frozen.update({s["path"].relative_to(root).as_posix():s["sha256"] for s in specs.values()})
    rows = []
    paths[0].parent.mkdir(parents=True,exist_ok=True)
    with ExitStack() as stack:
        outputs = [stack.enter_context(p.open("x",encoding="utf-8",newline="")) for p in paths]
        if not aggregate_only:
            inputs.mkdir(parents=True,exist_ok=False)
            (inputs/"manifest.json").write_text(json.dumps({"plan":planned,"frozen_sha256":frozen}),encoding="utf-8")
        for case,name in planned:
            elapsed, code, error = None, None, None
            if not aggregate_only:
                tick = clock()
                try:
                    if any(sha((root/f).read_bytes()) != h for f,h in frozen.items()):
                        raise ValueError("version_changed")
                    text = specs[case]["gold"]["description"].encode("utf-8")
                    description = inputs / (name + ".txt")
                    with description.open("xb") as output:
                        output.write(text)
                    if sha(description.read_bytes()) != specs[case]["gold"]["description_sha256"]:
                        raise ValueError("description_sha_mismatch")
                    argv = [sys.executable,"-B",str(root/"tools/cad_agent.py"),"--mode","description","--eval",
                            "--gold",str(specs[case]["path"]),"--description-file",str(description),"--run",name]
                    completed = runner(argv,cwd=str(root),capture_output=True,text=True,encoding="utf-8",
                                       errors="replace",shell=False,stdin=subprocess.DEVNULL,timeout=905)
                    code = completed.returncode
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    error = "timeout" if isinstance(exc,subprocess.TimeoutExpired) else "launcher_or_input"
                elapsed = clock()-tick
            row = record(root,case,name,specs[case],elapsed,code,error)
            directory = run_path(root,name)
            if not aggregate_only:
                row["completed"] = True  # An observed launcher failure is a completed miss.
                row["harness_sha256"] = frozen
                directory.mkdir(parents=True,exist_ok=True)
                with (directory/"eval-run.json").open("x",encoding="utf-8") as output:
                    json.dump(row,output,ensure_ascii=False,allow_nan=False)
            elif (directory/"eval-run.json").is_file():
                original = read_json((directory/"eval-run.json").read_text(encoding="utf-8"))
                if original.get("run") != name or original.get("case") != case:
                    raise ValueError("eval_record_identity")
                observed = original.get("wall_s")
                if type(observed) in (int,float) and math.isfinite(observed) and observed >= 0:
                    row = record(root,case,name,specs[case],elapsed=observed,
                                 launch_error=original.get("failure_class") if not original.get("passed") else None)
                if "harness_sha256" in original:
                    row["harness_sha256"] = original["harness_sha256"]
                if original.get("completed") is True:
                    row["completed"] = True
            rows.append(row)
        summary = summarize(rows)
        if not aggregate_only and any(sha((root/f).read_bytes()) != h for f,h in frozen.items()):
            summary.update(versions_consistent=False,bar_met=False)
        document = {"schema":"cad-harness.mvp-eval.v1","created_at":cad_agent.utc(),
                    "aggregate_only":aggregate_only,"frozen_sha256":frozen,"rows":rows,"summary":summary}
        json.dump(document,outputs[0],ensure_ascii=False,allow_nan=False,indent=2)
        writer = csv.DictWriter(outputs[1],fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k:(row["tokens"].get(k) if k in cad_agent.USAGE_KEYS else row.get(k)) for k in CSV_FIELDS})
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix",help="Fresh run prefix; fixed order P1,P2,P4,P5,P3, two each")
    parser.add_argument("--suffix",help="Optional aggregate filename suffix")
    parser.add_argument("--aggregate-only",action="store_true",help="Read existing reports; launch nothing")
    parser.add_argument("--run-ids",nargs="+",help="Ten existing IDs; requires aggregate-only, replaces prefix")
    args = parser.parse_args(argv)
    try:
        result = evaluate(args.prefix,args.suffix,args.aggregate_only,args.run_ids)
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({"status":"input_error","message_code":str(exc)}))
        return 2
    print(json.dumps(result["summary"],allow_nan=False))
    return 0 if result["summary"]["bar_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
