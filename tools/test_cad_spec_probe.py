"""Independent probe contract/gate tests; no CAD or external process calls."""
import copy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from tools import cad_spec_probe as probe

ROOT = Path(__file__).resolve().parents[1]


class Vec:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    def __sub__(self, other):
        return Vec(self.x-other.x, self.y-other.y, self.z-other.z)
    def __mul__(self, n):
        return Vec(self.x*n, self.y*n, self.z*n)


def box(b):
    return NS(**dict(zip(("XMin", "XMax", "YMin", "YMax", "ZMin", "ZMax"), b)))


class ProbeTests(unittest.TestCase):
    def test_world_shape_uses_copy_of_immutable_document_property(self):
        class Immutable:
            @property
            def Placement(self): return "local"
            def copy(self): return NS(Placement=self.Placement)
        native = Immutable()
        obj = NS(Shape=native,getGlobalPlacement=lambda:"world")
        measured = probe.world_shape(obj)
        self.assertEqual(measured.Placement,"world")
        self.assertEqual(native.Placement,"local")

    def test_human_gold_identity_and_nonfinite_rejection(self):
        for name in ("P1", "P2", "P3", "P4", "P5"):
            gold = probe.load_gold(ROOT / ("design/cad-harness-mvp/eval-v1/" + name + ".json"))
            self.assertEqual(hashlib.sha256(gold["description"].encode()).hexdigest(), gold["description_sha256"])
        for name in ("H_RECT_CHAMFER", "H_RECT_FILLET", "H_RECT_STACK", "H_SHAFT"):
            fixture = probe.load_gold(ROOT / ("tools/fixtures/mvp/" + name + ".gold.json"))
            self.assertEqual((fixture["provenance"]["authority"],fixture["provenance"]["confirmed"]),("fixture",False))
        for text in ('{"x":NaN}', '{"x":1,"x":2}'):
            with self.assertRaises(ValueError):
                probe.read_json(text)
        schema = probe.read_json(probe.GOLD_SCHEMA.read_text(encoding="utf-8"))
        bad = copy.deepcopy(gold)
        bad["bbox"][0] = float("inf")
        with self.assertRaises(ValueError):
            probe.gold_check(bad, schema, schema)

    def test_feedback_null_utf8_limits_and_first_failure_per_predicate(self):
        checks = probe.Checks("unit")
        checks.add("hole", "hole.missing", 6, None, False, .01)
        for i in range(70):
            checks.add("hole" if i < 35 else "pocket", "check.%d" % i,
                       "寸" * 200, i, False)
        details = checks.details()
        self.assertIsNone(details["checks"][0]["actual"])
        self.assertTrue(details["truncated"])
        self.assertLessEqual(len(details["checks"]), 32)
        self.assertLessEqual(len(json.dumps(details, ensure_ascii=False).encode()), 8192)
        self.assertEqual(details["checks"][1]["predicate"], "pocket")

    def test_thin_editability_used_dimensions_profile_recompute_and_warning(self):
        solid = NS()
        solid.isSame = lambda other: other is solid
        shape = NS(Solids=[solid], isValid=lambda: True)
        shape.isSame = lambda other: other is shape
        profile = NS(Name="Profile", TypeId="Sketcher::SketchObject", Shape=NS(isNull=lambda: False),
                     MapMode="Deactivated", State=[], GeometryCount=1,
                     Constraints=[NS(Type="Radius", First=0, Value=6)],
                     getDriving=lambda i: True, getConstruction=lambda i: False)
        top = copy.copy(profile)
        top.Name = "TopProfile"
        pad = NS(Name="Pad", TypeId="PartDesign::Pad", Profile=profile, Shape=shape, State=[],
                 PropertiesList=["Length"], Length=NS(Value=30))
        tip = NS(Name="Pocket", TypeId="PartDesign::Pocket", Profile=top, BaseFeature=pad,
                 Shape=shape, State=[], PropertiesList=["Length"], Length=NS(Value=4))
        body = NS(Name="Body", TypeId="PartDesign::Body", Tip=tip, Group=[profile, pad, top, tip], State=[])
        doc = NS(Objects=[body, profile, pad, top, tip])
        gold = {"tolerances":{"linear_mm":.01}, "editability":{"key_dimensions_mm":[12,30,4]}}
        checks = probe.Checks("unit")
        measured, warnings = probe.editability(doc, body, shape, gold, checks)
        self.assertTrue(all(checks.predicates.values()))
        self.assertEqual(warnings, ["flatface_advice"])
        for fault in ("profile", "recompute", "dimension", "native"):
            with self.subTest(fault=fault):
                saved = (tip.Profile, tip.State, body.Tip, gold["editability"]["key_dimensions_mm"])
                if fault == "profile": tip.Profile = None
                if fault == "recompute": tip.State = ["Invalid"]
                if fault == "dimension": gold["editability"]["key_dimensions_mm"] = [99]
                if fault == "native": body.Tip = NS(Name="Opaque",TypeId="Part::Feature",Shape=shape,State=[])
                checks = probe.Checks("unit")
                probe.editability(doc, body, shape, gold, checks)
                self.assertFalse(checks.predicates["editability"])
                tip.Profile, tip.State, body.Tip, gold["editability"]["key_dimensions_mm"] = saved

    def test_actual_cylinder_measurements_reject_blind_wrong_size_and_extra_finish(self):
        class Cylinder: pass
        class Circle: pass
        class Plane: pass
        gold = probe.load_gold(ROOT / "design/cad-harness-mvp/eval-v1/P5.json")
        gold = copy.deepcopy(gold)
        gold["sections"] = []  # This double isolates cylinder/opening measurements.
        modules = {"FreeCAD":NS(Vector=Vec), "Part":NS(Cylinder=Cylinder,Circle=Circle,Plane=Plane)}
        for fault in (None, "blind", "diameter", "finish"):
            faces, edges = [], []
            for i, expected in enumerate(gold["holes"]):
                x, y = expected["center_xy"]
                r = 3 if i == 0 and fault == "diameter" else 2.5
                z0 = 1 if i == 0 and fault == "blind" else 0
                surface = Cylinder()
                surface.Center, surface.Axis, surface.Radius = Vec(x,y,0),Vec(0,0,1),r
                faces.append(NS(Surface=surface, BoundBox=box([x-r,x+r,y-r,y+r,z0,5]),
                                ParameterRange=(0,1,0,1), valueAt=lambda u,v,x=x,y=y,r=r:Vec(x+r,y,3),
                                normalAt=lambda u,v:Vec(-1,0,0)))
                for z in (z0,5):
                    circle = Circle()
                    circle.Center,circle.Axis,circle.Radius = Vec(x,y,z),Vec(0,0,1),r
                    edges.append(NS(Curve=circle,BoundBox=box([x-r,x+r,y-r,y+r,z,z]),
                                    Vertexes=[],Length=2*math.pi*r))
            if fault == "finish":
                surface = Cylinder()
                surface.Center,surface.Axis,surface.Radius = Vec(0,0,0),Vec(1,0,0),1
                faces.append(NS(Surface=surface,BoundBox=box([-1,1,-1,1,0,1]),ParameterRange=(0,1,0,1),
                                valueAt=lambda u,v:Vec(0,1,0),normalAt=lambda u,v:Vec(0,1,0)))
            shape = NS(BoundBox=box(gold["bbox"]),Volume=gold["volume"]["target_mm3"],Area=0,
                       Solids=[1],Faces=faces,Edges=edges,isValid=lambda:True,isNull=lambda:False,
                       isInside=lambda v,t,b:False)
            with self.subTest(fault=fault), patch.dict("sys.modules",modules):
                result = probe.probe(None,NS(Shape=shape),gold,False)
                self.assertEqual(result["probe_pass"], fault is None)
                if fault: self.assertTrue(result["predicate_details"]["checks"])


if __name__ == "__main__":
    unittest.main()
