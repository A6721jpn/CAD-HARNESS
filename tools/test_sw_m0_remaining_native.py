"""Whole-boundary consumer regressions; discovery never starts CAD or SW."""
import importlib.util
import os
import unittest

from tools.sw_m0_distance import boundary_distance

NATIVE=os.environ.get('CAD_SW_M0_NATIVE')=='1' and importlib.util.find_spec('FreeCAD') is not None


@unittest.skipUnless(NATIVE,'set CAD_SW_M0_NATIVE=1 under pinned FreeCAD Python')
class BoundaryRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global App,Part
        import FreeCAD as App
        import Part
        if list(App.Version())[:3]!=['1','1','4']:
            raise RuntimeError('pinned_FreeCAD_1_1_4_required')

    def test_small_shift_has_entire_boundary_upper_below_target(self):
        a=Part.makeBox(4,4,4)
        b=a.copy();b.translate(App.Vector(.002,0,0))
        result=boundary_distance(a,b,.005,refinements=3)
        self.assertEqual(result['status'],'PASS',result)
        self.assertLessEqual(result['upper_mm'],.005)
        self.assertGreaterEqual(result['upper_mm'],.002)

    def test_intersection_minimum_zero_does_not_mask_excessive_shift(self):
        a=Part.makeBox(4,4,4)
        b=a.copy();b.translate(App.Vector(.01,0,0))
        self.assertEqual(a.distToShape(b)[0],0)
        result=boundary_distance(a,b,.005)
        self.assertEqual(result['status'],'FAIL',result)
        self.assertGreater(result['lower_mm'],.005)

    def test_new_internal_void_is_not_hidden_by_equal_outer_surface(self):
        a=Part.makeBox(4,4,4)
        b=a.cut(Part.makeBox(1,1,1,App.Vector(1.5,1.5,1.5)))
        result=boundary_distance(a,b,.005)
        self.assertEqual(result['status'],'FAIL',result)
        self.assertGreater(result['lower_mm'],1)


if __name__=='__main__':
    unittest.main()
