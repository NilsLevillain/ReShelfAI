import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { App } from '../App';
import { DataSourceProvider } from '../data/DataSource';
import { GlobePanel } from '../stock/GlobePanel';
import { WhyPanel } from './WhyPanel';
import type { Result } from './model';

const result = precomputed as unknown as Result;

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('globe panel', () => {
  it('lists every plant with its value at risk and says so when WebGL is missing', () => {
    render(<GlobePanel geo={result.geo} onSelect={() => undefined} webgl={false} />);
    expect(screen.getByTestId('globe-fallback')).toBeInTheDocument();
    expect(screen.queryByTestId('globe')).toBeNull();
    const rows = within(screen.getByTestId('plant-table')).getAllByRole('row');
    expect(rows).toHaveLength(result.geo.plants.length + 1);
  });

  it('filters the stock table on a plant and clears it again', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    render(
      <MemoryRouter initialEntries={['/stock']}>
        <DataSourceProvider initial="cached">
          <App />
        </DataSourceProvider>
      </MemoryRouter>,
    );
    await screen.findByTestId('stock-table');
    const plant = result.geo.plants[0].plant;
    const total = result.stock.lots.length;
    const expected = result.stock.lots.filter((l) => l.plant === plant).length;
    expect(expected).toBeLessThan(total);

    await userEvent.click(screen.getByRole('button', { name: `Filter stock on plant ${plant}` }));
    expect(screen.getByTestId('filter-chips')).toHaveTextContent(plant);
    expect(screen.getByText(new RegExp(`Units in ${expected} lots`))).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: `Clear plant ${plant}` }));
    expect(screen.getByText(new RegExp(`Units in ${total} lots`))).toBeInTheDocument();
  });
});

describe('why panel, live cost', () => {
  const line = result.trace.lines.find((l) => l.binding.some((b) => !b.instance.startsWith('sku[')))!;

  it('asks the live solver for the cost when the cache does not hold it', async () => {
    const answer = {
      base_destroyed: 10, base_objective: 100, constraint: 'cap', cost_eur: 1234, instance: 'x', message: 'Solved.',
      mip_gap: 0, mode: 'plus_10pct', relaxed_destroyed: 5, relaxed_objective: 110, status: 'optimal',
      time_limit_s: 10, time_s: 1, units_destroyed_by_rule: -5,
    };
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify(answer))));
    vi.stubGlobal('fetch', fetchMock);
    render(<WhyPanel result={{ ...result, counterfactuals: [] }} line={line} liveResultId={7} onClose={() => undefined} />);

    await userEvent.click(screen.getAllByRole('button', { name: 'Relax by 10%' })[0]);
    await waitFor(() => expect(screen.getAllByTestId('counterfactual-result')[0]).toHaveTextContent('Relax by 10%'));
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toContain('/results/7/lines/');
    expect(url.endsWith('/counterfactual')).toBe(true);
    expect(JSON.parse(init.body as string).mode).toBe('plus_10pct');
  });

  it('shows a failed request inline with a retry', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify({ detail: 'That rule cannot be relaxed.' }), { status: 422 }))));
    render(<WhyPanel result={{ ...result, counterfactuals: [] }} line={line} liveResultId={7} onClose={() => undefined} />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Switch off' })[0]);
    expect(await screen.findByTestId('inline-error')).toHaveTextContent('That rule cannot be relaxed.');
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('keeps the sentence in cached mode', () => {
    render(<WhyPanel result={{ ...result, counterfactuals: [] }} line={line} onClose={() => undefined} />);
    expect(screen.getByTestId('why-panel')).toHaveTextContent('not in the cached results');
  });
});
