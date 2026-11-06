import { SCENARIOS, type ScenarioName } from '../data/source';

const LABEL: Record<ScenarioName, string> = {
  default: 'Default',
  luxury_protection: 'Luxury protection',
};

export type Choice = ScenarioName | 'run';

export function ScenarioSwitch({
  value,
  onChange,
  runName,
}: {
  value: Choice;
  onChange: (s: Choice) => void;
  runName?: string;
}) {
  return (
    <div className="rs-seg" role="group" aria-label="Scenario">
      {SCENARIOS.map((s) => (
        <button key={s} type="button" aria-pressed={value === s} onClick={() => onChange(s)}>
          {LABEL[s]}
        </button>
      ))}
      {runName && (
        <button type="button" aria-pressed={value === 'run'} onClick={() => onChange('run')} data-testid="switch-run">
          Your run: {runName}
        </button>
      )}
    </div>
  );
}
