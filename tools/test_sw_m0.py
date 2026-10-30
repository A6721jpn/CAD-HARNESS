"""Consumer-visible M0 admission/safety boundaries; actual COM proof is separate."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import sys
from types import SimpleNamespace
from unittest.mock import Mock,patch

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


class PinnedAttachment(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,{'CAD_HARNESS_SW_PID':'53084'})
        self.environment.start();self.addCleanup(self.environment.stop)
        self.other=Mock();self.other.GetDisplayName.return_value='SolidWorks_PID_10800'
        self.target=Mock();self.target.GetDisplayName.return_value='SolidWorks_PID_53084'
        self.rot=Mock();self.rot.EnumRunning.side_effect=lambda:iter((self.other,self.target))
        self.app=Mock();self.app.GetProcessID.return_value=53084
        self.dispatch=Mock(return_value=self.app)
        pc=SimpleNamespace(GetRunningObjectTable=lambda:self.rot,CreateBindCtx=lambda _:object(),IID_IDispatch=object())
        dynamic=SimpleNamespace(Dispatch=self.dispatch)
        self.modules=patch.dict(sys.modules,{'pythoncom':pc,'win32com.client.dynamic':dynamic})
        self.modules.start();self.addCleanup(self.modules.stop)

    def test_other_registered_instance_is_never_bound(self):
        self.assertIs(sw_m0.attach_existing(),self.app)
        self.rot.GetObject.assert_called_once_with(self.target)

    def test_missing_authorized_instance_does_not_use_default_or_other_instance(self):
        self.rot.EnumRunning.side_effect=lambda:iter((self.other,))
        with self.assertRaisesRegex(RuntimeError,'PID_not_registered'):sw_m0.attach_existing()
        self.rot.GetObject.assert_not_called();self.dispatch.assert_not_called()

    def test_wrong_pid_is_refused_before_any_document_query(self):
        self.app.GetProcessID.return_value=10800
        with self.assertRaisesRegex(RuntimeError,'PID_mismatch'):sw_m0.attach_existing()
        self.app.GetDocumentCount.assert_not_called()

    def test_explicit_new_pid_binds_only_its_registered_instance(self):
        self.target.GetDisplayName.return_value='SolidWorks_PID_70316'
        self.app.GetProcessID.return_value=70316
        with patch.dict(os.environ,{'CAD_HARNESS_SW_PID':'70316'}):
            self.assertIs(sw_m0.attach_existing(),self.app)
        self.rot.GetObject.assert_called_once_with(self.target)

    def test_invalid_explicit_pid_never_binds_an_application(self):
        for value in ('','0','-1','nan','53084x','١','4294967296'):
            with self.subTest(value=value),patch.dict(os.environ,{'CAD_HARNESS_SW_PID':value}):
                with self.assertRaisesRegex(RuntimeError,'invalid_authorized_SW_PID'):sw_m0.attach_existing()
        self.rot.GetObject.assert_not_called()


class COMFailureSafety(unittest.TestCase):
    def test_rpc_call_failed_blocks_further_COM_and_document_cleanup(self):
        class RPCError(Exception):
            hresult=-2147023170
        session=object.__new__(sw_m0.Session)
        session.pc=SimpleNamespace(com_error=RPCError)
        session.events=io.StringIO()
        session.uncertain=False
        session.owned=Mock()
        session.title='HarnessOwned'
        session.app=Mock()
        feature_manager=Mock()
        feature_manager.FeatureExtrusion3.side_effect=RPCError()
        with self.assertRaises(RPCError):
            session.call(feature_manager,'FeatureExtrusion3')
        with self.assertRaisesRegex(RuntimeError,'COM_state_unknown_no_further_calls'):
            session.call(session.app,'GetDocumentCount')
        session.close()
        session.app.GetDocumentCount.assert_not_called()
        session.app.CloseDoc.assert_not_called()


if __name__=='__main__':
    unittest.main()
