"""B2 protocol tests; every Codex and cad_run subprocess is mocked."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from tools import cad_agent as agent, cad_run, cad_run_probes as specs
from tools.test_support import start_tempdirs, stop_tempdirs

SOURCE = "def build(doc):\n    doc.Label = '図面'\n    return None\n"
USAGE = dict(zip(agent.USAGE_KEYS, (100, 50, 0, 20, 10)))


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class CadAgentTests(unittest.TestCase):
    def test_mvp_context_separation_and_toml_roundtrip(self):
        description = '日本語 "quote"\\path\nrequest'
        context = agent.developer_context('skill "\\\n日本語', 'JSON only',
                                          {"actual": None, "expected": 6})
        argv = agent.exec_argv("codex.exe", Path("outside"), Path("last"), description, context)
        self.assertEqual(argv[-1], description)
        setting = next(arg for arg in argv if arg.startswith("developer_instructions="))
        self.assertEqual(tomllib.loads(setting)["developer_instructions"], context)
        self.assertNotIn("expected", argv[-1])
        with self.assertRaisesRegex(ValueError, "context_argv_limit"):
            agent.exec_argv("codex.exe", Path("outside"), Path("last"), description, "x" * 40000)

    def test_mvp_shared_call_attempt_budget_and_deadline_clip(self):
        clock = [10.0]
        budget = agent.Budget(clock=lambda: clock[0])
        self.assertEqual(budget.cad_timeout(), 300)
        for unused in range(3):
            budget.call()
            budget.cad()
        with self.assertRaisesRegex(ValueError, "call_limit"):
            budget.call()
        with self.assertRaisesRegex(ValueError, "attempt_limit"):
            budget.cad()
        clock[0] = 895.5
        self.assertEqual(budget.cad_timeout(), 14)
        clock[0] = 910
        with self.assertRaisesRegex(ValueError, "deadline_exceeded"):
            budget.remaining()

    def fake_runner(self, plans, source=SOURCE, cli_exit=0, with_usage=True, task_id=cad_run.TASK):
        model_calls, cad_calls, work_dirs = [], [], []
        def run(argv, **kwargs):
            self.assertFalse(kwargs["shell"])
            self.assertNotIn("env", kwargs)  # CODEX_HOME is inherited, never replaced.
            if argv[1] == "--version":
                return subprocess.CompletedProcess(argv, 0, "codex-cli 0.159.2\n", "")
            if argv[1] == "exec":
                self.assertEqual(argv[argv.index("-m") + 1], agent.MODEL)
                self.assertEqual(argv[argv.index("-c") + 1], 'model_reasoning_effort="xhigh"')
                self.assertEqual(argv[argv.index("-s") + 1], "read-only")
                self.assertEqual([argv[i + 1] for i, item in enumerate(argv) if item == "--disable"],
                                 list(agent.DISABLED))
                self.assertNotIn("resume", argv)
                self.assertFalse(any("dangerously" in item for item in argv))
                work = Path(kwargs["cwd"]).resolve()
                self.assertEqual(Path(argv[argv.index("-C") + 1]).resolve(), work)
                self.assertFalse(work.is_relative_to(self.driver_test_root))
                self.assertFalse(work.is_relative_to(agent.ROOT.resolve()))
                self.assertEqual(Path(argv[argv.index("-o") + 1]).parent, work)
                self.assertEqual(list(work.iterdir()), [])
                self.assertNotIn(str(work), argv[-1])
                work_dirs.append(work)
                model_calls.append(argv[-1])
                Path(argv[argv.index("-o") + 1]).write_text(source, encoding="utf-8")
                rows = [{"type": "thread.started", "thread_id": "mock-session-%d" % len(model_calls)}]
                if with_usage:
                    rows += [{"type": "turn.completed", "usage": USAGE}] * 2
                return subprocess.CompletedProcess(argv, cli_exit, "\n".join(map(json.dumps, rows)), "")
            self.assertEqual(Path(argv[2]).name, "cad_run.py")
            for flag, value in (("--recipe", "freecadcmd"), ("--timeout-s", "300"),
                                ("--task", task_id)):
                self.assertEqual(argv[argv.index(flag) + 1], value)
            self.assertNotIn("console", argv)
            script, out = (Path(argv[argv.index(flag) + 1]) for flag in ("--script", "--out-dir"))
            plan = plans[len(cad_calls)]
            cad_calls.append(out)
            out.mkdir()
            result = {"schema": "cad-harness.cad_run.v0", "task_id": task_id,
                      "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                      "attempt_id": "mock-cad-%d" % len(cad_calls), "status": "failed",
                      "failed_phase": "probe", "probe_status": "predicate_fail", "probe_pass": False,
                      "next_actor": "sol", "predicate_diff": ["outer_fillet"],
                      "measurements": {"face_count": 11}, "document_closed": True,
                      "script_completed": True, "cad_exit_code": 0, "cleanup_status": "exited"}
            result.update({key: value for key, value in plan.items() if key not in ("exit", "raw")})
            (out / "result.json").write_text(json.dumps(result), encoding="utf-8")
            return subprocess.CompletedProcess(argv, plan.get("exit", 1),
                                               plan.get("raw", json.dumps(result)), "")
        run.work_dirs = work_dirs
        return run, model_calls, cad_calls

    def drive(self, root, runner, name="unit-run", task_id=cad_run.TASK):
        self.driver_test_root = Path(root).resolve()
        with patch.object(agent, "agents_identity", return_value={"codex_home": None}), \
                patch.object(agent, "ROOT", self.driver_test_root):
            result = agent.run_driver(name, "codex.exe", Path(root), runner, task_id=task_id)
        work_dirs = getattr(runner, "work_dirs", [])
        self.assertEqual(len(set(work_dirs)), len(work_dirs))
        for work in work_dirs:
            self.assertFalse(work.exists())
        return result

    def test_source_accepts_one_fence_and_rejects_invalid_sources(self):
        for text in (SOURCE, "\x60\x60\x60python\n" + SOURCE + "\x60\x60\x60", "\x60\x60\x60\n" + SOURCE + "\x60\x60\x60"):
            self.assertEqual(agent.source_from_final(text), SOURCE)
        for text in ("", "pass", "def build(:", "def build(other): pass",
                     "説明\n\x60\x60\x60python\n" + SOURCE + "\x60\x60\x60",
                     "python tools/cad_run.py", SOURCE + "# token=test-placeholder\n"):
            with self.subTest(text=text), self.assertRaises((ValueError, SyntaxError)):
                agent.source_from_final(text)

    def test_invalid_generation_never_invokes_cad_and_usage_missing_is_null(self):
        for source, cli_exit in (("pass", 0), ("def build(:", 0), (SOURCE, 7)):
            with self.subTest(source=source, cli_exit=cli_exit), tempfile.TemporaryDirectory() as temp:
                run, models, cads = self.fake_runner([], source, cli_exit, with_usage=False)
                report, code = self.drive(temp, run)
                self.assertEqual(code, 1)
                self.assertEqual(len(models), 1)
                self.assertEqual(cads, [])
                self.assertIsNone(report["attempts"][0]["usage"])
                self.assertIsNone(report["final_exit"])
                events = [json.loads(line) for line in (Path(temp) / "reports/cad-run/unit-run/events.jsonl").read_text().splitlines()]
                self.assertEqual(next(e for e in events if e["event"] == "exec_finished")["status"], "failed")

    def test_stop_routes_and_type_only_diagnostic_do_not_repair(self):
        plans = (({"cleanup_status": "cleanup_pending"}, "cad_not_settled"),
                 ({"document_closed": False}, "cad_not_settled"),
                 *[({"cad_exit_code": value}, "cad_not_settled") for value in (None, "0", 0.0, False)],
                 ({"next_actor": "human"}, "human_required"),
                 ({"next_actor": None}, "human_required"),
                 ({"failed_phase": "launch"}, "human_required"),
                 ({"failed_phase": "dialog"}, "human_required"),
                 ({"probe_status": "exception"}, "human_required"),
                 ({"failed_phase": "build", "predicate_diff": None, "measurements": None,
                   "error_type": "RuntimeError"}, "diagnostic_insufficient"),
                 ({"failed_phase": "build", "predicate_diff": [],
                   "measurements": {"volume_mm3": None}}, "diagnostic_insufficient"))
        for plan, reason in plans:
            with self.subTest(reason=reason, plan=plan), tempfile.TemporaryDirectory() as temp:
                run, models, cads = self.fake_runner([plan])
                report, code = self.drive(temp, run)
                self.assertEqual((code, report["message_code"]), (1, reason))
                self.assertEqual((len(models), len(cads)), (1, 1))
                if reason == "cad_not_settled":
                    self.assertEqual(report["failed_phase"], "probe")

    def test_safe_repair_passes_previous_source_and_result_and_preserves_raw_usage(self):
        good = {"exit": 0, "status": "ok", "failed_phase": None, "probe_status": "pass",
                "probe_pass": True, "next_actor": None, "predicate_diff": []}
        with tempfile.TemporaryDirectory() as temp:
            run, models, cads = self.fake_runner([{}, good])
            report, code = self.drive(temp, run)
            self.assertEqual((code, report["status"], len(models), len(cads)), (0, "ok", 2, 2))
            self.assertIn(SOURCE.strip().splitlines()[0], models[1])
            self.assertIn('"exit": 1', models[1])
            self.assertIn("outer_fillet", models[1])
            self.assertEqual(cads[0].parent, cads[1].parent)
            self.assertEqual([out.name for out in cads], ["a1", "a2"])
            self.assertGreaterEqual(report["wall_ms"], 0)
            self.assertEqual({key for key in report if key.endswith("_ms")}, {"wall_ms"})
            for attempt in report["attempts"]:
                self.assertEqual({key for key in attempt if key.endswith("_ms")},
                                 {"exec_wall_ms", "cad_run_wall_ms"})
                self.assertEqual([u["values"] for u in attempt["usage"]], [USAGE, USAGE])
                self.assertNotIn("usage_total", attempt)
                self.assertIsNotNone(attempt["session_id"])
                self.assertIsNotNone(attempt["cli_version"])
                self.assertGreaterEqual(attempt["exec_wall_ms"], 0)
                self.assertGreaterEqual(attempt["cad_run_wall_ms"], 0)
            self.assertNotIn("script_ok", report)
            self.assertIsNone(report["geometry_ok"])
            stored = json.loads((cads[0].parent / "driver-run.json").read_text())
            self.assertEqual(stored, report)
            events = [json.loads(line) for line in (cads[0].parent / "events.jsonl").read_text().splitlines()]
            self.assertLessEqual({e["event"] for e in events},
                                 {"exec_started", "exec_finished", "cad_run_finished", "repair_decided", "run_finished"})

    def test_attempt_limit_has_no_hidden_fourth_call(self):
        with tempfile.TemporaryDirectory() as temp:
            run, models, cads = self.fake_runner([{}, {}, {}])
            report, code = self.drive(temp, run)
            self.assertEqual((code, report["message_code"], len(models), len(cads)), (1, "attempt_limit", 3, 3))
            self.assertEqual(report["final_out_dir"], "reports/cad-run/unit-run/a3")

    def test_run_output_guard_and_existing_cad_preflight_accept_nested_fresh_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("../outside", "reports/runs/new", str(root / "outside"), "bad.name", ""):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    agent.new_run_dir(root, name)
            out = agent.new_run_dir(root, "fresh")
            with self.assertRaises(ValueError):
                agent.new_run_dir(root, "fresh")
            script = out / "input.py"
            script.write_bytes(SOURCE.encode("utf-8"))
            args = cad_run.parser().parse_args(["--script", str(script), "--out-dir", str(out / "a1"),
                                               "--timeout-s", "300"])
            accepted, raw, unused = cad_run.preflight(args, root)
            self.assertEqual(accepted, out / "a1")
            self.assertEqual(raw, SOURCE.encode("utf-8"))
            self.assertFalse(accepted.exists())
            run, models, cads = self.fake_runner([])
            with patch.object(agent.tempfile, "gettempdir", return_value=str(root)):
                report, code = self.drive(root, run)
            self.assertEqual((code, report["message_code"]), (1, "exec_temp_inside_repository"))
            self.assertEqual((models, cads), ([], []))

    def test_nonzero_native_exit_with_diagnostic_allows_safe_repair(self):
        good = {"exit": 0, "status": "ok", "failed_phase": None, "probe_status": "pass",
                "probe_pass": True, "next_actor": None, "predicate_diff": []}
        for phase in ("build", "probe"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temp:
                failed = {"failed_phase": phase, "cad_exit_code": 9,
                          "script_completed": phase != "build"}
                run, models, cads = self.fake_runner([failed, good])
                report, code = self.drive(temp, run)
                self.assertEqual((code, len(models), len(cads)), (0, 2, 2))
                self.assertEqual(report["attempts"][0]["result"]["cad_exit_code"], 9)
                self.assertEqual(report["attempts"][0]["result"]["failed_phase"], phase)

    def test_external_work_is_removed_and_not_retained_on_source_or_exec_failure(self):
        for fault in ("source", "exec"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                base, models, cads = self.fake_runner([])
                def run(argv, **kwargs):
                    work = Path(kwargs["cwd"]).resolve()
                    if argv[1] == "--version":
                        return subprocess.CompletedProcess(argv, 0, str(work), "")
                    result = base(argv, **kwargs)
                    last = Path(argv[argv.index("-o") + 1])
                    if fault == "exec":
                        raise OSError("exec failure at " + str(work))
                    last.write_text(SOURCE + "# " + str(work) + "\n", encoding="utf-8")
                    return result
                run.work_dirs = base.work_dirs
                report, code = self.drive(temp, run)
                self.assertEqual((code, len(models), len(cads)), (1, 1, 0))
                out = Path(temp) / "reports/cad-run/unit-run"
                retained = [json.dumps(report), (out / "driver-run.json").read_text(),
                            (out / "events.jsonl").read_text(), *models]
                if (out / "last-a1.txt").exists():
                    retained.append((out / "last-a1.txt").read_text())
                for work in run.work_dirs:
                    for variant in (str(work), work.as_posix(), json.dumps(str(work))[1:-1]):
                        for text in retained:
                            self.assertNotIn(variant, text)
                self.assertNotIn("work-a1", [path.name for path in out.iterdir()])

    def test_invalid_cad_protocol_and_inconsistent_success_stop(self):
        for plan in ({"raw": "not JSON"}, {"script_sha256": "wrong"}, {"exit": 0},
                     {"task_id": "wrong"}, {"raw": '{"value": NaN}'}):
            with self.subTest(plan=plan), tempfile.TemporaryDirectory() as temp:
                run, models, cads = self.fake_runner([plan])
                report, code = self.drive(temp, run)
                self.assertEqual((code, len(models), len(cads)), (1, 1, 1))
                self.assertEqual(report["status"], "failed")


    def test_task_prompt_argv_and_unknown_task_no_calls(self):
        self.assertEqual(agent.digest(agent.PROMPT),
                         "ea2008c9dfdb3d1c9ff732dd5c373fd431064d53744e01db9cad8921e32cc641")
        good = {"exit": 0, "status": "ok", "failed_phase": None, "probe_status": "pass",
                "probe_pass": True, "next_actor": None, "predicate_diff": []}
        for task in (specs.TASK_A, specs.TASK_B):
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temp:
                run, models, cads = self.fake_runner([good], task_id=task)
                report, code = self.drive(temp, run, task_id=task)
                self.assertEqual((code, report["task_id"], len(cads)), (0, task, 1))
                self.assertEqual(models, [specs.SPECS[task]["prompt"]])
                if task == specs.TASK_B:
                    self.assertIn("80×60", models[0])
                    self.assertIn("DPC-019のみでCADを実行する", models[0])
                    self.assertIn("LPC-017ではCADを実行しない", models[0])
                    self.assertNotIn("幅40 mm", models[0])
        with tempfile.TemporaryDirectory() as temp:
            call = unittest.mock.Mock()
            with self.assertRaises(ValueError):
                agent.run_driver("unknown", "codex.exe", Path(temp), call, task_id="unknown")
            call.assert_not_called()
            self.assertEqual(list(Path(temp).iterdir()), [])
            with patch.object(agent, "run_driver") as driver, patch("sys.stderr"):
                with self.assertRaises(SystemExit) as rejected:
                    agent.main(["--run", "unknown", "--task", "unknown"])
                self.assertEqual(rejected.exception.code, 2)
                driver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
