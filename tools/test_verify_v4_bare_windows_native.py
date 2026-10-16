"""Opt-in, independent DEV smoke; no model/provider/private fixture is involved.

Windows shell command after integration:
  cmd /d /c "set CAD_BARE_DEV_SMOKE=1&& python -B -m unittest tools.test_verify_v4_bare_windows_native"
Optional CAD_BARE_SMOKE_RECEIPT selects a NEW JSON receipt path. Failure is a
blocked OS prerequisite, not permission to fall back to a host subprocess.
Receipts are published only after boundary, ownership and tempfile cleanup.
Fresh scratch must already be owned by the child user; ownership is verified,
never reassigned, because even a redundant owner update can alter OWNER_RIGHTS.
"""
import base64
import ctypes as C
from ctypes import wintypes as W
from contextlib import ExitStack, contextmanager
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
import time
from unittest.mock import patch

from tools import cad_verify_v4_bare_windows as isolation
from tools import cad_verify_v4_bare as bare


def security_descriptor(path, information=0x17):
    """Capture both rendered ACLs and their raw inheritance/control flags."""
    a, k = C.WinDLL('advapi32'), C.WinDLL('kernel32')
    descriptor, text, size = C.c_void_p(), W.LPWSTR(), W.ULONG()
    a.GetNamedSecurityInfoW.argtypes = [W.LPWSTR, C.c_int, W.DWORD, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)]
    a.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [C.c_void_p, W.DWORD, W.DWORD, C.POINTER(W.LPWSTR), C.POINTER(W.ULONG)]
    a.GetSecurityDescriptorControl.argtypes = [C.c_void_p, C.POINTER(W.WORD), C.POINTER(W.DWORD)]
    k.LocalFree.argtypes = [C.c_void_p]
    if a.GetNamedSecurityInfoW(str(path), 1, information, None, None, None, None, C.byref(descriptor)):
        raise RuntimeError('DEV_acl_snapshot_denied')
    try:
        control, revision = W.WORD(), W.DWORD()
        if not a.GetSecurityDescriptorControl(descriptor, C.byref(control), C.byref(revision)):
            raise RuntimeError('DEV_acl_control_snapshot_denied')
        if not a.ConvertSecurityDescriptorToStringSecurityDescriptorW(descriptor, 1, information, C.byref(text), C.byref(size)):
            raise RuntimeError('DEV_acl_render_denied')
        try:
            return text.value, control.value
        finally:
            k.LocalFree(text)
    finally:
        k.LocalFree(descriptor)


@contextmanager
def current_user_owned_scratch(path):
    """Verify the real owner worst case without changing the scratch security."""
    a, k = C.WinDLL('advapi32', use_last_error=True), C.WinDLL('kernel32', use_last_error=True)
    token, size, descriptor, owner = C.c_void_p(), W.DWORD(), C.c_void_p(), C.c_void_p()
    k.GetCurrentProcess.restype = C.c_void_p
    k.CloseHandle.argtypes = [C.c_void_p]
    k.LocalFree.argtypes = [C.c_void_p]
    a.OpenProcessToken.argtypes = [C.c_void_p, W.DWORD, C.POINTER(C.c_void_p)]
    a.GetTokenInformation.argtypes = [C.c_void_p, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)]
    a.GetNamedSecurityInfoW.argtypes = [W.LPWSTR, C.c_int, W.DWORD, C.POINTER(C.c_void_p), C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)]
    a.EqualSid.argtypes = [C.c_void_p, C.c_void_p]
    before = security_descriptor(path)
    status = a.GetNamedSecurityInfoW(str(path), 1, 1, C.byref(owner), None, None, None, C.byref(descriptor))
    if status:
        raise RuntimeError('DEV_scratch_owner_snapshot_denied:' + str(status))
    try:
        if not a.OpenProcessToken(k.GetCurrentProcess(), 8, C.byref(token)):
            raise RuntimeError('DEV_current_user_token_denied')
        try:
            a.GetTokenInformation(token, 1, None, 0, C.byref(size))
            if not size.value:
                raise RuntimeError('DEV_current_user_sid_size')
            data = C.create_string_buffer(size.value)
            if not a.GetTokenInformation(token, 1, data, size.value, C.byref(size)):
                raise RuntimeError('DEV_current_user_sid_denied')
            if not a.EqualSid(owner, C.cast(data, C.POINTER(C.c_void_p))[0]):
                raise RuntimeError('DEV_scratch_not_owned_by_current_user')
        finally:
            k.CloseHandle(token)
    finally:
        k.LocalFree(descriptor)
    # The fresh tempfile already satisfies the required child-user ownership.
    # Do not invoke an owner setter: OWNER-only SetFileSecurityW can discard the
    # effective inherited OWNER_RIGHTS ACE, revoking supervisor access before
    # a path-based rollback can reopen the object. No elevated repair is needed
    # when the native owner is verified instead of redundantly assigned.
    try:
        if security_descriptor(path) != before:
            raise RuntimeError('DEV_owner_verification_changed_security')
        yield
    finally:
        if security_descriptor(path) != before:
            raise RuntimeError('DEV_owned_scratch_security_not_restored')


