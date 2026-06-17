import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP = REPO_ROOT / "dashboard" / "app"
TSC = DASHBOARD_APP / "node_modules" / ".bin" / "tsc"


def run_compression_script(tmp_path: Path, script: str):
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


def test_signal_calculations_and_prediction_error(tmp_path):
    result = run_compression_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              calculateCompressionRatioDrop,
              calculateSparseFrameSpike,
              calculateUnseenSignatureSignal,
              calculatePredictionError,
            } = require('./core/foundation');
            assert.equal(calculateCompressionRatioDrop(0.6, 0.8), 0.25);
            assert.equal(calculateCompressionRatioDrop(0.9, 0.8), 0);
            assert.equal(calculateSparseFrameSpike(0.3, 0.2), 0.5);
            assert.equal(calculateSparseFrameSpike(0.1, 0.2), 0);
            assert.equal(calculateUnseenSignatureSignal(1.5), 1);
            assert.equal(calculateUnseenSignatureSignal(-0.2), 0);
            const input = {
              executionId: 'exec-1', windowId: 'w-1', timestamp: '2026-05-15T00:00:00.000Z', profileId: 'p-1',
              compressionRatio: 0.6, baselineCompressionRatio: 0.8,
              sparseFrameRate: 0.3, baselineSparseFrameRate: 0.2,
              unseenSignatureRate: 0.4,
              tokenEstimate: 300, baselineTokenEstimate: 100,
              replayConsistency: 0.5, baselineReplayConsistency: 1,
            };
            assert.equal(calculatePredictionError(input), 0.383);
            console.log(JSON.stringify({ predictionError: calculatePredictionError(input) }));
            """
        ),
    )
    assert result["predictionError"] == 0.383


def test_classification_and_debounce_rules(tmp_path):
    result = run_compression_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const { CompressionSignalEngine, classifyCognitiveMode } = require('./core/foundation');
            assert.equal(classifyCognitiveMode(0.2), 'habit');
            assert.equal(classifyCognitiveMode(0.4), 'monitor');
            assert.equal(classifyCognitiveMode(0.7), 'deliberation');
            assert.equal(classifyCognitiveMode(0.9), 'rollback_required');
            const makeInput = (windowId, sparseFrameRate, unseenSignatureRate, compressionRatio = 0.8) => ({
              executionId: 'exec-2', windowId, timestamp: `2026-05-15T00:00:0${windowId}.000Z`, profileId: 'p-1',
              compressionRatio, baselineCompressionRatio: 0.8,
              sparseFrameRate, baselineSparseFrameRate: 0.1,
              unseenSignatureRate,
            });
            const engine = new CompressionSignalEngine();
            const sequence = engine.evaluateSignalSequence([
              makeInput(1, 0.1, 0.01),
              makeInput(2, 0.26, 0.7, 0.42),
              makeInput(3, 0.1, 0.05),
              makeInput(4, 0.25, 0.7, 0.44),
            ]);
            assert.deepEqual(sequence.map((result) => result.mode), ['habit', 'monitor', 'habit', 'deliberation']);
            assert.equal(sequence[1].triggered, false);
            assert.equal(sequence[3].triggered, true);
            assert(sequence[3].reasons.includes('deliberation debounce satisfied'));
            console.log(JSON.stringify(sequence.map((result) => ({ mode: result.mode, error: result.predictionError, reasons: result.reasons }))));
            """
        ),
    )
    assert [entry["mode"] for entry in result] == ["habit", "monitor", "habit", "deliberation"]


def test_rollback_and_hysteresis_exit(tmp_path):
    result = run_compression_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const { CompressionSignalEngine, shouldExitDeliberation } = require('./core/foundation');
            const engine = new CompressionSignalEngine();
            const base = { executionId: 'exec-3', profileId: 'p-1', baselineCompressionRatio: 0.8, baselineSparseFrameRate: 0.1 };
            const rollback = engine.evaluateSignalWindow({
              ...base, windowId: 'rollback', timestamp: '2026-05-15T00:00:01.000Z',
              compressionRatio: 0.08, sparseFrameRate: 0.31, unseenSignatureRate: 0.95,
            });
            const stayDeliberation = engine.evaluateSignalWindow({
              ...base, windowId: 'stay', timestamp: '2026-05-15T00:00:02.000Z',
              compressionRatio: 0.8, sparseFrameRate: 0.22, unseenSignatureRate: 0.25,
            }, [], 'deliberation');
            const exitDeliberation = engine.evaluateSignalWindow({
              ...base, windowId: 'exit', timestamp: '2026-05-15T00:00:03.000Z',
              compressionRatio: 0.8, sparseFrameRate: 0.1, unseenSignatureRate: 0.01,
            }, [], 'deliberation');
            assert.equal(rollback.mode, 'rollback_required');
            assert.equal(rollback.triggered, true);
            assert(rollback.reasons.includes('prediction_error reached rollback threshold'));
            assert.equal(shouldExitDeliberation(0.42), true);
            assert.equal(shouldExitDeliberation(0.43), false);
            assert.equal(stayDeliberation.mode, 'deliberation');
            assert.equal(exitDeliberation.mode, 'habit');
            console.log(JSON.stringify({ rollback, stayDeliberation, exitDeliberation }));
            """
        ),
    )
    assert result["rollback"]["mode"] == "rollback_required"
    assert result["exitDeliberation"]["mode"] == "habit"


def test_deterministic_reasons_and_sample_data_validity(tmp_path):
    result = run_compression_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const { CompressionSignalEngine } = require('./core/foundation');
            const { coreFoundationSample } = require('./core/foundation/sampleData');
            const input = {
              executionId: 'exec-4', windowId: 'w-1', timestamp: '2026-05-15T00:00:01.000Z', profileId: 'p-1',
              compressionRatio: 0.42, baselineCompressionRatio: 0.8,
              sparseFrameRate: 0.26, baselineSparseFrameRate: 0.1,
              unseenSignatureRate: 0.72,
            };
            const engine = new CompressionSignalEngine();
            const first = engine.evaluateSignalSequence([input, { ...input, windowId: 'w-2', timestamp: '2026-05-15T00:00:02.000Z' }]);
            const second = engine.evaluateSignalSequence([input, { ...input, windowId: 'w-2', timestamp: '2026-05-15T00:00:02.000Z' }]);
            assert.deepEqual(first.map((result) => result.reasons), second.map((result) => result.reasons));
            assert.deepEqual(first.map((result) => result.mode), ['monitor', 'deliberation']);
            assert.equal(coreFoundationSample.compressionSignalWindows.length, 5);
            assert.deepEqual(
              coreFoundationSample.compressionSignalResults.map((result) => result.mode),
              ['habit', 'monitor', 'monitor', 'deliberation', 'rollback_required'],
            );
            console.log(JSON.stringify({ reasons: first[1].reasons, sampleModes: coreFoundationSample.compressionSignalResults.map((result) => result.mode) }));
            """
        ),
    )
    assert result["sampleModes"] == ["habit", "monitor", "monitor", "deliberation", "rollback_required"]
    assert result["reasons"] == [
        "compression_ratio_drop exceeded baseline",
        "sparse_frame_rate increased",
        "unseen_signature_rate remained elevated across debounce window",
        "deliberation debounce satisfied",
    ]
