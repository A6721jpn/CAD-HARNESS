"""Minimal offline VERIFY contracts. Every model/process invocation is mocked."""
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, Mock

from tools import cad_agent, cad_spec, cad_verify_probe, eval_verify
from tools.cad_verify_guard import Guard, Fault, Stop, quota_snapshot, q_score
from tools.test_support import start_tempdirs, stop_tempdirs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"design/cad-harness-verify"
NOW=datetime(2026,10,12,8,0,tzinfo=timezone.utc)


def setUpModule():
    global _temps
    _temps=start_tempdirs()


def tearDownModule(): stop_tempdirs(_temps)


class VerifyTests(unittest.TestCase):
    def snapshot(self,d,percent=20,age=0):
        p=Path(d)/"quota.json"
        p.write_text(json.dumps(dict(snapshot_id="supervisor-1",observed_at=(NOW-timedelta(seconds=age)).isoformat(),used_percent=percent)),encoding="utf-8")
        return p

    def root(self,d):
        root=Path(d)/"repo"
        for name in ("skills/freecad-modeling/SKILL.md","design/cad-harness-mvp/build-schema.json"):
            p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes((ROOT/name).read_bytes())
        return root

    def spec(self,case="V6"):
        if case=="V6":
            spec=json.loads((BASE/"test/F3/candidate.json").read_text(encoding="utf-8"))
            spec["holes"][0]["diameter"]=4
            return spec
        g=json.loads((BASE/"test/Q1/gold.json").read_text(encoding="utf-8"))
        return dict(schema="cad-harness.build-spec.v1",family="rect_prism",units="mm",frame="world",regions=[{"bounds":g["bbox"]}],
                    holes=[{k:v for k,v in h.items() if k!="through"} for h in g["holes"]],pockets=[],finish=None)

    def runner(self,outputs,case,cad_plans=(),clock=None):
        calls=[]; cad=[]
        def run(argv,**kwargs):
            self.assertFalse(kwargs["shell"])
            if argv[1]=="--version": return subprocess.CompletedProcess(argv,0,"mock CLI","")
            if argv[1]=="exec":
                calls.append(argv)
                Path(argv[argv.index("-o")+1]).write_text(outputs[len(calls)-1],encoding="utf-8")
                if clock: clock[0]+=10
                return subprocess.CompletedProcess(argv,0,'{"type":"turn.completed","usage":{"input_tokens":11,"output_tokens":2}}',"")
            self.assertEqual(Path(argv[2]).name,"cad_run.py")
            self.assertEqual(argv[argv.index("--probe-profile")+1],"verify-v1")
            self.assertLessEqual(int(argv[argv.index("--timeout-s")+1]),300)
            script,out,gold=[Path(argv[argv.index(k)+1]) for k in ("--script","--out-dir","--gold")]
            cad.append(argv); plan=cad_plans[len(cad)-1] if len(cad_plans)>=len(cad) else {}
            r=dict(schema="cad-harness.cad_run.v0",task_id=case,script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
                   gold_sha256=hashlib.sha256(gold.read_bytes()).hexdigest(),status="ok",geometry_ok=True,editability_ok=True,
                   probe_pass=True,probe_status="pass",script_completed=True,verification_pass=True,document_closed=True,
                   cleanup_status="exited",cad_exit_code=0,failed_phase=None,next_actor=None,generator=argv[argv.index("--generator")+1],
                   measurements={"editability":{"native_valid":True}})
            r.update(plan); code=0 if r["status"]=="ok" else 1
            out.mkdir(); (out/"result.json").write_text(json.dumps(r),encoding="utf-8")
            return subprocess.CompletedProcess(argv,code,json.dumps(r),"")
        return run,calls,cad

    def drive(self,d,outputs,case="Q1",plans=(),first=False,fault=None,clock=None):
        root=self.root(d); where=BASE/"test"/case
        rubric=json.loads((where/"rubric.json").read_text(encoding="utf-8")) if first else None
        runner,calls,cad=self.runner(outputs,case,plans,clock)
        guard=Guard(self.snapshot(d),clock=(lambda:clock[0]) if clock else None,now=lambda:NOW)
        report,code=cad_agent.run_mvp_driver("unit-verify-mvp1","mock-only",(where/"description.txt").read_text(encoding="utf-8"),
                    where/"gold.json" if (where/"gold.json").exists() else None,root=root,runner=runner,
                    evaluation=True,probe_profile="verify-v1",first_response_only=first,rubric=rubric,fault=fault,guard=guard,
                    max_calls=1 if first else 3)
        return report,code,calls,cad

    def test_frozen_texts_gold_stock_scope_and_fixed_order(self):
        plan=(BASE/"PLAN-CONSENSUS.md").read_text(encoding="utf-8")
        for part in ("test","dev"):
            for p in (BASE/part).glob("*/gold.json"):
                g=cad_verify_probe.load_gold(p)
                self.assertEqual((p.parent/"description.txt").read_bytes().decode("utf-8"),g["description"])
                if part=="test": self.assertIn(g["description"],plan)
        g=cad_verify_probe.load_gold(BASE/"test/S1/gold.json")
        self.assertEqual(g["volume"]["target_mm3"],29232)
        self.assertEqual(g["volume_scope"],[-29,29,-21,21,0,12])
        g=cad_verify_probe.load_gold(BASE/"test/V2/gold.json")
        self.assertEqual(g["sections"][1],dict(kind="rectangle",z=15,bounds=[-16,16,-10,10]))
        order=json.loads((BASE/"run-order.json").read_text(encoding="utf-8"))
        self.assertEqual(len(order["entries"]),54)
        self.assertEqual(sum(e["max_calls"] for e in order["entries"]),125)
        self.assertEqual(sum(e["min_calls"] for e in order["entries"]),71)
        self.assertEqual([e["case"] for e in order["entries"] if e["group"]=="fault"],["F1","F2","F3"]*2)
        for path in BASE.glob("*/*/*.py"):
            tree=ast.parse(path.read_text(encoding="utf-8")); cad_agent.cad_run.source_contract(tree)
            self.assertNotIn("cad_spec",path.read_text(encoding="utf-8"))

    def test_snapshot_age_thresholds_and_invalid_values_stop(self):
        with tempfile.TemporaryDirectory() as d:
            for pct,age,decision in ((54.9,300,"allow"),(55,0,"quota_soft_stop"),(60,0,"quota_hard_stop"),
                                     (20,301,"quota_snapshot_stale"),(20,-1,"quota_snapshot_future")):
                r=quota_snapshot(self.snapshot(d,pct,age),NOW)
                self.assertEqual(r["decision"],decision); self.assertTrue(r["sha256"])
            for value in (True,-1,101,float("nan")):
                with self.assertRaises(Stop): quota_snapshot(self.snapshot(d,value),NOW)
            with self.assertRaises(Stop): quota_snapshot(Path(d)/"absent.json",NOW)

    def test_shared_deadline_budget_and_quota_checked_before_every_call(self):
        with tempfile.TemporaryDirectory() as d:
            clock=[0.0]; p=self.snapshot(d)
            guard=Guard(p,clock=lambda:clock[0],now=lambda:NOW,call_budget=2)
            guard.before_call(); self.snapshot(d,55)
            with self.assertRaisesRegex(Stop,"soft_stop"): guard.before_call()
            self.assertEqual(guard.calls,1)
            self.snapshot(d,20); guard.before_call()
            with self.assertRaisesRegex(Stop,"budget"): guard.before_run(1)
            clock[0]=10796
            with self.assertRaisesRegex(Stop,"deadline"): guard.remaining()

    def test_clarification_and_invalid_first_response_are_one_call_zero_cad(self):
        for case,final,score in (("Q2",'{"needs_clarification":["plate_thickness"]}',1),
                                 ("Q3",'{"needs_clarification":["hole_positions"]}',1),
                                 ("Q2",'{"needs_clarification":["hole_positions"]}',0),
                                 ("Q3",'{"unsupported":["ambiguous"]}',0),("Q2","invalid",0)):
            with self.subTest(case=case,final=final),tempfile.TemporaryDirectory() as d:
                r,code,calls,cad=self.drive(d,[final],case,first=True)
                rubric=json.loads((BASE/"test"/case/"rubric.json").read_text(encoding="utf-8"))
                self.assertEqual((len(calls),len(cad)),(1,0))
                self.assertEqual(q_score(r["first_response"],False,case,rubric)[0],score)
                self.assertEqual(calls[0][-1],(BASE/"test"/case/"description.txt").read_text(encoding="utf-8"))
                self.assertNotIn("verify-gold",str(calls[0]))

    def test_q1_initial_defaults_final_gate_and_unnecessary_question(self):
        for outputs,expected in (([json.dumps(self.spec())],1),(['{"needs_clarification":["plate_thickness"]}'],0)):
            with tempfile.TemporaryDirectory() as d:
                r,code,calls,cad=self.drive(d,outputs)
                self.assertEqual(q_score(r["first_response"],r["status"]=="ok","Q1")[0],expected)
                self.assertEqual(len(calls),1)
                self.assertEqual(len(cad),expected)

    def test_critical_invention_scores_zero(self):
        for case in ("Q2","Q3"):
            rubric=json.loads((BASE/"test"/case/"rubric.json").read_text(encoding="utf-8"))
            first=dict(kind="spec",raw=self.spec())
            self.assertEqual(q_score(first,True,case,rubric),(0,True))

    def test_frozen_fault_once_and_real_settled_fail_then_repair(self):
        for fault_id,case in (("F1","F1"),("F2","F2"),("F3","F3")):
            with self.subTest(fault=fault_id),tempfile.TemporaryDirectory() as d:
                fault=Fault(BASE/"test"/fault_id/"fault.json")
                if fault_id=="F3":
                    outputs=[json.dumps(self.spec("V6")),json.dumps(self.spec("V6"))]
                    pred="holes"
                else:
                    outputs=['{"unsupported":["unsupported geometry"]}',"def build(doc): return doc","def build(doc): return doc"]
                    pred="roller" if fault_id=="F1" else "holes"
                fail=dict(status="failed",geometry_ok=False,probe_pass=False,probe_status="predicate_fail",
                          next_actor="sol",failed_phase="probe",predicate_diff=[pred])
                r,code,calls,cad=self.drive(d,outputs,case,[fail,{}],fault=fault)
                self.assertEqual((code,len(calls),len(cad)),(0,2 if fault_id=="F3" else 3,2))
                self.assertTrue(r["fault"]["reached"]); self.assertTrue(r["fault"]["injected"])
                self.assertTrue(r["fault"]["established"]); self.assertTrue(r["fault"]["detected"])
                self.assertNotEqual(r["fault"]["original_sha256"],r["fault"]["injected_sha256"])
                self.assertEqual(r["fault"]["actual_call"],2 if fault_id!="F3" else 1)
                self.assertEqual([a[-1] for a in calls],[calls[0][-1]]*len(calls))

    def test_fault_target_missing_is_not_reached_and_not_retried(self):
        for defect in ("path_missing","match_missing","match_ambiguous"):
            with self.subTest(defect=defect):
                candidate=self.spec("V6")
                if defect=="path_missing": del candidate["holes"]
                elif defect=="match_missing": candidate["holes"][0]["diameter"]=5
                else: candidate["holes"].append(dict(candidate["holes"][0]))
                original=json.loads(json.dumps(candidate))
                fault=Fault(BASE/"test/F3/fault.json")
                self.assertIs(fault.inject("spec",candidate),candidate)
                self.assertEqual(candidate,original)
                self.assertTrue(fault.attempted)
                self.assertFalse(fault.record["reached"])
                self.assertFalse(fault.record["injected"])
                self.assertIsNone(fault.record["injected_sha256"])
                self.assertEqual(fault.record["not_reached_reason"],"candidate_target_missing")
                retry=self.spec("V6")
                self.assertIs(fault.inject("spec",retry),retry)
                self.assertFalse(fault.record["reached"])
                self.assertFalse(fault.record["injected"])

    def test_injection_does_not_force_failure_false_pass_stops(self):
        with tempfile.TemporaryDirectory() as d:
            fault=Fault(BASE/"test/F3/fault.json")
            r,code,calls,cad=self.drive(d,[json.dumps(self.spec("V6"))],"F3",fault=fault)
            self.assertEqual((code,len(calls),len(cad)),(1,1,1))
            self.assertEqual(r["message_code"],"fault_false_pass")
            self.assertFalse(r["fault"]["detected"])

    def test_unused_decoy_dimensions_do_not_supply_editability(self):
        solid=NS(isSame=lambda other:other is solid)
        shape=NS(isValid=lambda:True,Solids=[solid],isNull=lambda:False)
        consumed=NS(Name="Used",TypeId="Sketcher::SketchObject",Shape=shape,GeometryCount=1,
                    Constraints=[],getConstruction=lambda i:False,Placement=NS(Base=NS(x=0,y=0,z=0)),MapMode="Deactivated",State=[])
        unused=NS(Name="Decoy",TypeId="Sketcher::SketchObject",Shape=shape,GeometryCount=1,
                  Constraints=[NS(Type="Distance",First=0,Value=99)],getDriving=lambda i:True,getConstruction=lambda i:False,State=[])
        tip=NS(Name="Tip",TypeId="PartDesign::Pad",Shape=shape,Profile=consumed,PropertiesList=["Length"],Length=10,State=[])
        body=NS(TypeId="PartDesign::Body",Tip=tip,Group=[consumed,unused,tip],State=[])
        doc=NS(Objects=[body,consumed,unused,tip])
        g={"editability":{"key_dimensions_mm":[99]}}
        checks=cad_verify_probe.Checks("mock")
        m,w=cad_verify_probe.editability(doc,body,shape,g,checks,native_shape=shape)
        self.assertTrue(m["native_valid"]); self.assertEqual(m["used_sketches"],1)
        self.assertFalse(checks.predicates["editability"])

    def test_straight_bspline_samples_preserve_segment_coverage(self):
        # DV2 native Loft sections expose straight B-spline edges. The Probe
        # adds three interior samples to their two endpoints before projection.
        class Vec:
            def __init__(self,x=0,y=0,z=0): self.x,self.y,self.z=x,y,z
            def __sub__(self,v): return Vec(self.x-v.x,self.y-v.y,self.z-v.z)
            def __truediv__(self,n): return Vec(self.x/n,self.y/n,self.z/n)
            @property
            def Length(self): return math.sqrt(self.dot(self))
            def dot(self,v): return self.x*v.x+self.y*v.y+self.z*v.z
            def cross(self,v): return Vec(self.y*v.z-self.z*v.y,self.z*v.x-self.x*v.z,self.x*v.y-self.y*v.x)

        def edge(low,high,bend=0):
            return NS(Curve=object(),Vertexes=[NS(Point=Vec(low)),NS(Point=Vec(high))],
                      FirstParameter=0,LastParameter=1,
                      valueAt=lambda t:Vec(low+(high-low)*t,bend*(1-abs(2*t-1))))

        with patch.dict(sys.modules,{"FreeCAD":NS(Vector=Vec),"Part":NS(Line=type("Line",(),{}))}):
            for edges,expected in (([edge(0,10)],True),([edge(0,5),edge(5,10)],True),
                                   ([edge(0,4),edge(6,10)],False),([edge(0,10,.1)],False)):
                with self.subTest(expected=expected,edges=len(edges)):
                    self.assertEqual(cad_verify_probe.segment_present(NS(Edges=edges),(0,0,0),(10,0,0),.01),expected)

    def test_verify_bounds_are_optimal_without_changing_mvp_measurement(self):
        from tools import cad_spec_probe
        ordinary=NS(XMin=0,XMax=41.1309,YMin=-10.1309,YMax=31,ZMin=-7,ZMax=7)
        tight=NS(XMin=0,XMax=38,YMin=-7,YMax=31,ZMin=-7,ZMax=7)
        shape=NS(BoundBox=ordinary,optimalBoundingBox=Mock(return_value=tight))
        self.assertEqual(cad_verify_probe.bounds(shape),[0,38,-7,31,-7,7])
        shape.optimalBoundingBox.assert_called_once_with(False,False)
        self.assertEqual(cad_spec_probe.bounds(shape),[0,41.1309,-10.1309,31,-7,7])

    def test_normalized_axis_counts_only_an_unambiguous_used_construction(self):
        solid=NS(isSame=lambda other:other is solid)
        shape=NS(isValid=lambda:True,Solids=[solid],isNull=lambda:False)
        for label,count,expected in (("Axis",1,True),("Axis",2,False),("Axis0",2,True),("H_Axis",1,False)):
            with self.subTest(label=label,count=count):
                profile=NS(Name="Profile",TypeId="Sketcher::SketchObject",Shape=shape,GeometryCount=1,
                           Constraints=[NS(Type="Radius",First=0,Value=7)],getDriving=lambda i:True,
                           getConstruction=lambda i:False,Placement=NS(Base=NS(x=0,y=0,z=0)),MapMode="Deactivated",State=[])
                used=NS(Name="AxisSketch",TypeId="Sketcher::SketchObject",Shape=shape,GeometryCount=count,
                        Constraints=[NS(Type="DistanceY",First=i,Value=v) for i,v in enumerate((31,99)[:count])],
                        getDriving=lambda i:True,getConstruction=lambda i:True,
                        Placement=NS(Base=NS(x=0,y=0,z=0)),MapMode="Deactivated",State=[])
                tip=NS(Name="Tip",TypeId="PartDesign::Revolution",Shape=shape,Profile=profile,
                       ReferenceAxis=(used,[label]),PropertiesList=[],State=[])
                body=NS(TypeId="PartDesign::Body",Tip=tip,Group=[profile,used,tip],State=[])
                doc=NS(Objects=[body,profile,used,tip])
                checks=cad_verify_probe.Checks("axis")
                m,_=cad_verify_probe.editability(doc,body,shape,{"editability":{"key_dimensions_mm":[31,14]}},checks,native_shape=shape)
                self.assertEqual(checks.predicates["editability"],expected)
                self.assertNotIn(99,m["driving_dimensions_mm"])

    def test_wilson_completed_only_and_missing_provider_tokens_remain_null(self):
        self.assertIsNone(eval_verify.wilson(1,2,False))
        self.assertAlmostEqual(eval_verify.wilson(2,2)[0],.3423719529,places=7)
        self.assertIsNone(eval_verify.metric([dict(completed=False,passed=False)])["wilson95"])
        totals=eval_verify.eval_mvp.provider_tokens({"calls":[{"usage":[{"values":{"input_tokens":5}}]}]})
        self.assertEqual(totals["input_tokens"],5); self.assertIsNone(totals["output_tokens"])

    def test_f3_manual_control_is_only_the_registered_hole_fault(self):
        folder=BASE/"test/F3"
        tree=ast.parse((folder/"manual-negative.py").read_text(encoding="utf-8"))
        p=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=="_PARAMETERS" for t in node.targets))
        fault=json.loads((folder/"fault.json").read_text(encoding="utf-8"))
        candidate=json.loads((folder/"candidate.json").read_text(encoding="utf-8"))
        self.assertTrue(p.pop("wrong_hole",False))
        self.assertNotIn("omit_finish",p)
        self.assertEqual(p,cad_verify_probe.load_gold(folder/"gold.json")["parameters"])
        self.assertEqual(p["holes"][0]["center_xy"],fault["match"]["center_xy"])
        self.assertEqual(p["holes"][0]["diameter"],fault["match"]["diameter"])
        self.assertEqual(candidate["holes"][0]["diameter"],p["holes"][0]["diameter"]+2)
        self.assertEqual(candidate["holes"][0]["diameter"],fault["set"]["diameter"])
        self.assertEqual(p["finish"],candidate["finish"])

    def test_no_overwrite_and_unknown_gold_predicates_fail(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"same.json"; eval_verify.write_json(path,{"a":1})
            with self.assertRaises(FileExistsError): eval_verify.write_json(path,{"a":2})
            g=json.loads((BASE/"test/Q1/gold.json").read_text(encoding="utf-8")); g["parameters"]["invented_gate"]=1
            invalid=Path(d)/"bad.json"; invalid.write_text(json.dumps(g),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"unsupported_verify_predicate"): cad_verify_probe.load_gold(invalid)


if __name__=="__main__": unittest.main()
