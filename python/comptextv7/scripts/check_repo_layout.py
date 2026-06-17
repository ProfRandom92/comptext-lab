"""Validate the expected repository layout.

The repository root has a minimal package.json command wrapper. Dashboard
remains the real Node app directory.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    REPO_ROOT / "package.json",
    REPO_ROOT / "dashboard" / "app" / "package.json",
    REPO_ROOT / "artifacts" / "paper_replay_results.json",
    REPO_ROOT / "artifacts" / "agent_trace_replay_results.json",
    REPO_ROOT / "artifacts" / "replay" / "exec-sample.replay.json",
)


def check_repo_layout() -> list[str]:
    """Return human-readable layout errors for missing required files."""
    errors = [
        f"missing required file: {path.relative_to(REPO_ROOT)}"
        for path in REQUIRED_FILES
        if not path.is_file()
    ]

    return errors


def main() -> int:
    errors = check_repo_layout()
    if errors:
        for error in errors:
            print(error)
        return 1

    print("repository layout OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
