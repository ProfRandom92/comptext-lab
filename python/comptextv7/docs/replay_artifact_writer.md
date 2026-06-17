# Replay Artifact Writer (v1-alpha.1)

## Purpose
The Replay Artifact Writer generates deterministic, standalone JSON artifacts that represent a fully verifiable snapshot of an agent execution in CompTextv7. These artifacts are designed for post-hoc analysis, continuous integration validation, and exact state reconstruction, fulfilling the requirements for auditability without reliance on external systems or runtime environments.

## Schema Version
The current schema version is strictly `v1-alpha.1`. All artifacts MUST include this version.

## Artifact Shape
A `ReplayArtifact` contains the following deterministic structures:
- `schemaVersion`: Must be `"v1-alpha.1"`.
- `artifactId`: Unique identifier for the artifact.
- `executionId`: Identifier of the execution trace.
- `createdAt`: ISO8601 deterministic timestamp.
- `referenceIndex`: The semantic context used during the execution.
- `eventFingerprints`: Compact signatures of execution steps (via `eventFingerprint`).
- `replayTimelineSummary`: A summarized sequence of execution state changes.
- `replaySnapshots`: A timeline of complete `ReplaySnapshot` structures.
- `compressionSignalMappings`: Step-level mappings of triggered cognitive modes.
- `compressionSummary`: Deterministic statistical summary of signal analysis. totalTokenOut remains null in v1-alpha.1 because CompressionSignalInput currently has no output token estimate field. Do not invent tokenOut values.
- `integrity`: Contains the computed deterministic hash and metadata to verify the artifact.

## Integrity Model
We use a synchronous, non-cryptographic (FNV-1a 32-bit) stable hash (`fnv1a:<hash>`).
- **Exclusion Rule:** When calculating the `artifactHash`, the `integrity.artifactHash` property itself is set to `undefined` so that the object can be stringified and hashed deterministically.
- **Normalization Version:** The artifact mandates `normalizationVersion: 1`, which drops volatile runtime payloads (like `Date.now`, `traceId`, `latencyMs`) from step-level fingerprints to guarantee identical hashes for identical semantic execution runs.

## Event Fingerprint Usage
Event fingerprints strip away volatile JSON paths (via `normalizeVolatilePayload`) and ensure that identical logic creates identical event trails across runs. `ReplayArtifact` ensures no raw `compactPayload` sneaks into the fingerprint sequence.

## Compression Signal Mapping & Orphan Handling
When compression signals are collected, they map directly to step IDs using `mapCompressionSignalsToStepIds`. Steps that don't logically fall into a signal window are recorded as unmapped steps (`unmappedStepIds`) with sorted `unmappedReasons`.

## Constraints
- **No Raw File Hydration:** Artifacts must NOT contain raw file strings. Files are managed by the environment, not the telemetry trace.
- **No LLM Judging:** Validation and hash stability must rely on structure and explicit tokens, not external AI evaluations.
- **Fixture-bound:** Interpreted deterministically across isolated test fixtures.

## Next Steps
Incorporate artifacts into automated CI checks to flag regressions in memory injection and token budgeting.
