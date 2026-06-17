import type { ReactNode } from 'react';
import { Download, Search } from 'lucide-react';
import { navigation } from '../../lib/navigation';
import { api } from '../../lib/api';
import type { RouteId } from '../../types/domain';

export function Shell({ activeRoute, onNavigate, onOpenCommand, children }: { activeRoute: RouteId; onNavigate: (route: RouteId) => void; onOpenCommand: () => void; children: ReactNode }) {
  const active = navigation.find((item) => item.id === activeRoute) ?? navigation[0];
  return (
    <div className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand"><div className="brand-mark">CT</div><div><h1>CompText V7</h1><p>Replay validation console</p></div></div>
        <nav className="nav">
          {navigation.map((item) => <button key={item.id} onClick={() => onNavigate(item.id)} aria-current={item.id === activeRoute ? 'page' : undefined}><item.icon size={20} /><span><strong>{item.label}</strong><span>{item.description}</span></span></button>)}
        </nav>
        <div className="sidebar-footer">Review surface: docs, CI artifacts, typed payloads, and validation boundaries.</div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="page-title"><h2>{active.label}</h2><p>{active.description}</p></div>
          <div className="toolbar">
            <button className="search-button" onClick={onOpenCommand}><span><Search size={16} /> Search or command</span><span className="kbd">⌘K</span></button>
            <a className="button" href={api.exportCsvUrl}><Download size={16} /> CSV</a>
            <a className="button" href={api.exportJsonUrl}>JSON</a>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
