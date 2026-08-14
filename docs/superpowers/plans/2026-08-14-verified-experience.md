# Verified Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an isolated, offline, deterministic Verified Experience experiment that compares raw history, ordinary persistent memory, and evidence/approval-gated trusted knowledge.

**Architecture:** Implement a stdlib-only Python experiment under `experiments/verified_experience/`. Keep candidate creation, evidence resolution, verification, approval, promotion, trusted-ledger state, context compilation, and benchmarking as separate units. The experiment must not modify AIR, `ctxt`, Rust workspace behavior, or Product Core semantics.

**Tech Stack:** Python 3.11+ standard library only (`dataclasses`, `enum`, `hashlib`, `hmac`, `json`, `pathlib`, `unittest`). HMAC-SHA256 is test-only local authority behind an abstract approval-verifier interface; production identity remains out of scope.

## Global Constraints

- No provider or network calls.
- No new runtime dependencies.
- Existing AIR and `ctxt` authoritative schemas remain unchanged.
- Agent/tool/model output is untrusted input.
- Candidate confidence is never an authorization signal.
- Promotion fails closed.
- Trusted records are append-only; corrections use supersession/revocation.
- Same canonical inputs must yield byte-identical digests and deterministic verdicts.
- A failed hard gate is reported as failure; thresholds are not weakened to force success.

---

## File Structure

```text
experiments/verified_experience/
├── README.md
├── run_gate.py
├── src/
│   └── verified_experience/
│       ├── __init__.py
│       ├── canonical.py
│       ├── models.py
│       ├── evidence.py
│       ├── approval.py
│       ├── verification.py
│       ├── ledger.py
│       ├── context.py
│       └── benchmark.py
├── tests/
│   ├── test_canonical.py
│   ├── test_promotion.py
│   ├── test_supersession.py
│   ├── test_context.py
│   └── test_benchmark.py
└── artifacts/
    ├── gate-report.json
    └── gate-report.md
```

---

### Task 1: Canonicalization and Experiment Contracts

**Files:**
- Create: `experiments/verified_experience/src/verified_experience/__init__.py`
- Create: `experiments/verified_experience/src/verified_experience/canonical.py`
- Create: `experiments/verified_experience/src/verified_experience/models.py`
- Test: `experiments/verified_experience/tests/test_canonical.py`

**Interfaces:**
- Produces: `canonical_bytes(value) -> bytes`, `sha256_digest(value) -> str`
- Produces dataclasses/enums: `EvidenceRef`, `ExperienceCandidate`, `VerificationResult`, `ApprovalEnvelope`, `TrustedKnowledgeRecord`, `CandidateStatus`, `TrustedState`

- [ ] **Step 1: Write failing canonicalization tests**

```python
from verified_experience.canonical import canonical_bytes, sha256_digest


def test_canonical_bytes_ignore_mapping_insertion_order():
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}
    assert canonical_bytes(left) == canonical_bytes(right)
    assert sha256_digest(left) == sha256_digest(right)
```

Also assert that changing one scalar changes the digest and that UTF-8 content is deterministic.

- [ ] **Step 2: Run the isolated test and verify RED**

Run:

```bash
PYTHONPATH=experiments/verified_experience/src python -m unittest experiments/verified_experience/tests/test_canonical.py -v
```

Expected: import failure because `verified_experience.canonical` does not exist.

- [ ] **Step 3: Implement minimal canonicalization**

`canonical_bytes()` must use `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` and UTF-8. `sha256_digest()` returns lowercase hex SHA-256 over canonical bytes.

- [ ] **Step 4: Add immutable experiment dataclasses**

Use `@dataclass(frozen=True)` where mutation is not required. `ExperienceCandidate.canonical_payload()` must exclude its `canonical_digest` field from digest calculation. `TrustedKnowledgeRecord` must expose `record_digest` derived from immutable promotion inputs.

- [ ] **Step 5: Run tests and verify GREEN**

Run the command from Step 2. Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add experiments/verified_experience
 git commit -m "feat(experiment): add verified experience contracts"
