import { EmptyState } from '../../components/states/AsyncStates';
import { VirtualTable, type Column } from '../../components/table/VirtualTable';
import { percent } from '../../lib/format';
import type { DashboardPayload, ForensicDataset, ForensicFinding } from '../../types/domain';

const datasetColumns: Column<ForensicDataset>[] = [
  { key: 'dataset', header: 'Dataset', width: '1.2fr', render: (row) => <strong>{row.dataset}</strong>, search: (row) => row.dataset },
  { key: 'semantic', header: 'Semantic', width: '.7fr', render: (row) => percent(row.semantic_retention * 100, 2), search: (row) => String(row.semantic_retention) },
  { key: 'anomaly', header: 'Anomaly', width: '.7fr', render: (row) => percent(row.anomaly_survivability * 100, 2), search: (row) => String(row.anomaly_survivability) },
  { key: 'anchor', header: 'Anchor', width: '.7fr', render: (row) => percent(row.anchor_retention * 100, 2), search: (row) => String(row.anchor_retention) },
  { key: 'safety', header: 'Safety', width: '.7fr', render: (row) => percent(row.safety_critical_retention * 100, 2), search: (row) => String(row.safety_critical_retention) },
  { key: 'state', header: 'Gate', width: '.55fr', render: (row) => <span className={`badge ${row.passed ? 'nominal' : 'critical'}`}>{row.passed ? 'pass' : 'fail'}</span>, search: (row) => row.passed ? 'pass' : 'fail' },
  { key: 'hash', header: 'Compressed hash', width: '1.1fr', render: (row) => <span className="mono">{row.compressed_sha256.slice(0, 18)}</span>, search: (row) => row.compressed_sha256 },
];

const findingColumns: Column<ForensicFinding>[] = [
  { key: 'id', header: 'Finding', width: '.7fr', render: (row) => <strong>{row.id}</strong>, search: (row) => row.id },
  { key: 'severity', header: 'Severity', width: '.65fr', render: (row) => <span className={`badge ${row.severity.toLowerCase()}`}>{row.severity}</span>, search: (row) => row.severity },
  { key: 'title', header: 'Title', width: '1.5fr', render: (row) => row.title, search: (row) => row.title },
  { key: 'owner', header: 'Owner', width: '.9fr', render: (row) => row.owner, search: (row) => row.owner },
  { key: 'evidence', header: 'Evidence', width: '1.4fr', render: (row) => <span className="muted">{row.evidence}</span>, search: (row) => row.evidence },
];

export function ForensicsPage({ payload }: { payload: DashboardPayload }) {
  const findings = payload.forensic.flatMap((dataset) => dataset.findings);
  return <div className="grid"><VirtualTable rows={payload.forensic} columns={datasetColumns} rowKey={(row) => row.dataset} searchPlaceholder="Filter forensic datasets…" />{findings.length ? <VirtualTable rows={findings} columns={findingColumns} rowKey={(row) => row.id} searchPlaceholder="Filter findings…" /> : <EmptyState title="No active forensic findings" description="All semantic, anomaly, anchor, and safety-critical gates are currently passing." />}</div>;
}
