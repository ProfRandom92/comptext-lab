interface Datum { label: string; value: number; auxiliary?: number }

export function BarChart({ data, valueLabel }: { data: Datum[]; valueLabel: (value: number) => string }) {
  const max = Math.max(...data.map((item) => Math.max(item.value, item.auxiliary ?? 0)), 1);
  const barWidth = 100 / Math.max(data.length, 1);
  return (
    <svg className="chart" viewBox="0 0 640 220" role="img" aria-label="Benchmark bar chart">
      <defs>
        <linearGradient id="barGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#6ee7f9" />
          <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.45" />
        </linearGradient>
      </defs>
      {[0, 1, 2, 3].map((line) => <line key={line} className="chart-grid" x1="0" x2="640" y1={35 + line * 45} y2={35 + line * 45} />)}
      {data.map((item, index) => {
        const height = (item.value / max) * 145;
        const x = index * barWidth * 6.4 + 22;
        const width = Math.max(26, barWidth * 4.7);
        return (
          <g key={item.label}>
            <rect className="chart-bar" x={x} y={170 - height} width={width} height={height} rx="8" />
            {item.auxiliary !== undefined ? <circle cx={x + width / 2} cy={170 - (item.auxiliary / max) * 145} r="5" fill="#fbbf24" /> : null}
            <text x={x} y="194" fill="#97a6ba" fontSize="11">{item.label.slice(0, 15)}</text>
            <text x={x} y={158 - height} fill="#e5edf7" fontSize="12">{valueLabel(item.value)}</text>
          </g>
        );
      })}
    </svg>
  );
}
