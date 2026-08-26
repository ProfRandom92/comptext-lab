# CompText Token Reducer — Preparation Plan

Status: PREP_ONLY
Branch: `feature/token-reducer-prep`
Baseline: `main@b997f62503066a81ed8ec53b3b9b154c064e00a8`
Date: 2026-08-26

## Mission

Reduce the actual model tokens required per successful agent task without weakening correctness, evidence, or safety.

This work targets:

- fewer uncached input tokens,
- fewer cached input tokens where repeated model turns can be eliminated,
- fewer reasoning/output tokens on routine continuations,
- fewer model round-trips,
- fewer model-visible tool-output bytes,
- fewer files loaded into model context,
- preserved/retrievable raw evidence,
- equal-or-better task success.

This work does **not** target quota bypass, subscription-limit bypass, or merely cheaper model pricing.

## Product Boundary

`ctxt` remains a deterministic local contract/runtime boundary. It does not become an external-agent executor or provider proxy.

The token-reducer design therefore follows:

```text
Human / Codex / Antigravity
        |
        v
CompText task/context contracts
        |
        +--> task-specific tool surface plan
        +--> selective context plan
        +--> local deterministic compute plan
        +--> batch execution plan
        +--> bounded/reversible result contract
        +--> evidence/checkpoint contract
        |
        v
External agent/runtime executes the plan
```

## Core Pipeline

```text
TASK
  |
  v
1. ROUTE
   - classify task intent
   - identify required repo surfaces
   - identify required tools/skills
  |
  v
2. SELECT BEFORE LOAD
   - path ranking
   - symbol/AST outlines
   - git/diff evidence
   - bounded excerpts
   - only promote to full files when required
  |
  v
3. COMPUTE LOCALLY
   - rg / git / AST / jq / tests / metadata
   - deterministic filtering and aggregation
  |
  v
4. BATCH
   - group independent read-only operations
   - avoid model re-entry between already-known operations
  |
  v
5. REDUCE OUTPUT
   - retain raw output locally
   - expose bounded structured summaries
   - keep raw retrieval ids/hashes
  |
  v
6. CHECKPOINT
   - compact verified state
   - mutation/evidence freshness
   - next action
  |
  v
MODEL / AGENT
```

Principle order:

> select -> compute -> batch -> compress -> verify

Compression is not the first line of defense.

## Existing CompText Components To Reuse

### `crates/comptext-core`

Use for shared deterministic primitives, contract types, stable serialization, hashing, and validation helpers.

### `crates/comptext-cli` (`ctxt`)

Use for local deterministic JSON contracts. Candidate future surfaces are contract-level only:

- `context plan`
- `batch plan`
- `checkpoint create`
- `measure summarize`

Names are provisional until implementation review against the existing CLI schema.

### `python/comptextv7`

Use as donor/research layer for replay validation, evidence survival, and benchmark methodology.

### `comptext-sparkctl`

Use as donor for evidence/context handling where existing primitives fit.

## CompText Plugin Roles

The token reducer should integrate the existing marketplace plugins instead of creating parallel behavior.

- **CompText Context** — task-scoped minimum operational context and missing-field detection.
- **CompText Benchmark** — Raw vs CompText experiments; quality and efficiency reported separately.
- **CompText Evidence** — freshness gate: verification must be newer than the latest successful mutation.
- **CompText Guard** — keep safety enforcement outside model context where possible; block unsafe/unscoped actions without expanding prompts.

The plugin integration contract is detailed in `PLUGIN_TRACK.md`.

## External Projects — Role, Not Dependency By Default

### Save-The-Token

Role: design/benchmark donor for MCP tool-surface measurement, task-routed instructions, `enabled_tools` allowlists, schema digests, and sufficiency-gated savings claims.

Adopt conceptually first. Do not add as mandatory runtime dependency during P0/P1.

### Open330/context-compress

Role: design/code donor for indexed large-result handling, FTS/BM25 retrieval, bounded tool-output responses, and Codex plugin packaging patterns.

### Headroom

Role: experimental comparison arm for reversible compression, content-aware reducers, proxy/MCP interception, and output-shaping ideas.

Do not place transparently in the default Codex path before compatibility and multi-turn tool-surface invariants are proven.

