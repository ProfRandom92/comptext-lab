import { useMemo, useRef, useState, type ReactNode } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { EmptyState } from '../states/AsyncStates';

export interface Column<T> {
  key: string;
  header: string;
  width: string;
  render: (row: T) => ReactNode;
  search?: (row: T) => string;
}

export function VirtualTable<T>({ rows, columns, rowKey, searchPlaceholder = 'Filter rows…' }: { rows: T[]; columns: Column<T>[]; rowKey: (row: T) => string; searchPlaceholder?: string }) {
  const [query, setQuery] = useState('');
  const parentRef = useRef<HTMLDivElement>(null);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return rows;
    return rows.filter((row) => columns.some((column) => (column.search?.(row) ?? '').toLowerCase().includes(normalized)));
  }, [columns, query, rows]);
  const virtualizer = useVirtualizer({ count: filtered.length, getScrollElement: () => parentRef.current, estimateSize: () => 58, overscan: 8 });
  const columnsTemplate = columns.map((column) => column.width).join(' ');

  return (
    <section className="table-wrap" style={{ ['--columns' as string]: columnsTemplate }}>
      <div className="table-toolbar">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={searchPlaceholder} aria-label={searchPlaceholder} />
        <span className="muted">{filtered.length} / {rows.length} rows</span>
      </div>
      <div className="table-head">{columns.map((column) => <div key={column.key}>{column.header}</div>)}</div>
      {filtered.length === 0 ? <EmptyState title="No matching rows" description="Adjust the filter or clear the search query." /> : (
        <div ref={parentRef} style={{ height: 430, overflow: 'auto', position: 'relative' }} tabIndex={0} aria-label="Virtualized result table">
          <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
            {virtualizer.getVirtualItems().map((item) => {
              const row = filtered[item.index];
              return (
                <div className="table-row" key={rowKey(row)} style={{ position: 'absolute', transform: `translateY(${item.start}px)`, width: '100%' }}>
                  {columns.map((column) => <div key={column.key}>{column.render(row)}</div>)}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
