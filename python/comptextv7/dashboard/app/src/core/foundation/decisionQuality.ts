export interface QualityRubric {
  weights: {
    validity: number;
    specificity: number;
    correctness: number;
    traceability: number;
    rollbackSafety: number;
    tokenEfficiency: number;
  };
  tokenBudget: number;
}

export interface QualityRubricInput {
  validityChecksPassed: number;
  validityChecksTotal: number;
  specificCriteriaMet: number;
  specificCriteriaTotal: number;
  correctnessChecksPassed: number;
  correctnessChecksTotal: number;
  linkedReplayStepIds: string[];
  linkedReferenceIds: string[];
  artifactRefs: string[];
  replaySnapshotIds: string[];
  tokenUsed: number;
}

export interface DecisionQualityMetrics {
  validity: number;
  specificity: number;
  correctness: number;
  traceability: number;
  rollbackSafety: number;
  tokenEfficiency: number;
}

export interface QualityEvalRun {
  overallScore: number;
  metrics: DecisionQualityMetrics;
  explanation: string;
  linkedReplayStepIds: string[];
  linkedReferenceIds: string[];
}

const defaultRubric: QualityRubric = Object.freeze({
  weights: Object.freeze({
    validity: 1,
    specificity: 1,
    correctness: 1,
    traceability: 1,
    rollbackSafety: 1,
    tokenEfficiency: 1,
  }),
  tokenBudget: 8000,
});

function ratio(passed: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return clamp01(passed / total);
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function unique(values: readonly string[]): string[] {
  return Array.from(new Set(values)).sort((left, right) => left.localeCompare(right));
}

function roundScore(value: number): number {
  return Math.round(value * 1000) / 1000;
}

export class DecisionQualityEngine {
  constructor(private readonly rubric: QualityRubric = defaultRubric) {}

  evaluate(input: QualityRubricInput): QualityEvalRun {
    const linkedReplayStepIds = unique(input.linkedReplayStepIds);
    const linkedReferenceIds = unique(input.linkedReferenceIds);
    const metrics: DecisionQualityMetrics = {
      validity: ratio(input.validityChecksPassed, input.validityChecksTotal),
      specificity: ratio(input.specificCriteriaMet, input.specificCriteriaTotal),
      correctness: ratio(input.correctnessChecksPassed, input.correctnessChecksTotal),
      traceability: clamp01((linkedReplayStepIds.length > 0 ? 0.5 : 0) + Math.min(0.5, linkedReferenceIds.length / 8)),
      rollbackSafety: clamp01((input.replaySnapshotIds.length > 0 ? 0.5 : 0) + Math.min(0.5, unique(input.artifactRefs).length / 4)),
      tokenEfficiency: input.tokenUsed <= 0 ? 1 : clamp01((this.rubric.tokenBudget - input.tokenUsed) / this.rubric.tokenBudget),
    };
    const weights = this.rubric.weights;
    const weightedTotal = Object.entries(metrics).reduce((sum, [key, value]) => sum + value * weights[key as keyof DecisionQualityMetrics], 0);
    const weightTotal = Object.values(weights).reduce((sum, value) => sum + value, 0);
    const overallScore = roundScore(weightTotal === 0 ? 0 : weightedTotal / weightTotal);
    return Object.freeze({
      overallScore,
      metrics: Object.freeze(Object.fromEntries(Object.entries(metrics).map(([key, value]) => [key, roundScore(value)])) as unknown as DecisionQualityMetrics),
      explanation: buildExplanation(overallScore, metrics, input, this.rubric.tokenBudget),
      linkedReplayStepIds,
      linkedReferenceIds,
    });
  }
}

function buildExplanation(overallScore: number, metrics: DecisionQualityMetrics, input: QualityRubricInput, budget: number): string {
  const traceability = metrics.traceability > 0 ? 'linked replay/reference evidence present' : 'no replay/reference evidence linked';
  const rollback = metrics.rollbackSafety > 0 ? 'rollback evidence includes snapshots or artifacts' : 'rollback evidence missing';
  const token = input.tokenUsed <= budget ? `${input.tokenUsed}/${budget} tokens used within budget` : `${input.tokenUsed}/${budget} tokens exceeded budget`;
  return `Deterministic quality score ${overallScore}: ${traceability}; ${rollback}; ${token}.`;
}

export const defaultQualityRubric = defaultRubric;
