# Contract Validation Report

- generated_at: deterministic-contract-validation
- status: pass
- schema_count: 5
- example_count: 4

## Schemas

| File | Status | Notes |
| --- | --- | --- |
| `contracts/api-dashboard.schema.json` | pass | valid JSON and required schema metadata present |
| `contracts/benchmark-summary.schema.json` | pass | valid JSON and required schema metadata present |
| `contracts/hash-chilli-cloud-ci-result.schema.json` | pass | valid JSON and required schema metadata present |
| `contracts/regression-summary.schema.json` | pass | valid JSON and required schema metadata present |
| `contracts/sanitization-summary.schema.json` | pass | valid JSON and required schema metadata present |

## Examples

| File | Schema | Status | Notes |
| --- | --- | --- | --- |
| `contracts/examples/api-dashboard.example.json` | `api-dashboard.schema.json` | pass | valid synthetic example structure |
| `contracts/examples/benchmark-summary.example.json` | `benchmark-summary.schema.json` | pass | valid synthetic example structure |
| `contracts/examples/regression-summary.example.json` | `regression-summary.schema.json` | pass | valid synthetic example structure |
| `contracts/examples/sanitization-summary.example.json` | `sanitization-summary.schema.json` | pass | valid synthetic example structure |

## Safety

This validator checks structure only. Contract examples are expected to remain synthetic and must not include secrets, raw production logs, customer data, or proprietary documents.
