import json
from pathlib import Path
from collections import OrderedDict
from canonical_json import hash_json_file, hash_event

AIR_FIXTURE = Path("fixtures/air/hash-chain.audit.air.json")
EVIDENCE_FIXTURE = Path("fixtures/evidence/hash-chain.events.json")
REPORT_OUTPUT = Path("reports/generated/replay-contract-report.json")

def fail(msg):
    print(f"FAILURE: {msg}")
    raise SystemExit(1)

def validate_replay():
    print(f"Validating replay contract: {EVIDENCE_FIXTURE} -> {AIR_FIXTURE}")

    report = OrderedDict([
        ("status", "failure"),
        ("air_fixture", str(AIR_FIXTURE)),
        ("evidence_fixture", str(EVIDENCE_FIXTURE)),
        ("air_hash", None),
        ("event_root_hash", None),
        ("pipeline_steps_count", 0),
        ("satisfied_steps_count", 0),
        ("contracts_count", 0),
        ("satisfied_contracts_count", 0),
        ("outputs_count", 0),
        ("satisfied_outputs_count", 0)
    ])

    # 1. Load AIR plan and compute hash
    if not AIR_FIXTURE.exists():
        fail(f"AIR fixture not found: {AIR_FIXTURE}")
    air_plan = json.loads(AIR_FIXTURE.read_text(encoding="utf-8"))
    real_air_hash = hash_json_file(AIR_FIXTURE)
    report["air_hash"] = real_air_hash
    print(f"  Real AIR hash: {real_air_hash['value']}")

    # 2. Load Evidence events
    if not EVIDENCE_FIXTURE.exists():
        fail(f"Evidence fixture not found: {EVIDENCE_FIXTURE}")
    events = json.loads(EVIDENCE_FIXTURE.read_text(encoding="utf-8"))

    # 3. Verify every evidence event references the same real AIR hash
    # 4. Verify evidence hash chain
    previous_hash = None
    for i, event in enumerate(events):
        # AIR ref check
        event_air_hash = event.get("air_ref", {}).get("hash", {})
        if event_air_hash != real_air_hash:
            fail(f"Event[{i}] has mismatched air_ref.hash. Expected {real_air_hash['value']}, got {event_air_hash.get('value')}")

        # Recompute event hash to ensure it's real
        actual_event_hash = hash_event(event)
        if event.get("event_hash") != actual_event_hash:
             fail(f"Event[{i}] has invalid event_hash (not recomputed correctly)")

        # Parent hash check
        if i == 0:
            if "parent_event_hash" in event:
                fail(f"Event[0] should not have parent_event_hash")
        else:
            if event.get("parent_event_hash") != previous_hash:
                fail(f"Event[{i}] has mismatched parent_event_hash")
        
        previous_hash = event["event_hash"]
    
    # event_root_hash is the final hash in the chain
    report["event_root_hash"] = previous_hash

    print("  Hash chain and AIR reference: OK")

    # 5. Verify AIR pipeline steps
    required_steps = air_plan.get("pipeline", [])
    report["pipeline_steps_count"] = len(required_steps)
    required_steps_set = set(required_steps)
    satisfied_steps = set()

    for event in events:
        action = event.get("action")
        if action in required_steps_set:
            satisfied_steps.add(action)
        
        step_meta = event.get("metadata", {}).get("step")
        if step_meta in required_steps_set:
            satisfied_steps.add(step_meta)
            
        contract_meta = event.get("metadata", {}).get("contract")
        if contract_meta in required_steps_set:
            satisfied_steps.add(contract_meta)

    report["satisfied_steps_count"] = len(satisfied_steps)
    missing_steps = required_steps_set - satisfied_steps
    if missing_steps:
        fail(f"Missing pipeline steps in evidence: {sorted(missing_steps)}")
    print(f"  Pipeline steps: OK ({len(satisfied_steps)} steps)")

    # 6. Verify AIR contracts
    required_contracts = air_plan.get("contracts", [])
    report["contracts_count"] = len(required_contracts)
    required_contracts_set = set(required_contracts)
    satisfied_contracts = set()

    for event in events:
        action = event.get("action")
        if action in required_contracts_set:
            satisfied_contracts.add(action)

        contract_meta = event.get("metadata", {}).get("contract")
        if contract_meta in required_contracts_set:
            satisfied_contracts.add(contract_meta)

        for output in event.get("outputs", []):
            if output.get("key") in required_contracts_set:
                satisfied_contracts.add(output.get("key"))

    report["satisfied_contracts_count"] = len(satisfied_contracts)
    missing_contracts = required_contracts_set - satisfied_contracts
    if missing_contracts:
        fail(f"Missing contracts in evidence: {sorted(missing_contracts)}")
    print(f"  Contracts: OK ({len(satisfied_contracts)} contracts)")

    # 7. Verify AIR outputs
    required_outputs = air_plan.get("outputs", [])
    report["outputs_count"] = len(required_outputs)
    satisfied_outputs = set()

    for output_spec in required_outputs:
        out_path = output_spec.get("path")
        out_kind = output_spec.get("kind")
        
        for event in events:
            # Check outputs
            for ev_out in event.get("outputs", []):
                key = ev_out.get("key")
                if key == out_path or key == out_kind:
                    satisfied_outputs.add(out_path or out_kind)
            
            # Check metadata report reference
            if event.get("metadata", {}).get("report") == out_path:
                satisfied_outputs.add(out_path or out_kind)

    report["satisfied_outputs_count"] = len(satisfied_outputs)
    missing_outputs = []
    for o in required_outputs:
        key = o.get("path") or o.get("kind")
        if key not in satisfied_outputs:
            missing_outputs.append(key)

    if missing_outputs:
        fail(f"Missing outputs in evidence: {sorted(missing_outputs)}")
    print(f"  Outputs: OK ({len(satisfied_outputs)} outputs)")

    report["status"] = "success"
    
    # Write report
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Report generated: {REPORT_OUTPUT}")

    print("SUCCESS: Replay contract fulfilled.")

if __name__ == "__main__":
    validate_replay()
