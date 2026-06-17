# Runtime Permission Template Specification

This document defines the inert schema templates for configuring runtime permissions. These configurations represent host-enforced permissions profiles and do not represent active Rust-level compiler restrictions.

---

## 1. Baseline Permissions Template (Inert Target)

```toml
# baseline_permissions.toml - Inert target schema for host execution
[runtime_permissions]
status = "target"
enforcement_layer = "host_orchestrator"

[read]
allowed_paths = ["."]
denied_paths = [
  "/etc",
  "C:\\Windows",
  "~/.ssh",
  "~/.aws"
]

[write]
allowed_paths = [
  "./src",
  "./tests",
  "./docs",
  "./reports",
  "./proposals"
]
denied_paths = [
  "./.git",
  "../"
]

[network]
allow_sockets = false
denied_domains = ["*"]

[provider]
allow_live_calls = false
allowed_providers = ["dummy"]
```
