# Policy Interceptor Specification

This document provides the inert specification format for policy interceptor hooks. These hooks represent target integration endpoints for orchestrator runtimes and are not actively executed by the local Rust CLI.

---

## 1. Interceptor Lifecycle Targets (Planned / Not Active)

```text
[ SessionStart ] ──────► Target-only: planned to initialize the validation profile (not active)
       │
       ▼
[ PreToolUse ] ────────► Target-only: planned to validate tool input parameters (not active)
       │
       ▼
  ( Tool Run )
       │
       ▼
[ PostToolUse ] ───────► Target-only: planned to filter output streams (not active)
       │
       ▼
[ PostPhase ] ─────────► Target-only: planned to check phase completeness (not active)
```

---

## 2. Specification Formats (Inert Targets)

### SessionStart Specification
- **Intent**: Target-only: planned to initialize the session state tracking profile (not active).
- **Inert Spec**:
  ```json
  {
    "hook": "SessionStart",
    "status": "target",
    "actions": [
      "verify_local_git_cleanliness",
      "load_active_phase_restrictions"
    ]
  }
  ```

### PreToolUse Specification
- **Intent**: Target-only: planned to validate tool invocation arguments before execution (not active).
- **Inert Spec**:
  ```json
  {
    "hook": "PreToolUse",
    "status": "target",
    "restricted_arguments": {
      "command_prefixes": ["env", "printenv"],
      "blocked_paths": [".env", "*.key", "*.pem"]
    }
  }
  ```

### PostToolUse Specification
- **Intent**: Target-only: planned to filter and sanitize outputs before returning them to the model context (not active).
- **Inert Spec**:
  ```json
  {
    "hook": "PostToolUse",
    "status": "target",
    "redaction_patterns": [
      "high_entropy_strings",
      "credential_variables"
    ]
  }
  ```

### PostPhase Specification
- **Intent**: Planned target verification of phase completeness status (not active in current CLI).
- **Inert Spec**:
  ```json
  {
    "hook": "PostPhase",
    "status": "target",
    "verification_suite": [
      "cargo fmt --all --check",
      "cargo check",
      "cargo test",
      "cargo clippy -- -D warnings"
    ]
  }
  ```
