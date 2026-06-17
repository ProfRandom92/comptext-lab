export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type SystemStatus = 'nominal' | 'degraded' | 'critical' | 'unknown';

export interface AuditSummary {
  forensic_failures: number;
  replay_determinism: boolean;
  tokenizer_version: string;
  tokenizer_drift_fingerprint: string;
  active_incidents: number;
  degraded_services: number;
  p95_compression_ms: number;
  fleet_token_savings: number;
}

export interface BenchmarkResult {
  name: string;
  lines: number;
  input_bytes: number;
  payload_bytes: number;
  original_tokens: number;
  compressed_tokens: number;
  reduction_percent: number;
  compression_ratio: number;
  median_ms: number;
  lines_per_second: number;
  peak_kib: number;
  distinct_families: number;
  top_family_coverage: number;
  honest_expectation: string;
}

export interface ForensicFinding {
  id: string;
  severity: Severity;
  category: 'semantic' | 'anomaly' | 'anchor' | 'safety' | 'replay';
  title: string;
  evidence: string;
  owner: string;
  opened_at: string;
}

export interface ForensicDataset {
  dataset: string;
  semantic_retention: number;
  anomaly_survivability: number;
  anchor_retention: number;
  safety_critical_retention: number;
  passed: boolean;
  compressed_sha256: string;
  findings: ForensicFinding[];
}

export interface ReplaySummary {
  stable: boolean;
  passes: number;
  mismatches: number;
  corpus_size: number;
  last_run_at: string;
}

export interface DriftPoint {
  dataset: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  timestamp: string;
}

export interface OpsIncident {
  id: string;
  title: string;
  service: string;
  severity: Severity;
  status: 'triage' | 'mitigating' | 'watching' | 'resolved';
  assignee: string;
  region: string;
  started_at: string;
  updated_at: string;
  error_budget_burn: number;
  impacted_assets: number;
}

export interface ServiceHealth {
  id: string;
  name: string;
  domain: 'compression' | 'validation' | 'replay' | 'telemetry' | 'gateway';
  status: SystemStatus;
  slo: number;
  latency_ms: number;
  throughput_lps: number;
  queue_depth: number;
  owner: string;
  dependencies: string[];
}


export type ReleaseHealthStatus = 'green' | 'yellow' | 'red' | 'unknown' | string;

export interface ReleaseHealthCheck {
  description?: string;
  key?: string;
  path?: string;
  present?: boolean;
  required?: boolean;
  size_bytes?: number;
  status?: string;
}

export interface ReleaseHealthMissingArtifacts {
  optional_cross_repo?: string[];
  required_local?: string[];
  [key: string]: string[] | undefined;
}

export interface ReleaseHealthSummary {
  overall_status?: ReleaseHealthStatus;
  checks?: Record<string, ReleaseHealthCheck>;
  required_artifacts_present?: string[];
  missing_artifacts?: ReleaseHealthMissingArtifacts;
  next_recommended_actions?: string[];
  safety_notes?: string[];
  generated_at?: string;
  synthetic?: boolean;
  summary_type?: string;
}

export interface DashboardPayload {
  audit_summary: AuditSummary;
  benchmarks: BenchmarkResult[];
  forensic: ForensicDataset[];
  replay: ReplaySummary;
  drift_severity_timeline: DriftPoint[];
  incidents: OpsIncident[];
  services: ServiceHealth[];
}

export type RouteId = 'overview' | 'forensics' | 'benchmarks' | 'replay' | 'incidents' | 'release-health';
