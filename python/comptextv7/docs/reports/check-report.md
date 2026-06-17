# Agent Check Report

- timestamp: `2026-05-15T22:11:55Z`
- detected_project_type: `mixed Python/Node`
- safety: `local deterministic checks only; no dependency installation; no network required`

## Results

### python -m py_compile scripts/check_repo_layout.py scripts/generate_contract_fixtures.py scripts/generate_dashboard_health_summary.py scripts/generate_project_health_report.py scripts/publish_hash_chilli_ci_artifacts.py scripts/repo_intake.py scripts/run_checks.py scripts/validate.py scripts/validate_api_exports.py scripts/validate_contracts.py

- status: `pass`
- command: `python -m py_compile scripts/check_repo_layout.py scripts/generate_contract_fixtures.py scripts/generate_dashboard_health_summary.py scripts/generate_project_health_report.py scripts/publish_hash_chilli_ci_artifacts.py scripts/repo_intake.py scripts/run_checks.py scripts/validate.py scripts/validate_api_exports.py scripts/validate_contracts.py`
- returncode: `0`

```text
completed with no output
```

### pytest

- status: `skip`
- command: `python -m pytest`

```text
pytest is not available; optional tool missing
```

### npm test (dashboard/app)

- status: `skip`
- command: `npm test`

```text
no test script detected in dashboard/app/package.json
```

### npm run lint (dashboard/app)

- status: `skip`
- command: `npm run lint`

```text
no lint script detected in dashboard/app/package.json
```

## Outcome

- status: `pass`
- note: missing optional tools or tests are reported as skips, not failures.
