# Runtime Adapters in CompText AIR

Runtime Adapters provide a descriptive layer that bridges the platform-agnostic AIR plans with specific execution environments (runtimes).

## Purpose

AIR plans are designed to be portable. They describe *what* should happen but not *how* it is executed at the process level. A Runtime Adapter fills this gap by describing:

1.  **Command Surface:** The binaries and commands available in the runtime.
2.  **Mapping:** How AIR inputs (like `path` or `artifact`) translate to runtime flags or arguments.
3.  **Evidence Generation:** How runtime signals (like `exit_0` or `stdout`) should be interpreted as Evidence event types.
4.  **Constraints:** What the runtime explicitly cannot do (disabled capabilities) and what its boundaries are.

## Key Principles

- **Descriptive Only:** An adapter is a configuration or manifest. It does not contain executable code.
- **Decoupled:** AIR does not depend on Adapters. Runtimes use Adapters to understand how to execute AIR.
- **Safety First:** Adapters must explicitly list disabled capabilities and boundaries to guide safe agent execution.
- **Local-First:** Current adapters prioritize local CLI and VFS (Virtual File System) surfaces.

## Schema

The adapter schema is defined in `schemas/adapter.schema.json`.

### Core Fields

- `adapter_id`: Unique identifier (e.g., `ctxt-local-v1`).
- `adapter_kind`: The type of runtime (e.g., `local-cli`).
- `supported_air_version`: Ensures compatibility with the AIR plan version.
- `command_surface`: The technical interface of the runtime.
- `input_mapping`: Translation of AIR inputs to runtime arguments.
- `output_mapping`: Translation of runtime results back to AIR outputs.
- `evidence_mapping`: Translation of runtime events to AIR Evidence types.

## Example: Local CLI Adapter

The `fixtures/adapter/ctxt-local.adapter.json` fixture describes how a local `comptext` CLI tool satisfies the AIR contract. It maps AIR's `audit` intent to the `comptext audit --json` command and defines the safety boundaries of the local environment.

## Negative Adapter Fixtures

To ensure the safety and integrity of the AIR layer, adapters that over-claim capabilities or miss required safety declarations are explicitly blocked during validation.

Required safety fields:
- `disabled_capabilities`: Must be present to explicitly list restricted actions.
- `evidence_mapping`: Must be present to define how runtime events translate to evidence.

Forbidden claims (blocked by validation):
- `provider_runtime`: No direct model provider execution allowed.
- `mcp_server`: No production MCP server claims.
- `external_agent_execution`: No delegation to external untrusted agents.
- `auto_apply`: No automatic application of suggested changes.
- `network_required`: No mandatory network access for execution.
- `production_runtime`: No claims of being a production-ready execution environment.
- `legal_assurance`, `compliance_assurance`, `forensic_assurance`: No legal or compliance guarantees.

Invalid fixtures are maintained in `fixtures/adapter/invalid/` to prove that these constraints are enforced.
