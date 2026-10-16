"""Offline LPAC construction boundary for the bare benchmark (Windows 10+).

No fallback exists: every child has a zero-capability AppContainer token, opts
out of ALL APPLICATION PACKAGES access, cannot create children or use Win32k,
and belongs to a kill-on-close, one-process job. ACL grants use a unique SID and
are restored, including their inheritance protection, before its profile is deleted.
"""
import ctypes as C
from ctypes import wintypes as W
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import time
import uuid
import stat

PINNED_PYTHON = Path('C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe')


class BoundaryUnavailable(RuntimeError):
    pass


def boot_id():
    if os.name != 'nt':
        raise BoundaryUnavailable('windows_boot_identity_required')
    class Environment(C.Structure):
        _fields_ = [('identifier', C.c_ubyte * 16), ('firmware', W.DWORD), ('flags', C.c_uint64)]
    value = Environment()
    query = C.WinDLL('ntdll').NtQuerySystemInformation
    query.argtypes = [C.c_int, C.c_void_p, W.ULONG, C.c_void_p]
    status = query(90, C.byref(value), C.sizeof(value), None)
    if status != 0:
        raise BoundaryUnavailable('windows_boot_identity:' + hex(status & 0xffffffff))
    return str(uuid.UUID(bytes_le=bytes(value.identifier)))


def regular_tree(root):
    """Reject junctions/symlinks, including an ancestor of a granted path."""
    root = Path(root).absolute()
    for path in (root, *root.parents):
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
            raise BoundaryUnavailable('boundary_reparse_path:' + str(path))
    if root.is_dir():
        for path in root.rglob('*'):
            if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
                raise BoundaryUnavailable('boundary_reparse_path:' + str(path))
    return root


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _relative_name(value):
    path = PurePosixPath(value)
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if (not value or path.is_absolute() or path.as_posix() != value or
            any(not p or p in ('.', '..') or p.endswith((' ', '.')) or
                p.split('.')[0].upper() in reserved or any(ord(c) < 32 or c in '\\:*?<>|"' for c in p)
                for p in value.split('/'))):
        raise BoundaryUnavailable('runtime_relative_path:' + value)
    return path


def _runtime_path(path, *, missing=False):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts or '.' in path.parts:
        raise BoundaryUnavailable('runtime_absolute_canonical_path_required')
    for candidate in reversed((path, *path.parents)):
        if missing and not candidate.exists():
            continue
        regular_tree(candidate) if candidate == path else None
        if candidate.is_symlink() or getattr(candidate.lstat(), 'st_file_attributes', 0) & 0x400:
            raise BoundaryUnavailable('boundary_reparse_path:' + str(candidate))
        if candidate.parent != candidate:
            # Windows accepts case/short-name aliases; the frozen path may not.
            names = [p.name for p in candidate.parent.iterdir() if p.name.casefold() == candidate.name.casefold()]
            if names != [candidate.name]:
                raise BoundaryUnavailable('runtime_path_case_alias:' + str(candidate))
    return path


def _tree_inventory(root, *, private=False):
    root = _runtime_path(root)
    if not root.is_dir():
        raise BoundaryUnavailable('runtime_directory_required')
    files, directories, names = {}, [], set()
    # os.walk propagates scandir failures instead of silently dropping inaccessible
    # SDK/cache subtrees (Path.rglob may suppress those errors).
    def failed(error):
        raise error
    for folder, children, entries in os.walk(root, onerror=failed, followlinks=False):
        for name in sorted(children + entries):
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            _relative_name(relative)
            folded = relative.casefold()
            if folded in names:
                raise BoundaryUnavailable('runtime_case_alias:' + relative)
            names.add(folded)
            info = path.lstat()
            if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise BoundaryUnavailable('boundary_reparse_path:' + str(path))
            if stat.S_ISDIR(info.st_mode):
                directories.append(relative)
            elif stat.S_ISREG(info.st_mode):
                if private and info.st_nlink != 1:
                    raise BoundaryUnavailable('runtime_private_hardlink:' + relative)
                files[relative] = {'sha256': file_hash(path), 'bytes': info.st_size}
            else:
                raise BoundaryUnavailable('runtime_nonregular_file:' + relative)
    return dict(files=dict(sorted(files.items())), directories=sorted(directories))


def validate_staged_runtime(root, inventory, proof):
    """Rehash the complete independent runtime; metadata alone never admits it."""
    root = _runtime_path(root)
    source = _runtime_path(PINNED_PYTHON.parent.parent)
    if root == source or root in source.parents or source in root.parents:
        raise BoundaryUnavailable('runtime_private_copy_required')
    if (inventory.get('schema') != 'cad-harness.bare-runtime.v2' or inventory.get('freecad_version') != '1.1.4' or
            inventory.get('source_root') != str(source) or inventory.get('root') != str(root) or
            inventory.get('source_python', {}).get('path') != str(PINNED_PYTHON)):
        raise BoundaryUnavailable('runtime_pinned_source_identity_required')
    expected = {key: inventory.get(key) for key in ('files', 'directories')}
    if (not isinstance(expected['files'], dict) or not expected['files'] or
            expected['files'].get('bin/python.exe') != {k: inventory['source_python'].get(k) for k in ('sha256', 'bytes')}):
        raise BoundaryUnavailable('runtime_original_python_inventory_required')
    if _tree_inventory(root, private=True) != expected:
        raise BoundaryUnavailable('runtime_staged_inventory_changed')
    if _tree_inventory(source) != expected:
        raise BoundaryUnavailable('runtime_source_inventory_changed')
    python = dict(path=str(root / 'bin/python.exe'), **expected['files']['bin/python.exe'])
    if (proof.get('schema') != 'cad-harness.bare-runtime-staging.v1' or
            proof.get('inventory_sha256') != hashlib.sha256(canonical(inventory)).hexdigest() or
            proof.get('source_root') != str(source) or proof.get('root') != str(root) or
            proof.get('source_python') != inventory['source_python'] or proof.get('python') != python or
            proof.get('isolation_sha256') != file_hash(__file__) or
            proof.get('purpose') != 'pretrial_software_environment' or proof.get('live_calls') != 0 or
            proof.get('copy_method') != 'exclusive_byte_copy_no_links' or
            not isinstance(proof.get('boot_id'), str) or not proof['boot_id']):
        raise BoundaryUnavailable('runtime_staging_proof_mismatch')
    try:
        start, end = (datetime.fromisoformat(proof[k]) for k in ('started_utc', 'finished_utc'))
        interval = proof['monotonic_interval']
        valid = (start.tzinfo is not None and end.tzinfo is not None and end >= start and
                 isinstance(interval, list) and len(interval) == 2 and
                 all(type(v) in (int, float) and 0 <= v < float('inf') for v in interval) and interval[1] >= interval[0])
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise BoundaryUnavailable('runtime_staging_times_required')
    return root


