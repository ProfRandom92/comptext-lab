from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import sha256_digest
from .models import EvidenceRef


@dataclass(frozen=True)
class _EvidenceRecord:
    evidence_id: str
    kind: str
    payload: Any
    criticality: str
    digest: str


class EvidenceStore:
    def __init__(self) -> None:
        self._records: dict[str, _EvidenceRecord] = {}
        self._sequence = 0

    def append(self, kind: str, payload: Any, criticality: str = "medium") -> EvidenceRef:
        self._sequence += 1
        digest = sha256_digest(
            {
                "sequence": self._sequence,
                "kind": kind,
                "payload": payload,
                "criticality": criticality,
            }
        )
        evidence_id = f"ev-{self._sequence:06d}-{digest[:12]}"
        self._records[evidence_id] = _EvidenceRecord(
            evidence_id=evidence_id,
            kind=kind,
            payload=payload,
            criticality=criticality,
            digest=digest,
        )
        return EvidenceRef(evidence_id=evidence_id, digest=digest, criticality=criticality)

    def resolve(self, ref: EvidenceRef) -> dict[str, Any] | None:
        record = self._records.get(ref.evidence_id)
        if record is None:
            return None
        if record.digest != ref.digest:
            return {
                "status": "digest_mismatch",
                "evidence_id": record.evidence_id,
                "stored_digest": record.digest,
            }
        return {
            "status": "ok",
            "evidence_id": record.evidence_id,
            "kind": record.kind,
            "payload": record.payload,
            "criticality": record.criticality,
            "digest": record.digest,
        }
