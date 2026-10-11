"""Compiler contracts use held-out typed dimensions only, never evaluation gold."""
import ast
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import cad_spec
from tools.fixtures.cad_mvp_build import HELD_OUT, held_out_specs


class CadSpecTests(unittest.TestCase):
    def test_held_out_families_compile_without_evaluation_access(self):
        real = Path.read_text
        def read(path, *args, **kwargs):
            if "eval-v1" in str(path) or "description" in path.name.lower():
                raise AssertionError("compiler test read evaluation input")
            return real(path, *args, **kwargs)
        with patch.object(Path, "read_text", read):
            specs = held_out_specs()
            seen = set()
            for name, spec in specs.items():
                with self.subTest(name=name):
                    source = cad_spec.compile_spec(spec)
                    self.assertEqual(source, cad_spec.compile_spec(copy.deepcopy(spec)))
                    tree = ast.parse(source)
                    self.assertEqual(sum(isinstance(n, ast.FunctionDef) and n.name == "build" for n in tree.body), 1)
                    changed = copy.deepcopy(spec)
                    if spec["family"] == "stepped_shaft":
                        changed["steps"][0]["diameter"] += 0.3
                    else:
                        changed["regions"][0]["bounds"][0] -= 0.3
                    self.assertNotEqual(source, cad_spec.compile_spec(changed))
                    seen.update(HELD_OUT[name])
            self.assertEqual(seen, set(cad_spec.RECIPE_FAMILIES))

    def test_schema_rejects_unsupported_nonfinite_and_intersecting_inputs(self):
        spec = held_out_specs()["H_RECT_CHAMFER"]
        for field, value in (("expected_volume", 1), ("case_id", "answer"), ("family", "loft")):
            bad = copy.deepcopy(spec)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                cad_spec.validate_spec(bad)
        for value in (False, float("nan"), float("inf")):
            bad = copy.deepcopy(spec)
            bad["holes"][0]["diameter"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                cad_spec.validate_spec(bad)
        bad = copy.deepcopy(spec)
        bad["holes"][1] = copy.deepcopy(bad["holes"][0])
        with self.assertRaisesRegex(ValueError, "overlapping_holes"):
            cad_spec.validate_spec(bad)
        with self.assertRaisesRegex(ValueError, "duplicate_key"):
            cad_spec.read_json('{"family":"a","family":"b"}')
        with self.assertRaises(ValueError):
            cad_spec.read_json('{"x": NaN}')

    def test_cli_units_normalize_without_a_model(self):
        spec = {"schema": cad_spec.VERSION, "family": "rect_prism", "units": "cm",
                "regions": [{"bounds": [-2.7, 2.7, -1.1, 1.1, 0, 0.8]}]}
        actual = cad_spec.validate_spec(spec)
        self.assertEqual(actual["units"], "mm")
        self.assertEqual(actual["regions"][0]["bounds"], [-27, 27, -11, 11, 0, 8])
        self.assertEqual(actual["pockets"], [])


if __name__ == "__main__":
    unittest.main()
