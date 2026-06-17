# Showcase Readiness Pack

> **Legacy showcase note:** This document is retained for historical context only. The current visual Monaco showcase UI, presentation-layer narrative, charts, reviewer walkthrough, and static fixture-bound profile comparison display are maintained in [`ProfRandom92/comptext-v7-monaco-showcase`](https://github.com/ProfRandom92/comptext-v7-monaco-showcase). This main repository remains the source of truth for deterministic replay-validation artifacts, benchmarks, failure labels, degradation evidence, and research positioning.

## 1. Executive Summary

CompText V7 is a deterministic, auditable prototype for reducing repetitive technical diagnostic logs into compact KVTC-V7 transport frames. It is designed for reviewer inspection before assistant, dashboard, audit, or CI handoff, especially where raw vehicle/workshop-style logs would be too verbose to send directly into an LLM context window.

This showcase pack is documentation-only and cloud-first. It does not ask reviewers to run local commands, does not introduce local validation requirements, and does not include Chilli/Hatch-Pet assets. The pack explains what is already validated in the repository, what is planned, and what is explicitly not claimed.

Use this page as the entry point, then open:

- [`DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md) for the reviewer/demo inspection path.
- [`BENCHMARK_EXPLANATION.md`](BENCHMARK_EXPLANATION.md) for how to read token-reduction and benchmark evidence conservatively.
- [`hash-companion/cloud-ci-result-contract.md`](hash-companion/cloud-ci-result-contract.md), [`hash-companion/validation-runner-workflow.md`](hash-companion/validation-runner-workflow.md), and [`hash-companion/artifact-consumption.md`](hash-companion/artifact-consumption.md) for CFI-01/02/03 details.

## 2. Problem / Use Case

Structured diagnostic logs are repetitive, high-volume, and costly to review directly in an LLM or dashboard workflow. A single incident can repeat ECU/module names, DTC/SPN/FMI codes, timestamps, measurements, and severity markers many times. Sending every raw line downstream increases token cost, context-window pressure, latency, and review noise.

CompText V7 targets synthetic vehicle/workshop-style diagnostics and similar industrial logs. The use case is not permanent archival storage. The use case is an auditable, compact handoff where reviewers still see retained anchors such as severity, module context, code families, temporal windows, counts, and payload metadata.

## 3. Technical Overview

The core review concept is KVTC-V7: a deterministic, layered compression frame for structured diagnostics. The repository describes a four-layer frame:

| Layer | Reviewer question answered | Typical retained evidence |
| --- | --- | --- |
| Header | What run and inventory is this? | event counts, provenance/fingerprint, severity counts, top codes, first/last timestamps |
| Middle family layer | Which diagnostic families dominate? | ECU/module, severity, primary code, compact signatures, field slots |
| Temporal window layer | When did bursts happen? | top time buckets and family counts |
| Compact payload/frame | What should be transported? | deterministic family dictionary and compact JSON-like payload |

The important property for reviewers is determinism: the same synthetic input should map to stable structured output under the same code and validation context. The output is intentionally lossy and therefore must be reviewed with benchmark, replay, and forensic evidence rather than treated as a byte-for-byte log substitute.

## 4. Token Reduction Explanation

Token reduction matters because modern AI and review systems often price, limit, or prioritize work by context size. For diagnostic logs, reducing repeated structure can make a larger incident inspectable in one handoff, reduce duplicated prompt content, and keep attention on severity/code/module patterns instead of repeated raw lines.

CompText V7 reduces token volume by grouping repeated diagnostic families and transporting counts, signatures, slots, and temporal windows instead of replaying every redundant line. This is useful only if the reduction remains auditable. Reviewers should therefore inspect both the compact result and the validation evidence that guards against dangerous semantic loss.

Do not interpret a large reduction percentage as proof of correctness. A showcase-ready review should ask:

1. Which anchors were retained?
2. Which rare or high-severity events could be lost?
3. Are benchmark inputs synthetic/static or real?
4. Did cloud CI run the validation surfaces for the reviewed commit?
5. Are any claims explicitly labeled illustrative or planned?

## 5. Validation and CI Model

The showcase posture is cloud-first. GitHub Actions is the execution authority for validation evidence; local execution is not required for this pack.

Repository validation surfaces include:

- Industrial validation workflow for pytest, deterministic replay, token telemetry, semantic forensic validation, benchmark replay, and dashboard startup validation.
- Agent workflow checks for repository reports, contract schemas, API/export fixtures, project health, dashboard health, dashboard typecheck/build, and release-health smoke coverage.
- The `hash-companion-validation` workflow for the CFI-01/02/03 cloud CI result contract and artifact flow.

For this showcase, reviewers should inspect GitHub Actions outcomes, committed documentation, contract schemas, report artifacts, and uploaded CI artifacts rather than running local checks.

## 6. CFI-01/02/03 Artifact Flow

CFI-01, CFI-02, and CFI-03 prove a compact cloud-backed result handoff, not a local execution system.

| Item | What it proves | Evidence to inspect |
| --- | --- | --- |
| CFI-01 | A strict Cloud CI result contract exists for status metadata. | `contracts/hash-chilli-cloud-ci-result.schema.json` and `docs/hash-companion/cloud-ci-result-contract.md` |
| CFI-02 | A GitHub Actions `validation_runner` workflow can produce authoritative cloud validation status. | `.github/workflows/validation_runner.yml` and `docs/hash-companion/validation-runner-workflow.md` |
| CFI-03 | The workflow publishes compact and review-friendly CI result artifacts. | `validation-runner-cfi-artifacts`, `reports/hash-chilli-cloud-ci-summary.json`, and `reports/hash-chilli-cloud-ci-result.json` |

Artifact flow:

```text
Pull request / push / workflow_dispatch
        ↓
GitHub Actions: hash-companion-validation
        ↓
Cloud validation steps and CFI publisher
        ↓
Schema-checked CFI-01 payload
        ↓
Uploaded validation-runner-cfi-artifacts bundle
        ↓
Display-only consumer can render status, links, timestamps, and summary
```

The artifact payload is metadata only. It is not a raw log export, not a secret-bearing bundle, not a production data dump, and not proof of OEM certification.

## 7. Reviewer Walkthrough

A reviewer-ready inspection can be completed without local execution:

1. Start with this readiness pack and confirm the scope is documentation-only and cloud-first.
2. Read the README executive snapshot for the repository-wide positioning.
3. Review [`DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md) to understand the proposed showcase narrative.
4. Review [`BENCHMARK_EXPLANATION.md`](BENCHMARK_EXPLANATION.md) before interpreting any token-reduction numbers.
5. Open the GitHub Actions tab for the reviewed commit/PR and inspect the three relevant workflows: industrial validation, agent workflow checks, and `hash-companion-validation`.
6. In the `hash-companion-validation` run, inspect the job summary and the `validation-runner-cfi-artifacts` artifact when present.
7. Confirm the CFI payload fields match the contract and point back to the same commit, branch, run URL, and artifact area.
8. Check limits and non-claims before escalating the showcase to enterprise stakeholders.

## 8. Demo Flow

Recommended demo narrative:

1. **Problem framing:** raw diagnostic logs are repetitive and expensive to review directly.
2. **CompText framing:** KVTC-V7 converts structured synthetic diagnostics into an auditable compact frame.
3. **Token reduction:** explain grouping, family dictionaries, temporal windows, and why reduction must be validated.
4. **Validation model:** show that cloud CI, not a local laptop, is the validation authority for this showcase.
5. **CFI artifact flow:** show the schema, workflow, compact summary artifact, and pretty review artifact.
6. **Reviewer inspection:** demonstrate how a reviewer checks commit binding, status, timestamps, run URL, artifact URL, and local-execution policy.
7. **Enterprise readiness:** explain deterministic outputs, synthetic-data posture, contract boundaries, CI evidence, and explicit non-claims.
8. **Next steps:** propose pilot-quality data governance, benchmark baselines, dashboard polish, and stakeholder-specific acceptance criteria.

## 9. Enterprise / Daimler Readiness

The repository is positioned for a Daimler-Truck-style industrial review posture, not as a certified Daimler product. Enterprise readiness signals include:

- Deterministic transformation rather than opaque free-form summarization.
- Layered audit surfaces that separate run inventory, diagnostic families, time windows, and payload representation.
- Cloud CI as the authoritative validation channel for the showcase pack.
- Strict CFI payload boundaries with `additionalProperties: false` in the contract schema.
- Synthetic/static data posture and explicit exclusion of secrets, production logs, customer data, and proprietary payloads.
- Display-only artifact consumption that avoids local mutation or implicit local validation.
- Clear distinction between validated repository behavior, planned future work, and illustrative demo language.

These properties support enterprise review conversations around governance, repeatability, data minimization, auditability, and CI evidence. They do not replace production safety review, legal review, OEM validation, cybersecurity assessment, or pilot-data evaluation.

## 10. Limits / Non-Claims

This showcase pack does not claim:

- Daimler certification, endorsement, deployment, or production approval.
- Correctness on real fleet, workshop, customer, or proprietary data.
- Lossless compression or byte-for-byte reconstruction.
- Safety-critical diagnostic authority.
- Security certification or privacy compliance certification.
- Local execution readiness for the showcase path.
- Chilli/Hatch-Pet implementation, assets, or demo content.
- Benchmark superiority beyond the synthetic/static evidence explicitly present in the repository and CI artifacts.

## 11. Next Steps

Recommended follow-up work after SHOWCASE-01:

1. Add a small GitHub-hosted showcase issue template that links this pack and asks reviewers to record the exact Actions run inspected.
2. Define pilot-data governance requirements before any real diagnostic logs are introduced.
3. Add dashboard copy that mirrors the validated/planned/non-claim distinctions from this pack.
4. Establish benchmark baselines and regression thresholds only from approved synthetic or governed pilot datasets.
5. Prepare stakeholder-specific demo scripts for engineering, QA/compliance, product, and enterprise architecture audiences.
