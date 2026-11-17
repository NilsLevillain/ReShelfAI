import { Loading } from '../components/Loading';
import { useState } from 'react';
import { HBars } from '../components/HBars';
import { InlineError } from '../components/InlineError';
import { NextStep } from '../components/NextStep';
import { useScenarioResult } from '../data/useScenarioResult';
import { useMoney } from '../data/currency';
import { REASON_LABEL, applyFilters, int, totalsOf, type Filters, type StockLot } from '../stock/model';
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
  const [withPlan, setWithPlan] = useState(false);
  const { money, compact } = useMoney();

  if (state.status === 'loading') return <Loading what="stock" />;
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
  const tierOf = new Map(all.map((l) => [l.brand, l.tier]));
  const chips = Object.entries(filters).filter(([, v]) => v) as [keyof Filters, string][];

  return (
    <div className="rs-stack">
      <section className="rs-page-head">
        <h2>Stock that cannot sell the normal way</h2>
        <p className="rs-section__sub">
          These lots cannot sell through the main channels. No plan is applied yet: this is the stock as it stands before you
          run the plan.
        </p>
        <span className="rs-evidence">Simulated data, {state.result.n_skus} SKUs</span>
        <div className="rs-seg" role="group" aria-label="View">
          <button type="button" aria-pressed={!withPlan} onClick={() => setWithPlan(false)}>
            Before the plan
          </button>
          <button type="button" aria-pressed={withPlan} onClick={() => setWithPlan(true)}>
            With the ready plan applied
          </button>
        </div>
      </section>

      <div className="rs-cards rs-cards--stat">
        <div className="rs-card rs-stat" data-testid="kpi-value-at-risk">
          <span className="rs-stat__value" title={money(t.valueAtRisk)}>
            {compact(t.valueAtRisk)}
          </span>
          <span>Value at risk</span>
          <span className="rs-stat__hint">What this stock cost, if it is destroyed.</span>
        </div>
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{int(t.units)}</span>
          <span>Units in {t.lots} lots</span>
        </div>
        {withPlan && (
          <>
            <div className="rs-card rs-stat">
              <span className="rs-stat__value">{int(t.allocated)}</span>
              <span>Units the plan sends out</span>
            </div>
            <div className="rs-card rs-stat">
              <span className="rs-stat__value">{int(t.units - t.allocated)}</span>
              <span>Units left unplaced</span>
            </div>
          </>
        )}
      </div>

      <GlobePanel geo={state.result.geo} selected={filters.plant} onSelect={(plant) => set({ plant })} withPlan={withPlan} />

      <div className="rs-cards">
        <div className="rs-card">
          <h3>Why the stock is stuck</h3>
          <p className="rs-section__sub">Value at risk by reason. Click a bar to filter. Reasons use warm colors, brands use cool ones.</p>
          <HBars
            testId="reason-bars"
            selected={filters.reason}
            onSelect={(k) => set({ reason: filters.reason === k ? undefined : k })}
            items={reasons.map(([k, v]) => ({ key: k, label: REASON_LABEL[k] ?? k, value: v, text: money(v), tone: { kind: 'reason' as const, value: k } }))}
          />
        </div>
        <div className="rs-card">
          <h3>{filters.brand ? `${filters.brand} by category` : 'Which brands'}</h3>
          <p className="rs-section__sub">Value at risk. Violet is luxury, blue is premium, teal is mass market.</p>
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
            items={drill.map(([k, v]) => ({
              key: k,
              label: k,
              value: v,
              text: money(v),
              tone: filters.brand ? undefined : { kind: 'tier' as const, value: tierOf.get(k) ?? '' },
            }))}
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
        <StockTable lots={visible} showPlan={withPlan} />
      </section>
      <NextStep
        to="/parameters"
        label="Set the rules and run the plan"
        text="You have seen the stock that needs a second life. Check the business rules, then run the plan."
      />
    </div>
  );
}