```

---

### Task 2: Evidence Store and Verification Gate

**Files:**
- Create: `experiments/verified_experience/src/verified_experience/evidence.py`
- Create: `experiments/verified_experience/src/verified_experience/verification.py`
- Test: `experiments/verified_experience/tests/test_promotion.py`

**Interfaces:**
- Consumes: contracts/canonical helpers from Task 1
- Produces: `EvidenceStore.append(kind, payload, criticality) -> EvidenceRef`
- Produces: `EvidenceStore.resolve(ref) -> dict | None`
- Produces: `Verifier.verify(candidate, evidence_store, contradictions=()) -> VerificationResult`

- [ ] **Step 1: Write failing evidence-resolution tests**

Test that a candidate with an unresolved evidence reference returns verdict `reject` and reason `EVIDENCE_UNRESOLVED`.

- [ ] **Step 2: Run and verify RED**

```bash
PYTHONPATH=experiments/verified_experience/src python -m unittest experiments/verified_experience/tests/test_promotion.py -v
```

Expected: missing `EvidenceStore`/`Verifier`.

- [ ] **Step 3: Implement append-only in-memory EvidenceStore**

Each appended event receives deterministic content digest and an ID derived from sequence plus digest. Returned refs include `evidence_id`, `digest`, and criticality. Resolution must verify stored digest before returning payload.

- [ ] **Step 4: Implement fail-closed Verifier**

Required behavior:

```text
missing evidence            -> reject / EVIDENCE_UNRESOLVED
digest mismatch             -> reject / EVIDENCE_MISMATCH
blocking contradiction      -> quarantine / CONTRADICTION_BLOCKING
all required evidence valid -> pass
```

`VerificationResult.candidate_digest` must equal the candidate's recomputed canonical digest, not a caller-provided trust claim.

- [ ] **Step 5: Run promotion test module and verify GREEN**

Expected: evidence/verification tests pass.

- [ ] **Step 6: Commit**

```bash
git add experiments/verified_experience
 git commit -m "feat(experiment): verify candidates against evidence"
```

---

### Task 3: Approval Boundary and Promotion Gate

**Files:**
- Create: `experiments/verified_experience/src/verified_experience/approval.py`
- Create: `experiments/verified_experience/src/verified_experience/ledger.py`
- Modify/Test: `experiments/verified_experience/tests/test_promotion.py`

**Interfaces:**
- Produces protocol/interface: `ApprovalVerifier.verify(envelope, now) -> tuple[bool, str | None]`
- Produces test authority: `HmacTestAuthority.issue(...) -> ApprovalEnvelope`
- Produces: `TrustedLedger.promote(candidate, verification, approval, approval_verifier, evidence_store, now) -> TrustedKnowledgeRecord`
- Produces: `PromotionError(code)`

- [ ] **Step 1: Write failing attack tests**

Tests must cover:

```text
candidate payload says human_review -> APPPROVAL_MISSING / no promotion
approved=true in content             -> no effect
forged HMAC                           -> APPROVAL_INVALID
approval for candidate A on B        -> APPROVAL_INVALID
wrong scope                           -> APPROVAL_SCOPE_MISMATCH
expired approval                      -> APPROVAL_EXPIRED
same approval consumed twice          -> APPROVAL_REPLAYED
verification digest mismatch          -> CANDIDATE_DIGEST_MISMATCH
```

- [ ] **Step 2: Run tests and verify RED**

Expected: missing approval/ledger implementation.

- [ ] **Step 3: Implement `HmacTestAuthority`**

The signed canonical payload must bind exactly:

```text
approval_id
principal_id
candidate_id
candidate_digest
action=promote_trusted_knowledge
target_scope
policy_version
issued_at
expires_at
nonce
```

Use `hmac.new(secret, canonical_bytes(payload), hashlib.sha256).hexdigest()` and `hmac.compare_digest()`.

- [ ] **Step 4: Implement fail-closed `TrustedLedger.promote`**

Promotion order must be deterministic: candidate digest -> verification pass -> evidence resolution -> approval validity/action/scope/policy -> replay-consumption check -> trusted record creation. Never mark approval consumed until every check except consumption has passed.

- [ ] **Step 5: Run attack tests and verify GREEN**

All negative cases must pass and valid promotion must succeed.

- [ ] **Step 6: Commit**

```bash
git add experiments/verified_experience
 git commit -m "feat(experiment): gate trusted knowledge promotion"
