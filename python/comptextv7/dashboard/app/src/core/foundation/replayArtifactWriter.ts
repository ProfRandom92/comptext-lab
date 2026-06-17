import { ExecutionEvent, ExecutionTimelineSummary } from './executionEventLog';
import { ReplaySnapshot } from './replaySnapshot';
import { CompressionSignalResult } from './compressionSignals';
import {
  ReferenceIndex,
  ReferenceIndexEntry,
  buildReferenceIndex
} from './referenceIndex';
import { SemanticReference } from './semanticReferences';
import {
  PayloadNormalizationVersion,
  ReplayArtifactEventFingerprint,
  MappedCompressionSignal,
  eventFingerprint,
  buildReplayTimelineSummaryFromEvents,
  buildReplaySnapshotsFromEvents,
  mapCompressionSignalsToStepIds
} from './eventLogArtifactAdapter';
import { stableHash, stableStringify } from './shared';

export type ReplayArtifactSchemaVersion = 'v1-alpha.1';

export interface ReplayArtifactCompressionSummary {
  totalSignals: number;
  triggeredSignals: number;
  averageCompressionRatio: number | null;
  totalTokenIn: number | null;
  totalTokenOut: number | null;
  mappedStepCount: number;
  unmappedStepCount: number;
  unmappedReasons: string[];
}

export interface ReplayArtifactIntegrity {
  artifactHash: string;
  artifactHashAlgorithm: string;
  normalizationVersion: PayloadNormalizationVersion;
  deterministicSerializationVersion: 1;
}

export interface ReplayArtifact {
  schemaVersion: ReplayArtifactSchemaVersion;
  artifactId: string;
  executionId: string;
  createdAt: string;
  referenceIndex: ReferenceIndex;
  eventFingerprints: ReplayArtifactEventFingerprint[];
  replayTimelineSummary: ExecutionTimelineSummary;
  replaySnapshots: ReplaySnapshot[];
  compressionSignalMappings: MappedCompressionSignal[];
  compressionSummary: ReplayArtifactCompressionSummary;
  integrity: ReplayArtifactIntegrity;
}

export interface ReplayArtifactWriterInput {
  artifactId: string;
  executionId: string;
  createdAt: string;
  references?: SemanticReference[];
  referenceIndex?: ReferenceIndex;
  events: ExecutionEvent[];
  compressionSignals: CompressionSignalResult[];
}

export interface ReplayArtifactValidationResult {
  valid: boolean;
  errors: string[];
}

