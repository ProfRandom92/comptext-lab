import { fallbackPayload } from '../mocks/fallbackPayload';
import { fetchReleaseHealthSummary } from './releaseHealth';
import type { DashboardPayload } from '../types/domain';

const API_BASE = import.meta.env.VITE_COMP_TEXT_API_BASE ?? '';

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal, headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export async function fetchDashboard(signal?: AbortSignal): Promise<DashboardPayload> {
  try {
    return await request<DashboardPayload>('/api/dashboard', signal);
  } catch (error) {
    if (import.meta.env.DEV) return fallbackPayload;
    throw error;
  }
}

export const api = {
  dashboard: fetchDashboard,
  releaseHealth: (signal?: AbortSignal) => fetchReleaseHealthSummary(API_BASE, signal),
  exportJsonUrl: `${API_BASE}/export.json`,
  exportCsvUrl: `${API_BASE}/export.csv`,
};
