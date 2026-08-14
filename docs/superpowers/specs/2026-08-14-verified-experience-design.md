# Verified Experience Track — Design

Date: 2026-08-14  
Status: DESIGN / NOT IMPLEMENTED  
Target repository: `ProfRandom92/comptext-lab`  
Target branch for this design: `design/verified-experience-track`

## 1. Purpose

This track tests one narrow hypothesis:

> A model-agnostic agent that persists only evidence-linked, policy-verified, authority-approved experience as trusted knowledge will accumulate fewer false or stale beliefs than an agent using raw history or ordinary persistent memory, while retaining enough useful experience to improve later work.

This is an experiment, not a claim that CompText implements neural continual learning. Model weights remain unchanged. The proposed system is an external, persistent learning layer owned by CompText.

The design extends the existing CompText principle:

```text
Compute before Context
        ↓
Evidence before Trust
        ↓
Verify before Memory
        ↓
Experience → Evidence → Promotion → Context
```

## 2. Why `comptext-lab`

`comptext-lab` already combines the relevant deterministic surfaces:

- Rust shared core primitives;
- `ctxt` context/runtime CLI;
- evidence/context tooling;
- CompText V7 replay-validation research;
- AIR schemas, fixtures, and replay contracts.

The experiment therefore belongs in the integration laboratory first. It must not create a new permanent repository and must not change Product Core authority until the benchmark passes.

## 3. Scope

### In scope

- immutable experience/evidence references;
- candidate knowledge records;
- deterministic candidate hashing;
- verification and contradiction checks;
- fail-closed promotion policy;
- action-bound approval verification;
- trusted knowledge records;
- supersession and revocation;
- context compilation from trusted knowledge;
- deterministic A/B/C evaluation;
- replay/evidence-survival evaluation;
- adversarial memory-poisoning fixtures;
- local, offline tests and artifacts.

### Out of scope

- model-weight updates, fine-tuning, LoRA, RL, or online training;
- embeddings or a vector database as a requirement;
- provider/network calls;
- autonomous promotion without an authority boundary;
- production database design;
- changing existing AIR or `ctxt` authoritative schemas during the experiment;
- merging code from historical repositories into Product Core;
- MCP runtime expansion;
- UI implementation;
- deleting or renaming historical repositories.

## 4. Approaches Considered

### A. Implement directly in the current CompText Product Core

Benefit: shortest path to a user-visible feature.

Risk: it would promote an unvalidated research hypothesis into an authority-bearing runtime and make rollback difficult.

Decision: rejected for phase 0.

### B. Create a separate `comptext-memory` or `comptext-learning` repository

Benefit: maximum isolation.

Risk: increases ecosystem fragmentation, duplicates contracts, and weakens the existing monorepo consolidation effort.

Decision: rejected.

### C. Isolated Verified Experience experiment inside `comptext-lab`

Benefit: reuses AIR/V7/CLI primitives, keeps the authority chain unchanged, supports deterministic benchmarking, and can later be upstreamed only if the experiment passes.

Decision: selected.

## 5. Conceptual Model

The experiment must keep three classes of state distinct.

### 5.1 Evidence

Evidence answers: **what happened?**

Properties:

- append-only reference;
- provenance-bearing;
- hash-addressable;
- replayable where the source subsystem permits it;
- never silently rewritten into a stronger claim.

### 5.2 Subjective experience

Subjective experience answers: **what did an agent infer, remember, or believe?**

It may be incomplete, wrong, stale, or contradictory. It is never authoritative merely because an agent produced it.

### 5.3 Trusted knowledge

Trusted knowledge answers: **what may CompText deliberately reuse as authoritative context for a defined scope?**

A trusted record must have:

- resolvable evidence references;
- deterministic content digest;
- verification result;
- promotion policy version;
- approval bound to the exact candidate/action;
- state (`active`, `superseded`, or `revoked`);
- temporal and scope metadata.

## 6. Minimal Data Contracts

These are experiment-local contracts. They do not replace AIR or `ctxt` schemas.

### `ExperienceCandidate`

```text
candidate_id
kind: fact | constraint | decision | preference | skill | failure_lesson | workflow_rule
content
scope
evidence_refs[]
producer
confidence
created_at
supersedes[]
contradicts[]
canonical_digest
status: candidate | quarantined | awaiting_approval | rejected | promoted
```

Rules:

1. `canonical_digest` is derived from canonical candidate content; it is never accepted from an untrusted producer as authority.
2. `confidence` is descriptive, not an authorization signal.
3. `producer=agent` never grants promotion rights.
4. Empty or unresolved `evidence_refs` cannot reach trusted state.

### `VerificationResult`

```text
candidate_id
candidate_digest
evidence_resolved
replay_result
contradiction_result
outcome_result
policy_version
verdict: pass | quarantine | reject
reasons[]
verification_digest
```

