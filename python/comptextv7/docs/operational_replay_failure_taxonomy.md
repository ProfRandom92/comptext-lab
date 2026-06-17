# Operational Replay Failure Taxonomy

## Purpose

This document defines a small, deterministic taxonomy for describing how operational replay can fail in Comptextv7 fixtures. The taxonomy is design guidance only: it does not implement new validators, change benchmark logic, or make claims about production readiness, general AI memory, or superiority over other systems.

The failure modes are fixture-bound. A mode is detectable only when the source fixture and reconstructed replay artifact expose the relevant fields for deterministic comparison.

The current deterministic replay failure classifier emits the implemented subset `EVIDENCE_LOSS`, `HIGH_CRITICAL_EVIDENCE_LOSS`, `CONSTRAINT_DRIFT`, and `BLOCKER_DETACHMENT`. The remaining labels stay documented as taxonomy guidance for future fixture fields; they are not inferred by the current classifier.

## Scope and constraints

- Deterministic, fixture-bound replay validation only.
- No LLM judges, embeddings, vector databases, external APIs, or graph stores.
- No subjective quality assessment.
- No claim that preserving these fields is sufficient for real-world task success.
- No claim that the taxonomy is complete for every agent system or workflow domain.

## Failure modes

### EVIDENCE_LOSS

- **Stable ID:** `EVIDENCE_LOSS`
- **Definition:** Evidence entries present in the source fixture are absent from the replayed artifact or no longer attach to the expected task, claim, or operational state element.
- **Deterministic detection signal:** Compare source and replay evidence identifiers, counts, or fixture-defined evidence references; flag when `evidence_survived < evidence_total` or when an expected evidence reference is missing.
- **Severity guidance:** Low to high depending on fixture criticality, quantity lost, and whether remaining evidence still supports the replayed operational state.
- **Non-claims / limitations:** Does not judge whether missing evidence is semantically important outside the fixture schema. Does not assess evidence quality or truth.

### HIGH_CRITICAL_EVIDENCE_LOSS

- **Stable ID:** `HIGH_CRITICAL_EVIDENCE_LOSS`
- **Definition:** At least one evidence item marked `HIGH` criticality in the source fixture is missing or detached after replay.
- **Deterministic detection signal:** Filter fixture evidence by criticality `HIGH`, then compare source and replay survival by stable evidence reference; flag when high-critical survived count is below high-critical total.
- **Severity guidance:** High by default because current adaptive policy design treats loss of high-critical evidence as a reason to fall back to conservative behavior.
- **Non-claims / limitations:** High severity is a validation-policy signal, not proof of real-world harm. The mode depends on fixture-authored criticality labels.

### CONSTRAINT_DRIFT

- **Stable ID:** `CONSTRAINT_DRIFT`
- **Definition:** A constraint required by the source fixture is missing, rewritten into a different operational requirement, or attached to the wrong task after replay.
- **Deterministic detection signal:** Compare fixture-defined constraint IDs, normalized constraint text, or constraint-task associations between source and replay; flag missing, added, or mismatched required constraints.
- **Severity guidance:** Medium to high when the constraint controls safety boundaries, allowed actions, validation requirements, or deployment limits; low when the fixture marks it as informational.
- **Non-claims / limitations:** Does not infer unstated constraints. Only constraints represented in the fixture can be checked.

### BLOCKER_DETACHMENT

- **Stable ID:** `BLOCKER_DETACHMENT`
- **Definition:** A blocker survives as text or structure but is no longer linked to the task, dependency, or recovery action it blocks.
- **Deterministic detection signal:** Compare blocker IDs and their fixture-defined task, dependency, or recovery-path references; flag when the blocker exists but the expected attachment edge is absent or changed.
- **Severity guidance:** Medium to high when detachment would make the replayed task appear actionable despite an unresolved blocker; low when the blocker is informational and not gating.
- **Non-claims / limitations:** Does not determine whether a human could recover the relationship from prose. It only checks explicit fixture relationships.

### DEPENDENCY_COLLAPSE

- **Stable ID:** `DEPENDENCY_COLLAPSE`
- **Definition:** Multiple distinct dependencies from the source fixture collapse into one replayed dependency, disappear, or lose ordering/parentage needed to continue the workflow.
- **Deterministic detection signal:** Compare dependency IDs, dependency counts, parent-child links, and required ordering edges; flag missing dependencies, merged IDs, or lost dependency graph edges.
- **Severity guidance:** Medium when redundant context remains; high when the collapsed dependency gates execution order, validation, or recovery.
- **Non-claims / limitations:** Does not require or introduce a graph store. The check is limited to explicit dependency fields already present in fixtures or artifacts.

