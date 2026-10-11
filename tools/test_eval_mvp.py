"""Offline evaluation protocol tests; every driver invocation is a mock."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import cad_agent, eval_mvp as evaluation
from tools.test_support import start_tempdirs, stop_tempdirs

ROOT = Path(__file__).resolve().parents[1]


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class EvalTests(unittest.TestCase):
    def root(self, temp):
        root = Path(temp) / "repo"
        names = list(evaluation.FILES) + ["design/cad-harness-mvp/eval-v1/%s.json" % c for c in evaluation.ORDER]
        for name in names:
            destination = root / name
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes((ROOT / name).read_bytes())
        return root.resolve()

    def report(self, root, case, name, result_updates=None, report_updates=None):
        spec = evaluation.suite(root)[case]
        directory = evaluation.run_path(root,name)
        final = directory / "a1-mvp1"
        final.mkdir(parents=True,exist_ok=True)
        result = {"schema":"cad-harness.cad_run.v0","task_id":case,"gold_sha256":spec["sha256"],
                  "probe_profile":"mvp-v1","status":"ok","geometry_ok":True,"editability_ok":True,
                  "probe_pass":True,"probe_status":"pass","script_completed":True,"cad_exit_code":0,
                  "document_closed":True,"cleanup_status":"exited","verification_pass":True,
                  "verification_exit_code":0,"verification_cleanup_status":"exited",
                  "verification":{"document_closed":True,"verification_pass":True}}
        result.update(result_updates or {})
        (final / "result.json").write_text(json.dumps(result),encoding="utf-8")
        usage = dict.fromkeys(cad_agent.USAGE_KEYS,0)
        usage.update(input_tokens=10,output_tokens=2,reasoning_output_tokens=1)
        report = {"schema":"cad-harness.cad_agent.mvp1","run_id":name,"task_id":case,"mode":"description",
                  "description_sha256":spec["gold"]["description_sha256"],"gold_sha256":spec["sha256"],
                  "wall_ms":250,"status":"ok","llm_calls":1,"cad_attempts":1,
                  "calls":[{"prompt_sha256":spec["gold"]["description_sha256"],
                            "usage":[{"event_index":0,"values":usage}]}],
                  "attempts":[{"result":result}],"final_out_dir":final.relative_to(root).as_posix(),
                  "skill_sha256":"skill-v1","schema_sha256":"schema-v1","compiler_sha256":"compiler-v1",
                  "probe_sha256":"probe-v1","agents_sha256":{"codex_home":"rules-v1"},
                  "settings":{"model":cad_agent.MODEL,"effort":cad_agent.EFFORT},"cli_version":"mock-only",
                  "estimated_tokens":9999999}
        report.update(report_updates or {})
        (directory / "driver-run.json").write_text(json.dumps(report),encoding="utf-8")
        return report

    def test_fixed_fresh_description_suite_records_failures_and_provider_usage(self):
        with tempfile.TemporaryDirectory() as temp:
            root, calls = self.root(temp), []
            planned = evaluation.plan("mock-eval")
            def runner(argv,**kwargs):
                index = len(calls)
                case,name = planned[index]
                self.assertEqual(argv[:3],[sys.executable,"-B",str(root / "tools/cad_agent.py")])
                self.assertEqual(argv[argv.index("--mode")+1],"description")
                self.assertIn("--eval",argv)
                self.assertEqual(argv[argv.index("--run")+1],name)
                gold = root / "design/cad-harness-mvp/eval-v1" / (case + ".json")
                self.assertEqual(Path(argv[argv.index("--gold")+1]),gold)
                expected = json.loads(gold.read_text(encoding="utf-8"))
                description = Path(argv[argv.index("--description-file")+1]).read_bytes()
                self.assertEqual(description,expected["description"].encode("utf-8"))
                self.assertEqual(evaluation.sha(description),expected["description_sha256"])
                self.assertFalse(kwargs["shell"])
                self.assertEqual(kwargs["cwd"],str(root))
                calls.append(argv)
                failure = {"geometry_ok":False,"failed_phase":"probe"} if index == 1 else (
                          {"verification_pass":False,"failed_phase":"verification"} if index == 2 else {})
                self.report(root,case,name,failure,{"status":"failed"} if failure else {})
                return subprocess.CompletedProcess(argv,1 if failure else 0)
            ticks = iter(range(20))
            document = evaluation.evaluate("mock-eval","mock",root=root,runner=runner,clock=lambda:next(ticks))
            self.assertEqual([r["case"] for r in document["rows"]],[c for c,n in planned])
            self.assertEqual((len(calls),document["summary"]["pass_count"],document["summary"]["bar_met"]),(10,8,True))
            self.assertEqual(document["summary"]["per_part"]["P1"],{"passes":1,"runs":2})
            self.assertEqual(document["summary"]["tokens"]["input_tokens"],100)
            self.assertEqual(document["rows"][2]["failure_class"],"verification")
            self.assertTrue(all(r["wall_s"] == 1 and r["sol_calls"] == r["cad_attempts"] == 1 for r in document["rows"]))
            for row in document["rows"]:
                saved = json.loads((evaluation.run_path(root,row["run"]) / "eval-run.json").read_text(encoding="utf-8"))
                self.assertEqual(saved,row)
            aggregate = root / "reports/aggregate-mvp-eval-v1-mock.json"
            self.assertEqual(json.loads(aggregate.read_text(encoding="utf-8")),document)
            with aggregate.with_suffix(".csv").open(encoding="utf-8",newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual((len(rows),rows[0]["input_tokens"],rows[0]["geometry_ok"]),(10,"10","True"))

    def test_aggregate_only_existing_ids_and_mixed_versions_never_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root, runner = self.root(temp), Mock(side_effect=AssertionError("no launch"))
            planned = evaluation.plan("existing")
            for case,name in planned:
                self.report(root,case,name)
            ids = [name for case,name in planned]
            result = evaluation.evaluate(suffix="existing",aggregate_only=True,run_ids=ids,root=root,runner=runner)
            self.assertTrue(result["summary"]["bar_met"])
            self.assertTrue(all(row["wall_s"] == .25 for row in result["rows"]))
            self.assertFalse((root / "reports/cad-run/existing-eval-inputs-mvp1").exists())
            self.report(root,*planned[0],report_updates={"compiler_sha256":"other-version"})
            mixed = evaluation.evaluate("existing","mixed",True,root=root,runner=runner)
            self.assertEqual((mixed["summary"]["pass_count"],mixed["summary"]["versions_consistent"],
                              mixed["summary"]["bar_met"]),(10,False,False))
            self.report(root,*planned[0])
            (evaluation.run_path(root,planned[0][1]) / "driver-run.json").unlink()
            incomplete = evaluation.evaluate("existing","incomplete",True,root=root,runner=runner)
            self.assertEqual((incomplete["summary"]["pass_count"],incomplete["summary"]["complete"],
                              incomplete["summary"]["bar_met"]),(9,False,False))
            runner.assert_not_called()

    def test_pass_requires_time_budgets_geometry_editability_and_both_reimports(self):
        changes = (({"geometry_ok":False},{},"geometry_or_editability"),
                   ({"editability_ok":False},{},"geometry_or_editability"),
                   ({"verification_pass":False},{},"verification"),
                   ({"verification_exit_code":1},{},"driver"),
                   ({"cleanup_status":"timeout"},{},"cleanup"),
                   ({},{"wall_ms":900001},"timeout"),
                   ({},{"llm_calls":4},"budget"),
                   ({},{"gold_sha256":"wrong"},"protocol"),
                   ({},{"calls":[{"prompt_sha256":"wrong","usage":None}]},"protocol"))
        with tempfile.TemporaryDirectory() as temp:
            root = self.root(temp)
            spec = evaluation.suite(root)["P1"]
            for index,(result_updates,report_updates,failure) in enumerate(changes):
                with self.subTest(failure=failure,index=index):
                    name = "gates-%d-mvp1" % index
                    self.report(root,"P1",name,result_updates,report_updates)
                    row = evaluation.record(root,"P1",name,spec)
                    self.assertEqual((row["passed"],row["failure_class"]),(False,failure))
            self.report(root,"P1","valid-mvp1",report_updates={"wall_ms":900000})
            self.assertTrue(evaluation.record(root,"P1","valid-mvp1",spec)["passed"])
            self.assertFalse(evaluation.record(root,"P1","valid-mvp1",spec,elapsed=900.01)["passed"])

    def test_tokens_are_provider_only_and_partial_usage_stays_null(self):
        values = dict.fromkeys(cad_agent.USAGE_KEYS,1)
        report = {"calls":[{"usage":[{"values":values},{"values":values}]},
                           {"usage":[{"values":values}]}],"estimated_tokens":1000000}
        self.assertEqual(evaluation.provider_tokens(report),dict.fromkeys(cad_agent.USAGE_KEYS,3))
        for usage in (None,[],[{"values":None}],[{"values":{"output_tokens":2}}]):
            with self.subTest(usage=usage):
                report["calls"][1]["usage"] = usage
                tokens = evaluation.provider_tokens(report)
                self.assertIsNone(tokens["input_tokens"])
                self.assertEqual(tokens["output_tokens"],4 if usage == [{"values":{"output_tokens":2}}] else None)

    def test_existing_aggregate_or_run_refused_before_any_driver_call(self):
        for existing in ("aggregate.json","aggregate.csv","run"):
            with self.subTest(existing=existing),tempfile.TemporaryDirectory() as temp:
                root, runner = self.root(temp), Mock(side_effect=AssertionError("no launch"))
                path = (evaluation.run_path(root,"fresh-P1-r1-mvp1") if existing == "run" else
                        root / "reports" / ("aggregate-mvp-eval-v1." + existing.split(".")[1]))
                path.parent.mkdir(parents=True,exist_ok=True)
                if existing == "run": path.mkdir()
                else: path.write_bytes(b"preserve")
                with self.assertRaisesRegex(ValueError,"aggregate_exists|run_exists"):
                    evaluation.evaluate("fresh",root=root,runner=runner)
                if existing != "run": self.assertEqual(path.read_bytes(),b"preserve")
                runner.assert_not_called()
        with patch.object(evaluation,"evaluate",side_effect=ValueError("aggregate_exists")),patch("builtins.print"):
            self.assertEqual(evaluation.main(["--prefix","fresh"]),2)

    def test_threshold_and_launch_timeout_keep_all_ten_without_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root, planned = self.root(temp), evaluation.plan("threshold")
            for index,(case,name) in enumerate(planned):
                self.report(root,case,name,{"geometry_ok":False} if index < 2 else {})
            runner = Mock(side_effect=AssertionError("no launch"))
            result = evaluation.evaluate("threshold","threshold",True,root=root,runner=runner)
            self.assertEqual((result["summary"]["pass_count"],result["summary"]["per_part"]["P1"]["passes"],
                              result["summary"]["bar_met"]),(8,0,False))
            timeout = Mock(side_effect=subprocess.TimeoutExpired("mock-only",905))
            failed = evaluation.evaluate("timeouts","timeouts",root=root,runner=timeout,clock=lambda:0)
            self.assertEqual((timeout.call_count,failed["summary"]["pass_count"],failed["summary"]["bar_met"]),(10,0,False))
            self.assertTrue(all(row["failure_class"] == "timeout" for row in failed["rows"]))
            with self.assertRaisesRegex(ValueError,"ten_distinct"):
                evaluation.evaluate(suffix="bad",aggregate_only=True,run_ids=[planned[0][1]]*10,root=root,runner=runner)
            runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
