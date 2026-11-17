import { Delta } from '../components/Delta';
import { useMoney } from '../data/currency';
import { RULE_HELP } from '../glossary';
import { int } from '../stock/model';
import { pct, violationCount, type Result } from './model';

/** The plan against a plan made by hand (the greedy baseline), with the rules the hand made plan breaks. */
export function BaselineCompare({ result: r }: { result: Result }) {
  const { money, signed } = useMoney();
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
    <section className="rs-stack" data-testid="baseline-compare">
      <div className="rs-section__head">
        <h3>Why not plan by hand?</h3>
        <p className="rs-section__sub">
          The greedy baseline is a plan made by hand: it sends each lot to the channel that pays most and skips{' '}
          {Object.keys(r.baseline.audit).length} kinds of rule. Its raw plan breaks {int(broken)} rules, so nobody could run it.
          The compliant plan is the same plan after repair. Compare against the compliant plan.
        </p>
      </div>
      <div className="rs-card rs-stat rs-stat--goal">
        <Delta large testId="baseline-delta" text={signed(delta)} change={delta} better="up" />
        <span>more value recovered against the greedy baseline, compared with its compliant plan</span>
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
                The plan
              </th>
            </tr>
          </thead>
          <tbody>
            {row('Value recovered', money(raw.value_recovered), money(fair.value_recovered), money(opt.value_recovered))}
            {row('Units placed', int(raw.units_allocated), int(fair.units_allocated), int(opt.units_allocated))}
            {row('Units destroyed', int(raw.units_destroyed), int(fair.units_destroyed), int(opt.units_destroyed))}
            {row('Brand risk index', pct(raw.brand_risk_index), pct(fair.brand_risk_index), pct(opt.brand_risk_index))}
            {row('Rules broken', int(broken), '0', '0')}
          </tbody>
        </table>
      </div>
      <div>
        <h4>Rules the greedy baseline breaks</h4>
        <ul data-testid="baseline-audit" className="rs-list">
          {Object.entries(r.baseline.audit).map(([name, a]) => (
            <li key={name}>
              <span>
                <strong>{RULE_HELP[name]?.name ?? name}</strong>: broken {int(a.count)} times, {int(a.excess)} over the limit.{' '}
                {RULE_HELP[name]?.text}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
