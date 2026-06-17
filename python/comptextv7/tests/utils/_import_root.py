"""Shared import helper for direct benchmark/replay script execution."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_repo_root_on_path() -> None:
    """Add the repository root to ``sys.path`` once for local script imports."""

    repo_root = Path(__file__).resolve().parents[2]
    root = str(repo_root)
    if root not in sys.path:
        sys.path.insert(0, root)
