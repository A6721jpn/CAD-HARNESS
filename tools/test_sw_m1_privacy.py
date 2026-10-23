"""Consumer-visible privacy boundary: no gold under public report fields."""
from pathlib import Path
import tempfile
import unittest

from tools.sw_m1 import ROOT,publish


class PublicProjectionPrivacy(unittest.TestCase):
    def test_extra_gold_field_never_creates_public_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            dest=Path(tmp)/'public.json'
            with self.assertRaises(RuntimeError):
                publish(dest,[{'sequence':1,'gold':{'secret_dimension':123.456}}])
            self.assertFalse(dest.exists())

    def test_nested_gold_in_allowed_status_field_never_creates_public_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            dest=Path(tmp)/'public.json'
            with self.assertRaises(RuntimeError):
                publish(dest,[{'sequence':1,'reason':{'secret_dimension':123.456}}])
            self.assertFalse(dest.exists())


if __name__=='__main__':
    unittest.main()
