from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "elsevier-figure-style"
SCRIPTS = SKILL / "scripts"
PROFILE = SKILL / "assets" / "elsevier_figure_style.json"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def root() -> Path:
    return ROOT


@pytest.fixture
def skill() -> Path:
    return SKILL


@pytest.fixture
def profile_path() -> Path:
    return PROFILE
