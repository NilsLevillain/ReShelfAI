import { useId, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { KPI_HELP, PARAM_HELP, RULE_CHOICE_HELP } from '../glossary';

/**
 * Small info button with a short explanation. It opens on hover, on keyboard focus and on click,
 * and Escape closes it. The explanation text always comes from `glossary.ts`.
 */
export function Hint({ label, children }: { label: string; children: ReactNode }) {
  const id = useId();
  const [over, setOver] = useState(false);
  const [pinned, setPinned] = useState(false);
  const open = over || pinned;
  return (
    <span
      className="rs-hint"
      onMouseEnter={() => setOver(true)}
      onMouseLeave={() => setOver(false)}
      onFocus={() => setOver(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
          setOver(false);
          setPinned(false);
        }
      }}
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          setOver(false);
          setPinned(false);
        }
      }}
    >
      <button
        type="button"
        className="rs-hint__btn"
        aria-label={`About: ${label}`}
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setPinned((p) => !p)}
      >
        i
      </button>
      {open && (
        <span className="rs-hint__panel" id={id} role="note">
          {children}
        </span>
      )}
    </span>
  );
}

/** The explanation of one rules page parameter: what it does, what raising or lowering it causes, how to pick a value. */
export function ParamHint({ k }: { k: string }) {
  const help = PARAM_HELP[k];
  if (!help) return null;
  return (
    <Hint label={help.name}>
      <p>{help.text}</p>
      <dl>
        <dt>If you raise it</dt>
        <dd>{help.raise}</dd>
        <dt>If you lower it</dt>
        <dd>{help.lower}</dd>
        <dt>Allowed values</dt>
        <dd>{help.range}</dd>
        <dt>How to choose</dt>
        <dd>{help.how}</dd>
      </dl>
      <Link className="rs-hint__more" to={`/glossary#${k}`}>
        Open the glossary
      </Link>
    </Hint>
  );
}

export function RuleHint({ k }: { k: string }) {
  const help = RULE_CHOICE_HELP[k];
  return help ? (
    <Hint label={help.name}>
      <p>{help.text}</p>
    </Hint>
  ) : null;
}

export function KpiHint({ k }: { k: string }) {
  const help = KPI_HELP[k];
  if (!help) return null;
  return (
    <Hint label={help.name}>
      <p>{help.text}</p>
      <p>{help.better === 'up' ? 'Higher is better.' : 'Lower is better.'}</p>
      <Link className="rs-hint__more" to={`/glossary#${k}`}>
        Open the glossary
      </Link>
    </Hint>
  );
}
