from __future__ import annotations

from .canonical import sha256_digest
from .evidence import EvidenceStore
from .models import ExperienceCandidate, VerificationResult


class Verifier:
    def __init__(self, policy_version: str = "ve-policy-v1") -> None:
        self.policy_version = policy_version

    def verify(
        self,
        candidate: ExperienceCandidate,
        evidence_store: EvidenceStore,
        *,
        contradictions: tuple[str, ...] = (),
    ) -> VerificationResult:
        reasons: list[str] = []
        evidence_resolved = bool(candidate.evidence_refs)

        if not candidate.evidence_refs:
            reasons.append("EVIDENCE_UNRESOLVED")
            evidence_resolved = False

        for ref in candidate.evidence_refs:
            resolved = evidence_store.resolve(ref)
            if resolved is None:
                reasons.append("EVIDENCE_UNRESOLVED")
                evidence_resolved = False
            elif resolved.get("status") == "digest_mismatch":
                reasons.append("EVIDENCE_MISMATCH")
                evidence_resolved = False

        blocking = sorted(set(candidate.contradicts).intersection(contradictions))
        if blocking:
            reasons.append("CONTRADICTION_BLOCKING")

        if "EVIDENCE_UNRESOLVED" in reasons or "EVIDENCE_MISMATCH" in reasons:
            verdict = "reject"
        elif "CONTRADICTION_BLOCKING" in reasons:
            verdict = "quarantine"
        else:
            verdict = "pass"

        candidate_digest = sha256_digest(candidate.canonical_payload())
        payload = {
            "candidate_id": candidate.candidate_id,
            "candidate_digest": candidate_digest,
            "evidence_resolved": evidence_resolved,
            "replay_result": "not_run",
            "contradiction_result": "blocking" if blocking else "clear",
            "outcome_result": "not_evaluated",
            "policy_version": self.policy_version,
            "verdict": verdict,
            "reasons": sorted(set(reasons)),
        }
        verification_digest = sha256_digest(payload)
        return VerificationResult(
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate_digest,
            evidence_resolved=evidence_resolved,
            replay_result=payload["replay_result"],
            contradiction_result=payload["contradiction_result"],
            outcome_result=payload["outcome_result"],
            policy_version=self.policy_version,
            verdict=verdict,
            reasons=tuple(payload["reasons"]),
            verification_digest=verification_digest,
        )
