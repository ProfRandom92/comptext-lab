#!/usr/bin/env python3
"""Generate a deterministic bundle example that references MCP context output."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_artifact_bundle import build_agent_artifact_bundle
from scripts.safe_pr_gate import GateState

ARTIFACT_ID = "mcp_context_bundle_ref_example_v1"
MCP_CONTEXT_OUTPUT_REF = "artifacts/mcp_context_layer_example.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "mcp_context_bundle_ref_example.json"

EXAMPLE_STATE = GateState(
    branch="feat/mcp-context-bundle-ref-example",
    status_short=(),
    changed_paths=(
        "artifacts/mcp_context_bundle_ref_example.json",
        "scripts/generate_mcp_context_bundle_ref_example.py",
        "tests/test_agent_artifact_bundle.py",
    ),
)
VALIDATION_COMMANDS = [
    "python -m compileall -q scripts/agent_artifact_bundle.py scripts/generate_mcp_context_bundle_ref_example.py",
    "pytest tests/test_agent_artifact_bundle.py -q",
    "python scripts/validate_agent_artifact_bundle.py --bundle artifacts/mcp_context_bundle_ref_example.json",
]
VALIDATION_RESULTS = ["pass", "pass", "pass"]


def build_mcp_context_bundle_ref_example() -> dict[str, Any]:
    return {
        "artifact_id": ARTIFACT_ID,
        "bundle": build_agent_artifact_bundle(
            EXAMPLE_STATE,
            allow_main=False,
            validation_commands=VALIDATION_COMMANDS,
            validation_results=VALIDATION_RESULTS,
            mcp_context_output_ref=MCP_CONTEXT_OUTPUT_REF,
        ),
        "evaluation_mode": "deterministic",
        "external_apis": "none",
        "generated_by": "McpContextBundleRefExampleGenerator",
        "llm_judges": "none",
        "schema_version": "mcp_context_bundle_ref_example.v1",
        "version": "1.0",
    }


def generate_mcp_context_bundle_ref_example(output_path: Path = OUTPUT_PATH) -> Path:
    artifact = build_mcp_context_bundle_ref_example()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_mcp_context_bundle_ref_example()
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
