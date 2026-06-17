export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

/**
 * A tiny synchronous dependency-free non-cryptographic hash (FNV-1a 32-bit).
 * Deterministic across repeated runs. Not for security.
 */
export function stableNonCryptoHash(input: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

export interface StableStringifyOptions {
  maxDepth?: number;
  maxStringLength?: number;
}

/**
 * Deterministically stringifies a value with recursive key sorting,
 * NaN/Infinity handling, and depth/length limits.
 *
 * Rules:
 * - Object properties with undefined/function/symbol are dropped.
 * - Array entries with undefined/function/symbol use deterministic placeholders.
 */
export function stableStringify(value: unknown, options: StableStringifyOptions = {}): string {
  const maxDepth = options.maxDepth ?? 8;
  const maxStringLength = options.maxStringLength ?? 1024;

  function stringifyInternal(val: unknown, depth: number, isArrayElement: boolean): string | undefined {
    if (depth > maxDepth) {
      return '"[MAX_DEPTH_EXCEEDED]"';
    }

    if (val === undefined) {
      return isArrayElement ? '"[UNDEFINED]"' : undefined;
    }
    if (typeof val === 'function') {
      return isArrayElement ? '"[NON_SERIALIZABLE_FUNCTION]"' : undefined;
    }
    if (typeof val === 'symbol') {
      return isArrayElement ? '"[NON_SERIALIZABLE_SYMBOL]"' : undefined;
    }

    if (val === null) return 'null';
    if (typeof val === 'boolean') return val ? 'true' : 'false';

    if (typeof val === 'number') {
      if (Number.isNaN(val)) return '"[NON_FINITE_NUMBER_NAN]"';
      if (val === Infinity) return '"[NON_FINITE_NUMBER_INFINITY]"';
      if (val === -Infinity) return '"[NON_FINITE_NUMBER_NEGATIVE_INFINITY]"';
      return JSON.stringify(val);
    }

    if (typeof val === 'string') {
      if (val.length > maxStringLength) {
        const hash = stableNonCryptoHash(val);
        return '"' + `[TRUNCATED_STRING_HASH_${hash}_LENGTH_${val.length}]` + '"';
      }
      return JSON.stringify(val);
    }

    if (Array.isArray(val)) {
      const parts = val.map((item) => stringifyInternal(item, depth + 1, true) ?? '"[UNDEFINED]"');
      return `[${parts.join(',')}]`;
    }

    if (typeof val === 'object') {
      const entries = Object.entries(val as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right));

      const parts: string[] = [];
      for (const [key, entry] of entries) {
        const s = stringifyInternal(entry, depth + 1, false);
        if (s !== undefined) {
          parts.push(`${JSON.stringify(key)}:${s}`);
        }
      }
      return `{${parts.join(',')}}`;
    }

    return '"[UNKNOWN_TYPE]"';
  }

  // Top-level value is treated like an array element (not dropped)
  return stringifyInternal(value, 0, true) ?? '"[UNDEFINED]"';
}

/**
 * Synchronous stable hash using stableStringify and stableNonCryptoHash.
 */
export function stableHash(value: unknown, options?: StableStringifyOptions): string {
  const serialized = stableStringify(value, options);
  return `fnv1a:${stableNonCryptoHash(serialized)}`;
}

export function uniqueStable(values: readonly string[]): string[] {
  return Array.from(new Set(values)).sort((left, right) => left.localeCompare(right));
}

export function assertJsonSerializable(value: unknown, label: string): asserts value is JsonValue {
  try {
    const serialized = JSON.stringify(value);
    if (serialized === undefined) {
      throw new Error('value serializes to undefined');
    }
  } catch (error) {
    throw new Error(`${label} must be JSON-serializable: ${error instanceof Error ? error.message : String(error)}`);
  }
}
