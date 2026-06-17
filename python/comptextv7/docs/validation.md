# Validation Guide

This repository intentionally has multiple validation surfaces. Use the root npm
wrapper commands for broad reviewer-friendly validation, or use direct dashboard
commands when only the dashboard application is affected.

## Repository layout

```text
Comptextv7/
├── package.json    # Root command wrapper only; no root dependencies
├── dashboard/app/  # Vite + TypeScript dashboard application
├── tests/          # Python regression, replay, and foundation tests
├── scripts/        # Python validation and repository utility scripts
├── artifacts/      # Committed deterministic replay artifacts
└── docs/           # Reviewer and validation documentation
```

The repository root contains a minimal `package.json` wrapper for reviewer
convenience. It does not define workspaces, dependencies, or a root Node app.
The dashboard remains the only Node application in this repository, with its
dependency management in `dashboard/app`.

Root npm scripts use `npm --prefix` to delegate to the dashboard directory and
use `pytest` for Python validation. No root `node_modules` directory or root npm
dependencies are required for the wrapper itself.

## Root wrapper commands

Run broad validation commands from the repository root:

```bash
npm run layout
npm run typecheck
npm run validate
npm run build
npm test
npm run check
```

The root wrapper delegates as follows:

- `npm run layout` runs `python scripts/check_repo_layout.py`.
- `npm run typecheck` runs the dashboard typecheck with `npm --prefix`.
- `npm run validate` runs the dashboard release-health smoke test with
  `npm --prefix`.
- `npm run build` runs the dashboard build with `npm --prefix`.
- `npm test` runs `pytest`.
- `npm run check` chains layout, typecheck, validate, build, and Python tests.

## Dashboard app validation

Run dashboard validation directly from `dashboard/app` for targeted dashboard
changes:

```bash
cd dashboard/app
npm run typecheck
npm run build
npm run smoke:release-health
```

Use these commands for dashboard TypeScript changes, release-health UI changes,
and `dashboard/app/src/core/foundation/` modules.

## Python replay validation from the repository root

Run Python tests from the repository root:

```bash
pytest -q
pytest tests/test_core_foundation_ts.py -q
pytest tests/test_paper_replay_bench.py tests/test_agent_trace_replay.py tests/test_replay_continuity.py -q
```

The focused replay command validates the deterministic paper replay, agent trace
replay, and replay continuity surfaces without changing benchmark logic.

Agent trace replay is fixture-bound: curated traces live in
`tests/fixtures/agent_traces/`, the deterministic runner is
`tests/utils/agent_trace_replay_runner.py`, and committed replay output is stored
in `artifacts/agent_trace_replay_results.json`. Validation is local and does not
use embeddings, vector databases, LLM judges, or external APIs.

Install the Python test dependency set:

```bash
python -m pip install -e '.[test]'
```

Regenerate deterministic replay artifacts:

```bash
python tests/utils/paper_replay_runner.py
python tests/utils/agent_trace_replay_runner.py
python benchmarks/run_replay_continuity.py --iterations 250 --output-dir reports/replay_continuity
```

The KVTC-V7 technical-log compressor in `src/core/kvtc_v7.py` is a deterministic
prototype, not a production-readiness or certification claim.
