import { useState } from 'react';
import { eur } from '../stock/model';
import {
  MODE_WORDS,
  REASON_WORDS,
  counterfactualsFor,
  ruleName,
  signedInt,
  type LineTrace,
  type Result,
} from './model';

export function WhyPanel({ result, line, onClose }: { result: Result; line: LineTrace; onClose: () => void }) {
  const [shown, setShown] = useState<string | null>(null);

  return (
    <aside className="rs-card" data-testid="why-panel" aria-label={`Why ${line.line}`}>
      <div className="rs-toolbar">
        <h3>Why this line</h3>
        <button type="button" className="rs-btn" onClick={onClose}>
          Close
        </button>
      </div>
      <p>
        {line.quantity} units of lot <code>{line.lot}</code> go to <code>{line.channel}</code>.
      </p>

      <h4>Rules that limit this line</h4>
      {line.binding.length === 0 ? (
        <p>No rule is binding for this line.</p>
      ) : (
        <ul className="rs-chips" data-testid="rule-trace">
          {line.binding.map((b) => (
            <li key={b.instance} className="rs-chip" title={b.instance}>
              {ruleName(b.constraint)} <code>{b.instance}</code> slack {b.slack}
            </li>
          ))}
        </ul>
      )}

      <h4>Channels blocked for this lot</h4>
      {line.blocked.length === 0 ? (
        <p>No channel is blocked for this lot.</p>
      ) : (
        <ul>
          {line.blocked.map((b) => (
            <li key={b.channel}>
              <code>{b.channel}</code>:{' '}
              {b.reasons.map((r) => (
                <span key={r}>
                  <code>{r}</code> {REASON_WORDS[r] ?? ''}{' '}
                </span>
              ))}
            </li>
          ))}
        </ul>
      )}

      <h4>What a rule costs</h4>
      {line.binding.map((b) => {
        const cfs = counterfactualsFor(result, b.instance);
        return (
          <div key={b.instance}>
            {cfs.length === 0 ? (
              <p>
                <code>{b.instance}</code>: the cost of this rule is not in the cached results. The live solver computes it on
                demand.
              </p>
            ) : (
              <>
                <button type="button" className="rs-btn" data-testid="counterfactual-button" onClick={() => setShown(b.instance)}>
                  Relax this rule
                </button>{' '}
                <code>{b.instance}</code>
                {shown === b.instance && (
                  <ul data-testid="counterfactual-result">
                    {cfs.map((c) => (
                      <li key={c.mode}>
                        {MODE_WORDS[c.mode] ?? c.mode}: <strong style={{ color: 'var(--rs-compare-delta-cost)' }}>{eur(c.cost_eur)}</strong>{' '}
                        more value recovered, {signedInt(c.units_destroyed_by_rule)} units destroyed ({c.status}).
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        );
      })}
    </aside>
  );
}
