# Hash/chilli Cloud CI Result Contract

## Status

CFI-01 defines this document and
`contracts/hash-chilli-cloud-ci-result.schema.json` as the authoritative Cloud CI
result contract for Hash/chilli handoff. The contract is cloud-first: Cloud/GitHub
CI produces the result, performs any schema validation, and publishes the compact
payload for the local Hash companion and chilli UI to display.

Local Hash/chilli consumers must not execute validation, builds, tests,
formatters, retries, cleanup, reset, generated-output updates, or process-isolated
tasks to interpret this contract. When local execution is degraded, the existing
status-only fallback model remains intact and Cloud/GitHub CI remains the result
authority.

## Consumer model

The local UI consumes this payload as display state only:

1. Read the latest published Cloud CI result payload from the configured handoff
   channel.
2. Match `runner`, `execution_target`, `commit_sha`, `branch`, and optional
   `request_id` to the visible companion request when available.
3. Render `status`, `summary`, `run_url`, `artifact_url`, and timestamps.
4. If no payload is available, continue rendering the degraded local fallback
   status without attempting local validation.

The local UI may check for field presence before display, but it must not treat
local schema validation as authoritative and must not replace missing or malformed
Cloud CI results with local execution.

## Required fields

| Field | Type | Meaning | Consumer behavior |
| --- | --- | --- | --- |
| `contract` | string constant | Contract identifier, always `hash_chilli_cloud_ci_result`. | Route payload to the Hash/chilli CI result renderer. |
| `contract_version` | integer constant | Contract version, currently `1`. | Use for deterministic compatibility checks. |
| `result_id` | string | Stable CI-produced identifier for this result payload. | Use as a UI key and deduplication value. |
| `runner` | string enum | Producing logical runner, currently `validation_runner`. | Confirm the result belongs to the validation surface. |
| `execution_target` | string constant | Execution authority, always `cloud_ci`. | Display Cloud CI authority; never run locally. |
| `provider` | string enum | CI provider, currently `github_actions`. | Label the run source. |
| `workflow` | string | CI workflow name that produced the result. | Display workflow provenance. |
| `status` | string enum | One of `queued`, `in_progress`, `passed`, `failed`, `cancelled`, or `degraded`. | Render state without recomputing it locally. |
| `commit_sha` | string | Full 40-character git commit SHA under test. | Bind result to a revision. |
| `branch` | string | Branch or ref name under test. | Display result scope. |
| `run_url` | URI string | CI run URL. | Link to authoritative CI run. |
| `artifact_url` | URI string or null | Sanitized artifact/report URL when available. | Link when present; hide when null. |
| `requested_at` | date-time string | Request or queue time in ISO 8601/RFC 3339 form. | Render request time. |
| `completed_at` | date-time string or null | Completion time; null while queued or running. | Render completion time when present. |
| `summary` | string | CI-produced human-readable summary, maximum 240 characters. | Display exactly as summary text. |
| `local_execution` | string constant | Local execution policy, always `disabled`. | Preserve degraded local fallback and cloud-first authority. |

## Optional fields

| Field | Type | Meaning | Consumer behavior |
| --- | --- | --- | --- |
| `request_id` | string or null | Hash/chilli request identifier when a local request triggered the run. | Associate CI result with a pending request when present. |

No other fields are part of CFI-01. Producers must keep payloads compact and must
not add ad hoc fields for raw logs, user prompts, repository secrets, machine
paths, or unredacted diagnostics.

## Status semantics

| Status | Meaning |
| --- | --- |
| `queued` | Cloud CI accepted the request but has not started execution. |
| `in_progress` | Cloud CI is running the authoritative validation work. |
| `passed` | Cloud CI completed successfully. |
| `failed` | Cloud CI completed and found a validation/build/test failure. |
| `cancelled` | Cloud CI stopped before producing a pass/fail outcome. |
| `degraded` | Cloud CI could not produce a normal result; local fallback remains status-only. |

`completed_at` must be `null` for `queued` and `in_progress` results. For
`passed`, `failed`, `cancelled`, and `degraded`, `completed_at` should contain the
CI completion timestamp when known.

## Canonical compact example

```json
{
  "contract": "hash_chilli_cloud_ci_result",
  "contract_version": 1,
  "result_id": "gha:1234567890:1",
  "request_id": "hash:req-2026-05-12T00:00:00Z",
  "runner": "validation_runner",
  "execution_target": "cloud_ci",
  "provider": "github_actions",
  "workflow": "hash-companion-validation",
  "status": "passed",
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "branch": "work",
  "run_url": "https://github.com/ProfRandom92/Comptextv7/actions/runs/1234567890",
  "artifact_url": "https://github.com/ProfRandom92/Comptextv7/actions/runs/1234567890/artifacts/987654321",
  "requested_at": "2026-05-12T00:00:00Z",
  "completed_at": "2026-05-12T00:05:00Z",
  "summary": "Cloud CI validation passed for the requested commit.",
  "local_execution": "disabled"
}
```

## Security and privacy guarantees

- The contract contains metadata and a short CI-authored summary only.
- The contract does not carry raw logs, source file contents, user prompts,
  secrets, credentials, tokens, local usernames, local machine paths, customer
  data, production data, or chilli pet assets.
- `artifact_url` may point to a sanitized CI artifact, but the payload itself does
  not embed artifact contents.
- Local Hash/chilli consumers must not use the payload as permission to execute
  local validation or mutate local source/assets.
- Cloud/GitHub CI is responsible for producing and validating the payload before
  publication; local consumers render the published result as status metadata.

## Schema

The machine-readable schema is
`contracts/hash-chilli-cloud-ci-result.schema.json`. It fixes the CFI-01 field
set with `additionalProperties: false` so producers cannot expand the handoff
surface without a future contract revision.
