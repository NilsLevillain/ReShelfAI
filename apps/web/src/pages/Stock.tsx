import { useState } from 'react';
import { HBars } from '../components/HBars';
import { InlineError } from '../components/InlineError';
import { useScenarioResult } from '../data/useScenarioResult';
import { REASON_LABEL, applyFilters, eur, int, totalsOf, type Filters, type StockLot } from '../stock/model';
import { GlobePanel } from '../stock/GlobePanel';
import { StockTable } from '../stock/StockTable';

function bucketBy(lots: StockLot[], key: 'brand' | 'category' | 'reason') {
  const m = new Map<string, number>();
  for (const l of lots) m.set(l[key], (m.get(l[key]) ?? 0) + l.value_at_risk);
  return [...m].sort((a, b) => b[1] - a[1]);
}

export function Stock() {
  const state = useScenarioResult('default');
  const [filters, setFilters] = useState<Filters>({});

  if (state.status === 'loading') return <p role="status">Loading stock</p>;
  if (state.status === 'error') return <InlineError error={state.error} onRetry={state.retry} />;

  const all = state.result.stock.lots;
  const visible = applyFilters(all, filters);
  const t = totalsOf(visible);
  const set = (patch: Filters) => setFilters((f) => ({ ...f, ...patch }));

  // Drill: brands first, then the categories of the chosen brand. The reason bars follow the filters.
  const drillSource = applyFilters(all, { reason: filters.reason });
  const drill = filters.brand
    ? bucketBy(applyFilters(drillSource, { brand: filters.brand }), 'category')
    : bucketBy(drillSource, 'brand');
  const reasons = bucketBy(applyFilters(all, { brand: filters.brand, category: filters.category }), 'reason');
  const chips = Object.entries(filters).filter(([, v]) => v) as [keyof Filters, string][];

  return (
    <>
      <section className="rs-page-head">
        <h2>Stock that cannot sell the normal way</h2>
        <span className="rs-evidence">Simulated data, {state.result.n_skus} SKUs</span>
      </section>

      <div className="rs-cards rs-cards--stat">
        <div className="rs-card rs-stat" data-testid="kpi-value-at-risk">
          <span className="rs-stat__value">{eur(t.valueAtRisk)}</span>
          <span>Value at risk</span>
        </div>
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{int(t.units)}</span>
          <span>Units in {t.lots} lots</span>
        </div>
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{int(t.allocated)}</span>
          <span>Units the plan sends out</span>
        </div>
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{int(t.units - t.allocated)}</span>
          <span>Units left unplaced</span>
        </div>
      </div>

      <GlobePanel geo={state.result.geo} selected={filters.plant} onSelect={(plant) => set({ plant })} />

      <div className="rs-cards">
        <div className="rs-card">
          <h3>By reason</h3>
          <HBars
            testId="reason-bars"
            selected={filters.reason}
            onSelect={(k) => set({ reason: filters.reason === k ? undefined : k })}
            items={reasons.map(([k, v]) => ({ key: k, label: REASON_LABEL[k] ?? k, value: v, text: eur(v) }))}
          />
        </div>
        <div className="rs-card">
          <ol className="rs-crumbs" aria-label="Drill">
            <li aria-current={filters.brand ? undefined : 'page'}>
              {filters.brand ? (
                <button type="button" onClick={() => set({ brand: undefined, category: undefined })}>
                  All brands
                </button>
              ) : (
                'All brands'
              )}
            </li>
            {filters.brand && <li aria-current="page">{filters.brand}</li>}
          </ol>
          <HBars
            testId="drill-bars"
            selected={filters.brand ? filters.category : undefined}
            onSelect={(k) => (filters.brand ? set({ category: filters.category === k ? undefined : k }) : set({ brand: k }))}
            items={drill.map(([k, v]) => ({ key: k, label: k, value: v, text: eur(v) }))}
          />
        </div>
      </div>

      <section>
        {chips.length > 0 && (
          <div className="rs-chips" data-testid="filter-chips">
            {chips.map(([k, v]) => (
              <button key={k} type="button" className="rs-chip" aria-label={`Clear ${k} ${v}`} onClick={() => set({ [k]: undefined })}>
                {k}: {k === 'reason' ? (REASON_LABEL[v] ?? v) : v} ×
              </button>
            ))}
          </div>
        )}
        <StockTable lots={visible} />
      </section>
    </>
  );
}
