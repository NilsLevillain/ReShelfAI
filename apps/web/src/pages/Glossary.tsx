import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  CAUSE_HELP,
  CHANNEL_TYPES,
  KPI_HELP,
  PARAM_HELP,
  REASON_HELP,
  RULE_CHOICE_HELP,
  RULE_HELP,
  SCENARIO_INFO,
  STOCK_REASON_HELP,
} from '../glossary';

type Entry = { id: string; term: string; text: string };

function Section({ title, intro, entries }: { title: string; intro?: string; entries: Entry[] }) {
  return (
    <section className="rs-card" aria-label={title}>
      <h3>{title}</h3>
      {intro && <p className="rs-section__sub">{intro}</p>}
      <dl className="rs-glossary">
        {entries.map((e) => (
          <div key={e.id}>
            <dt id={e.id}>{e.term}</dt>
            <dd>{e.text}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/** Every word of the app in one place. It reads `glossary.ts`, the same source as the tooltips. */
export function Glossary() {
  const { hash } = useLocation();
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView({ block: 'center' });
  }, [hash]);

  const params: Entry[] = Object.entries(PARAM_HELP).map(([id, h]) => ({
    id,
    term: h.name,
    text: `${h.text} If you raise it: ${h.raise} If you lower it: ${h.lower} ${h.range} How to choose: ${h.how}`,
  }));
  return (
    <div className="rs-stack">
      <section className="rs-page-head">
        <h2>Glossary</h2>
        <p className="rs-section__sub">
          The words of Reshelf in plain language. The goal is always the same: a plan the brand can accept, so that stock is not
          destroyed. Every figure is simulated.
        </p>
      </section>
      <Section
        title="Numbers you can change"
        intro="On the Rules and run page. Change one value at a time to see what it does to the plan."
        entries={params}
      />
      <Section
        title="Results"
        entries={Object.entries(KPI_HELP).map(([id, h]) => ({
          id,
          term: h.name,
          text: `${h.text} ${h.better === 'up' ? 'Higher is better.' : 'Lower is better.'}`,
        }))}
      />
      <Section
        title="Why stock is destroyed"
        intro="Shown on the Plan page. Each unit that is not placed has one main reason."
        entries={Object.entries(CAUSE_HELP).map(([id, h]) => ({ id, term: h.title, text: h.text }))}
      />
      <Section
        title="Rules in the plan"
        entries={Object.entries(RULE_HELP).map(([id, h]) => ({ id: `rule-${id}`, term: h.name, text: h.text }))}
      />
      <Section
        title="Rules that apply by hand"
        entries={Object.entries(RULE_CHOICE_HELP).map(([id, h]) => ({ id: `hand-${id}`, term: h.name, text: h.text }))}
      />
      <Section
        title="Why a channel is closed to a lot"
        entries={Object.entries(REASON_HELP).map(([id, text]) => ({ id: `reason-${id}`, term: id, text }))}
      />
      <Section
        title="Why stock is at risk"
        entries={Object.entries(STOCK_REASON_HELP).map(([id, text]) => ({ id: `stock-${id}`, term: id.replace('_', ' '), text }))}
      />
      <Section
        title="Channels"
        entries={Object.entries(CHANNEL_TYPES).map(([id, h]) => ({ id: `channel-${id}`, term: h.name, text: h.text }))}
      />
      <Section
        title="Scenarios"
        intro="Ready made sets of rules. Open two of them on the Compare page."
        entries={Object.entries(SCENARIO_INFO).map(([id, h]) => ({ id: `scenario-${id}`, term: h.name, text: h.story }))}
      />
    </div>
  );
}
