# Proposal Mode (Phase 5)

Proposal Mode allows `ctxt` to build a Context Pack, query a provider (e.g. the offline `dummy` provider), and generate a structured, deterministic proposal JSON under `proposals/` without mutating the active repository source files.

## Command Usage

```bash
ctxt propose --provider dummy "Add context inspect"
```

## Generated Artifacts

Executing proposal mode produces two files:
1. `proposals/proposal_<slugified_task>.json` — A task-specific proposal file where `<slugified_task>` is the slugified version of the task description (e.g. `add_context_inspect`).
2. `proposals/proposal.latest.json` — A pointer file containing a copy of the latest generated proposal for quick references and integration checks.

## Schema Specification

The proposal JSON format uses the following schema fields:

* `schema_version`: The version of the proposal schema format (e.g. `"0.1"`).
* `task`: The original user task prompt.
* `rationale`: Descriptive reason for the change.
* `preconditions`: List of build/check commands to verify preconditions.
* `affected_files`: List of files that this proposal suggests modifying.
* `operations`: List of operations to perform. Each operation contains:
  * `op`: Type of operation (e.g. `"patch"`).
  * `path`: Relative path to the target file.
  * `detail`: Detailed description of the proposed patch or edits.
* `validation_commands`: List of verification commands to run after the changes are applied.
* `rollback_strategy`: Command or action to undo the changes.
* `risk_notes`: Potential risks identified for this proposal.

## Offline Execution / Dummy Provider

During offline validation and testing, using the `--provider dummy` argument retrieves a deterministic mock response from the Dummy Provider, ensuring no network calls are executed. The proposal output is fully generated using this mock model output.
