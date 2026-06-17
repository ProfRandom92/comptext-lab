<p align="center">
  <img src="assets/brand/comptext-air-readme-header.png" alt="CompText AIR - Agent Intermediate Representation" width="100%">
</p>

<div align="center">

![AIR: schema validated](https://img.shields.io/badge/AIR-schema%20validated-blue)
![Evidence: hash chained](https://img.shields.io/badge/evidence-hash%20chained-brightgreen)
![Replay: contracts](https://img.shields.io/badge/replay-contracts-purple)
![Adapters: descriptive only](https://img.shields.io/badge/adapters-descriptive%20only-lightgrey)
![Audit reports: deterministic](https://img.shields.io/badge/audit%20reports-deterministic-brightgreen)
![Agent skills: local](https://img.shields.io/badge/agent%20skills-local-blue)
![Network: offline only](https://img.shields.io/badge/network-offline%20only-red)
![Provider runtime: not implemented](https://img.shields.io/badge/provider%20runtime-not%20implemented-lightgrey)
![MCP: not claimed](https://img.shields.io/badge/MCP-not%20claimed-lightgrey)
![CoT capture: disabled](https://img.shields.io/badge/CoT%20capture-disabled-lightgrey)

</div>

# CompText AIR

Agent Intermediate Representation for CompText.

CompText AIR separates agent intent from runtime evidence. The goal is not to preserve or expose hidden chain-of-thought. The goal is to make agent work auditable through explicit plans, evidence events, replay contracts, and reproducible hashes.

> If chain-of-thought becomes unreadable, replay becomes the safety primitive.

## Architecture

```text
Natural Language
  <-> CompText AIR
  <-> LLM / Codex / Agent Runtime
  <-> Evidence Events
  <-> Replay / Hash Chain
  <-> Natural Language Summary
```

See:
- [AIR vs Evidence](docs/AIR_VS_EVIDENCE.md)
- [Replay Contracts](docs/REPLAY_CONTRACTS.md)
- [Runtime Adapters](docs/RUNTIME_ADAPTERS.md)
- [Audit Reports](docs/AUDIT_REPORTS.md)

## Current status

Phase 12 is validated.

Implemented:

- AIR intent/plan schema
- Evidence event schema
- Adapter schema
- AIR fixtures
- Evidence hash-chain fixture
- Runtime adapter fixtures
- Negative adapter fixtures
- JSON validation
- AIR fixture validation
- Evidence fixture validation
- Replay contract validation
- Adapter fixture validation
- Real canonical SHA-256 event hashing
- Parent-event hash-chain validation
- Deterministic generated audit reports
- Repository-local agent skill pack

Current canonicalization profile:

```text
json-c14n-v1
```

Current required hash algorithm:

```text
sha256
```

BLAKE3 is not mandatory. It may be added later as an optional algorithm after the base evidence format is stable.

## Core distinction

### AIR

AIR describes what should happen:

- intent
- goal
- inputs
- pipeline
- contracts
- outputs
- metadata

### Evidence

Evidence describes what happened:

- AIR artifact reference
- executor
- event type
- action
- input and output hashes
- event hash
- parent event hash

## Validation

Run locally:

```bash
python scripts/validate_json.py
python scripts/validate_air_fixtures.py
python scripts/validate_evidence_fixtures.py
python scripts/validate_replay_contracts.py
python scripts/validate_adapter_fixtures.py
```

## Boundaries

This repository does not claim:

- hidden chain-of-thought capture
- provider runtime
- production MCP support
- legal or forensic assurance
- remote Supabase deployment
- package publishing

## Current validated baseline

Phase 12 validates the AIR contract layer, Evidence layer, replay contracts, adapter boundaries, deterministic audit reports, repository-local agent skill pack, and final pre-tag consistency audit.

The repository remains offline-only and does not claim provider runtime, production MCP support, hidden chain-of-thought capture, package publishing, or legal/compliance/forensic assurance.

<p align="center">
  <img src="assets/brand/comptext-air-readme-footer.png" alt="CompText AIR - Deterministic, portable, verifiable" width="100%">
</p>


## Agent Skill Pack

CompText AIR includes a repository-local agent skill pack for Gemini, Codex, and other coding agents.

The skill pack is not an official plugin, provider runtime, or MCP server. It is a local instruction layer that documents read order, validation commands, safety boundaries, and forbidden claims.

See:

- `.agent/skills/comptext-air/SKILL.md`
- `agent_prompts/GEMINI_AIR_VALIDATION_PROMPT.md`
- `agent_prompts/CODEX_AIR_VALIDATION_PROMPT.md`
- `docs/AGENT_SKILLS.md`

## Release Readiness

CompText AIR is prepared for public review as a validated contract and representation layer.

See:
- [Validation Baseline](docs/VALIDATION_BASELINE.md)
- [Release Readiness](docs/RELEASE_READINESS.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

### Pre-release preparation

The repository is currently preparing for its first public pre-release candidate (`v0.1.0-pre`).

See:
- [Tagging Checklist](docs/TAGGING_CHECKLIST.md)
- [v0.1.0-pre Release Notes](docs/RELEASE_NOTES_v0.1.0-pre.md)
- [Validation Baseline](docs/VALIDATION_BASELINE.md)
- [Release Readiness](docs/RELEASE_READINESS.md)