### `ApprovalEnvelope`

```text
approval_id
principal_id
candidate_id
candidate_digest
action: promote_trusted_knowledge
target_scope
policy_version
issued_at
expires_at
nonce
authority_proof
```

The authority proof must be verified by a trusted `ApprovalVerifier` boundary. Candidate fields such as `source_role=human_review` or `approved=true` have no authority.

The first implementation may use deterministic local test identities/keys, but the interface must permit later reuse of the stronger principal-bound approval primitives already explored in other CompText repositories.

### `TrustedKnowledgeRecord`

```text
record_id
kind
content
scope
evidence_refs[]
evidence_root
candidate_digest
verification_digest
approval_id
promotion_policy_version
created_at
valid_from
valid_until
state: active | superseded | revoked
supersedes[]
record_digest
```

Trusted records are append-only objects. A correction creates a new record and supersedes the old record; it does not rewrite history.

## 7. Promotion Invariants

The experiment fails closed.

A candidate must not be promoted unless all of the following are true:

1. every required evidence reference resolves;
2. candidate digest matches the verified candidate;
3. verification verdict is `pass`;
4. no blocking contradiction remains unresolved;
5. approval is issued by the trusted approval boundary;
6. approval candidate digest matches exactly;
7. approval action is exactly `promote_trusted_knowledge`;
8. approval target scope matches the candidate scope;
9. approval policy version matches the verification policy;
10. approval has not expired or been consumed;
11. the resulting trusted record can be deterministically reproduced from the promotion inputs.

No model, tool, adapter, memory renderer, or candidate payload may bypass this gate.

## 8. Data Flow

```text
Run / trajectory / event
        ↓
Raw evidence reference
        ↓
Experience candidate
        ↓
Deterministic verification
   ┌────┴───────────┐
 reject/quarantine  pass
                     ↓
               approval request
                     ↓
              ApprovalVerifier
                     ↓
                 promotion
                     ↓
           TrustedKnowledgeRecord
                     ↓
              context compiler
                     ↓
                Context Pack
                     ↓
                   Agent
                     ↓
                  outcome
                     ↓
               new evidence
```

The feedback arrow always returns as evidence, never directly as truth.

## 9. Context Compilation

The experiment must not dump the complete knowledge store into context.

The context compiler selects only active records that:

- match task scope;
- are not expired;
- are not superseded or revoked;
- satisfy policy-required evidence criticality;
- fit the configured context budget.

Every compiled item retains a compact back-reference to its trusted record and evidence provenance so that replay/evaluation can determine what was lost.

## 10. A/B/C Benchmark

The same deterministic task sequence is executed against three state strategies.

### A — Raw history

The context strategy uses bounded raw trajectory/history without a promoted knowledge layer.

### B — Ordinary persistent memory

Agent-produced memory is persisted and retrieved without the Verified Experience promotion gate. This represents the practical baseline used by many memory systems.

### C — Verified Experience

Only active, promoted `TrustedKnowledgeRecord` objects may enter the trusted-memory portion of context.

All three variants use the same task fixtures and expected outcomes.

## 11. Initial Fixture Families

### 11.1 Coding outcome

A command/workflow succeeds, a plausible alternative fails, and a later task asks for the correct procedure.

Purpose: test useful procedural learning.

### 11.2 Rumor versus observer truth

Adapt the conceptual pattern from Society Lab: an agent receives a plausible but false/modified claim while the event/evidence layer contains the objective source state.

Purpose: test subjective-memory contamination.

### 11.3 Approval spoof

A candidate claims `human_review`, `approved=true`, or equivalent authority in its own payload but has no valid approval envelope.

Purpose: test authority separation.

### 11.4 Temporal supersession

A fact is correct at T1 and becomes invalid at T2. Later tasks must use the newer active record without erasing the T1 evidence.

Purpose: test stale-memory handling.

### 11.5 Constraint retention under replay

A high-criticality constraint is attached to evidence and the context representation is repeatedly compacted/replayed.

Purpose: reuse the V7 style of evidence-survival and constraint-drift evaluation.

## 12. Metrics

The experiment reports exact fixture-bound counts and ratios; it must not present them as universal model-memory performance.

Primary metrics:

- task success rate;
- unauthorized promotion count;
- unsupported trusted-claim count;
- false promotion rate;
- trusted recall precision;
- contradiction recovery rate;
- supersession correctness;
- revocation correctness;
- high-criticality evidence survival;
- constraint survival;
- operational drift;
- context bytes/tokens when deterministically measurable;
- deterministic replay consistency.

## 13. Phase-0 Gate

The experiment is eligible for an implementation/upstreaming discussion only if all hard gates pass:

