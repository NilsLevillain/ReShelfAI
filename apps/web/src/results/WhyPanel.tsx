import { useEffect, useRef, useState } from 'react';
import { InlineError } from '../components/InlineError';
import { useMoney } from '../data/currency';
import { liveApi, type CounterfactualOut } from '../data/live';
import { REASON_HELP, RULE_HELP, channelInfo, ruleLabel } from '../glossary';
import { MODE_WORDS, counterfactualsFor, signedInt, type LineTrace, type Result } from './model';

/** Cost of one rule, asked from the live solver when the cached results do not hold it. */
function LiveCost({ resultId, line, instance }: { resultId: number; line: string; instance: string }) {
  const { money } = useMoney();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [found, setFound] = useState<Record<string, CounterfactualOut>>({});

  const ask = (mode: string) => {
    setBusy(mode);
    setError(null);
    liveApi.counterfactual(resultId, line, instance, mode).then(
      (c) => {
        setFound((f) => ({ ...f, [mode]: c }));
        setBusy(null);
      },
      (e: Error) => {
        setError(e);
        setBusy(null);
      },
    );
  };

  return (
    <div data-testid="live-cost" className="rs-actions">
      {Object.entries(MODE_WORDS).map(([mode, words]) => (
        <button key={mode} type="button" className="rs-btn" disabled={busy !== null} onClick={() => ask(mode)}>
          {busy === mode ? 'Solving' : words}
        </button>
      ))}
      {error && <InlineError error={error} onRetry={() => setError(null)} />}
      <ul data-testid="counterfactual-result">
        {Object.values(found).map((c) => (
          <li key={c.mode}>
            {MODE_WORDS[c.mode] ?? c.mode}: <span className="rs-cost">{money(c.cost_eur)}</span> more value recovered,{' '}
            {signedInt(c.units_destroyed_by_rule)} units destroyed ({c.status}). {c.message}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Side drawer: why one allocation line exists, in business words. Closes on Escape, backdrop or Close. */
export function WhyPanel({
  result,
  line,
  liveResultId,
  onClose,
}: {
  result: Result;
  line: LineTrace;
  liveResultId?: number;
  onClose: () => void;
}) {
  const { money } = useMoney();
  const [shown, setShown] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const channels = result.geo.channels;
  const channel = channelInfo(line.channel, channels);
  const lot = result.stock.lots.find((l) => l.lot === line.lot);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <>
      <div className="rs-drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside className="rs-drawer" role="dialog" aria-modal="true" data-testid="why-panel" aria-label={`Why ${line.line}`}>
        <div className="rs-toolbar">
          <h3>Why this line is in the plan</h3>
          <button ref={closeRef} type="button" className="rs-btn" onClick={onClose}>
            Close
          </button>
        </div>
        <p>
          <strong>{line.quantity} units</strong> of {lot ? lot.description : 'this lot'} <span className="rs-tag">{line.lot}</span>{' '}
          go to <strong>{channel.name}</strong>.
        </p>
        {channel.text && <p className="rs-note">{channel.text}</p>}

        <h4>What limits this line</h4>
        {line.binding.length === 0 ? (
          <p>No rule limits this line. It could grow if there were more stock.</p>
        ) : (
          <ul data-testid="rule-trace">
            {line.binding.map((b) => {
              const kind = /^(\w+)\[/.exec(b.instance)?.[1] ?? b.constraint;
              return (
                <li key={b.instance} className="rs-drawer__why" title={b.instance}>
                  <b>{ruleLabel(b.instance, channels)}</b>
                  <span>{RULE_HELP[kind]?.text ?? ''} It is used up, so the plan cannot send more here.</span>
                </li>
              );
            })}
          </ul>
        )}

        <h4>Other channels this lot cannot go to</h4>
        {line.blocked.length === 0 ? (
          <p>Every channel can take this lot.</p>
        ) : (
          <ul>
            {line.blocked.map((b) => (
              <li key={b.channel} className="rs-drawer__why">
                <b>{channelInfo(b.channel, channels).name}</b>
                {b.reasons.map((r) => (
                  <span key={r}>{REASON_HELP[r] ?? r}</span>
                ))}
              </li>
            ))}
          </ul>
        )}

        <h4>What relaxing a rule is worth</h4>
        {line.binding.length === 0 && <p>No rule to relax for this line.</p>}
        {line.binding.map((b) => {
          const cfs = counterfactualsFor(result, b.instance);
          const label = ruleLabel(b.instance, channels);
          return (
            <div key={b.instance} className="rs-drawer__why">
              <b>{label}</b>
              {cfs.length === 0 && liveResultId !== undefined ? (
                <LiveCost resultId={liveResultId} line={line.line} instance={b.instance} />
              ) : cfs.length === 0 ? (
                <span>The value of this rule is not in the cached results. The live solver computes it on demand.</span>
              ) : (
                <>
                  <div>
                    <button type="button" className="rs-btn" data-testid="counterfactual-button" onClick={() => setShown(b.instance)}>
                      Show what this rule is worth
                    </button>
                  </div>
                  {shown === b.instance && (
                    <ul data-testid="counterfactual-result">
                      {cfs.map((c) => (
                        <li key={c.mode}>
                          {MODE_WORDS[c.mode] ?? c.mode}: <span className="rs-cost">{money(c.cost_eur)}</span> more value recovered.
                          {c.units_destroyed_by_rule > 0 && ` ${signedInt(c.units_destroyed_by_rule)} units destroyed.`}
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
    </>
  );
}
