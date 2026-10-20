"""One LIBRARY_ONLY (k=1) Propose-Probe-Compose cycle.

Run: python -m h2.cycle --task A-box-pocket-fillet --candidates 3
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import uuid

from .edits import apply_edits, validate_proposals
from .library import materialize_library
from .runtime import (CadRunner, CodexClient, elapsed, extract_code, extract_json,
                      sum_tokens, token_usage)
from .statistics import cache_metrics, decide, rank_group, summarize

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ("Use only the information in this prompt. Do not read tools/fixtures, existing "
            "reports, evidence, v4, or other project files. Do not use tools, run commands, "
            "write files, access the network, request expanded permissions, or delegate. ")


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


class BudgetExceeded(RuntimeError):
    pass


class Cycle:
    def __init__(self, root=ROOT, *, task="A-box-pocket-fillet", candidates=3,
                 max_calls=100, repeats=1, model=None, cycle_id=None, llm=None, cad=None):
        if task != "A-box-pocket-fillet":
            raise ValueError("MVP supports only A-box-pocket-fillet")
        if type(candidates) is not int or candidates < 1 or type(max_calls) is not int or not 1 <= max_calls <= 100:
            raise ValueError("candidates must be positive and max_calls must be 1..100")
        if type(repeats) is not int or repeats < 1:
            raise ValueError("repeats must be a positive integer")
        self.root = Path(root).resolve()
        self.task_id, self.count, self.max_calls = task, candidates, max_calls
        self.repeats, self.model = repeats, model
        self.id = cycle_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
        if not self.id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in self.id):
            raise ValueError("Unsafe cycle id")
        self.report = self.root / "reports" / "h2" / self.id
        self.cad_report = self.root / "reports" / "cad-run" / "h2" / self.id
        self.library = self.root / "h2" / "library" / "cad-freecad.jsonl"
        self.llm, self.cad = llm or CodexClient(), cad or CadRunner(self.root)
        self.data = {"schema": "h2.cycle.v1", "cycle_id": self.id, "task_id": task,
                     "mode": "LIBRARY_ONLY", "k": 1, "created_at": now(),
                     "max_llm_calls": max_calls, "repeats": repeats, "requested_model": model,
                     "decision_rule": "D15", "std_convention": "sample; N=1 uses zero",
                     "cache_policy": {"intent": "warm_after_one_excluded_warmup_run",
                                      "guaranteed_equal_cache": False,
                                      "limitation": "Provider controls cache hits; measured per call and group"},
                     "status": "running", "runs": {}, "groups": {}, "execution_order": [],
                     "llm_calls": [], "stages": {}, "proposals": [], "library_entries": []}

    def call(self, prompt, harness, role):
        if len(self.data["llm_calls"]) >= self.max_calls:
            raise BudgetExceeded(f"LLM call budget exhausted ({self.max_calls})")
        index = len(self.data["llm_calls"]) + 1
        settings = harness["executor"]
        record = {"call_id": index, "role": role, "requested_model": settings.get("model"),
                  "model": None, "model_source": None, "model_reason": "call_not_completed",
                  "cache_phase": "warmup" if role.startswith("warmup/") else "post_warmup",
                  "reasoning_effort": settings["reasoning_effort"], "tokens": token_usage(None),
                  "wall_ms": None, "log_dir": str((self.report / "llm" / str(index)).relative_to(self.root))}
        self.data["llm_calls"].append(record)
        start = time.perf_counter()
        try:
            response = self.llm(prompt, effort=settings["reasoning_effort"],
                                model=settings.get("model"), log_dir=self.root / record["log_dir"])
            record.update({key: response.get(key) for key in ("tokens", "wall_ms", "exit_code", "error")})
            record.update(model=response.get("model"), model_source=response.get("model_source"),
                          model_reason=response.get("model_reason") if response.get("model") else
                          response.get("model_reason", "model_not_reported_by_client"))
            record["cache"] = cache_metrics(record["tokens"])
            if response.get("error"):
                raise RuntimeError(response["error"])
            return response["text"]
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            if record["wall_ms"] is None:
                record["wall_ms"] = elapsed(start)
            raise

    def execute(self, name, harness, task):
        start = time.perf_counter()
        calls_start = len(self.data["llm_calls"])
        run = {"harness": harness, "attempts": [], "geometry_pass": False,
               "attempt_count": 0, "tokens": token_usage(None), "wall_ms": None,
               "included_in_comparison": name != "warmup"}
        self.data["runs"][name] = run
        self.data["execution_order"].append(name)
        previous, feedback = None, None
        try:
            for number in range(1, harness["max_attempts"] + 1):
                prompt = (BOUNDARY + "Return exactly one fenced Python block defining build(doc). "
                          "Build in the supplied FreeCAD document and return its PartDesign Body.\n"
                          + json.dumps({"task": task, "rules": harness["rules"],
                                        "snippets": harness["snippets"], "previous_code": previous,
                                        "feedback": feedback}, ensure_ascii=False))
                answer = self.call(prompt, harness, f"{name}/a{number}")
                attempt = {"number": number, "llm_call_id": len(self.data["llm_calls"])}
                run["attempts"].append(attempt)
                try:
                    previous = extract_code(answer)
                except (ValueError, SyntaxError) as exc:
                    result = {"status": "failed", "probe_status": None, "failed_phase": "response",
                              "message_code": "invalid_build_response", "next_actor": "sol"}
                    attempt.update(result=result, response_error=str(exc), cad_wall_ms=0)
                else:
                    inputs = self.cad_report / name / "inputs"
                    inputs.mkdir(parents=True, exist_ok=True)
                    script = inputs / f"a{number}-build.py"
                    script.write_text(previous, encoding="utf-8")
                    out_dir = self.cad_report / name / f"a{number}"
                    cad = self.cad(script, out_dir, self.task_id)
                    result = cad["result"]
                    attempt.update(result=result, cad_wall_ms=cad["wall_ms"],
                                   cad_exit_code=cad["exit_code"],
                                   script=str(script.relative_to(self.root)),
                                   out_dir=str(out_dir.relative_to(self.root)))
                    save_json(self.report / f"{name}-a{number}-cad.json", cad)
                if result.get("probe_status") == "pass":
                    run["geometry_pass"] = True
                    break
                if result.get("next_actor") != "sol":
                    break
                feedback = {key: result.get(key) for key in harness["feedback_fields"]}
        finally:
            run["attempt_count"] = len(run["attempts"])
            run["tokens"] = sum_tokens(self.data["llm_calls"][calls_start:])
            run["wall_ms"] = elapsed(start)
            run["cache"] = cache_metrics(run["tokens"])
            run["final_code_summary"] = self.code_summary(previous)
        return run

    def run_name(self, group, repeat):
        return group if self.repeats == 1 else f"{group}-r{repeat}"

    def execute_group(self, group, harness, task):
        names = []
        for repeat in range(1, self.repeats + 1):
            name = self.run_name(group, repeat)
            self.execute(name, harness, task)
            names.append(name)
        result = summarize(names, self.data["runs"])
        self.data["groups"][group] = result
        return result

    @staticmethod
    def code_summary(code):
        if not code:
            return None
        tree = ast.parse(code)
        return {"sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                "line_count": len(code.splitlines()),
                "api_calls": sorted({ast.unparse(node.func) for node in ast.walk(tree)
                                     if isinstance(node, ast.Call)})}

    def stage(self, name, action):
        start = time.perf_counter()
        self.data["stages"][name] = {"status": "running", "wall_ms": None}
        try:
            value = action()
            self.data["stages"][name]["status"] = "completed"
            return value
        except Exception:
            self.data["stages"][name]["status"] = "failed"
            raise
        finally:
            self.data["stages"][name]["wall_ms"] = elapsed(start)

    def propose(self, base, run0, history):
        prompt = (BOUNDARY + f"Propose exactly {self.count} distinct harness edits. "
                  'Return JSON only: {"candidates":[{"edit":[{"op":"add_rule","value":"..."}],'
                  '"rationale":"when and why this helps"}]}. '
                  "Allowed ops: add_rule/string, add_snippet/string (guidance or API example, not executable "
                  "hooks), set_max_attempts/integer 1..4, set_feedback_fields/nonempty unique list from "
                  "status,failed_phase,probe_status,predicate_diff,message_code,next_actor,measurements,"
                  "cad_exit_code,script_completed,cleanup_status,timings_ms, "
                  "set_reasoning_effort/low|medium. Each operation has only op and value. "
                  "Each candidate has only edit and rationale. No repeated scalar op within an edit.\n"
                  + json.dumps({"base": base, "run0": run0,
                                "baseline_traces": [self.data["runs"][name] for name in run0["run_names"]],
                                "prior_library": history}, ensure_ascii=False))
        proposer = {"executor": {**base["executor"], "reasoning_effort": "medium"}}
        for retry in range(2):
            answer = self.call(prompt, proposer, "propose" if retry == 0 else "propose-retry")
            try:
                return validate_proposals(extract_json(answer), self.count)
            except (ValueError, TypeError) as exc:
                if retry:
                    raise ValueError(f"Invalid proposals after one retry: {exc}") from exc
                prompt += "\nYour invalid response:\n" + answer + "\nValidation error: " + str(exc)

    def compose(self, base, task, candidates):
        run0 = self.data["groups"]["run0"]
        for i, candidate in enumerate(candidates):
            candidate["variant"] = f"probe-{i + 1}"
            candidate["decision"] = decide(run0, self.data["groups"][candidate["variant"]])
            candidate["verdict"] = candidate["decision"]["verdict"]
        supported = sorted((c for c in candidates if c["verdict"] == "supported"),
                           key=lambda c: rank_group(self.data["groups"][c["variant"]]))
        composition = {"supported": [c["variant"] for c in supported], "adopted": [],
                       "fallback": False, "selected_run": "run0", "harness": base}
        self.data["composition"] = composition
        if not supported:
            return
        edits = [c["edit"] for c in supported]
        harness = apply_edits(base, edits)
        composed = self.execute_group("composed", harness, task)
        composition["decision"] = decide(run0, composed)
        if composition["decision"]["verdict"] == "supported":
            composition.update(adopted=[c["variant"] for c in supported],
                               selected_run="composed", harness=harness)
        else:
            best = supported[0]
            composition.update(adopted=[best["variant"]], fallback=True,
                               selected_run=best["variant"], harness=apply_edits(base, [best["edit"]]))
        # A candidate consisting only of overridden scalar settings was not adopted.
        selected = composition["harness"]
        def retained(candidate):
            for operation in candidate["edit"]:
                op, value = operation["op"], operation["value"]
                if op in ("add_rule", "add_snippet"):
                    if value in selected["rules" if op == "add_rule" else "snippets"]:
                        return True
                elif op == "set_reasoning_effort":
                    if selected["executor"]["reasoning_effort"] == value:
                        return True
                elif selected[op.removeprefix("set_")] == value:
                    return True
            return False
        composition["adopted"] = [c["variant"] for c in supported
                                  if c["variant"] in composition["adopted"] and retained(c)]
        # Record scalar losers explicitly; additive parts of a partially conflicting edit may survive.
        composition["conflicts"] = []
        assigned = {}
        for candidate in supported:
            for op in candidate["edit"]:
                if op["op"].startswith("set_"):
                    key = op["op"]
                    if key in assigned and assigned[key] != op["value"]:
                        composition["conflicts"].append({"variant": candidate["variant"], **op,
                                                            "kept_value": assigned[key]})
                    else:
                        assigned[key] = op["value"]

    def append_library(self, candidates):
        adopted = self.data["composition"]["adopted"]
        for candidate in candidates:
            probe = self.data["groups"][candidate["variant"]]
            run0 = self.data["groups"]["run0"]
            entry = {"entry_id": uuid.uuid4().hex, "domain": "cad-freecad", "task_id": self.task_id,
                     "cycle_id": self.id, "created_at": now(), "edit": candidate["edit"],
                     "verdict": candidate["verdict"],
                     "contrast": {"run0": self.metrics(run0), "probe": self.metrics(probe)},
                     "decision": candidate["decision"],
                     "lesson": (candidate["rationale"] + " Measured verdict: " + candidate["verdict"]
                                + "; run0=" + json.dumps(self.metrics(run0))
                                + "; probe=" + json.dumps(self.metrics(probe)) + "."),
                     "adopted_in_composed": candidate["variant"] in adopted}
            self.library.parent.mkdir(parents=True, exist_ok=True)
            with self.library.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + "\n")
            self.data["library_entries"].append(entry)

    @staticmethod
    def metrics(run):
        return {key: run[key] for key in ("n", "run_names", "geometry_pass", "pass_count", "pass_rate",
                                         "attempt_count", "tokens", "wall_ms", "statistics", "cache")}

    def run(self):
        start = time.perf_counter()
        self.report.mkdir(parents=True, exist_ok=False)
        try:
            base = json.loads((self.root / "h2" / "base" / "harness.json").read_text(encoding="utf-8"))
            if self.model:
                base["executor"]["model"] = self.model
            task = json.loads((self.root / "h2" / "tasks" / f"{self.task_id}.json").read_text(encoding="utf-8"))
            # Snapshot before Run0: entries from this cycle can never influence proposals.
            records = [json.loads(line) for line in self.library.read_text(encoding="utf-8").splitlines()
                       if line.strip()] if self.library.exists() else []
            history = materialize_library(records)
            self.data["prior_library_record_count"] = len(records)
            self.data["prior_library_count"] = len(history)
            self.stage("warmup", lambda: self.execute("warmup", base, task))
            run0 = self.stage("run0", lambda: self.execute_group("run0", base, task))
            candidates = self.stage("propose", lambda: self.propose(base, run0, history))
            self.data["proposals"] = candidates

            def probes():
                # Repetition outermost: c1,c2,c3; c1,c2,c3; ... never concurrent.
                for repeat in range(1, self.repeats + 1):
                    for i, candidate in enumerate(candidates):
                        self.execute(self.run_name(f"probe-{i + 1}", repeat),
                                     apply_edits(base, [candidate["edit"]]), task)
                for i in range(1, len(candidates) + 1):
                    names = [self.run_name(f"probe-{i}", r) for r in range(1, self.repeats + 1)]
                    self.data["groups"][f"probe-{i}"] = summarize(names, self.data["runs"])

            self.stage("probe", probes)
            self.stage("compose", lambda: self.compose(base, task, candidates))
            self.stage("library", lambda: self.append_library(candidates))
            self.data["status"] = "completed"
            selected = self.data["groups"][self.data["composition"]["selected_run"]]
            self.data["geometry_pass"], self.data["pass_rate"] = selected["geometry_pass"], selected["pass_rate"]
        except Exception as exc:
            self.data["status"] = "budget_exhausted" if isinstance(exc, BudgetExceeded) else "failed"
            self.data["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            self.data["completed_at"] = now()
            self.data["wall_ms"] = elapsed(start)
            self.data["tokens"] = sum_tokens(self.data["llm_calls"])
            measured_ids = {a["llm_call_id"] for name, r in self.data["runs"].items() if name != "warmup"
                            for a in r["attempts"]}
            self.data["comparison_tokens"] = sum_tokens([c for c in self.data["llm_calls"] if c["call_id"] in measured_ids])
            self.data["cache"] = cache_metrics(self.data["tokens"])
            self.data["comparison_wall_ms"] = sum(r["wall_ms"] for name, r in self.data["runs"].items()
                                                  if name != "warmup")
            self.data["llm_call_count"] = len(self.data["llm_calls"])
            self.data["cad_wall_ms"] = sum(a.get("cad_wall_ms", 0) for r in self.data["runs"].values()
                                          for a in r["attempts"])
            save_json(self.report / "cycle.json", self.data)
        return self.data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="A-box-pocket-fillet", choices=["A-box-pocket-fillet"])
    parser.add_argument("--candidates", type=int, default=3)
    parser.add_argument("--max-llm-calls", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("-m", "--model", default="gpt-6.1-sol")
    args = parser.parse_args()
    if args.candidates < 1 or not 1 <= args.max_llm_calls <= 100 or args.repeats < 1:
        parser.error("candidates/repeats must be positive; max-llm-calls must be 1..100")
    cycle = Cycle(task=args.task, candidates=args.candidates, max_calls=args.max_llm_calls,
                  repeats=args.repeats, model=args.model)
    data = cycle.run()
    print(json.dumps({"cycle_id": cycle.id, "status": data["status"],
                      "geometry_pass": data.get("geometry_pass"), "tokens": data["tokens"],
                      "pass_rate": data.get("pass_rate"), "repeats": args.repeats, "model": args.model,
                      "wall_ms": data["wall_ms"], "report": str(cycle.report / "cycle.json")}, ensure_ascii=False))
    return 0 if data["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
