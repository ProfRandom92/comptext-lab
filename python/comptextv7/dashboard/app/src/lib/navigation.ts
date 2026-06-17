import { Activity, AlertTriangle, BarChart3, GitCompareArrows, HeartPulse, ShieldCheck } from 'lucide-react';
import type { RouteId } from '../types/domain';

export const navigation = [
  { id: 'overview', label: 'Overview', description: 'Replay validation review experience', icon: Activity },
  { id: 'release-health', label: 'Release Health', description: 'Readiness gates and promotion evidence', icon: HeartPulse },
  { id: 'forensics', label: 'Forensics', description: 'Safety and retention gates', icon: ShieldCheck },
  { id: 'benchmarks', label: 'Benchmarks', description: 'Compression and throughput lanes', icon: BarChart3 },
  { id: 'replay', label: 'Replay', description: 'Determinism and drift controls', icon: GitCompareArrows },
  { id: 'incidents', label: 'Incidents', description: 'Active SRE work queue', icon: AlertTriangle },
] satisfies Array<{ id: RouteId; label: string; description: string; icon: typeof Activity }>;
