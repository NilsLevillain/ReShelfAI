import { useState } from 'react';
import { InlineError } from '../components/InlineError';
import { ScenarioSwitch, type Choice } from '../components/ScenarioSwitch';
import { useChoiceResult } from '../data/useScenarioResult';
import { useRun } from '../data/run';
import { liveApi } from '../data/live';
import { Charts } from '../results/Charts';
import { RuleDial } from '../results/RuleDial';
import { SolverStatus } from '../results/SolverStatus';
import { WhyPanel } from '../results/WhyPanel';
import { eur, int } from '../stock/model';

export function Results() {
  const { run } = useRun();
  const [scenario, setScenario] = useState<Choice>(run ? 'run' : 'default');
  const [lineId, setLineId] = useState<string | null>(null);
  const state = useChoiceResult(scenario);

  const switcher = (
    <ScenarioSwitch
      value={scenario}
      runName={run?.name}
      onChange={(s) => {
        setScenario(s);
        setLineId(null);
      }}
    />
  );
  if (state.status === 'loading')
    return (
      <>
        {switcher}
        <p role="status">Loading results</p>
      </>
    );
  if (state.status === 'error')
    return (
      <>
        {switcher}
        <InlineError error={state.error} onRetry={state.retry} />
      </>
    );

  const r = state.result;
  const line = r.trace.lines.find((l) => l.line === lineId);
  const lineRows = [...r.lines].sort((a, b) => b.net_value_eur - a.net_value_eur);

  return (
    <>
      <section className="rs-page-head">
        <h2>What the plan does with the stock</h2>
        <SolverStatus solve={r.solve} />
      </section>
      {switcher}
      <div className="rs-actions" data-testid="export-step">
        {scenario === 'run' && run ? (
          <a className="rs-btn rs-btn--primary" href={liveApi.exportUrl(run.scenarioId)} download data-testid="export-xlsx">
            Download Excel
          </a>
        ) : (
          <>
            <button type="button" className="rs-btn" disabled data-testid="export-xlsx">
              Download Excel
            </button>
            <span>The export needs the live solver and a run of your own. Open Parameters and run one.</span>
          </>
        )}
      </div>

      <div className="rs-cards rs-cards--stat">
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{eur(r.optimizer.value_recovered)}</span>
          <span>Value recovered, optimizer</span>
          <span>
            {eur(r.baseline.compliant.value_recovered)} against the greedy baseline (compliant plan)
          </span>
        </div>
        <div className="rs-card rs-stat" data-testid="kpi-units-destroyed">
          <span className="rs-stat__value">{int(r.optimizer.units_destroyed)}</span>
          <span>Units destroyed, optimizer</span>
          <span>{int(r.baseline.compliant.units_destroyed)} against the greedy baseline (compliant plan)</span>
        </div>
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{int(r.optimizer.units_allocated)}</span>
          <span>Units placed in second life channels</span>
        </div>
      </div>

      <Charts result={r} />

      <RuleDial key={scenario} result={r} />

      <section>
        <h3>Allocation lines</h3>
        <div className="rs-table-scroll">
          <table className="rs-table" data-testid="lines-table">
            <thead>
              <tr>
                <th>Lot</th>
                <th>Channel</th>
                <th className="rs-num">Units</th>
                <th className="rs-num">Net value</th>
                <th>Why</th>
              </tr>
            </thead>
            <tbody>
              {lineRows.map((l) => (
                <tr key={l.line}>
                  <th scope="row">{l.lot}</th>
                  <td>{l.channel}</td>
                  <td className="rs-num">{int(l.quantity)}</td>
                  <td className="rs-num">{eur(l.net_value_eur)}</td>
                  <td>
                    <button type="button" className="rs-btn" aria-label={`Why ${l.line}`} onClick={() => setLineId(l.line)}>
                      Why
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {line && (
        <WhyPanel
          key={line.line}
          result={r}
          line={line}
          liveResultId={scenario === 'run' ? run?.resultId : undefined}
          onClose={() => setLineId(null)}
        />
      )}
    </>
  );
}
