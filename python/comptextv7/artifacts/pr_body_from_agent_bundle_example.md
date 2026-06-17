## Summary

Deterministic agent artifact bundle evidence for this change.

## Scope

- `artifacts/agent_artifact_bundle_example.json`
- `scripts/generate_agent_artifact_bundle_example.py`
- `tests/test_agent_artifact_bundle.py`

## Validation

- `python -m compileall -q scripts/agent_artifact_bundle.py scripts/generate_agent_artifact_bundle_example.py`: `pass`
- `pytest tests/test_agent_artifact_bundle.py -q`: `pass`

## Safety Gate

- result: `PASS`
- ok: `true`
- allow_dirty: `false`
- problems: `none`

## Evidence

- branch: `feat/agent-artifact-bundle-example`
- bundle_result: `PASS`
- mcp_context_output_ref: `artifacts/mcp_context_layer_example.json`
