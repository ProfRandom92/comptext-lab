import type { DashboardPayload } from '../types/domain';

export const fallbackPayload: DashboardPayload = {
  audit_summary: {
    forensic_failures: 0,
    replay_determinism: true,
    tokenizer_version: 'offline-fallback',
    tokenizer_drift_fingerprint: 'local-preview',
    active_incidents: 2,
    degraded_services: 1,
    p95_compression_ms: 640,
    fleet_token_savings: 98.4,
  },
  benchmarks: [
    { name: 'repetitive_xentry_2k', lines: 2000, input_bytes: 345326, payload_bytes: 998, original_tokens: 33998, compressed_tokens: 139, reduction_percent: 99.59, compression_ratio: 346.0, median_ms: 1070.06, lines_per_second: 1869, peak_kib: 4899.7, distinct_families: 6, top_family_coverage: 100, honest_expectation: 'Repeated diagnostic families compress extremely well.' },
    { name: 'mixed_obd_workshop_1_5k', lines: 1500, input_bytes: 142738, payload_bytes: 1281, original_tokens: 13804, compressed_tokens: 155, reduction_percent: 98.88, compression_ratio: 111.4, median_ms: 555.42, lines_per_second: 2701, peak_kib: 2379.4, distinct_families: 10, top_family_coverage: 100, honest_expectation: 'Realistic middle case with noisy but structured measurements.' },
    { name: 'high_entropy_json_750', lines: 750, input_bytes: 179617, payload_bytes: 2509, original_tokens: 21000, compressed_tokens: 113, reduction_percent: 99.46, compression_ratio: 71.6, median_ms: 501.4, lines_per_second: 1496, peak_kib: 1684.6, distinct_families: 750, top_family_coverage: 1.6, honest_expectation: 'Low coverage is a quality warning for high entropy payloads.' },
  ],
  forensic: [
    { dataset: 'can_bus_reference', semantic_retention: 0.997, anomaly_survivability: 1, anchor_retention: 1, safety_critical_retention: 1, passed: true, compressed_sha256: 'a61f-preview', findings: [] },
    { dataset: 'sparse_alarm_reference', semantic_retention: 0.991, anomaly_survivability: 1, anchor_retention: 0.998, safety_critical_retention: 1, passed: true, compressed_sha256: 'b28e-preview', findings: [] },
  ],
  replay: { stable: true, passes: 2, mismatches: 0, corpus_size: 4, last_run_at: new Date().toISOString() },
  drift_severity_timeline: [
    { dataset: 'can_bus_reference', critical: 0, high: 0, medium: 1, low: 2, timestamp: new Date().toISOString() },
    { dataset: 'sparse_alarm_reference', critical: 0, high: 1, medium: 1, low: 1, timestamp: new Date().toISOString() },
  ],
  incidents: [
    { id: 'INC-2407', title: 'Replay backlog exceeding replay lane SLO', service: 'Replay Orchestrator', severity: 'HIGH', status: 'mitigating', assignee: 'SRE / Validation', region: 'eu-central-1', started_at: new Date(Date.now() - 1000 * 60 * 41).toISOString(), updated_at: new Date().toISOString(), error_budget_burn: 3.2, impacted_assets: 14 },
    { id: 'INC-2408', title: 'Tokenizer drift canary in watch mode', service: 'Token Telemetry', severity: 'MEDIUM', status: 'watching', assignee: 'ML-Ops', region: 'us-east-2', started_at: new Date(Date.now() - 1000 * 60 * 92).toISOString(), updated_at: new Date().toISOString(), error_budget_burn: 1.1, impacted_assets: 3 },
  ],
  services: [
    { id: 'svc-compress', name: 'KVTC Compression Gateway', domain: 'compression', status: 'nominal', slo: 99.95, latency_ms: 84, throughput_lps: 2690, queue_depth: 12, owner: 'Platform Core', dependencies: ['token-telemetry', 'frame-store'] },
    { id: 'svc-replay', name: 'Replay Orchestrator', domain: 'replay', status: 'degraded', slo: 99.7, latency_ms: 640, throughput_lps: 418, queue_depth: 128, owner: 'Validation SRE', dependencies: ['golden-corpus', 'artifact-cache'] },
    { id: 'svc-forensic', name: 'Forensic Audit Workers', domain: 'validation', status: 'nominal', slo: 99.9, latency_ms: 180, throughput_lps: 72, queue_depth: 7, owner: 'Safety Assurance', dependencies: ['frame-store'] },
  ],
};
