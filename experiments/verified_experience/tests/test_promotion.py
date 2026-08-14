import unittest
from dataclasses import replace

from verified_experience.approval import HmacTestAuthority
from verified_experience.ledger import PromotionError, TrustedLedger
from verified_experience.models import EvidenceRef, ExperienceCandidate
from verified_experience.evidence import EvidenceStore
from verified_experience.verification import Verifier


SCOPE = "repo:comptext-lab"
NOW = "2026-08-14T12:00:00Z"


def make_candidate(*, evidence_refs, contradicts=()):
    return ExperienceCandidate.create(
        candidate_id="cand-cargo",
        kind="workflow_rule",
        content={"package_manager": "cargo"},
        scope=SCOPE,
        evidence_refs=tuple(evidence_refs),
        producer="agent:test",
        confidence=0.99,
        created_at=NOW,
        contradicts=tuple(contradicts),
    )


class EvidenceVerificationTests(unittest.TestCase):
    def test_missing_evidence_is_rejected(self):
        store = EvidenceStore()
        missing = EvidenceRef("ev-missing", "0" * 64, "high")
        result = Verifier().verify(make_candidate(evidence_refs=(missing,)), store)
        self.assertEqual(result.verdict, "reject")
        self.assertIn("EVIDENCE_UNRESOLVED", result.reasons)

    def test_evidence_digest_mismatch_is_rejected(self):
        store = EvidenceStore()
        ref = store.append("command_result", {"command": "cargo test", "exit_code": 0}, "high")
        forged = EvidenceRef(ref.evidence_id, "f" * 64, ref.criticality)
        result = Verifier().verify(make_candidate(evidence_refs=(forged,)), store)
        self.assertEqual(result.verdict, "reject")
        self.assertIn("EVIDENCE_MISMATCH", result.reasons)

    def test_valid_evidence_passes(self):
        store = EvidenceStore()
        ref = store.append("command_result", {"command": "cargo test", "exit_code": 0}, "high")
        result = Verifier().verify(make_candidate(evidence_refs=(ref,)), store)
        self.assertEqual(result.verdict, "pass")
        self.assertEqual(result.reasons, ())
        self.assertTrue(result.evidence_resolved)

    def test_blocking_contradiction_quarantines_candidate(self):
        store = EvidenceStore()
        ref = store.append("command_result", {"command": "cargo test", "exit_code": 0}, "high")
        result = Verifier().verify(
            make_candidate(evidence_refs=(ref,), contradicts=("cand-npm",)),
            store,
            contradictions=("cand-npm",),
        )
        self.assertEqual(result.verdict, "quarantine")
        self.assertIn("CONTRADICTION_BLOCKING", result.reasons)


class PromotionGateTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.ref = self.store.append(
            "command_result",
            {"command": "cargo test --workspace", "exit_code": 0},
            "high",
        )
        self.candidate = ExperienceCandidate.create(
            candidate_id="cand-valid",
            kind="workflow_rule",
            content={"package_manager": "cargo"},
            scope=SCOPE,
            evidence_refs=(self.ref,),
            producer="agent:test",
            confidence=1.0,
            created_at=NOW,
        )
        self.verification = Verifier().verify(self.candidate, self.store)
        self.authority = HmacTestAuthority(b"phase-zero-test-secret")
        self.ledger = TrustedLedger()

    def issue(self, candidate=None, **overrides):
        candidate = candidate or self.candidate
        values = {
            "approval_id": "appr-1",
            "principal_id": "reviewer:test",
            "candidate_id": candidate.candidate_id,
            "candidate_digest": candidate.canonical_digest,
            "action": "promote_trusted_knowledge",
            "target_scope": candidate.scope,
            "policy_version": self.verification.policy_version,
            "issued_at": "2026-08-14T12:01:00Z",
            "expires_at": "2026-08-14T12:11:00Z",
            "nonce": "nonce-1",
        }
        values.update(overrides)
        return self.authority.issue(**values)

    def assert_promotion_error(self, code, *, candidate=None, verification=None, approval=None, now="2026-08-14T12:05:00Z"):
        with self.assertRaises(PromotionError) as caught:
            self.ledger.promote(
                candidate or self.candidate,
                verification or self.verification,
                approval,
                self.authority,
                self.store,
                now=now,
            )
        self.assertEqual(caught.exception.code, code)

    def test_valid_approval_promotes_trusted_record(self):
        record = self.ledger.promote(
            self.candidate,
            self.verification,
            self.issue(),
            self.authority,
            self.store,
            now="2026-08-14T12:05:00Z",
        )
        self.assertEqual(record.content, {"package_manager": "cargo"})
        self.assertEqual(record.scope, SCOPE)
        self.assertEqual(len(self.ledger.active()), 1)

    def test_self_claimed_human_review_without_envelope_is_rejected(self):
        candidate = ExperienceCandidate.create(
            candidate_id="cand-spoof",
            kind="fact",
            content={"package_manager": "pip", "source_role": "human_review", "approved": True},
            scope=SCOPE,
            evidence_refs=(self.ref,),
            producer="agent:attacker",
            confidence=1.0,
            created_at=NOW,
        )
        verification = Verifier().verify(candidate, self.store)
        self.assert_promotion_error("APPROVAL_MISSING", candidate=candidate, verification=verification, approval=None)

    def test_forged_authority_proof_is_rejected(self):
        approval = replace(self.issue(), authority_proof="0" * 64)
        self.assert_promotion_error("APPROVAL_INVALID", approval=approval)

    def test_approval_for_other_candidate_is_rejected(self):
        other = ExperienceCandidate.create(
            candidate_id="cand-other",
            kind="workflow_rule",
            content={"package_manager": "pip"},
            scope=SCOPE,
            evidence_refs=(self.ref,),
            producer="agent:test",
            confidence=1.0,
            created_at=NOW,
        )
        approval = self.issue(candidate=other)
        self.assert_promotion_error("APPROVAL_INVALID", approval=approval)

    def test_wrong_scope_is_rejected(self):
        approval = self.issue(target_scope="repo:other")
        self.assert_promotion_error("APPROVAL_SCOPE_MISMATCH", approval=approval)

    def test_expired_approval_is_rejected(self):
        approval = self.issue(expires_at="2026-08-14T12:04:00Z")
        self.assert_promotion_error("APPROVAL_EXPIRED", approval=approval, now="2026-08-14T12:05:00Z")

    def test_consumed_approval_cannot_be_replayed(self):
        approval = self.issue()
        self.ledger.promote(
            self.candidate,
            self.verification,
            approval,
            self.authority,
            self.store,
            now="2026-08-14T12:05:00Z",
        )
        self.assert_promotion_error("APPROVAL_REPLAYED", approval=approval)

    def test_verification_for_different_candidate_is_rejected(self):
        other = ExperienceCandidate.create(
            candidate_id="cand-other",
            kind="workflow_rule",
            content={"package_manager": "pip"},
            scope=SCOPE,
            evidence_refs=(self.ref,),
            producer="agent:test",
            confidence=1.0,
            created_at=NOW,
        )
        other_verification = Verifier().verify(other, self.store)
        self.assert_promotion_error(
            "CANDIDATE_DIGEST_MISMATCH",
            verification=other_verification,
            approval=self.issue(),
        )

    def test_candidate_digest_field_tampering_is_rejected(self):
        tampered = replace(self.candidate, canonical_digest="f" * 64)
        self.assert_promotion_error(
            "CANDIDATE_DIGEST_MISMATCH",
            candidate=tampered,
            approval=self.issue(),
        )


if __name__ == "__main__":
    unittest.main()
