import { Fragment, useState } from 'react';
import { useMoney } from '../data/currency';
import { REASON_LABEL, groupLots, int, sharePct, totalsOf, type GroupKey, type StockLot } from './model';

type ColGroup = 'identity' | 'stock' | 'allocation' | 'value';
const GROUPS: { id: ColGroup; label: string; title: string; text: string; cols: number }[] = [
  { id: 'identity', label: 'Identity', title: 'What it is', text: 'Brand, category and the plant that holds it', cols: 3 },
  { id: 'stock', label: 'Stock', title: 'Why it is stuck', text: 'Reason, expiry date and quantity', cols: 4 },
  { id: 'allocation', label: 'Allocation', title: 'What the plan does', text: 'Share sent out and channels that can take it', cols: 3 },
  { id: 'value', label: 'Value', title: 'What it is worth', text: 'Cost per unit and value at risk', cols: 2 },
];

function Share({ part, whole }: { part: number; whole: number }) {
  const pct = sharePct(part, whole);
  return (
    <span className="rs-share" style={{ '--rs-share': `${pct}%` } as React.CSSProperties}>
      {int(part)} ({pct}%)
      <span className="rs-share__bar">
        <span className="rs-share__fill" />
      </span>
    </span>
  );
}

export function StockTable({ lots, showPlan = false }: { lots: StockLot[]; showPlan?: boolean }) {
  const { money } = useMoney();
  const [shown, setShown] = useState<Set<ColGroup>>(new Set(['identity', 'stock', 'allocation', 'value']));
  const [by, setBy] = useState<GroupKey>('none');
  const [closed, setClosed] = useState<Set<string>>(new Set());
  const on = (g: ColGroup) => shown.has(g) && (g !== 'allocation' || showPlan);
  const groupsShown = GROUPS.filter((g) => g.id !== 'allocation' || showPlan);
  const toggle = (g: ColGroup) =>
    setShown((s) => {
      const n = new Set(s);
      if (n.has(g)) n.delete(g);
      else n.add(g);
      return n;
    });
  const flip = (k: string) =>
    setClosed((s) => {
      const n = new Set(s);
      if (n.has(k)) n.delete(k);
      else n.add(k);
      return n;
    });

  const groups = groupLots(lots, by);
  const t = totalsOf(lots);
  const span = 1 + (on('identity') ? 3 : 0) + (on('stock') ? 4 : 0) + (on('allocation') ? 3 : 0) + (on('value') ? 2 : 0);

  const cells = (totals: { units: number; allocated: number; valueAtRisk: number }, l?: StockLot) => (
    <>
      {on('identity') && (l ? [l.brand, l.category, l.plant].map((v) => <td key={v}>{v}</td>) : <td colSpan={3} />)}
      {on('stock') && (
        <>
          {l ? (
            <>
              <td className="rs-gstart">
                <span className="rs-label" data-reason={l.reason}>
                  <span className="rs-dot" aria-hidden="true" />
                  {REASON_LABEL[l.reason] ?? l.reason}
                </span>
              </td>
              <td>{l.expiry_date}</td>
              <td className="rs-num">{int(l.days_to_expiry)}</td>
            </>
          ) : (
            <td colSpan={3} className="rs-gstart" />
          )}
          <td className="rs-num">{int(totals.units)}</td>
        </>
      )}
      {on('allocation') && (
        <>
          <td className="rs-gstart">
            <Share part={totals.allocated} whole={totals.units} />
          </td>
          {l ? (
            <>
              <td className="rs-num">{l.channels_open}</td>
              <td className="rs-num">{l.channels_blocked}</td>
            </>
          ) : (
            <td colSpan={2} />
          )}
        </>
      )}
      {on('value') && (
        <>
          <td className="rs-num rs-gstart">{l ? l.unit_cost.toFixed(2) : ''}</td>
          <td className="rs-num">{money(totals.valueAtRisk)}</td>
        </>
      )}
    </>
  );

  return (
    <div data-testid="stock-table">
      <div className="rs-toolbar">
        <div className="rs-seg rs-seg--cols" role="group" aria-label="Column groups">
          {groupsShown.map((g) => (
            <button key={g.id} type="button" aria-pressed={on(g.id)} title={`${g.title}: ${g.text}`} onClick={() => toggle(g.id)}>
              {g.label}
            </button>
          ))}
        </div>
        <label className="rs-groupby">
          Group by
          <select value={by} onChange={(e) => setBy(e.target.value as GroupKey)}>
            <option value="none">None</option>
            <option value="brand">Brand</option>
            <option value="category">Category</option>
            <option value="reason">Reason</option>
            <option value="plant">Plant</option>
          </select>
        </label>
      </div>
      <div className="rs-table-scroll">
        <table className="rs-table">
          <thead>
            <tr className="rs-colgroup">
              <th>
                Lot<small>One batch of one product</small>
              </th>
              {groupsShown.filter((g) => on(g.id)).map((g) => (
                <th key={g.id} colSpan={g.cols}>
                  {g.title}
                  <small>{g.text}</small>
                </th>
              ))}
            </tr>
            <tr>
              <th>Lot</th>
              {on('identity') && (
                <>
                  <th className="rs-gstart">Brand</th>
                  <th>Category</th>
                  <th>Plant</th>
                </>
              )}
              {on('stock') && (
                <>
                  <th className="rs-gstart">Reason</th>
                  <th>Expiry</th>
                  <th className="rs-num">Days left</th>
                  <th className="rs-num">Units</th>
                </>
              )}
              {on('allocation') && (
                <>
                  <th className="rs-gstart">Sent out</th>
                  <th className="rs-num">Open channels</th>
                  <th className="rs-num">Blocked channels</th>
                </>
              )}
              {on('value') && (
                <>
                  <th className="rs-num rs-gstart">Unit cost</th>
                  <th className="rs-num">Value at risk</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {lots.length === 0 && (
              <tr>
                <td colSpan={span}>No lot matches the filters. Clear a filter chip to see more.</td>
              </tr>
            )}
            {groups.map((g) => (
              <Fragment key={g.key || 'all'}>
                {by !== 'none' && (
                  <tr className="rs-row--group" data-testid="group-row">
                    <th scope="row">
                      <button type="button" aria-expanded={!closed.has(g.key)} onClick={() => flip(g.key)}>
                        {closed.has(g.key) ? '▸' : '▾'} {by === 'reason' ? (REASON_LABEL[g.key] ?? g.key) : g.key}
                      </button>
                    </th>
                    {cells(g.totals)}
                  </tr>
                )}
                {!closed.has(g.key) &&
                  g.lots.map((l) => (
                    <tr key={l.lot}>
                      <th scope="row">{l.lot}</th>
                      {cells({ units: l.units, allocated: l.allocated_units, valueAtRisk: l.value_at_risk }, l)}
                    </tr>
                  ))}
              </Fragment>
            ))}
            <tr className="rs-row--total" data-testid="total-row">
              <th scope="row">Total ({t.lots} lots)</th>
              {cells({ units: t.units, allocated: t.allocated, valueAtRisk: t.valueAtRisk })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
