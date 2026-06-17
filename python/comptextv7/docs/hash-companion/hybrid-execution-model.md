# Hash/chilli Hybrid Execution Model

## Status

The Hash/chilli companion architecture uses a hybrid execution model while the
local Windows sandbox is unreliable. The local stop condition is:

```text
CreateProcessAsUserW failed: 5
```

When this condition is present, local execution is considered unavailable. The
local runner must not retry, validate, mutate files, run builds, or start any
process-isolated task. Heavy execution is Cloud/GitHub CI-backed by default until
the local sandbox is repaired and this document is superseded by a follow-up
architecture decision.

## Scope

This plan applies to the Hash companion architecture and the chilli/hatch-pet UI
integration only. It does not change chilli pet assets or source behavior in
`C:\Comptextv7`.

## Hybrid model

| Layer | Execution authority | Required behavior |
| --- | --- | --- |
| chilli/hatch-pet UI | Local | Remains a local user interface for companion status, requests, and CI results. |
| Hash companion manifest | Local | Remains local and describes companion capabilities, request metadata, degraded status, and CI handoff endpoints. |
| Hash companion runner | Local status/request layer only | Accepts or displays requested work, records status, and hands execution requests to Cloud/GitHub CI. It does not execute heavy tasks locally. |
| `validation_runner` | Cloud/GitHub CI by default | Runs validation through the configured CI workflow and treats CI output as authoritative. |
| Local fallback | Status-only | Reports degraded status and the hard stop reason; it never executes validation or retries local sandbox execution. |

## Local responsibilities

The local environment is responsible for user experience and state visibility:

1. Keep the chilli/hatch-pet UI running locally.
2. Keep the Hash companion manifest local and readable by the UI.
3. Display companion status, queued/requested work, and Cloud/GitHub CI results.
4. Capture user requests, perform local sanitization (masking/hashing), and route them to the cloud-backed execution path.
5. Report local runner degradation when `CreateProcessAsUserW failed: 5` is
   observed.
6. Refuse local execution for validation, builds, tests, formatters, execution
   retries, mutation, cleanup, reset, generated-output updates, or
   process-isolated tasks while the stop condition remains active.

## Cloud/GitHub CI responsibilities

Cloud/GitHub CI is the execution authority for heavy work:

1. Run `validation_runner` by default.
2. Run validation, tests, builds, companion checks, and any task that requires
   reliable sandboxed process creation.
3. Publish structured run metadata for the local Hash companion and chilli UI.
4. Treat the CI run result as authoritative for pass/fail/degraded validation
   state.
5. Attach logs and artifacts needed for triage.
6. Identify the commit/SHA, branch, workflow name, run URL, timestamp, and
   triggered request identifier for each result.

## Degraded-mode behavior

When the local runner detects or is configured with the hard stop condition, it
must enter degraded mode:

- `mode`: `degraded`
- `local_execution`: `disabled`
- `reason`: `CreateProcessAsUserW failed: 5`
- `action`: report status only
- `execution_target`: Cloud/GitHub CI

In degraded mode the local runner may:

- render the status in chilli/hatch-pet UI;
- show request handoff state;
- show the latest known Cloud/GitHub CI result;
- provide a link or identifier for the CI run;
- queue a request for CI handoff if the configured request channel supports it.

In degraded mode the local runner must not:

- run validation locally;
- retry local sandbox creation;
- run builds, tests, formatters, cleanups, resets, or generated-output updates;
- modify chilli pet assets;
- mutate comptextv7 source behavior.

## `validation_runner` plan

`validation_runner` is Cloud/GitHub CI-backed by default. The local Hash
companion should resolve validation requests as follows:

1. Read the local companion manifest.
2. Detect the default execution target from configuration.
3. If the target is `cloud_ci`, create or display a CI validation request.
4. If the local runner is degraded, return a status-only response immediately.
5. Display the latest CI result when available.
6. Never fall back to local execution while `CreateProcessAsUserW failed: 5` is
   active.

The local fallback response should use this shape:

```json
{
  "runner": "validation_runner",
  "mode": "degraded",
  "local_execution": "disabled",
  "reason": "CreateProcessAsUserW failed: 5",
  "execution_target": "cloud_ci",
  "status_only": true,
  "message": "Local validation is disabled; use Cloud/GitHub CI for authoritative validation."
}
```

## CI result contract

Cloud/GitHub CI publishes authoritative result metadata for the local UI and
manifest through the CFI-01 contract in
[`cloud-ci-result-contract.md`](cloud-ci-result-contract.md) and the
machine-readable schema at
`contracts/hash-chilli-cloud-ci-result.schema.json`. The local UI consumes this
payload as display state only; it must not run local validation, retries, builds,
tests, formatters, cleanup, reset, generated-output updates, or process-isolated
tasks to interpret a CI result.

The CFI-01 field set is deterministic and compact: `contract`,
`contract_version`, `result_id`, optional `request_id`, `runner`,
`execution_target`, `provider`, `workflow`, `status`, `commit_sha`, `branch`,
`run_url`, `artifact_url`, `requested_at`, `completed_at`, `summary`, and
`local_execution`.

## Re-enable criteria for local execution

Local execution must remain disabled until all of the following are true:

1. The Windows sandbox no longer returns `CreateProcessAsUserW failed: 5`.
2. A follow-up architecture decision explicitly permits local execution.
3. The companion manifest default is changed away from `cloud_ci`.
4. Local validation is intentionally reintroduced with documented guardrails.

Until those criteria are met, `CreateProcessAsUserW failed: 5` is a hard local
stop condition.
