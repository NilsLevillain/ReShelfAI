import { useState } from 'react';
import { InlineError } from '../components/InlineError';
import { SCENARIO_LABEL, type Choice } from '../components/ScenarioSwitch';
import { useMoney } from '../data/currency';
import { useRun } from '../data/run';
import { SCENARIOS } from '../data/source';
import { useChoiceResult } from '../data/useScenarioResult';
import { pct } from '../results/model';
import { int } from '../stock/model';

const label = (c: Choice, runName?: string) => (c === 'run' ? `Your run: ${runName ?? ''}` : SCENARIO_LABEL[c]);
const signedNum = (v: number) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${int(Math.abs(v))}`;

function Picker({ name, value, onChange, runName }: { name: string; value: Choice; onChange: (c: Choice) => void; runName?: string }) {
  return (
    <label className="rs-groupby">
      {name}
      <select className="rs-select" value={value} onChange={(e) => onChange(e.target.value as Choice)}>
        {SCENARIOS.map((s) => (
          <option key={s} value={s}>
            {SCENARIO_LABEL[s]}
          </option>
        ))}
        {runName && <option value="run">Your run: {runName}</option>}
      </select>
    </label>
  );
}

/** Two scenarios side by side. Both come from the same source, nothing is recomputed here. */
export function Compare() {
  const { run } = useRun();
  const { money, signed } = useMoney();
  const [a, setA] = useState<Choice>('default');
  const [b, setB] = useState<Choice>(run ? 'run' : 'luxury_protection');
  const sa = useChoiceResult(a);
  const sb = useChoiceResult(b);

  const pickers = (
    <div className="rs-toolbar">
      <Picker name="Scenario A" value={a} onChange={setA} runName={run?.name} />
      <Picker name="Scenario B" value={b} onChange={setB} runName={run?.name} />
    </div>
  );
  const head = (
    <section className="rs-page-head">
      <h2>Compare two scenarios</h2>
      <p className="rs-section__sub">
        Pick two scenarios, for example the default rules and a tighter set, and see what the change does to the value
        recovered and to the stock that is destroyed. Run your own on the Rules and run page to add it here.
      </p>
    </section>
  );

  if (sa.status === 'loading' || sb.status === 'loading')
    return (
      <>
        {head}
        {pickers}
        <p role="status">Loading comparison</p>
      </>
    );
  if (sa.status === 'error' || sb.status === 'error') {
    const failed = sa.status === 'error' ? sa : (sb as typeof sa);
    return (
      <>
        {head}
        {pickers}
        {failed.status === 'error' && <InlineError error={failed.error} onRetry={failed.retry} />}
      </>
    );
  }

  const x = sa.result.optimizer;
  const y = sb.result.optimizer;
  const delta = y.value_recovered - x.value_recovered;
  const rows: [string, string, string, string][] = [
    ['Value recovered', money(x.value_recovered), money(y.value_recovered), signed(delta)],
    ['Units given a second life', int(x.units_allocated), int(y.units_allocated), signedNum(y.units_allocated - x.units_allocated)],
    ['Units destroyed', int(x.units_destroyed), int(y.units_destroyed), signedNum(y.units_destroyed - x.units_destroyed)],
    ['Brand risk index', pct(x.brand_risk_index), pct(y.brand_risk_index), `${((y.brand_risk_index - x.brand_risk_index) * 100).toFixed(1)} points`],
  ];

  return (
    <>
      {head}
      {pickers}
      <div className="rs-card rs-stat rs-stat--goal" data-testid="scenario-delta">
        <span className="rs-stat__value" style={{ color: delta >= 0 ? 'var(--rs-compare-delta-gain)' : 'var(--rs-compare-delta-cost)' }}>
          {signed(delta)}
        </span>
        <span>value recovered by scenario B against scenario A.</span>
      </div>
      <div className="rs-table-scroll" data-testid="scenario-compare">
        <table className="rs-table">
          <thead>
            <tr>
              <th>Simulated data</th>
              <th className="rs-num">A: {label(a, run?.name)}</th>
              <th className="rs-num rs-me">B: {label(b, run?.name)}</th>
              <th className="rs-num">Change</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([name, va, vb, d]) => (
              <tr key={name}>
                <th scope="row">{name}</th>
                <td className="rs-num">{va}</td>
                <td className="rs-num rs-me">{vb}</td>
                <td className="rs-num">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rs-note">Looking for the plan against a plan made by hand? That comparison sits at the bottom of the Plan page.</p>
    </>
  );
}