def _create_private_directory(path, *, low_integrity=False):
    if os.name != 'nt':
        path.mkdir(mode=0o700)
        return
    a, k = C.WinDLL('advapi32', use_last_error=True), C.WinDLL('kernel32', use_last_error=True)
    P = C.c_void_p
    class Attributes(C.Structure):
        _fields_ = [('length', W.DWORD), ('descriptor', P), ('inherit', W.BOOL)]
    k.GetCurrentProcess.restype = P
    k.CloseHandle.argtypes, k.LocalFree.argtypes = [P], [P]
    k.CreateDirectoryW.argtypes = [W.LPCWSTR, C.POINTER(Attributes)]
    a.OpenProcessToken.argtypes = [P, W.DWORD, C.POINTER(P)]
    a.GetTokenInformation.argtypes = [P, C.c_int, P, W.DWORD, C.POINTER(W.DWORD)]
    a.ConvertSidToStringSidW.argtypes = [P, C.POINTER(W.LPWSTR)]
    a.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [W.LPCWSTR, W.DWORD, C.POINTER(P), P]
    token, descriptor, text, size = P(), P(), W.LPWSTR(), W.DWORD()
    def required(value, operation):
        if not value:
            raise BoundaryUnavailable(operation + ':' + str(C.get_last_error()))
    required(a.OpenProcessToken(k.GetCurrentProcess(), 8, C.byref(token)), 'staging_user_token')
    try:
        a.GetTokenInformation(token, 1, None, 0, C.byref(size))
        if not size.value:
            raise BoundaryUnavailable('staging_user_sid_size')
        data = C.create_string_buffer(size.value)
        required(a.GetTokenInformation(token, 1, data, size.value, C.byref(size)), 'staging_user_sid')
        required(a.ConvertSidToStringSidW(C.cast(data, C.POINTER(P))[0], C.byref(text)), 'staging_user_sid_text')
        # Atomically create a protected current-user-only inheritable DACL.
        # A public destination parent's permissions must never enter this copy.
        sddl = 'D:P(A;OICI;FA;;;' + text.value + ')'
        if low_integrity:
            sddl += 'S:(ML;OICI;NW;;;LW)'
        required(a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, C.byref(descriptor), None), 'staging_private_descriptor')
        attributes = Attributes(C.sizeof(Attributes), descriptor, False)
        required(k.CreateDirectoryW(str(path), C.byref(attributes)), 'staging_private_directory')
    finally:
        if text:
            k.LocalFree(text)
        if descriptor:
            k.LocalFree(descriptor)
        k.CloseHandle(token)

def create_scratch(path):
    """Create the private low-integrity workspace; never relabel an existing tree."""
    path = _runtime_path(path, missing=True)
    source = PINNED_PYTHON.parent.parent
    if path == source or path in source.parents or source in path.parents:
        raise BoundaryUnavailable('boundary_scratch_source_overlap')
    _create_private_directory(path, low_integrity=True)
    return path



