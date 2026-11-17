import { useState } from 'react';
import { Delta } from '../components/Delta';
import { KpiHint } from '../components/Hint';
import { InlineError } from '../components/InlineError';
import { SCENARIO_LABEL, type Choice } from '../components/ScenarioSwitch';
import { useMoney } from '../data/currency';
import { useRun } from '../data/run';
import { SCENARIOS } from '../data/source';
import { useChoiceResult } from '../data/useScenarioResult';
import { SCENARIO_INFO, KPI_HELP } from '../glossary';
import { pct } from '../results/model';
import { int } from '../stock/model';

const label = (c: Choice, runName?: string) => (c === 'run' ? `Your run: ${runName ?? ''}` : SCENARIO_LABEL[c]);
const story = (c: Choice) => (c === 'run' ? 'The plan you ran on the Rules and run page.' : SCENARIO_INFO[c].story);

/** A sentence a planner can read out: what changed from A to B, and whether it is good. */
function verdict(a: string, b: string, d: { value: number; units: number; destroyed: number; brand: number }, money: (n: number) => string): string {
  const more = (n: number, up: string, down: string) => (n > 0 ? up : down);
  const parts = [
    d.value === 0 ? 'recovers the same value' : `recovers ${money(Math.abs(d.value))} ${more(d.value, 'more', 'less')}`,
    d.destroyed === 0 ? 'destroys the same number of units' : `destroys ${int(Math.abs(d.destroyed))} ${more(d.destroyed, 'more', 'fewer')} units`,
    Math.abs(d.brand) < 0.0005 ? 'leaves brand risk where it was' : `${more(d.brand, 'raises', 'lowers')} brand risk by ${(Math.abs(d.brand) * 100).toFixed(1)} points`,
  ];
  return `Compared with ${a}, ${b} ${parts[0]}, ${parts[1]} and ${parts[2]}.`;
}
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
  const [b, setB] = useState<Choice>(run ? 'run' : 'max_recovery');
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
  const d = {
    value: y.value_recovered - x.value_recovered,
    units: y.units_allocated - x.units_allocated,
    destroyed: y.units_destroyed - x.units_destroyed,
    brand: y.brand_risk_index - x.brand_risk_index,
  };
  const nameA = label(a, run?.name);
  const nameB = label(b, run?.name);
  const rows = [
    { k: 'value_recovered', va: money(x.value_recovered), vb: money(y.value_recovered), text: signed(d.value), change: d.value, eps: 0 },
    { k: 'units_allocated', va: int(x.units_allocated), vb: int(y.units_allocated), text: signedNum(d.units), change: d.units, eps: 0 },
    { k: 'units_destroyed', va: int(x.units_destroyed), vb: int(y.units_destroyed), text: signedNum(d.destroyed), change: d.destroyed, eps: 0 },
    {
      k: 'brand_risk_index',
      va: pct(x.brand_risk_index),
      vb: pct(y.brand_risk_index),
      text: `${d.brand > 0 ? '+' : d.brand < 0 ? '−' : ''}${(Math.abs(d.brand) * 100).toFixed(1)} points`,
      change: d.brand,
      eps: 0.0005,
    },
  ];

  return (
    <>
      {head}
      {pickers}
      <ul className="rs-note" data-testid="scenario-stories">
        <li>
          <strong>A:</strong> {story(a)}
        </li>
        <li>
          <strong>B:</strong> {story(b)}
        </li>
      </ul>
      <div className="rs-card rs-verdict" data-testid="scenario-delta">
        <Delta large text={signed(d.value)} change={d.value} better="up" />
        <span data-testid="scenario-verdict">{verdict(nameA, nameB, d, money)}</span>
      </div>
      <div className="rs-table-scroll" data-testid="scenario-compare">
        <table className="rs-table">
          <thead>
            <tr>
              <th>Simulated data</th>
              <th className="rs-num">A: {nameA}</th>
              <th className="rs-num rs-me">B: {nameB}</th>
              <th className="rs-num">Change from A to B</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.k}>
                <th scope="row">
                  {KPI_HELP[r.k].name}
                  <KpiHint k={r.k} />
                </th>
                <td className="rs-num">{r.va}</td>
                <td className="rs-num rs-me">{r.vb}</td>
                <td className="rs-num">
                  <Delta text={r.text} change={r.change} better={KPI_HELP[r.k].better} epsilon={r.eps} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rs-note">Looking for the plan against a plan made by hand? That comparison sits at the bottom of the Plan page.</p>
    </>
  );
}
