# Release Readiness

This document outlines the current state of CompText AIR and its readiness for public pre-release review.

## Current State: Phase 10 (Public Repo Polish)

CompText AIR is currently a **validated contract and representation layer**. It provides the formal schemas and verification logic for agent intent (AIR) and runtime audit trails (Evidence).

### What is Ready
- **Core Schemas:** Stable definitions for AIR plans, Evidence events, and Runtime Adapters.
- **Verification Logic:** Complete local validation suite for hash integrity, hash-chain continuity, and contract fulfillment.
- **Safety Guardrails:** Explicit blocking of forbidden claims (e.g., direct provider runtime or production MCP claims).
- **Auditability:** Deterministic, machine-readable validation reports.
- **Documentation:** Architectural guides, replay contract explanations, and adapter principles.

### What is Not Ready
- **Provider Runtime:** There is no implementation for executing AIR plans via specific LLM providers (OpenAI, Anthropic, etc.).
- **Production MCP:** There is no production-ready MCP server implementation.
- **Remote Orchestration:** The repository is strictly offline-only; no remote database or API integration is active.
- **Automated Execution:** AIR plans must currently be executed manually or via external drivers; this repo only handles the *representation* and *validation*.

## Release Blockers
- None for `v0.1.0-pre` baseline. All core representations are validated.

## v0.1.0-pre Checklist
- [x] All schemas validated against fixtures.
- [x] Hash-chain integrity verified with real SHA-256.
- [x] Replay contracts proven for core audit flows.
- [x] Negative adapter tests blocking unsafe claims.
- [x] Documentation aligned with "offline-only contract" status.
- [x] Agent skill pack local to repository.

## Non-Claims / Safety Boundary

CompText AIR makes the following explicit **non-claims**:

1.  **No Hidden CoT Capture:** We do not attempt to capture or verify the internal "thinking" process of LLMs. We only audit explicit plans and evidence.
2.  **No Provider Runtime:** This repo does not execute code against model APIs.
3.  **No Production MCP:** Claims of being a production MCP environment are forbidden.
4.  **No Package Publishing:** This is a source/contract repository, not a distributed library.
5.  **No Legal/Compliance/Forensic Assurance:** The validation is a technical fulfillment check, not a legal guarantee.

## Recommended Next Steps (Post-v0.1.0)
- Conceptual design for AIR context snapshotting.
- Expansion of the Lexicon for specialized agent tasks.
- Cross-repository validation fixtures.
