import unittest

from verified_experience.approval import HmacTestAuthority
from verified_experience.evidence import EvidenceStore
from verified_experience.ledger import PromotionError, TrustedLedger
from verified_experience.models import ExperienceCandidate, TrustedState
from verified_experience.verification import Verifier


SCOPE = "repo:comptext-lab"


class TrustedLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.authority = HmacTestAuthority(b"phase-zero-test-secret")
        self.ledger = TrustedLedger()
        self.verifier = Verifier()
        self.approval_seq = 0

    def promote(self, *, candidate_id, value, at, supersedes=()):
        ref = self.store.append(
            "user_confirmed_project_state",
            {"package_manager": value, "effective_at": at},
            "high",
        )
        candidate = ExperienceCandidate.create(
            candidate_id=candidate_id,
            kind="fact",
            content={"key": "package_manager", "value": value},
            scope=SCOPE,
            evidence_refs=(ref,),
            producer="user:owner",
            confidence=1.0,
            created_at=at,
            supersedes=tuple(supersedes),
        )
        verification = self.verifier.verify(candidate, self.store)
        self.approval_seq += 1
        approval = self.authority.issue(
            approval_id=f"appr-{self.approval_seq}",
            principal_id="reviewer:test",
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.canonical_digest,
            action="promote_trusted_knowledge",
            target_scope=SCOPE,
            policy_version=verification.policy_version,
            issued_at=at,
            expires_at="2026-08-15T00:00:00Z",
            nonce=f"nonce-{self.approval_seq}",
        )
        return self.ledger.promote(
            candidate,
            verification,
            approval,
            self.authority,
            self.store,
            now=at,
        )

    def test_new_fact_supersedes_old_without_deleting_history(self):
        old = self.promote(candidate_id="cand-t1", value="cargo", at="2026-08-14T12:00:00Z")
        new = self.promote(
            candidate_id="cand-t2",
            value="buck2",
            at="2026-08-14T13:00:00Z",
            supersedes=(old.record_id,),
        )

        self.ledger.supersede(old.record_id, new.record_id)

        self.assertEqual(self.ledger.state_of(old.record_id), TrustedState.SUPERSEDED)
        self.assertEqual(self.ledger.state_of(new.record_id), TrustedState.ACTIVE)
        self.assertEqual([r.content["value"] for r in self.ledger.active(SCOPE)], ["buck2"])
        self.assertEqual(self.ledger.get(old.record_id).content["value"], "cargo")
        self.assertEqual(self.ledger.get(new.record_id).content["value"], "buck2")

    def test_revoked_record_is_excluded_but_preserved(self):
        record = self.promote(candidate_id="cand-t1", value="cargo", at="2026-08-14T12:00:00Z")
        self.ledger.revoke(record.record_id, "owner correction")
        self.assertEqual(self.ledger.state_of(record.record_id), TrustedState.REVOKED)
        self.assertEqual(self.ledger.active(SCOPE), ())
        self.assertEqual(self.ledger.get(record.record_id), record)

    def test_supersede_requires_declared_relation(self):
        old = self.promote(candidate_id="cand-t1", value="cargo", at="2026-08-14T12:00:00Z")
        unrelated = self.promote(candidate_id="cand-t2", value="buck2", at="2026-08-14T13:00:00Z")
        with self.assertRaises(PromotionError) as caught:
            self.ledger.supersede(old.record_id, unrelated.record_id)
        self.assertEqual(caught.exception.code, "SUPERSESSION_RELATION_MISSING")

    def test_unknown_record_cannot_be_revoked(self):
        with self.assertRaises(PromotionError) as caught:
            self.ledger.revoke("tk-missing", "test")
        self.assertEqual(caught.exception.code, "TRUSTED_RECORD_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
