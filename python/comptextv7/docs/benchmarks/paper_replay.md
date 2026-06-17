# Paper replay benchmark methodology

## Purpose

The paper replay benchmark validates Comptextv7 as deterministic
operational-state preservation infrastructure. It checks whether dense technical
paper excerpts can be reduced to compact operational state, replayed, and audited
with reproducible metrics.

It is not a general AI memory system benchmark and it is not a prose-summary
quality benchmark.

## Deterministic replay philosophy

The benchmark uses checked-in text fixtures and local string operations only.
Each run follows the same pipeline:

```text
paper excerpt
→ deterministic state extraction
→ bounded operational-state compaction
→ replay reconstruction
→ deterministic validation
→ stable JSON artifact
```

There are no timestamps, random seeds, network calls, service dependencies, or
model calls in the artifact path. Stable paper ordering, sorted JSON keys,
normalized numeric precision, and newline-terminated UTF-8 output keep CI and Git
diffs clean.

## Operational-state compression vs summarization

Operational-state compression keeps the fields needed to replay and audit the
paper's engineering claims:

- problem;
- method;
- metrics;
- baselines;
- limitations;
- deployment relevance;
- canonical operational entities;
- required entities.

The compact representation stores bounded normalized keywords and sorted entity
lists. It intentionally does not store large verbatim excerpts or try to produce
fluent prose. A compact replay can lose wording while still preserving the state
needed for deterministic audit.

## Why LLMs and embeddings are excluded

LLM judging, embeddings, cosine similarity, vector databases, and external APIs
are intentionally excluded because they make benchmark interpretation harder for
infrastructure review:

- they can change independently of the repository;
- they can introduce nondeterministic outputs;
- they make exact CI artifact diffs harder to explain;
- they blur whether the benchmark is measuring replay preservation or model
  preference.

The benchmark therefore relies on exact section headers, regex/token extraction,
keyword overlap, entity retention, and field-survival checks.

## Survival metrics

Each paper row reports deterministic metrics:

- `entity_retention_rate`: replayed canonical operational entities divided by
  original canonical operational entities.
- `section_survival_rate`: fraction of replay text fields that meet fixed
  keyword-overlap survival thresholds.
- `metric_survival_rate`: normalized keyword overlap for the `metrics` field.
- `limitation_survival_rate`: normalized keyword overlap for the `limitations`
  field.
- `compression_ratio`: `original_token_count / compact_token_count`; values
  greater than `1.0` indicate that the compact representation is smaller than the
  original fixture.
- `original_token_count`, `compact_token_count`, and `replay_token_count`:
  deterministic regex token counts over the corresponding representation.

The artifact also includes an `aggregate` block with deterministic averages over
all paper rows and `paper_count`.

## Replay consistency

`replay_consistency` is not a confidence score. It is computed as:

```text
surviving_operational_fields / total_operational_fields
```

The operational fields are the six text fields plus `entities` and
`required_entities`. Text fields survive when normalized keyword overlap meets a
fixed threshold. Required entities must match exactly. Optional operational
entities are intentionally compacted and may degrade.

## Why imperfect replay is expected

Perfect replay across all papers would imply that the compact representation is
preserving nearly the full operational text. This benchmark expects controlled,
deterministic degradation: required entities remain present, but optional
entities and some wording are removed. That tradeoff makes the benchmark closer
to operational compression than structured duplication.

## Why dense papers are useful stress tests

Dense academic paper excerpts combine method claims, metrics, baselines,
limitations, named systems, benchmark names, and deployment caveats in a small
space. Losing a single entity or limitation can change audit interpretation.
That makes them useful stress tests for replay continuity and state survival.

## Enterprise and audit relevance

For enterprise review, the artifact is intended to answer concrete reliability
questions:

- What operational state was extracted?
- How much smaller is the compact representation?
- Which replay fields survived deterministic validation?
- Are required entities retained?
- Are aggregate benchmark results stable across CI runs?

Because the artifact is deterministic, reviewers can diff it across commits and
trace metric changes to code or fixture changes rather than opaque model
behavior.

## Adversarial continuity perspective

The benchmark treats compaction as an adversarial continuity boundary: replay has
to preserve enough operational state after redundant prose and optional entities
are removed. The result is a small, auditable signal about continuity under
compression, not a broad semantic equivalence claim.
