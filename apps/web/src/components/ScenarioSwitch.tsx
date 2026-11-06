import { SCENARIOS, type ScenarioName } from '../data/source';

const LABEL: Record<ScenarioName, string> = {
  default: 'Default',
  luxury_protection: 'Luxury protection',
};

export function ScenarioSwitch({ value, onChange }: { value: ScenarioName; onChange: (s: ScenarioName) => void }) {
  return (
    <div className="rs-seg" role="group" aria-label="Scenario">
      {SCENARIOS.map((s) => (
        <button key={s} type="button" aria-pressed={value === s} onClick={() => onChange(s)}>
          {LABEL[s]}
        </button>
      ))}
    </div>
  );
}
