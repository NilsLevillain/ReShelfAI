import { Suspense, lazy, useState } from 'react';
import type { ScenarioResult } from '../data/source';
import { useMoney, type Money } from '../data/currency';
import { channelInfo, countryName } from '../glossary';
import { codeOfCountryId } from './countries';
import { int } from './model';

export type Geo = ScenarioResult['geo'];
type Country = Geo['countries'][number];

const GlobeCanvas = lazy(() => import('./GlobeCanvas'));

export function hasWebGl(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl2') ?? canvas.getContext('webgl'));
  } catch {
    return false;
  }
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** Lines of a hover card. Numbers come from the result, only formatted here. */
function countryLines(c: Country, m: Money, withPlan: boolean): string[] {
  const lines = [`Stock held here: ${int(c.units)} units, ${m.compact(c.value_at_risk)} at cost`];
  if (withPlan && c.units > 0) lines.push(`Placed by the plan: ${int(c.allocated_units)} units`, `Destroyed: ${int(c.destroyed_units)} units, ${m.compact(c.value_destroyed)} at cost`);
  if (withPlan && c.received_units > 0) lines.push(`Received from the plan: ${int(c.received_units)} units, ${m.compact(c.value_recovered)} recovered`);
  if (!withPlan && c.channels.length > 0) lines.push(`${c.channels.length} second life channel(s) here`);
  return lines;
}

const card = (title: string, lines: string[]) =>
  `<div class="rs-globe__tip"><strong>${esc(title)}</strong>${lines.map((l) => `<span>${esc(l)}</span>`).join('')}</div>`;

type SortKey = 'country' | 'value_at_risk' | 'units' | 'allocated_units' | 'destroyed_units' | 'value_destroyed' | 'received_units' | 'value_recovered';

