# Skill 08: Agentic Output Contract

## 1. Stdout and Stderr Separation
To facilitate automation and downstream piping by software agents:
- **stdout** is strictly reserved for machine-readable payloads, exported file contents, and structured JSON logs.
- **stderr** is used for interactive human-facing indicators, warnings, logs, diagnostics, and CLI title blocks.

## 2. Structured JSON Output
- When running with `--json` or `--output json`, all command-line outputs, errors, and run steps must be serialized into structured JSON objects on stdout.
- Any output sent to stdout under JSON mode must validate against the target JSON schema.
- `agy-ct run` generates a structured report at `reports/latest.json` mapping indices, stages, status, and generated SPARK context artifacts.
- Generated `reports/latest.json` is a local runtime artifact and must not be committed to git.
- No official SPARK compatibility, production readiness, or EU AI Act compliance claims are made.

## 3. Quiet and Plain Configurations
- Under `--plain` or `--json` or `--non-interactive` flags, no ANSI formatting escape codes, progressive spinners, interactive loading lines, or ticker indicators may be printed to stdout or stderr.
- Terminal outputs must remain static and flat in these modes.

## 4. Exit Codes and Compact Error Model
- The binary must propagate specific exit codes on validation failures:
  - `0`: Complete success.
  - `1`: Unexpected execution error.
  - `2`: Validation integrity or leak check failure.
  - `3`: Missing configuration files or schema files.
  - `4`: Invalid file structure or signature.
- Error outputs must be compact (single-line text) by default. Detailed traces can be requested via `--explain <CODE>` or `--verbose`.
- In non-interactive mode, if input is required, the execution must abort immediately and exit with a non-zero code.

## 5. Security and Leak Limits
- Access keys, environment secrets, and sensitive tokens must never be written to JSON reports, stdout, or stderr logs.
