import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { App } from './App';
import { CurrencyProvider } from './data/currency';
import { DataSourceProvider } from './data/DataSource';
import { channelInfo, ruleLabel, solverSentence } from './glossary';
import type { Result } from './results/model';

const result = precomputed as unknown as Result;

describe('glossary', () => {
  it('names a channel by its type and country', () => {
    const c = result.geo.channels[0];
    const info = channelInfo(c.channel, result.geo.channels);
    expect(info.name).not.toBe(c.channel);
    expect(info.text.length).toBeGreaterThan(0);
  });

  it('turns a rule instance into words and keeps unknown parts', () => {
    const c = result.geo.channels[0].channel;
    expect(ruleLabel(`sku[${c}]`, result.geo.channels)).toContain('Channel limit on SKUs');
    expect(ruleLabel('weird', result.geo.channels)).toBe('weird');
  });

  it('says in one sentence what the solver status means', () => {
    expect(solverSentence({ ...result.solve, status: 'optimal' })).toMatch(/best/);
    expect(solverSentence({ ...result.solve, status: 'infeasible' })).toMatch(/Relax a rule/);
  });
});

describe('currency selector', () => {
  it('changes how amounts are shown, not the amounts', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    render(
      <MemoryRouter initialEntries={['/stock']}>
        <DataSourceProvider initial="cached">
          <CurrencyProvider>
            <App />
          </CurrencyProvider>
        </DataSourceProvider>
      </MemoryRouter>,
    );
    const tile = await screen.findByTestId('kpi-value-at-risk');
    expect(tile.textContent).toContain('€');
    await userEvent.selectOptions(screen.getByLabelText('Show amounts in'), 'USD');
    expect(screen.getByTestId('kpi-value-at-risk').textContent).toContain('US$');
    vi.unstubAllGlobals();
    localStorage.removeItem('reshelf-currency');
  });
});
