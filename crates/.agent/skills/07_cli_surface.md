# Skill 07: agy-ct CLI Surface Rules

## 1. CLI Subcommand Taxonomy
`agy-ct` must implement the following subcommand structure exactly:
- `run`
- `demo`
- `doctor`
- `validate`
- `handoff`
- `package`
  - `compress`
  - `inspect`
  - `verify`
  - `replay`
  - `adversarial`
- `context`
  - `build`
  - `render`
  - `validate`
  - `all`
- `schema check`
- `report export`
- `notebook bundle`

## 2. Clap Parser Behavior
- Subcommands must be defined using strict typed options inside Rust's `clap` crate.
- Command-line parsing must enforce correct parameter names, required arguments, and mutually exclusive options at the parser level.
- Clean `-h` and `--help` pages must be auto-generated for each command and subcommand.

## 3. Phase 6B-6E Execution Orchestrator Implementation
- `agy-ct run` is implemented as a local automatic workflow orchestrator. It executes the following stages in order:
  1. workspace doctor (`sparkctl::doctor::run_doctor()`)
  2. context pipeline (`sparkctl::context_all::run_context_all()`)
  3. spark demo (`sparkctl::spark_demo::run_spark_demo()`)
  4. handoff check (`sparkctl::handoff_check::run_handoff_check()`)
- `agy-ct run` creates or overwrites `reports/latest.json` containing stage-level status reports and artifact mappings.
- The `reports/latest.json` is a generated local runtime file and must remain untracked by default.

## 4. Preservation of sparkctl
- Under no circumstances should implementation changes to `agy-ct` alter or break any existing command surface or execution behavior of the compatibility CLI binary `sparkctl`.
- Codebase refactoring must maintain backward compatibility.
