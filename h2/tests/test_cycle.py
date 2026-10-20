"""Stub-only verification. No Codex, LLM, FreeCAD, or tool imports."""
import copy
import itertools
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
import uuid

from h2.cycle import Cycle
from h2.edits import apply_edits, rank, validate_proposals, verdict
from h2.library import materialize_library
from h2.runtime import CadRunner, CodexClient, parse_events, reported_model, token_usage
from h2.supplement import supplement_cycle
from h2.statistics import decide, distribution, summarize

SOURCE = Path(__file__).resolve().parents[1]
CODE = "```python\ndef build(doc):\n    return doc\n```"


class StubLLM:
    def __init__(self, *, invalid_first=False, invalid_always=False, count=3):
        self.prompts = []
        self.proposals = 0
        self.invalid_first, self.invalid_always = invalid_first, invalid_always
        self.count = count

    def __call__(self, prompt, *, effort, model, log_dir):
        self.prompts.append((prompt, effort, log_dir))
        if "Propose exactly" in prompt:
            self.proposals += 1
            candidates = [{"edit": [{"op": "add_rule", "value": f"Guidance {i}"}],
                           "rationale": f"Use guidance {i} for this shape."} for i in range(self.count)]
            text = "{}" if self.invalid_always or (self.invalid_first and self.proposals == 1) else json.dumps({"candidates": candidates})
        else:
            text = CODE
        return {"text": text, "tokens": token_usage({"input_tokens": 10, "cached_input_tokens": 2,
                                                       "output_tokens": 5, "reasoning_tokens": 1}),
                "wall_ms": 1, "exit_code": 0, "error": None}


class StubCAD:
    def __init__(self, *, composed_fail=False, human=False, always_pass=False):
        self.calls = []
        self.composed_fail, self.human, self.always_pass = composed_fail, human, always_pass

    def __call__(self, script, out_dir, task):
        self.calls.append((script, out_dir, task))
        name, attempt = out_dir.parent.name, out_dir.name
        if "-r" in name:
            name = name.rsplit("-r", 1)[0]
        passed = (self.always_pass or not (name == "run0" and attempt == "a1")) and not (
            self.composed_fail and name == "composed")
        return {"result": {"probe_status": "pass" if passed else "fail",
                           # Deliberately inconsistent status: geometry relies ONLY on probe_status.
                           "status": "failed" if passed else "ok", "next_actor": "human" if self.human else "sol",
                           "failed_phase": None if passed else "probe", "predicate_diff": {"bbox": passed},
                           "message_code": "stub"}, "wall_ms": 2, "exit_code": 1}


