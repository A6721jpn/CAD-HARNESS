"""Checksum continuation must refuse changed artifacts before any CAD/output."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import sw_m0 as base
from tools.sw_m1_inputs import PRIVATE
from tools.sw_m1_saved import CustodyError,prepare,record


class SavedCustodyTests(unittest.TestCase):
    def test_modified_saved_step_rejected_before_copy_or_COM(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            source=Path(temp)/'source';source.mkdir()
            out=Path(temp)/'out';out.mkdir()
            gold=source/'fake-gold.json';gold.write_text('{}')
            entry=dict(sequence=1,group='dev',route='source',profile='rect_prism',
                gold={},gold_path=str(gold),gold_sha256=base.digest(gold),card={},card_sha256=None)
            base.save_json(source/'job.json',dict(entry,out=str(source)))
            files={}
            for name,key in (('positive.sldprt','native'),('before-reopen.step','before_step'),('reopened.step','reopened_step')):
                path=source/name;path.write_bytes(b'independent fake artifact, no CAD invocation')
                files[key]=record(path)
            base.save_json(source/'com-result.json',dict(files,status='PASS',
                original_native_unchanged=True,final_documents=0,COM_state_unknown=False))
            (source/'reopened.step').write_bytes(b'changed bytes')
            with self.assertRaises(CustodyError):prepare(entry,out,source,False)
            self.assertFalse(any(out.iterdir()))


if __name__=='__main__':unittest.main()
