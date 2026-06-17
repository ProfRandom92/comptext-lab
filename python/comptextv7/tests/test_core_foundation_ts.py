import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP = REPO_ROOT / "dashboard" / "app"
TSC = DASHBOARD_APP / "node_modules" / ".bin" / "tsc"


def run_foundation_script(tmp_path: Path, script: str):
    out_dir = tmp_path / "compiled"
    source_files = sorted((DASHBOARD_APP / "src" / "core" / "foundation").glob("*.ts"))
    subprocess.run(
        [
            str(TSC),
            "--target",
            "ES2022",
            "--module",
            "CommonJS",
            "--moduleResolution",
            "Node",
            "--rootDir",
            str(DASHBOARD_APP / "src"),
            "--outDir",
            str(out_dir),
            "--strict",
            "--skipLibCheck",
            *[str(path) for path in source_files],
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=out_dir,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_reference_dedup_budget_and_compact_prompt(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              SemanticReferenceRegistry,
              TokenBudgetManager,
              ContextManifestBuilder,
              CompactPromptBuilder,
            } = require('./core/foundation');
            const registry = new SemanticReferenceRegistry();
            const first = registry.register({
              uri: 'ctx://project/goal', summary: 'Short project goal summary.', tokenEstimate: 20,
              relevanceScore: 0.9, resolver: 'static', createdAt: '2026-05-15T00:00:00.000Z',
              metadata: { rawTokenEstimate: 220 },
            });
            const duplicate = registry.register({
              uri: 'ctx://project/goal', summary: 'Duplicate should not be inserted.', tokenEstimate: 30,
              relevanceScore: 0.1, resolver: 'static', createdAt: '2026-05-15T00:00:01.000Z',
            });
            const memory = registry.register({
              uri: 'mem://project/constraint', summary: 'Do not touch showcase assets.', tokenEstimate: 15,
              relevanceScore: 1, resolver: 'static', createdAt: '2026-05-15T00:00:02.000Z',
            });
            const artifact = registry.register({
              uri: 'artifact://large/raw', summary: 'Large artifact summary only.', tokenEstimate: 40,
              relevanceScore: 0.4, resolver: 'static', createdAt: '2026-05-15T00:00:03.000Z',
            });
            assert.equal(first.id, duplicate.id);
            assert.equal(registry.list().length, 3);
            const manifest = new ContextManifestBuilder(new TokenBudgetManager(35)).build('exec-1', [first, duplicate, memory, artifact], '2026-05-15T00:00:04.000Z');
            assert.deepEqual(manifest.selectedRefs.map((ref) => ref.id), [memory.id, first.id]);
            assert.deepEqual(manifest.omittedRefs.map((ref) => ref.id), [artifact.id]);
            assert.equal(manifest.totalTokenEstimate, 35);
            assert.equal(manifest.rawTokenAvoided, 200);
            const prompt = new CompactPromptBuilder().build(manifest);
            assert.match(prompt, /Short project goal summary/);
            assert.match(prompt, /Do not touch showcase assets/);
            assert.doesNotMatch(prompt, /Duplicate should not be inserted/);
            console.log(JSON.stringify({ selected: manifest.selectedRefs.length, omitted: manifest.omittedRefs.length, prompt }));
            """
        ),
    )
    assert result["selected"] == 2
    assert result["omitted"] == 1


def test_append_only_event_ordering_and_summary(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              InMemoryExecutionEventStore,
              appendExecutionEvent,
              getExecutionTimeline,
              summarizeExecutionEvents,
            } = require('./core/foundation');
            const store = new InMemoryExecutionEventStore();
            const base = {
              executionId: 'exec-2', agentId: 'agent-a', inputRefIds: [], outputRefIds: [],
              tokenIn: 0, tokenOut: 0, latencyMs: 0, status: 'succeeded', compactPayload: {},
            };
            appendExecutionEvent(store, { ...base, stepId: 'step-2', timestamp: '2026-05-15T00:00:02.000Z', eventType: 'tool.called', outputRefIds: ['tool://call/1'], tokenIn: 5, tokenOut: 7, latencyMs: 9 });
            appendExecutionEvent(store, { ...base, stepId: 'step-1', timestamp: '2026-05-15T00:00:01.000Z', eventType: 'execution.started', inputRefIds: ['ctx-1'], tokenIn: 3 });
            appendExecutionEvent(store, { ...base, stepId: 'step-3', timestamp: '2026-05-15T00:00:03.000Z', eventType: 'execution.completed', outputRefIds: ['artifact-1'], tokenOut: 11, latencyMs: 2 });
            const appendOrder = store.list('exec-2').map((event) => event.stepId);
            const timeline = getExecutionTimeline(store, 'exec-2');
            const summary = summarizeExecutionEvents(timeline, 'exec-2');
            assert.deepEqual(appendOrder, ['step-2', 'step-1', 'step-3']);
            assert.deepEqual(timeline.map((event) => event.stepId), ['step-1', 'step-2', 'step-3']);
            assert.equal(summary.totalTokenIn, 8);
            assert.equal(summary.totalTokenOut, 18);
            assert.equal(summary.totalLatencyMs, 11);
            assert.equal(summary.eventTypeCounts['tool.called'], 1);
            console.log(JSON.stringify(summary));
            """
        ),
    )
    assert result["stepIds"] == ["step-1", "step-2", "step-3"]
    assert result["status"] == "succeeded"


