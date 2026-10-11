"""MVP driver, failure routing and verification contracts; all processes mocked."""
import hashlib
import ast
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, Mock

from tools import cad_agent as agent, cad_run, cad_verify_freecad
from tools.fixtures.cad_mvp_build import typed_spec
from tools.test_support import start_tempdirs, stop_tempdirs

ROOT = Path(__file__).resolve().parents[1]
DETAILS = {"version":1,"task_id":"P5","checks":[{"predicate":"holes","sub_check_id":"holes.0.radius",
           "expected":2.5,"actual":3.5,"tolerance":.01}],"truncated":False,"omitted":0}


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class MvpTests(unittest.TestCase):
    def root(self, temp):
        root = Path(temp) / "repo"
        for name in ("skills/freecad-modeling/SKILL.md", "design/cad-harness-mvp/build-schema.json"):
            file = root / name
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes((ROOT/name).read_bytes())
        return root

    def runner(self, outputs, plans=(), clock=None):
        calls, cads = [], []
        def run(argv, **kwargs):
            self.assertFalse(kwargs["shell"])
            self.assertLessEqual(kwargs["timeout"], 900)
            if argv[1] == "--version":
                return subprocess.CompletedProcess(argv,0,"codex-cli mock-0.159.2","")
            if argv[1] == "exec":
                context = next(x for x in argv if x.startswith("developer_instructions="))
                calls.append((argv[-1],context,kwargs["cwd"]))
                self.assertLessEqual(len(calls),3)
                Path(argv[argv.index("-o")+1]).write_text(outputs[len(calls)-1],encoding="utf-8")
                if clock is not None: clock[0] += 10
                return subprocess.CompletedProcess(argv,0,'{"type":"turn.completed","usage":{"output_tokens":10}}',"")
            self.assertEqual(Path(argv[2]).name,"cad_run.py")
            self.assertEqual(argv[argv.index("--probe-profile")+1],"mvp-v1")
            self.assertLessEqual(int(argv[argv.index("--timeout-s")+1]),300)
            script,out,gold = (Path(argv[argv.index(flag)+1]) for flag in ("--script","--out-dir","--gold"))
            cads.append(argv)
            self.assertLessEqual(len(cads),3)
            plan = plans[len(cads)-1] if len(plans)>=len(cads) else {}
            result = {"schema":"cad-harness.cad_run.v0","task_id":"P5","attempt_id":"mock",
                      "script_sha256":hashlib.sha256(script.read_bytes()).hexdigest(),
                      "gold_sha256":hashlib.sha256(gold.read_bytes()).hexdigest(),"status":"ok",
                      "probe_pass":True,"probe_status":"pass","verification_pass":True,
                      "geometry_ok":True,"editability_ok":True,"cad_exit_code":0,"document_closed":True,
                      "cleanup_status":"exited","next_actor":None,"failed_phase":None}
            result.update({k:v for k,v in plan.items() if k != "exit"})
            out.mkdir()
            (out/"result.json").write_text(json.dumps(result),encoding="utf-8")
            return subprocess.CompletedProcess(argv,plan.get("exit",0),json.dumps(result),"")
        return run,calls,cads

    def drive(self, root, runner, mode="description", spec=None, evaluation=True, clock=None):
        gold = ROOT/"design/cad-harness-mvp/eval-v1/P5.json"
        text = json.dumps(spec or typed_spec("P5")) if mode == "typed" else json.loads(gold.read_text(encoding="utf-8"))["description"]
        return agent.run_mvp_driver("unit-mvp1","mock-only",text,gold,mode=mode,root=root,
                                    runner=runner,evaluation=evaluation,clock=clock)

    def test_typed_zero_calls_description_preview_and_eval(self):
        for mode,evaluation,model_count,cad_count,status in (("typed",True,0,1,"ok"),
                    ("description",False,1,0,"preview"),("description",True,1,1,"ok")):
            with self.subTest(mode=mode,evaluation=evaluation),tempfile.TemporaryDirectory() as temp:
                root = self.root(temp)
                runner,calls,cads = self.runner([json.dumps(typed_spec("P5"))])
                report,code = self.drive(root,runner,mode=mode,evaluation=evaluation)
                self.assertEqual((code,report["status"],len(calls),len(cads)),(0,status,model_count,cad_count))
                if calls:
                    self.assertEqual(agent.digest(calls[0][0]),report["description_sha256"])
                    self.assertNotIn("cad-harness.gold.v1",calls[0][1])
                    self.assertNotIn(report["gold_sha256"],calls[0][1])
                    self.assertFalse(Path(calls[0][2]).is_relative_to(root))

    def test_spec_geometry_repair_has_details_only_in_separate_context(self):
        wrong = typed_spec("P5")
        wrong["holes"][0]["diameter"] = 7
        failure = {"exit":1,"status":"failed","failed_phase":"probe","probe_pass":False,
                   "probe_status":"predicate_fail","next_actor":"sol","geometry_ok":False,
                   "predicate_diff":["holes"],"predicate_details":DETAILS,"measurements":{"volume_mm3":29000}}
        with tempfile.TemporaryDirectory() as temp:
            runner,calls,cads = self.runner([json.dumps(wrong),json.dumps(typed_spec("P5"))],[failure,{}])
            report,code = self.drive(self.root(temp),runner)
            self.assertEqual((code,len(calls),len(cads)),(0,2,2))
            self.assertEqual(calls[0][0],calls[1][0])
            self.assertNotIn("predicate_details",calls[1][0])
            self.assertIn("holes.0.radius",calls[1][1])
            self.assertEqual(report["attempts"][0]["result"]["predicate_details"],DETAILS)

    def test_fallback_invalid_outputs_shared_limit_and_repeated_spec_stops(self):
        failures = {"exit":1,"status":"failed","failed_phase":"probe","probe_pass":False,
                    "probe_status":"predicate_fail","next_actor":"sol","predicate_diff":["holes"],
                    "measurements":{"volume_mm3":29000}}
        spec = json.dumps(typed_spec("P5"))
        cases = ((['{"unsupported":["other shape"]}',"pass","def build(doc): return doc"],[{}],3,1,"ok"),
                 (["bad","bad","bad"],[],3,0,"call_limit"),
                 ([spec,spec],[failures],2,1,"unchanged_spec"))
        for outputs,plans,call_count,cad_count,reason in cases:
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as temp:
                runner,calls,cads = self.runner(outputs,plans)
                report,code = self.drive(self.root(temp),runner)
                self.assertEqual((len(calls),len(cads)),(call_count,cad_count))
                self.assertEqual(report["status"] if reason == "ok" else report["message_code"],reason)

    def test_native_and_io_failures_do_not_call_model_to_repair(self):
        for plan in ({"editability_ok":False},{"save_error_type":"OSError"},
                     {"failed_phase":"verification","next_actor":"human"},{"cleanup_status":"cleanup_pending"}):
            with self.subTest(plan=plan),tempfile.TemporaryDirectory() as temp:
                failure = {"exit":1,"status":"failed","failed_phase":"probe","probe_pass":False,
                           "probe_status":"predicate_fail","next_actor":"sol","predicate_diff":["holes"]}
                failure.update(plan)
                runner,calls,cads = self.runner([json.dumps(typed_spec("P5"))],[failure])
                report,code = self.drive(self.root(temp),runner)
                self.assertEqual((code,len(calls),len(cads)),(1,1,1))

    def test_deadline_clips_cad_and_cannot_return_late_success(self):
        clock = [0.0]
        with tempfile.TemporaryDirectory() as temp:
            runner,calls,cads = self.runner([json.dumps(typed_spec("P5"))],clock=clock)
            base = runner
            def slow(argv,**kwargs):
                clock[0] = 885 if argv[1] == "exec" else clock[0]
                result = base(argv,**kwargs)
                if argv[1] not in ("exec", "--version"): clock[0] = 901
                return result
            report,code = self.drive(self.root(temp),slow,clock=lambda:clock[0])
            self.assertEqual((code,report["message_code"]),(1,"deadline_exceeded"))
            self.assertEqual(cads[0][cads[0].index("--timeout-s")+1],"5")

    def test_verify_hash_binding_rejects_before_opening_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            gold = ROOT/"design/cad-harness-mvp/eval-v1/P5.json"
            raw = gold.read_bytes()
            (directory/"gold.json").write_bytes(raw)
            for name in ("model.FCStd","model.step"): (directory/name).write_bytes(b"changed artifact")
            app = NS(GuiUp=0,Version=lambda:["1","1","4"],listDocuments=lambda:{},openDocument=Mock())
            request = {"task_id":"P5","gold_sha256":hashlib.sha256(raw).hexdigest(),"artifact_sha256":{}}
            result = cad_verify_freecad.verify(app,Mock(),request,directory)
            self.assertFalse(result["verification_pass"])
            self.assertEqual(result["error_code"],"verify_artifact_hash")
            app.openDocument.assert_not_called()

    def test_source_contract_cli_owns_imports_lifecycle_and_io(self):
        for source in ("import os", "from pathlib import Path", "open('file')",
                       "App.newDocument('x')", "doc.saveAs('x')", "Part.export([],'x')"):
            with self.subTest(source=source), self.assertRaises(cad_run.InputError):
                cad_run.source_contract(ast.parse("def build(doc):\n    " + source))
        cad_run.source_contract(ast.parse("import FreeCAD as App\ndef build(doc):\n    return doc.addObject('PartDesign::Body','Body')"))


if __name__ == "__main__":
    unittest.main()
