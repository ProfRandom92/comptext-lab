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

def test_reference_index_deduplication(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent("""
        const { buildReferenceIndex } = require('./core/foundation/index');
        const entries = [
          { id: '1', uri: 'ctx://a', type: 'ctx', summary: 'a', tokenEstimate: 10, relevanceScore: 1, hash: 'hash1', resolver: 'r', createdAt: '2026-01-01T00:00:00.000Z' },
          { id: '1', uri: 'ctx://b', type: 'ctx', summary: 'b', tokenEstimate: 10, relevanceScore: 1, hash: 'hash2', resolver: 'r', createdAt: '2026-01-02T00:00:00.000Z' },
          { id: '2', uri: 'ctx://a', type: 'ctx', summary: 'c', tokenEstimate: 10, relevanceScore: 1, hash: 'hash3', resolver: 'r', createdAt: '2026-01-03T00:00:00.000Z' },
          { id: '3', uri: 'ctx://c', type: 'ctx', summary: 'd', tokenEstimate: 10, relevanceScore: 1, hash: 'hash1', resolver: 'r', createdAt: '2026-01-04T00:00:00.000Z' },
        ];
        const index = buildReferenceIndex(entries);
        console.log(JSON.stringify(index.entries.map(e => e.id)));
        """)
    )
    assert len(result) == 1
    assert result[0] == '1'

def test_reference_uri_validation(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent("""
        const { validateReferenceUri } = require('./core/foundation/index');
        const tests = [
          validateReferenceUri('ctx://good'),
          validateReferenceUri('mem://good'),
          validateReferenceUri('replay://good'),
          validateReferenceUri('artifact://good'),
          validateReferenceUri('tool://good'),
          validateReferenceUri('file://src/main.ts'),
          validateReferenceUri('file://dashboard/app/src/core/foundation/index.ts'),
          validateReferenceUri('run://good'),
          validateReferenceUri('http://bad'),
          validateReferenceUri('file:///Users/bad'),
          validateReferenceUri('file://C:/bad'),
          validateReferenceUri('file://\\\\\\\\server\\\\share'),
          validateReferenceUri('file://localhost/bad'),
          validateReferenceUri('file://127.0.0.1/bad'),
          validateReferenceUri('file://../bad'),
          validateReferenceUri('file://src/../bad'),
          validateReferenceUri('file://%2e%2e/bad'),
          validateReferenceUri('file://'),
        ];
        console.log(JSON.stringify(tests.map(t => t.valid)));
        """)
    )
    assert all(result[:8])
    assert not any(result[8:])

def test_payload_normalization(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent("""
        const { normalizeVolatilePayload } = require('./core/foundation/index');
        const payload = {
          traceId: 'abc',
          requestId: '123',
          timestamp: '2026-01-01',
          durationMs: 42,
          serverUptime: 9999,
          documentId: 'doc-1',
          userId: 'user-2',
          nested: {
            spanId: 'span-x',
            recordId: 'rec-1'
          }
        };
        const norm = normalizeVolatilePayload(payload, 1);
        console.log(JSON.stringify(norm));
        """)
    )
    assert result['traceId'] == '[RUNTIME_ID_STRIPPED]'
    assert result['requestId'] == '[RUNTIME_ID_STRIPPED]'
    assert result['timestamp'] == '[TIMESTAMP_STRIPPED]'
    assert result['durationMs'] == '[DURATION_STRIPPED]'
    assert result['serverUptime'] == '[UPTIME_STRIPPED]'
    assert result['documentId'] == 'doc-1'
    assert result['userId'] == 'user-2'
    assert result['nested']['spanId'] == '[RUNTIME_ID_STRIPPED]'
    assert result['nested']['recordId'] == 'rec-1'

def test_event_fingerprints(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent("""
        const { generateReplayArtifactEventFingerprint } = require('./core/foundation/index');
        const event = {
          executionId: 'exec-1',
          stepId: 'step-1',
          agentId: 'a',
          timestamp: '2026-01-01T00:00:00.000Z',
          eventType: 'context.selected',
          inputRefIds: ['ref-b', 'ref-a'],
          outputRefIds: [],
          tokenIn: 10,
          tokenOut: 0,
          latencyMs: 10,
          status: 'succeeded',
          compactPayload: { traceId: '123', docId: 'doc-1' }
        };
        const fp = generateReplayArtifactEventFingerprint(event, { normalizationVersion: 1 });
        console.log(JSON.stringify(fp));
        """)
    )
    assert result['executionId'] == 'exec-1'
    assert result['stepId'] == 'step-1'
    assert result['normalizationVersion'] == 1
    assert result['inputRefIds'] == ['ref-a', 'ref-b']

def test_compression_mapping(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent("""
        const { mapCompressionSignalsToStepIds } = require('./core/foundation/index');
        const events = [
          { executionId: 'exec-1', stepId: 'step-1', timestamp: '2026-01-01T00:00:01Z', eventType: 'context.selected', status: 'succeeded' },
          { executionId: 'exec-1', stepId: 'step-2', timestamp: '2026-01-01T00:00:02Z', eventType: 'tool.called', status: 'succeeded' }, // In gap
          { executionId: 'exec-1', stepId: 'step-3', timestamp: '2026-01-01T00:00:03Z', eventType: 'tool.called', status: 'succeeded' },
          { executionId: 'exec-1', stepId: 'step-4', timestamp: '2026-01-01T00:00:04Z', eventType: 'execution.failed', status: 'failed' },
        ];
        const signals = [
          { windowId: 'sig-1', timestamp: '2026-01-01T00:00:01Z', window: { input: {} } },
          { windowId: 'sig-2', timestamp: '2026-01-01T00:00:03Z', window: { input: { metadata: { startTimestamp: '2026-01-01T00:00:03Z' } } } }
        ];
        const mapping = mapCompressionSignalsToStepIds(signals, events);
        console.log(JSON.stringify(mapping));
        """)
    )
    assert len(result) == 2
    assert result[0]['windowId'] == 'sig-1'
    assert result[0]['associatedStepIds'] == ['step-1']
    assert result[1]['windowId'] == 'sig-2'
    assert result[1]['associatedStepIds'] == ['step-3']
    # step-2 is in the gap, step-4 is a trailing failure
    assert result[1]['unmappedStepIds'] == ['step-2', 'step-4']
    assert result[1]['unmappedReason'] == '[UNMAPPED_EXECUTION_HALT]'

def test_compression_mapping_no_signals(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent("""
        const { mapCompressionSignalsToStepIds } = require('./core/foundation/index');
        const events = [
          { executionId: 'exec-1', stepId: 'step-1', timestamp: '2026-01-01T00:00:01Z', eventType: 'context.selected', status: 'succeeded' },
          { executionId: 'exec-1', stepId: 'step-2', timestamp: '2026-01-01T00:00:02Z', eventType: 'execution.failed', status: 'failed' },
        ];
        const signals = [];
        const mapping = mapCompressionSignalsToStepIds(signals, events);
        console.log(JSON.stringify(mapping));
        """)
    )
    assert len(result) == 1
    assert result[0]['windowId'] == 'synthetic-unmapped-window'
    assert result[0]['associatedStepIds'] == []
    assert result[0]['unmappedStepIds'] == ['step-1', 'step-2']
    assert result[0]['unmappedReason'] == '[UNMAPPED_EXECUTION_HALT]'
