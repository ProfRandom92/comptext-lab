# Replay Contracts

A Replay Contract in CompText AIR is the formal fulfillment check between an AIR plan (the "expected") and an Evidence event chain (the "observed").

## Core Principles

- **AIR is the plan:** It defines intent, goal, pipeline steps, contracts, and required outputs.
- **Evidence is the run:** It is a hash-linked chain of events that actually occurred.
- **Fulfillment:** A replay contract is fulfilled only if the Evidence chain proves that all AIR requirements were met.

## Verification Steps

The `scripts/validate_replay_contracts.py` tool performs the following checks:

1. **AIR Integrity:** Computes the canonical SHA-256 hash of the AIR plan.
2. **Attribution:** Verifies that every event in the Evidence chain references this exact AIR hash.
3. **Hash Chain Continuity:** Validates the parent-child hash links across the entire Evidence chain.
4. **Pipeline Fulfillment:** Ensures every pipeline step defined in the AIR plan is represented by at least one evidence action or metadata declaration.
5. **Contract Fulfillment:** Ensures every AIR contract is represented by evidence metadata, actions, or specific output keys.
6. **Output Fulfillment:** Ensures every required AIR output is present in the evidence event outputs or referenced in the final report metadata.

## Safety Primitive

If chain-of-thought becomes unreadable or untrusted, the Replay Contract becomes the safety primitive. It ensures that regardless of *how* the agent thought about the problem, the *work performed* matches the *authorized plan*.

This mechanism does not rely on hidden chain-of-thought capture. It relies on explicit, verifiable evidence.
