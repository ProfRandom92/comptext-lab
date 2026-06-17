# Cross-Repo Release Checklist

## Purpose

This checklist defines the promotion gate for moving findings from
`ProfRandom92/Comptext-Daimler-Experiment-` into `ProfRandom92/Comptextv7`.
It keeps the workflow practical and auditable:

```text
experiment result -> review -> Comptextv7 issue/PR -> validation -> release
```

The checklist is documentation-first. It does not authorize runtime imports,
shared dependencies, git submodules, copied benchmark code, or CI jobs that
require the experiment repository. Use only sanitized summaries and synthetic
examples in Comptextv7.

## Repository roles

| Repository | Release role | Boundary |
| --- | --- | --- |
| `ProfRandom92/Comptext-Daimler-Experiment-` | Produces benchmark runs, regression reports, sanitization reports, forensic replay documentation, contract-compatible JSON summaries, and report contract validation evidence. | Owns experiment execution and producer-side validation. Do not promote raw payloads, production logs, real Daimler/customer data, or secrets. |
| `ProfRandom92/Comptextv7` | Owns runtime/API/dashboard documentation, benchmark integration documentation, agent workflow documentation, repo intake, local checks, machine-readable schemas, contract validation, and API/export contract enforcement. | Owns implementation and release decisions after sanitized evidence passes this promotion gate. |

If ownership is unclear, stop and create or update an issue before opening an
implementation PR.

## Promotion lifecycle

1. **Experiment result**: Complete the benchmark, regression, sanitization, or
   forensic replay work in `ProfRandom92/Comptext-Daimler-Experiment-`.
2. **Experiment validation**: Confirm the required experiment artifacts exist,
   are sanitized, and pass report contract validation.
3. **Promotion review**: Apply the go/no-go criteria below. Do not copy raw
   experiment artifacts into Comptextv7.
4. **Comptextv7 issue/PR**: Open a focused issue or small PR in Comptextv7 only
   when the evidence is safe, owned, and actionable.
5. **Comptextv7 validation**: Run the required local validation commands in
   Comptextv7 and include the results in the PR.
6. **Release decision**: Merge only when the PR remains reversible, contract-safe,
   and free of sensitive material.
7. **Post-release monitoring**: Roll back or follow up if the rollback criteria
   appear after merge.

## Required experiment artifacts

Before promotion, reviewers must verify that the experiment repository produced
all of the following sanitized artifacts:

- `docs/reports/benchmark-summary.json`
- `docs/reports/regression-summary.json`
- `docs/reports/sanitization-summary.json`
- `docs/reports/report-contract-validation-report.md`

These artifacts must be contract-compatible, reviewed, and safe to summarize in a
Comptextv7 issue or PR. They must not contain real Daimler data, customer data,
secrets, credentials, cookies, raw production logs, proprietary payloads, or
unmasked sensitive identifiers.

## Required Comptextv7 checks

Run these commands in `ProfRandom92/Comptextv7` before a promotion PR is marked
ready for review:

```bash
python scripts/repo_intake.py
python scripts/run_checks.py
python scripts/validate_contracts.py
python scripts/generate_contract_fixtures.py
python scripts/validate_api_exports.py
python scripts/generate_project_health_report.py
```

If a command cannot run because of an environment limitation, document the exact
command, the limitation, and why the PR remains safe to review.

## Go criteria

Promotion may proceed only when all of these statements are true:

- The benchmark summary exists and is contract-compatible.
- The regression summary exists and shows no unresolved blocker.
- The sanitization summary exists and contains no unmasked sensitive findings.
- The report contract validation passes in the experiment repository.
- Comptextv7 local checks pass.
- API/export contract validation passes.
- The generated project health report exists at
  `docs/reports/project-health-report.md` and reflects the current validation
  and promotion-readiness snapshot.
- The PR is small and reversible.
- The change has clear ownership in Comptextv7.
- The PR uses synthetic examples only and avoids runtime coupling to the
  experiment repository.

## No-go criteria

Do not promote the finding, and do not open or merge a Comptextv7 implementation
PR, when any of these conditions apply:

- Real Daimler data is present.
- Secrets, credentials, tokens, cookies, or session material are present.
- Raw production logs are present.
- Proprietary payloads or customer data are present.
- A benchmark regression exists without explanation or reviewer acceptance.
- Report contract validation fails.
- Comptextv7 checks fail.
- API/export contract validation fails.
- Project health report generation fails or records missing required local
  validation evidence without an accepted explanation.
