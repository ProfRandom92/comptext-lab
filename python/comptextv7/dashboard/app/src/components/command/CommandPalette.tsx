import { useEffect, useMemo, useState } from 'react';
import { navigation } from '../../lib/navigation';
import type { DashboardPayload, RouteId } from '../../types/domain';

interface Command { id: string; label: string; hint: string; route: RouteId }

export function CommandPalette({ open, payload, onClose, onNavigate }: { open: boolean; payload?: DashboardPayload; onClose: () => void; onNavigate: (route: RouteId) => void }) {
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const commands = useMemo<Command[]>(() => [
    ...navigation.map((item) => ({ id: item.id, label: `Open ${item.label}`, hint: item.description, route: item.id })),
    { id: 'release-health-summary', label: 'Inspect release health summary', hint: 'Readiness gates, missing artifacts, next actions, and safety notes', route: 'release-health' },
    { id: 'promotion-checklist', label: 'Review cross-repo promotion gate', hint: 'Experiment-to-runtime checklist and go/no-go signals', route: 'release-health' },
    ...(payload?.incidents ?? []).map((incident) => ({ id: incident.id, label: `${incident.id}: ${incident.title}`, hint: `${incident.service} · ${incident.assignee}`, route: 'incidents' as RouteId })),
    ...(payload?.forensic ?? []).map((dataset) => ({ id: dataset.dataset, label: `Inspect ${dataset.dataset}`, hint: dataset.passed ? 'Passing forensic gate' : 'Failing forensic gate', route: 'forensics' as RouteId })),
  ], [payload]);
  const filtered = commands.filter((command) => `${command.label} ${command.hint}`.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'ArrowDown') { event.preventDefault(); setActiveIndex((value) => Math.min(value + 1, filtered.length - 1)); }
      if (event.key === 'ArrowUp') { event.preventDefault(); setActiveIndex((value) => Math.max(value - 1, 0)); }
      if (event.key === 'Enter' && filtered[activeIndex]) { onNavigate(filtered[activeIndex].route); onClose(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [activeIndex, filtered, onClose, onNavigate, open]);

  useEffect(() => { if (open) { setQuery(''); setActiveIndex(0); } }, [open]);
  if (!open) return null;
  return (
    <div className="command-overlay" role="presentation" onMouseDown={onClose}>
      <section className="command" role="dialog" aria-modal="true" aria-label="Command palette" onMouseDown={(event) => event.stopPropagation()}>
        <input autoFocus value={query} onChange={(event) => { setQuery(event.target.value); setActiveIndex(0); }} placeholder="Jump to release gates, datasets, incidents, or pages…" />
        <div className="command-list" role="listbox">
          {filtered.map((command, index) => <button key={command.id} className="command-item" aria-selected={index === activeIndex} onMouseEnter={() => setActiveIndex(index)} onClick={() => { onNavigate(command.route); onClose(); }}><span className="kbd">↵</span><span><strong>{command.label}</strong><br /><span className="muted">{command.hint}</span></span><span>{command.route}</span></button>)}
        </div>
      </section>
    </div>
  );
}
