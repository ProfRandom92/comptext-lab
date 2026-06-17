# CompText AIR v0.1

This document describes the structure and fields of CompText AIR (Agent Intermediate Representation) version 0.1, as defined by `air.schema.json`.

## Schema: `air.schema.json`

The `air.schema.json` defines the core structure of an AIR artifact. Each artifact represents a distinct, immutable record of an agent's intent, plan, and requirements.

### Fields:

*   **`version`** (string):
    *   **Value:** Must be `"air-v0.1"`.
    *   **Description:** Specifies the version of the AIR schema.
*   **`intent`** (object):
    *   **Required Fields:** `type`.
    *   **`type`** (enum): `audit`, `summarize`, `validate`, `transform`, `search`, `plan`, `unknown`.
    *   **`risk_category`** (string, optional): Categorization of the operation's risk (e.g., "integrity", "privacy").
*   **`goal`** (string):
    *   **Description:** A clear, natural language description of the objective to be achieved.
*   **`inputs`** (array, optional):
    *   **Items:** Objects with `kind` (enum: `path`, `text`, `url`, `artifact`, `repo`, `query`) and `value`.
    *   **Description:** The source data or artifacts required for the task.
*   **`pipeline`** (array):
    *   **Items:** Strings matching `^[a-z][a-z0-9_-]*$`.
    *   **Description:** A sequence of logical steps the agent will execute.
*   **`contracts`** (array, optional):
    *   **Items:** Strings (contract identifiers).
    *   **Description:** Constraints or invariants that must be upheld during execution.
*   **`outputs`** (array):
    *   **Items:** Objects with `kind` (enum: `report`, `json`, `markdown`, `artifact`, `summary`) and optional `path` and `schema`.
    *   **Description:** The expected artifacts produced by the operation.
*   **`metadata`** (object, optional):
    *   **Description:** Additional structured information about the AIR artifact.

## Examples

### Minimal AIR Plan

```json
{
  "version": "air-v0.1",
  "intent": {
    "type": "summarize"
  },
  "goal": "Summarize the project status.",
  "pipeline": [
    "read_logs",
    "generate_summary"
  ],
  "outputs": [
    {
      "kind": "markdown",
      "path": "SUMMARY.md"
    }
  ]
}
```

## Validation

Validation is performed via `scripts/validate_air_fixtures.py`.
Full JSON schema is available at `schemas/air.schema.json`.
