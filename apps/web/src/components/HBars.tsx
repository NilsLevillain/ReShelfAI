import type { CSSProperties } from 'react';

export type BarItem = { key: string; label: string; value: number; text: string };

/** Horizontal bars. The value is always printed, color is never the only signal. */
export function HBars({
  items,
  onSelect,
  selected,
  testId,
}: {
  items: BarItem[];
  onSelect?: (key: string) => void;
  selected?: string;
  testId?: string;
}) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <ul className="rs-hbars" data-testid={testId}>
      {items.map((it, i) => {
        const style = {
          '--rs-share': `${(it.value / max) * 100}%`,
          '--rs-bar-color': `var(--rs-chart-categorical-${(i % 5) + 1})`,
        } as CSSProperties;
        const body = (
          <>
            <span className="rs-hbar__label">{it.label}</span>
            <span className="rs-hbar__track">
              <span className="rs-hbar__fill" style={style} />
            </span>
            <span className="rs-hbar__value">{it.text}</span>
          </>
        );
        return (
          <li key={it.key}>
            {onSelect ? (
              <button type="button" className="rs-hbar" aria-pressed={selected === it.key} onClick={() => onSelect(it.key)}>
                {body}
              </button>
            ) : (
              <div className="rs-hbar">{body}</div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