1. **0 unauthorized promotions** across adversarial approval fixtures;
2. **0 trusted records with unresolved required evidence**;
3. **100% supersession correctness** on the seeded temporal fixtures;
4. **100% revocation exclusion** from trusted context on seeded fixtures;
5. **100% high-criticality evidence survival** in the seeded Verified Experience replay fixtures;
6. identical inputs produce byte-identical canonical digests and deterministic verdicts;
7. strategy C performs at least as well as strategy B on the deterministic task-success fixture set;
8. strategy C strictly outperforms B on at least one seeded poisoning, contradiction, or stale-memory scenario;
9. no network/provider dependency is required for validation.

A failed gate is a research result. It must not be weakened merely to make the experiment pass.

## 14. Failure Handling

Fail-closed classifications should be stable and machine-readable. Initial labels:

```text
EVIDENCE_UNRESOLVED
EVIDENCE_MISMATCH
CANDIDATE_DIGEST_MISMATCH
CONTRADICTION_BLOCKING
APPROVAL_MISSING
APPROVAL_INVALID
APPROVAL_SCOPE_MISMATCH
APPROVAL_EXPIRED
APPROVAL_REPLAYED
POLICY_VERSION_MISMATCH
TRUSTED_RECORD_SUPERSEDED
TRUSTED_RECORD_REVOKED
HIGH_CRITICAL_EVIDENCE_LOSS
```

These labels may later map into the existing V7 failure taxonomy, but the experiment must not silently change current V7 labels.

## 15. Proposed Repository Boundary

Implementation planning should prefer an isolated tree such as:

```text
experiments/
└── verified-experience/
    ├── README.md
    ├── contracts/
    ├── fixtures/
    ├── src/
    ├── tests/
    └── artifacts/
```

Language is intentionally not mandated by this design. The implementation plan must choose the smallest option that maximizes reuse of current `comptext-lab` primitives and preserves deterministic validation. A Rust implementation is likely preferable if it can reuse the existing workspace without pulling the research harness into Product Core; a Python harness remains acceptable for benchmark orchestration around V7.

## 16. Cross-Repository Reuse Policy

Historical repositories are evidence and component sources, not automatic authority.

Concepts to evaluate for reuse:

- `comptext-society-lab`: subjective memory, claims, belief/observer-truth separation, trajectory fixtures;
- `Comptextv7`: evidence survival, replay consistency, drift/failure taxonomy;
- `comptext-Daimler-Experiment-`: operational-memory continuity benchmark concepts;
- `comptext-air`: intent/evidence/replay contract discipline;
- `comptext-cloud-workspace`: principal/action/target/parameter-bound approvals;
- `comptext-core`: signing/Merkle concepts where compatible;
- `comptext-revolution` / `Ctvault-comptext`: ordinary persistent-memory baseline patterns;
- `comptext-phone-agent`: bounded agent trajectories and action-bound approval patterns.

No implementation should copy a historical component merely because it exists. Each reuse decision must be recorded with source commit, compatibility assessment, and tests.

## 17. Security Properties

The design specifically defends against:

- agent self-approval;
- authority-role string spoofing;
- replaying an approval for a different candidate;
- changing candidate content after verification;
- promoting evidence-free summaries;
- stale facts remaining active after supersession;
- revoked knowledge re-entering context;
- compression detaching a trusted claim from its critical evidence;
- ordinary memory poisoning becoming authoritative context.

It does not claim to solve compromised host identity, stolen signing keys, malicious human approval, or model alignment.

## 18. Testing Strategy

Implementation must be test-first.

Minimum test layers:

- contract canonicalization/digest unit tests;
- promotion-gate unit tests;
- approval mismatch/expiry/replay negative tests;
- evidence-resolution negative tests;
- contradiction/supersession/revocation tests;
- context compiler exclusion tests;
- deterministic repeated-run tests;
- A/B/C fixture integration tests;
- V7-style evidence-survival/replay tests;
- full offline validation command producing a committed or reproducibly generated machine-readable report.

## 19. Deliverables for the First Implementation Increment

The first increment is complete only when it contains:

1. experiment-local contracts;
2. deterministic promotion gate;
3. fail-closed approval-verifier interface and local test authority;
4. append-only trusted-record representation;
5. context compiler for active trusted records;
6. the five initial fixture families;
7. A/B/C runner;
8. machine-readable metrics artifact;
9. human-readable gate report;
10. tests proving the phase-0 hard gates.

No provider calls, production storage, UI, or Product Core merge are required.

## 20. Decision

Proceed with an isolated Verified Experience experiment in `comptext-lab`.

Do not modify existing authoritative AIR/`ctxt` semantics during the experiment. Treat all historical CompText repositories as reusable evidence sources, not as automatically correct implementations. Upstreaming is permitted only after the benchmark and adversarial gates produce evidence strong enough to justify a separate architecture decision.
