import { type JsonValue, assertJsonSerializable, stableHash, stableStringify, uniqueStable } from './shared';

export const semanticReferenceSchemes = ['ctx', 'mem', 'replay', 'artifact', 'tool', 'file', 'run'] as const;
export type SemanticReferenceScheme = (typeof semanticReferenceSchemes)[number];
export type SemanticReferenceType = SemanticReferenceScheme;

export interface SemanticReference {
  id: string;
  uri: `${SemanticReferenceScheme}://${string}`;
  type: SemanticReferenceType;
  summary: string;
  tokenEstimate: number;
  relevanceScore: number;
  hash: string;
  resolver: string;
  createdAt: string;
  expiresAt?: string;
  metadata?: Record<string, JsonValue>;
}

export interface ContextManifest {
  manifestId: string;
  executionId: string;
  selectedRefs: SemanticReference[];
  omittedRefs: SemanticReference[];
  totalTokenEstimate: number;
  rawTokenAvoided: number;
  createdAt: string;
}

export interface ReferenceResolver {
  readonly resolverId: string;
  resolve(reference: SemanticReference): string | undefined;
}

export interface RegisterReferenceInput {
  uri: SemanticReference['uri'];
  type?: SemanticReferenceType;
  summary: string;
  tokenEstimate: number;
  relevanceScore: number;
  resolver: string;
  createdAt?: string;
  expiresAt?: string;
  metadata?: Record<string, JsonValue>;
  rawTokenEstimate?: number;
  hash?: string;
}

function schemeFromUri(uri: string): SemanticReferenceScheme {
  const [scheme] = uri.split('://');
  if (!semanticReferenceSchemes.includes(scheme as SemanticReferenceScheme)) {
    throw new Error(`Unsupported semantic reference scheme: ${scheme}`);
  }
  return scheme as SemanticReferenceScheme;
}

function clampScore(score: number): number {
  if (!Number.isFinite(score)) {
    throw new Error('relevanceScore must be finite');
  }
  return Math.max(0, Math.min(1, score));
}

function assertTokenEstimate(tokenEstimate: number): void {
  if (!Number.isInteger(tokenEstimate) || tokenEstimate < 0) {
    throw new Error('tokenEstimate must be a non-negative integer');
  }
}

export class SemanticReferenceRegistry {
  private readonly refsById = new Map<string, SemanticReference>();
  private readonly idsByUri = new Map<string, string>();
  private readonly idsByHash = new Map<string, string>();

  register(input: RegisterReferenceInput): SemanticReference {
    const inferredType = schemeFromUri(input.uri);
    const type = input.type ?? inferredType;
    if (type !== inferredType) {
      throw new Error(`Reference type ${type} does not match URI scheme ${inferredType}`);
    }
    assertTokenEstimate(input.tokenEstimate);
    if (input.metadata) {
      assertJsonSerializable(input.metadata, 'reference metadata');
    }

    const hash = input.hash ?? stableHash({ uri: input.uri, summary: input.summary, metadata: input.metadata ?? null });
    const existingId = this.idsByUri.get(input.uri) ?? this.idsByHash.get(hash);
    if (existingId) {
      return this.refsById.get(existingId)!;
    }

    const reference: SemanticReference = Object.freeze({
      id: `${type}-${hash.replace(/[^a-z0-9]/gi, '').slice(-12)}`,
      uri: input.uri,
      type,
      summary: input.summary,
      tokenEstimate: input.tokenEstimate,
      relevanceScore: clampScore(input.relevanceScore),
      hash,
      resolver: input.resolver,
      createdAt: input.createdAt ?? new Date().toISOString(),
      expiresAt: input.expiresAt,
      metadata: input.metadata ? Object.freeze({ ...input.metadata }) : undefined,
    });

    this.refsById.set(reference.id, reference);
    this.idsByUri.set(reference.uri, reference.id);
    this.idsByHash.set(reference.hash, reference.id);
    return reference;
  }

  get(id: string): SemanticReference | undefined {
    return this.refsById.get(id);
  }

  getByUri(uri: string): SemanticReference | undefined {
    const id = this.idsByUri.get(uri);
    return id ? this.refsById.get(id) : undefined;
  }

