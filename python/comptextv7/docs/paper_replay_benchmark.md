# Paper replay benchmark

The paper replay benchmark is a deterministic Comptextv7 validation scenario for
operational-state preservation from dense academic text. It uses checked-in text
fixtures for three papers and produces a reproducible JSON artifact at
`artifacts/paper_replay_results.json`.

Target fixtures:

- `prefixguard`: **PrefixGuard: From LLM-Agent Traces to Online Failure-Warning Monitors**
- `fate`: **FATE: Future-State-Aware Scheduling for Heterogeneous LLM Workflows**
- `self_consolidating`: **Self-Consolidating Language Models: Continual Knowledge Incorporation from Context**

## Replay pipeline

The implemented pipeline is:

```text
excerpt
→ state extraction
→ compact representation
→ replay reconstruction
→ deterministic validator
→ metrics JSON
```

The detailed methodology is documented in `docs/benchmarks/paper_replay.md`.
The runner lives in `tests/utils/paper_replay_runner.py`. It can be executed
locally or in CI with:

```bash
python -m tests.utils.paper_replay_runner
```

That command rewrites `artifacts/paper_replay_results.json` using deterministic
ordering, sorted JSON keys, stable separators, and checked-in fixtures only.

## Deterministic extraction

The extraction stage does not infer meaning. It uses deterministic text
operations only:

- exact `SECTION: ...` headers for `problem`, `method`, `metrics`,
  `limitations`, and `deployment_relevance`;
- sentence-window selection for the derived `baselines` field;
- exact keyword matching for required entities;
- deterministic entity extraction for canonical operational entities;
- deterministic word-token counting with a repository-local regular expression;
- normalized keyword extraction with a fixed stop-word list;
- bounded keyword budgets per field to avoid storing large verbatim excerpts;
- field-presence checks for every operational field.

The structured operational state contains these fields:

```json
{
  "problem": "...",
  "method": "...",
  "metrics": "...",
  "baselines": "...",
  "limitations": "...",
  "deployment_relevance": "...",
  "entities": ["..."],
  "required_entities": ["..."]
}
```

All values are produced from fixture text. There is no LLM judge, no embedding
model, no cosine similarity, no vector database, no external API, no PDF parser,
and no heavyweight dependency.

## Compact representation and replay reconstruction

The compact representation stores bounded normalized keyword lists, a sorted
required-entity list, and a deliberately reduced sorted operational-entity list
rather than raw paper prose. It uses short transport keys and per-field keyword
budgets so the compact representation is smaller than the fixture excerpt. Replay
reconstruction rebuilds the operational-state object from that compact
representation. The validator compares `original_state` and `replayed_state`; it
does not compare free-form summaries.

This matters because the benchmark is replay/state-preservation oriented. A
successful replay means that the typed operational fields needed for audit are
still present after compaction and reconstruction, not that a generated summary
sounds good.

## Metric derivation

The public artifact schema is:

```json
{
  "aggregate": {
    "avg_compression_ratio": 1.347063,
    "avg_entity_retention_rate": 0.86526,
    "avg_limitation_survival_rate": 0.772727,
    "avg_metric_survival_rate": 0.850446,
    "avg_replay_consistency": 0.791667,
    "avg_section_survival_rate": 0.888889,
    "paper_count": 3
  },
  "benchmark": "paper_replay_bench",
  "papers": [
    {
      "paper": "<paper_name>",
      "entity_retention_rate": 0.863636,
      "section_survival_rate": 0.833333,
      "limitation_survival_rate": 0.75,
      "metric_survival_rate": 0.774194,
      "compression_ratio": 1.424837,
      "replay_consistency": 0.75,
      "original_token_count": 218,
      "compact_token_count": 153,
      "replay_token_count": 164
    }
  ]
}
```

The values above are examples of the schema shape, including the deterministic
aggregate block. The checked-in artifact is regenerated from the fixtures and
should be treated as the measured source of truth.

Metrics are derived as follows:

- `entity_retention_rate`: replayed canonical operational entities divided by
  canonical operational entities extracted from the original fixture. Required
  entities are retained separately and must remain present after replay.
- `section_survival_rate`: survived operational text fields divided by the six
  text fields (`problem`, `method`, `metrics`, `baselines`, `limitations`, and
  `deployment_relevance`).
- `limitation_survival_rate`: normalized keyword overlap between original and
  replayed `limitations` fields.
- `metric_survival_rate`: normalized keyword overlap between original and
  replayed `metrics` fields.
- `compression_ratio`: deterministic original fixture token count divided by
  compact token count, so values greater than `1.0` indicate actual compression.
- `replay_consistency`: mathematically derived as
  `surviving_operational_fields / total_operational_fields`, where the eight
  operational fields are the six text fields plus `entities` and
  `required_entities`. Text-field survival is determined by fixed normalized
  keyword-overlap thresholds; list-field survival is determined by deterministic
  entity retention or exact required-entity retention.
- `original_token_count`, `compact_token_count`, and `replay_token_count`:
  deterministic regex token counts over the fixture excerpt, compact
  representation, and replay representation respectively.
- `aggregate`: deterministic averages over all paper rows plus `paper_count`,
  with normalized float precision for stable CI diffs.

## Why this differs from summarization

Summarization rewards fluent condensation. This benchmark rewards deterministic
state survival. The replay validator does not ask whether prose is elegant,
complete, or semantically equivalent. It asks whether specific operational
fields and required paper entities survived a reproducible compaction/replay
path.

## Why this differs from semantic evaluation

Semantic evaluation often depends on model judgments, embeddings, fuzzy
similarity, or external scoring services. This benchmark intentionally avoids
all of those. Every score is computed by local string operations, keyword-set
overlap, exact required-entity retention, bounded operational-entity retention,
and field-presence checks. That keeps CI runs reproducible and audit-friendly.

## Showcase readiness

For the Comptextv7 showcase, the benchmark demonstrates that dense technical
inputs can be converted into compact, replayable operational state with visible
retention metrics. Enterprise reviewers can inspect:

- exactly which papers were replayed;
- exactly which token counts were measured;
- exactly how field survival contributed to `replay_consistency`;
- the deterministic artifact emitted by CI;
- the absence of external services or subjective model judging.

This makes the benchmark suitable for cloud-first CI artifact publishing,
release gating, and audit diffs while remaining small enough to run on every
pull request.

## Non-goals

This benchmark is not:

- a PDF ingestion system;
- an OCR/layout reconstruction workflow;
- an LLM evaluation framework;
- an embedding or semantic-similarity benchmark;
- a generic academic-paper leaderboard;
- a test of full-paper recall.

It is a deterministic replay benchmark for operational-state preservation under
compaction and reconstruction.
