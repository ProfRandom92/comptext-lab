# validation_runner Cloud CI Workflow

## Purpose

CFI-02 adds `hash-companion-validation`, a cloud-backed GitHub Actions workflow
for the `validation_runner` surface. CFI-03 refines artifact publication for the
same workflow by using a structured publisher and uploading both a review result
and a compact JSON summary for consumers. The workflow keeps the CFI-01 authority
model intact: GitHub Actions runs validation in cloud CI, emits the compact
CFI-01 result payload, and uploads that payload as a CI artifact for Hash/chilli
consumers to display.

The workflow does not enable local validation. Local Hash/chilli behavior remains
status-only and degraded when local execution is unavailable; it must not run
builds, tests, validation, retries, cleanup, generated-output updates, or chilli
asset mutations to interpret the result.

## Triggers

The workflow is defined in `.github/workflows/validation_runner.yml` and can run
from these GitHub-hosted entry points:

- `workflow_dispatch`, with an optional `request_id` input to echo a
  Hash/chilli request identifier into the CFI-01 payload.
- `pull_request`, to validate proposed changes in GitHub Actions.
- `push` to `main` or `work`, matching the existing cloud CI branch coverage.

## Cloud workflow behavior

The single `validation-runner` job runs on `ubuntu-latest` and performs only
cloud-hosted work:

1. Captures a UTC request timestamp.
2. Checks out the requested commit or pull request head SHA, including the pull
   request head repository for forked pull requests.
3. Sets up Python 3.11 and syntax-checks the CFI-03 publisher in GitHub
   Actions with `python -m py_compile scripts/publish_hash_chilli_ci_artifacts.py`
   before the workflow uses it.
4. Installs test dependencies in the GitHub runner with
   `python -m pip install -e ".[test]"`; `pyproject.toml` defines the `test`
   optional dependency group used by the existing CI workflow.
5. Runs the cloud validation commands aligned with the existing CI workflow:
   - `python -m pytest`
   - `python dashboard/industrial_dashboard.py --once`
6. Relies on `dashboard/industrial_dashboard.py --once` for the integrated
   dashboard data path that already invokes benchmark, forensic, replay, and
   token telemetry surfaces, avoiding duplicate direct runner calls.
7. Runs `scripts/publish_hash_chilli_ci_artifacts.py` in GitHub Actions to write
   `reports/hash-chilli-cloud-ci-result.json` and the compact
   `reports/hash-chilli-cloud-ci-summary.json` from cloud step outcomes.
8. Validates the result JSON payload against
   `contracts/hash-chilli-cloud-ci-result.schema.json` in GitHub Actions.
9. Adds selected compact payload fields to the GitHub job summary.
10. Uploads both JSON files as the `validation-runner-cfi-artifacts` artifact.
11. Fails the workflow if any required cloud validation step failed or was
    skipped.

Validation steps use `continue-on-error` so the CFI-01 summary artifact is still
written and uploaded for failing runs whenever GitHub Actions reaches the summary
steps. The final enforcement step preserves normal CI pass/fail semantics. The
job also has a bounded timeout so a hung cloud runner cannot block the workflow
indefinitely.

## Artifact contract

The uploaded `validation-runner-cfi-artifacts` artifact contains the CFI-01
payload in two publication forms:

```text
reports/hash-chilli-cloud-ci-summary.json
reports/hash-chilli-cloud-ci-result.json
```

The compact summary is minified for display handoff, while the result file is
pretty-printed for review. Both files carry the same CFI-01 fields and use the
schema in
`contracts/hash-chilli-cloud-ci-result.schema.json`. They include these fields:

| Field | Value source |
| --- | --- |
| `contract` | Constant `hash_chilli_cloud_ci_result`. |
| `contract_version` | Constant `1`. |
| `result_id` | `gha:<github.run_id>:<github.run_attempt>`. |
| `request_id` | Optional `workflow_dispatch` input when it matches the CFI-01 identifier pattern, otherwise `null`. |
| `runner` | Constant `validation_runner`. |
| `execution_target` | Constant `cloud_ci`. |
| `provider` | Constant `github_actions`. |
| `workflow` | Constant `hash-companion-validation`. |
| `status` | `passed`, `failed`, `cancelled`, or `degraded` per the CFI-01 contract. The workflow emits `passed`, `failed`, or `cancelled` from cloud step outcomes. |
| `commit_sha` | Pull request head SHA or triggering commit SHA. |
| `branch` | Pull request head ref or triggering ref name. |
| `run_url` | GitHub Actions run URL. |
| `artifact_url` | GitHub Actions run artifact section URL for the same run. |
| `requested_at` | UTC timestamp captured before checkout. |
| `completed_at` | UTC timestamp captured when the payload is written. |
| `summary` | Compact CI-authored status summary, maximum 240 characters. |
| `local_execution` | Constant `disabled`. |

## Consumer expectations

Hash/chilli consumers should render the artifact as status metadata only. If no
artifact is available, consumers should keep the existing degraded local runner
status rather than attempting local validation or mutating source/assets. See
[`artifact-consumption.md`](artifact-consumption.md) for the CFI-03 consumption
flow and artifact URL behavior.
