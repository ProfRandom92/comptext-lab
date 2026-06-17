# CompText Replay Validation Console

This frontend is intentionally structured as an internal validation and review console rather than a marketing page.

## Architecture decisions

- **Feature-based architecture:** route-level domains live under `src/features/*` and compose shared infrastructure from `src/components`, `src/lib`, and `src/types`.
- **Typed API boundary:** `src/types/domain.ts` describes the backend contract emitted by `dashboard/industrial_dashboard.py` at `/api/dashboard`.
- **React Query state model:** server state is owned by TanStack Query with refresh, retry, stale-time, and abort-signal behavior configured in `src/lib/queryClient.ts`.
- **Data-heavy UX:** tables use TanStack Virtual and column-level search to keep large benchmark, forensic, and incident lists responsive.
- **Operational UX:** the shell has scalable navigation, CSV/JSON export links, explicit loading/error/empty states, and a keyboard-accessible command palette (`Ctrl/⌘+K`).
- **Release-health UX:** the dedicated Release Health route renders readiness status, required artifacts, missing artifacts, next actions, and safety notes from the generated dashboard health summary contract.
- **Reusable visualization and theme:** charts are abstract SVG components, and design tokens are centralized in `src/styles/tokens.css`.

## Release health route

The dashboard exposes a first-class `Release Health` route for reviewers and future agents. It consumes `/dashboard-health-summary.json` through `src/lib/releaseHealth.ts` and falls back to synthetic metadata from `src/mocks/releaseHealthSummary.ts` if the summary cannot be loaded.

The page renders:

- overall release-readiness status
- required local validation artifacts
- missing required/optional artifacts
- next recommended actions
- safety notes
- fallback/unavailable state

Local smoke coverage lives in `scripts/release-health-smoke.mjs` and is runnable with:

```bash
npm run smoke:release-health
```

## Validation commands

Use these commands before dashboard-facing PRs:

```bash
npm run typecheck
npm run build
npm run smoke:release-health
```

GitHub Actions runs the same dashboard validation sequence in `.github/workflows/agent-checks.yml`.

## Local development

```bash
npm install
npm run dev
```

Run the Python API in another terminal:

```bash
python dashboard/industrial_dashboard.py --host 127.0.0.1 --port 8765
```

Build the production bundle:

```bash
npm run build
```

After a build, the stdlib Python server serves `dashboard/app/dist` automatically. Without a built bundle it falls back to the lightweight HTML export screen so air-gapped validation remains possible.
