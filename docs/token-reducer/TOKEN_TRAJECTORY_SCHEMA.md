# Token Trajectory Measurement Contract

Status: PREP_ONLY

## Purpose

Define a neutral measurement record for Raw vs CompText runs. The record must support actual token-reduction analysis without confusing:

- raw token reduction,
- prompt-cache reuse,
- subscription/credit weighting,
- cheaper model pricing,
- wall-clock speedups.

## Record Identity

Each run records:

```text
run_id
benchmark_case_id
arm_id
repo
commit_sha
branch_or_detached
working_tree_state_digest
model
reasoning_effort
client_surface
client_version
permissions_profile
plugin_set_digest
tool_surface_digest
started_at
ended_at
```

## Token Counters

Required when available from the client/runtime:

```text
input_tokens_total
cached_input_tokens
uncached_input_tokens
output_tokens_total
reasoning_tokens
```

Derived:

```text
non_reasoning_output_tokens = output_tokens_total - reasoning_tokens
model_tokens_total = input_tokens_total + output_tokens_total
```

Do not subtract cached input from actual token volume. Cached input is reported separately because it remains useful for diagnosing repeated model turns.

## Agent Loop Counters

```text
model_turns
tool_calls
tool_batches
wait_only_model_turns
poll_only_model_turns
subagent_count
subagent_model_turns
compaction_count
```

Derived:

```text
avg_tool_calls_per_model_turn
batching_ratio
wait_poll_turn_ratio
```

## Context Loading Counters

```text
candidate_paths_discovered
paths_selected
files_loaded_full
files_loaded_partial
symbol_outlines_loaded
context_bytes_selected
context_bytes_delivered
context_token_estimate_delivered
re_reads
active_retrieval_calls
```

## Tool Output Counters

```text
raw_tool_output_bytes
reduced_tool_output_bytes
model_visible_tool_output_bytes
raw_artifact_count
reduced_artifact_count
raw_retrieval_count
```

Derived:

```text
tool_output_delivery_ratio = model_visible_tool_output_bytes / raw_tool_output_bytes
tool_output_reduction_ratio = reduced_tool_output_bytes / raw_tool_output_bytes
```

A small delivery ratio is not sufficient evidence of success. Correctness/evidence gates must also pass.

## Quality / Outcome

```text
task_success
acceptance_checks_total
acceptance_checks_passed
tests_passed
tests_failed
verification_errors
evidence_loss_regressions
false_completion_claims
manual_intervention_count
```

`task_success` must come from case-specific acceptance criteria, not from the model saying it succeeded.

## Evidence Integrity

```text
latest_successful_mutation_at
latest_verification_at
verification_fresh_after_mutation
raw_evidence_retrievable
raw_evidence_digest
checkpoint_digest
```

## Performance

```text
wall_time_ms
model_wait_ms
tool_execution_ms
retrieval_ms
compression_ms
```

## Primary Comparison Metrics

Compare each optimized arm against B0 baseline:

```text
success_rate_delta
median_model_tokens_delta
median_input_tokens_delta
median_output_tokens_delta
median_reasoning_tokens_delta
median_model_turns_delta
median_model_visible_tool_bytes_delta
median_files_loaded_delta
median_wall_time_delta
```

Primary product KPI:

```text
tokens_per_success = sum(model_tokens_total) / successful_runs
```

Also report:

```text
uncached_input_tokens_per_success
cached_input_tokens_per_success
model_turns_per_success
raw_tool_output_bytes_per_success
model_visible_tool_output_bytes_per_success
```

## Benchmark Integrity Rules

1. Same frozen repo state for matched A/B runs.
2. Same task outcome and acceptance criteria.
3. Same model and reasoning effort unless the tested arm explicitly targets routing.
4. Same permissions.
5. Same client version where possible.
6. Record tool/plugin surface differences explicitly.
7. Do not count insufficient-context runs as savings wins.
8. Do not claim whole-session savings from one compressed tool output.
9. Preserve failed runs in the dataset.
10. Separate measured counters from estimates.

## Minimal JSON Shape

```json
{
  "schema": "comptext.token_trajectory.v1",
  "identity": {
    "run_id": "",
    "benchmark_case_id": "",
    "arm_id": "B0",
    "repo": "",
    "commit_sha": "",
    "model": "",
    "reasoning_effort": ""
  },
  "tokens": {
    "input_tokens_total": null,
    "cached_input_tokens": null,
    "uncached_input_tokens": null,
    "output_tokens_total": null,
    "reasoning_tokens": null
  },
  "agent_loop": {
    "model_turns": 0,
    "tool_calls": 0,
    "tool_batches": 0,
    "wait_only_model_turns": 0,
    "poll_only_model_turns": 0,
    "subagent_count": 0,
    "compaction_count": 0
  },
  "context": {
    "candidate_paths_discovered": 0,
    "paths_selected": 0,
    "files_loaded_full": 0,
    "files_loaded_partial": 0,
    "context_bytes_delivered": 0,
    "re_reads": 0
  },
  "tool_output": {
    "raw_tool_output_bytes": 0,
    "model_visible_tool_output_bytes": 0,
    "raw_retrieval_count": 0
  },
  "quality": {
    "task_success": false,
    "acceptance_checks_total": 0,
    "acceptance_checks_passed": 0,
    "evidence_loss_regressions": 0,
    "false_completion_claims": 0
  },
  "evidence": {
    "verification_fresh_after_mutation": false,
    "raw_evidence_retrievable": false,
    "raw_evidence_digest": "",
    "checkpoint_digest": ""
  },
  "performance": {
    "wall_time_ms": 0
  }
}
```

## Plugin Eval Mapping

Plugin Eval should be used as an independent evaluator of the future Token Reducer plugin/skill bundle.

Planned workflow once an implementation path exists:

```text
plugin-eval analyze <target> --format markdown
plugin-eval explain-budget <target> --format markdown
plugin-eval init-benchmark <target>
plugin-eval benchmark <target> --dry-run
plugin-eval measurement-plan <target>
plugin-eval benchmark <target>
```

Static estimates and measured harness results must remain visibly separate.

## Gate

P0 is complete only when a small fixed fixture produces reproducible token-trajectory JSON twice with no unexplained field drift and the quality/evidence fields are machine-checkable.
