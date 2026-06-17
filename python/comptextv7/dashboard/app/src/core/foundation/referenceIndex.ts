import { stableHash } from './shared';

export const allowedReferenceSchemes = ['ctx', 'mem', 'replay', 'artifact', 'tool', 'file', 'run'] as const;
export type AllowedReferenceScheme = (typeof allowedReferenceSchemes)[number];

export interface ReferenceIndexEntry {
  id: string;
  uri: string;
  type: string;
  summary: string;
  tokenEstimate: number;
  relevanceScore: number;
  hash: string;
  resolver: string;
  createdAt: string;
  expiresAt?: string;
}

export interface ReferenceIndex {
  entries: ReferenceIndexEntry[];
}

export interface ReferenceIndexValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateReferenceUri(uri: string): ReferenceIndexValidationResult {
  const errors: string[] = [];

  const schemeMatch = uri.match(/^([a-z]+):\/\/(.*)$/i);
  if (!schemeMatch) {
    errors.push(`Invalid URI format: ${uri}`);
    return { valid: false, errors };
  }

  const [, scheme, path] = schemeMatch;
  if (!allowedReferenceSchemes.includes(scheme as AllowedReferenceScheme)) {
    errors.push(`Unsupported URI scheme: ${scheme}`);
    return { valid: false, errors };
  }

  if (scheme === 'file') {
    if (!path || path.trim() === '') {
      errors.push(`Empty file path: ${uri}`);
    } else if (path.startsWith('/')) {
      errors.push(`Absolute file path forbidden: ${uri}`);
    } else if (path.match(/^[a-zA-Z]:(\/|\\)/)) {
      errors.push(`Windows absolute file path forbidden: ${uri}`);
    } else if (path.startsWith('\\\\')) {
      errors.push(`Network share file path forbidden: ${uri}`);
    } else if (uri.startsWith('file://localhost/')) {
      errors.push(`Localhost file path forbidden: ${uri}`);
    } else if (uri.startsWith('file://127.0.0.1/')) {
      errors.push(`Loopback file path forbidden: ${uri}`);
    } else {
      // Check for traversal
      const decodedPath = decodeURIComponent(path);
      if (decodedPath.includes('..') || decodedPath.includes('\\') || path.includes('..') || path.includes('%2e%2e') || path.includes('%2E%2E') || path.includes('\\') || path.includes('%5c') || path.includes('%5C')) {
        errors.push(`Path traversal forbidden: ${uri}`);
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

export function buildReferenceIndex(entries: ReferenceIndexEntry[]): ReferenceIndex {
  const seenIds = new Set<string>();
  const seenUris = new Set<string>();
  const seenHashes = new Set<string>();
  const deduped: ReferenceIndexEntry[] = [];

  for (const entry of entries) {
    if (!seenIds.has(entry.id) && !seenUris.has(entry.uri) && !seenHashes.has(entry.hash)) {
      seenIds.add(entry.id);
      seenUris.add(entry.uri);
      seenHashes.add(entry.hash);
      deduped.push(entry);
    }
  }

  const sortedEntries = deduped.sort((a, b) => {
    // Sort deterministically
    if (a.createdAt !== b.createdAt) return a.createdAt.localeCompare(b.createdAt);
    if (a.id !== b.id) return a.id.localeCompare(b.id);
    if (a.uri !== b.uri) return a.uri.localeCompare(b.uri);
    return a.hash.localeCompare(b.hash);
  });

  return { entries: sortedEntries };
}

export function mergeReferenceIndexes(indexes: ReferenceIndex[]): ReferenceIndex {
  const allEntries = indexes.flatMap((idx) => idx.entries);
  return buildReferenceIndex(allEntries);
}

export function validateReferenceIndex(index: ReferenceIndex): ReferenceIndexValidationResult {
  const errors: string[] = [];
  for (const entry of index.entries) {
    const uriValidation = validateReferenceUri(entry.uri);
    if (!uriValidation.valid) {
      errors.push(...uriValidation.errors);
    }
  }
  return { valid: errors.length === 0, errors };
}
