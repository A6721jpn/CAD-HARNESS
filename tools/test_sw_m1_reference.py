"""Actual independent public legacy geometry, not private holdout data."""
import unittest
from pathlib import Path
try:
    import FreeCAD
except ImportError:
    FreeCAD=None


@unittest.skipIf(FreeCAD is None,'pinned FreeCAD SDK required')
class LegacyReferenceTests(unittest.TestCase):
    def test_through_annotation_keeps_strict_reference_geometry_compatible(self):
        from tools.cad_spec_probe import load_gold
        from tools.sw_m1_judge import independent_reference,original_geometry
        path=Path(__file__).resolve().parents[1]/'design/cad-harness-mvp/eval-v1/P2.json'
        gold=load_gold(path)
        shape=independent_reference(gold)
        result=original_geometry(shape,gold)
        self.assertTrue(result['passed'])


if __name__=='__main__':unittest.main()
