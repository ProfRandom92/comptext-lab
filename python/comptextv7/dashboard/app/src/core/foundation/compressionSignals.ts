import type { JsonValue } from './shared';

export type CognitiveMode = 'habit' | 'monitor' | 'deliberation' | 'rollback_required';

export interface CompressionSignalInput {
  executionId: string;
  windowId: string;
  timestamp: string;
  profileId: string;
  compressionRatio: number;
  baselineCompressionRatio: number;
  sparseFrameRate: number;
  baselineSparseFrameRate: number;
  unseenSignatureRate: number;
  tokenEstimate?: number;
  baselineTokenEstimate?: number;
  replayConsistency?: number;
  baselineReplayConsistency?: number;
  metadata?: Record<string, JsonValue>;
}

export interface CompressionSignalProfile {
  profileId: string;
  medianCompressionRatio: number;
  medianSparseFrameRate: number;
  medianUnseenSignatureRate: number;
  medianTokenEstimate?: number;
  medianReplayConsistency?: number;
  sampleCount: number;
  updatedAt: string;
}

export interface CompressionSignalWeights {
  compressionRatioDrop: number;
  sparseFrameSpike: number;
  unseenSignatureRate: number;
  tokenCostSpike?: number;
  replayConsistencyDrop?: number;
}

export interface CompressionSignalThresholds {
  habitMax: number;
  monitorMax: number;
  deliberationMin: number;
  rollbackRequiredMin: number;
}

export interface CompressionSignalHysteresis {
  enterDeliberation: number;
  exitDeliberation: number;
}

export interface CompressionSignalDebounce {
  requiredWindows: number;
  ofLast: number;
}

export interface CompressionSignalWindow {
  input: CompressionSignalInput;
  compressionRatioDrop: number;
  sparseFrameSpike: number;
  unseenSignatureSignal: number;
  tokenCostSpike?: number;
  replayConsistencyDrop?: number;
  predictionError: number;
}

export type CompressionSignalReason =
  | 'compression_ratio_drop exceeded baseline'
  | 'sparse_frame_rate increased'
  | 'unseen_signature_rate elevated'
  | 'unseen_signature_rate remained elevated across debounce window'
  | 'token_cost increased'
  | 'replay_consistency dropped'
  | 'deliberation debounce pending'
  | 'deliberation debounce satisfied'
  | 'prediction_error below exit threshold'
  | 'prediction_error reached rollback threshold'
  | 'prediction_error within habit band'
  | 'prediction_error within monitor band';

export interface CompressionSignalResult {
  executionId: string;
  windowId: string;
  timestamp: string;
  profileId: string;
  mode: CognitiveMode;
  predictionError: number;
  triggered: boolean;
  window: CompressionSignalWindow;
  reasons: readonly CompressionSignalReason[];
}

export const defaultCompressionSignalWeights: CompressionSignalWeights = Object.freeze({
  compressionRatioDrop: 0.35,
  sparseFrameSpike: 0.35,
  unseenSignatureRate: 0.3,
});

export const defaultCompressionSignalThresholds: CompressionSignalThresholds = Object.freeze({
  habitMax: 0.3,
  monitorMax: 0.55,
  deliberationMin: 0.62,
  rollbackRequiredMin: 0.85,
});

export const defaultCompressionSignalHysteresis: CompressionSignalHysteresis = Object.freeze({
  enterDeliberation: 0.62,
  exitDeliberation: 0.42,
});

export const defaultCompressionSignalDebounce: CompressionSignalDebounce = Object.freeze({
  requiredWindows: 2,
  ofLast: 3,
});