export function createReplayArtifact(input: ReplayArtifactWriterInput): ReplayArtifact {
  if (!input.references && !input.referenceIndex) {
    throw new Error('Must provide either references or referenceIndex');
  }

  const referenceIndex = input.referenceIndex ?? buildReferenceIndex(input.references!);

  const normalizationVersion: PayloadNormalizationVersion = 1;
  const eventFingerprints = input.events.map(event =>
    eventFingerprint(event, { normalizationVersion })
  );

  const replayTimelineSummary = buildReplayTimelineSummaryFromEvents(input.events);
  const replaySnapshots = buildReplaySnapshotsFromEvents(input.events);

  const compressionSignalMappings = mapCompressionSignalsToStepIds(input.compressionSignals, input.events);

  let totalSignals = input.compressionSignals.length;
  let triggeredSignals = input.compressionSignals.filter(s => s.triggered).length;

  let totalTokenIn: number | null = null;
  // totalTokenOut remains null because output token estimates are not supported by the current CompressionSignalInput model.
  let totalTokenOut: number | null = null;
  let compressionRatioSum = 0;
  let compressionRatioCount = 0;

  for (const signal of input.compressionSignals) {
    if (signal.window.input.tokenEstimate !== undefined) {
      if (totalTokenIn === null) totalTokenIn = 0;
      totalTokenIn += signal.window.input.tokenEstimate;
    }

    if (signal.window.input.compressionRatio !== undefined && signal.window.input.compressionRatio !== null) {
      compressionRatioSum += signal.window.input.compressionRatio;
      compressionRatioCount++;
    }
  }

  const averageCompressionRatio = compressionRatioCount > 0 ? compressionRatioSum / compressionRatioCount : null;

  const mappedStepIds = new Set<string>();
  const unmappedStepIds = new Set<string>();
  const unmappedReasonsSet = new Set<string>();

  for (const mapping of compressionSignalMappings) {
    for (const id of mapping.associatedStepIds) mappedStepIds.add(id);
    if (mapping.unmappedStepIds) {
      for (const id of mapping.unmappedStepIds) unmappedStepIds.add(id);
    }
    if (mapping.unmappedReason) {
      unmappedReasonsSet.add(mapping.unmappedReason);
    }
  }

  let mappedStepCount = mappedStepIds.size;
  let unmappedStepCount = unmappedStepIds.size;
  const unmappedReasons = Array.from(unmappedReasonsSet).sort((a, b) => a.localeCompare(b));

  const compressionSummary: ReplayArtifactCompressionSummary = {
    totalSignals,
    triggeredSignals,
    averageCompressionRatio,
    totalTokenIn,
    totalTokenOut,
    mappedStepCount,
    unmappedStepCount,
    unmappedReasons
  };

  const artifactWithoutHash = {
    schemaVersion: 'v1-alpha.1' as ReplayArtifactSchemaVersion,
    artifactId: input.artifactId,
    executionId: input.executionId,
    createdAt: input.createdAt,
    referenceIndex,
    eventFingerprints,
    replayTimelineSummary,
    replaySnapshots,
    compressionSignalMappings,
    compressionSummary,
    integrity: {
      artifactHash: '',
      artifactHashAlgorithm: 'fnv1a-32',
      normalizationVersion,
      deterministicSerializationVersion: 1 as const
    }
  };

  const serializedForHashing = stableStringify({
    ...artifactWithoutHash,
    integrity: {
      ...artifactWithoutHash.integrity,
      artifactHash: undefined // Exclude hash itself
    }
  });

  const artifactHash = stableHash(serializedForHashing);

  artifactWithoutHash.integrity.artifactHash = artifactHash;

  return artifactWithoutHash;
}

export function serializeReplayArtifact(artifact: ReplayArtifact): string {
  return stableStringify(artifact);
}

export function parseReplayArtifact(serialized: string): ReplayArtifact {
  const parsed = JSON.parse(serialized);
  return parsed as ReplayArtifact;
}






