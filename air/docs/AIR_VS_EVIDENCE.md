# AIR vs Evidence in CompText

This document explains the architectural separation between AIR (Agent Intermediate Representation) and Evidence events.

## AIR: Intent and Plan

**File:** `schemas/air.schema.json`
**Purpose:** Describes *what* the agent intends to do.

AIR is the "blueprint" or "manifest" for an agent operation. It is typically generated before execution or as a proposal.

- **Intent:** The high-level action (audit, summarize, etc.).
- **Goal:** Natural language description of the objective.
- **Inputs:** What data or artifacts the agent will use.
- **Pipeline:** The steps the agent will take.
- **Contracts:** Declarative constraints on the execution and output.
- **Outputs:** Expected artifacts or reports.

AIR artifacts are **static** descriptions of intent.

## Evidence: Runtime and Replay

**File:** `schemas/evidence.schema.json`
**Purpose:** Describes *how* the agent actually executed the plan.

Evidence is the verifiable record of runtime behavior. It provides the "proof" of what happened.

- **Events:** Discrete points in time during execution (start, step, end).
- **Typed Hashes:** All hashes are objects containing `algorithm` (default: `sha256`), `canonicalization` (default: `rfc8785`), and the hex `value`.
- **Hash Chain:** Each evidence event (except the first) references the `event_hash` of the previous event via `parent_event_hash`, creating an immutable audit trail.
- **Canonicalization:** Events are hashed using RFC 8785 (JSON Canonicalization Scheme) to ensure deterministic results across different platforms.
- **Executor:** Identification of who performed the action (agent, human, or system).
- **Verification:** Links back to the AIR plan via `air_hash`.

Evidence allows for **verifiable replay** and safety audits without needing to trust the agent's internal chain-of-thought.

## Relationship

1. An **AIR artifact** is created to define a plan.
2. The agent executes the plan, generating **Evidence events**.
3. Each Evidence event includes the `air_hash` of the plan it is executing.
4. The sequence of Evidence events forms a **Hash Chain**.
5. Auditors can verify the Evidence against the AIR plan and the produced artifacts.
