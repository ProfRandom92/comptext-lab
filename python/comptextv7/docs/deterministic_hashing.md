# Deterministic Shared Serialization and Hashing

## Purpose
This document outlines the rules and implementation details for deterministic hashing in CompTextv7. These utilities are foundational for creating stable replay artifacts and ensuring consistent identification of semantic states across different runs.

## Utilities

### stableStringify(value, options)
A synchronous, dependency-free function that converts any value into a deterministic JSON string.

#### Rules
- **Key Ordering**: Object keys are recursively sorted alphabetically.
- **Array Order**: Preserved as-is.
- **Undefined / Non-Serializable Fields**:
  - In **objects**, fields with values of `undefined`, `function`, or `symbol` are **dropped** (matching `JSON.stringify` behavior).
  - In **arrays**, these values are replaced with deterministic placeholders to avoid invalid JSON and maintain array length:
    - `undefined` -> `"[UNDEFINED]"`
    - `function` -> `"[NON_SERIALIZABLE_FUNCTION]"`
    - `symbol` -> `"[NON_SERIALIZABLE_SYMBOL]"`
- **NaN**: Serialized as `"[NON_FINITE_NUMBER_NAN]"`.
- **Infinity**: Serialized as `"[NON_FINITE_NUMBER_INFINITY]"`.
- **-Infinity**: Serialized as `"[NON_FINITE_NUMBER_NEGATIVE_INFINITY]"`.
- **Immutability**: Does not mutate the input object.

#### Safety Limits
- **maxDepth**: Default is 8. Exceeding this depth replaces values with `"[MAX_DEPTH_EXCEEDED]"`.
- **maxStringLength**: Default is 1024 characters. Exceeding this length replaces the string with a placeholder: `"[TRUNCATED_STRING_HASH_<hash>_LENGTH_<length>]"`.

### stableNonCryptoHash(input)
A tiny synchronous 32-bit FNV-1a hash implementation.

- **Deterministic**: Produces the same output for the same input across repeated runs.
- **Output**: Returns a compact 8-character lowercase hex string.
- **Non-Cryptographic**: This hash is NOT for security. It is used for deterministic differentiation and fingerprinting of states.

### stableHash(value, options)
Combines `stableStringify` and `stableNonCryptoHash` to produce a deterministic fingerprint for any object.

- **Stability**: Objects with the same semantic content but different insertion order produce the same hash.
- **Synchronous**: Does not use WebCrypto or return Promises.

## Why this supports replay artifact determinism
Replay artifacts rely on stable identifiers for snapshots, events, and semantic references. By using deterministic serialization and hashing:
1. We can detect when the state of a replay has deviated from the original execution.
2. We can deduplicate semantic references based on their content hash.
3. We ensure that replaying the same sequence of events results in identical artifact fingerprints.
