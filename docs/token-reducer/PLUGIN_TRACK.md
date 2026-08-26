# Plugin Track — Token Reducer Integration

Status: PREP_ONLY

## Goal

Use plugins as modular control/evaluation/packaging surfaces around CompText rather than moving token-reduction logic into opaque runtime hooks.

## Existing CompText Marketplace Plugins

### CompText Context

Current role:

- compile minimal operational context,
- report missing required fields,
- keep ordering/dependencies/blockers/recovery paths explicit,
- emit canonical compact context.

Token Reducer role:

- own task-to-context-plan contract,
- receive path/symbol/evidence candidates from local deterministic discovery,
- enforce token/byte budget,
- return sufficiency/missing-fact status,
- never hide omitted evidence; keep retrieval references.

### CompText Benchmark

Current role:

- Raw vs CompText reproducible comparison,
- separate quality from efficiency,
- preserve evidence.

Token Reducer role:

- own B0/B1/B2/B3/B4/B5/H1 experiment definitions,
- consume token-trajectory records,
- refuse savings claims when optimized context is insufficient,
- report measured values separately from estimates,
- compare task success before token reduction.

### CompText Evidence

Current role:

- verify evidence freshness relative to latest successful mutation.

Token Reducer role:

- prevent compressed summaries/checkpoints from becoming authority by themselves,
- require fresh verification after mutations,
- bind reduced artifacts to raw evidence digests,
- require raw evidence retrieval for disputed/critical claims.

### CompText Guard

Current role:

- local safety hooks without expanding agent context,
- block secret reads and unscoped Git/GitHub/release/deploy writes,
- warn on protected paths.

Token Reducer role:

- enforce "do not optimize away safety-critical data",
- block reducer access to secrets/credential material,
- block automatic config mutation during P0/P1,
- keep safety enforcement local/deterministic rather than prompt-heavy.

## Plugin Eval

Role: independent evaluation gate for the future plugin/skill bundle.

Use it to answer four different questions separately:

1. Static design quality: is the plugin/skill structurally sound?
2. Static token budget: what context overhead does the plugin itself introduce?
3. Measurement plan: what live telemetry is required to make a savings claim?
4. Benchmark result: does the implementation reduce tokens while preserving success?

Planned commands once the target exists:

```bash
plugin-eval analyze <target> --format markdown
plugin-eval explain-budget <target> --format markdown
plugin-eval init-benchmark <target>
plugin-eval benchmark <target> --dry-run
plugin-eval measurement-plan <target>
plugin-eval benchmark <target>
```

Plugin Eval is a gate, not part of the hot model path.

## Plugin Autopilot

Role: packaging/release automation after the implementation and benchmark gates pass.

Planned use:

- package the approved MCP/skills/hooks/assets into the Codex plugin layout,
- validate plugin metadata and expected files,
- prepare marketplace/release artifacts,
- keep packaging separate from token-reducer semantics.

Do not use Plugin Autopilot to design the runtime algorithm or to mutate production plugin configuration during P0/P1.

## stark AI Developer

Role: optional implementation assistant for bounded coding tasks.

Good candidate tasks:

- scaffold a benchmark parser from an already-frozen schema,
- implement isolated serializers/parsers,
- generate focused tests from explicit acceptance criteria,
- refactor a bounded reducer module after behavior is already specified.

Do not treat it as architecture authority, benchmark authority, or completion authority.

## External Open-Source Donors

### Save-The-Token

Use for:

- MCP tool-surface measurement ideas,
- task-specific `enabled_tools` generation,
- instruction routing,
- schema digesting,
- sufficiency-gated benchmark methodology.

Key design lesson: selection wins should be measured separately from compression wins.

### Open330/context-compress

Use for:

- large output indexing,
- FTS/BM25 retrieval,
- bounded model-visible outputs,
- Codex plugin layout patterns.

### Headroom

Use for:

- reversible compression design,
- content-aware reducer ideas,
- output-shaping experiments,
- separate H1 comparison arm.

Do not make Headroom a default transparent proxy until multi-turn Codex tool-surface behavior is regression-tested.

### RTK / squeez

Use for:

- command-specific output reduction,
- low-risk deterministic formatting,
- reversible/raw retrieval patterns.

Prefer command-aware reducers before generic LLM summarization.

## Proposed Plugin Architecture

```text
                      Codex / Agent
                           |
                           v
                CompText Context plugin
                    context contract
                           |
                           v
                 local ctxt/core layer
             route / select / batch / reduce
                           |
              +------------+------------+
              |                         |
              v                         v
       CompText Guard              raw evidence store
         pre-action                      |
              |                          v
              +------ execution ----> CompText Evidence
                                      post-action/freshness
                                              |
                                              v
                                     CompText Benchmark
                                     experiment/result gate
                                              |
                                              v
                                         Plugin Eval
                                       independent audit
                                              |
                                              v
                                      Plugin Autopilot
                                      packaging/release
```

`stark AI Developer` may assist implementation between specification and benchmark, but is intentionally not shown in the authority chain.

## Hot-Path Rule

Keep the runtime path minimal:

```text
Context + local core + Guard + Evidence
```

Keep these out of the hot path:

```text
Plugin Eval
Plugin Autopilot
stark AI Developer
benchmark reporting UI
release tooling
```

This avoids spending context/tokens merely to observe or package the reducer.

## Initial Plugin Gate

Before publishing any new Token Reducer plugin:

```text
[ ] P0 token trajectory reproducible
[ ] B0 baseline captured
[ ] B1 native slimming measured
[ ] B2 selective context measured
[ ] evidence-loss regressions == 0
[ ] CompText Benchmark report generated
[ ] Plugin Eval static analysis passes or findings triaged
[ ] Plugin Eval measurement plan completed
[ ] no secrets/config auto-mutation
[ ] Guard policy reviewed
[ ] Evidence freshness contract verified
[ ] Plugin Autopilot packaging only after all above
```
