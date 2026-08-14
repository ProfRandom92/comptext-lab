from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from typing import Protocol

from .canonical import canonical_bytes
from .models import ApprovalEnvelope


class ApprovalVerifier(Protocol):
    def verify(self, envelope: ApprovalEnvelope, now: str) -> tuple[bool, str | None]: ...


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _approval_payload(envelope: ApprovalEnvelope) -> dict[str, str]:
    return {
        "approval_id": envelope.approval_id,
        "principal_id": envelope.principal_id,
        "candidate_id": envelope.candidate_id,
        "candidate_digest": envelope.candidate_digest,
        "action": envelope.action,
        "target_scope": envelope.target_scope,
        "policy_version": envelope.policy_version,
        "issued_at": envelope.issued_at,
        "expires_at": envelope.expires_at,
        "nonce": envelope.nonce,
    }


class HmacTestAuthority:
    """Phase-0 local test authority. Not a production identity mechanism."""

    def __init__(self, secret: bytes) -> None:
        if not secret:
            raise ValueError("test authority secret must not be empty")
        self._secret = bytes(secret)

    def issue(
        self,
        *,
        approval_id: str,
        principal_id: str,
        candidate_id: str,
        candidate_digest: str,
        action: str,
        target_scope: str,
        policy_version: str,
        issued_at: str,
        expires_at: str,
        nonce: str,
    ) -> ApprovalEnvelope:
        unsigned = ApprovalEnvelope(
            approval_id=approval_id,
            principal_id=principal_id,
            candidate_id=candidate_id,
            candidate_digest=candidate_digest,
            action=action,
            target_scope=target_scope,
            policy_version=policy_version,
            issued_at=issued_at,
            expires_at=expires_at,
            nonce=nonce,
            authority_proof="",
        )
        proof = hmac.new(
            self._secret,
            canonical_bytes(_approval_payload(unsigned)),
            hashlib.sha256,
        ).hexdigest()
        return ApprovalEnvelope(**{**unsigned.__dict__, "authority_proof": proof})

    def verify(self, envelope: ApprovalEnvelope, now: str) -> tuple[bool, str | None]:
        expected = hmac.new(
            self._secret,
            canonical_bytes(_approval_payload(envelope)),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, envelope.authority_proof):
            return False, "APPROVAL_INVALID"
        try:
            current = _parse_time(now)
            issued = _parse_time(envelope.issued_at)
            expires = _parse_time(envelope.expires_at)
        except ValueError:
            return False, "APPROVAL_INVALID"
        if current < issued:
            return False, "APPROVAL_INVALID"
        if current > expires:
            return False, "APPROVAL_EXPIRED"
        return True, None
