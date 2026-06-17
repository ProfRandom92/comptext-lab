# Repository Intake Report

- timestamp: `2026-05-11T09:19:49Z`
- repository_root: `Comptextv7`
- detected_project_type: `mixed Python/Node`

## Detected important files

### README files

- `README.md`
- `dashboard/app/README.md`
- `docs/wiki/README.md`

### Python project files

- `pyproject.toml`

### Node project files

- `dashboard/app/package-lock.json`
- `dashboard/app/package.json`

### GitHub workflow files

- `.github/workflows/agent-checks.yml`
- `.github/workflows/ci.yml`

### Test folders

- `tests`

### Test files

- `tests/test_benchmarks.py`
- `tests/test_industrial_audit.py`
- `tests/test_industry_audit.py`
- `tests/test_kvtc_v7.py`
- `tests/test_validation_hardening.py`

## Detected test commands

- `python -m py_compile scripts/*.py`
- `python -m pytest`
- `npm test (only where package.json defines a test script)`
- `npm run lint (only where package.json defines a lint script)`

## Detected API areas

- `dashboard/app/README.md`
- `dashboard/app/index.html`
- `dashboard/app/package-lock.json`
- `dashboard/app/package.json`
- `dashboard/app/src/app/App.tsx`
- `dashboard/app/src/components/charts/BarChart.tsx`
- `dashboard/app/src/components/command/CommandPalette.tsx`
- `dashboard/app/src/components/layout/Shell.tsx`
- `dashboard/app/src/components/states/AsyncStates.tsx`
- `dashboard/app/src/components/table/VirtualTable.tsx`
- `dashboard/app/src/features/benchmarks/BenchmarksPage.tsx`
- `dashboard/app/src/features/forensics/ForensicsPage.tsx`
- `dashboard/app/src/features/incidents/IncidentsPage.tsx`
- `dashboard/app/src/features/overview/OverviewPage.tsx`
- `dashboard/app/src/features/replay/ReplayPage.tsx`
- `dashboard/app/src/lib/api.ts`
- `dashboard/app/src/lib/format.ts`
- `dashboard/app/src/lib/navigation.ts`
- `dashboard/app/src/lib/queryClient.ts`
- `dashboard/app/src/main.tsx`
- `dashboard/app/src/mocks/fallbackPayload.ts`
- `dashboard/app/src/styles/app.css`
- `dashboard/app/src/styles/tokens.css`
- `dashboard/app/src/types/domain.ts`
- `dashboard/app/src/vite-env.d.ts`
- `dashboard/app/tsconfig.json`
- `dashboard/app/tsconfig.node.json`
- `dashboard/app/vite.config.ts`
- `docs/API_SURFACE.md`

## Detected dashboard areas

- `dashboard/app/README.md`
- `dashboard/app/index.html`
- `dashboard/app/package-lock.json`
- `dashboard/app/package.json`
- `dashboard/app/src/app/App.tsx`
- `dashboard/app/src/components/charts/BarChart.tsx`
- `dashboard/app/src/components/command/CommandPalette.tsx`
- `dashboard/app/src/components/layout/Shell.tsx`
- `dashboard/app/src/components/states/AsyncStates.tsx`
- `dashboard/app/src/components/table/VirtualTable.tsx`
- `dashboard/app/src/features/benchmarks/BenchmarksPage.tsx`
- `dashboard/app/src/features/forensics/ForensicsPage.tsx`
- `dashboard/app/src/features/incidents/IncidentsPage.tsx`
- `dashboard/app/src/features/overview/OverviewPage.tsx`
- `dashboard/app/src/features/replay/ReplayPage.tsx`
- `dashboard/app/src/lib/api.ts`
- `dashboard/app/src/lib/format.ts`
- `dashboard/app/src/lib/navigation.ts`
- `dashboard/app/src/lib/queryClient.ts`
- `dashboard/app/src/main.tsx`
- `dashboard/app/src/mocks/fallbackPayload.ts`
- `dashboard/app/src/styles/app.css`
- `dashboard/app/src/styles/tokens.css`
- `dashboard/app/src/types/domain.ts`
- `dashboard/app/src/vite-env.d.ts`
- `dashboard/app/tsconfig.json`
- `dashboard/app/tsconfig.node.json`
- `dashboard/app/vite.config.ts`
- `dashboard/industrial_dashboard.py`

## Detected export/report areas

- `DETERMINISM_REPORT.md`
- `RECONSTRUCTION_DRIFT_REPORT.md`
- `TOKEN_TELEMETRY_REPORT.md`
- `VALIDATION_REPORT.md`
- `dashboard/app/package-lock.json`
- `dashboard/app/package.json`
- `dashboard/app/tsconfig.json`
- `dashboard/app/tsconfig.node.json`
- `datasets/golden/can_bus_reference.jsonl`
- `datasets/golden/mixed_incident_reference.jsonl`
- `datasets/golden/scada_reference.jsonl`
- `datasets/golden/sparse_alarm_reference.jsonl`
- `docs/reports/check-report.md`
- `docs/reports/repo-intake-report.md`
- `reports/replay_summary.json`

## Empty-state note

Repository files were detected; review the categorized paths above before making runtime, API, dashboard, or export changes.

## Next recommended checks

- Run `python scripts/run_checks.py` for deterministic local validation.
- Review `docs/AGENT_WORKFLOW.md` before agent-authored changes.
- Review `docs/API_SURFACE.md` before API, dashboard, or export contract changes.
- Use sanitized benchmark/regression summaries from `ProfRandom92/Comptext-Daimler-Experiment-` only as review evidence.

## Safety notes

- This intake reads paths and file names only; it does not inspect raw payloads.
- Do not commit secrets, tokens, cookies, raw production logs, customer data, or proprietary documents.
- Treat Daimler-related context as sensitive and use synthetic examples only.
- Keep Comptextv7 decoupled from benchmark runtime code unless a future issue explicitly approves coupling.