/** One row per country. Click a column to sort. */
function CountryTable({ countries, withPlan }: { countries: Country[]; withPlan: boolean }) {
  const { compact, money } = useMoney();
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: 'value_at_risk', desc: true });
  const cols: { key: SortKey; label: string; plan?: boolean }[] = [
    { key: 'country', label: 'Country' },
    { key: 'value_at_risk', label: 'Value at risk' },
    { key: 'units', label: 'Units at risk' },
    { key: 'allocated_units', label: 'Units placed', plan: true },
    { key: 'destroyed_units', label: 'Units destroyed', plan: true },
    { key: 'value_destroyed', label: 'Value destroyed', plan: true },
    { key: 'received_units', label: 'Units received', plan: true },
    { key: 'value_recovered', label: 'Value recovered', plan: true },
  ];
  const shown = cols.filter((c) => withPlan || !c.plan);
  const rows = [...countries].sort((a, b) => {
    const [x, y] = sort.key === 'country' ? [countryName(a.country), countryName(b.country)] : [a[sort.key], b[sort.key]];
    const order = typeof x === 'string' ? x.localeCompare(y as string) : (x as number) - (y as number);
    return sort.desc ? -order : order;
  });
  const cell = (c: Country, key: SortKey) => {
    switch (key) {
      case 'country':
        return countryName(c.country);
      case 'value_at_risk':
      case 'value_destroyed':
      case 'value_recovered':
        return <span title={money(c[key])}>{compact(c[key])}</span>;
      default:
        return int(c[key]);
    }
  };
  return (
    <div className="rs-table-scroll">
      <table className="rs-table" data-testid="country-table">
        <caption className="rs-sr">Stock and plan by country. Click a column title to sort.</caption>
        <thead>
          <tr>
            {shown.map((c) => (
              <th
                key={c.key}
                className={c.key === 'country' ? undefined : 'rs-num'}
                aria-sort={sort.key === c.key ? (sort.desc ? 'descending' : 'ascending') : 'none'}
              >
                <button
                  type="button"
                  className="rs-sortbtn"
                  onClick={() => setSort((s) => ({ key: c.key, desc: s.key === c.key ? !s.desc : c.key !== 'country' }))}
                >
                  {c.label}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.country}>
              {shown.map((col) =>
                col.key === 'country' ? (
                  <th key={col.key} scope="row">
                    {cell(c, col.key)}
                  </th>
                ) : (
                  <td key={col.key} className="rs-num">
                    {cell(c, col.key)}
                  </td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Globe over the plants and channels, with tables that always work as filter and fallback. */
export function GlobePanel({
  geo,
  selected,
  onSelect,
  webgl = hasWebGl(),
  withPlan = true,
}: {
  geo: Geo;
  selected?: string;
  onSelect: (plant: string | undefined) => void;
  webgl?: boolean;
  withPlan?: boolean;
}) {
  const m = useMoney();
  const { money, compact } = m;
  const byCountry = new Map(geo.countries.map((c) => [c.country, c]));

  const labelOf = (kind: 'plant' | 'channel' | 'country', code: string): string => {
    if (kind === 'plant') {
      const p = geo.plants.find((x) => x.plant === code);
      if (!p) return '';
      const lines = [`Stock held: ${int(p.units)} units, ${compact(p.value_at_risk)} at cost`];
      if (withPlan) lines.push(`Placed: ${int(p.allocated_units)} units`, `Destroyed: ${int(p.destroyed_units)} units, ${compact(p.value_destroyed)} at cost`);
      return card(`${p.name} (${p.plant}), ${countryName(p.country)}`, lines);
    }
    if (kind === 'channel') {
      const c = geo.channels.find((x) => x.channel === code);
      if (!c) return '';
      const info = channelInfo(code, geo.channels);
      return card(info.name, withPlan ? [`Receives ${int(c.allocated_units)} units`, `Recovers ${compact(c.value_recovered)}`] : ['A second life channel']);
    }
    const country = byCountry.get(codeOfCountryId(code) ?? '');
    return country ? card(countryName(country.country), countryLines(country, m, withPlan)) : '';
  };

  return (
    <section className="rs-card rs-stack" data-testid="globe-panel">
      <h3>Where the stock sits</h3>
      {webgl ? (
        <>
          <div className="rs-globe" data-testid="globe">
            <Suspense fallback={<p role="status">Loading globe</p>}>
              <GlobeCanvas geo={geo} selected={selected} onSelect={(p) => onSelect(selected === p ? undefined : p)} labelOf={labelOf} />
            </Suspense>
          </div>
          <div className="rs-legend" data-testid="globe-legend">
            <span>
              <span className="rs-dot rs-dot--plant" aria-hidden="true" />
              Plant, taller means more value at risk
            </span>
            <span>
              <span className="rs-dot rs-dot--channel" aria-hidden="true" />
              Second life channel
            </span>
            <span>
              <span className="rs-dot rs-dot--outline rs-dot--land" aria-hidden="true" />
              Country with a plant or a channel
            </span>
            <span>Hover a point or a country for the numbers. Click a plant to filter the stock table.</span>
          </div>
        </>
      ) : (
        <p data-testid="globe-fallback">This browser has no WebGL, so the globe is off. The tables below show the same numbers.</p>
      )}

      <div>
        <h4>By country</h4>
        <CountryTable countries={geo.countries} withPlan={withPlan} />
      </div>

      <div>
        <h4>By plant</h4>
        <div className="rs-table-scroll">
          <table className="rs-table" data-testid="plant-table">
            <thead>
              <tr>
                <th>Plant</th>
                <th>Country</th>
                <th className="rs-num">Value at risk</th>
                <th className="rs-num">Units at risk</th>
                {withPlan && <th className="rs-num">Units placed</th>}
                {withPlan && <th className="rs-num">Units destroyed</th>}
                <th>Filter</th>
              </tr>
            </thead>
            <tbody>
              {geo.plants.map((p) => (
                <tr key={p.plant}>
                  <th scope="row">
                    {p.name} <code>{p.plant}</code>
                  </th>
                  <td>{countryName(p.country)}</td>
                  <td className="rs-num">{money(p.value_at_risk)}</td>
                  <td className="rs-num">{int(p.units)}</td>
                  {withPlan && <td className="rs-num">{int(p.allocated_units)}</td>}
                  {withPlan && <td className="rs-num">{int(p.destroyed_units)}</td>}
                  <td>
                    <button
                      type="button"
                      className="rs-btn"
                      aria-pressed={selected === p.plant}
                      aria-label={`Filter stock on plant ${p.plant}`}
                      onClick={() => onSelect(selected === p.plant ? undefined : p.plant)}
                    >
                      {selected === p.plant ? 'Clear' : 'Show lots'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
