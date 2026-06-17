import { VirtualTable, type Column } from '../../components/table/VirtualTable';
import { percent, relativeTime } from '../../lib/format';
import type { DashboardPayload, OpsIncident } from '../../types/domain';

const columns: Column<OpsIncident>[] = [
  { key: 'id', header: 'Incident', width: '.75fr', render: (row) => <strong>{row.id}</strong>, search: (row) => row.id },
  { key: 'title', header: 'Title', width: '1.7fr', render: (row) => row.title, search: (row) => row.title },
  { key: 'severity', header: 'Severity', width: '.7fr', render: (row) => <span className={`badge ${row.severity.toLowerCase()}`}>{row.severity}</span>, search: (row) => row.severity },
  { key: 'status', header: 'Status', width: '.8fr', render: (row) => <span className={`badge ${row.status}`}>{row.status}</span>, search: (row) => row.status },
  { key: 'service', header: 'Service', width: '1fr', render: (row) => row.service, search: (row) => row.service },
  { key: 'assignee', header: 'Assignee', width: '.9fr', render: (row) => row.assignee, search: (row) => row.assignee },
  { key: 'burn', header: 'Burn', width: '.55fr', render: (row) => percent(row.error_budget_burn, 1), search: (row) => String(row.error_budget_burn) },
  { key: 'updated', header: 'Updated', width: '.7fr', render: (row) => relativeTime(row.updated_at), search: (row) => row.updated_at },
];

export function IncidentsPage({ payload }: { payload: DashboardPayload }) {
  return <div className="grid"><section className="grid cols-3">{payload.incidents.map((incident) => <article className="card" key={incident.id}><div className="card-header"><div><h3>{incident.id}</h3><p>{incident.service} · {incident.region}</p></div><span className={`badge ${incident.status}`}>{incident.status}</span></div><strong>{incident.title}</strong><p>{incident.impacted_assets} assets · owner {incident.assignee}</p><div className="metric">{percent(incident.error_budget_burn, 1)}</div></article>)}</section><VirtualTable rows={payload.incidents} columns={columns} rowKey={(row) => row.id} searchPlaceholder="Filter incidents…" /></div>;
}
