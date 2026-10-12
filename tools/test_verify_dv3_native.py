"""DV3 fixture sanity from frozen description only; run with the fixed FreeCADcmd."""
import json
import math
from pathlib import Path
import re
import runpy
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def setUpModule():
    if "FreeCAD" in sys.modules:
        global _temps
        from tools.test_support import start_tempdirs
        _temps=start_tempdirs()


def tearDownModule():
    if "FreeCAD" in sys.modules:
        from tools.test_support import stop_tempdirs
        stop_tempdirs(_temps)


@unittest.skipUnless("FreeCAD" in sys.modules,"requires the authorized headless FreeCADcmd")
class DV3DescriptionSanity(unittest.TestCase):
    def test_reopened_pipe_sections_measure_circular_polylines(self):
        import FreeCAD as App
        import Part
        from tools import cad_verify_probe, cad_spec_probe
        folder=ROOT/"design/cad-harness-verify/dev/DV3"
        gold=cad_verify_probe.load_gold(folder/"gold.json")
        doc=None
        try:
            with tempfile.TemporaryDirectory() as directory:
                doc=App.newDocument("DV3ReopenedSectionSanity")
                body=runpy.run_path(str(folder/"positive.py"))["build"](doc)
                doc.recompute()
                path=Path(directory)/"model.FCStd"
                doc.saveAs(str(path))
                App.closeDocument(doc.Name)
                doc=None
                doc=App.openDocument(str(path))
                doc.recompute()
                body=next(o for o in doc.Objects if o.TypeId=="PartDesign::Body")
                shape=cad_spec_probe.world_shape(body.Tip)
                theta=math.pi/4
                center=[31*math.sin(theta),31*(1-math.cos(theta)),0]
                normal=[math.cos(theta),math.sin(theta),0]
                cut=cad_verify_probe.plane_cut(shape,center,normal)
                self.assertTrue(any(isinstance(e.Curve,Part.BSplineCurve) and e.Curve.Degree==1 for e in cut.Edges))
                measured=cad_verify_probe.probe(doc,body,gold)
                self.assertTrue(measured["geometry_ok"],measured["predicate_details"])
                self.assertTrue(measured["editability_ok"],measured["predicate_details"])
                # A section loop must still have the requested size and plane.
                outer=max(cut.Edges,key=lambda e:e.Length)
                self.assertFalse(cad_verify_probe.circular_edge(outer,center,normal,8))
                self.assertFalse(cad_verify_probe.circular_edge(outer,center,[0,0,1],7))
                print("DV3_REOPENED_SECTION",json.dumps({"types":[type(e.Curve).__name__ for e in cut.Edges],
                      "geometry_ok":measured["geometry_ok"],"editability_ok":measured["editability_ok"]}))
                App.closeDocument(doc.Name)
                doc=None
        finally:
            if doc:App.closeDocument(doc.Name)
        self.assertFalse(App.listDocuments())

    def test_verify_optimal_bounds_match_gold_and_ordinary_overestimates(self):
        import FreeCAD as App
        from tools import cad_verify_probe, cad_spec_probe
        folder=ROOT/"design/cad-harness-verify/dev/DV3"
        gold=cad_verify_probe.load_gold(folder/"gold.json")
        self.assertEqual(App.GuiUp,0)
        self.assertFalse(App.listDocuments())
        doc=App.newDocument("DV3VerifyBoundsSanity")
        try:
            body=runpy.run_path(str(folder/"positive.py"))["build"](doc)
            doc.recompute()
            shape=cad_spec_probe.world_shape(body.Tip)
            ordinary=cad_spec_probe.bounds(shape)
            actual=cad_verify_probe.bounds(shape)
            self.assertTrue(cad_spec_probe.same_bounds(actual,gold["bbox"],.01))
            self.assertGreater(ordinary[1]-gold["bbox"][1],.01)
            self.assertLess(ordinary[2]-gold["bbox"][2],-.01)
            self.assertEqual(cad_spec_probe.bounds(shape),ordinary)
            print("DV3_VERIFY_OPTIMAL_GOLD",json.dumps({"gold":gold["bbox"],"optimal":actual,"ordinary":ordinary}))
        finally:
            App.closeDocument(doc.Name)
        self.assertFalse(App.listDocuments())

    def test_native_fixture_matches_description_without_gold(self):
        import FreeCAD as App
        import Part
        folder=ROOT/"design/cad-harness-verify/dev/DV3"
        text=(folder/"description.txt").read_text(encoding="utf-8")
        match=re.fullmatch(r"中心線R([\d.]+)でXY上を直角に曲がる外径([\d.]+)、内径([\d.]+)の管。始点\(0,0,0\)、接線\+X、終点\(([\d.]+),([\d.]+),0\)、接線\+Y。両端開口。単位mm。",text)
        self.assertIsNotNone(match)
        radius,diameter,bore,end_x,end_y=map(float,match.groups())
        self.assertEqual((end_x,end_y),(radius,radius))
        outer,inner=diameter/2,bore/2
        expected=[0,radius+outer,-outer,radius,-outer,outer]
        self.assertEqual(App.GuiUp,0)
        self.assertFalse(App.listDocuments())
        doc=App.newDocument("DV3DescriptionSanity")
        try:
            body=runpy.run_path(str(folder/"positive.py"))["build"](doc)
            doc.recompute()
            shape=body.Tip.Shape.copy()
            shape.Placement=body.Tip.getGlobalPlacement()
            self.assertTrue(shape.isValid())
            self.assertEqual(len(shape.Solids),1)
            bb=shape.optimalBoundingBox()
            actual=[bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax]
            for e,a in zip(expected,actual): self.assertAlmostEqual(e,a,delta=1e-6)
            self.assertAlmostEqual(shape.Volume/(math.pi*(outer**2-inner**2)*math.pi*radius/2),1,delta=1e-6)
            caps=[f for f in shape.Faces if isinstance(f.Surface,Part.Plane)]
            self.assertEqual(len(caps),2)
            for center,normal in (((0,0,0),(-1,0,0)),((end_x,end_y,0),(0,1,0))):
                face=min(caps,key=lambda f:(f.CenterOfMass-App.Vector(*center)).Length)
                self.assertLess((face.CenterOfMass-App.Vector(*center)).Length,1e-6)
                u0,u1,v0,v1=face.ParameterRange
                self.assertLess((face.normalAt((u0+u1)/2,(v0+v1)/2)-App.Vector(*normal)).Length,1e-6)
                radii=sorted(e.Curve.Radius for e in face.Edges if isinstance(e.Curve,Part.Circle))
                self.assertEqual(len(radii),2)
                for e,a in zip((inner,outer),radii): self.assertAlmostEqual(e,a,delta=1e-6)
                self.assertAlmostEqual(face.Area/(math.pi*(outer**2-inner**2)),1,delta=1e-6)
            print("DV3_DESCRIPTION_BOUNDS",json.dumps({"expected":expected,"optimal":actual,
                  "ordinary":[shape.BoundBox.XMin,shape.BoundBox.XMax,shape.BoundBox.YMin,
                              shape.BoundBox.YMax,shape.BoundBox.ZMin,shape.BoundBox.ZMax]}))
        finally:
            App.closeDocument(doc.Name)
        self.assertFalse(App.listDocuments())


if "FreeCAD" in sys.modules:
    setUpModule()
    try:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DV3DescriptionSanity))
    finally:
        tearDownModule()
    print("DV3_NATIVE_SANITY_RESULT",json.dumps({"passed":result.wasSuccessful(),"tests":result.testsRun,
                                               "documents_closed":not sys.modules["FreeCAD"].listDocuments()}))
