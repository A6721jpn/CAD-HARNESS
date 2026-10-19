"""A2 behavior tests; run via run_a2.py with the real FreeCADCmd interpreter."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "freecad-bridge")]
from schemas import ValidationError

try:
    import FreeCAD as App
    import Part
except ImportError:
    App = None

RECORDS = {}


def spec_for(length=100):
    spec = json.loads((ROOT / "fixtures/plate_valid.json").read_text(encoding="utf-8"))
    spec["dimensions"]["L"] = f"{length} mm"
    return spec


@unittest.skipUnless(App is not None, "requires FreeCADCmd; use tests/run_a2.py")
class NativeAssertions(unittest.TestCase):
    def check_document(self, doc, spec):
        from observe import measure, compare_spec
        doc.recompute(None, True, True)
        result = measure(doc.Body.Shape)
        self.assertEqual(compare_spec(result, spec), [])
        dims = {k: float(v[:-3]) for k, v in spec["dimensions"].items()}
        pitch = dims["L"] - 2*dims["e"]
        self.assertAlmostEqual(doc.Params.hole_pitch.Value, pitch)
        self.assertEqual(doc.Params.getContents("B6"), "=plate_length - 2 * edge_offset")
        self.assertEqual(doc.Body.Tip, doc.HolesCut)
        self.assertEqual(doc.Body.Origin.TypeId, "App::Origin")
        self.assertEqual(doc.Body.SemanticId, "plate.main")
        self.assertEqual(doc.BasePad.Profile[0], doc.BaseSketch)
        self.assertEqual(doc.HolesCut.Profile[0], doc.HoleSketch)
        self.assertEqual(doc.HolesCut.Type, "ThroughAll")
        self.assertTrue(doc.HolesCut.Reversed)
        self.assertFalse(doc.BasePad.Reversed)
        for sketch in (doc.BaseSketch, doc.HoleSketch):
            self.assertEqual(sketch.solve(), 0)
            self.assertTrue(sketch.FullyConstrained)
            self.assertEqual(sketch.MapMode, "FlatFace")
            self.assertEqual(sketch.AttachmentSupport[0][0].Name, "XY_Plane")
            self.assertAlmostEqual(sketch.Placement.Base.z, 0)
            self.assertTrue(all(c.Type not in ("Block", "Fixed") for c in sketch.Constraints))
        self.assertEqual({c.Type for c in doc.BaseSketch.Constraints},
                         {"Coincident", "Horizontal", "Vertical", "Symmetric", "Distance"})
        self.assertEqual({c.Type for c in doc.HoleSketch.Constraints},
                         {"Symmetric", "Equal", "DistanceY", "DistanceX", "Diameter"})
        expected_expressions = {
            "BaseSketch": {"Constraints.PlateLength": "Params.plate_length", "Constraints.PlateWidth": "Params.plate_width"},
            "BasePad": {"Length": "Params.plate_thickness"},
            "HoleSketch": {"Constraints.LeftCenterX": "-Params.hole_pitch / 2", "Constraints.HoleDiameter": "Params.hole_diameter"},
            "MountLeft": {"Placement.Base.x": "-Params.hole_pitch / 2"},
            "MountRight": {"Placement.Base.x": "Params.hole_pitch / 2"},
        }
        for name, expressions in expected_expressions.items():
            obj = doc.getObject(name)
            actual = {path.lstrip("."): value for path, value in obj.ExpressionEngine}
            for path, expression in expressions.items():
                self.assertIn(path, actual)
                self.assertEqual(actual[path], expression)
        for name, x in (("MountLeft", -pitch/2), ("MountRight", pitch/2)):
            mount = doc.getObject(name)
            self.assertEqual(mount.TypeId, "PartDesign::CoordinateSystem")
            self.assertAlmostEqual(mount.Placement.Base.x, x)
            self.assertAlmostEqual(mount.Placement.Base.y, 0)
            self.assertAlmostEqual(mount.Placement.Base.z, 0)
        states = {obj.Name: list(obj.State) for obj in doc.Objects}
        for obj in doc.Objects:
            self.assertNotIn("Invalid", obj.State, obj.Name)
            self.assertNotIn("Error", obj.State, obj.Name)
        result["history"] = {"expressions": {name: list(doc.getObject(name).ExpressionEngine)
                                             for name in expected_expressions},
                             "fully_constrained": [doc.BaseSketch.FullyConstrained, doc.HoleSketch.FullyConstrained],
                             "states": states,
                             "pocket_type": doc.HolesCut.Type,
                             "pocket_reversed": doc.HolesCut.Reversed,
                             "mounts_mm": [[doc.getObject(n).Placement.Base.x, doc.getObject(n).Placement.Base.y,
                                            doc.getObject(n).Placement.Base.z] for n in ("MountLeft", "MountRight")]}
        return result


class BuildTests(NativeAssertions):
    def test_supported_range_endpoints(self):
        from compiler.plate import compile_plate
        measurements = []
        for dimensions in ({"L": 80, "W": 30, "T": 4, "D": 4, "e": 12},
                           {"L": 180, "W": 80, "T": 16, "D": 12, "e": 25}):
            spec = spec_for()
            spec["dimensions"] = {key: f"{value} mm" for key, value in dimensions.items()}
            doc = compile_plate(spec, "RangeEndpoint")
            try:
                measurements.append(self.check_document(doc, spec))
            finally:
                App.closeDocument(doc.Name)
        RECORDS["supported_range_endpoints"] = measurements

    def test_three_lengths_and_live_expressions(self):
        from compiler.plate import compile_plate
        out = Path(os.environ["A2_OUTPUT"])
        doc = compile_plate(spec_for())
        try:
            for length in (100, 140, 160):
                doc.Params.set("B1", f"{length} mm")
                spec = spec_for(length)
                measured = self.check_document(doc, spec)
                doc.saveAs(str(out / f"plate-L{length}.FCStd"))
                RECORDS[f"L{length}"] = measured
                # Also exercise the compiler boundary directly for each input.
                direct = compile_plate(spec, f"Direct{length}")
                try:
                    other = self.check_document(direct, spec)
                    self.assertAlmostEqual(other["volume_mm3"], measured["volume_mm3"])
                finally:
                    App.closeDocument(direct.Name)
        finally:
            App.closeDocument(doc.Name)

    def test_reject_invalid_before_document_creation(self):
        from compiler.plate import compile_plate
        rejected = []
        limits = {"L": (80, 180), "W": (30, 80), "T": (4, 16), "D": (4, 12), "e": (12, 25)}
        cases = []
        for key, (low, high) in limits.items():
            for value in (low - 0.001, high + 0.001):
                cases.append((key, f"{value} mm"))
        cases += [("e", "3 mm"), ("e", "2 mm"), ("D", "40 mm"), ("e", "47 mm"), ("L", "100 cm")]
        for key, value in cases:
            spec = spec_for()
            spec["dimensions"][key] = value
            before = set(App.listDocuments())
            with self.assertRaises(ValidationError) as caught:
                compile_plate(spec)
            self.assertEqual(set(App.listDocuments()), before)
            rejected.append({"dimension": key, "value": value, "reason": str(caught.exception)})
        RECORDS["rejected"] = rejected

    def test_observer_detects_bad_geometry(self):
        from observe import measure, compare_spec
        block = Part.makeBox(100, 40, 8, App.Vector(-50, -20, 0))
        through = Part.makeCylinder(3, 8, App.Vector(-35, 0, 0))
        blind = Part.makeCylinder(3, 4, App.Vector(35, 0, 4))
        bad = block.cut(through).cut(blind)
        result = measure(bad)
        self.assertFalse(result["through"])
        self.assertTrue(compare_spec(result, spec_for()))
        self.assertEqual(result["holes"][1]["end_openings"], [False, True])
        filled = measure(block)
        self.assertEqual(filled["hole_count"], 0)
        self.assertFalse(filled["through"])
        self.assertTrue(compare_spec(filled, spec_for()))
        RECORDS["negative_measurements"] = {"blind": result, "filled": filled}


class ReopenTests(NativeAssertions):
    def test_reopen_recompute_and_edit(self):
        from observe import measure
        self.assertNotIn("compiler.plate", sys.modules)
        length = int(os.environ["A2_LENGTH"])
        doc = App.openDocument(str(Path(os.environ["A2_OUTPUT"]) / f"plate-L{length}.FCStd"))
        try:
            spec = spec_for(length)
            RECORDS["reopened"] = self.check_document(doc, spec)
            built = json.loads((Path(os.environ["A2_OUTPUT"]) / "build.json").read_text(encoding="utf-8"))
            self.assertNotEqual(built["pid"], os.getpid())
            # All measured B-Rep fields must survive the separate process.
            for key, value in measure(doc.Body.Shape).items():
                self.assertEqual(value, built["measurements"][f"L{length}"][key])
            # All five independent dimensions must remain live after reopening.
            edited = copy.deepcopy(spec)
            edited["dimensions"] = {"L": "150 mm", "W": "50 mm", "T": "10 mm", "D": "8 mm", "e": "20 mm"}
            for key, cell in {"L": "B1", "W": "B2", "T": "B3", "D": "B4", "e": "B5"}.items():
                doc.Params.set(cell, edited["dimensions"][key])
            RECORDS["edited_after_reopen"] = self.check_document(doc, edited)
        finally:
            App.closeDocument(doc.Name)
