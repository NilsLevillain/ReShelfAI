import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { Hint, ParamHint } from './components/Hint';
import { CurrencyProvider } from './data/currency';
import { CAUSE_HELP, LEVER_FIELD, PARAM_HELP } from './glossary';
import { Glossary } from './pages/Glossary';
import { DestructionPanel } from './results/DestructionPanel';
import type { Result } from './results/model';

const result = precomputed as unknown as Result;

function inRouter(ui: React.ReactElement, path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <CurrencyProvider>{ui}</CurrencyProvider>
    </MemoryRouter>,
  );
}

describe('destruction panel', () => {
  it('lists every cause of the result with its units, in plain words', () => {
    inRouter(<DestructionPanel destruction={result.destruction} />);
    const panel = screen.getByTestId('destruction');
    expect(panel).toHaveTextContent('Why is stock destroyed?');
    for (const c of result.destruction.causes) {
      const row = within(panel).getByTestId(`cause-${c.cause}`);
      expect(row).toHaveTextContent(CAUSE_HELP[c.cause].title);
    }
    const total = result.destruction.causes.reduce((n, c) => n + c.units, 0);
    expect(total).toBe(result.destruction.units_destroyed);
  });

  it('offers a button to the rule that moves a cause', () => {
    inRouter(<DestructionPanel destruction={result.destruction} />);
    const row = screen.getByTestId('cause-coverage_ceiling');
    const link = within(row).getByRole('link', { name: CAUSE_HELP.coverage_ceiling.action });
    expect(link).toHaveAttribute('href', '/parameters?lever=coverage_days');
    expect(row).toHaveTextContent(LEVER_FIELD.coverage_days);
  });

  it('says nothing is destroyed when everything is placed', () => {
    inRouter(
      <DestructionPanel destruction={{ ...result.destruction, units_destroyed: 0, causes: [], value_destroyed: 0 }} />,
    );
    expect(screen.getByTestId('destruction')).toHaveTextContent('Nothing is destroyed');
  });
});

describe('hint', () => {
  it('opens on click, shows what raising and lowering does, closes on Escape', async () => {
    inRouter(<ParamHint k="coverage_days" />);
    expect(screen.queryByRole('note')).toBeNull();
    await userEvent.click(screen.getByRole('button', { name: `About: ${PARAM_HELP.coverage_days.name}` }));
    const note = screen.getByRole('note');
    expect(note).toHaveTextContent(PARAM_HELP.coverage_days.raise);
    expect(note).toHaveTextContent(PARAM_HELP.coverage_days.lower);
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('note')).toBeNull();
  });

  it('opens on keyboard focus', async () => {
    inRouter(<Hint label="Thing">Words</Hint>);
    await userEvent.tab();
    expect(screen.getByRole('note')).toHaveTextContent('Words');
  });

  it('has an explanation for every number of the rules page', () => {
    for (const key of ['coverage_days', 'coverage_alpha', 'score_rank_weight', 'epsilon', 'score_base', 'push_quantity_units', 'planner_rules', 'channel_sku_limit_scale']) {
      const h = PARAM_HELP[key];
      expect(h, key).toBeDefined();
      for (const part of [h.name, h.text, h.raise, h.lower, h.range, h.how]) expect(part.length, key).toBeGreaterThan(10);
    }
  });
});

describe('glossary page', () => {
  it('has an entry for every number, result and cause', () => {
    inRouter(<Glossary />);
    for (const [key, h] of Object.entries(PARAM_HELP)) expect(document.getElementById(key)).toHaveTextContent(h.name);
    for (const [key, h] of Object.entries(CAUSE_HELP)) expect(document.getElementById(key)).toHaveTextContent(h.title);
    expect(document.getElementById('brand_risk_index')).toHaveTextContent('Brand risk index');
  });
});
