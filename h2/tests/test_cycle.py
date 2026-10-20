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
from h2.runtime import CadRunner, CodexClient, parse_events, token_usage

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
        cycle = Cycle(self.root, cycle_id="stub-cycle", llm=llm, cad=cad, **kwargs)
        clock = itertools.count(1, .001)
        with patch("time.perf_counter", side_effect=lambda: next(clock)):
            result = cycle.run()
        return cycle, result, llm, cad

    def test_full_cycle_appends_library_and_keeps_base_immutable(self):
        cycle, data, llm, cad = self.run_cycle()
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["geometry_pass"])
        self.assertEqual(data["runs"]["run0"]["attempt_count"], 2)
        self.assertEqual(len(cad.calls), 6)
        self.assertEqual(data["llm_call_count"], 7)
        self.assertEqual(data["tokens"]["total"], 105)
        self.assertEqual(data["cad_wall_ms"], 12)
        self.assertEqual(set(data["stages"]), {"run0", "propose", "probe", "compose", "library"})
        self.assertTrue(all(s["wall_ms"] > 0 for s in data["stages"].values()))
        entries = [json.loads(line) for line in self.library.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(entries[0], self.prior)
        self.assertEqual(len(entries), 4)
        self.assertTrue(all(e["verdict"] == "supported" and e["adopted_in_composed"] for e in entries[1:]))
        self.assertEqual(self.base_path.read_bytes(), self.original_base)
        self.assertNotIn("Past learning", llm.prompts[0][0])
        self.assertIn("Past learning", llm.prompts[2][0])
        self.assertEqual(llm.prompts[2][1], "medium")
        self.assertIn('"previous_code": "def build(doc)', llm.prompts[1][0])
        self.assertIn('"predicate_diff": {"bbox": false}', llm.prompts[1][0])
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
        self.assertEqual(len(cad.calls), 8)  # composed uses its max_attempts=3

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
        self.assertEqual(len(cad.calls), 2)
        self.assertEqual(self.library.read_bytes(), before)

    def test_budget_stops_and_retains_partial_measurements(self):
        cycle, data, llm, cad = self.run_cycle(max_calls=3)
        self.assertEqual(data["status"], "budget_exhausted")
        self.assertEqual(len(llm.prompts), 3)
        self.assertEqual(len(cad.calls), 2)
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
        self.assertEqual(usage, {"input": 100, "cached_input": 20, "output": 30,
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


if __name__ == "__main__":
    unittest.main()