def stage_runtime(source, target):
    """Prepare software only, before freeze; never execute or mutate source.

    Return root plus inventory/proof JSON objects. The caller freezes both files
    OUTSIDE the runtime and registers their file IDs; no model/task data is read.
    A failed copy is retained as unadmitted evidence, never reused or repaired.
    """
    started_utc, start = datetime.now(timezone.utc).isoformat(), time.monotonic()
    source, target = _runtime_path(source), _runtime_path(target, missing=True)
    if source != PINNED_PYTHON.parent.parent or source / 'bin/python.exe' != PINNED_PYTHON:
        raise BoundaryUnavailable('runtime_original_pinned_source_required')
    if target.exists() or target == source or target in source.parents or source in target.parents:
        raise BoundaryUnavailable('runtime_new_private_destination_required')
    original = _tree_inventory(source)
    if 'bin/python.exe' not in original['files']:
        raise BoundaryUnavailable('runtime_original_python_required')
    _create_private_directory(target)
    for name in sorted(original['directories'], key=lambda p: (p.count('/'), p)):
        target.joinpath(*_relative_name(name).parts).mkdir()
    for name, record in original['files'].items():
        src, dst = source.joinpath(*_relative_name(name).parts), target.joinpath(*_relative_name(name).parts)
        # Exclusive creation is intentional: no copy2 ACL metadata, hard links,
        # cache exclusions, package downloads, generated files or silent skips.
        with src.open('rb') as reader, dst.open('xb') as writer:
            while block := reader.read(1024 * 1024):
                writer.write(block)
        if dst.stat().st_size != record['bytes'] or file_hash(dst) != record['sha256']:
            raise BoundaryUnavailable('runtime_copy_changed:' + name)
    inventory = dict(schema='cad-harness.bare-runtime.v2', freecad_version='1.1.4',
                     source_root=str(source), root=str(target),
                     source_python=dict(path=str(PINNED_PYTHON), **original['files']['bin/python.exe']), **original)
    proof = dict(schema='cad-harness.bare-runtime-staging.v1', source_root=str(source), root=str(target),
                 source_python=inventory['source_python'], python=dict(path=str(target / 'bin/python.exe'), **original['files']['bin/python.exe']),
                 inventory_sha256=hashlib.sha256(canonical(inventory)).hexdigest(), isolation_sha256=file_hash(__file__),
                 purpose='pretrial_software_environment', copy_method='exclusive_byte_copy_no_links', live_calls=0,
                 started_utc=started_utc, finished_utc=datetime.now(timezone.utc).isoformat(),
                 monotonic_interval=[start, time.monotonic()], boot_id=boot_id())
    validate_staged_runtime(target, inventory, proof)
    proof.update(finished_utc=datetime.now(timezone.utc).isoformat(), monotonic_interval=[start, time.monotonic()])
    return dict(root=str(target), inventory=inventory, proof=proof)


