from __future__ import annotations

from datetime import datetime
from typing import Any

from .ledger import TrustedLedger


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ContextCompiler:
    def compile(
        self,
        ledger: TrustedLedger,
        scope: str,
        *,
        now: str,
        budget_records: int = 8,
    ) -> tuple[dict[str, Any], ...]:
        if budget_records < 0:
            raise ValueError("budget_records must be non-negative")
        current = _parse_time(now)
        eligible = []
        for record in ledger.active(scope):
            if record.valid_until is not None and current > _parse_time(record.valid_until):
                continue
            eligible.append(record)

        eligible.sort(key=lambda r: (r.scope, r.kind, r.created_at, r.record_id))
        selected = eligible[:budget_records]
        return tuple(
            {
                "record_id": record.record_id,
                "record_digest": record.record_digest,
                "evidence_root": record.evidence_root,
                "kind": record.kind,
                "content": record.content,
                "scope": record.scope,
                "valid_until": record.valid_until,
            }
            for record in selected
        )
