# Audit Reports in CompText AIR

CompText AIR generates deterministic, machine-readable validation reports to provide evidence of contract fulfillment and runtime safety.

## Report Philosophy

- **JSON Only:** Reports are structured as JSON for ease of consumption by other agents and tools.
- **Deterministic:** Key order and content are stable across runs.
- **Path Neutrality:** All file paths are relative to the repository root. No absolute local paths are permitted.
- **No Timestamps:** To ensure bit-for-bit reproducibility of reports (unless timestamps are required for a specific replay flow and can be mocked).
- **No Claims:** Reports state facts about validation results, not legal or compliance guarantees.

## Generated Reports

### Replay Contract Report

- **Path:** `reports/generated/replay-contract-report.json`
- **Purpose:** Proves that an Evidence chain satisfies an AIR plan.
- **Key Fields:**
  - `status`: Result of the validation.
  - `air_hash`: The canonical SHA-256 hash of the AIR plan.
  - `event_root_hash`: The final hash in the evidence chain (anchoring the chain).
  - `pipeline_steps_count`: Total steps defined in AIR.
  - `satisfied_steps_count`: Steps verified in Evidence.
  - `contracts_count`: Total contracts defined in AIR.
  - `satisfied_contracts_count`: Contracts verified in Evidence.
  - `outputs_count`: Total outputs defined in AIR.
  - `satisfied_outputs_count`: Outputs verified in Evidence.

### Adapter Validation Report

- **Path:** `reports/generated/adapter-validation-report.json`
- **Purpose:** Proves that runtime adapters are safe and do not contain forbidden claims.
- **Key Fields:**
  - `status`: Result of the validation.
  - `checked_files`: List of adapter fixtures validated.
  - `invalid_fixtures_failures`: Details of why negative fixtures failed as expected.
  - `forbidden_claims_blocked`: List of specific claims that were identified and blocked.

## Usage in CI

These reports are generated during every CI run. They can be used as artifacts to prove the integrity of a specific build or commit without requiring re-execution of the validation logic.
