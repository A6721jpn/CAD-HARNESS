"""Offline contract tests: no CAD executable is invoked."""
import contextlib
import copy
from math import pi
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import cad_run as host, cad_run_freecad as worker, cad_run_probes as specs
from tools.fixtures import cad_run_a_build as fixture
from tools.test_support import start_tempdirs, stop_tempdirs

EVIDENCE = host.ROOT / "reports/evidence/A-box-pocket-fillet-FreeCAD-20261005"


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


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

    def test_primary_worker_failure_survives_save_and_close_failures(self):
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            for passed in (True, False):
                for close_failed in (False, True):
                    with self.subTest(passed=passed, close_failed=close_failed):
                        doc = SimpleNamespace(recompute=Mock(), saveAs=Mock(side_effect=OSError("intentional")))
                        app = self.fake_app(doc)
                        if close_failed:
                            app.closeDocument.side_effect = OSError("intentional")
                        body = SimpleNamespace(Document=doc, TypeId="PartDesign::Body")
                        probe = Mock(return_value={"probe_pass": passed, "measurements": {}, "predicates": {"ok": passed}})
                        result = worker.execute(app, lambda unused: body, Path(temp) / "model.FCStd", Mock(), probe)
                        self.assertEqual((result["failed_phase"], result["probe_status"], result["next_actor"]),
                                         ("build", "pass", "human") if passed else ("probe", "predicate_fail", "sol"))
                        self.assertFalse(result["script_completed"])
                        self.assertEqual(result["document_closed"], not close_failed)
                        if not passed:
                            self.assertEqual(result["save_error_type"], "OSError")
                        if close_failed:
                            self.assertEqual(result["close_error_type"], "OSError")

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
        self.assertEqual(result["cleanup_status"], "exited")
        self.assertEqual(result["cleanup_action"], "forced_own_headless_exit")
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
            for dest, reason in (("reports/runs/new", "output_root"), ("reports/outcomes/new", "output_root"),
                                 ("reports/evidence/new", "output_root"), ("../outside", "parent_path"),
                                 ("reports/cad-run", "output_root"), ("reports/cad-run/existing", "output_exists")):
                with self.subTest(dest=dest), self.assertRaises(host.InputError) as rejected:
                    args = host.parser().parse_args(["--script", str(script), "--out-dir", dest, "--timeout-s", "1"])
                    host.run_attempt(args, root, process)
                self.assertEqual(str(rejected.exception), reason)
            attempt = host.run_attempt
            for text, timeout, dest, reason in (
                    ("def build(doc): pass", "0", "reports/cad-run/new", "invalid_timeout"),
                    ("pass", "1", "reports/cad-run/new", "build_required"),
                    ("def build(doc): pass\n# token=test-placeholder", "1", "reports/cad-run/new", "private_input"),
                    ("def build(doc): pass", "1", "reports/runs/new", "output_root")):
                script.write_text(text, encoding="utf-8")
                with self.subTest(reason=reason), patch.object(
                        host, "run_attempt", side_effect=lambda a: attempt(a, root, process)), contextlib.redirect_stdout(io.StringIO()) as output:
                    code = host.main(["--script", str(script), "--out-dir", dest, "--timeout-s", timeout])
                result = json.loads(output.getvalue())
                self.assertEqual((code, result["message_code"], result["probe_status"]), (2, reason, "not_run"))
            process.assert_not_called()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = host.main([])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["failed_phase"], "preflight")
        self.assertEqual(json.loads(output.getvalue())["message_code"], "invalid_arguments")
        with patch.object(host, "run_attempt", side_effect=OSError("intentional")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(host.main(["--script", "unused.py", "--out-dir", "unused", "--timeout-s", "1"]), 1)

    def test_host_warning_failure_routes_and_event_schema(self):
        measurements = json.loads((EVIDENCE / "run05-cad.json").read_text(encoding="utf-8"))["measurements"]
        cases = ((0, "pass", 0, None, True), (9, "pass", 1, "human", True),
                 (0, "predicate_fail", 1, "sol", True), (0, "exception", 1, "human", True),
                 (0, None, 1, "human", True), (9, "predicate_fail", 1, "sol", True),
                 (0, "predicate_fail", 1, "sol", False))
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            root = Path(temp)
            script = root / "build.py"
            script.write_text("def build(doc):\n    return None\n", encoding="utf-8")
            exe = root / "freecad/bin/freecadcmd.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"offline fixture; never executed")
            for index, (cad_exit, probe_status, expected_exit, actor, closed) in enumerate(cases):
                with self.subTest(probe_status=probe_status, cad_exit=cad_exit):
                    out = root / "reports/cad-run" / str(index)
                    proc = SimpleNamespace(pid=4242, _handle=object(),
                                           poll=Mock(side_effect=[None, cad_exit, cad_exit, cad_exit]),
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
                            {"kind": "ready", "owned_pid": 4242, "gui_up": 0}) + "\n"
                            + json.dumps({"kind": "event", "phase": "build", "event": "build_finished",
                                          "status": "ok", "ts": "2026-10-11T12:00:00+00:00"}) + "\n",
                            encoding="utf-8")
                        if probe_status is not None:
                            report = {"schema": "cad-harness.cad_run.worker.v0", **request,
                                      "owned_pid": 4242, "document_closed": closed,
                                      "status": "ok" if probe_status == "pass" else "failed",
                                      "failed_phase": None if probe_status == "pass" else "probe",
                                      "code_owner": "script" if probe_status == "predicate_fail" else "probe",
                                      "next_actor": "sol" if probe_status == "predicate_fail" else "human",
                                      "script_completed": probe_status != "exception",
                                      "probe_pass": probe_status == "pass",
                                      "probe_status": probe_status, "measurements": measurements, "predicate_diff": []}
                            if not closed:
                                report["close_error_type"] = "OSError"
                            (out / "worker-result.json").write_text(json.dumps(report), encoding="utf-8")
                            (out / "model.FCStd").write_bytes(b"offline model placeholder")
                        return proc
                    args = host.parser().parse_args(["--script", str(script), "--out-dir", str(out),
                                                     "--timeout-s", "1"])
                    scan = Mock(return_value={"state": "scan_failed"})
                    with patch.object(host, "FREECAD_DIR", root / "freecad"), patch.object(host.time, "sleep"):
                        result, code = host.run_attempt(args, root, spawn, scan)
                    scan.assert_called_once_with(4242)
                    self.assertEqual((code, result["next_actor"]), (expected_exit, actor))
                    self.assertEqual(result["cad_exit_code"], cad_exit)
                    if probe_status == "predicate_fail":
                        self.assertEqual((result["failed_phase"], result["probe_status"]), ("probe", "predicate_fail"))
                    if not closed:
                        self.assertFalse(result["document_closed"])
                        self.assertEqual(result["close_error_type"], "OSError")
                    self.assertEqual(result["removed_warning_lines"], 1)
                    self.assertIsNone(result["geometry_ok"])
                    self.assertNotIn("script_ok", result)
                    self.assertEqual(json.loads((out / "result.json").read_text(encoding="utf-8")), result)
                    events = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
                    self.assertTrue(all(set(e) == set(host.EVENT_KEYS) for e in events))
                    launches = [e for e in events if e["event"] == "launch_finished"]
                    self.assertEqual(launches[0]["status"], "pending")
                    self.assertEqual(launches[1]["message_code"], "worker_ready")
                    self.assertEqual(launches[1]["status"], "ok")
                    self.assertTrue(all(set(e["data"]) <= host.DATA_KEYS for e in events))
                    transferred = [e for e in events if e["data"]["worker_ts"] is not None]
                    self.assertEqual(len(transferred), 1)
                    self.assertEqual(transferred[0]["data"]["worker_ts"], "2026-10-11T12:00:00+00:00")
                    self.assertNotEqual(transferred[0]["ts"], transferred[0]["data"]["worker_ts"])
                    self.assertNotIn("test-placeholder", (out / "stderr.txt").read_text(encoding="utf-8"))
                    proc.terminate.assert_not_called()

    def test_primary_dialog_survives_worker_merge(self):
        result = host.new_result()
        result.update(status="ok", attempt_id="attempt", script_sha256="hash", probe_status="not_run")
        host.fail(result, "dialog", "recovery_dialog")
        report = {"schema": "cad-harness.cad_run.worker.v0", "attempt_id": "attempt",
                  "script_sha256": "hash", "owned_pid": 4242, "status": "failed",
                  "failed_phase": "probe", "next_actor": "sol", "code_owner": "script",
                  "probe_status": "predicate_fail", "probe_pass": False, "document_closed": False,
                  "close_error_type": "OSError"}
        host.merge_worker(result, report, SimpleNamespace(pid=4242))
        host.fail(result, "cleanup", "capture_incomplete")
        self.assertEqual((result["failed_phase"], result["probe_status"], result["next_actor"]),
                         ("dialog", "not_run", "human"))
        self.assertEqual(result["close_error_type"], "OSError")

    def test_window_scan_limits_query_failures_to_owned_pid(self):
        for mode, expected in (("foreign_failed", "windows"), ("owned_failed", "scan_failed"),
                               ("foreign_only", "no_windows"), ("enumeration_failed", "scan_failed")):
            with self.subTest(mode=mode):
                user = Mock()
                def enumerate_windows(callback, unused):
                    callback(101, 0)
                    if mode != "foreign_only":
                        callback(102, 0)
                    return mode != "enumeration_failed"
                def owner(hwnd, pointer):
                    pointer._obj.value = 4242 if hwnd == 102 else 0
                    return 0 if hwnd == 101 or mode == "owned_failed" else 1
                user.EnumWindows.side_effect = enumerate_windows
                user.GetWindowThreadProcessId.side_effect = owner
                user.GetWindowTextLengthW.return_value = 0
                user.GetWindowTextW.return_value = 0
                with patch.object(host.os, "name", "nt"), patch.object(host.ctypes, "WinDLL", return_value=user, create=True), \
                        patch.object(host.ctypes, "WINFUNCTYPE", return_value=lambda fn: fn, create=True), \
                        patch.object(host.ctypes, "set_last_error", create=True), \
                        patch.object(host.ctypes, "get_last_error", return_value=0, create=True):
                    result = host.window_scan(4242)
                self.assertEqual(result["state"], expected)
                self.assertTrue(all(call.args[0] == 102 for call in user.GetWindowTextW.call_args_list))

    def test_launch_rules_skip_stub_and_unmatched_failure_calls_it(self):
        cases = (("PATH unavailable", "rule_path", False), ("ExecutionPolicy blocked", "rule_execution_policy", False),
                 ("実行ポリシーで拒否", "rule_execution_policy", False), ("CIM denied", "rule_cim", False),
                 ("unknown launch fault", None, False), ("PATH unavailable", "rule_path", True))
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            root = Path(temp)
            script = root / "build.py"
            script.write_text("def build(doc): pass", encoding="utf-8")
            exe = root / "freecad/bin/freecadcmd.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"offline fixture; never executed")
            for index, (diagnostic, rule, spawn_error) in enumerate(cases):
                with self.subTest(diagnostic=diagnostic, spawn_error=spawn_error):
                    proc = SimpleNamespace(pid=4242, poll=lambda: 7,
                                           stdout=io.BufferedReader(io.BytesIO(b"")),
                                           stderr=io.BufferedReader(io.BytesIO(diagnostic.encode("utf-8"))))
                    spawn = Mock(side_effect=OSError(diagnostic)) if spawn_error else Mock(return_value=proc)
                    out = root / "reports/cad-run" / str(index)
                    args = host.parser().parse_args(["--script", str(script), "--out-dir", str(out), "--timeout-s", "1"])
                    with patch.object(host, "FREECAD_DIR", root / "freecad"), patch.object(host, "judge_stub", wraps=host.judge_stub) as judge:
                        result, code = host.run_attempt(args, root, spawn, Mock())
                    events = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
                    self.assertEqual((code, result["failed_phase"]), (1, "launch"))
                    self.assertEqual(judge.call_count, 0 if rule else 1)
                    self.assertEqual(sum(e["event"] == "j1_skipped" for e in events), 0 if rule else 1)
                    if rule:
                        self.assertEqual(result["message_code"], rule)
                    launches = [e for e in events if e["event"] == "launch_finished"]
                    self.assertEqual(launches[-1]["status"], "failed")
                    if not spawn_error:
                        self.assertEqual(launches[0]["status"], "pending")

    def test_unreported_exit_keeps_launch_pending_and_never_terminates_on_failed_scan(self):
        with tempfile.TemporaryDirectory(prefix="cad-run-unit-") as temp:
            root = Path(temp)
            script = root / "build.py"
            script.write_text("def build(doc): pass", encoding="utf-8")
            exe = root / "freecad/bin/freecadcmd.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"offline fixture; never executed")
            proc = SimpleNamespace(pid=4242, _handle=object(), poll=lambda: None, terminate=Mock(), wait=Mock(),
                                   stdout=io.BufferedReader(io.BytesIO(b"")), stderr=io.BufferedReader(io.BytesIO(b"")))
            out = root / "reports/cad-run/pending"
            args = host.parser().parse_args(["--script", str(script), "--out-dir", str(out), "--timeout-s", "1"])
            scan = Mock(return_value={"state": "scan_failed"})
            with patch.object(host, "FREECAD_DIR", root / "freecad"), patch.object(host.time, "monotonic", side_effect=(0, 2)), \
                    patch.object(host, "fail", wraps=host.fail) as failures:
                result, code = host.run_attempt(args, root, Mock(return_value=proc), scan)
            self.assertEqual((code, result["message_code"], result["cleanup_status"]), (1, "timeout", "cleanup_pending"))
            self.assertIsNone(result["cad_exit_code"])
            self.assertEqual(scan.call_count, 2)
            self.assertNotIn("cad_nonzero", [call.args[2] for call in failures.call_args_list])
            proc.terminate.assert_not_called()
            events = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([e["status"] for e in events if e["event"] == "launch_finished"], ["pending"])

    def test_disabled_judge_and_source_provenance(self):
        self.assertEqual(host.judge_stub(), {"enabled": False, "invoked": False, "decision": None, "usage": None})
        self.assertEqual(fixture.SOURCE_SHA256, hashlib.sha256((host.ROOT / fixture.SOURCE).read_bytes()).hexdigest())
        for file in ("cad_run.py", "cad_run_freecad.py", "fixtures/cad_run_a_build.py"):
            text = (host.ROOT / "tools" / file).read_text(encoding="utf-8").lower()
            for forbidden in ("Get" + "-CimInstance", "Win32" + "_Process", "w" + "mi",
                              "so" + "cket", "ht" + "tp", "url" + "lib"):
                self.assertNotIn(forbidden.lower(), text)


    def test_task_selection_and_worker_protocol(self):
        cli = ["--script", "unused.py", "--out-dir", "unused", "--timeout-s", "1"]
        self.assertEqual(host.parser().parse_args(cli).task, specs.TASK_A)
        self.assertEqual(host.parser().parse_args(cli + ["--task", specs.TASK_B]).task, specs.TASK_B)
        with patch.object(host, "run_attempt") as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(host.main(cli + ["--task", "unknown"]), 2)
            run.assert_not_called()
        result = host.new_result(specs.TASK_B)
        result.update(attempt_id="a", script_sha256="h")
        report = {"schema": "cad-harness.cad_run.worker.v0", "attempt_id": "a",
                  "script_sha256": "h", "owned_pid": 42, "status": "failed",
                  "failed_phase": "probe", "probe_status": "predicate_fail", "next_actor": "sol",
                  "document_closed": True, "timings_ms": dict(build=1, recompute=2, probe=3, save=4)}
        for task in (None, specs.TASK_A):
            with self.subTest(task=task), self.assertRaises(ValueError):
                host.merge_worker(result, dict(report, **({"task_id": task} if task else {})),
                                  SimpleNamespace(pid=42))
        host.merge_worker(result, dict(report, task_id=specs.TASK_B), SimpleNamespace(pid=42))
        self.assertEqual(result["timings_ms"], report["timings_ms"])

    def test_b_predicates_reject_independent_geometry_and_history_errors(self):
        good = {"body_count": 1, "body_identity": True, "solid_count": 1, "is_valid": True,
                "bound_box_mm": dict(zip(worker.BOX_KEYS, (-40, 40, -30, 30, 0, 10, 80, 60, 10))),
                "volume_mm3": 48000 - 30 * 20 * 4 - 3 * pi * 3**2 * 10 - 416 / 3,
                "feature_counts": {"PartDesign::Body": 1, "Sketcher::SketchObject": 3,
                                   "PartDesign::Pad": 1, "PartDesign::Pocket": 2,
                                   "PartDesign::LinearPattern": 1, "PartDesign::Chamfer": 1,
                                   "PartDesign::Fillet": 0},
                "standard_auxiliaries": True, "feature_chain_ok": True,
                "pocket_geometry": True, "pocket_inner_sharp": True, "pocket_depth_mm": 4,
                "pocket_length_mode": True,
                "pocket_sketch_box": dict(zip(worker.BOX_KEYS, (-15, 15, -10, 10, 10, 10))),
                "hole_pattern_attributes": True, "outer_chamfer_geometry": True,
                "outer_chamfer_selection": True,
                "holes": [dict(x=x, y=-20, radius=3, axis=[0, 0, 1], z_min=0, z_max=10,
                               top_open=True, bottom_open=True, axis_empty=True) for x in (-20, 0, 20)]}
        self.assertTrue(all(specs.b_predicates(good).values()))
        for fault, expected in (("chamfer", {"volume", "feature_counts", "feature_chain", "outer_chamfer"}),
                                ("depth", {"central_pocket"}), ("count", {"holes_pattern"}),
                                ("position", {"holes_pattern"})):
            changed = copy.deepcopy(good)
            if fault == "chamfer":
                changed.update(volume_mm3=45600 - 270 * pi, feature_chain_ok=False,
                               outer_chamfer_geometry=False, outer_chamfer_selection=False)
                changed["feature_counts"]["PartDesign::Chamfer"] = 0
            elif fault == "depth":
                changed["pocket_depth_mm"] = 5
            elif fault == "count":
                changed["holes"].pop()
            else:
                changed["holes"][1]["x"] = 1
            with self.subTest(fault=fault):
                self.assertEqual({k for k, v in specs.b_predicates(changed).items() if not v}, expected)

    def fake_b_probe_input(self, fault=None, direction="vector"):
        # Small geometric doubles: b_probe reads these faces/edges, not preset flags.
        class Entity:
            def __init__(self, **fields):
                self.__dict__.update(fields)
        class Vector:
            def __init__(self, x, y, z):
                self.x, self.y, self.z = x, y, z
            def __iter__(self):
                return iter((self.x, self.y, self.z))
            def dot(self, other):
                return sum(a * b for a, b in zip(self, other))
        class Plane:
            pass
        class Line:
            pass
        class Cylinder(Entity):
            pass
        class Circle(Entity):
            pass
        def bounds(values):
            x0, x1, y0, y1, z0, z1 = values
            return Entity(XMin=x0, XMax=x1, YMin=y0, YMax=y1, ZMin=z0, ZMax=z1,
                          XLength=x1-x0, YLength=y1-y0, ZLength=z1-z0)
        def box_points(points):
            return bounds([f(p[i] for p in points) for i in range(3) for f in (min, max)])
        def vertices(points):
            return [Entity(Point=Vector(*p)) for p in points]
        def line(a, b):
            edge = Entity(Curve=Line(), Vertexes=vertices((a, b)), BoundBox=box_points((a, b)),
                          Length=sum((v-u)**2 for u, v in zip(a, b))**0.5)
            edge.Curve.Direction = Vector(*(v-u for u, v in zip(a, b)))
            edge.isSame = lambda other: edge is other
            return edge
        def rectangle(x, y, z):
            points = [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
            return [line(points[i], points[(i+1) % 4]) for i in range(4)]
        def shape(values, edges=()):
            return Entity(BoundBox=bounds(values), Edges=list(edges), Faces=[], Solids=[object()],
                          Volume=specs.B_VOLUME, Area=0, isValid=lambda: True,
                          isInside=lambda point, tol, boundary: False)
        def face(points, normal, edges=(), surface=None):
            return Entity(BoundBox=box_points(points), Vertexes=vertices(points), Edges=list(edges),
                          Surface=surface or Plane(), normalAt=lambda u, v: Vector(*normal))
        def rim(x, y, z, length=6*pi):
            curve = Circle(Center=Vector(x, y, z), Radius=3, Axis=Vector(0, 0, 1))
            return Entity(Curve=curve, BoundBox=bounds((x-3, x+3, y-3, y+3, z, z)),
                          Vertexes=[], Length=length)
        top_inner, bottom_inner = rectangle(15, 10, 10), rectangle(15, 10, 6)
        corners = [(-15, -10), (15, -10), (15, 10), (-15, 10)]
        vertical = [line((x, y, 6), (x, y, 10)) for x, y in corners]
        outer = rectangle(39, 29, 10)
        floor_z = 5 if fault == "floor" else 6
        faces = [face([(x, y, floor_z) for x, y in corners], (0, 0, 1), bottom_inner)]
        for i, normal in enumerate(((0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0))):
            p, q = corners[i], corners[(i+1) % 4]
            faces.append(face([(*p, 6), (*q, 6), (*q, 10), (*p, 10)], normal,
                              [top_inner[i], bottom_inner[i], vertical[i], vertical[(i+1) % 4]]))
        faces.append(face([(-39,-29,10),(39,-29,10),(39,29,10),(-39,29,10)],
                          (0,0,1), top_inner + outer))
        for index, (axis, side, half, span) in enumerate(
                (("x",-1,40,30),("x",1,40,30),("y",-1,30,40),("y",1,30,40))):
            if fault == "bevel" and index == 0:
                continue
            points = [(side*half, -span, 9), (side*half, span, 9),
                      (side*(half-1), span-1, 10), (side*(half-1), -span+1, 10)]
            normal = (side*2**-0.5, 0, 2**-0.5)
            if axis == "y":
                points = [(y,x,z) for x,y,z in points]
                normal = (0, side*2**-0.5, 2**-0.5)
            faces.append(face(points, normal))
        edges = top_inner + bottom_inner + vertical + outer
        for x in (-20, 0, 20):
            x = 1 if fault == "hole" and x == 0 else x
            cylinder = Cylinder(Center=Vector(x,-20,0), Radius=3, Axis=Vector(0,0,1))
            # Exercise grouping of split cylinder faces and circle arcs.
            for low, high in ((0,5),(5,10)):
                faces.append(face([(x-3,-23,low),(x+3,-17,high)], (1,0,0), surface=cylinder))
            for z in (0,10):
                edges.extend((rim(x,-20,z,3*pi), rim(x,-20,z,3*pi)))
        final = shape((-40,40,-30,30,0,10), edges)
        final.Faces = faces
        origin = Entity(TypeId="App::Origin")
        axis = Entity(TypeId="App::Line", Role="X_Axis", InList=[origin],
                      getGlobalPlacement=lambda: Entity(Rotation=Entity(multVec=lambda v: v)))
        origin.OriginFeatures = [axis]
        body = Entity(TypeId="PartDesign::Body", Origin=origin, Shape=final,
                      Placement=Entity(isIdentity=lambda: True))
        def sketch(values, count, edges=()):
            return Entity(TypeId="Sketcher::SketchObject", Shape=shape(values, edges), GeometryCount=count)
        # Extra construction geometry must not invalidate otherwise correct profiles.
        base = sketch((-40,40,-30,30,0,0), 5, rectangle(40,30,0))
        ps = sketch((-15,15,-10,10,10,10), 5, top_inner)
        hs = sketch((-23,-17,-23,-17,10,10), 2, [rim(-20,-20,10)])
        def feature(kind, profile, length, previous=None):
            return Entity(TypeId="PartDesign::"+kind, Profile=profile, Length=Entity(Value=length),
                          Type="Length", Reversed=False, PropertiesList=[], Midplane=False,
                          BaseFeature=previous)
        pad = feature("Pad", base, 10)
        pad.getSubObject = lambda name: line((0,0,0),(2,0,0))
        central, hole = feature("Pocket", ps, 4, pad), None
        hole = feature("Pocket", hs, 10, central)
        ps.AttachmentSupport, hs.AttachmentSupport = (pad, ["Face1"]), (central, ["Face1"])
        ps.MapMode = hs.MapMode = "FlatFace"
        selected = {"vector": Vector(7,0,0), "origin": (axis, [""]), "edge": (pad, ["Edge1"]),
                    "negative": Vector(-1,0,0), "zero": Vector(0,0,0), "reversed": Vector(1,0,0)}[direction]
        pattern = Entity(TypeId="PartDesign::LinearPattern", Originals=[hole], BaseFeature=hole,
                         Direction=selected, Length=Entity(Value=40), Occurrences=3,
                         Reversed=direction == "reversed", Shape=shape((-40,40,-30,30,0,10),
                                                                       rectangle(40,30,10)))
        chamfer = Entity(TypeId="PartDesign::Chamfer", Base=(pattern, ["Edge1","Edge2","Edge3","Edge4"]),
                         Size=Entity(Value=1))
        body.Group = [base,pad,ps,central,hs,hole,pattern,chamfer]
        body.Tip = chamfer
        doc = Entity(Objects=[body,origin,axis] + body.Group)
        modules = {"FreeCAD": Entity(Vector=Vector), "Part": Entity(
            Plane=Plane, Line=Line, Circle=Circle, Cylinder=Cylinder)}
        return doc, body, modules

    def test_b_probe_extracts_faces_circles_and_rejects_only_matching_geometry(self):
        cases = ((None, set()), ("hole", {"holes_pattern"}), ("floor", {"central_pocket"}),
                 ("bevel", {"outer_chamfer"}))
        for fault, expected in cases:
            with self.subTest(fault=fault):
                doc, body, modules = self.fake_b_probe_input(fault)
                with patch.dict("sys.modules", modules):
                    result = specs.b_probe(doc, body)
                self.assertEqual({k for k,v in result["predicates"].items() if not v}, expected)
                self.assertEqual(result["probe_pass"], not expected)
        for direction in ("origin", "edge", "negative", "zero", "reversed"):
            with self.subTest(direction=direction):
                doc, body, modules = self.fake_b_probe_input(direction=direction)
                with patch.dict("sys.modules", modules):
                    result = specs.b_probe(doc, body)
                expected = {"feature_chain"} if direction in ("negative", "zero", "reversed") else set()
                self.assertEqual({k for k,v in result["predicates"].items() if not v}, expected)

    def test_worker_clocks_record_stages_failures_and_unreached_nulls(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "model.FCStd"
            doc = SimpleNamespace(recompute=Mock(), saveAs=lambda name: Path(name).write_bytes(b"model"))
            body = SimpleNamespace(Document=doc, TypeId="PartDesign::Body")
            observed = {"probe_pass": True, "predicates": {"ok": True}, "measurements": {}}
            with patch.object(worker.time, "monotonic", side_effect=(1, 1.1, 2, 2.2, 3, 3.3, 4, 4.4)):
                result = worker.execute(self.fake_app(doc), lambda d: body, path, Mock(),
                                        lambda d, b: observed, task_id=specs.TASK_B)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(doc.Name, "CadRunB")
            for name, expected in zip(("build", "recompute", "probe", "save"), (100, 200, 300, 400)):
                self.assertAlmostEqual(result["timings_ms"][name], expected)
            for stage, phase, actor, reached in (("build", "build", "sol", 1),
                                                ("recompute", "build", "human", 2),
                                                ("probe", "probe", "human", 3),
                                                ("save", "build", "human", 4)):
                doc.recompute.side_effect = RuntimeError("recompute") if stage == "recompute" else None
                doc.saveAs = Mock(side_effect=OSError("save")) if stage == "save" else Mock()
                builder = Mock(side_effect=RuntimeError("build")) if stage == "build" else lambda d: body
                prober = Mock(side_effect=RuntimeError("probe")) if stage == "probe" else lambda d, b: observed
                with self.subTest(stage=stage), patch.object(
                        worker.time, "monotonic", side_effect=range(2 * reached)):
                    result = worker.execute(self.fake_app(doc), builder, path, Mock(), prober)
                self.assertEqual((result["failed_phase"], result["next_actor"]), (phase, actor))
                self.assertEqual(list(result["timings_ms"].values()),
                                 [1000] * reached + [None] * (4 - reached))
            for kind in ("ready", "event"):
                self.assertTrue(worker.worker_row(kind, {})["ts"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
