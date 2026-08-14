# Verified Experience — Phase 0

Deterministic research experiment for a CompText learning boundary:

```text
Experience → Evidence → Verify → Approval → Trusted Knowledge → Context
```

The experiment compares three strategies over the same seeded task sequences:

- **A — raw history:** bounded chronological interaction state;
- **B — ordinary memory:** latest write wins for a logical memory key;
- **C — Verified Experience:** only evidence-linked, verification-passed, action/scope/policy-bound approved records enter trusted context.

## Run

No third-party Python dependencies, provider calls, or network access are required.

```bash
PYTHONPATH=experiments/verified_experience/src \
python -m unittest discover -s experiments/verified_experience/tests -v

PYTHONPATH=experiments/verified_experience/src \
python experiments/verified_experience/run_gate.py
```

Generated reports:

- `artifacts/gate-report.json`
- `artifacts/gate-report.md`

## Phase-0 Fixtures

1. successful coding/workflow outcome;
2. rumor versus observer truth;
3. self-claimed approval/authority spoof;
4. temporal supersession plus stale-memory reintroduction;
5. high-criticality constraint retention under an untrusted compressed summary.

A separate deterministic revocation probe verifies that revoked knowledge is excluded from compiled context while its immutable record remains preserved.

## Security Boundary

A candidate may contain strings such as `source_role=human_review` or `approved=true`; these have **zero authorization meaning**. Promotion requires an `ApprovalEnvelope` bound to candidate digest, action, target scope, policy version, expiry, and nonce, validated through the `ApprovalVerifier` interface.

The current `HmacTestAuthority` is deliberately **test-only** and exists solely to exercise the authority boundary with Python standard-library primitives. Production identity/signing integration is out of scope for Phase 0.

## Important Limitations

- This is **not neural continual learning**: model weights do not change.
- The B baseline is intentionally simple latest-write persistent memory. It does not represent every existing memory product.
- Fixtures are deterministic and seeded; reported percentages are not external benchmark claims.
- Evidence resolution currently establishes provenance/integrity, not full semantic entailment between evidence and every candidate claim.
- A malicious or compromised trusted human/authority can still approve a bad candidate; that threat is outside Phase 0.
- No production database, provider integration, MCP runtime, UI, or cross-device identity system is included.

A failed hard gate is a valid research result and must not be weakened to force `GO`.
