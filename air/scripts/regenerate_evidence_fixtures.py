import json
from pathlib import Path

from canonical_json import hash_event, hash_json_file, hash_json_value

AIR_PATH = Path("fixtures/air/hash-chain.audit.air.json")
OUT_PATH = Path("fixtures/evidence/hash-chain.events.json")


def build_event(event_id, timestamp, event_type, action, air_hash, parent_hash=None, inputs=None, outputs=None, metadata=None):
    event = {
        "event_id": event_id,
        "air_ref": {
            "path": str(AIR_PATH),
            "hash": air_hash,
        },
        "timestamp": timestamp,
        "executor": {
            "id": "comptext-air-local",
            "type": "system",
        },
        "event_type": event_type,
        "action": action,
        "metadata": metadata or {},
    }

    if parent_hash is not None:
        event["parent_event_hash"] = parent_hash

    if inputs:
        event["inputs"] = inputs

    if outputs:
        event["outputs"] = outputs

    event["event_hash"] = hash_event(event)
    return event


def main():
    air_hash = hash_json_file(AIR_PATH)

    # 1. load_evidence_events
    e1 = build_event(
        event_id="evt-001",
        timestamp="2026-06-16T10:00:00Z",
        event_type="start",
        action="load_evidence_events",
        air_hash=air_hash,
        inputs=[
            {"key": "evidence_input", "hash": hash_json_value({"path": "fixtures/evidence/raw.json"})}
        ],
        metadata={"phase": "loading"}
    )

    # 2. verify_parent_links (Contract: no_missing_parent_event)
    e2 = build_event(
        event_id="evt-002",
        timestamp="2026-06-16T10:00:05Z",
        event_type="verification",
        action="verify_parent_links",
        air_hash=air_hash,
        parent_hash=e1["event_hash"],
        metadata={"contract": "no_missing_parent_event"}
    )

    # 3. verify_hash_chain (Contracts: hash_chain_contiguous, event_hash_present)
    e3 = build_event(
        event_id="evt-003",
        timestamp="2026-06-16T10:00:10Z",
        event_type="verification",
        action="verify_hash_chain",
        air_hash=air_hash,
        parent_hash=e2["event_hash"],
        metadata={"contract": "hash_chain_contiguous"},
        outputs=[
            {"key": "event_hash_present", "hash": hash_json_value({"status": "verified"})}
        ]
    )

    # 4. emit_validation_report (Contract: final_report_references_evidence, Outputs: reports/hash-chain.validation.json, reports/hash-chain.validation.md)
    e4 = build_event(
        event_id="evt-004",
        timestamp="2026-06-16T10:00:15Z",
        event_type="end",
        action="emit_validation_report",
        air_hash=air_hash,
        parent_hash=e3["event_hash"],
        metadata={
            "contract": "final_report_references_evidence",
            "report": "reports/hash-chain.validation.json"
        },
        outputs=[
            {"key": "reports/hash-chain.validation.json", "hash": hash_json_value({"result": "pass"})},
            {"key": "reports/hash-chain.validation.md", "hash": hash_json_value("# Validation Report\nPass.")}
        ]
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps([e1, e2, e3, e4], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
