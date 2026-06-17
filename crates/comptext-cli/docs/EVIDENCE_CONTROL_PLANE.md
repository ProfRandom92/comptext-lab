# Evidence Control Plane

This document specifies the relationship between the local control plane and execution surfaces.

---

## 1. Role Division

- **CompText (Control Plane)**: CompText acts as the offline-first control plane. It defines context packs, executes verification commands, and manages local agent state schemas.
- **Antigravity (Execution Surface)**: Antigravity acts as the execution surface. It reads context packs to formulate prompt queries, but the control plane remains the authoritative boundary.

---

## 2. Bounded Evidence Trail

Agent state JSON files serve as bounded evidence trails. By logging the status and SHA-256 hashes of changed files, the control plane can verify that execution is consistent with the planned task boundary.
All audits, verification, and state reporting occur locally without remote coordination.
