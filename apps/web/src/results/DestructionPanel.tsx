import type { CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import type { components } from '../api/schema';
import { useMoney } from '../data/currency';
import { CAUSE_HELP, LEVER_FIELD } from '../glossary';
import { int } from '../stock/model';

type Destruction = components['schemas']['DestructionOut'];

/**
 * Why units are destroyed, by cause, with the rule a planner can change for each cause.
 * Everything comes from the `destruction` block of the result, nothing is recomputed here.
 */
export function DestructionPanel({ destruction }: { destruction: Destruction }) {
  const { compact, money } = useMoney();
  const d = destruction;
  if (d.units_destroyed === 0)
    return (
      <section className="rs-card" data-testid="destruction">
        <h3>Why is stock destroyed?</h3>
        <p>The plan places every unit. Nothing is destroyed.</p>
      </section>
    );
  const percent = Math.round((d.units_destroyed / d.units_at_risk) * 100);
  return (
    <section className="rs-card rs-stack" data-testid="destruction">
      <div>
        <h3>Why is stock destroyed?</h3>
        <p className="rs-section__sub">
          {int(d.units_destroyed)} of {int(d.units_at_risk)} units ({percent} percent) are not placed. At cost that is{' '}
          <span title={money(d.value_destroyed)}>{compact(d.value_destroyed)}</span>. Each unit has one main reason, listed from the biggest.
        </p>
      </div>
      <div className="rs-causebar" role="img" aria-label="Destroyed units by cause">
        {d.causes.map((c) => (
          <span key={c.cause} data-cause={c.cause} style={{ '--rs-share': c.share } as CSSProperties} title={CAUSE_HELP[c.cause]?.title ?? c.cause} />
        ))}
      </div>
      <ul className="rs-causes">
        {d.causes.map((c) => {
          const help = CAUSE_HELP[c.cause];
          return (
            <li key={c.cause} className="rs-cause" data-cause={c.cause} data-testid={`cause-${c.cause}`}>
              <div>
                <h4>{help?.title ?? c.cause}</h4>
                <p>{help?.text}</p>
                {c.top_materials.length > 0 && (
                  <p>
                    Biggest: {c.top_materials.map((m) => `${m.description} (${int(m.units)})`).join(', ')}.
                  </p>
                )}
              </div>
              <span className="rs-cause__num">
                {int(c.units)} units
                <small>
                  {Math.round(c.share * 100)} percent, {compact(c.value_at_risk)} at cost
                </small>
              </span>
              {c.lever && help?.action && (
                <div className="rs-cause__action">
                  <Link className="rs-btn" to={`/parameters?lever=${c.lever}`}>
                    {help.action}
                  </Link>
                  <span className="rs-note"> Opens the rules page at: {LEVER_FIELD[c.lever]}.</span>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
