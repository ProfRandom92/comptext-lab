# API Export Validation Report

- generated_at: deterministic-api-export-validation
- status: pass
- schema: `contracts/api-dashboard.schema.json`
- fixture: `contracts/examples/api-dashboard.example.json`
- synthetic_required: true
- live_server_required: false

## Checks

| Check | Status | Notes |
| --- | --- | --- |
| Schema load and shape | pass | schema JSON loaded with supported field types |
| Fixture contract | pass | required fields, simple types, synthetic flag, and array fields validated |

## Safety

Validation uses only local synthetic fixtures and does not contact a live server or read experiment repository data.
The report intentionally records structural results only and does not print fixture payload contents.
