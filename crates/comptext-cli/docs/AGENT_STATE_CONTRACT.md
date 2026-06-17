# Agent State Contract

This document outlines the local agent state contract for context-controlled execution.

---

## 1. Local Agent State Contract Model

The agent state contract captures local workspace metadata and files to serve as bounded evidence artifacts.

- **Schema Definition**: Agent state files are stored as JSON documents (such as `.comptext/agent_state.latest.json`).
- **Paths**: All paths in the evidence list must be relative to the repository root.
- **Evidence IDs**: Every evidence item must have a unique identifier.
- **Status and Failure Labels**: The state contract distinguishes between different status values and details errors using standard labels:
  - `ChecksumMismatch`
  - `PathSafetyViolation`
  - `InvalidSchema`
  - `MissingFile`

### Schema Shape

```json
{
  "schema_version": "0.1",
  "task": "Build feature x",
  "timestamp": "2026-06-05T13:39:50Z",
  "evidence": [
    {
      "id": "src_cli_rs",
      "file_path": "src/cli.rs",
      "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
      "status": "verified",
      "failure_label": null
    }
  ]
}
```

---

## 2. Boundaries and Verification Rules

- **Local Verification**: The verifying command parses the agent state and checks that all evidence IDs are unique, paths are relative, schema version is exactly `0.1`, and hashes match when present.
- **No Unsupported Assurance Claims**: These state files and integrity checks are designed to support local change verification only.
