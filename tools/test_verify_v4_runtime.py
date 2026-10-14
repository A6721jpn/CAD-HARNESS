"""Integrity controls using synthetic executable bytes, never CAD evidence."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

if __package__:
    from . import cad_verify_v4_runtime as runtime
else:
    import cad_verify_v4_runtime as runtime


class RuntimeBinding(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cad-runtime-integrity-')
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.root,self.sdk=self.base/'repo',self.base/'sdk'
        (self.root/'tools/__pycache__').mkdir(parents=True)
        (self.root/'skills/cad-harness-v4').mkdir(parents=True)
        (self.sdk/'Lib/pkg/__pycache__').mkdir(parents=True)
        (self.sdk/'bin').mkdir()
        self.source=self.sdk/'Lib/pkg/module.py';self.source.write_bytes(b'value = 1\n')
        self.cache=self.sdk/'Lib/pkg/__pycache__/module.cpython-311.pyc'
        self.cache.write_bytes(b'unchanged-header'+b'first executable payload')
        (self.sdk/'bin/python.exe').write_bytes(b'synthetic interpreter identity; not executed')
        self.repo_cache=self.root/'tools/__pycache__/driver.cpython-311.pyc'
        self.repo_cache.write_bytes(b'synthetic repository cache')
        self.extension=self.base/'independent_feature.py';self.extension.write_bytes(b'parameter = 1\n')
        self.extension_cache=self.base/'__pycache__';self.extension_cache.mkdir()
        self.extension_cache=self.extension_cache/'independent_feature.cpython-311.pyc'
        self.extension_cache.write_bytes(b'original extension cache')
        replacement=patch.object(runtime.cad_run,'FREECAD_DIR',self.sdk)
        replacement.start();self.addCleanup(replacement.stop)

    def snapshot(self):
        return runtime.capture(self.root,extension_paths=[self.extension])

    def test_changed_executable_cache_fails_with_identical_source_and_header(self):
        snapshot=self.snapshot();source=self.source.read_bytes()
        header=self.cache.read_bytes()[:16]
        self.cache.write_bytes(header+b'different executable payload')
        self.assertEqual(self.source.read_bytes(),source)
        with self.assertRaisesRegex(ValueError,'runtime_binding_changed'):
            runtime.verify(snapshot,root=self.root,extension_paths=[self.extension])

    def test_added_removed_or_changed_library_inputs_cannot_reuse_snapshot(self):
        snapshot=self.snapshot()
        added=self.sdk/'bin/new-library.dll';added.write_bytes(b'new native library')
        with self.assertRaisesRegex(ValueError,'runtime_binding_changed'):
            runtime.verify(snapshot,root=self.root,extension_paths=[self.extension])
        added.unlink();self.source.unlink()
        with self.assertRaisesRegex(ValueError,'runtime_binding_changed'):
            runtime.verify(snapshot,root=self.root,extension_paths=[self.extension])

    def test_repository_and_independent_extension_caches_are_execution_inputs(self):
        for path in (self.repo_cache,self.extension_cache,self.extension):
            snapshot=self.snapshot();original=path.read_bytes()
            path.write_bytes(original+b' changed')
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'runtime_binding_changed'):
                runtime.verify(snapshot,root=self.root,extension_paths=[self.extension],native_files=snapshot['native_files'])
            path.write_bytes(original)

    def test_forbidden_root_is_rejected_before_metadata(self):
        with patch.object(Path,'lstat',side_effect=AssertionError('private metadata lookup')):
            with self.assertRaises(ValueError):
                runtime.capture(self.base/'pilot-user')


if __name__=='__main__':
    unittest.main()
