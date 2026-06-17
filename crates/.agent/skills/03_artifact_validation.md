# Agent Skill 03 — Artifact Validation

This skill defines the requirements for generating deterministic packages and validation snapshots.

## 1. Package Artifact Integrity

- **Stable Key Ordering:** Objects must have keys sorted alphabetically (canonical JSON) before hashing or writing.
- **No Volatile Elements:** Timestamps, randomized transaction identifiers, and environment-dependent properties are strictly forbidden.
- **Offline Hashing:** Hash chain calculations must happen locally using standard `sha2` crate. No network APIs or external tokenizers can be queried.

## 2. Snapshot Document Standards

At the completion of each phase, a snapshot file (e.g., `PHASE1_SPARK_SNAPSHOT.md`) must be written containing the following structured sections:

1. **Phase Name & Sandbox Root**
2. **Created/Modified File Trees** (excluding intermediate build artifacts like `target/`)
3. **Execution Logs & Command Lists**
4. **Validation Test Run Status**
5. **Deterministic Hash Signatures** (from package validation tests)
6. **Leak Verification Evidence** (for inspect/replay commands)
7. **Adversarial Tamper Suite Statistics**
8. **Explicit Non-Claims & Risks**
