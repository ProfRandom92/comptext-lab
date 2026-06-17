#!/usr/bin/env python3
"""Generate a deterministic agent artifact bundle example."""

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

ARTIFACT_ID = "agent_artifact_bundle_example_v1"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "agent_artifact_bundle_example.json"

EXAMPLE_STATE = GateState(
    branch="feat/agent-artifact-bundle-example",
    status_short=(),
    changed_paths=(
        "artifacts/agent_artifact_bundle_example.json",
        "scripts/generate_agent_artifact_bundle_example.py",
        "tests/test_agent_artifact_bundle.py",
    ),
)
VALIDATION_COMMANDS = [
    "python -m compileall -q scripts/agent_artifact_bundle.py scripts/generate_agent_artifact_bundle_example.py",
    "pytest tests/test_agent_artifact_bundle.py -q",
]
VALIDATION_RESULTS = ["pass", "pass"]
MCP_CONTEXT_OUTPUT_REF = "artifacts/mcp_context_layer_example.json"


def build_agent_artifact_bundle_example() -> dict[str, Any]:
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
        "generated_by": "AgentArtifactBundleExampleGenerator",
        "llm_judges": "none",
        "schema_version": "agent_artifact_bundle_example.v1",
        "version": "1.0",
    }


def generate_agent_artifact_bundle_example(output_path: Path = OUTPUT_PATH) -> Path:
    artifact = build_agent_artifact_bundle_example()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    output_path = generate_agent_artifact_bundle_example()
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
