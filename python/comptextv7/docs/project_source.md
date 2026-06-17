# Project Source: CompText V7

## Canonical Positioning
“CompText V7 is a deterministic replay-validation prototype for compact operational agent/MCP traces, with a KVTC-V7 technical-log compression prototype.”

## Strategic Category
CompText V7 is a deterministic replay-validation research prototype.

## Core Thesis
The core project question is:

“Can compact operational trace state still reproduce a safe replay trajectory?”

The governing research direction is:

“Deterministic replay validation for compact operational agent/MCP traces”

## Research Alignment Principle
Every accepted change must strengthen deterministic, offline, reproducible replay validation for compact operational agent/MCP traces, or be strictly maintenance-only.

## Current Strategic State
The project remains:
- offline
- deterministic
- artifact-first
- trace-native
- reproducible
- narrowly scoped
- audit-oriented

## Current Implementation State
Current implemented surfaces:
- curated agent trace fixtures in `tests/fixtures/agent_traces/`
- deterministic replay runner in `tests/utils/agent_trace_replay_runner.py`
- MCP replay payload layer in `src/comptext_v7/mcp/`
- evidence survival helpers in `src/validation/evidence.py`
- replay failure labels in `src/validation/replay_failure_classifier.py`
- committed artifacts such as `artifacts/agent_trace_replay_results.json`
- KVTC-V7 technical-log compression prototype in `src/core/kvtc_v7.py`

The `mcp_trace_replay` fixture family is hardened via explicit capability-boundary structures, deterministic degraded variants, and `failure_label_on_violation` handling.

A deterministic artifact evidence index maps committed evidence artifacts to their generators, evidence categories, fixture-family coverage, manifest alignment, deterministic evaluation status, LLM-free status, and external-API-free status.

## Non-Goals
See `NON_GOALS.md` in the repository root for the full list of prohibited expansion paths and the hard scope test.

## Hard Scope Rule
A proposal is out of scope unless it directly improves deterministic replay validation for compact operational agent/MCP traces without introducing probabilistic or platform-expansion behavior.

## Scope Evolution & RFC Process
Scope-expanding proposals require an RFC before implementation. RFCs must:
1. define the exact replay-validation gain,
2. prove deterministic and offline reproducibility,
3. show no hidden orchestration/platform expansion,
4. describe artifact and failure-taxonomy implications,
5. include rollback/de-scope criteria.

Default decision for scope-expanding proposals is rejection until the RFC is accepted.

## Correct Abstraction Level
CompText V7 focuses on replay contracts, trace-derived artifacts, fixture families, deterministic validators, and auditable evidence outputs. It does not absorb adjacent runtime or product-platform responsibilities.

## Preferred Terminology
Prefer:
- deterministic replay validation
- compact operational agent/MCP traces
- artifact evidence
- failure taxonomy and labels
- capability boundary
- offline reproducibility

Avoid vague or marketing abstractions that hide deterministic constraints. Do not frame the repository as industrial, enterprise-ready, production-ready, certification-grade, showcase-first, or a cognitive fabric.

## Roadmap From Here
1. Expand deterministic replay-validation fixture coverage.
2. Strengthen artifact-evidence traceability and reproducibility checks.
3. Improve contract-level validation clarity and failure classification precision.
4. Add narrowly scoped capabilities only via approved RFC.

## Merge Policy
- Documentation-only governance changes should stay small and focused.
- Core logic changes must include targeted tests.
- No merge-ready state until CI is green and review threads are resolved/outdated.
- Keep unrelated docs, demos, and core refactors separated.

## PR Template Additions
PR descriptions should explicitly confirm:
- deterministic replay-validation alignment,
- non-goals preserved,
- artifact regeneration expectations,
- evidence-index impact (updated or unchanged),
- RFC status when scope is touched.

## Strategic Risk Register
1. **Platform drift risk**: accidental expansion into orchestration/platform scope.
2. **Determinism erosion risk**: introduction of probabilistic evaluation paths.
3. **Evidence integrity risk**: artifact changes without corresponding evidence/governance updates.
4. **Terminology drift risk**: ambiguous framing that weakens enforceable boundaries.

## Governance Stance
Governance is conservative, boundary-enforcing, and evidence-led. CompTextv7 accepts incremental improvements over broad platform ambitions.

## Current Priority Stack
1. Deterministic replay-validation correctness.
2. Artifact evidence traceability.
3. Failure-label clarity and consistency.
4. Scope-bound documentation and review discipline.

## One-Sentence Rule
If a change does not directly improve deterministic replay validation for compact operational agent/MCP traces, it should not merge into core.
