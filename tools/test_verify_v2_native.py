"""Native API, saved v1 reproduction and construction decoys; no model calls."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import cad_verify_v2_probe as probe


@unittest.skipUnless("FreeCAD" in sys.modules, "requires the fixed FreeCAD 1.1.4 headless host")
class NativeV2(unittest.TestCase):
    def test_saved_v1_v5_pcd_sixty_is_reachable_after_reopen(self):
        import FreeCAD as App
        for round_number in (1, 2):
            path = ROOT / ("reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r%d-mvp1/a1-mvp1/model.FCStd" % round_number)
            doc = App.openDocument(str(path))
            try:
                doc.recompute()
                body = next(o for o in doc.Objects if o.TypeId == "PartDesign::Body")
                gold = probe.load_gold(ROOT / "design/cad-harness-verify/test/V5/gold.json")
                result = probe.probe(doc, body, gold)
                self.assertTrue(result["geometry_ok"], result["predicate_details"])
                self.assertTrue(result["editability_ok"], result["predicate_details"])
                self.assertIn(60, result["measurements"]["editability"]["driving_dimensions_mm"])
                proof = result["measurements"]["editability"]["dimension_evidence"]
                self.assertTrue(any(p.get("value_mm") == 60 and any(len(path) > 1 for path in p.get("paths", [])) for p in proof))
            finally:
                App.closeDocument(doc.Name)

    def test_native_construction_chain_and_decoys(self):
        import FreeCAD as App
        import Part
        import Sketcher
        for mode, wanted in (("chain", True), ("isolated", False), ("origin", False), ("reference", False), ("inactive", False)):
            doc = App.newDocument("Graph"+mode)
            try:
                s = doc.addObject("Sketcher::SketchObject", "Sketch")
                s.addGeometry(Part.Circle(App.Vector(30, 0, 0), App.Vector(0, 0, 1), 2), False)
                s.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 30), True)
                s.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(30, 0, 0)), True)
                index = s.addConstraint(Sketcher.Constraint("Diameter", 1, 60))
                s.addConstraint(Sketcher.Constraint("PointOnObject", 2, 2, 1))
                if mode in ("chain", "reference", "inactive"):
                    s.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 2, 2))
                elif mode == "origin":
                    s.addConstraint(Sketcher.Constraint("PointOnObject", 0, 3, -1))
                    s.addConstraint(Sketcher.Constraint("PointOnObject", 1, 3, -1))
                if mode == "reference": s.setDriving(index, False)
                if mode == "inactive": s.setActive(index, False)
                doc.recompute()
                paths = probe.reachable(s, {0: [{"geometry": 0}]})
                values = [c.Value for i, c in enumerate(s.Constraints) if c.Type in probe.DIMENSIONS
                          and s.getDriving(i) and s.getActive(i) and c.First in paths]
                self.assertEqual(60 in values, wanted)
                if wanted: self.assertEqual([p["geometry"] for p in paths[1]], [0, 2, 1])
            finally:
                App.closeDocument(doc.Name)

    def test_partial_selection_keeps_only_selected_real_geometry(self):
        import FreeCAD as App
        import Part
        doc = App.newDocument("Selection")
        try:
            s = doc.addObject("Sketcher::SketchObject", "Sketch")
            s.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 3), False)
            s.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 9), True)
            s.addGeometry(Part.Circle(App.Vector(15, 0, 0), App.Vector(0, 0, 1), 4), False)
            s.Placement.Base = App.Vector(10, 3, 0)
            doc.recompute()
            self.assertEqual(probe.selected_geometry(s, ("Edge1",)), [0])
            self.assertEqual(probe.selected_geometry(s, ("Edge2",)), [2])
        finally:
            App.closeDocument(doc.Name)


if __name__ == "__main__" or "FreeCAD" in sys.modules and not __package__:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeV2)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("VERIFY_V2_NATIVE_OK="+str(result.wasSuccessful()))
