# Agent Skill 04 — SPARK Context Layer

This skill outlines the design concepts for representing compact, replay-safe operational contexts inside SPARK-style packages.

## 1. Core Purpose

The SPARK Context Layer exists to package prior task history and metadata into a minimal, deterministic, and replay-safe payload. It is NOT an orchestration framework or active workflow runner.

## 2. Design Anchors (For Future Integration Only)

When implemented, the context layer must preserve the following metadata blocks:
- **Causal dependency edges** (e.g. step A must precede step B)
- **Constraint lists & Blockers**
- **Recovery paths & Alternative plans**
- **Schema validation anchors**
- **Task & Context identifiers**

## 3. Strict Context Constraints (Do NOT Violate)

- **No Active Code Execution:** Do not write execution loops or implement tool runners.
- **No External Integrations:** Do not connect to LiteLLM, VLLM, database proxies, or outer APIs.
- **No MCP Server Role:** Do not bundle the library as a Model Context Protocol server.
- **Strict Leak Rules:**
  - **No Raw Dumps:** Rendered prompts/contexts must not dump the entire raw payload or trace history.
  - **Token Hygiene:** Output must be token-light, summarized, and deterministic.
