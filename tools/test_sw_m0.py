"""Consumer-visible M0 admission/safety boundaries; actual COM proof is separate."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import sw_m0


class AdmissionTests(unittest.TestCase):
    def test_output_rejects_traversal_sibling_and_protected_worktrees(self):
        for path in (sw_m0.OUTPUTS/'../../foreign',sw_m0.OUTPUTS.parent/'sw-m0-other'/'x',
                     Path('C:/dev/CAD-HARNESS-herdr/reports/sw-m0/x'),
                     Path('C:/dev/CAD-HARNESS-h2/reports/sw-m0/x')):
            with self.subTest(path=path),self.assertRaises(ValueError):
                sw_m0.output_path(path)

    def test_unknown_operation_and_through_pocket_rejected_before_COM(self):
        base=json.loads((sw_m0.FIXTURES/'positive.json').read_text())
        bads=[]
        unknown=json.loads(json.dumps(base));unknown['macro']='not_allowed';bads.append(unknown)
        through=json.loads(json.dumps(base));through['pockets'][0]['depth']=20;bads.append(through)
        hole=json.loads(json.dumps(base));hole['holes']=[{'center_xy':[15,0],'diameter':1,'z':[0,20]}];bads.append(hole)
        with tempfile.TemporaryDirectory(dir=sw_m0.ROOT) as tmp:
            for i,bad in enumerate(bads):
                p=Path(tmp)/('%s.json'%i);p.write_text(json.dumps(bad))
                with self.subTest(i=i),self.assertRaises(ValueError):
                    sw_m0.read_spec(p)


if __name__=='__main__':
    unittest.main()
