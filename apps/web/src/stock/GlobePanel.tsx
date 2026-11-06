import { Suspense, lazy } from 'react';
import type { ScenarioResult } from '../data/source';
import { eur, int } from './model';

export type Geo = ScenarioResult['geo'];

const GlobeCanvas = lazy(() => import('./GlobeCanvas'));

export function hasWebGl(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl2') ?? canvas.getContext('webgl'));
  } catch {
    return false;
  }
}

/** Globe over the plants and channels, with a plant table that always works as filter and fallback. */
export function GlobePanel({
  geo,
  selected,
  onSelect,
  webgl = hasWebGl(),
}: {
  geo: Geo;
  selected?: string;
  onSelect: (plant: string | undefined) => void;
  webgl?: boolean;
}) {
  return (
    <section className="rs-card" data-testid="globe-panel">
      <h3>Where the stock sits</h3>
      {webgl ? (
        <div className="rs-globe" data-testid="globe">
          <Suspense fallback={<p role="status">Loading globe</p>}>
            <GlobeCanvas geo={geo} selected={selected} onSelect={(p) => onSelect(selected === p ? undefined : p)} />
          </Suspense>
        </div>
      ) : (
        <p data-testid="globe-fallback">This browser has no WebGL, so the globe is off. The table below shows the same plants.</p>
      )}
      <div className="rs-table-scroll">
        <table className="rs-table" data-testid="plant-table">
          <thead>
            <tr>
              <th>Plant</th>
              <th>Country</th>
              <th className="rs-num">Value at risk</th>
              <th className="rs-num">Units placed</th>
              <th>Filter</th>
            </tr>
          </thead>
          <tbody>
            {geo.plants.map((p) => (
              <tr key={p.plant}>
                <th scope="row">
                  {p.name} <code>{p.plant}</code>
                </th>
                <td>{p.country}</td>
                <td className="rs-num">{eur(p.value_at_risk)}</td>
                <td className="rs-num">{int(p.allocated_units)}</td>
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
    </section>
  );
}