class CycleTests(unittest.TestCase):
    def setUp(self):
        # Normal inherited directory permissions also work inside the Windows sandbox.
        self.root = SOURCE / "tests" / (".stub-" + uuid.uuid4().hex)
        self.root.mkdir()
        for sub in ("base/harness.json", "tasks/A-box-pocket-fillet.json"):
            target = self.root / "h2" / sub
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((SOURCE / sub).read_bytes())
        self.library = self.root / "h2/library/cad-freecad.jsonl"
        self.library.parent.mkdir(parents=True)
        self.prior = {"entry_id": "prior-entry", "lesson": "Past learning"}
        self.library.write_text(json.dumps(self.prior) + "\n", encoding="utf-8")
        self.base_path = self.root / "h2/base/harness.json"
        self.original_base = self.base_path.read_bytes()

    def tearDown(self):
        self.assertTrue(self.root.resolve().is_relative_to((SOURCE / "tests").resolve()))
        shutil.rmtree(self.root)

    def run_cycle(self, llm=None, cad=None, **kwargs):
        llm, cad = llm or StubLLM(), cad or StubCAD()
        cycle = Cycle(self.root, cycle_id=kwargs.pop("cycle_id", "stub-cycle"), llm=llm, cad=cad, **kwargs)
        clock = itertools.count(1, .001)
        with patch("time.perf_counter", side_effect=lambda: next(clock)):
            result = cycle.run()
        return cycle, result, llm, cad

    def test_full_cycle_appends_library_and_keeps_base_immutable(self):
        cycle, data, llm, cad = self.run_cycle()
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["geometry_pass"])
        self.assertEqual(data["runs"]["run0"]["attempt_count"], 2)
        self.assertEqual(len(cad.calls), 7)
        self.assertEqual(data["llm_call_count"], 8)
        self.assertEqual(data["tokens"]["total"], 120)
        self.assertEqual(data["comparison_tokens"]["total"], 90)
        self.assertEqual(data["cad_wall_ms"], 14)
        self.assertEqual(set(data["stages"]), {"warmup", "run0", "propose", "probe", "compose", "library"})
        self.assertTrue(all(s["wall_ms"] > 0 for s in data["stages"].values()))
        entries = [json.loads(line) for line in self.library.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(entries[0], self.prior)
        self.assertEqual(len(entries), 4)
        self.assertTrue(all(e["verdict"] == "supported" and e["adopted_in_composed"] for e in entries[1:]))
        self.assertEqual(self.base_path.read_bytes(), self.original_base)
        self.assertNotIn("Past learning", llm.prompts[0][0])
        self.assertIn("Past learning", llm.prompts[3][0])
        self.assertEqual(llm.prompts[3][1], "medium")
        self.assertIn('"previous_code": "def build(doc)', llm.prompts[2][0])
        self.assertIn('"predicate_diff": {"bbox": false}', llm.prompts[2][0])
        for script, out_dir, task in cad.calls:
            self.assertTrue(script.is_relative_to(self.root / "reports/cad-run/h2/stub-cycle"))
            self.assertEqual(script.parent.name, "inputs")
        self.assertEqual(json.loads((cycle.report / "cycle.json").read_text(encoding="utf-8"))["status"], "completed")

    def test_composition_failure_falls_back_to_best_single_probe(self):
        _, data, _, cad = self.run_cycle(cad=StubCAD(composed_fail=True))
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["composition"]["fallback"])
        self.assertEqual(data["composition"]["adopted"], ["probe-1"])
        self.assertEqual(data["composition"]["selected_run"], "probe-1")
        self.assertTrue(data["geometry_pass"])
        self.assertEqual(len(cad.calls), 9)  # includes excluded warmup

    def test_human_stops_attempts_and_does_not_support_claim(self):
        _, data, _, _ = self.run_cycle(cad=StubCAD(human=True))
        self.assertEqual(data["runs"]["run0"]["attempt_count"], 1)
        self.assertEqual(data["composition"]["adopted"], [])
        self.assertNotIn("composed", data["runs"])
        self.assertEqual(data["proposals"][0]["verdict"], "confounded")

    def test_proposal_validation_retries_once_only(self):
        _, data, llm, _ = self.run_cycle(llm=StubLLM(invalid_first=True))
        self.assertEqual(data["status"], "completed")
        self.assertEqual(llm.proposals, 2)

    def test_twice_invalid_is_recorded_without_library_write(self):
        before = self.library.read_bytes()
        _, data, llm, cad = self.run_cycle(llm=StubLLM(invalid_always=True))
        self.assertEqual(data["status"], "failed")
        self.assertEqual(llm.proposals, 2)
        self.assertEqual(len(cad.calls), 3)
        self.assertEqual(self.library.read_bytes(), before)

    def test_budget_stops_and_retains_partial_measurements(self):
        cycle, data, llm, cad = self.run_cycle(max_calls=3)
        self.assertEqual(data["status"], "budget_exhausted")
        self.assertEqual(len(llm.prompts), 3)
        self.assertEqual(len(cad.calls), 3)
        self.assertEqual(data["tokens"]["total"], 45)
        self.assertTrue((cycle.report / "cycle.json").exists())
        self.assertEqual(data["library_entries"], [])

    def test_scalar_conflicts_use_first_and_validation_rejects_unsafe_edits(self):
        base = json.loads(self.original_base)
        a = [{"op": "set_max_attempts", "value": 1}, {"op": "add_rule", "value": "extra"}]
        b = [{"op": "set_max_attempts", "value": 4}, {"op": "set_reasoning_effort", "value": "medium"}]
        merged = apply_edits(base, [a, b])
        self.assertEqual(merged["max_attempts"], 1)
        self.assertEqual(merged["executor"]["reasoning_effort"], "medium")
        self.assertEqual(base, json.loads(self.original_base))
        for edit in ([{"op": "exec", "value": "x"}], [{"op": "set_max_attempts", "value": True}],
                     [{"op": "set_reasoning_effort", "value": "high"}],
                     [{"op": "set_feedback_fields", "value": ["unknown"]}], a + [a[0]]):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_proposals({"candidates": [{"edit": edit, "rationale": "why"}]}, 1)
        with self.assertRaises(ValueError):
            validate_proposals({"candidates": [{"edit": a, "rationale": "why"},
                                                {"edit": a[::-1], "rationale": "why"}]}, 2)

    def test_support_tolerance_unknowns_and_ranking(self):
        base = {"geometry_pass": True, "attempt_count": 2, "tokens": {"total": 100},
                "wall_ms": 100, "attempts": []}
        probe = copy.deepcopy(base)
        probe.update(attempt_count=1, wall_ms=109)
        self.assertEqual(verdict(base, probe), "supported")
        probe["wall_ms"] = 111
        self.assertEqual(verdict(base, probe), "unsupported")
        probe["tokens"]["total"] = None
        self.assertEqual(verdict(base, probe), "confounded")
        self.assertLess(rank(base), rank({**base, "geometry_pass": False}))

    def test_cli_adapters_are_stubbed_and_preserve_usage(self):
        events = '\n'.join(json.dumps(e) for e in [
            {"type": "item.completed", "item": {"type": "agent_message", "text": CODE}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20,
                                                     "output_tokens": 30}}])
        text, usage = parse_events(events)
        self.assertEqual(text, CODE)
        self.assertEqual(usage, {"input": 100, "cached_input": 20, "uncached_input": 80, "output": 30,
                                 "reasoning": None, "total": 130})
        self.assertTrue(all(x is None for x in token_usage(None).values()))
        with patch("h2.runtime.subprocess.run") as process:
            process.return_value.stdout = events
            process.return_value.stderr = ""
            process.return_value.returncode = 0
            log_dir = self.root / "reports/h2/calls/1"
            response = CodexClient("stub-codex.exe")("prompt", effort="low", model=None, log_dir=log_dir)
            self.assertEqual(response["tokens"]["total"], 130)
            command = process.call_args.args[0]
            self.assertIn("read-only", command)
            self.assertIn("--skip-git-repo-check", command)
            self.assertIn('approval_policy="never"', command)
            self.assertEqual(list((log_dir / "empty-workdir").iterdir()), [])
        with patch("h2.runtime.subprocess.run") as process:
            process.return_value.stdout = '{"probe_status":"pass","status":"failed"}'
            process.return_value.stderr = ""
            process.return_value.returncode = 1
            response = CadRunner(self.root)(self.root / "input.py", self.root / "reports/cad-run/test", "A-box-pocket-fillet")
            self.assertEqual(response["result"]["probe_status"], "pass")
            self.assertIn("freecadcmd", process.call_args.args[0])

    def test_reasoning_output_tokens_are_a_subset_including_zero(self):
        for reasoning in (0, 7):
            with self.subTest(reasoning=reasoning):
                usage = token_usage({"input_tokens": 100, "output_tokens": 30,
                                     "reasoning_output_tokens": reasoning, "cached_input_tokens": 20})
                self.assertEqual(usage["reasoning"], reasoning)
                self.assertEqual(usage["total"], 130)
        self.assertEqual(token_usage({"output_tokens_details": {"reasoning_tokens": 3}})["reasoning"], 3)

    def test_reported_model_is_runtime_evidence_or_null_with_reason(self):
        events = '\n'.join(json.dumps(e) for e in [
            {"type": "thread.started", "model": "reported-model"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": CODE}},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5,
                                                     "reasoning_output_tokens": 2}}])
        self.assertEqual(reported_model(events)["model"], "reported-model")
        unknown = reported_model('{"type":"thread.started","thread_id":"opaque"}')
        self.assertIsNone(unknown["model"])
        self.assertEqual(unknown["model_reason"], "model_not_reported_in_runtime_events")
        selected = reported_model('{"type":"thread.started"}', "gpt-6.1-sol")
        self.assertEqual(selected["model"], "gpt-6.1-sol")
        self.assertEqual(selected["model_source"], "explicit_cli_argument")
        with patch("h2.runtime.subprocess.run") as process:
            process.return_value.stdout, process.return_value.stderr, process.return_value.returncode = events, "", 0
            response = CodexClient("stub")("prompt", effort="low", model="requested-model",
                                            log_dir=self.root / "reports/h2/model-call")
            self.assertEqual(response["model"], "reported-model")
            self.assertEqual(response["model_source"], "runtime_events")
            self.assertEqual(response["tokens"]["reasoning"], 2)
            self.assertEqual(process.call_args.args[0][-3:-1], ["-m", "requested-model"])
        _, data, _, _ = self.run_cycle()
        self.assertIsNone(data["llm_calls"][0]["model"])
        self.assertEqual(data["llm_calls"][0]["model_reason"], "model_not_reported_by_client")

    def test_accounting_supplement_preserves_originals_and_is_idempotent(self):
        cycle, data, _, _ = self.run_cycle()
        for call in data["llm_calls"]:
            call["tokens"]["reasoning"] = None
            log_dir = self.root / call["log_dir"]
            log_dir.mkdir(parents=True)
            events = [{"type": "thread.started", "model": "measured-model"},
                      {"type": "item.completed", "item": {"type": "agent_message", "text": CODE}},
                      {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5,
                                                               "cached_input_tokens": 2, "reasoning_output_tokens": 1}}]
            (log_dir / "events.jsonl").write_text('\n'.join(json.dumps(e) for e in events), encoding="utf-8")
        data["tokens"]["reasoning"] = None
        for run in data["runs"].values():
            run["tokens"]["reasoning"] = None
        original = copy.deepcopy(data)
        report = cycle.report / "cycle.json"
        report.write_text(json.dumps(data), encoding="utf-8")
        rows = [self.prior, *data["library_entries"]]
        self.library.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding="utf-8")
        original_library = self.library.read_bytes()
        supplement = supplement_cycle(self.root, cycle.id)
        self.assertEqual(supplement["tokens"]["reasoning"], 8)
        self.assertEqual(supplement["tokens"]["total"], 120)
        self.assertEqual(supplement["runs"]["run0"]["tokens"]["reasoning"], 2)
        self.assertEqual(supplement["library_entries"][0]["contrast"]["probe"]["tokens"]["reasoning"], 1)
        corrected = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual({k: v for k, v in corrected.items() if k != "accounting_supplements"}, original)
        self.assertTrue(self.library.read_bytes().startswith(original_library))
        self.assertEqual(len(self.library.read_text(encoding="utf-8").splitlines()), 7)
        report_bytes, library_bytes = report.read_bytes(), self.library.read_bytes()
        self.assertEqual(supplement_cycle(self.root, cycle.id), supplement)
        self.assertEqual(report.read_bytes(), report_bytes)
        self.assertEqual(self.library.read_bytes(), library_bytes)

    def test_second_cycle_proposer_gets_previous_entries_only_base_stays_fixed(self):
        _, first, _, _ = self.run_cycle()
        correction = copy.deepcopy(first["library_entries"][0])
        correction.update(entry_id="correction-only", entry_type="measurement_supplement",
                          supplements_entry_id=correction["entry_id"], supplement_id="test-supplement")
        with self.library.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(correction) + '\n')
        previous = [json.loads(line) for line in self.library.read_text(encoding="utf-8").splitlines()]
        llm = StubLLM()
        second = Cycle(self.root, cycle_id="stub-cycle-2", llm=llm, cad=StubCAD())
        clock = itertools.count(1, .001)
        with patch("time.perf_counter", side_effect=lambda: next(clock)):
            data = second.run()
        self.assertEqual(data["status"], "completed")
        proposal_prompt = next(prompt for prompt, _, _ in llm.prompts if "Propose exactly" in prompt)
        supplied = json.loads(proposal_prompt.split('\n', 1)[1])["prior_library"]
        self.assertEqual(supplied, materialize_library(previous))
        self.assertEqual(data["prior_library_count"], 4)
        self.assertEqual(data["prior_library_record_count"], 5)
        supplied_ids = {row["entry_id"] for row in supplied}
        self.assertTrue({e["entry_id"] for e in first["library_entries"]}.issubset(supplied_ids))
        self.assertTrue(supplied_ids.isdisjoint({e["entry_id"] for e in data["library_entries"]}))
        self.assertNotIn("correction-only", supplied_ids)
        self.assertEqual(data["runs"]["run0"]["harness"], json.loads(self.original_base))
        self.assertEqual(self.base_path.read_bytes(), self.original_base)

    def test_library_supplements_fill_missing_tokens_without_duplicate_lessons(self):
        original = {"entry_id": "original", "domain": "cad-freecad", "task_id": "A",
                    "cycle_id": "previous", "edit": [{"op": "add_rule", "value": "guidance"}],
                    "verdict": "supported", "lesson": "Original lesson",
                    "contrast": {side: {"tokens": {"reasoning": None, "total": 15}}
                                 for side in ("run0", "probe")}}
        correction = copy.deepcopy(original)
        correction.update(entry_id="correction", entry_type="measurement_supplement",
                          supplements_entry_id="original", supplement_id="test", created_at="then",
                          lesson="Accounting correction, not a lesson")
        correction["contrast"]["run0"]["tokens"]["reasoning"] = 2
        correction["contrast"]["probe"]["tokens"]["reasoning"] = 1
        rows = [original, correction]
        snapshot = copy.deepcopy(rows)
        result = materialize_library(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["entry_id"], "original")
        self.assertEqual(result[0]["lesson"], "Original lesson")
        self.assertEqual(result[0]["contrast"]["run0"]["tokens"], {"reasoning": 2, "total": 15})
        self.assertEqual(result[0]["contrast"]["probe"]["tokens"]["reasoning"], 1)
        self.assertEqual(rows, snapshot)
        correction["contrast"]["probe"]["tokens"]["total"] = 16
        with self.assertRaises(ValueError):
            materialize_library(rows)

    def test_repeats_round_robin_warmup_statistics_library_and_model(self):
        llm = StubLLM()
        active = False
        def sequential_llm(prompt, *, effort, model, log_dir):
            nonlocal active
            self.assertFalse(active)
            active = True
            try:
                self.assertEqual(model, "gpt-6.1-sol")
                response = llm(prompt, effort=effort, model=model, log_dir=log_dir)
                response.update(model=model, model_source="explicit_cli_argument", model_reason=None)
                return response
            finally:
                active = False
        _, data, _, _ = self.run_cycle(repeats=3, model="gpt-6.1-sol", llm=sequential_llm)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["max_llm_calls"], 100)
        expected = (["warmup"] + [f"run0-r{r}" for r in range(1, 4)]
                    + [f"probe-{i}-r{r}" for r in range(1, 4) for i in range(1, 4)]
                    + [f"composed-r{r}" for r in range(1, 4)])
        self.assertEqual(data["execution_order"], expected)
        self.assertEqual(data["llm_call_count"], 20)
        self.assertEqual(data["tokens"]["total"], 300)
        self.assertEqual(data["comparison_tokens"]["total"], 270)
        self.assertFalse(data["runs"]["warmup"]["included_in_comparison"])
        self.assertEqual(data["llm_calls"][0]["cache_phase"], "warmup")
        self.assertTrue(all(c["cache_phase"] == "post_warmup" for c in data["llm_calls"][1:]))
        self.assertTrue(all(c["model"] == "gpt-6.1-sol" for c in data["llm_calls"]))
        self.assertTrue(all(c["tokens"]["uncached_input"] == 8 for c in data["llm_calls"]))
        base, probe = data["groups"]["run0"], data["groups"]["probe-1"]
        self.assertEqual(base["n"], 3)
        self.assertEqual(base["pass_rate"], 1)
        self.assertEqual(base["statistics"]["tokens"]["total"], {"mean": 30, "std": 0})
        self.assertEqual(probe["statistics"]["tokens"]["total"], {"mean": 15, "std": 0})
        self.assertAlmostEqual(probe["cache"]["cached_input_ratio"], .2)
        self.assertEqual(data["composition"]["selected_run"], "composed")
        self.assertEqual(data["groups"]["composed"]["n"], 3)
        proposal = next(p for p, _, _ in llm.prompts if "Propose exactly" in p)
        self.assertEqual(len(json.loads(proposal.split('\n', 1)[1])["baseline_traces"]), 3)
        for entry in data["library_entries"]:
            self.assertEqual(entry["contrast"]["probe"]["n"], 3)
            self.assertEqual(entry["decision"]["rule"], "D15")
            self.assertEqual(entry["contrast"]["run0"]["pass_rate"], 1)

    def test_d15_pass_rate_saving_noise_unknowns_and_strict_boundaries(self):
        def group(rate=1, tokens=(100, 100, 100), wall=(100, 100, 100)):
            return {"n": 3, "pass_rate": rate, "infrastructure_failure": False,
                    "statistics": {"tokens": {"total": distribution(tokens)}, "wall_ms": distribution(wall)}}
        base = group()
        self.assertEqual(decide(group(rate=1/3), group(rate=2/3))["verdict"], "supported")
        self.assertEqual(decide(base, group(rate=2/3, tokens=(1,1,1)))["verdict"], "unsupported")
        self.assertEqual(decide(base, group(tokens=(90,90,90)))["verdict"], "unsupported")
        self.assertEqual(decide(base, group(tokens=(89,89,89)))["verdict"], "supported")
        self.assertEqual(decide(base, group(tokens=(60,80,100)))["verdict"], "unsupported")
        self.assertEqual(decide(base, group(wall=(50,50,50), tokens=(200,200,200)))["verdict"], "supported")
        self.assertEqual(decide(base, group(tokens=(None,100,100)))["verdict"], "confounded")
        self.assertEqual(decide(base, {**group(), "infrastructure_failure": True})["verdict"], "confounded")
        self.assertEqual(distribution([1,2,3]), {"mean": 2, "std": 1})

    def test_repeated_cycle_composition_fallback_and_budget(self):
        _, data, _, _ = self.run_cycle(repeats=3, cad=StubCAD(composed_fail=True))
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["groups"]["composed"]["n"], 3)
        self.assertEqual(data["groups"]["composed"]["pass_rate"], 0)
        self.assertTrue(data["composition"]["fallback"])
        self.assertEqual(data["composition"]["selected_run"], "probe-1")
        self.assertEqual(data["pass_rate"], 1)
        _, limited, _, _ = self.run_cycle(repeats=3, max_calls=5, cycle_id="limited")
        self.assertEqual(limited["status"], "budget_exhausted")
        self.assertEqual(limited["llm_call_count"], 5)
        self.assertEqual(limited["library_entries"], [])
        with self.assertRaises(ValueError):
            Cycle(self.root, max_calls=101)
        with self.assertRaises(ValueError):
            Cycle(self.root, repeats=0)


if __name__ == "__main__":
    unittest.main()
