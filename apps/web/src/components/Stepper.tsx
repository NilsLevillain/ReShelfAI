export const STEPS = ['Parameters', 'Run', 'Review', 'Export'] as const;

export function Stepper({ current }: { current: number }) {
  return (
    <ol className="rs-stepper" aria-label="Process" data-testid="stepper">
      {STEPS.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'current' : 'upcoming';
        return (
          <li
            key={label}
            className="rs-stepper__item"
            data-state={state}
            aria-current={state === 'current' ? 'step' : undefined}
          >
            <span className="rs-stepper__disc">{state === 'done' ? '✓' : i + 1}</span>
            <span className="rs-stepper__label">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
