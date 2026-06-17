import type { ExecutionEvent } from './executionEventLog';
import { stableHash, uniqueStable } from './shared';

export interface ReplaySnapshot {
  snapshotId: string;
  executionId: string;
  stepId: string;
  timestamp: string;
  inputRefIds: string[];
  outputRefIds: string[];
  memoryRefIds: string[];
  toolCallRefs: string[];
  tokenIn: number;
  tokenOut: number;
  qualityScore?: number;
  artifactRefs: string[];
  stateHash: string;
}

export interface ReplayBranch {
  branchId: string;
  executionId: string;
  fromStepId: string;
  baseSnapshotId: string;
  parentStateHash: string;
  createdAt: string;
  reason?: string;
}

export interface ReplayTimeline {
  executionId: string;
  snapshots: ReplaySnapshot[];
}

export interface ReplayComparison {
  leftExecutionId: string;
  rightExecutionId: string;
  tokenCost: { left: number; right: number; delta: number };
  memoryInjection: { added: string[]; removed: string[]; shared: string[] };
  toolCalls: { added: string[]; removed: string[]; shared: string[] };
  outputReferenceDiff: { added: string[]; removed: string[]; shared: string[] };
  qualityScore: { left?: number; right?: number; delta?: number };
  changedArtifactReferences: { added: string[]; removed: string[]; shared: string[] };
}

function refSetDifference(left: readonly string[], right: readonly string[]): string[] {
  const rightSet = new Set(right);
  return uniqueStable(left.filter((value) => !rightSet.has(value)));
}

function refSetIntersection(left: readonly string[], right: readonly string[]): string[] {
  const rightSet = new Set(right);
  return uniqueStable(left.filter((value) => rightSet.has(value)));
}

function metadataRefs(event: ExecutionEvent, key: string): string[] {
  const payload = event.compactPayload;
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const value = payload[key];
    if (Array.isArray(value) && value.every((entry) => typeof entry === 'string')) {
      return value;
    }
  }
  return [];
}

export function createReplaySnapshot(event: ExecutionEvent, priorEvents: readonly ExecutionEvent[] = []): ReplaySnapshot {
  const relevantEvents = [...priorEvents.filter((candidate) => candidate.executionId === event.executionId), event];
  const memoryRefIds = uniqueStable(relevantEvents.flatMap((candidate) => candidate.eventType === 'memory.injected' ? candidate.outputRefIds : metadataRefs(candidate, 'memoryRefIds')));
  const toolCallRefs = uniqueStable(relevantEvents.flatMap((candidate) => candidate.eventType === 'tool.called' ? candidate.outputRefIds : metadataRefs(candidate, 'toolCallRefs')));
  const artifactRefs = uniqueStable(relevantEvents.flatMap((candidate) => candidate.eventType === 'diff.generated' || candidate.eventType === 'file.read' ? candidate.outputRefIds : metadataRefs(candidate, 'artifactRefs')));
  const tokenIn = relevantEvents.reduce((sum, candidate) => sum + candidate.tokenIn, 0);
  const tokenOut = relevantEvents.reduce((sum, candidate) => sum + candidate.tokenOut, 0);
  const qualityScore = relevantEvents.reduce<number | undefined>((score, candidate) => {
    const payload = candidate.compactPayload;
    if (payload && typeof payload === 'object' && !Array.isArray(payload) && typeof payload.qualityScore === 'number') {
      return payload.qualityScore;
    }
    return score;
  }, undefined);

  const stateHash = stableHash({
    executionId: event.executionId,
    stepId: event.stepId,
    inputRefIds: uniqueStable(event.inputRefIds),
    outputRefIds: uniqueStable(event.outputRefIds),
    memoryRefIds,
    toolCallRefs,
    artifactRefs,
    tokenIn,
    tokenOut,
    qualityScore,
  });

  return Object.freeze({
    snapshotId: `snapshot-${stateHash.slice(-8)}`,
    executionId: event.executionId,
    stepId: event.stepId,
    timestamp: event.timestamp,
    inputRefIds: uniqueStable(event.inputRefIds),
    outputRefIds: uniqueStable(event.outputRefIds),
    memoryRefIds,
    toolCallRefs,
    tokenIn,
    tokenOut,
    qualityScore,
    artifactRefs,
    stateHash,
  });
}

export function branchFromStep(snapshot: ReplaySnapshot, createdAt = new Date().toISOString(), reason?: string): ReplayBranch {
  return Object.freeze({
    branchId: `branch-${stableHash({ snapshotId: snapshot.snapshotId, createdAt, reason: reason ?? null }).slice(-8)}`,
    executionId: snapshot.executionId,
    fromStepId: snapshot.stepId,
    baseSnapshotId: snapshot.snapshotId,
    parentStateHash: snapshot.stateHash,
    createdAt,
    reason,
  });
}

export class ReplayComparator {
  compare(left: ReplayTimeline, right: ReplayTimeline): ReplayComparison {
    return compareReplayRuns(left, right);
  }
}

export function compareReplayRuns(left: ReplayTimeline, right: ReplayTimeline): ReplayComparison {
  const leftRefs = collectTimelineRefs(left);
  const rightRefs = collectTimelineRefs(right);
  const leftQuality = lastQuality(left.snapshots);
  const rightQuality = lastQuality(right.snapshots);
  return {
    leftExecutionId: left.executionId,
    rightExecutionId: right.executionId,
    tokenCost: { left: leftRefs.tokenCost, right: rightRefs.tokenCost, delta: rightRefs.tokenCost - leftRefs.tokenCost },
    memoryInjection: compareRefs(leftRefs.memoryRefIds, rightRefs.memoryRefIds),
    toolCalls: compareRefs(leftRefs.toolCallRefs, rightRefs.toolCallRefs),
    outputReferenceDiff: compareRefs(leftRefs.outputRefIds, rightRefs.outputRefIds),
    qualityScore: { left: leftQuality, right: rightQuality, delta: leftQuality === undefined || rightQuality === undefined ? undefined : rightQuality - leftQuality },
    changedArtifactReferences: compareRefs(leftRefs.artifactRefs, rightRefs.artifactRefs),
  };
}

function compareRefs(left: readonly string[], right: readonly string[]) {
  return {
    added: refSetDifference(right, left),
    removed: refSetDifference(left, right),
    shared: refSetIntersection(left, right),
  };
}

function collectTimelineRefs(timeline: ReplayTimeline) {
  return {
    tokenCost: timeline.snapshots.reduce((sum, snapshot) => sum + snapshot.tokenIn + snapshot.tokenOut, 0),
    memoryRefIds: uniqueStable(timeline.snapshots.flatMap((snapshot) => snapshot.memoryRefIds)),
    toolCallRefs: uniqueStable(timeline.snapshots.flatMap((snapshot) => snapshot.toolCallRefs)),
    outputRefIds: uniqueStable(timeline.snapshots.flatMap((snapshot) => snapshot.outputRefIds)),
    artifactRefs: uniqueStable(timeline.snapshots.flatMap((snapshot) => snapshot.artifactRefs)),
  };
}

function lastQuality(snapshots: readonly ReplaySnapshot[]): number | undefined {
  return [...snapshots].reverse().find((snapshot) => snapshot.qualityScore !== undefined)?.qualityScore;
}
