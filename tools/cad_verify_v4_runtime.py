"""Host-safe execution bindings for the pinned SDK, including readable bytecode.

-B prevents cache writes, not cache reads. Snapshot existing caches as executable
inputs, alongside sources/libraries/config. This records integrity, not an OS
sandbox or a cryptographic attestation of another machine's execution.
"""
import hashlib
import os
from pathlib import Path
import re
import stat

if __package__:
    from . import cad_run, cad_verify_v4_inputs as inputs
else:
    import cad_run, cad_verify_v4_inputs as inputs

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {'.py', '.pyc', '.pyo', '.pyd', '.dll', '.so', '.exe', '.zip', '.json',
            '.pth', '.qml', '.js', '.rcc'}
CACHE_SUFFIXES = {'.pyc', '.pyo'}
FIELDS = {'schema', 'root', 'sdk_root', 'native_files', 'repository_caches', 'extension_files'}


def _root(path):
    return inputs.guarded_path(path, regular=False)


def _sha(path):
    path = inputs.guarded_path(path)
    before = path.stat()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if key(before) != key(after):
        raise ValueError('runtime_file_changed_during_hash')
    return str(path), digest


def _tree(root, suffixes):
    result = {}
    root = _root(root)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    directory_identity = lambda s: (s.st_dev, s.st_ino, s.st_mode,
        getattr(s, 'st_file_attributes', 0), s.st_mtime_ns, s.st_ctime_ns)

    def visit(directory):
        before_directory = directory.lstat()
        if stat.S_ISLNK(before_directory.st_mode) or getattr(before_directory, 'st_file_attributes', 0) & 0x400:
            raise ValueError('linked_runtime_directory')
        with os.scandir(directory) as entries:
            for entry in entries:
                # The guarded ancestor is already open. Real entry names avoid
                # repeated ancestor resolution/stat for every SDK file.
                inputs._lexical(entry.name)
                if entry.is_symlink():
                    raise ValueError('linked_runtime_entry')
                selected = Path(entry.name).suffix.casefold() in suffixes
                is_directory = entry.is_dir(follow_symlinks=False)
                if not is_directory and not selected:
                    continue
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                    raise ValueError('linked_runtime_entry')
                path = directory / entry.name
                if is_directory:
                    visit(path)
                else:
                    if not stat.S_ISREG(info.st_mode):
                        raise ValueError('runtime_input_not_regular')
                    before = path.lstat()
                    if stat.S_ISLNK(before.st_mode) or getattr(before, 'st_file_attributes', 0) & 0x400:
                        raise ValueError('linked_runtime_entry')
                    with path.open('rb') as stream:
                        opened = os.fstat(stream.fileno())
                        # Windows DirEntry caches omit inode/device; fstat and
                        # lstat also expose different ctime semantics. Compare
                        # like APIs for change-time, common fields across APIs.
                        common = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
                        if common(opened) != common(before):
                            raise ValueError('runtime_file_replaced_before_hash')
                        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                        if identity(opened) != identity(os.fstat(stream.fileno())):
                            raise ValueError('runtime_file_changed_during_hash')
                    if identity(before) != identity(path.lstat()):
                        raise ValueError('runtime_file_changed_during_hash')
                    result[str(path)] = digest
        after_directory = directory.lstat()
        # Windows may populate directory allocation size only after enumeration;
        # it is not a content identity. File sizes remain strictly compared.
        if directory_identity(before_directory) != directory_identity(after_directory):
            raise ValueError('runtime_directory_changed_during_hash:' + str(directory))

    visit(root)
    return dict(sorted(result.items()))


def native_files(sdk_root=None):
    """Complete executable-source/cache/library/config inventory of the SDK."""
    value = _tree(cad_run.FREECAD_DIR if sdk_root is None else sdk_root, SUFFIXES)
    if not value:
        raise ValueError('runtime_native_inventory_empty')
    return value


def repository_caches(root=ROOT):
    root = _root(root)
    value = {}
    for name in ('tools', 'skills/cad-harness-v4'):
        directory = root / name
        inputs._lexical(directory)
        if directory.exists():
            value.update(_tree(directory, CACHE_SUFFIXES))
    return dict(sorted(value.items()))


def extension_files(paths):
    result = {}
    for raw in paths:
        source = inputs.guarded_path(raw)
        if source.suffix != '.py':
            raise ValueError('runtime_extension_source_type')
        key, value = _sha(source)
        result[key] = value
        for suffix in CACHE_SUFFIXES:
            adjacent = source.with_suffix(suffix)
            if adjacent.exists():
                key, value = _sha(adjacent)
                result[key] = value
        cache = source.parent / '__pycache__'
        if cache.exists():
            cache = _root(cache)
            for path in cache.iterdir():
                if path.name.startswith(source.stem + '.') and path.suffix.casefold() in CACHE_SUFFIXES:
                    key, value = _sha(path)
                    result[key] = value
    return dict(sorted(result.items()))


def capture(root=ROOT, *, extension_paths=()):
    root, sdk = _root(root), _root(cad_run.FREECAD_DIR)
    return dict(schema='cad-harness.runtime-binding.v4', root=str(root), sdk_root=str(sdk),
                native_files=native_files(sdk), repository_caches=repository_caches(root),
                extension_files=extension_files(extension_paths))


def verify(snapshot, *, root=ROOT, extension_paths=(), native_files=None):
    """Recheck all identities; optional SDK map must already be trusted/verified."""
    root, sdk = _root(root), _root(cad_run.FREECAD_DIR)
    if (not isinstance(snapshot, dict) or set(snapshot) != FIELDS
            or snapshot['schema'] != 'cad-harness.runtime-binding.v4'
            or snapshot['root'] != str(root) or snapshot['sdk_root'] != str(sdk)):
        raise ValueError('runtime_binding_contract')
    for field in ('native_files', 'repository_caches', 'extension_files'):
        values = snapshot[field]
        if not isinstance(values, dict) or (field == 'native_files' and not values):
            raise ValueError('runtime_binding_inventory_contract')
        for name, digest in values.items():
            inputs._lexical(name)
            if not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None:
                raise ValueError('runtime_binding_digest_contract')
            path = Path(name)
            if not path.is_absolute() or (field == 'native_files' and not path.is_relative_to(sdk)):
                raise ValueError('runtime_binding_path_contract')
    if native_files is None:
        expected = capture(root, extension_paths=extension_paths)
    else:
        expected = dict(schema='cad-harness.runtime-binding.v4', root=str(root), sdk_root=str(sdk),
                        native_files=native_files, repository_caches=repository_caches(root),
                        extension_files=extension_files(extension_paths))
    if snapshot != expected:
        raise ValueError('runtime_binding_changed')
    return snapshot
