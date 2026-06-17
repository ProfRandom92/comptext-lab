# SPARK Hackathon Path Demo — agy7rust

This document outlines the 5-minute live demo flow showing how CompText v7 secures SPARK-style extractions.

> [!IMPORTANT]
> **Core Claim:**
> "CompText v7 makes SPARK-style extractions deterministic, replayable, and tamper-sensitive."

## 5-Minute Demo Flow

### 1. Build the Hardened Rust CLI
Compile the `agy7rust` crate to produce the optimized binary.
```bash
cargo build --release
```

### 2. Compress (04)
Build a deterministic, hashed SPARK-V7-PACKAGE from a raw extraction JSON.
```bash
cargo run --release -- compress -i ../examples/spark/extraction.json -o ../artifacts/spark/extraction.spkg
```
*Expected Output:* Creates a stable JSON file with canonical sorting and generated hash chains. Repeated runs yield identical file bytes (and matching SHA-256 signatures).

### 3. Inspect (05)
Read package metadata without leaking raw values from the administrative payload.
```bash
cargo run --release -- inspect -i ../artifacts/spark/extraction.spkg
```
*Expected Output:*
```text
schema: SPARK-V7-PACKAGE
version: 1
source_type: spark_extraction_json
payload_sha256: 4df59458e0a3e8cc1cf0d262...
integrity_hash: e4c9d8a3be4162e0327f...
field_paths count: 12
commitment_tokens count: 7
tool_sequence count: 1
```

### 4. Verify (06)
Verify the full integrity chain (schema validation, sidecar hashes, and package integrity signature).
```bash
cargo run --release -- verify -i ../artifacts/spark/extraction.spkg
```
*Expected Output:*
```text
OK: package verified
```

### 5. Replay (07)
Replay the extraction by verifying the package first, then emitting a canonical replay JSON.
```bash
cargo run --release -- replay -i ../artifacts/spark/extraction.spkg
```
*Expected Output:*
```json
{
  "commitment_tokens": [
    "BImSchG-Genehmigungsantrag",
    "DE-NI-004-9872",
    "Nordwind Energie GmbH",
    "SPARK-2026-0042",
    "Staatliches Amt fuer Umwelt und Arbeitsschutz",
    "Vereinfachtes Verfahren",
    "Zustimmung mit Nebenbestimmungen zur Schallemission"
  ],
  "field_paths": [
    "$",
    "$.applicant",
    "$.authority",
    "$.case_id",
    "$.document_type",
    "$.extraction",
    "$.extraction.confidence",
    "$.extraction.fields",
    "$.extraction.fields.decision_recommendation",
    "$.extraction.fields.location",
    "$.extraction.fields.parcel_id",
    "$.extraction.fields.project_type",
    "$.extraction.notes",
    "$.metadata",
    "$.metadata.source_pdf_sha256"
  ],
  "payload_sha256": "4df59458e0a3e8cc1cf0d262...",
  "schema": "SPARK-V7-REPLAY",
  "source_type": "spark_extraction_json",
  "tool_sequence": [
    "spark.extractor"
  ]
}
```

### 6. Adversarial Tamper Suite (08)
Test five distinct tampering scenarios in memory to prove the package is tamper-sensitive.
```bash
cargo run --release -- adversarial -i ../examples/spark/extraction.json
```
*Expected Output:*
```text
case 01/05 payload field mutation: ok
case 02/05 payload field deletion: ok
case 03/05 payload_sha256 mutation: ok
case 04/05 integrity_hash mutation: ok
case 05/05 tool sequence mutation: ok
adversarial: 5/5 detected
```

## Failure Explanation for Tamper Cases

- **Payload mutation / deletion:** If a bad actor modifies a planning detail (e.g. `parcel_id` or `decision_recommendation`), the recalculated payload SHA-256 mismatches the sidecar's committed `payload_sha256`.
- **Sidecar hash mutation:** If the attacker alters the sidecar's `payload_sha256` to match their mutated payload, the calculated `final_state_hash` of the sidecar mismatches the committed `final_state_hash`.
- **Integrity hash mutation:** If the attacker updates both the sidecar and payload, the recomputed outer `integrity_hash` of the entire package mismatches the committed signature, resulting in verification rejection.
