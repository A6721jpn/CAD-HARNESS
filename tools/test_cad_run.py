"""Offline contract tests: no CAD executable is invoked."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import cad_run as host, cad_run_freecad as worker
from tools.fixtures import cad_run_a_build as fixture

EVIDENCE = host.ROOT / "reports/evidence/A-box-pocket-fillet-FreeCAD-20261005"


class CadRunTests(unittest.TestCase):
    def test_evidence_numeric_and_inner_edge_predicates(self):
        good = json.loads((EVIDENCE / "run04-cad.json").read_text(encoding="utf-8"))
        self.assertTrue(all(worker.numeric_predicates(good["measurements"]).values()))
        bad = json.loads((EVIDENCE / "run02-cad.json").read_text(encoding="utf-8"))["features"]["pocket"]["shape"]
        checks = worker.numeric_predicates(bad)
        self.assertFalse(checks["volume"])
        self.assertFalse(checks["faces"])
        inner = [dict(e, line=True) for e in good["feature_measurements"]["pocket_inner_edges"]]
        self.assertTrue(worker.inner_predicate(inner))
        inner[0]["adjacent_normal_dot"] = 1
        self.assertFalse(worker.inner_predicate(inner))
        inner[0] = dict(inner[1])
        self.assertFalse(worker.inner_predicate(inner))

    def fake_app(self, doc):
        documents = {}
        def create(name):
            doc.Name = name
            documents[name] = doc
            return doc
        return SimpleNamespace(GuiUp=0, Version=lambda: ["1", "1", "4"],
                               listDocuments=lambda: documents.copy(), newDocument=create,
                               closeDocument=Mock(side_effect=lambda name: documents.pop(name)))

    def test_actual_worker_build_exception_boundary(self):
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            doc = SimpleNamespace(recompute=Mock(), saveAs=Mock())
            app, probe = self.fake_app(doc), Mock()
            build = Mock(side_effect=RuntimeError("intentional"))
            result = worker.execute(app, build, Path(temp) / "model.FCStd", Mock(), probe)
            self.assertEqual((result["failed_phase"], result["next_actor"]), ("build", "sol"))
            self.assertFalse(result["script_completed"])
            self.assertTrue(result["document_closed"])
            probe.assert_not_called()
            doc.saveAs.assert_not_called()
            app.closeDocument.assert_called_once_with("CadRunA")

    def test_save_failure_is_fixed_worker_failure(self):
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            doc = SimpleNamespace(recompute=Mock(), saveAs=Mock(side_effect=OSError("intentional")))
            app = self.fake_app(doc)
            body = SimpleNamespace(Document=doc, TypeId="PartDesign::Body")
            probe = Mock(return_value={"probe_pass": True, "measurements": {}, "predicates": {"ok": True}})
            result = worker.execute(app, lambda unused: body, Path(temp) / "model.FCStd", Mock(), probe)
            self.assertEqual((result["code_owner"], result["next_actor"]), ("harness", "human"))
            self.assertFalse(result["script_completed"])
            self.assertTrue(result["document_closed"])

    def test_cleanup_only_terminates_confirmed_owned_headless_process(self):
        for state, gui, handle, blocked in (
                ("recovery", 0, True, False), ("windows", 0, True, False),
                ("scan_failed", 0, True, False), ("no_windows", 1, True, False),
                ("no_windows", 0, False, False), ("no_windows", 0, True, True)):
            with self.subTest(state=state, gui=gui, handle=handle, blocked=blocked):
                proc = SimpleNamespace(pid=4242, _handle=object() if handle else None,
                                       poll=lambda: None, terminate=Mock(), wait=Mock())
                scan = Mock(return_value={"state": state})
                result = host.cleanup(proc, gui, scan, blocked=blocked)
                self.assertEqual(result["cleanup_status"], "cleanup_pending")
                proc.terminate.assert_not_called()
                if not blocked:
                    scan.assert_called_once_with(4242)
        proc = SimpleNamespace(pid=4242, _handle=object(), poll=lambda: None,
                               terminate=Mock(), wait=Mock())
        result = host.cleanup(proc, 0, lambda pid: {"state": "no_windows"})
        self.assertEqual(result["cleanup_status"], "forced_own_headless_exit")
        proc.terminate.assert_called_once_with()
        route = host.new_result()
        host.fail(route, "dialog", "recovery_dialog")
        host.fail(route, "build", "later_script_error", "script", "sol")
        self.assertEqual((route["failed_phase"], route["next_actor"]), ("dialog", "human"))

    def test_preflight_rejects_outputs_without_spawning(self):
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            root = Path(temp)
            script = root / "build.py"
            script.write_text("def build(doc):\n    return doc\n", encoding="utf-8")
            (root / "reports/cad-run/existing").mkdir(parents=True)
            process = Mock()
            for dest in ("reports/runs/new", "reports/outcomes/new", "reports/evidence/new",
                         "../outside", "reports/cad-run", "reports/cad-run/existing"):
                with self.subTest(dest=dest), self.assertRaises(ValueError):
                    args = host.parser().parse_args(["--script", str(script), "--out-dir", dest, "--timeout-s", "1"])
                    host.run_attempt(args, root, process)
            process.assert_not_called()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = host.main([])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["failed_phase"], "preflight")
        with patch.object(host, "run_attempt", side_effect=OSError("intentional")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(host.main(["--script", "unused.py", "--out-dir", "unused", "--timeout-s", "1"]), 1)

    def test_host_warning_failure_routes_and_event_schema(self):
        measurements = json.loads((EVIDENCE / "run05-cad.json").read_text(encoding="utf-8"))["measurements"]
        cases = ((0, "pass", 0, None), (9, "pass", 1, "human"),
                 (0, "predicate_fail", 1, "sol"), (0, "exception", 1, "human"),
                 (0, None, 1, "human"))
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            root = Path(temp)
            script = root / "build.py"
            script.write_text("def build(doc):\n    return None\n", encoding="utf-8")
            exe = root / "freecad/bin/freecadcmd.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"offline fixture; never executed")
            for index, (cad_exit, probe_status, expected_exit, actor) in enumerate(cases):
                with self.subTest(probe_status=probe_status, cad_exit=cad_exit):
                    out = root / "reports/cad-run" / str(index)
                    proc = SimpleNamespace(pid=4242, _handle=object(), poll=lambda: cad_exit,
                                           terminate=Mock(), wait=Mock(),
                                           stdout=io.BufferedReader(io.BytesIO(b"")),
                                           stderr=io.BufferedReader(io.BytesIO(
                                               ("The 'Midplane' property is deprecated\n"
                                                + "token" + "=test-placeholder\n").encode("utf-16"))))
                    def spawn(argv, **kwargs):
                        self.assertFalse(kwargs["shell"])
                        self.assertEqual(Path(kwargs["cwd"]), out)
                        request = json.loads((out / "request.json").read_text(encoding="utf-8"))
                        (out / "worker-events.jsonl").write_text(json.dumps(
                            {"kind": "ready", "owned_pid": 4242, "gui_up": 0}) + "\n", encoding="utf-8")
                        if probe_status is not None:
                            report = {"schema": "cad-harness.cad_run.worker.v0", **request,
                                      "owned_pid": 4242, "document_closed": True,
                                      "status": "ok" if probe_status == "pass" else "failed",
                                      "failed_phase": None if probe_status == "pass" else "probe",
                                      "code_owner": "script" if probe_status == "predicate_fail" else "probe",
                                      "next_actor": "sol" if probe_status == "predicate_fail" else "human",
                                      "script_completed": probe_status != "exception",
                                      "probe_pass": probe_status == "pass",
                                      "probe_status": probe_status, "measurements": measurements, "predicate_diff": []}
                            (out / "worker-result.json").write_text(json.dumps(report), encoding="utf-8")
                            (out / "model.FCStd").write_bytes(b"offline model placeholder")
                        return proc
                    args = host.parser().parse_args(["--script", str(script), "--out-dir", str(out),
                                                     "--timeout-s", "1"])
                    with patch.object(host, "FREECAD_DIR", root / "freecad"):
                        result, code = host.run_attempt(args, root, spawn)
                    self.assertEqual((code, result["next_actor"]), (expected_exit, actor))
                    self.assertEqual(result["cad_exit_code"], cad_exit)
                    self.assertEqual(result["removed_warning_lines"], 1)
                    self.assertIsNone(result["geometry_ok"])
                    self.assertNotIn("script_ok", result)
                    self.assertEqual(json.loads((out / "result.json").read_text(encoding="utf-8")), result)
                    events = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
                    self.assertTrue(all(set(e) == set(host.EVENT_KEYS) for e in events))
                    self.assertTrue(all(set(e["data"]) <= host.DATA_KEYS for e in events))
                    self.assertNotIn("test-placeholder", (out / "stderr.txt").read_text(encoding="utf-8"))
                    proc.terminate.assert_not_called()

    def test_disabled_judge_and_source_provenance(self):
        self.assertEqual(host.judge_stub(), {"enabled": False, "invoked": False, "decision": None, "usage": None})
        self.assertEqual(fixture.SOURCE_SHA256, hashlib.sha256((host.ROOT / fixture.SOURCE).read_bytes()).hexdigest())
        for file in ("cad_run.py", "cad_run_freecad.py", "fixtures/cad_run_a_build.py"):
            text = (host.ROOT / "tools" / file).read_text(encoding="utf-8").lower()
            for forbidden in ("Get" + "-CimInstance", "Win32" + "_Process", "w" + "mi",
                              "so" + "cket", "ht" + "tp", "url" + "lib"):
                self.assertNotIn(forbidden.lower(), text)


if __name__ == "__main__":
    unittest.main()
