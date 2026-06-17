# Deterministic Operational Failure Taxonomy

This taxonomy defines stable replay/admissibility failure labels with explicit operational semantics. Every label maps to an observable deterministic condition, a failed contract/invariant type, or explicit artifact/metric drift.

Non-goals:
- no semantic-only labels
- no fuzzy matching labels
- no model-judged labels

Canonical source for registered labels and field definitions: `src/validation/failure_taxonomy.py`.

## Required fields per label

Each registered label includes:
- label name
- operational meaning
- observable trigger
- linked contract or invariant type
- severity class
- explicit non-goal (what it must not mean)

## Preferred labels hardened in this taxonomy

- `TOOL_ORDER_VIOLATION`
- `RECOVERY_PATH_LOSS`
- `BLOCKER_DETACHMENT`
- `GOVERNANCE_DRIFT`
- `DEPENDENCY_CHAIN_BREAK`
- `EVIDENCE_SURVIVAL_LOSS`
- `HIGH_CRITICAL_EVIDENCE_LOSS`

These preferred labels are operationally defined in the canonical registry, regardless of whether a given fixture family currently emits each one.

## Capability/security taxonomy expansion (registration-only)

The following labels are registered for future deterministic fixture/artifact hardening, with operational semantics anchored to explicit contracts and replay evidence:

- `CAPABILITY_BOUNDARY_LOSS`
  - deterministic focus: explicit boundary preservation loss in reconstructed replay state
  - expected evidence shape: missing boundary nodes/edges in capability-boundary contracts, fixtures, or artifacts
- `UNAUTHORIZED_CAPABILITY_PATH`
  - deterministic focus: explicit new capability/resource/tool path introduced in reconstruction
  - expected evidence shape: added boundary edges or nodes that create a new path not present in allowed baseline
- `APPROVAL_GATE_LOSS`
  - deterministic focus: required approval/validation/human-gate commitment missing before guarded action path
  - expected evidence shape: ordering/capability-boundary fixtures or artifacts showing absent gate precondition
- `POLICY_ENFORCEMENT_GAP`
  - deterministic focus: policy enforcement condition dropped while related action/dependency path remains present
  - expected evidence shape: policy/guard contract evidence showing missing enforcement constraint with surviving action path

Registration in this taxonomy does not itself change fixture expectations or generated artifacts. Any future fixture use of these labels must be backed by deterministic contracts or artifact evidence.
