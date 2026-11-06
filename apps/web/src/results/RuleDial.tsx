import { useState } from 'react';
import { eur } from '../stock/model';
import { MODE_WORDS, counterfactualsFor, ruleInstances, ruleName, type Result } from './model';

/**
 * Read only dial on a precomputed grid: current value, relaxed by 10 percent, switched off.
 * Each position shows the cost that the solver measured. Nothing is recomputed here.
 */
export function RuleDial({ result }: { result: Result }) {
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

  return (
    <section className="rs-card" data-testid="rule-dial" aria-label="Rule dial">
      <h3>Relax a rule and see what it is worth</h3>
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
              {i}
            </option>
          ))}
        </select>
      </label>
      <p>
        {ruleName(constraint)}: <strong>{step.label}</strong>
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
        <span className="rs-text-kpi-hero" data-testid="euro-delta" style={{ color: 'var(--rs-compare-delta-cost)' }}>
          {eur(step.cost)}
        </span>{' '}
        cost of this rule
      </p>
      <p>Precomputed with the solver, against the greedy baseline plan of the same world.</p>
    </section>
  );
}
