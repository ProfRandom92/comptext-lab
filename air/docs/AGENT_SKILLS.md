# Agent Skills

CompText AIR includes a repository-local agent skill pack.

The skill pack is not an official Gemini plugin, MCP server, provider runtime, or package distribution.

It is a local instruction layer for agents that work on this repository.

## Files

- `.agent/skills/comptext-air/SKILL.md`
- `agent_prompts/GEMINI_AIR_VALIDATION_PROMPT.md`
- `agent_prompts/CODEX_AIR_VALIDATION_PROMPT.md`

## Purpose

The skill pack gives agents a stable read order, repository map, validation commands, and safety boundaries.

It helps prevent:

- provider runtime overclaims
- MCP support overclaims
- fake hashes
- simulated evidence being described as real
- hidden chain-of-thought capture
- stale validation reports
- unsafe adapter claims

## Required validation

Agents must run:

python scripts/validate_json.py
python scripts/validate_air_fixtures.py
python scripts/validate_evidence_fixtures.py
python scripts/validate_replay_contracts.py
python scripts/validate_adapter_fixtures.py

## Boundary

This repository remains an AIR contract, evidence, replay, adapter-description, and validation project.

It does not become a provider runtime, MCP runtime, package registry, or legal/compliance/forensic assurance product.
