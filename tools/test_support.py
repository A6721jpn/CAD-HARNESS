"""Offline temp directories inherit workspace ACLs on managed Windows hosts."""
import os
from pathlib import Path
import tempfile
from unittest.mock import patch


def start_tempdirs():
    base = Path(__file__).resolve().parents[1] / ".tmp" / "unittest-mvp1"
    base.mkdir(parents=True, exist_ok=True)
    real_mkdir = os.mkdir

    def mkdir(path, mode=0o777, **kwargs):
        # Python 3.12's private 0700 ACL excludes the restricted sandbox token.
        # Inherit existing ACLs only within the already writable test directory.
        if mode == 0o700 and Path(path).absolute().is_relative_to(base):
            mode = 0o777
        return real_mkdir(path, mode, **kwargs)

    patches = [patch.object(tempfile, "tempdir", str(base)), patch.object(os, "mkdir", mkdir)]
    for item in patches:
        item.start()
    return patches


def stop_tempdirs(patches):
    for item in reversed(patches):
        item.stop()
