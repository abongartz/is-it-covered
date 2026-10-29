import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv not available")
def test_app_requirements_match_lockfile():
    """app/requirements.txt (read by the host) must be exported from uv.lock, without offline-only groups."""
    exported = subprocess.run(
        [
            "uv",
            "export",
            "--format",
            "requirements-txt",
            "--no-dev",
            "--no-emit-project",
            "--locked",
            "--no-header",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    committed = (ROOT / "app" / "requirements.txt").read_text(encoding="utf-8")
    body = "\n".join(line for line in committed.splitlines() if not line.startswith("#"))
    assert body.strip() == "\n".join(exported.splitlines()).strip().replace("\r", "")
    assert "pymupdf" not in body.lower()
