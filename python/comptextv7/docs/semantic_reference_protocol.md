# Semantic Reference Protocol

## Purpose

The Semantic Reference Protocol is the compact context layer for the CompTextv7 core foundation. It replaces repeated raw prompt context with stable references that can be selected, omitted, and hydrated only when explicitly requested.

Supported schemes are `ctx://`, `mem://`, `replay://`, `artifact://`, `tool://`, `file://`, and `run://`.

## Data shape

A `SemanticReference` carries an `id`, typed `uri`, compact `summary`, `tokenEstimate`, `relevanceScore`, stable `hash`, abstract `resolver`, creation time, optional expiry, and optional JSON metadata. A `ContextManifest` records the selected and omitted references for one execution plus the selected token estimate and avoided raw-token estimate.

Core primitives:

- `SemanticReferenceRegistry`
- `ReferenceResolver`
- `ContextManifestBuilder`
- `CompactPromptBuilder`
- `TokenBudgetManager`

## Why it supports token-efficient replay

The registry deduplicates by URI and hash, the token budget manager selects references before prompt construction, and compact prompts include summaries by default rather than hydrating raw content. The manifest becomes a replayable record of exactly which semantic context was available and what was omitted.

## Compact JSON example

```json
{
  "manifestId": "manifest-a1b2c3d4",
  "executionId": "exec-123",
  "selectedRefs": [
    {
      "id": "ctx-fnv1a0abc1234",
      "uri": "ctx://task/core-promise",
      "type": "ctx",
      "summary": "Token-efficient replayable execution foundation.",
      "tokenEstimate": 12,
      "relevanceScore": 0.98,
      "hash": "fnv1a:0abc1234",
      "resolver": "local-registry",
      "createdAt": "2026-05-15T00:00:00.000Z"
    }
  ],
  "omittedRefs": [],
  "totalTokenEstimate": 12,
  "rawTokenAvoided": 180,
  "createdAt": "2026-05-15T00:00:01.000Z"
}
```

## Current limitations

This is a model-only protocol. Resolvers are abstract and make no network calls. Persistence, encrypted reference storage, distributed cache invalidation, and full memory-governance policy are intentionally left for later PRs.
