# Validation Baseline

This document summarizes the current validated state of the CompText AIR repository. All success claims are backed by the local validation suite.

## Validated Components

### 1. Schemas
- **AIR Plan:** `schemas/air.schema.json` defines agent intent and pipeline requirements.
- **Evidence:** `schemas/evidence.schema.json` defines the hash-linked runtime event trail.
- **Adapter:** `schemas/adapter.schema.json` defines descriptive runtime mapping and safety boundaries.
- **Contract:** `schemas/contract.schema.json` defines the structure for replay and fulfillment.

### 2. Fixtures
- **AIR Plans:** `fixtures/air/` contains minimal and full hash-chain plans.
- **Evidence Trails:** `fixtures/evidence/` contains real SHA-256 hash-chained event sequences.
- **Adapters:** `fixtures/adapter/` contains a valid local CLI adapter and multiple negative fixtures.
- **Negative Fixtures:** `fixtures/adapter/invalid/` proves that forbidden claims and missing safety fields are blocked.

### 3. Hash Integrity
- **Algorithm:** SHA-256.
- **Canonicalization:** CompText `json-c14n-v1` (based on RFC 8785).
- **Evidence Hash Chain:** Every event `event_hash` is recomputed; `parent_event_hash` continuity is verified.
- **AIR References:** Evidence events reference the exact AIR plan hash.

### 4. Replay Contracts
- **Fulfillment:** Verified that evidence events satisfy the pipeline steps, contracts, and output requirements defined in AIR plans.
- **Attribution:** Every event in a chain is correctly attributed to its parent AIR plan.

### 5. Adapter Boundaries
- **Forbidden Claims:** Validation explicitly blocks `provider_runtime`, `mcp_server`, `auto_apply`, `network_required`, and legal/compliance assurance claims.
- **Safety Fields:** Validation requires `disabled_capabilities` and `evidence_mapping`.

### 6. Audit Reports
- **Deterministic:** Reports in `reports/generated/` are path-neutral and bit-for-bit reproducible.
- **Machine-Readable:** Structured JSON for automated verification.

### 7. Agent Skill Pack
- **Local Support:** Instructions for Gemini, Codex, and other agents are integrated into the repository to ensure consistent maintenance and validation.

## Validation Commands

To verify the entire baseline, run:

```bash
# JSON syntax and schema validation
python scripts/validate_json.py

# AIR fixture integrity
python scripts/validate_air_fixtures.py

# Evidence hash-chain integrity
python scripts/validate_evidence_fixtures.py

# AIR-to-Evidence replay contract fulfillment
python scripts/validate_replay_contracts.py

# Runtime adapter safety and boundary validation
python scripts/validate_adapter_fixtures.py
```