### RTK / squeez

Role: command-aware tool-output reduction donors. Prefer deterministic reducers for git/test/log commands before generic language compression.

### Aider / semantic code-navigation projects

Role: donor for repo maps, symbol ranking, dependency hints, and AST-based selective loading.

## P0 — Measurement First

Before implementing routing or compression, define and validate a token-trajectory record.

Required metrics:

```text
input_tokens
cached_input_tokens
uncached_input_tokens
output_tokens
reasoning_tokens
model_turns
tool_calls
files_loaded
raw_tool_output_bytes
delivered_tool_output_bytes
retrieval_count
reread_count
compactions
subagent_turns
wall_time_ms
task_success
```

Primary KPI:

```text
tokens_per_success
```

Secondary KPIs:

```text
model_turns_per_success
tool_output_delivery_ratio
files_loaded_per_success
latency_per_success
```

Never claim session-level savings from a single compressed payload.

## P1 — Native/Low-Risk Savings

Implement only after P0 schema/harness agreement.

1. Measure MCP tool-schema surface per task.
2. Produce task-specific Codex `enabled_tools` recommendations/snippets.
3. Route repo instructions by task instead of loading all guidance.
4. Preserve progressive disclosure through skills.
5. Batch independent read-only inspections into one external-agent execution stage.
6. Avoid model-mediated busy polling.
7. Bound tool output before it becomes model-visible.
8. Keep raw evidence retrievable.

## P2 — Selective Context Compiler

Candidate levels:

```text
L0 repo topology
L1 symbols/signatures/AST outline
L2 relevant excerpts
L3 full file only when required
```

A context plan must include:

- task query,
- selected paths,
- why each path is selected,
- evidence ids,
- token/byte budget,
- omitted-but-retrievable candidates,
- missing facts,
- sufficiency status.

## P3 — Batch Plan

A batch plan must distinguish:

- independent read-only work: may run concurrently,
- dependent/adaptive work: sequential,
- approval-sensitive work: sequential,
- conflicting mutations: sequential,
- waits/resumes: event/process driven where possible.

Goal: reduce outer model/tool cycles without expanding scope.

## P4 — Reversible Output Reduction

Every reducer result must retain:

- raw artifact id,
- raw byte count,
- reduced byte/token estimate,
- transform id/version,
- critical evidence preserved,
- retrieval path/contract,
- fail-open-to-raw behavior when reduction is unsafe.

Never summarize away exact evidence required for correctness.

## P5 — Verified Checkpoints

Use short checkpoint artifacts instead of indefinitely extending model threads.

Checkpoint minimum:

- goal,
- repo/branch/head,
- dirty paths,
- verified claims,
- latest successful mutation,
- fresh evidence after that mutation,
- changed files,
- tests/validation,
- blockers,
- next action,
- evidence digest.

## Benchmark Arms

```text
B0 normal agent baseline
B1 native tool/instruction slimming
B2 B1 + selective context
B3 B2 + batching
B4 B3 + reversible output reduction
B5 B4 + verified checkpoint handoff
H1 baseline + Headroom (comparison only)
```

Hold constant where possible:

- frozen repository commit,
- task prompt/outcome,
- model,
- reasoning effort,
- permissions,
- tool/plugin set except the tested layer,
- expected success criteria.

## Initial Promotion Gate

`COMPTEXT_TOKEN_REDUCER_V1_PASS` requires:

```text
success_rate >= baseline
median_total_input_tokens <= baseline * 0.80
median_model_turns_on_batchable_tasks <= baseline * 0.80
median_model_visible_noisy_tool_bytes <= baseline * 0.40
evidence_loss_regressions == 0
raw_evidence_retrievable == true
```

These are initial engineering gates, not public performance claims.

## Explicit Non-Goals For Prep Branch

- no provider interception,
- no Codex wrapping,
- no automatic MCP config mutation,
- no agent execution,
- no Stage 8 Windows Agent changes,
- no `runtime/runtime-v2` changes,
- no marketplace release,
- no public token-savings claim.

## Next Implementation Decision

When Codex is available again, start by implementing **P0 only** and proving that the measurement record is trustworthy before any optimization layer is promoted.
