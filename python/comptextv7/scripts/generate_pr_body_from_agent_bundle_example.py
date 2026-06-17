#!/usr/bin/env python3
"""Generate a deterministic PR body Markdown example from an agent bundle."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.pr_body_from_agent_bundle import render_pr_body_from_file

INPUT_BUNDLE_PATH = REPO_ROOT / "artifacts" / "agent_artifact_bundle_example.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "pr_body_from_agent_bundle_example.md"


def generate_pr_body_from_agent_bundle_example(output_path: Path = OUTPUT_PATH) -> Path:
    rendered = render_pr_body_from_file(INPUT_BUNDLE_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_pr_body_from_agent_bundle_example()
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