### TOOL_ORDER_MUTATION

- **Stable ID:** `TOOL_ORDER_MUTATION`
- **Definition:** The replayed tool sequence contains the expected tools but in an order different from the source fixture where order is operationally significant.
- **Deterministic detection signal:** Compare ordered tool-call identifiers or fixture-defined tool sequence arrays; flag when the replay order differs from the source order for order-sensitive traces.
- **Severity guidance:** Medium to high when execution order affects state, artifacts, validation, or rollback; low when fixture metadata marks the order as non-gating.
- **Non-claims / limitations:** Does not judge whether a different order might still work in an external environment. It only reports mutation relative to the fixture.

### TASK_IDENTITY_SPLIT

- **Stable ID:** `TASK_IDENTITY_SPLIT`
- **Definition:** A single source task is replayed as multiple tasks, or its identity is split across fields such that blockers, constraints, dependencies, or evidence no longer point to one stable task.
- **Deterministic detection signal:** Compare stable task IDs and inbound references from evidence, blockers, constraints, dependencies, and recovery actions; flag one-to-many task mappings or references to replay-only task fragments.
- **Severity guidance:** Medium when the split is cosmetic; high when it separates required operational fields from the task they govern.
- **Non-claims / limitations:** Does not decide whether task decomposition is useful. It treats identity splits as failures only when they violate fixture-defined task identity.

### STATE_ALIASING

- **Stable ID:** `STATE_ALIASING`
- **Definition:** Two or more distinct source state elements are replayed with the same identifier, label, or attachment target, making them indistinguishable for deterministic validation.
- **Deterministic detection signal:** Check uniqueness constraints for fixture-defined IDs, labels, or attachment keys; flag duplicate replay identifiers where the source contains distinct elements.
- **Severity guidance:** Medium when duplicated elements are read-only context; high when aliasing affects blockers, constraints, evidence, dependencies, or recovery decisions.
- **Non-claims / limitations:** Does not detect aliasing that is only semantic or hidden in natural language. It requires explicit fixture keys or normalized fields.

### RECOVERY_PATH_LOSS

- **Stable ID:** `RECOVERY_PATH_LOSS`
- **Definition:** A recovery action, fallback path, rollback instruction, or next-step remediation present in the source fixture is absent or disconnected after replay.
- **Deterministic detection signal:** Compare recovery action IDs, fallback references, rollback markers, and their links to blocked or failed tasks; flag missing recovery paths or changed attachments.
- **Severity guidance:** Medium to high when the lost path is the fixture-defined way to continue after a blocker or validation failure; low when recovery guidance is optional.
- **Non-claims / limitations:** Does not validate that the recovery path would succeed in a real system. It only checks that the fixture-defined path survived replay.

## Relationship to existing metrics

The taxonomy is intended to name field-level failure modes that can explain changes in existing deterministic metrics. It does not replace those metrics.

- `evidence_survival_rate`: Primary aggregate signal for `EVIDENCE_LOSS`.
- `high_critical_evidence_survival_rate`: Primary aggregate signal for `HIGH_CRITICAL_EVIDENCE_LOSS`.
- `replay_consistency`: Broad replay preservation signal that may decrease when any taxonomy mode is present.
- `constraint_survival_rate`: Aggregate signal for `CONSTRAINT_DRIFT`, especially missing or mismatched required constraints.
- `blocker_survival_rate`: Aggregate signal for `BLOCKER_DETACHMENT` when blocker identity or blocker-task links fail to survive.
- `operational_drift_rate`: Broad field-loss signal that can increase when constraints, blockers, dependencies, task identity, tool order, state aliases, or recovery paths drift.

These relationships are interpretive design guidance. Current and future metric calculations should remain deterministic and avoid subjective scoring.

## Classifier scope

The current deterministic classifier covers the implemented subset listed in the purpose section and can summarize those labels in replay artifacts. The remaining taxonomy entries are conservative labels for fixture fields that may be added or expanded later. Any expansion should:

1. keep all checks fixture-bound and schema-driven;
2. compare only explicit IDs, counts, normalized fields, and declared attachment edges;
3. emit stable failure IDs without natural-language judging;
4. preserve existing metrics and use taxonomy labels as explanatory metadata;
5. include regression coverage for each newly implemented failure mode using small checked-in fixtures.
