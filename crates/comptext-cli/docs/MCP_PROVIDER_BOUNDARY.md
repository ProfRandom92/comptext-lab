# MCP and Provider Boundary

Model Context Protocol providers provide context and tool surfaces. They are security-sensitive boundaries.

## Minimal MCP stack

1. Git MCP for repo topology, history context, and diffs.
2. Developer knowledge/docs MCP for API and SDK documentation.
3. Optional internal docs/RAG MCP for Comptextv7, comptext-sparkctl, and historical CompText CLI material.
4. Optional CI/logs MCP later, read-only.

## Rules

- Prefer read-only MCP access.
- Do not route secrets into Context Packs.
- Do not let MCP tools apply source changes outside the proposal/apply flow.
- Do not use deploy/cloud/database write tools in the initial build.
- Treat MCP output as untrusted input that must be normalized and validated.