class NativeTrace:
    """No provider API: only actual native boundary state, deadline and receipts."""
    wall = staticmethod(time.monotonic)

    def __init__(self, boundary, deadline):
        self.boundary, self.deadline, self.events = boundary, deadline, []

    def check(self):
        if not self.boundary.entered:
            raise isolation.BoundaryUnavailable('DEV_boundary_not_entered')
        if self.wall() >= self.deadline:
            raise TimeoutError('DEV_native_deadline')

    def event(self, kind, **fields):
        self.events.append((kind, fields))


@unittest.skipUnless(os.name == 'nt' and os.environ.get('CAD_BARE_DEV_SMOKE') == '1',
                     'requires explicit independent DEV Windows LPAC smoke opt-in')
class NativeBareIsolation(unittest.TestCase):
    def test_shell_handover_requires_lpac_not_plain_appcontainer(self):
        with tempfile.TemporaryDirectory(prefix='bare-private-launch-dev-') as temporary:
            root = Path(temporary)
            source = root / 'MOCK-SDK-SOURCE'
            (source / 'bin').mkdir(parents=True)
            (source / 'bin/python.exe').write_bytes(b'MOCK ACL fixture, never executable')
            scratch = isolation.create_scratch(root / 'scratch')
            (scratch / 'inputs').mkdir()
            original = scratch / 'inputs/original.bin'
            payload = b'independent actual shell fixture\r\n'
            original.write_bytes(payload)
            with patch.object(isolation, 'PINNED_PYTHON', source / 'bin/python.exe'):
                staged = isolation.stage_runtime(source, root / 'runtime')
                with isolation.WindowsBoundary(scratch, Path(staged['root']), read_files=[original],
                        runtime_inventory=staged['inventory'], staging_proof=staged['proof']) as boundary:
                    command = [str(Path(os.environ['SystemRoot']) / 'System32/cmd.exe'), '/d', '/s', '/c',
                               'copy /b inputs\\original.bin produced.bin >nul && ren produced.bin handover.bin']
                    actual_update = boundary.k.UpdateProcThreadAttribute
                    ordinary = W.DWORD()
                    def plain_appcontainer(attributes, flags, key, value, size, previous, returned):
                        if key == 0x2000f:
                            value, size = C.byref(ordinary), C.sizeof(ordinary)
                        return actual_update(attributes, flags, key, value, size, previous, returned)
                    boundary.k.UpdateProcThreadAttribute = plain_appcontainer
                    with self.assertRaises(isolation.BoundaryUnavailable) as rejected:
                        boundary.run(command, stdout=root/'ordinary.stdout', stderr=root/'ordinary.stderr', timeout=10)
                    self.assertTrue(str(rejected.exception).startswith('child_lpac_access_semantics:'))
                    self.assertFalse((scratch / 'handover.bin').exists())
                    self.assertFalse(boundary.last_receipt['lpac_token_verified'])
                    self.assertEqual(boundary.last_receipt['cleanup_status'], 'exited')
                    boundary.k.UpdateProcThreadAttribute = actual_update
                    receipt = boundary.run(command, stdout=root/'lpac.stdout', stderr=root/'lpac.stderr', timeout=10)
                    self.assertEqual(receipt['returncode'], 0)
                    self.assertEqual((scratch / 'handover.bin').read_bytes(), payload)
                    self.assertEqual(original.read_bytes(), payload)
                    evidence = receipt['lpac_token_evidence']
                    self.assertFalse(evidence['world_only_read'])
                    self.assertFalse(evidence['all_application_packages_read'])
                    self.assertTrue(evidence['own_package_read'])
                    self.assertEqual(receipt['capability_count'], 0)
                    self.assertEqual(receipt['cleanup_status'], 'exited')

    def test_midgrant_failure_preserves_low_scratch_and_absent_runtime_sacl(self):
        with tempfile.TemporaryDirectory(prefix='bare-private-acl-dev-') as temporary:
            root = Path(temporary)
            source = root / 'MOCK-SDK-SOURCE'
            (source / 'bin').mkdir(parents=True)
            (source / 'bin/python.exe').write_bytes(b'MOCK ACL fixture, never executable')
            (source / 'library.txt').write_text('independent security fixture', encoding='utf-8')
            scratch = isolation.create_scratch(root / 'scratch')
            (scratch / 'inputs').mkdir()
            original = scratch / 'inputs/original.txt'
            original.write_text('independent original', encoding='utf-8')
            with patch.object(isolation, 'PINNED_PYTHON', source / 'bin/python.exe'):
                staged = isolation.stage_runtime(source, root / 'runtime')
                runtime = Path(staged['root'])
                paths = [scratch, *scratch.rglob('*'), runtime, *runtime.rglob('*')]
                before = {str(path): security_descriptor(path) for path in paths}
                actual_acl = isolation.WindowsBoundary._acl
                def interrupted_acl(boundary, path, *args, **kwargs):
                    actual_acl(boundary, path, *args, **kwargs)
                    if path == runtime:
                        raise RuntimeError('independent injected interruption')
                with patch.object(isolation.WindowsBoundary, '_acl', interrupted_acl):
                    with self.assertRaises(RuntimeError) as raised:
                        with isolation.WindowsBoundary(scratch, runtime, read_files=[original],
                                runtime_inventory=staged['inventory'], staging_proof=staged['proof']):
                            self.fail('interrupted setup cannot start a child')
                self.assertIs(type(raised.exception), RuntimeError)
                self.assertEqual(before, {str(path): security_descriptor(path) for path in paths})
                self.assertEqual(list(root.glob('*.security-recovery.json')), [])

    def test_owned_scratch_preserves_security_after_setup_failure(self):
        with tempfile.TemporaryDirectory(prefix='bare-lpac-independent-dev-owner-') as temporary:
            scratch = isolation.create_scratch(Path(temporary) / 'scratch')
            before, non_owner_before = security_descriptor(scratch), security_descriptor(scratch, 0x16)
            with self.assertRaisesRegex(RuntimeError, '^DEV_injected_setup_failure$'):
                with current_user_owned_scratch(scratch):
                    self.assertEqual(non_owner_before, security_descriptor(scratch, 0x16))
                    (scratch / 'inputs').mkdir()
                    raise RuntimeError('DEV_injected_setup_failure')
            self.assertEqual(before, security_descriptor(scratch))
            (scratch / 'after-restore.txt').write_text('DEV_OWNER_RESTORED', encoding='utf-8')

    def test_real_lpac_denies_escape_and_builds_ordinary_native_artifacts(self):
        source_runtime = isolation.PINNED_PYTHON.parent.parent
        self.assertTrue(isolation.PINNED_PYTHON.is_file(), 'pinned offline FreeCAD 1.1.4 is required')
        with tempfile.TemporaryDirectory(prefix='bare-lpac-independent-dev-') as temporary, ExitStack() as ownership:
            root = Path(temporary)
            staged = isolation.stage_runtime(source_runtime, root / 'runtime')
            runtime = Path(staged['root'])
            boundary_options = dict(runtime_inventory=staged['inventory'], staging_proof=staged['proof'])
            source_paths = [source_runtime, *(source_runtime / name for name in staged['inventory']['directories']),
                            *(source_runtime / name for name in staged['inventory']['files'])]
            source_before = {str(p): security_descriptor(p) for p in source_paths}
            scratch = isolation.create_scratch(root / 'scratch')
            ownership.enter_context(current_user_owned_scratch(scratch))
            inputs = scratch / 'inputs'
            inputs.mkdir()
            original = inputs / 'original.txt'
            original.write_text('INDEPENDENT_DEV_ORIGINAL', encoding='utf-8')
            outside = root / 'must-not-read.txt'
            outside.write_text('INDEPENDENT_DEV_SECRET', encoding='utf-8')
            private_paths = [scratch, inputs, original, runtime, *(runtime / name for name in staged['inventory']['directories']),
                             *(runtime / name for name in staged['inventory']['files'])]
            before = {str(p): security_descriptor(p) for p in private_paths}
            actual_acl = isolation.WindowsBoundary._acl
            def interrupted_acl(boundary, path, *args, **kwargs):
                actual_acl(boundary, path, *args, **kwargs)
                if path == runtime:
                    raise RuntimeError('DEV_injected_after_runtime_grant')
            with patch.object(isolation.WindowsBoundary, '_acl', interrupted_acl):
                with self.assertRaises(RuntimeError) as interrupted:
                    with isolation.WindowsBoundary(scratch, runtime, read_files=[original], **boundary_options):
                        self.fail('interrupted setup cannot launch a child')
            self.assertIs(type(interrupted.exception), RuntimeError)
            self.assertEqual(before, {str(path): security_descriptor(path) for path in private_paths})
            self.assertEqual(list(root.glob('*.security-recovery.json')), [])
            listener = socket.socket()
            self.addCleanup(listener.close)
            listener.bind(('127.0.0.1', 0))
            listener.listen(1)
            listener.settimeout(.1)
            source = '''import json, pathlib, socket, subprocess, sys
config = json.loads(__DEV_CONFIG__)
import FreeCAD as A
import Part, Sketcher
assert tuple(A.Version()[:3]) == ('1','1','4') and not A.GuiUp
assert pathlib.Path('inputs/original.txt').read_text() == 'INDEPENDENT_DEV_ORIGINAL'
results = {}
try:
    pathlib.Path(config['outside']).read_bytes()
    results['external_file_denied'] = False
except OSError:
    results['external_file_denied'] = True
try:
    pathlib.Path(config['repo']).read_bytes()
    results['repository_denied'] = False
except OSError:
    results['repository_denied'] = True
try:
    pathlib.Path('inputs/original.txt').write_text('NOT_ALLOWED')
    results['inputs_read_only'] = False
except OSError:
    results['inputs_read_only'] = True
import ctypes as C
from ctypes import wintypes as W
a = C.WinDLL('advapi32')
a.SetNamedSecurityInfoW.argtypes = [W.LPWSTR, C.c_int, W.DWORD, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p]
k = C.WinDLL('kernel32')
k.GetCurrentProcess.restype = C.c_void_p
k.CloseHandle.argtypes = [C.c_void_p]
k.LocalFree.argtypes = [C.c_void_p]
a.OpenProcessToken.argtypes = [C.c_void_p, W.DWORD, C.POINTER(C.c_void_p)]
a.GetTokenInformation.argtypes = [C.c_void_p, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)]
a.GetNamedSecurityInfoW.argtypes = [W.LPWSTR, C.c_int, W.DWORD, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)]
a.EqualSid.argtypes = [C.c_void_p, C.c_void_p]
token, needed, owner, descriptor = C.c_void_p(), W.DWORD(), C.c_void_p(), C.c_void_p()
assert a.OpenProcessToken(k.GetCurrentProcess(), 8, C.byref(token))
try:
    a.GetTokenInformation(token, 1, None, 0, C.byref(needed))
    data = C.create_string_buffer(needed.value)
    assert a.GetTokenInformation(token, 1, data, needed, C.byref(needed))
    assert a.GetNamedSecurityInfoW(str(pathlib.Path.cwd()), 1, 1, C.byref(owner), None, None, None, C.byref(descriptor)) == 0
    results['root_owned_by_child_user'] = bool(a.EqualSid(owner, C.cast(data, C.POINTER(C.c_void_p))[0]))
finally:
    k.CloseHandle(token)
    if descriptor:
        k.LocalFree(descriptor)
results['acl_tamper_denied'] = a.SetNamedSecurityInfoW('inputs/original.txt', 1, 4, None, None, None, None) == 5
results['root_acl_tamper_denied'] = a.SetNamedSecurityInfoW(str(pathlib.Path.cwd()), 1, 4, None, None, None, None) == 5
results['runtime_acl_tamper_denied'] = a.SetNamedSecurityInfoW(config['python'], 1, 4, None, None, None, None) == 5
current_user = C.cast(data, C.POINTER(C.c_void_p))[0]
results['owner_tamper_denied'] = a.SetNamedSecurityInfoW(str(pathlib.Path.cwd()), 1, 1, current_user, None, None, None) == 5
results['runtime_owner_tamper_denied'] = a.SetNamedSecurityInfoW(config['python'], 1, 1, current_user, None, None, None) == 5
try:
    pathlib.Path('inputs').rename('inputs-moved')
    pathlib.Path('inputs').mkdir()
    pathlib.Path('inputs/original.txt').write_text('REPLACED_INPUT')
    results['inputs_rename_denied'] = False
except OSError as error:
    results['inputs_rename_denied'] = error.winerror == 5
ordinary = pathlib.Path('ordinary.tmp')
ordinary.write_text('DEV_OWNED_FILE')
ordinary = ordinary.rename('ordinary-renamed.tmp')
ordinary.unlink()
results['construction_file_ops'] = True
try:
    subprocess.run([sys.executable, '-I', '-c', 'print("CHILD_NOT_ALLOWED")'], check=True)
    results['child_denied'] = False
except (OSError, subprocess.SubprocessError):
    results['child_denied'] = True
s = None
try:
    s = socket.socket()
    s.settimeout(1)
    s.connect(('127.0.0.1', config['port']))
    results['network_denied'] = False
except OSError:
    results['network_denied'] = True
finally:
    if s is not None:
        s.close()
doc = A.newDocument('IndependentDev')
body = doc.addObject('PartDesign::Body', 'Body')
sketch = doc.addObject('Sketcher::SketchObject', 'Sketch')
body.addObject(sketch)
points = [(0,0), (12,0), (12,7), (0,7)]
for i, point in enumerate(points):
    end = points[(i+1)%4]
    sketch.addGeometry(Part.LineSegment(A.Vector(*point,0), A.Vector(*end,0)), False)
pad = body.newObject('PartDesign::Pad', 'Pad')
pad.Profile, pad.Length = sketch, 4
doc.recompute()
assert pad.Shape.isValid() and len(pad.Shape.Solids) == 1
out = pathlib.Path('out')
out.mkdir()
doc.saveAs(str(out / 'model.FCStd'))
Part.export([body], str(out / 'model.step'))
results['native_freecad'] = True
print('BARE_DEV_RESULT=' + json.dumps(results, sort_keys=True))
'''.replace('__DEV_CONFIG__', repr(json.dumps({'outside': str(outside), 'repo': str(Path(isolation.__file__).resolve()),
                                            'python': str(runtime / 'bin/python.exe'), 'port': listener.getsockname()[1]})), 1)
            (scratch / 'build.py').write_text(source, encoding='utf-8')
            stdout, stderr = root / 'tool-001.stdout', root / 'tool-001.stderr'
            with isolation.WindowsBoundary(scratch, runtime, read_files=[original], **boundary_options) as boundary:
                trace = NativeTrace(boundary, time.monotonic() + 180)
                loop = bare.ToolLoop(trace, scratch, boundary, root,
                                     lambda: trace.deadline - trace.wall(), 'independent-dev-native')
                try:
                    visible = loop.execute({'kind': 'python', 'args': ['build.py']})
                except isolation.BoundaryUnavailable as error:
                    self.fail(str(error) + '\n' + json.dumps(boundary.last_receipt, sort_keys=True) +
                              '\nstdout:\n' + stdout.read_text(encoding='utf-8', errors='replace') +
                              '\nstderr:\n' + stderr.read_text(encoding='utf-8', errors='replace'))
                result = [fields['result'] for kind, fields in trace.events if kind == 'bare_tool'][-1]
                native_command = [fields['command'] for kind, fields in trace.events if kind == 'bare_process_stopped'][-1]
                self.assertEqual(visible['returncode'], 0, stderr.read_text(encoding='utf-8', errors='replace'))
                self.assertEqual(result['initialization']['bootstrap_sha256'], bare.BOOTSTRAP_SHA256)
                self.assertEqual(len(loop.native_intervals), 1)
                self.assertEqual(loop.unverified_native_intervals, [])
                self.assertEqual(result['isolation'], 'windows_lpac_zero_capabilities')
                text = stdout.read_text(encoding='utf-8', errors='strict')
                records = [line.removeprefix('BARE_DEV_RESULT=') for line in text.splitlines() if line.startswith('BARE_DEV_RESULT=')]
                self.assertEqual(len(records), 1, text)
                receipt = json.loads(records[0])
                self.assertTrue(all(receipt.values()), receipt)
                self.assertTrue((scratch / 'out/model.FCStd').is_file())
                self.assertTrue((scratch / 'out/model.step').is_file())
                with self.assertRaises(socket.timeout):
                    listener.accept()
                self.assertEqual(result['cleanup_status'], 'exited')
                shell_stdout, shell_stderr = root / 'shell.stdout', root / 'shell.stderr'
                shell_command = 'echo DEV_SHELL_OK>shell-ordinary.tmp && type shell-ordinary.tmp && ren shell-ordinary.tmp shell-renamed.tmp && del shell-renamed.tmp'
                shell = boundary.run([str(Path(os.environ['SystemRoot']) / 'System32/cmd.exe'), '/d', '/s', '/c', shell_command],
                                     stdout=shell_stdout, stderr=shell_stderr, timeout=30)
                self.assertEqual(shell['returncode'], 0, shell_stderr.read_text(encoding='utf-8', errors='replace'))
                self.assertIn('DEV_SHELL_OK', shell_stdout.read_text(encoding='utf-8'))
                self.assertFalse((scratch / 'shell-ordinary.tmp').exists())
                self.assertFalse((scratch / 'shell-renamed.tmp').exists())
                timeout_out = root / 'timeout'
                timeout_out.mkdir()
                timeout_loop = bare.ToolLoop(trace, scratch, boundary, timeout_out,
                                             lambda: .1, 'independent-dev-owned-timeout')
                with self.assertRaises(TimeoutError):
                    timeout_loop.execute({'kind': 'python', 'args': ['-c', 'import time;time.sleep(30)']})
                self.assertEqual(boundary.last_receipt['cleanup_status'], 'exited')
                self.assertEqual(boundary.handles, [])
                timeout_receipt = dict(boundary.last_receipt)
                for key in ('stdout', 'stderr'):
                    timeout_receipt[key + '_base64'] = base64.b64encode(Path(timeout_receipt[key]).read_bytes()).decode('ascii')
                receipt.update(shell_file_io=True, owned_timeout_cleanup=True)
            after = {str(p): security_descriptor(p) for p in private_paths}
            self.assertEqual(before, after, 'scoped owner/group/DACL/integrity labels must be restored')
            self.assertEqual(original.read_text(encoding='utf-8'), 'INDEPENDENT_DEV_ORIGINAL')
            self.assertEqual(source_before, {str(p): security_descriptor(p) for p in source_paths},
                             'installed source owner/group/DACL/integrity/control must never change')
            isolation.validate_staged_runtime(runtime, staged['inventory'], staged['proof'])
            self.assertEqual(list(root.glob('*.security-recovery.json')), [])
            receipt.update(schema='cad-harness.bare-isolation-smoke.v1', lpac=True,
                           zero_capabilities=True, cleanup_restored=True, boot_id=isolation.boot_id(),
                           freecad_bootstrap_initialized=True, bootstrap_sha256=bare.BOOTSTRAP_SHA256,
                           python_sha256=isolation.file_hash(isolation.PINNED_PYTHON),
                           relocated_python=str(runtime / 'bin/python.exe'), runtime_inventory=staged['inventory'],
                           runtime_staging_proof=staged['proof'],
                           runtime_inventory_sha256=hashlib.sha256(isolation.canonical(staged['inventory'])).hexdigest(),
                           runtime_staging_proof_sha256=hashlib.sha256(isolation.canonical(staged['proof'])).hexdigest(),
                           native_smoke_sha256=isolation.file_hash(Path(__file__)),
                           source_security_unchanged=True, private_runtime_verified=True, setup_failure_restored=True,
                           source_sha256=isolation.file_hash(scratch / 'build.py'),
                           source_base64=base64.b64encode((scratch / 'build.py').read_bytes()).decode('ascii'),
                           native_process=result, native_command=native_command, timeout_process=timeout_receipt,
                           shell_process=dict(shell, stdout_base64=base64.b64encode(shell_stdout.read_bytes()).decode('ascii'),
                                              stderr_base64=base64.b64encode(shell_stderr.read_bytes()).decode('ascii')),
                           isolation_sha256=isolation.file_hash(Path(isolation.__file__)),
                           supervisor_sha256=isolation.file_hash(Path(__file__).with_name('cad_verify_v4_bare.py')),
                           stdout_sha256=isolation.file_hash(stdout), stderr_sha256=isolation.file_hash(stderr),
                           evidence_mode='independent_dev', live_calls=0)
        receipt['owner_setup_and_temp_cleanup_restored'] = True
        if os.environ.get('CAD_BARE_SMOKE_RECEIPT'):
            receipt_path = Path(os.environ['CAD_BARE_SMOKE_RECEIPT'])
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            with receipt_path.open('x', encoding='utf-8') as handle:
                json.dump(receipt, handle, sort_keys=True, indent=2)
        print('BARE_ISOLATION_DEV_RECEIPT=' + json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
