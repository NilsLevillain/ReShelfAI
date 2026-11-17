import { SCENARIOS, type ScenarioName } from '../data/source';
import { SCENARIO_INFO } from '../glossary';

export const SCENARIO_LABEL = Object.fromEntries(SCENARIOS.map((s) => [s, SCENARIO_INFO[s].name])) as Record<ScenarioName, string>;

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
          {SCENARIO_LABEL[s]}
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
