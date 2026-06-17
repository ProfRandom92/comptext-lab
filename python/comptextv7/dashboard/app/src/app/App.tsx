import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CommandPalette } from '../components/command/CommandPalette';
import { Shell } from '../components/layout/Shell';
import { ErrorState, LoadingState } from '../components/states/AsyncStates';
import { api } from '../lib/api';
import { BenchmarksPage } from '../features/benchmarks/BenchmarksPage';
import { ForensicsPage } from '../features/forensics/ForensicsPage';
import { IncidentsPage } from '../features/incidents/IncidentsPage';
import { OverviewPage } from '../features/overview/OverviewPage';
import { ReleaseHealthPage } from '../features/release-health/ReleaseHealthPage';
import { ReplayPage } from '../features/replay/ReplayPage';
import type { RouteId } from '../types/domain';

const routes: RouteId[] = ['overview', 'release-health', 'forensics', 'benchmarks', 'replay', 'incidents'];

function routeFromHash(): RouteId {
  const route = window.location.hash.replace('#/', '') as RouteId;
  return routes.includes(route) ? route : 'overview';
}

export function App() {
  const [route, setRoute] = useState<RouteId>(routeFromHash);
  const [commandOpen, setCommandOpen] = useState(false);
  const dashboard = useQuery({ queryKey: ['dashboard'], queryFn: ({ signal }) => api.dashboard(signal) });
  const releaseHealth = useQuery({ queryKey: ['release-health'], queryFn: ({ signal }) => api.releaseHealth(signal) });

  useEffect(() => {
    const onHash = () => setRoute(routeFromHash());
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setCommandOpen(true); }
    };
    window.addEventListener('hashchange', onHash);
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('hashchange', onHash); window.removeEventListener('keydown', onKey); };
  }, []);

  const navigate = (next: RouteId) => {
    window.location.hash = `/${next}`;
    setRoute(next);
  };

  let content = <LoadingState />;
  if (route === 'release-health') {
    content = <ReleaseHealthPage state={releaseHealth.data} isLoading={releaseHealth.isLoading} />;
  } else if (dashboard.isError) {
    content = <ErrorState message={dashboard.error.message} onRetry={() => void dashboard.refetch()} />;
  } else if (dashboard.data) {
    content = route === 'overview' ? <OverviewPage payload={dashboard.data} releaseHealth={releaseHealth.data} />
      : route === 'forensics' ? <ForensicsPage payload={dashboard.data} />
      : route === 'benchmarks' ? <BenchmarksPage payload={dashboard.data} />
      : route === 'replay' ? <ReplayPage payload={dashboard.data} />
      : <IncidentsPage payload={dashboard.data} />;
  }

  return <><Shell activeRoute={route} onNavigate={navigate} onOpenCommand={() => setCommandOpen(true)}>{content}</Shell><CommandPalette open={commandOpen} payload={dashboard.data} onClose={() => setCommandOpen(false)} onNavigate={navigate} /></>;
}