function clamp01(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function roundSignal(value: number): number {
  return Math.round((clamp01(value) + Number.EPSILON) * 1000) / 1000;
}

export function calculateCompressionRatioDrop(compressionRatio: number, baselineCompressionRatio: number): number {
  if (!Number.isFinite(baselineCompressionRatio) || baselineCompressionRatio <= 0) {
    return 0;
  }
  return roundSignal((baselineCompressionRatio - compressionRatio) / baselineCompressionRatio);
}

export function calculateSparseFrameSpike(sparseFrameRate: number, baselineSparseFrameRate: number): number {
  if (!Number.isFinite(sparseFrameRate)) {
    return 0;
  }
  if (!Number.isFinite(baselineSparseFrameRate) || baselineSparseFrameRate <= 0) {
    return roundSignal(sparseFrameRate);
  }
  return roundSignal((sparseFrameRate - baselineSparseFrameRate) / baselineSparseFrameRate);
}

export function calculateUnseenSignatureSignal(unseenSignatureRate: number): number {
  return roundSignal(unseenSignatureRate);
}

export function calculateTokenCostSpike(tokenEstimate?: number, baselineTokenEstimate?: number): number {
  if (tokenEstimate === undefined || baselineTokenEstimate === undefined || !Number.isFinite(baselineTokenEstimate) || baselineTokenEstimate <= 0) {
    return 0;
  }
  return roundSignal((tokenEstimate - baselineTokenEstimate) / baselineTokenEstimate);
}

export function calculateReplayConsistencyDrop(replayConsistency?: number, baselineReplayConsistency?: number): number {
  if (replayConsistency === undefined || baselineReplayConsistency === undefined || !Number.isFinite(baselineReplayConsistency) || baselineReplayConsistency <= 0) {
    return 0;
  }
  return roundSignal((baselineReplayConsistency - replayConsistency) / baselineReplayConsistency);
}

export function calculatePredictionError(input: CompressionSignalInput, weights: CompressionSignalWeights = defaultCompressionSignalWeights): number {
  const compressionRatioDrop = calculateCompressionRatioDrop(input.compressionRatio, input.baselineCompressionRatio);
  const sparseFrameSpike = calculateSparseFrameSpike(input.sparseFrameRate, input.baselineSparseFrameRate);
  const unseenSignatureSignal = calculateUnseenSignatureSignal(input.unseenSignatureRate);
  const tokenCostSpike = calculateTokenCostSpike(input.tokenEstimate, input.baselineTokenEstimate);
  const replayConsistencyDrop = calculateReplayConsistencyDrop(input.replayConsistency, input.baselineReplayConsistency);

  return roundSignal(
    weights.compressionRatioDrop * compressionRatioDrop
      + weights.sparseFrameSpike * sparseFrameSpike
      + weights.unseenSignatureRate * unseenSignatureSignal
      + (weights.tokenCostSpike ?? 0) * tokenCostSpike
      + (weights.replayConsistencyDrop ?? 0) * replayConsistencyDrop,
  );
}

export function classifyCognitiveMode(predictionError: number, thresholds: CompressionSignalThresholds = defaultCompressionSignalThresholds): CognitiveMode {
  const score = clamp01(predictionError);
  if (score >= thresholds.rollbackRequiredMin) {
    return 'rollback_required';
  }
  if (score < thresholds.habitMax) {
    return 'habit';
  }
  if (score <= thresholds.monitorMax) {
    return 'monitor';
  }
  if (score >= thresholds.deliberationMin) {
    return 'deliberation';
  }
  return 'monitor';
}

function buildSignalWindow(input: CompressionSignalInput, weights: CompressionSignalWeights): CompressionSignalWindow {
  const tokenCostSpike = calculateTokenCostSpike(input.tokenEstimate, input.baselineTokenEstimate);
  const replayConsistencyDrop = calculateReplayConsistencyDrop(input.replayConsistency, input.baselineReplayConsistency);
  return Object.freeze({
    input: Object.freeze({ ...input, metadata: input.metadata === undefined ? undefined : Object.freeze({ ...input.metadata }) }),
    compressionRatioDrop: calculateCompressionRatioDrop(input.compressionRatio, input.baselineCompressionRatio),
    sparseFrameSpike: calculateSparseFrameSpike(input.sparseFrameRate, input.baselineSparseFrameRate),
    unseenSignatureSignal: calculateUnseenSignatureSignal(input.unseenSignatureRate),
    tokenCostSpike: input.tokenEstimate === undefined || input.baselineTokenEstimate === undefined ? undefined : tokenCostSpike,
    replayConsistencyDrop: input.replayConsistency === undefined || input.baselineReplayConsistency === undefined ? undefined : replayConsistencyDrop,
    predictionError: calculatePredictionError(input, weights),
  });
}

export function shouldEnterDeliberation(
  windows: readonly Pick<CompressionSignalWindow, 'predictionError'>[],
  hysteresis: CompressionSignalHysteresis = defaultCompressionSignalHysteresis,
  debounce: CompressionSignalDebounce = defaultCompressionSignalDebounce,
): boolean {
  const recent = windows.slice(-debounce.ofLast);
  return recent.filter((window) => window.predictionError >= hysteresis.enterDeliberation).length >= debounce.requiredWindows;
}

export function shouldExitDeliberation(
  currentPredictionError: number,
  hysteresis: CompressionSignalHysteresis = defaultCompressionSignalHysteresis,
): boolean {
  return clamp01(currentPredictionError) <= hysteresis.exitDeliberation;
}

function uniqueReasons(reasons: CompressionSignalReason[]): CompressionSignalReason[] {
  return Array.from(new Set(reasons));
}

function buildReasons(
  window: CompressionSignalWindow,
  mode: CognitiveMode,
  enteredDeliberation: boolean,
  exitedDeliberation: boolean,
  hysteresis: CompressionSignalHysteresis,
): CompressionSignalReason[] {
  const reasons: CompressionSignalReason[] = [];
  if (window.compressionRatioDrop > 0) {
    reasons.push('compression_ratio_drop exceeded baseline');
  }
  if (window.sparseFrameSpike > 0) {
    reasons.push('sparse_frame_rate increased');
  }
  if (window.unseenSignatureSignal > 0) {
    reasons.push(mode === 'deliberation' ? 'unseen_signature_rate remained elevated across debounce window' : 'unseen_signature_rate elevated');
  }
  if ((window.tokenCostSpike ?? 0) > 0) {
    reasons.push('token_cost increased');
  }
  if ((window.replayConsistencyDrop ?? 0) > 0) {
    reasons.push('replay_consistency dropped');
  }
  if (mode === 'rollback_required') {
    reasons.push('prediction_error reached rollback threshold');
  } else if (enteredDeliberation) {
    reasons.push('deliberation debounce satisfied');
  } else if (window.predictionError >= hysteresis.enterDeliberation) {
    reasons.push('deliberation debounce pending');
  } else if (exitedDeliberation) {
    reasons.push('prediction_error below exit threshold');
  } else if (mode === 'habit') {
    reasons.push('prediction_error within habit band');
  } else if (mode === 'monitor') {
    reasons.push('prediction_error within monitor band');
  }
  return uniqueReasons(reasons);
}

export interface CompressionSignalEngineOptions {
  weights?: CompressionSignalWeights;
  thresholds?: CompressionSignalThresholds;
  hysteresis?: CompressionSignalHysteresis;
  debounce?: CompressionSignalDebounce;
}

export class CompressionSignalEngine {
  private readonly weights: CompressionSignalWeights;
  private readonly thresholds: CompressionSignalThresholds;
  private readonly hysteresis: CompressionSignalHysteresis;
  private readonly debounce: CompressionSignalDebounce;

  constructor(options: CompressionSignalEngineOptions = {}) {
    this.weights = Object.freeze({ ...defaultCompressionSignalWeights, ...options.weights });
    this.thresholds = Object.freeze({ ...defaultCompressionSignalThresholds, ...options.thresholds });
    this.hysteresis = Object.freeze({ ...defaultCompressionSignalHysteresis, ...options.hysteresis });
    this.debounce = Object.freeze({ ...defaultCompressionSignalDebounce, ...options.debounce });
  }

  evaluateSignalWindow(input: CompressionSignalInput, priorWindows: readonly CompressionSignalWindow[] = [], priorMode: CognitiveMode = 'habit'): CompressionSignalResult {
    const window = buildSignalWindow(input, this.weights);
    const windows = [...priorWindows, window];
    const rollback = window.predictionError >= this.thresholds.rollbackRequiredMin;
    const enterDeliberation = !rollback && shouldEnterDeliberation(windows, this.hysteresis, this.debounce);
    const exitDeliberation = priorMode === 'deliberation' && shouldExitDeliberation(window.predictionError, this.hysteresis);

    let mode: CognitiveMode;
    if (rollback) {
      mode = 'rollback_required';
    } else if (priorMode === 'deliberation' && !exitDeliberation) {
      mode = 'deliberation';
    } else if (enterDeliberation) {
      mode = 'deliberation';
    } else if (window.predictionError < this.thresholds.habitMax) {
      mode = 'habit';
    } else {
      mode = 'monitor';
    }

    return Object.freeze({
      executionId: input.executionId,
      windowId: input.windowId,
      timestamp: input.timestamp,
      profileId: input.profileId,
      mode,
      predictionError: window.predictionError,
      triggered: mode === 'deliberation' || mode === 'rollback_required',
      window,
      reasons: Object.freeze(buildReasons(window, mode, enterDeliberation, exitDeliberation, this.hysteresis)),
    });
  }

  evaluateSignalSequence(inputs: readonly CompressionSignalInput[], initialMode: CognitiveMode = 'habit'): CompressionSignalResult[] {
    const windows: CompressionSignalWindow[] = [];
    let priorMode = initialMode;
    return inputs.map((input) => {
      const result = this.evaluateSignalWindow(input, windows, priorMode);
      windows.push(result.window);
      priorMode = result.mode;
      return result;
    });
  }
}

const defaultEngine = new CompressionSignalEngine();

export function evaluateSignalWindow(
  input: CompressionSignalInput,
  priorWindows: readonly CompressionSignalWindow[] = [],
  priorMode: CognitiveMode = 'habit',
): CompressionSignalResult {
  return defaultEngine.evaluateSignalWindow(input, priorWindows, priorMode);
}

export function evaluateSignalSequence(inputs: readonly CompressionSignalInput[], initialMode: CognitiveMode = 'habit'): CompressionSignalResult[] {
  return defaultEngine.evaluateSignalSequence(inputs, initialMode);
}
