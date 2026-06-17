import { releaseHealthSummaryFallback } from '../mocks/releaseHealthSummary';
import type { ReleaseHealthCheck, ReleaseHealthSummary } from '../types/domain';

export const RELEASE_HEALTH_SUMMARY_PATH = 'docs/reports/dashboard-health-summary.json';

export interface ReleaseHealthState {
  summary: ReleaseHealthSummary;
  unavailable: boolean;
  message?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function normalizeCheck(value: unknown, key: string): ReleaseHealthCheck {
  if (!isRecord(value)) return { key, status: 'unknown', present: false };
  return {
    description: typeof value.description === 'string' ? value.description : undefined,
    key: typeof value.key === 'string' ? value.key : key,
    path: typeof value.path === 'string' ? value.path : undefined,
    present: typeof value.present === 'boolean' ? value.present : undefined,
    required: typeof value.required === 'boolean' ? value.required : undefined,
    size_bytes: typeof value.size_bytes === 'number' ? value.size_bytes : undefined,
    status: typeof value.status === 'string' ? value.status : undefined,
  };
}

export function normalizeReleaseHealthSummary(value: unknown): ReleaseHealthSummary | null {
  if (!isRecord(value)) return null;
  const checks = isRecord(value.checks)
    ? Object.fromEntries(Object.entries(value.checks).map(([key, check]) => [key, normalizeCheck(check, key)]))
    : undefined;
  const missing = isRecord(value.missing_artifacts)
    ? Object.fromEntries(Object.entries(value.missing_artifacts).map(([key, artifacts]) => [key, stringArray(artifacts)]))
    : undefined;

  return {
    overall_status: typeof value.overall_status === 'string' ? value.overall_status : 'unknown',
    checks,
    required_artifacts_present: stringArray(value.required_artifacts_present),
    missing_artifacts: missing,
    next_recommended_actions: stringArray(value.next_recommended_actions),
    safety_notes: stringArray(value.safety_notes),
    generated_at: typeof value.generated_at === 'string' ? value.generated_at : undefined,
    synthetic: typeof value.synthetic === 'boolean' ? value.synthetic : undefined,
    summary_type: typeof value.summary_type === 'string' ? value.summary_type : undefined,
  };
}

function releaseHealthUrl(apiBase: string) {
  return `${apiBase.replace(/\/$/, '')}/dashboard-health-summary.json`;
}

async function fetchSummary(path: string, signal?: AbortSignal): Promise<ReleaseHealthSummary> {
  const response = await fetch(path, { signal, headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const summary = normalizeReleaseHealthSummary(await response.json());
  if (!summary) throw new Error('Invalid release health summary payload');
  return summary;
}

export async function fetchReleaseHealthSummary(apiBase = '', signal?: AbortSignal): Promise<ReleaseHealthState> {
  try {
    return { summary: await fetchSummary(releaseHealthUrl(apiBase), signal), unavailable: false };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown summary load error';
    return {
      summary: releaseHealthSummaryFallback,
      unavailable: true,
      message: `Health summary unavailable. Expected ${RELEASE_HEALTH_SUMMARY_PATH}. ${message}`,
    };
  }
}
