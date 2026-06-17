import { BarChart } from '../../components/charts/BarChart';
import { VirtualTable, type Column } from '../../components/table/VirtualTable';
import { compactNumber, ms, percent, ratio } from '../../lib/format';
import type { BenchmarkResult, DashboardPayload } from '../../types/domain';

const columns: Column<BenchmarkResult>[] = [
  { key: 'name', header: 'Case', width: '1.35fr', render: (row) => <strong>{row.name}</strong>, search: (row) => row.name },
  { key: 'ratio', header: 'Ratio', width: '.6fr', render: (row) => ratio(row.compression_ratio), search: (row) => String(row.compression_ratio) },
  { key: 'tokens', header: 'Token savings', width: '.75fr', render: (row) => percent(row.reduction_percent, 2), search: (row) => String(row.reduction_percent) },
  { key: 'latency', header: 'Median', width: '.6fr', render: (row) => ms(row.median_ms), search: (row) => String(row.median_ms) },
  { key: 'throughput', header: 'Throughput', width: '.7fr', render: (row) => `${compactNumber.format(row.lines_per_second)} l/s`, search: (row) => String(row.lines_per_second) },
  { key: 'coverage', header: 'Coverage', width: '.65fr', render: (row) => percent(row.top_family_coverage), search: (row) => String(row.top_family_coverage) },
  { key: 'expectation', header: 'Expectation', width: '1.6fr', render: (row) => <span className="muted">{row.honest_expectation}</span>, search: (row) => row.honest_expectation },
];

export function BenchmarksPage({ payload }: { payload: DashboardPayload }) {
  return <div className="grid"><article className="card"><div className="card-header"><div><h3>Throughput vs memory</h3><p>Reusable chart abstraction for compression lanes and capacity planning.</p></div></div><BarChart data={payload.benchmarks.map((row) => ({ label: row.name, value: row.lines_per_second, auxiliary: row.peak_kib }))} valueLabel={(value) => compactNumber.format(value)} /></article><VirtualTable rows={payload.benchmarks} columns={columns} rowKey={(row) => row.name} searchPlaceholder="Filter benchmark cases…" /></div>;
}
