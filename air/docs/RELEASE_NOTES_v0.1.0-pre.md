# CompText AIR v0.1.0-pre

**Status:** Pre-release / Public Review Candidate

## Summary

CompText AIR v0.1.0-pre is the first public review candidate for the Agent Intermediate Representation layer. This release establishes a validated baseline for representing agent intent, runtime evidence, and replay contracts. It provides a formal, hash-linked foundation for agent auditability without relying on internal chain-of-thought capture.

## Validated Components

- **AIR schema:** Formal definition of agent intent, goals, and pipelines.
- **Evidence schema:** Hash-chained runtime event representation.
- **Adapter schema:** Descriptive mapping for runtime environments.
- **AIR fixtures:** Validated examples of agent plans.
- **Evidence fixtures:** Real SHA-256 hash-chained event sequences.
- **Canonical SHA-256 evidence hashing:** Deterministic hashing using the `json-c14n-v1` profile.
- **Replay contract validation:** Verified fulfillment of AIR plans by Evidence trails.
- **Negative adapter validation:** Explicit blocking of forbidden claims and unsafe configurations.
- **Deterministic generated audit reports:** Path-neutral, machine-readable validation artifacts.
- **Agent skill pack:** Repository-local instructions for Gemini, Codex, and other agents.

## Safety Boundary

This pre-release is a **contract and representation layer only**. The following are explicitly **not** included or claimed:

- **No provider runtime:** No implementation for executing plans against model APIs.
- **No production MCP support:** No production-ready MCP server implementation.
- **No hidden chain-of-thought capture:** No attempt to verify internal model "thinking".
- **No package publishing:** Not available via npm, pip, or other registries.
- **No legal/compliance/forensic assurance:** Technical validation only; no legal guarantees.

## Verification Commands

To verify the integrity of this release candidate, run the following in a local environment:

```bash
python scripts/validate_json.py
python scripts/validate_air_fixtures.py
python scripts/validate_evidence_fixtures.py
python scripts/validate_replay_contracts.py
python scripts/validate_adapter_fixtures.py
```

## Known Limitations

- Offline-only validation.
- Minimal example fixtures for hash-chains.
- Heuristic mapping for replay contract fulfillment.
- No automated execution engine.

## Intended Reviewers

- Agent architects and developers.
- AI safety researchers.
- Audit and transparency tool builders.
- CompText ecosystem contributors.