def test_replay_snapshot_branch_and_comparison(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const { createReplaySnapshot, branchFromStep, compareReplayRuns } = require('./core/foundation');
            const eventA = {
              executionId: 'exec-a', stepId: 'step-a', agentId: 'agent', timestamp: '2026-05-15T00:00:01.000Z',
              eventType: 'quality.evaluated', inputRefIds: ['ctx-a'], outputRefIds: ['out-a'], tokenIn: 10,
              tokenOut: 5, latencyMs: 1, status: 'succeeded', compactPayload: { qualityScore: 0.7, memoryRefIds: ['mem-a'], toolCallRefs: ['tool-a'], artifactRefs: ['artifact-a'] },
            };
            const eventB = {
              ...eventA, executionId: 'exec-b', stepId: 'step-b', outputRefIds: ['out-b'], tokenIn: 7,
              compactPayload: { qualityScore: 0.9, memoryRefIds: ['mem-a', 'mem-b'], toolCallRefs: ['tool-b'], artifactRefs: ['artifact-b'] },
            };
            const snapshotA = createReplaySnapshot(eventA);
            const snapshotB = createReplaySnapshot(eventB);
            const branch = branchFromStep(snapshotA, '2026-05-15T00:00:02.000Z', 'retry with compact context');
            const comparison = compareReplayRuns({ executionId: 'exec-a', snapshots: [snapshotA] }, { executionId: 'exec-b', snapshots: [snapshotB] });
            assert.equal(branch.fromStepId, 'step-a');
            assert.deepEqual(comparison.memoryInjection.added, ['mem-b']);
            assert.deepEqual(comparison.outputReferenceDiff.added, ['out-b']);
            assert.deepEqual(comparison.outputReferenceDiff.removed, ['out-a']);
            assert.equal(comparison.qualityScore.delta, 0.20000000000000007);
            console.log(JSON.stringify({ snapshotA, branch, comparison }));
            """
        ),
    )
    assert result["branch"]["baseSnapshotId"] == result["snapshotA"]["snapshotId"]
    assert result["comparison"]["tokenCost"]["delta"] == -3


def test_decision_quality_scoring(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const { DecisionQualityEngine } = require('./core/foundation');
            const engine = new DecisionQualityEngine({
              weights: { validity: 1, specificity: 1, correctness: 1, traceability: 1, rollbackSafety: 1, tokenEfficiency: 1 },
              tokenBudget: 100,
            });
            const evaluation = engine.evaluate({
              validityChecksPassed: 2, validityChecksTotal: 2,
              specificCriteriaMet: 1, specificCriteriaTotal: 2,
              correctnessChecksPassed: 3, correctnessChecksTotal: 4,
              linkedReplayStepIds: ['step-1', 'step-1'], linkedReferenceIds: ['ref-a', 'ref-b'],
              artifactRefs: ['artifact-a'], replaySnapshotIds: ['snapshot-a'], tokenUsed: 40,
            });
            assert.equal(evaluation.metrics.validity, 1);
            assert.equal(evaluation.metrics.specificity, 0.5);
            assert.equal(evaluation.metrics.correctness, 0.75);
            assert.equal(evaluation.metrics.traceability, 0.75);
            assert.equal(evaluation.metrics.rollbackSafety, 0.75);
            assert.equal(evaluation.metrics.tokenEfficiency, 0.6);
            assert.equal(evaluation.overallScore, 0.725);
            assert.deepEqual(evaluation.linkedReplayStepIds, ['step-1']);
            console.log(JSON.stringify(evaluation));
            """
        ),
    )
    assert result["overallScore"] == 0.725