class WindowsBoundary:
    """The supervisor alone handles file I/O; generated programs stay in LPAC.

    ``runtime`` is the frozen complete runtime inventory (including documents).
    ``read_files`` are individually authorized ORIGINAL inputs, never a repo.
    Runtime and source copies are read-only; ``scratch`` alone is writable.
    """
    def __init__(self, scratch, runtime, *, runtime_inventory=None, staging_proof=None, read_files=(), wall=None):
        if os.name != 'nt':
            raise BoundaryUnavailable('windows_lpac_required')
        if not isinstance(runtime_inventory, dict) or not isinstance(staging_proof, dict):
            raise BoundaryUnavailable('boundary_verified_private_runtime_required')
        source, candidate = PINNED_PYTHON.parent.parent, Path(scratch)
        if candidate == source or candidate in source.parents or source in candidate.parents:
            raise BoundaryUnavailable('boundary_scratch_source_overlap')
        self.scratch = _runtime_path(scratch)
        self.runtime = validate_staged_runtime(runtime, runtime_inventory, staging_proof)
        self.python = self.runtime / 'bin/python.exe'
        self.read_files = [regular_tree(p) for p in read_files]
        if any(not p.is_file() or not p.is_relative_to(self.scratch) or p.stat().st_nlink != 1 for p in self.read_files):
            raise BoundaryUnavailable('boundary_private_input_copy_required')
        if self.scratch == self.runtime or self.scratch in self.runtime.parents or self.runtime in self.scratch.parents:
            raise BoundaryUnavailable('boundary_runtime_scratch_overlap')
        self.wall = wall or time.monotonic
        self.name = 'CADBare.' + uuid.uuid4().hex
        self.sid = C.c_void_p()
        self.owner_sid, self.host_sid = C.c_void_p(), C.c_void_p()
        self.host_sid_buffer = None
        self.snapshots, self.handles = {}, []
        self.changed = False
        self.recovery_path = self.scratch.parent / (self.name + '.security-recovery.json')
        self.entered = False
        self._api()

    def _api(self):
        self.k = C.WinDLL('kernel32', use_last_error=True)
        self.a = C.WinDLL('advapi32', use_last_error=True)
        self.u = C.WinDLL('userenv', use_last_error=True)
        P = C.c_void_p
        self.k.LocalFree.argtypes, self.k.LocalFree.restype = [P], P
        self.k.CloseHandle.argtypes, self.k.CloseHandle.restype = [P], W.BOOL
        self.k.CreateJobObjectW.argtypes, self.k.CreateJobObjectW.restype = [P, W.LPCWSTR], P
        self.k.SetInformationJobObject.argtypes = [P, C.c_int, P, W.DWORD]
        self.k.AssignProcessToJobObject.argtypes = [P, P]
        self.k.TerminateJobObject.argtypes = [P, W.UINT]
        self.k.WaitForSingleObject.argtypes = [P, W.DWORD]
        self.k.GetExitCodeProcess.argtypes = [P, C.POINTER(W.DWORD)]
        self.k.ResumeThread.argtypes = [P]
        self.k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, P, W.DWORD, W.DWORD, P]
        self.k.CreateFileW.restype = P
        self.k.InitializeProcThreadAttributeList.argtypes = [P, W.DWORD, W.DWORD, C.POINTER(C.c_size_t)]
        self.k.UpdateProcThreadAttribute.argtypes = [P, W.DWORD, C.c_size_t, P, C.c_size_t, P, P]
        self.k.DeleteProcThreadAttributeList.argtypes = [P]
        self.k.CreateProcessW.argtypes = [W.LPCWSTR, W.LPWSTR, P, P, W.BOOL, W.DWORD, P, W.LPCWSTR, P, P]
        self.a.GetSecurityInfo.argtypes = [P, C.c_int, W.DWORD, P, P, P, P, C.POINTER(P)]
        self.a.SetSecurityInfo.argtypes = [P, C.c_int, W.DWORD, P, P, P, P]
        self.a.SetKernelObjectSecurity.argtypes = [P, W.DWORD, P]
        self.a.GetSecurityDescriptorLength.argtypes, self.a.GetSecurityDescriptorLength.restype = [P], W.DWORD
        self.a.GetSecurityDescriptorOwner.argtypes = [P, C.POINTER(P), C.POINTER(W.BOOL)]
        self.a.GetSecurityDescriptorDacl.argtypes = [P, C.POINTER(W.BOOL), C.POINTER(P), C.POINTER(W.BOOL)]
        self.a.GetSecurityDescriptorSacl.argtypes = [P, C.POINTER(W.BOOL), C.POINTER(P), C.POINTER(W.BOOL)]
        self.a.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [P, W.DWORD, W.DWORD, C.POINTER(W.LPWSTR), P]
        self.a.EqualSid.argtypes = [P, P]
        self.a.GetAce.argtypes = [P, W.DWORD, C.POINTER(P)]
        self.a.GetSecurityDescriptorControl.argtypes = [P, C.POINTER(W.WORD), C.POINTER(W.DWORD)]
        self.a.SetEntriesInAclW.argtypes = [W.ULONG, P, P, C.POINTER(P)]
        self.k.GetCurrentProcess.argtypes, self.k.GetCurrentProcess.restype = [], P
        self.a.OpenProcessToken.argtypes = [P, W.DWORD, C.POINTER(P)]
        self.a.GetTokenInformation.argtypes = [P, C.c_int, P, W.DWORD, C.POINTER(W.DWORD)]
        self.a.ConvertStringSidToSidW.argtypes = [W.LPCWSTR, C.POINTER(P)]
        self.a.FreeSid.argtypes = [P]
        self.u.CreateAppContainerProfile.argtypes = [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, P, W.DWORD, C.POINTER(P)]
        self.u.DeleteAppContainerProfile.argtypes = [W.LPCWSTR]

    @staticmethod
    def _ok(value, operation):
        if not value:
            raise BoundaryUnavailable(operation + ':' + str(C.get_last_error()))
        return value

    def _acl_principals(self):
        token, size = C.c_void_p(), W.DWORD()
        self._ok(self.a.OpenProcessToken(self.k.GetCurrentProcess(), 8, C.byref(token)), 'supervisor_token')
        try:
            self.a.GetTokenInformation(token, 1, None, 0, C.byref(size))
            if not size.value:
                raise BoundaryUnavailable('supervisor_token_user_size')
            self.host_sid_buffer = C.create_string_buffer(size.value)
            self._ok(self.a.GetTokenInformation(token, 1, self.host_sid_buffer, size.value, C.byref(size)), 'supervisor_token_user')
            self.host_sid = C.cast(self.host_sid_buffer, C.POINTER(C.c_void_p)).contents
        finally:
            self.k.CloseHandle(token)
        self._ok(self.a.ConvertStringSidToSidW('S-1-3-4', C.byref(self.owner_sid)), 'owner_rights_sid')

    def _security(self, handle):
        descriptor, text = C.c_void_p(), W.LPWSTR()
        status = self.a.GetSecurityInfo(handle, 1, 0x17, None, None, None, None, C.byref(descriptor))
        if status:
            raise BoundaryUnavailable('security_snapshot:' + str(status))
        try:
            control, revision = W.WORD(), W.DWORD()
            self._ok(self.a.GetSecurityDescriptorControl(descriptor, C.byref(control), C.byref(revision)), 'security_control')
            self._ok(self.a.ConvertSecurityDescriptorToStringSecurityDescriptorW(descriptor, 1, 0x17, C.byref(text), None), 'security_render')
            owner, defaulted = C.c_void_p(), W.BOOL()
            self._ok(self.a.GetSecurityDescriptorOwner(descriptor, C.byref(owner), C.byref(defaulted)), 'security_owner')
            owned = bool(self.a.EqualSid(owner, self.host_sid))
            present, dacl = W.BOOL(), C.c_void_p()
            self._ok(self.a.GetSecurityDescriptorDacl(descriptor, C.byref(present), C.byref(dacl), C.byref(defaulted)), 'security_dacl')
            private_acl = False
            if present.value and dacl:
                # ACL header AceCount is the WORD at offset four. An ordinary
                # staged object has exactly one current-user FULL_CONTROL ACE;
                # neither a public/null DACL nor another user's copy is private.
                count = C.cast(dacl.value + 4, C.POINTER(W.WORD))[0]
                if count == 1:
                    ace = C.c_void_p()
                    self._ok(self.a.GetAce(dacl, 0, C.byref(ace)), 'security_private_ace')
                    private_acl = (C.cast(ace, C.POINTER(C.c_ubyte))[0] == 0 and
                                   C.cast(ace.value + 4, C.POINTER(W.DWORD))[0] == 0x1f01ff and
                                   bool(self.a.EqualSid(ace.value + 8, self.host_sid)))
            return dict(descriptor=C.string_at(descriptor, self.a.GetSecurityDescriptorLength(descriptor)),
                        sddl=text.value, control=control.value, owned=owned, private_acl=private_acl)
        finally:
            if text:
                self.k.LocalFree(text)
            self.k.LocalFree(descriptor)

    def _prepare_security(self):
        # Hold READ_CONTROL/WRITE_DAC before any private DACL changes.
        # Ownership and integrity are fixed at creation, never transitioned here.
        paths = [self.scratch, *self.scratch.rglob('*'), self.runtime, *self.runtime.rglob('*')]
        try:
            for path in sorted(set(paths), key=lambda p: (len(p.parts), str(p))):
                if path.is_file() and path.stat().st_nlink != 1:
                    raise BoundaryUnavailable('boundary_private_hardlink:' + str(path))
                handle = self.k.CreateFileW(str(path), 0x60000, 3, None, 3, 0x02200000, None)
                if handle == C.c_void_p(-1).value:
                    raise BoundaryUnavailable('security_preflight_handle:' + str(path) + ':' + str(C.get_last_error()))
                try:
                    snapshot = self._security(handle)
                    if not snapshot['owned']:
                        raise BoundaryUnavailable('boundary_current_user_private_copy_required:' + str(path))
                    if path == self.scratch and '(ML;OICI;NW;;;LW)' not in snapshot['sddl']:
                        raise BoundaryUnavailable('boundary_created_low_scratch_required')
                    if path.is_relative_to(self.runtime) and not snapshot['private_acl']:
                        raise BoundaryUnavailable('boundary_private_runtime_dacl_required:' + str(path))
                    info = path.stat()
                    self.snapshots[path] = dict(handle=handle, identity=[info.st_dev, info.st_ino], **snapshot)
                except BaseException:
                    self.k.CloseHandle(handle)
                    raise
            journal = dict(schema='cad-harness.bare-security-recovery.v1', profile=self.name,
                           scratch=str(self.scratch), runtime=str(self.runtime), boot_id=boot_id(),
                           snapshots=[dict(path=str(path), identity=snapshot['identity'],
                               descriptor_base64=base64.b64encode(snapshot['descriptor']).decode('ascii'),
                               sddl=snapshot['sddl'], control=snapshot['control'])
                               for path, snapshot in self.snapshots.items()])
            with self.recovery_path.open('xb') as stream:
                stream.write(canonical(journal))
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            for snapshot in self.snapshots.values():
                self.k.CloseHandle(snapshot['handle'])
            self.snapshots.clear()
            raise

    def _restore_security(self):
        errors = []
        if self.changed:
            # Never propagate security through a generated link/reparse point.
            # Existing objects remain restorable through their held handles.
            safe = True
            try:
                def failed(error):
                    raise error
                for folder, directories, files in os.walk(self.scratch, onerror=failed, followlinks=False):
                    for name in directories + files:
                        path = Path(folder) / name
                        info = path.lstat()
                        if (path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or
                                stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
                            raise BoundaryUnavailable('cleanup_link_path:' + str(path))
            except (OSError, BoundaryUnavailable) as exc:
                safe = False
                errors.append(str(exc))
            if safe:
                # Restore inheritance for new files before exact per-object
                # restoration. Parent setters cannot reopen revoked handles.
                snapshot = self.snapshots[self.scratch]
                descriptor = C.create_string_buffer(snapshot['descriptor'])
                present, defaulted, dacl = W.BOOL(), W.BOOL(), C.c_void_p()
                self._ok(self.a.GetSecurityDescriptorDacl(descriptor, C.byref(present), C.byref(dacl), C.byref(defaulted)), 'restore_dacl')
                protection = 0x80000000 if snapshot['control'] & 0x1000 else 0x20000000
                status = self.a.SetSecurityInfo(snapshot['handle'], 1, 4 | protection, None, None, dacl, None)
                if status:
                    errors.append('scratch_inheritance_restore:' + str(status))
            for path, snapshot in self.snapshots.items():
                try:
                    current = self._security(snapshot['handle'])
                except BoundaryUnavailable as exc:
                    errors.append(str(exc))
                    continue
                if (current['sddl'], current['control']) == (snapshot['sddl'], snapshot['control']):
                    continue
                descriptor = C.create_string_buffer(snapshot['descriptor'])
                protection = 0x80000000 if snapshot['control'] & 0x1000 else 0x20000000
                # LABEL with an absent SACL creates a present NULL SACL. Only
                # DACLs changed: preserve the exact creation-time integrity state.
                if not self.a.SetKernelObjectSecurity(snapshot['handle'], 4 | protection, descriptor):
                    errors.append('security_restore:' + str(path) + ':' + str(C.get_last_error()))
                try:
                    after = self._security(snapshot['handle'])
                    if (after['sddl'], after['control']) != (snapshot['sddl'], snapshot['control']):
                        errors.append('security_restore_not_exact:' + str(path))
                except BoundaryUnavailable as exc:
                    errors.append(str(exc))
        # Keep the durable recovery evidence on any failure; never claim cleanup.
        for snapshot in self.snapshots.values():
            self.k.CloseHandle(snapshot['handle'])
        self.snapshots.clear()
        if not errors and self.recovery_path.exists():
            self.recovery_path.unlink()
        if errors:
            errors.append('security_recovery_evidence:' + str(self.recovery_path))
        return errors

    def _acl(self, path, mask, *, inherit=False, deny=False, guard_owner=False, read_only=False):
        class Trustee(C.Structure):
            _fields_ = [('multiple', C.c_void_p), ('operation', C.c_int), ('form', C.c_int),
                        ('type', C.c_int), ('name', C.c_void_p)]
        class Access(C.Structure):
            _fields_ = [('permissions', W.DWORD), ('mode', C.c_int), ('inheritance', W.DWORD), ('trustee', Trustee)]
        old, descriptor, new = C.c_void_p(), C.c_void_p(), C.c_void_p()
        status = self.a.GetSecurityInfo(self.snapshots[path]['handle'], 1, 4, None, None, C.byref(old), None, C.byref(descriptor))
        if status:
            raise BoundaryUnavailable('acl_read:' + str(status))
        control, revision = W.WORD(), W.DWORD()
        try:
            self._ok(self.a.GetSecurityDescriptorControl(descriptor, C.byref(control), C.byref(revision)), 'acl_control')
        except BaseException:
            self.k.LocalFree(descriptor)
            raise
        protection = 0x80000000 if control.value & 0x1000 else 0x20000000
        # Guarded nodes must not re-inherit a broad OWNER_RIGHTS ACE from an
        # unmodified parent while the package runs. Restore the original
        # protection state after removing this scope's grants.
        applied_protection = 0x80000000 if guard_owner else protection
        flags = 3 if inherit else 0
        entries = [Access(mask, 3 if deny else 1, flags, Trustee(None, 0, 0, 0, self.sid))]
        if guard_owner:
            # Narrowing OWNER_RIGHTS also removes the supervisor's data access
            # when a private tempfile tree grants access only through that SID.
            # Keep explicit supervisor file/administration rights, not merely
            # WRITE_DAC/WRITE_OWNER. The lowbox's additional restricted-SID
            # check still receives no package ACL/owner administration rights.
            entries += [Access(0x1f01ff, 1, flags, Trustee(None, 0, 0, 1, self.host_sid)),
                        Access(0x20000, 2, flags, Trustee(None, 0, 0, 5, self.owner_sid))]
        if read_only:
            entries.append(Access(0xd0156, 3, flags, Trustee(None, 0, 0, 0, self.sid)))
        access = (Access * len(entries))(*entries)
        try:
            status = self.a.SetEntriesInAclW(len(entries), access, old, C.byref(new))
            if status:
                raise BoundaryUnavailable('acl_merge:' + str(status))
            self.changed = True
            status = self.a.SetSecurityInfo(self.snapshots[path]['handle'], 1, 4 | applied_protection, None, None, new, None)
            if status:
                raise BoundaryUnavailable('acl_grant:' + str(status))
        finally:
            if new:
                self.k.LocalFree(new)
            if descriptor:
                self.k.LocalFree(descriptor)


    def __enter__(self):
        result = self.u.CreateAppContainerProfile(self.name, self.name, 'Offline CAD benchmark boundary', None, 0, C.byref(self.sid))
        if result != 0:
            raise BoundaryUnavailable('appcontainer_profile:' + hex(result & 0xffffffff))
        try:
            self._acl_principals()
            self._prepare_security()
            # All snapshots and rollback handles already exist, including every
            # child whose inherited descriptor a parent setter can modify.
            # MODIFY for descendants, but no package ACL/owner administration.
            # Root DELETE/DELETE_CHILD are denied independently: an immutable
            # inputs directory cannot be renamed away through its parent.
            self._acl(self.scratch, 0x1301bf, inherit=True, guard_owner=True)
            self._acl(self.scratch, 0xd0040, deny=True)
            inputs = self.scratch / 'inputs'
            if inputs.is_dir():
                self._acl(inputs, 0x1200a9, inherit=True, guard_owner=True, read_only=True)
            self._acl(self.runtime, 0x1200a9, guard_owner=True, read_only=True)
            for path in self.runtime.rglob('*'):
                self._acl(path, 0x1200a9, guard_owner=True, read_only=True)
            for path in self.read_files:
                self._acl(path, 0x120089, guard_owner=True, read_only=True)
            self.entered = True
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        errors = []
        for job in self.handles:
            if not self.k.TerminateJobObject(job, 1):
                errors.append('job_cleanup')
            self.k.CloseHandle(job)
        self.handles.clear()
        errors.extend(self._restore_security())
        if self.owner_sid:
            self.k.LocalFree(self.owner_sid)
            self.owner_sid = C.c_void_p()
        self.host_sid, self.host_sid_buffer = C.c_void_p(), None
        if self.sid:
            self.a.FreeSid(self.sid)
            self.sid = C.c_void_p()
        if self.u.DeleteAppContainerProfile(self.name) != 0:
            errors.append('profile_cleanup')
        self.entered = False
        if errors:
            raise BoundaryUnavailable(';'.join(errors))

    def _lpac_access(self, token):
        """Attest effective package access, without the unsupported class-46 query."""
        class Mapping(C.Structure):
            _fields_ = [('read', W.DWORD), ('write', W.DWORD), ('execute', W.DWORD), ('all', W.DWORD)]
        P = C.c_void_p
        self.a.DuplicateToken.argtypes = [P, C.c_int, C.POINTER(P)]
        self.a.ConvertSidToStringSidW.argtypes = [P, C.POINTER(W.LPWSTR)]
        self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [W.LPCWSTR, W.DWORD, C.POINTER(P), P]
        self.a.AccessCheck.argtypes = [P, P, W.DWORD, C.POINTER(Mapping), P,
                                      C.POINTER(W.DWORD), C.POINTER(W.DWORD), C.POINTER(W.BOOL)]
        duplicate, package_text = P(), W.LPWSTR()
        self._ok(self.a.DuplicateToken(token, 2, C.byref(duplicate)), 'lpac_probe_token')
        try:
            self._ok(self.a.ConvertSidToStringSidW(self.sid, C.byref(package_text)), 'lpac_probe_sid')
            mapping = Mapping(0x120089, 0x120116, 0x1200a0, 0x1f01ff)
            probes = {}
            for name, extra, expected in (
                    ('world_only_read', '', False),
                    ('all_application_packages_read', '(A;;0x1;;;S-1-15-2-1)', False),
                    ('own_package_read', '(A;;0x1;;;' + package_text.value + ')', True)):
                descriptor = P()
                try:
                    sddl = 'O:SYG:SYD:(A;;0x1;;;WD)' + extra
                    self._ok(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                        sddl, 1, C.byref(descriptor), None), 'lpac_probe_descriptor')
                    required, granted, allowed = W.DWORD(), W.DWORD(), W.BOOL()
                    ok = self.a.AccessCheck(descriptor, duplicate, 1, C.byref(mapping), None,
                                            C.byref(required), C.byref(granted), C.byref(allowed))
                    if not ok:
                        error = C.get_last_error()
                        if error != 122 or not required.value:
                            raise BoundaryUnavailable('lpac_accesscheck_size:' + str(error))
                        privileges = C.create_string_buffer(required.value)
                        self._ok(self.a.AccessCheck(descriptor, duplicate, 1, C.byref(mapping), privileges,
                            C.byref(required), C.byref(granted), C.byref(allowed)), 'lpac_accesscheck')
                    probes[name] = bool(allowed.value)
                    if probes[name] != expected:
                        raise BoundaryUnavailable('child_lpac_access_semantics:' + name)
                finally:
                    if descriptor:
                        self.k.LocalFree(descriptor)
            return dict(schema='cad-harness.lpac-accesscheck.v1', **probes)
        finally:
            if package_text:
                self.k.LocalFree(package_text)
            self.k.CloseHandle(duplicate)

    def _verify_token(self, process):
        token = C.c_void_p()
        self.a.OpenProcessToken.argtypes = [C.c_void_p, W.DWORD, C.POINTER(C.c_void_p)]
        self.a.GetTokenInformation.argtypes = [C.c_void_p, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)]
        self.a.EqualSid.argtypes = [C.c_void_p, C.c_void_p]
        self._ok(self.a.OpenProcessToken(process, 0xa, C.byref(token)), 'open_child_token')
        try:
            value, size = W.DWORD(), W.DWORD()
            self._ok(self.a.GetTokenInformation(token, 29, C.byref(value), C.sizeof(value), C.byref(size)), 'child_token_appcontainer')
            if not value.value:
                raise BoundaryUnavailable('child_not_appcontainer')
            for info in (30, 31):
                size = W.DWORD()
                self.a.GetTokenInformation(token, info, None, 0, C.byref(size))
                buffer = C.create_string_buffer(size.value)
                self._ok(self.a.GetTokenInformation(token, info, buffer, size.value, C.byref(size)), 'child_token_scope')
                if info == 30 and C.cast(buffer, C.POINTER(W.DWORD)).contents.value != 0:
                    raise BoundaryUnavailable('child_capabilities_not_empty')
                if info == 31 and not self.a.EqualSid(C.cast(buffer, C.POINTER(C.c_void_p)).contents, self.sid):
                    raise BoundaryUnavailable('child_appcontainer_sid_mismatch')
            return self._lpac_access(token)
        finally:
            self.k.CloseHandle(token)

    def run(self, argv, *, stdout, stderr, timeout):
        self.last_receipt = None
        if not self.entered or timeout <= 0:
            raise BoundaryUnavailable('boundary_not_entered_or_expired')
        if not argv or Path(argv[0]).resolve() not in (self.python.resolve(), Path(os.environ['SystemRoot'], 'System32/cmd.exe').resolve()):
            raise BoundaryUnavailable('boundary_executable_not_allowed')
        class SA(C.Structure):
            _fields_ = [('length', W.DWORD), ('descriptor', C.c_void_p), ('inherit', W.BOOL)]
        class SI(C.Structure):
            _fields_ = [('cb', W.DWORD), ('reserved', W.LPWSTR), ('desktop', W.LPWSTR), ('title', W.LPWSTR),
                        ('x', W.DWORD), ('y', W.DWORD), ('xs', W.DWORD), ('ys', W.DWORD),
                        ('xc', W.DWORD), ('yc', W.DWORD), ('fill', W.DWORD), ('flags', W.DWORD),
                        ('show', W.WORD), ('reserved2size', W.WORD), ('reserved2', C.c_void_p),
                        ('stdin', C.c_void_p), ('stdout', C.c_void_p), ('stderr', C.c_void_p)]
        class SIX(C.Structure):
            _fields_ = [('startup', SI), ('attributes', C.c_void_p)]
        class PI(C.Structure):
            _fields_ = [('process', C.c_void_p), ('thread', C.c_void_p), ('pid', W.DWORD), ('tid', W.DWORD)]
        class Caps(C.Structure):
            _fields_ = [('sid', C.c_void_p), ('caps', C.c_void_p), ('count', W.DWORD), ('reserved', W.DWORD)]
        class Basic(C.Structure):
            _fields_ = [('process_time', C.c_int64), ('job_time', C.c_int64), ('flags', W.DWORD),
                        ('minws', C.c_size_t), ('maxws', C.c_size_t), ('active', W.DWORD),
                        ('affinity', C.c_size_t), ('priority', W.DWORD), ('scheduling', W.DWORD)]
        class IO(C.Structure):
            _fields_ = [(name, C.c_uint64) for name in ('readops', 'writeops', 'otherops', 'readbytes', 'writebytes', 'otherbytes')]
        class Limits(C.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_memory', C.c_size_t), ('job_memory', C.c_size_t),
                        ('peak_process', C.c_size_t), ('peak_job', C.c_size_t)]
        job = self._ok(self.k.CreateJobObjectW(None, None), 'create_job')
        self.handles.append(job)
        limits = Limits()
        limits.basic.flags, limits.basic.active = 0x2008, 1  # KILL_ON_JOB_CLOSE | ACTIVE_PROCESS
        self._ok(self.k.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)), 'job_limits')
        ui = W.DWORD(0xff)
        self._ok(self.k.SetInformationJobObject(job, 4, C.byref(ui), C.sizeof(ui)), 'job_ui_limits')
        handles, attrs, created = [], None, False
        process = PI()
        start = self.wall()
        receipt, cleanup_error, verified, assigned = None, None, False, False
        token_evidence = None
        try:
            sa = SA(C.sizeof(SA), None, True)
            for name, access in (('NUL', 0x80000000), (str(stdout), 0x40000000), (str(stderr), 0x40000000)):
                handle = self.k.CreateFileW(name, access, 3, C.byref(sa), 3 if name == 'NUL' else 2, 0x80, None)
                if handle == C.c_void_p(-1).value:
                    raise BoundaryUnavailable('capture_handle:' + str(C.get_last_error()))
                handles.append(handle)
            size = C.c_size_t()
            self.k.InitializeProcThreadAttributeList(None, 5, 0, C.byref(size))
            attrs = C.create_string_buffer(size.value)
            self._ok(self.k.InitializeProcThreadAttributeList(attrs, 5, 0, C.byref(size)), 'attribute_list')
            caps, child, lpac = Caps(self.sid, None, 0, 0), W.DWORD(1), W.DWORD(1)
            mitigation = C.c_uint64((1 << 28) | (1 << 32))
            inherited = (C.c_void_p * len(handles))(*handles)
            for key, value in ((0x20009, caps), (0x2000e, child), (0x2000f, lpac),
                               (0x20007, mitigation), (0x20002, inherited)):
                self._ok(self.k.UpdateProcThreadAttribute(attrs, 0, key, C.byref(value), C.sizeof(value), None, None), 'boundary_attribute:' + hex(key))
            si = SIX()
            si.startup.cb, si.attributes = C.sizeof(SIX), C.cast(attrs, C.c_void_p)
            si.startup.flags = 0x100
            si.startup.stdin, si.startup.stdout, si.startup.stderr = handles
            environment = {'SystemRoot': os.environ['SystemRoot'], 'WINDIR': os.environ['SystemRoot'],
                           'TEMP': str(self.scratch), 'TMP': str(self.scratch), 'HOME': str(self.scratch),
                           'USERPROFILE': str(self.scratch), 'LOCALAPPDATA': str(self.scratch),
                           'PATH': str(self.runtime / 'bin'), 'PYTHONNOUSERSITE': '1', 'QT_QPA_PLATFORM': 'offscreen'}
            block = C.create_unicode_buffer('\0'.join(k + '=' + v for k, v in sorted(environment.items())) + '\0\0')
            command = C.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in argv]))
            flags = 0x80000 | 0x400 | 0x4 | 0x8  # EXTENDED | UNICODE | SUSPENDED | DETACHED
            self._ok(self.k.CreateProcessW(str(argv[0]), command, None, None, True, flags, block,
                                          str(self.scratch), C.byref(si), C.byref(process)), 'lpac_create_process')
            created = True
            self._ok(self.k.AssignProcessToJobObject(job, process.process), 'job_assign')
            assigned = True
            token_evidence = self._verify_token(process.process)
            verified = True
            if self.wall() - start >= timeout:
                raise TimeoutError('bare_tool_timeout')
            if self.k.ResumeThread(process.thread) == 0xffffffff:
                raise BoundaryUnavailable('resume_process')
            remaining = timeout - (self.wall() - start)
            if remaining <= 0:
                raise TimeoutError('bare_tool_timeout')
            wait = self.k.WaitForSingleObject(process.process, min(int(remaining * 1000), 0xfffffffe))
            if wait == 0x102:
                raise TimeoutError('bare_tool_timeout')
            if wait != 0:
                raise BoundaryUnavailable('process_wait:' + str(wait))
            code = W.DWORD()
            self._ok(self.k.GetExitCodeProcess(process.process, C.byref(code)), 'process_exit')
            receipt = {'returncode': code.value, 'pid': process.pid, 'start': start, 'end': self.wall(),
                       'isolation': 'windows_lpac_zero_capabilities', 'job_child_limit': 1, 'stdin': 'NUL',
                       'lpac_token_verified': True, 'lpac_token_evidence': token_evidence,
                       'capability_count': 0, 'cleanup_status': 'pending',
                       'stdout': str(stdout), 'stderr': str(stderr)}
            return receipt
        finally:
            # TerminateProcess covers failures before job assignment too.
            if created:
                self.k.TerminateJobObject(job, 1)
                self.k.TerminateProcess.argtypes = [C.c_void_p, W.UINT]
                self.k.TerminateProcess(process.process, 1)
                if self.k.WaitForSingleObject(process.process, 30000) != 0:
                    cleanup_error = 'owned_process_cleanup_timeout'
                self.k.CloseHandle(process.thread)
                self.k.CloseHandle(process.process)
            if attrs is not None:
                self.k.DeleteProcThreadAttributeList(attrs)
            for handle in handles:
                self.k.CloseHandle(handle)
            self.k.CloseHandle(job)
            self.handles.remove(job)
            if receipt is None:
                receipt = {'pid': process.pid if created else None, 'start': start,
                           'isolation': 'windows_lpac_zero_capabilities',
                           'job_child_limit': 1, 'job_assigned': assigned, 'stdin': 'NUL',
                           'lpac_token_verified': verified, 'lpac_token_evidence': token_evidence,
                           'capability_count': 0 if verified else None,
                           'stdout': str(stdout), 'stderr': str(stderr)}
            receipt.update(end=self.wall(), job_assigned=assigned,
                           cleanup_status='failed' if cleanup_error else 'exited' if created else 'not_created')
            self.last_receipt = receipt
            if cleanup_error:
                raise BoundaryUnavailable(cleanup_error)
