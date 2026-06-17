# Hash/chilli CI Artifact Consumption

## Purpose

CFI-03 refines the already-merged CFI-01 contract and CFI-02
`hash-companion-validation` workflow into a structured, cloud-first artifact
publisher. GitHub Actions remains the only execution authority. Local
Hash/chilli consumers read the published metadata for display only and must keep
the degraded local runner fallback when a cloud artifact is unavailable.

## Published artifacts

The `validation-runner-cfi-artifacts` GitHub Actions artifact contains two small
JSON files:

| Path | Purpose | Consumer guidance |
| --- | --- | --- |
| `reports/hash-chilli-cloud-ci-summary.json` | Compact, minified CFI-01 payload for display handoff. | Preferred file for Hash/chilli UI ingestion. |
| `reports/hash-chilli-cloud-ci-result.json` | Pretty-printed CFI-01 payload for human review and CI diagnostics. | Use for review/debug display only; do not parse logs or infer extra state. |

Both files contain the same CFI-01 field set from
`contracts/hash-chilli-cloud-ci-result.schema.json`. The compact summary is not a
new contract version and does not add any fields. `additionalProperties: false`
continues to prevent ad hoc expansion of the Hash/chilli handoff surface.

## Artifact URL behavior

The publisher fills `artifact_url` with the run artifact section URL for the same
GitHub Actions run:

```text
https://github.com/<owner>/<repo>/actions/runs/<run_id>#artifacts
```

GitHub Actions does not expose a stable uploaded artifact ID before the upload
step completes, so consumers should treat this URL as a navigation hint to the
published artifact area, not as a signed download URL. Consumers should still use
`run_url` as the authoritative run provenance link.

## Display-only consumption flow

1. Fetch the latest `validation-runner-cfi-artifacts` artifact from the relevant
   GitHub Actions run.
2. Prefer `reports/hash-chilli-cloud-ci-summary.json` and fall back to
   `reports/hash-chilli-cloud-ci-result.json` only if the compact file is absent.
3. Confirm the visible request matches `runner`, `execution_target`,
   `commit_sha`, `branch`, and optional `request_id` when those values are
   available.
4. Render `status`, `summary`, `run_url`, `artifact_url`, `requested_at`, and
   `completed_at` exactly as CI-produced metadata.
5. If the artifact cannot be found, cannot be read, or does not match the visible
   request, continue showing the existing degraded local runner status.

## Prohibited local behavior

Local Hash/chilli consumers must not respond to these artifacts by running local
validation, builds, tests, formatters, retries, cleanup, reset commands,
generated-output updates, process-isolated tasks, or chilli asset mutations. The
artifact publisher does not change the local runner model: cloud CI publishes the
status, and local UI surfaces render that status without becoming an execution
authority.

## Safety notes

- The artifact payloads contain compact metadata only.
- The payloads do not include raw logs, source contents, user prompts, secrets,
  credentials, local machine paths, customer data, production data, or chilli
  assets.
- The publisher sanitizes invalid `request_id` values to `null` rather than
  publishing uncontracted identifiers.
- Consumers should ignore unknown files in the artifact bundle and rely only on
  the CFI-01 JSON payload files listed above.