- Ownership between the experiment repository and runtime repository is unclear.
- The proposed PR requires runtime coupling to the experiment repository without a
  separate approved issue.

## Rollback criteria

Roll back the Comptextv7 change or open an urgent follow-up when any of these
conditions appear after merge:

- API contract breakage.
- Dashboard export breakage.
- Benchmark degradation beyond the accepted threshold.
- New sanitizer findings.
- Unexpected runtime failures.
- Missing report artifacts.
- Stale or missing project health report after validation, promotion, or release
  readiness changes.
- Evidence that sensitive material entered the repository, dashboard, exports, or
  documentation.

## Security checklist

- [ ] Use synthetic examples only.
- [ ] Do not include real Daimler data.
- [ ] Do not include customer data.
- [ ] Do not include secrets, credentials, tokens, cookies, or session material.
- [ ] Do not include raw production logs.
- [ ] Do not include proprietary payloads or unreleased vendor material.
- [ ] Do not include unmasked VIN/FIN, account, employee, plant, vehicle, or
      workshop identifiers.
- [ ] Summarize experiment evidence instead of copying raw artifacts.
- [ ] Keep generated fixtures deterministic and explicitly synthetic.

## PR checklist

- [ ] PR targets `main` from a feature branch.
- [ ] PR links the tracking issue.
- [ ] PR explains which experiment finding is being promoted.
- [ ] Required experiment artifacts are listed and reviewed.
- [ ] Required Comptextv7 validation commands are run or explicitly documented as
      not required because of a safe environment limitation.
- [ ] `python scripts/generate_project_health_report.py` has refreshed
      `docs/reports/project-health-report.md` for the current PR.
- [ ] Go/no-go decision is documented.
- [ ] Rollback criteria are understood and noted when relevant.
- [ ] PR scope is small, reviewable, and reversible.
- [ ] No new dependency or runtime coupling is introduced unless separately
      approved.

## Agent instructions

Codex/Gemini agents should use this checklist after experiment validation and
before creating a Comptextv7 implementation PR. Agents should:

1. Confirm the required experiment artifacts exist in the experiment repository
   or are summarized by a human reviewer.
2. Apply the go/no-go criteria before changing Comptextv7.
3. Create a Comptextv7 issue when ownership, safety, or release impact is unclear.
4. Keep promotion PRs narrow and avoid unrelated refactors.
5. Run the required Comptextv7 validation commands for implementation PRs.
6. Generate and review `docs/reports/project-health-report.md` when release
   readiness, validation evidence, API/export contracts, or cross-repo promotion
   status changes.
7. Use documentation-only updates when the finding only changes review policy or
   release criteria.
8. Never introduce imports, generated vendor folders, submodules, or CI coupling
   to the experiment repository as part of this checklist.

## Example synthetic promotion record

```yaml
promotion_id: synthetic-promotion-2026-05-11-001
source_repo: ProfRandom92/Comptext-Daimler-Experiment-
target_repo: ProfRandom92/Comptextv7
source_artifacts:
  benchmark_summary: docs/reports/benchmark-summary.json
  regression_summary: docs/reports/regression-summary.json
  sanitization_summary: docs/reports/sanitization-summary.json
  contract_validation: docs/reports/report-contract-validation-report.md
finding_summary: >-
  Synthetic benchmark evidence showed stable dashboard export latency after a
  schema-only fixture update. No raw payloads or production logs were reviewed.
go_decision: go
no_go_findings: []
required_comptextv7_commands:
  - python scripts/repo_intake.py
  - python scripts/run_checks.py
  - python scripts/validate_contracts.py
  - python scripts/generate_contract_fixtures.py
  - python scripts/validate_api_exports.py
  - python scripts/generate_project_health_report.py
security_review:
  synthetic_only: true
  real_daimler_data_present: false
  secrets_present: false
  raw_production_logs_present: false
rollback_watch:
  - API contract breakage
  - dashboard export breakage
  - benchmark degradation beyond accepted threshold
  - new sanitizer findings
  - unexpected runtime failures
  - missing report artifacts
comptextv7_action: Open a small implementation PR linked to the tracking issue.
```
