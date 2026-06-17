# Benchmark and Token Reduction Explanation

## Purpose

This document explains how reviewers should interpret CompText V7 benchmark, token-reduction, and deterministic replay-validation evidence. It is intentionally conservative: token reduction and replay metrics are useful fixture-bound signals, but they are not proof of semantic correctness, enterprise readiness, production value, or solved AI memory.

## What is being reduced

CompText V7 targets structured, repetitive diagnostic-style text. Instead of transporting every repeated raw line, KVTC-V7 groups events into a compact frame with retained anchors such as:

- severity counts and top codes,
- ECU/module and diagnostic-family context,
- code-like identifiers such as DTC/SPN/FMI-style anchors when present in the parsed structure,
- temporal windows and burst counts,
- deterministic family dictionaries and compact payload fields.

The result is lossy by design. Reviewers should treat it as an auditable handoff representation, not as a complete archive.

## Why token reduction matters

Token reduction can help a review or assistant workflow by:

1. fitting more incident context into a bounded LLM context window,
2. reducing repeated boilerplate around identical diagnostic families,
3. lowering downstream processing cost and latency pressure,
4. making high-frequency fault patterns easier to scan,
5. preserving enough structured anchors for audit-oriented review.

These benefits remain conditional. They depend on the input domain, retained anchors, validation gates, and acceptable loss profile.

## How to read benchmark results

When a benchmark or report contains original-token and compressed-token values, read them with this hierarchy:

| Evidence | How to use it | What not to infer |
| --- | --- | --- |
| Original vs compressed tokens | Shows approximate context-size reduction for the tested input. | Does not prove semantic fidelity. |
| Payload bytes | Shows transport-size change. | Does not prove LLM quality or business ROI. |
| Runtime metrics | Helps reason about benchmark cost for tested cases. | Does not prove production latency at fleet scale. |
| Distinct families / coverage | Shows whether repeated structures dominate. | Does not prove rare event preservation. |
| Replay / forensic checks | Shows whether fixture-defined operational fields, evidence references, and failure labels survived deterministic replay. | Does not certify safety-critical behavior or semantic completeness. |
| CI status | Shows cloud workflows completed for a commit. | Does not replace domain validation on real governed data. |

## Conservative interpretation rules

Use these rules in reviewer conversations:

- Prefer exact artifact and workflow references over generalized performance claims.
- Say `synthetic/static` unless the specific artifact is explicitly governed real data.
- Say `lossy token reduction` rather than `lossless compression`.
- Say `cloud CI validated this commit/workflow` only when the inspected Actions run supports that statement.
- Say `illustrative` for demo narratives that are not backed by a committed artifact.
- Do not extrapolate token savings to enterprise cost savings without a defined workload, model pricing, baseline, and governance review.

## Validated, planned, and illustrative

| Category | Meaning in this showcase |
| --- | --- |
| Validated | Evidence exists in repository files, schemas, reports, or GitHub Actions artifacts for the reviewed commit. |
| Planned | Reasonable follow-up work listed as next steps, not yet delivered in the referenced artifact or review scope. |
| Illustrative | Demo language or example framing used to help reviewers understand the architecture, not a measured claim. |

## Relationship to CFI artifacts

CFI-01/02/03 artifacts do not publish benchmark datasets or raw logs. They publish compact Cloud CI result metadata so a display-only consumer can show status, provenance, links, and timestamps without becoming an execution authority.

In showcase terms:

- Benchmark evidence explains token-reduction behavior.
- Validation workflows explain whether checks ran for a commit.
- CFI artifacts explain how cloud validation status is packaged for review or display.

## Non-claims for benchmark discussion

Do not claim:

- benchmark results from real Daimler or customer data,
- production-grade cost reduction,
- safety-critical diagnostic correctness,
- lossless reconstruction,
- universal compression performance across all log types,
- superiority over other systems without controlled comparative evidence,
- local validation results for this showcase pack.