export function validateReplayArtifact(artifact: ReplayArtifact): ReplayArtifactValidationResult {
  const errors: string[] = [];

  if (artifact.schemaVersion !== 'v1-alpha.1') {
    errors.push(`Invalid schemaVersion: expected v1-alpha.1, got ${artifact.schemaVersion}`);
  }

  if (!artifact.integrity || artifact.integrity.normalizationVersion !== 1) {
    errors.push(`Invalid normalizationVersion: expected 1, got ${artifact.integrity?.normalizationVersion}`);
  }

  if (!artifact.integrity || artifact.integrity.deterministicSerializationVersion !== 1) {
    errors.push(`Invalid deterministicSerializationVersion: expected 1, got ${artifact.integrity?.deterministicSerializationVersion}`);
  }

  if (!artifact.integrity || artifact.integrity.artifactHashAlgorithm !== 'fnv1a-32') {
    errors.push(`Invalid artifactHashAlgorithm: expected fnv1a-32, got ${artifact.integrity?.artifactHashAlgorithm}`);
  }

  if (!artifact.artifactId) errors.push('Missing artifactId');
  if (!artifact.executionId) errors.push('Missing executionId');
  if (!artifact.createdAt) errors.push('Missing createdAt');

  if (!artifact.integrity || !artifact.integrity.artifactHash) {
    errors.push('Missing artifactHash');
  } else {
    const serializedForHashing = stableStringify({
      ...artifact,
      integrity: {
        ...artifact.integrity,
        artifactHash: undefined
      }
    });
    const expectedHash = stableHash(serializedForHashing);
    if (artifact.integrity.artifactHash !== expectedHash) {
      errors.push(`artifactHash mismatch: expected ${expectedHash}, got ${artifact.integrity.artifactHash}`);
    }
  }

  if (artifact.referenceIndex) {
    if (!Array.isArray(artifact.referenceIndex.entries)) {
        errors.push('referenceIndex.entries is not an array');
    }
  } else {
      errors.push('Missing referenceIndex');
  }

  if (!artifact.replayTimelineSummary) {
      errors.push('Missing replayTimelineSummary');
  }

  if (!artifact.replaySnapshots) {
      errors.push('Missing replaySnapshots');
  }

  const allStepIds = new Set<string>();

  if (artifact.eventFingerprints) {
    if (artifact.eventFingerprints.length === 0 && artifact.replayTimelineSummary?.eventCount > 0) {
        errors.push('eventFingerprints is empty while timelineSummary.eventCount > 0');
    }
    for (let i = 0; i < artifact.eventFingerprints.length; i++) {
      const fp = artifact.eventFingerprints[i];
      if (fp.normalizationVersion !== 1) {
        errors.push(`eventFingerprints[${i}] has invalid normalizationVersion: ${fp.normalizationVersion}`);
      }
      if ('compactPayload' in fp) {
        errors.push(`eventFingerprints[${i}] contains raw compactPayload`);
      }
      allStepIds.add(fp.stepId);
    }
  } else {
      errors.push('Missing eventFingerprints');
  }

  const mappedSteps = new Set<string>();
  const unmappedSteps = new Set<string>();

  if (artifact.compressionSignalMappings) {
      for (const mapping of artifact.compressionSignalMappings) {
          for (const stepId of mapping.associatedStepIds) {
              if (mappedSteps.has(stepId)) {
                  errors.push(`duplicate mapped stepId: ${stepId}`);
              }
              mappedSteps.add(stepId);
          }
          if (mapping.unmappedStepIds) {
              for (const unmapped of mapping.unmappedStepIds) {
                 if (unmappedSteps.has(unmapped)) {
                     errors.push(`duplicate unmapped stepId: ${unmapped}`);
                 }
                 unmappedSteps.add(unmapped);
              }
          }
      }
  } else {
      errors.push('Missing compressionSignalMappings');
  }



  for (const stepId of allStepIds) {
      if (!mappedSteps.has(stepId) && !unmappedSteps.has(stepId)) {
          errors.push(`event fingerprint stepId ${stepId} is neither in associatedStepIds nor unmappedStepIds`);
      }
  }

  for (const stepId of mappedSteps) {
      if (unmappedSteps.has(stepId)) {
          errors.push(`stepId ${stepId} appears in both associatedStepIds and unmappedStepIds`);
      }
      if (!allStepIds.has(stepId)) {
          errors.push(`compression mapping refers to unknown stepId: ${stepId}`);
      }
  }

  for (const stepId of unmappedSteps) {
      if (!allStepIds.has(stepId)) {
          errors.push(`unmapped stepId refers to unknown stepId: ${stepId}`);
      }
  }




  function containsUnsafeHydration(obj: any, path: string = ''): boolean {
    if (obj === null || typeof obj !== 'object') return false;
    if (Array.isArray(obj)) {
      return obj.some((item, idx) => containsUnsafeHydration(item, path + '[' + idx + ']'));
    }
    for (const [key, value] of Object.entries(obj)) {
      const currentPath = path ? path + '.' + key : key;
      if (key === 'rawFileContents' || key === 'fileData' || key === 'rawPayload' || key === 'compactPayload') {
        return true;
      }
      if (key === 'content' || key === 'body') {
        // Only reject these specific keys if they are deeply nested inside known payload containers or metadata
        if (currentPath.includes('metadata') || currentPath.includes('compactPayload') || currentPath.includes('replaySnapshots') || currentPath.includes('compressionSignalMappings')) {
            return true;
        }
      }
      if (containsUnsafeHydration(value, currentPath)) return true;
    }
    return false;
  }


  if (containsUnsafeHydration(artifact)) {
      errors.push('Artifact contains raw file hydration fields');
  }

  return { valid: errors.length === 0, errors };

}