```

---

### Task 4: Supersession, Revocation, and Active Knowledge

**Files:**
- Modify: `experiments/verified_experience/src/verified_experience/ledger.py`
- Test: `experiments/verified_experience/tests/test_supersession.py`

**Interfaces:**
- Produces: `TrustedLedger.supersede(old_record_id, new_record_id) -> None`
- Produces: `TrustedLedger.revoke(record_id, reason) -> None`
- Produces: `TrustedLedger.active(scope=None) -> tuple[TrustedKnowledgeRecord, ...]`

- [ ] **Step 1: Write failing temporal tests**

Create T1 fact `package_manager=cargo`, then valid T2 fact `package_manager=buck2` that supersedes T1. Assert only T2 is active while both immutable records remain retrievable.

Also revoke T2 and assert neither record enters active context.

- [ ] **Step 2: Run and verify RED**

Expected: missing supersession/revocation API.

- [ ] **Step 3: Implement state transitions without mutation of historical payloads**

Maintain state metadata separately from immutable records. Reject cycles and attempts to supersede unknown records.

- [ ] **Step 4: Run and verify GREEN**

Expected: 100% seeded supersession and revocation correctness.

- [ ] **Step 5: Commit**

```bash
git add experiments/verified_experience
 git commit -m "feat(experiment): add trusted knowledge lifecycle"
```

---

### Task 5: Context Compiler

**Files:**
- Create: `experiments/verified_experience/src/verified_experience/context.py`
- Test: `experiments/verified_experience/tests/test_context.py`

**Interfaces:**
- Produces: `ContextCompiler.compile(ledger, scope, budget_records=8) -> tuple[dict, ...]`

- [ ] **Step 1: Write failing selection tests**

Seed active, superseded, revoked, wrong-scope, and expired records. Assert compiled context contains only eligible active records and retains `record_id`, `record_digest`, `evidence_root`, `kind`, and `content`.

- [ ] **Step 2: Run and verify RED**

Expected: missing compiler.

- [ ] **Step 3: Implement deterministic selection**

Sort eligible records by `(scope, kind, created_at, record_id)` and enforce a record-count budget. No semantic/vector retrieval is required in Phase 0.

- [ ] **Step 4: Run and verify GREEN**

- [ ] **Step 5: Commit**

```bash
git add experiments/verified_experience
 git commit -m "feat(experiment): compile trusted context deterministically"
```

---

### Task 6: A/B/C Benchmark and Five Fixture Families

**Files:**
- Create: `experiments/verified_experience/src/verified_experience/benchmark.py`
- Create: `experiments/verified_experience/tests/test_benchmark.py`

**Interfaces:**
- Produces: `run_benchmark() -> dict`
- Benchmark strategies: `RawHistoryStrategy`, `OrdinaryMemoryStrategy`, `VerifiedExperienceStrategy`

- [ ] **Step 1: Write failing benchmark assertions**

Fixtures:

1. coding outcome/procedural learning;
2. rumor versus observer truth;
3. approval spoof;
4. temporal supersession;
5. high-criticality constraint retention.

The test must assert exact fixture IDs and deterministic results, not generic random scores.

- [ ] **Step 2: Run and verify RED**

- [ ] **Step 3: Implement A raw-history baseline**

Use bounded latest history. Deliberately do not add trust promotion.

- [ ] **Step 4: Implement B ordinary-memory baseline**

Latest write for each logical memory key wins, regardless of evidence/authority. This is intentionally simple and documented as a baseline, not a universal representation of every memory product.

- [ ] **Step 5: Implement C using the real experiment promotion path**

Do not special-case expected answers. All C answers must come from active trusted records/context compiler.

- [ ] **Step 6: Compute metrics**

Return at least:

```text
task_success_rate
unauthorized_promotions
unsupported_trusted_claims
false_promotion_rate
trusted_recall_precision
contradiction_recovery_rate
supersession_correctness
revocation_correctness
high_criticality_evidence_survival
constraint_survival
context_record_count
```

- [ ] **Step 7: Run benchmark tests twice**

Serialize both results with canonical JSON and assert byte identity.

- [ ] **Step 8: Commit**

```bash
git add experiments/verified_experience
 git commit -m "test(experiment): add verified experience ABC benchmark"
