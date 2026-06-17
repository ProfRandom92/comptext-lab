# Cryptographic Provenance Model

This document outlines the design and local verification guidelines for the CompText Cryptographic Provenance Engine.

---

## 1. Local Integrity Manifest Model

CompText utilizes local provenance manifests to track artifact changes and link them back to their origin task context.

- **Schema Definition**: Provenance manifests are stored as JSON files with the `.provenance.json` extension alongside their matching artifact.
- **Raw file content SHA-256**: Checksums are computed entirely offline using a self-contained SHA-256 algorithm.
- **Parent Link**: Connects the artifact to its preceding parent artifact or task description to establish a local chain of custody.

### Schema Shape
```json
{
  "schema_version": "0.1",
  "artifact_path": ".comptext/context_pack.latest.json",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "parent_link": "task_description_or_proposal_path",
  "metadata": {
    "timestamp": "2026-06-05T10:57:20Z"
  }
}
```

---

## 2. Boundaries and Scope Limits

- **Local-Only Verification**: Checksums are calculated locally. No blockchain, distributed consensus, or remote network validation is supported or implemented.
- **No Unsupported Assurance Claims**: These manifests are for change detection and chain of custody tracking. They do not constitute unsupported assurance claims.
- **Untrusted Input Stance**: Any file without a matching/valid provenance manifest or one whose checksum fails verification is treated as mutated and untrusted.
