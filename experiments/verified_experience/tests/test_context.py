import unittest

from verified_experience.approval import HmacTestAuthority
from verified_experience.context import ContextCompiler
from verified_experience.evidence import EvidenceStore
from verified_experience.ledger import TrustedLedger
from verified_experience.models import ExperienceCandidate
from verified_experience.verification import Verifier


class ContextCompilerTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.ledger = TrustedLedger()
        self.authority = HmacTestAuthority(b"phase-zero-test-secret")
        self.verifier = Verifier()
        self.seq = 0

    def promote(self, *, value, scope="repo:comptext-lab", at, valid_until=None, supersedes=(), kind="fact"):
        self.seq += 1
        ref = self.store.append("confirmed_state", {"value": value, "at": at}, "high")
        candidate = ExperienceCandidate.create(
            candidate_id=f"cand-{self.seq}",
            kind=kind,
            content={"key": f"k-{self.seq}", "value": value},
            scope=scope,
            evidence_refs=(ref,),
            producer="user:owner",
            confidence=1.0,
            created_at=at,
            valid_until=valid_until,
            supersedes=tuple(supersedes),
        )
        verification = self.verifier.verify(candidate, self.store)
        approval = self.authority.issue(
            approval_id=f"appr-{self.seq}",
            principal_id="reviewer:test",
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.canonical_digest,
            action="promote_trusted_knowledge",
            target_scope=scope,
            policy_version=verification.policy_version,
            issued_at=at,
            expires_at="2026-08-16T00:00:00Z",
            nonce=f"nonce-{self.seq}",
        )
        return self.ledger.promote(
            candidate,
            verification,
            approval,
            self.authority,
            self.store,
            now=at,
        )

    def test_compile_excludes_superseded_revoked_expired_and_wrong_scope(self):
        old = self.promote(value="cargo", at="2026-08-14T10:00:00Z")
        current = self.promote(
            value="buck2",
            at="2026-08-14T11:00:00Z",
            supersedes=(old.record_id,),
        )
        self.ledger.supersede(old.record_id, current.record_id)

        revoked = self.promote(value="revoked", at="2026-08-14T11:10:00Z")
        self.ledger.revoke(revoked.record_id, "bad lesson")
        self.promote(
            value="expired",
            at="2026-08-14T11:20:00Z",
            valid_until="2026-08-14T11:30:00Z",
        )
        self.promote(value="other-scope", scope="repo:other", at="2026-08-14T11:40:00Z")

        compiled = ContextCompiler().compile(
            self.ledger,
            "repo:comptext-lab",
            now="2026-08-14T12:00:00Z",
            budget_records=8,
        )
        self.assertEqual([item["content"]["value"] for item in compiled], ["buck2"])
        item = compiled[0]
        self.assertEqual(item["record_id"], current.record_id)
        self.assertEqual(item["record_digest"], current.record_digest)
        self.assertEqual(item["evidence_root"], current.evidence_root)

    def test_budget_and_order_are_deterministic(self):
        self.promote(value="z", at="2026-08-14T11:00:00Z", kind="workflow_rule")
        first = self.promote(value="a", at="2026-08-14T10:00:00Z", kind="fact")
        self.promote(value="b", at="2026-08-14T10:30:00Z", kind="fact")

        compiled = ContextCompiler().compile(
            self.ledger,
            "repo:comptext-lab",
            now="2026-08-14T12:00:00Z",
            budget_records=1,
        )
        self.assertEqual(len(compiled), 1)
        self.assertEqual(compiled[0]["record_id"], first.record_id)


if __name__ == "__main__":
    unittest.main()