```

---

### Task 7: Gate Runner and Reports

**Files:**
- Create: `experiments/verified_experience/run_gate.py`
- Create: `experiments/verified_experience/README.md`
- Generate: `experiments/verified_experience/artifacts/gate-report.json`
- Generate: `experiments/verified_experience/artifacts/gate-report.md`

**Interfaces:**
- CLI exit `0` when every Phase-0 hard gate passes
- CLI exit non-zero when any hard gate fails

- [ ] **Step 1: Write gate evaluation in `run_gate.py`**

Evaluate exactly:

```text
0 unauthorized promotions
0 trusted records with unresolved evidence
100% supersession correctness
100% revocation exclusion
100% high-criticality evidence survival
byte-identical deterministic repeated results
C task success >= B task success
C strictly better than B on >=1 poisoning/contradiction/stale-memory fixture
no network/provider dependency
```

- [ ] **Step 2: Run full unittest suite**

```bash
PYTHONPATH=experiments/verified_experience/src python -m unittest discover -s experiments/verified_experience/tests -v
```

Expected: PASS.

- [ ] **Step 3: Run gate twice and compare generated JSON**

```bash
PYTHONPATH=experiments/verified_experience/src python experiments/verified_experience/run_gate.py
cp experiments/verified_experience/artifacts/gate-report.json /tmp/gate-1.json
PYTHONPATH=experiments/verified_experience/src python experiments/verified_experience/run_gate.py
cmp /tmp/gate-1.json experiments/verified_experience/artifacts/gate-report.json
```

Expected: exit 0 and `cmp` exit 0.

- [ ] **Step 4: Document limitations in README**

README must explicitly state: fixture-bound, deterministic Phase-0 research; no neural continual-learning claim; ordinary-memory baseline is intentionally simple; no production identity/storage/provider integration.

- [ ] **Step 5: Commit**

```bash
git add experiments/verified_experience
 git commit -m "feat(experiment): add phase zero gate runner"
```

---

### Task 8: Final Verification and Review Handoff

**Files:**
- No new behavior required; fix only findings discovered by verification.

- [ ] **Step 1: Run syntax compilation**

```bash
python -m compileall -q experiments/verified_experience
```

Expected: exit 0.

- [ ] **Step 2: Run unittest suite with warnings promoted**

```bash
PYTHONWARNINGS=error PYTHONPATH=experiments/verified_experience/src python -m unittest discover -s experiments/verified_experience/tests -v
```

Expected: PASS with no warnings.

- [ ] **Step 3: Run Phase-0 gate**

```bash
PYTHONPATH=experiments/verified_experience/src python experiments/verified_experience/run_gate.py
```

Expected: explicit `GO` only if all hard gates pass; otherwise `NO-GO` and non-zero exit.

- [ ] **Step 4: Verify experiment isolation**

```bash
git diff main...HEAD --name-only
```

Expected: changes only under `experiments/verified_experience/` plus the approved Superpowers spec/plan documents.

- [ ] **Step 5: Review diff for accidental authority changes**

```bash
git diff main...HEAD -- air crates Cargo.toml Cargo.lock
```

Expected: empty diff.

- [ ] **Step 6: Final commit only if verification fixes were needed**

```bash
git add experiments/verified_experience
 git commit -m "fix(experiment): address phase zero verification findings"
```

## Plan Self-Review

- Spec coverage: evidence, subjective candidate state, verification, approval, promotion, trusted records, supersession, revocation, context compilation, five fixture families, A/B/C metrics, and hard gate are covered.
- Placeholder scan: no implementation step relies on TODO/TBD behavior.
- Type consistency: promotion consumes `ExperienceCandidate`, `VerificationResult`, `ApprovalEnvelope`, `ApprovalVerifier`, and `EvidenceStore`; context consumes only `TrustedLedger` active records.
- Scope: production storage, network/providers, UI, MCP, model-weight learning, and Product Core changes remain explicitly out of scope.
