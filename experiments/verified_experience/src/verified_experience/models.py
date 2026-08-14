from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from .canonical import sha256_digest


class CandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    QUARANTINED = "quarantined"
    AWAITING_APPROVAL = "awaiting_approval"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class TrustedState(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    digest: str
    criticality: str = "medium"

    def as_dict(self) -> dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "digest": self.digest,
            "criticality": self.criticality,
        }


@dataclass(frozen=True)
class ExperienceCandidate:
    candidate_id: str
    kind: str
    content: Any
    scope: str
    evidence_refs: tuple[EvidenceRef, ...]
    producer: str
    confidence: float
    created_at: str
    valid_until: str | None = None
    supersedes: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    status: CandidateStatus = CandidateStatus.CANDIDATE
    canonical_digest: str = ""

    @classmethod
    def create(
        cls,
        *,
        candidate_id: str,
        kind: str,
        content: Any,
        scope: str,
        evidence_refs: tuple[EvidenceRef, ...],
        producer: str,
        confidence: float,
        created_at: str,
        valid_until: str | None = None,
        supersedes: tuple[str, ...] = (),
        contradicts: tuple[str, ...] = (),
        status: CandidateStatus = CandidateStatus.CANDIDATE,
    ) -> "ExperienceCandidate":
        base = cls(
            candidate_id=candidate_id,
            kind=kind,
            content=content,
            scope=scope,
            evidence_refs=evidence_refs,
            producer=producer,
            confidence=confidence,
            created_at=created_at,
            valid_until=valid_until,
            supersedes=supersedes,
            contradicts=contradicts,
            status=status,
        )
        return replace(base, canonical_digest=sha256_digest(base.canonical_payload()))

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "content": self.content,
            "scope": self.scope,
            "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
            "producer": self.producer,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "valid_until": self.valid_until,
            "supersedes": list(self.supersedes),
            "contradicts": list(self.contradicts),
            "status": self.status.value,
        }


@dataclass(frozen=True)
class VerificationResult:
    candidate_id: str
    candidate_digest: str
    evidence_resolved: bool
    replay_result: str
    contradiction_result: str
    outcome_result: str
    policy_version: str
    verdict: str
    reasons: tuple[str, ...]
    verification_digest: str


@dataclass(frozen=True)
class ApprovalEnvelope:
    approval_id: str
    principal_id: str
    candidate_id: str
    candidate_digest: str
    action: str
    target_scope: str
    policy_version: str
    issued_at: str
    expires_at: str
    nonce: str
    authority_proof: str


@dataclass(frozen=True)
class TrustedKnowledgeRecord:
    record_id: str
    kind: str
    content: Any
    scope: str
    evidence_refs: tuple[EvidenceRef, ...]
    evidence_root: str
    candidate_digest: str
    verification_digest: str
    approval_id: str
    promotion_policy_version: str
    created_at: str
    valid_from: str
    valid_until: str | None
    supersedes: tuple[str, ...]
    record_digest: str
