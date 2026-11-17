import { useState } from 'react';
import { useMoney } from '../data/currency';
import { RULE_HELP, ruleLabel } from '../glossary';
import { MODE_WORDS, counterfactualsFor, ruleInstances, type Result } from './model';

/**
 * Read only dial on a precomputed grid: current value, relaxed by 10 percent, switched off.
 * Each position shows the cost that the solver measured. Nothing is recomputed here.
 */
export function RuleDial({ result }: { result: Result }) {
  const { money } = useMoney();
  const instances = ruleInstances(result);
  const [instance, setInstance] = useState(instances[0] ?? '');
  const [pos, setPos] = useState(0);

  if (instances.length === 0) {
    return <p data-testid="rule-dial">No rule cost is in these results.</p>;
  }
  const cfs = counterfactualsFor(result, instance);
  const steps = [{ mode: 'current', label: 'Current value', cost: 0 }, ...cfs.map((c) => ({ mode: c.mode, label: MODE_WORDS[c.mode] ?? c.mode, cost: c.cost_eur }))];
  const step = steps[Math.min(pos, steps.length - 1)];
  const constraint = cfs[0]?.constraint ?? '';
  const help = RULE_HELP[constraint]?.text;

  return (
    <section className="rs-card" data-testid="rule-dial" aria-label="Rule dial">
      <h3>What is a rule worth?</h3>
      <p className="rs-section__sub">
        Pick a rule and loosen it. The number is the extra value the plan would recover. Use it to decide which rule is worth
        a conversation with the brand.
      </p>
      <label className="rs-groupby">
        Rule
        <select
          value={instance}
          onChange={(e) => {
            setInstance(e.target.value);
            setPos(0);
          }}
        >
          {instances.map((i) => (
            <option key={i} value={i}>
              {ruleLabel(i, result.geo.channels)}
            </option>
          ))}
        </select>
      </label>
      <p>
        {help ?? ''} Now: <strong>{step.label}</strong>
      </p>
      <input
        type="range"
        min={0}
        max={steps.length - 1}
        step={1}
        value={Math.min(pos, steps.length - 1)}
        aria-label="Rule value"
        aria-valuetext={step.label}
        onChange={(e) => setPos(Number(e.target.value))}
      />
      <p>
        <span className="rs-cost" data-testid="euro-delta">
          {money(step.cost)}
        </span>{' '}
        extra value recovered
      </p>
      <ul data-testid="rule-worth">
        {cfs.map((c) => (
          <li key={c.mode}>
            {MODE_WORDS[c.mode] ?? c.mode}: <span className="rs-cost">{money(c.cost_eur)}</span>
          </li>
        ))}
      </ul>
      <p className="rs-note">Measured by the solver on this plan. At the current value the extra value is zero, by definition.</p>
    </section>
  );
}
