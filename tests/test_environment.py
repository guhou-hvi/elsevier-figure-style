from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import check_environment


def test_environment_report_is_ready() -> None:
    report = check_environment.environment_report()
    assert report["status"] == "PASS"
    assert report["python"]["ok"] is True
    assert report["requirements_file_found"] is True
    assert report["missing"] == []
    assert report["outdated"] == {}


def test_environment_cli_json(root: Path) -> None:
    script = root / "skills/elsevier-figure-style/scripts/check_environment.py"
    result = subprocess.run(
        [sys.executable, str(script), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert Path(payload["requirements_path"]).is_file()
