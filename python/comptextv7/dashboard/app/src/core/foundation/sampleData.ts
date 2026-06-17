import { CompressionSignalEngine, type CompressionSignalInput } from './compressionSignals';
import { DecisionQualityEngine } from './decisionQuality';
import { InMemoryExecutionEventStore, appendExecutionEvent, getExecutionTimeline, summarizeExecutionEvents } from './executionEventLog';
import { createReplaySnapshot } from './replaySnapshot';
import { CompactPromptBuilder, ContextManifestBuilder, SemanticReferenceRegistry, TokenBudgetManager } from './semanticReferences';
import { ReferenceIndexEntry, buildReferenceIndex } from './referenceIndex';
import { eventFingerprint, mapCompressionSignalsToStepIds } from './eventLogArtifactAdapter';
import { createReplayArtifact } from './replayArtifactWriter';

const registry = new SemanticReferenceRegistry();
const reference = registry.register({
  uri: 'ctx://example/core-promise',
  summary: 'CompTextv7 keeps execution observable through compact semantic references.',
  tokenEstimate: 18,
  relevanceScore: 0.95,
  resolver: 'static-sample',
  createdAt: '2026-05-15T00:00:00.000Z',
  metadata: { rawTokenEstimate: 120 },
});

const referenceIndexEntries: ReferenceIndexEntry[] = [
  {
    id: reference.id,
    uri: reference.uri,
    type: reference.type,
    summary: reference.summary,
    tokenEstimate: reference.tokenEstimate,
    relevanceScore: reference.relevanceScore,
    hash: reference.hash,
    resolver: reference.resolver,
    createdAt: reference.createdAt,
    expiresAt: reference.expiresAt,
  }
];

const referenceIndex = buildReferenceIndex(referenceIndexEntries);

const manifest = new ContextManifestBuilder(new TokenBudgetManager(64)).build('exec-sample', [reference], '2026-05-15T00:00:01.000Z');
export const eventStore = new InMemoryExecutionEventStore();
export const event = appendExecutionEvent(eventStore, {
  executionId: 'exec-sample',
  stepId: 'step-1',
  agentId: 'agent-core',
  timestamp: '2026-05-15T00:00:02.000Z',
  eventType: 'context.selected',
  inputRefIds: [],
  outputRefIds: [reference.id],
  tokenIn: 18,
  tokenOut: 0,
  latencyMs: 3,
  status: 'succeeded',
  compactPayload: { manifestId: manifest.manifestId, requestId: 'req-123', traceId: 'trace-abc', durationMs: 45 },
});

const eventFingerprintSample = eventFingerprint(event, { normalizationVersion: 1 });

export const compressionSignalWindows: CompressionSignalInput[] = [
  {
    executionId: 'exec-sample',
    windowId: 'signal-stable-known-family',
    timestamp: '2026-05-15T00:00:03.000Z',
    profileId: 'known-family',
    compressionRatio: 0.79,
    baselineCompressionRatio: 0.8,
    sparseFrameRate: 0.11,
    baselineSparseFrameRate: 0.1,
    unseenSignatureRate: 0.02,
  },
  {
    executionId: 'exec-sample',
    windowId: 'signal-minor-fluctuation',
    timestamp: '2026-05-15T00:00:04.000Z',
    profileId: 'known-family',
    compressionRatio: 0.72,
    baselineCompressionRatio: 0.8,
    sparseFrameRate: 0.18,
    baselineSparseFrameRate: 0.1,
    unseenSignatureRate: 0.08,
  },
  {
    executionId: 'exec-sample',
    windowId: 'signal-sparse-signature-spike-a',
    timestamp: '2026-05-15T00:00:05.000Z',
    profileId: 'known-family',
    compressionRatio: 0.42,
    baselineCompressionRatio: 0.8,
    sparseFrameRate: 0.26,
    baselineSparseFrameRate: 0.1,
    unseenSignatureRate: 0.72,
  },
  {
    executionId: 'exec-sample',
    windowId: 'signal-sparse-signature-spike-b',
    timestamp: '2026-05-15T00:00:06.000Z',
    profileId: 'known-family',
    compressionRatio: 0.44,
    baselineCompressionRatio: 0.8,
    sparseFrameRate: 0.25,
    baselineSparseFrameRate: 0.1,
    unseenSignatureRate: 0.7,
  },
  {
    executionId: 'exec-sample',
    windowId: 'signal-severe-unknown-pattern',
    timestamp: '2026-05-15T00:00:07.000Z',
    profileId: 'known-family',
    compressionRatio: 0.08,
    baselineCompressionRatio: 0.8,
    sparseFrameRate: 0.31,
    baselineSparseFrameRate: 0.1,
    unseenSignatureRate: 0.95,
  },
];

export const compressionSignalResults = new CompressionSignalEngine().evaluateSignalSequence(compressionSignalWindows);

const compressionMappingSample = mapCompressionSignalsToStepIds(compressionSignalResults, [event]);


const sampleReplayArtifact = createReplayArtifact({
  artifactId: 'artifact-sample-1',
  executionId: 'exec-sample',
  createdAt: '2026-05-15T00:00:10.000Z',
  referenceIndex,
  events: [event],
  compressionSignals: compressionSignalResults,
});

export const coreFoundationSample = Object.freeze({
  events: Object.freeze([event]),
  sampleReplayArtifact,

  reference,
  referenceIndex,
  manifest,
  compactPrompt: new CompactPromptBuilder().build(manifest),
  timelineSummary: summarizeExecutionEvents(getExecutionTimeline(eventStore, 'exec-sample'), 'exec-sample'),
  replaySnapshot: createReplaySnapshot(event),
  eventFingerprint: eventFingerprintSample,
  compressionMapping: compressionMappingSample,
  quality: new DecisionQualityEngine({
    weights: { validity: 1, specificity: 1, correctness: 1, traceability: 1, rollbackSafety: 1, tokenEfficiency: 1 },
    tokenBudget: 64,
  }).evaluate({
    validityChecksPassed: 1,
    validityChecksTotal: 1,
    specificCriteriaMet: 1,
    specificCriteriaTotal: 1,
    correctnessChecksPassed: 1,
    correctnessChecksTotal: 1,
    linkedReplayStepIds: ['step-1'],
    linkedReferenceIds: [reference.id],
    artifactRefs: [],
    replaySnapshotIds: [],
    tokenUsed: manifest.totalTokenEstimate,
  }),
  compressionSignalWindows: Object.freeze(compressionSignalWindows),
  compressionSignalResults: Object.freeze(compressionSignalResults),
});
