import { useState } from 'react';
import { InlineError } from '../components/InlineError';
import { ScenarioSwitch, type Choice } from '../components/ScenarioSwitch';
import { useChoiceResult } from '../data/useScenarioResult';
import { useRun } from '../data/run';
import { liveApi } from '../data/live';
import { BaselineCompare } from '../results/BaselineCompare';
import { Charts } from '../results/Charts';
import { RuleDial } from '../results/RuleDial';
import { SolverStatus } from '../results/SolverStatus';
import { WhyPanel } from '../results/WhyPanel';
import { useMoney } from '../data/currency';
import { CHANNEL_TYPES, channelInfo } from '../glossary';
import { int } from '../stock/model';

export function Results() {
  const { run } = useRun();
  const [scenario, setScenario] = useState<Choice>(run ? 'run' : 'default');
  const [lineId, setLineId] = useState<string | null>(null);
  const { money: eur, compact } = useMoney();
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
    <div className="rs-stack">
      <section className="rs-page-head">
        <h2>The plan: where the stock goes</h2>
        <p className="rs-section__sub">
          Each line sends a lot to a channel that can take it, within your rules. Open any line to see why it is there.
        </p>
        <SolverStatus solve={r.solve} />
      </section>
      <div className="rs-toolbar" data-testid="export-step">
        {switcher}
        {scenario === 'run' && run ? (
          <a className="rs-btn rs-btn--primary" href={liveApi.exportUrl(run.scenarioId)} download data-testid="export-xlsx">
            Download the plan as Excel
          </a>
        ) : (
          <div className="rs-actions">
            <button type="button" className="rs-btn" disabled data-testid="export-xlsx">
              Download the plan as Excel
            </button>
            <span className="rs-note">To export, run a plan of your own on the Rules and run page.</span>
          </div>
        )}
      </div>

      <div className="rs-cards rs-cards--stat">
        <div className="rs-card rs-stat">
          <span className="rs-stat__value" title={eur(r.optimizer.value_recovered)}>
            {compact(r.optimizer.value_recovered)}
          </span>
          <span>Value recovered by the plan</span>
          <span className="rs-stat__hint">{eur(r.baseline.compliant.value_recovered)} against the greedy baseline (compliant plan)</span>
        </div>
        <div className="rs-card rs-stat" data-testid="kpi-units-destroyed">
          <span className="rs-stat__value">{int(r.optimizer.units_destroyed)}</span>
          <span>Units still destroyed</span>
          <span className="rs-stat__hint">{int(r.baseline.compliant.units_destroyed)} against the greedy baseline (compliant plan)</span>
        </div>
        <div className="rs-card rs-stat">
          <span className="rs-stat__value">{int(r.optimizer.units_allocated)}</span>
          <span>Units given a second life</span>
        </div>
      </div>

      <details className="rs-more">
        <summary>What are these channels?</summary>
        <ul className="rs-list">
          {r.geo.channels.map((c) => {
            const i = channelInfo(c.channel, r.geo.channels);
            return (
              <li key={c.channel}>
                <span>
                  <strong>{i.name}</strong> <span className="rs-tag">{c.channel}</span>. {CHANNEL_TYPES[c.type]?.text}
                </span>
              </li>
            );
          })}
        </ul>
      </details>

      <Charts result={r} />

      <RuleDial key={scenario} result={r} />

      <section>
        <h3>Plan lines</h3>
        <p className="rs-section__sub">One line per lot and channel, best value first.</p>
        <div className="rs-table-scroll">
          <table className="rs-table" data-testid="lines-table">
            <thead>
              <tr>
                <th>Lot</th>
                <th>Channel</th>
                <th className="rs-num">Units</th>
                <th className="rs-num">Net value</th>
                <th>Why this line</th>
              </tr>
            </thead>
            <tbody>
              {lineRows.map((l) => (
                <tr key={l.line}>
                  <th scope="row">{l.lot}</th>
                  <td>
                    {channelInfo(l.channel, r.geo.channels).name} <span className="rs-tag">{l.channel}</span>
                  </td>
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

      <BaselineCompare result={r} />

      {line && (
        <WhyPanel
          key={line.line}
          result={r}
          line={line}
          liveResultId={scenario === 'run' ? run?.resultId : undefined}
          onClose={() => setLineId(null)}
        />
      )}
    </div>
  );
}