  list(): SemanticReference[] {
    return Array.from(this.refsById.values()).sort((left, right) => left.id.localeCompare(right.id));
  }
}

export class TokenBudgetManager {
  constructor(private readonly maxTokens: number) {
    if (!Number.isInteger(maxTokens) || maxTokens < 0) {
      throw new Error('maxTokens must be a non-negative integer');
    }
  }

  selectReferences(references: readonly SemanticReference[]): { selectedRefs: SemanticReference[]; omittedRefs: SemanticReference[]; totalTokenEstimate: number } {
    const deduped = new Map<string, SemanticReference>();
    for (const reference of references) {
      const existing = deduped.get(reference.uri) ?? deduped.get(reference.hash);
      if (!existing) {
        deduped.set(reference.uri, reference);
        deduped.set(reference.hash, reference);
      }
    }
    const candidates = uniqueStable(Array.from(deduped.values()).map((reference) => reference.id))
      .map((id) => Array.from(deduped.values()).find((reference) => reference.id === id)!)
      .sort((left, right) => right.relevanceScore - left.relevanceScore || left.tokenEstimate - right.tokenEstimate || left.id.localeCompare(right.id));

    const selectedRefs: SemanticReference[] = [];
    const omittedRefs: SemanticReference[] = [];
    let totalTokenEstimate = 0;
    for (const reference of candidates) {
      if (totalTokenEstimate + reference.tokenEstimate <= this.maxTokens) {
        selectedRefs.push(reference);
        totalTokenEstimate += reference.tokenEstimate;
      } else {
        omittedRefs.push(reference);
      }
    }
    return { selectedRefs, omittedRefs, totalTokenEstimate };
  }
}

export class ContextManifestBuilder {
  constructor(private readonly tokenBudgetManager: TokenBudgetManager) {}

  build(executionId: string, references: readonly SemanticReference[], createdAt = new Date().toISOString()): ContextManifest {
    const { selectedRefs, omittedRefs, totalTokenEstimate } = this.tokenBudgetManager.selectReferences(references);
    const rawTokenAvoided = selectedRefs.reduce((sum, reference) => {
      const rawTokenEstimate = typeof reference.metadata?.rawTokenEstimate === 'number' ? reference.metadata.rawTokenEstimate : reference.tokenEstimate;
      return sum + Math.max(0, rawTokenEstimate - reference.tokenEstimate);
    }, 0);
    return Object.freeze({
      manifestId: `manifest-${stableHash({ executionId, selected: selectedRefs.map((ref) => ref.id), omitted: omittedRefs.map((ref) => ref.id), createdAt }).slice(-8)}`,
      executionId,
      selectedRefs,
      omittedRefs,
      totalTokenEstimate,
      rawTokenAvoided,
      createdAt,
    });
  }
}

export interface CompactPromptOptions {
  hydrateRefIds?: readonly string[];
  resolvers?: ReadonlyMap<string, ReferenceResolver>;
  instruction?: string;
}

export class CompactPromptBuilder {
  build(manifest: ContextManifest, options: CompactPromptOptions = {}): string {
    const hydrateRefIds = new Set(options.hydrateRefIds ?? []);
    const lines = [options.instruction ?? 'Use semantic references. Hydrate only when explicitly requested.', `manifest: ${manifest.manifestId}`, `execution: ${manifest.executionId}`];
    for (const reference of manifest.selectedRefs) {
      const resolver = options.resolvers?.get(reference.resolver);
      const hydrated = hydrateRefIds.has(reference.id) ? resolver?.resolve(reference) : undefined;
      lines.push(stableStringify({
        id: reference.id,
        uri: reference.uri,
        type: reference.type,
        summary: reference.summary,
        tokenEstimate: reference.tokenEstimate,
        relevanceScore: reference.relevanceScore,
        hash: reference.hash,
        content: hydrated,
      }));
    }
    if (manifest.omittedRefs.length > 0) {
      lines.push(stableStringify({ omittedRefIds: manifest.omittedRefs.map((reference) => reference.id) }));
    }
    return lines.join('\n');
  }
}
