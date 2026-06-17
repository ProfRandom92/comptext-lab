# Reference Index and Event Fingerprints

This document explains the foundational structures for deterministic replay artifact generation: the `ReferenceIndex` and `EventLogArtifactAdapter`.

## Reference Index

The `ReferenceIndex` tracks semantic references compactly. It acts as an observable registry for context injected into and returned from an agent execution.

### Allowed URI Schemes
To ensure safety and observability, only specific URI schemes are permitted:
- `ctx://`
- `mem://`
- `replay://`
- `artifact://`
- `tool://`
- `file://`
- `run://`

Any other schemes are rejected and cause validation to fail.

### File URI Hardening and Raw Hydration
A core constraint of the `ReferenceIndex` is that raw file contents are **not hydrated** into the index itself, and local filesystem access is forbidden.
The system enforces strict validation for `file://` URIs:
- **Workspace relative only**: `file://src/main.ts` is valid.
- **Absolute paths forbidden**: `file:///Users/jules/code` or `file://C:/code` are rejected.
- **Localhost and network shares forbidden**: `file://localhost/` or `file://\\server\share` are rejected.
- **Path traversal forbidden**: Paths containing `..`, `\`, `%2e%2e`, `%5c`, etc. are rejected.

We forbid raw file hydration to keep the index compact and to avoid leaking host directory structures, usernames, or secrets into deterministic artifacts.

## Event Log Artifact Adapter

The `EventLogArtifactAdapter` provides deterministic representations of execution events, primarily through `eventFingerprint`.

### Volatile Payload Masking
Event payloads can contain volatile runtime IDs (e.g. `traceId`) or timestamps (e.g. `durationMs`). Including these in fingerprints would destroy determinism.
We use an **exact key denylist** to mask these values, replacing them with deterministic placeholders like `[RUNTIME_ID_STRIPPED]` or `[TIMESTAMP_STRIPPED]`.

**Runtime Identity Denylist**:
`traceId`, `requestId`, `runRequestId`, `processId`, `pid`, `sessionId`, `spanId`, `serverUptime`, `uptime`.

**Runtime Timing Denylist**:
`timestamp`, `timestamps`, `createdAt`, `updatedAt`, `startedAt`, `finishedAt`, `durationMs`, `latencyMs`, `elapsedMs`.

**Semantic IDs that MUST NOT be masked**:
`id`, `userId`, `documentId`, `recordId`, `artifactId`, `referenceId`, `executionId`, `stepId`, `snapshotId`, `branchId`, `fileId`, `toolId`.
These IDs are semantic markers representing stable entities, even if they visually resemble UUIDs. They remain untouched.

### Event Fingerprint Shape
The event fingerprint captures the essential identity of an execution event:
- `executionId`
- `stepId`
- `eventType`
- `timestamp`
- `inputRefIds` (deterministically sorted)
- `outputRefIds` (deterministically sorted)
- `tokenIn`
- `tokenOut`
- `status`
- `compactPayloadHash`
- `normalizationVersion`

### Normalization Version 1
The masking rules rely on `normalizationVersion: 1`. If masking rules must change in the future, the version will be incremented, fundamentally altering the fingerprint to prevent hidden regressions.

### Dependency on Deterministic Hashing
`compactPayloadHash` relies on `stableHash` and `stableStringify` (introduced in PR #89). This guarantees that equivalent payloads hash to the exact same value across any runtime environment.

## Compression Signal Step Mapping

Execution steps map to cognitive mode windows (compression signals) deterministically:
1. **Explicit Mapping**: Signals can explicitly list `associatedStepIds`.
2. **Timestamp Window Mapping**: Signals can define a start and end timestamp to capture events occurring within the window.
3. **Fallback Mapping**: If only a single timestamp exists, the window captures all events since the previous signal up to that timestamp.

### Orphaned / Unclosed Execution Handling
Execution trailing events (e.g., an `execution.failed` step with no trailing signal window) do not silently disappear. They are appended to the final window's `unmappedStepIds` with the explicit unmapped reason `[UNMAPPED_EXECUTION_HALT]`. We do not invent compression scores for windows never evaluated, nor do we silently drop orphaned events.

## Next Step
These foundations are required for the next milestone: **ReplayArtifactWriter v1-alpha.1**.
