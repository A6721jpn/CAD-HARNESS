"""Consumer geometry regressions for the planar fallback with real OCCT faces.

Inject only the unavailable offset result: the actual v4 interval/filled-trim
certificate still runs. Synthetic fixtures, no private cards or SolidWorks.
"""
import unittest
from unittest.mock import patch

try:
    import FreeCAD as App
    import Part
except ImportError:
    App=Part=None

from tools.sw_m1_distance import whole_distance


@unittest.skipIf(App is None,'pinned FreeCAD SDK required')
class PlanarWholeBoundaryTests(unittest.TestCase):
    def certificate(self,a,b):
        with patch('tools.sw_m1_distance.boundary_distance',return_value={
            'status':'UNVERIFIED','maximum_mm':.005,'lower_mm':0.,'upper_mm':None,
            'reason':'no_whole_boundary_upper_certificate_at_target'}):
            return whole_distance(a,b,.005)

    def test_small_planar_translation_has_complete_upper_bound(self):
        a=Part.makeBox(40,30,20)
        b=a.copy();b.translate(App.Vector(.001,0,0))
        proof=self.certificate(a,b)
        self.assertEqual(proof['status'],'PASS')
        self.assertEqual(proof['face_pairs'],6)
        self.assertGreaterEqual(proof['upper_mm'],.001)
        self.assertLessEqual(proof['upper_mm'],.005)

    def test_internal_cavity_shift_cannot_hide_behind_equal_outer_bbox_volume(self):
        outer=Part.makeBox(40,30,20)
        cavity=Part.makeBox(10,10,5,App.Vector(10,10,15))
        shifted=cavity.copy();shifted.translate(App.Vector(.01,0,0))
        a=outer.cut(cavity);b=outer.cut(shifted)
        self.assertAlmostEqual(a.Volume,b.Volume,places=8)
        fields=('XMin','XMax','YMin','YMax','ZMin','ZMax')
        self.assertEqual(tuple(getattr(a.BoundBox,k) for k in fields),tuple(getattr(b.BoundBox,k) for k in fields))
        self.assertNotEqual(self.certificate(a,b)['status'],'PASS')


if __name__=='__main__':unittest.main()
