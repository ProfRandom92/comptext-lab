from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .approval import ApprovalVerifier
from .canonical import sha256_digest
from .evidence import EvidenceStore
from .models import (
    ApprovalEnvelope,
    ExperienceCandidate,
    TrustedKnowledgeRecord,
    TrustedState,
    VerificationResult,
)


class PromotionError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class _StateMetadata:
    state: TrustedState
    reason: str | None = None


class TrustedLedger:
    def __init__(self) -> None:
        self._records: dict[str, TrustedKnowledgeRecord] = {}
        self._states: dict[str, _StateMetadata] = {}
        self._consumed_approvals: set[str] = set()
        self._superseded_by: dict[str, str] = {}

    def promote(
        self,
        candidate: ExperienceCandidate,
        verification: VerificationResult,
        approval: ApprovalEnvelope | None,
        approval_verifier: ApprovalVerifier,
        evidence_store: EvidenceStore,
        *,
        now: str,
    ) -> TrustedKnowledgeRecord:
        recomputed_digest = sha256_digest(candidate.canonical_payload())
        if (
            candidate.canonical_digest != recomputed_digest
            or verification.candidate_digest != recomputed_digest
            or verification.candidate_id != candidate.candidate_id
        ):
            raise PromotionError("CANDIDATE_DIGEST_MISMATCH")
        if verification.verdict != "pass" or not verification.evidence_resolved:
            raise PromotionError("VERIFICATION_NOT_PASS")

        for ref in candidate.evidence_refs:
            resolved = evidence_store.resolve(ref)
            if resolved is None:
                raise PromotionError("EVIDENCE_UNRESOLVED")
            if resolved.get("status") != "ok":
                raise PromotionError("EVIDENCE_MISMATCH")

        if approval is None:
            raise PromotionError("APPROVAL_MISSING")
        if approval.candidate_id != candidate.candidate_id or approval.candidate_digest != recomputed_digest:
            raise PromotionError("APPROVAL_INVALID")
        if approval.action != "promote_trusted_knowledge":
            raise PromotionError("APPROVAL_INVALID")
        if approval.target_scope != candidate.scope:
            raise PromotionError("APPROVAL_SCOPE_MISMATCH")
        if approval.policy_version != verification.policy_version:
            raise PromotionError("POLICY_VERSION_MISMATCH")

        valid, reason = approval_verifier.verify(approval, now)
        if not valid:
            raise PromotionError(reason or "APPROVAL_INVALID")
        if approval.approval_id in self._consumed_approvals:
            raise PromotionError("APPROVAL_REPLAYED")

        evidence_root = sha256_digest([ref.as_dict() for ref in candidate.evidence_refs])
        record_payload: dict[str, Any] = {
            "kind": candidate.kind,
            "content": candidate.content,
            "scope": candidate.scope,
            "evidence_refs": [ref.as_dict() for ref in candidate.evidence_refs],
            "evidence_root": evidence_root,
            "candidate_digest": recomputed_digest,
            "verification_digest": verification.verification_digest,
            "approval_id": approval.approval_id,
            "promotion_policy_version": verification.policy_version,
            "created_at": now,
            "valid_from": now,
            "valid_until": candidate.valid_until,
            "supersedes": list(candidate.supersedes),
        }
        record_digest = sha256_digest(record_payload)
        record = TrustedKnowledgeRecord(
            record_id=f"tk-{record_digest[:16]}",
            kind=candidate.kind,
            content=candidate.content,
            scope=candidate.scope,
            evidence_refs=candidate.evidence_refs,
            evidence_root=evidence_root,
            candidate_digest=recomputed_digest,
            verification_digest=verification.verification_digest,
            approval_id=approval.approval_id,
            promotion_policy_version=verification.policy_version,
            created_at=now,
            valid_from=now,
            valid_until=candidate.valid_until,
            supersedes=candidate.supersedes,
            record_digest=record_digest,
        )
        self._records[record.record_id] = record
        self._states[record.record_id] = _StateMetadata(TrustedState.ACTIVE)
        self._consumed_approvals.add(approval.approval_id)
        return record

    def active(self, scope: str | None = None) -> tuple[TrustedKnowledgeRecord, ...]:
        records = [
            record
            for record_id, record in self._records.items()
            if self._states[record_id].state is TrustedState.ACTIVE
            and (scope is None or record.scope == scope)
        ]
        return tuple(sorted(records, key=lambda item: item.record_id))

    def get(self, record_id: str) -> TrustedKnowledgeRecord:
        return self._records[record_id]

    def state_of(self, record_id: str) -> TrustedState:
        if record_id not in self._states:
            raise PromotionError("TRUSTED_RECORD_UNKNOWN")
        return self._states[record_id].state

    def supersede(self, old_record_id: str, new_record_id: str) -> None:
        if old_record_id not in self._records or new_record_id not in self._records:
            raise PromotionError("TRUSTED_RECORD_UNKNOWN")
        if old_record_id == new_record_id:
            raise PromotionError("SUPERSESSION_CYCLE")
        new_record = self._records[new_record_id]
        if old_record_id not in new_record.supersedes:
            raise PromotionError("SUPERSESSION_RELATION_MISSING")
        if self._states[new_record_id].state is not TrustedState.ACTIVE:
            raise PromotionError("SUPERSESSION_TARGET_NOT_ACTIVE")
        if self._states[old_record_id].state is not TrustedState.ACTIVE:
            raise PromotionError("SUPERSESSION_SOURCE_NOT_ACTIVE")

        cursor = new_record_id
        seen: set[str] = set()
        while cursor in self._superseded_by:
            if cursor in seen:
                raise PromotionError("SUPERSESSION_CYCLE")
            seen.add(cursor)
            cursor = self._superseded_by[cursor]
            if cursor == old_record_id:
                raise PromotionError("SUPERSESSION_CYCLE")

        self._states[old_record_id] = _StateMetadata(
            TrustedState.SUPERSEDED, reason=f"superseded_by:{new_record_id}"
        )
        self._superseded_by[old_record_id] = new_record_id

    def revoke(self, record_id: str, reason: str) -> None:
        if record_id not in self._records:
            raise PromotionError("TRUSTED_RECORD_UNKNOWN")
        self._states[record_id] = _StateMetadata(TrustedState.REVOKED, reason=reason)
