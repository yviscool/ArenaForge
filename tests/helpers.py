from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

TEST_WORKDIR_ROOT = Path(".test-workdir")


@contextmanager
def local_test_workspace(prefix: str):
    TEST_WORKDIR_ROOT.mkdir(parents=True, exist_ok=True)
    workspace = TEST_WORKDIR_ROOT / f"{prefix}-{uuid.uuid4().hex}"
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
