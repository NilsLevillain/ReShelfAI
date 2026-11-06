import { useState } from 'react';
import { InlineError } from '../components/InlineError';
import { ScenarioSwitch } from '../components/ScenarioSwitch';
import type { ScenarioName } from '../data/source';
import { useScenarioResult } from '../data/useScenarioResult';
import { ruleName, signedEur, violationCount, pct } from '../results/model';
import { SolverStatus } from '../results/SolverStatus';
import { eur, int } from '../stock/model';

export function Compare() {
  const [scenario, setScenario] = useState<ScenarioName>('default');
  const state = useScenarioResult(scenario);
  const switcher = <ScenarioSwitch value={scenario} onChange={setScenario} />;

  if (state.status === 'loading')
    return (
      <>
        {switcher}
        <p role="status">Loading comparison</p>
      </>
    );
  if (state.status === 'error')
    return (
      <>
        {switcher}
        <InlineError error={state.error} onRetry={state.retry} />
      </>
    );

  const r = state.result;
  const raw = r.baseline.raw;
  const fair = r.baseline.compliant;
  const opt = r.optimizer;
  const delta = opt.value_recovered - fair.value_recovered;
  const broken = violationCount(r);

  const row = (label: string, a: string, b: string, c: string) => (
    <tr key={label}>
      <th scope="row">{label}</th>
      <td className="rs-num">{a}</td>
      <td className="rs-num">{b}</td>
      <td className="rs-num rs-me">{c}</td>
    </tr>
  );

  return (
    <>
      <section className="rs-page-head">
        <h2>Optimizer against the greedy baseline</h2>
        <SolverStatus solve={r.solve} />
      </section>
      {switcher}

      <div className="rs-card rs-stat rs-stat--goal">
        <span className="rs-stat__value" data-testid="euro-delta" style={{ color: 'var(--rs-compare-delta-gain)' }}>
          {signedEur(delta)}
        </span>
        <span>value recovered against the greedy baseline, compared with its compliant plan</span>
      </div>

      <div className="rs-callout rs-callout--info">
        The greedy baseline picks channels by hand and ignores {Object.keys(r.baseline.audit).length} kinds of rule. Its raw plan
        breaks {int(broken)} rule instances, so its raw value is not a plan anyone can run. The compliant plan is the same plan
        after repair. Compare against the compliant plan.
      </div>

      <div className="rs-table-scroll" data-testid="compare-panel">
        <table className="rs-table">
          <thead>
            <tr>
              <th>Simulated data</th>
              <th className="rs-num" data-testid="baseline-column">
                Greedy baseline, raw
              </th>
              <th className="rs-num">Greedy baseline, compliant</th>
              <th className="rs-num rs-me" data-testid="optimizer-column">
                Optimizer
              </th>
            </tr>
          </thead>
          <tbody>
            {row('Value recovered', eur(raw.value_recovered), eur(fair.value_recovered), eur(opt.value_recovered))}
            {row('Units placed', int(raw.units_allocated), int(fair.units_allocated), int(opt.units_allocated))}
            {row('Units destroyed', int(raw.units_destroyed), int(fair.units_destroyed), int(opt.units_destroyed))}
            {row('Brand risk index', pct(raw.brand_risk_index), pct(fair.brand_risk_index), pct(opt.brand_risk_index))}
            {row('Rule instances broken', int(broken), '0', '0')}
          </tbody>
        </table>
      </div>

      <section>
        <h3>Rules the greedy baseline breaks</h3>
        <ul data-testid="baseline-audit">
          {Object.entries(r.baseline.audit).map(([name, a]) => (
            <li key={name}>
              {ruleName(name)} <code>{name}</code>: broken {int(a.count)} times, {int(a.excess)} over the limit
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
