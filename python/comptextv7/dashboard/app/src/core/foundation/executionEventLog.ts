import { type JsonValue, assertJsonSerializable, stableHash } from './shared';

export const executionEventTypes = [
  'execution.started',
  'agent.thinking',
  'context.selected',
  'memory.injected',
  'tool.called',
  'file.read',
  'diff.generated',
  'command.executed',
  'test.finished',
  'quality.evaluated',
  'replay.snapshot.created',
  'execution.completed',
  'execution.failed',
] as const;

export type ExecutionEventType = (typeof executionEventTypes)[number];
export type ExecutionEventStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped';

export interface ExecutionEvent {
  executionId: string;
  stepId: string;
  agentId: string;
  timestamp: string;
  eventType: ExecutionEventType;
  inputRefIds: string[];
  outputRefIds: string[];
  tokenIn: number;
  tokenOut: number;
  latencyMs: number;
  status: ExecutionEventStatus;
  compactPayload: JsonValue;
}

export interface ExecutionTimelineSummary {
  executionId: string;
  eventCount: number;
  startedAt?: string;
  completedAt?: string;
  status: ExecutionEventStatus;
  totalTokenIn: number;
  totalTokenOut: number;
  totalLatencyMs: number;
  eventTypeCounts: Record<ExecutionEventType, number>;
  inputRefIds: string[];
  outputRefIds: string[];
  stepIds: string[];
}

export interface ExecutionEventLog {
  append(event: ExecutionEvent): ExecutionEvent;
  list(executionId?: string): ExecutionEvent[];
}

function assertNonNegativeInteger(value: number, label: string): void {
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
}

function cloneEvent(event: ExecutionEvent): ExecutionEvent {
  return Object.freeze({
    ...event,
    inputRefIds: Object.freeze([...event.inputRefIds]) as unknown as string[],
    outputRefIds: Object.freeze([...event.outputRefIds]) as unknown as string[],
    compactPayload: JSON.parse(JSON.stringify(event.compactPayload)) as JsonValue,
  });
}

export class InMemoryExecutionEventStore implements ExecutionEventLog {
  private readonly events: ExecutionEvent[] = [];

  append(event: ExecutionEvent): ExecutionEvent {
    validateExecutionEvent(event);
    const stored = cloneEvent(event);
    this.events.push(stored);
    return stored;
  }

  list(executionId?: string): ExecutionEvent[] {
    return this.events
      .filter((event) => executionId === undefined || event.executionId === executionId)
      .map(cloneEvent);
  }
}

export function validateExecutionEvent(event: ExecutionEvent): void {
  if (!executionEventTypes.includes(event.eventType)) {
    throw new Error(`Unsupported execution event type: ${event.eventType}`);
  }
  assertNonNegativeInteger(event.tokenIn, 'tokenIn');
  assertNonNegativeInteger(event.tokenOut, 'tokenOut');
  assertNonNegativeInteger(event.latencyMs, 'latencyMs');
  assertJsonSerializable(event.compactPayload, 'compactPayload');
  const payloadSize = JSON.stringify(event.compactPayload).length;
  if (payloadSize > 4096) {
    throw new Error(`compactPayload must stay small; received ${payloadSize} bytes`);
  }
}

export function appendExecutionEvent(store: ExecutionEventLog, event: ExecutionEvent): ExecutionEvent {
  return store.append(event);
}

export function getExecutionTimeline(store: ExecutionEventLog, executionId: string): ExecutionEvent[] {
  return store
    .list(executionId)
    .map((event, index) => ({ event, index }))
    .sort((left, right) => left.event.timestamp.localeCompare(right.event.timestamp) || left.index - right.index)
    .map(({ event }) => event);
}

export function summarizeExecutionEvents(events: readonly ExecutionEvent[], executionId = events[0]?.executionId ?? 'unknown'): ExecutionTimelineSummary {
  const ordered = events
    .filter((event) => event.executionId === executionId)
    .map((event, index) => ({ event, index }))
    .sort((left, right) => left.event.timestamp.localeCompare(right.event.timestamp) || left.index - right.index)
    .map(({ event }) => event);

  const eventTypeCounts = Object.fromEntries(executionEventTypes.map((eventType) => [eventType, 0])) as Record<ExecutionEventType, number>;
  for (const event of ordered) {
    eventTypeCounts[event.eventType] += 1;
  }
  const terminal = [...ordered].reverse().find((event) => event.eventType === 'execution.completed' || event.eventType === 'execution.failed');
  const failed = ordered.some((event) => event.status === 'failed' || event.eventType === 'execution.failed');

  return {
    executionId,
    eventCount: ordered.length,
    startedAt: ordered[0]?.timestamp,
    completedAt: terminal?.timestamp,
    status: terminal?.status ?? (failed ? 'failed' : ordered.at(-1)?.status ?? 'pending'),
    totalTokenIn: ordered.reduce((sum, event) => sum + event.tokenIn, 0),
    totalTokenOut: ordered.reduce((sum, event) => sum + event.tokenOut, 0),
    totalLatencyMs: ordered.reduce((sum, event) => sum + event.latencyMs, 0),
    eventTypeCounts,
    inputRefIds: Array.from(new Set(ordered.flatMap((event) => event.inputRefIds))).sort(),
    outputRefIds: Array.from(new Set(ordered.flatMap((event) => event.outputRefIds))).sort(),
    stepIds: ordered.map((event) => event.stepId),
  };
}

export function eventFingerprint(event: ExecutionEvent): string {
  return stableHash({
    executionId: event.executionId,
    stepId: event.stepId,
    eventType: event.eventType,
    inputRefIds: event.inputRefIds,
    outputRefIds: event.outputRefIds,
    compactPayload: event.compactPayload,
  });
}
