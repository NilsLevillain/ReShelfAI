import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { App } from '../App';
import { DataSourceProvider } from '../data/DataSource';
import { applyFilters, groupLots, sharePct, totalsOf, type StockLot } from './model';

const lots = precomputed.stock.lots as StockLot[];

function renderStock() {
  return render(
    <MemoryRouter initialEntries={['/stock']}>
      <DataSourceProvider initial="cached">
        <App />
      </DataSourceProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('stock model', () => {
  it('totals add up and groups reconcile with the whole', () => {
    const t = totalsOf(lots);
    expect(t.valueAtRisk).toBeCloseTo(precomputed.stock.summary.value_at_risk, 0);
    for (const by of ['brand', 'category', 'reason', 'plant'] as const) {
      const groups = groupLots(lots, by);
      expect(groups.reduce((s, g) => s + g.totals.units, 0)).toBe(t.units);
    }
  });

  it('filters combine', () => {
    const brand = lots[0].brand;
    const rows = applyFilters(lots, { brand });
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((l) => l.brand === brand)).toBe(true);
    expect(applyFilters(lots, { brand, reason: 'no_such_reason' })).toEqual([]);
  });

  it('share is 0 for an empty lot', () => {
    expect(sharePct(5, 0)).toBe(0);
    expect(sharePct(1, 4)).toBe(25);
  });
});

describe('stock page', () => {
  it('shows value at risk from the precomputed file and a totals row', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    renderStock();
    const tile = await screen.findByTestId('kpi-value-at-risk');
    expect(tile.textContent).toMatch(/€/);
    expect(screen.getByTestId('total-row')).toHaveTextContent(`Total (${lots.length} lots)`);
  });

  it('a click on a reason bar adds a filter chip and narrows the table', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    renderStock();
    const bars = await screen.findByTestId('reason-bars');
    await userEvent.click(within(bars).getAllByRole('button')[0]);
    expect(screen.getByTestId('filter-chips')).toBeInTheDocument();
    const rows = within(screen.getByTestId('stock-table')).getAllByRole('row');
    expect(rows.length).toBeLessThan(lots.length + 2);
    await userEvent.click(within(screen.getByTestId('filter-chips')).getAllByRole('button')[0]);
    expect(screen.queryByTestId('filter-chips')).toBeNull();
  });

  it('drills from brand to category and back', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    renderStock();
    const drill = await screen.findByTestId('drill-bars');
    const first = within(drill).getAllByRole('button')[0];
    const brand = first.querySelector('.rs-hbar__label')!.textContent!;
    await userEvent.click(first);
    expect(screen.getByLabelText('Drill')).toHaveTextContent(brand);
    await userEvent.click(screen.getByRole('button', { name: 'All brands' }));
    expect(screen.queryByTestId('filter-chips')).toBeNull();
  });

  it('groups rows with subtotals and hides a column group', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    renderStock();
    await screen.findByTestId('stock-table');
    await userEvent.selectOptions(screen.getByLabelText('Group by'), 'brand');
    expect(screen.getAllByTestId('group-row').length).toBeGreaterThan(1);
    await userEvent.click(screen.getByRole('button', { name: 'Value' }));
    expect(screen.queryByRole('columnheader', { name: 'Value at risk' })).toBeNull();
  });

  it('shows an inline error with the endpoint and retries', async () => {
    const f = vi
      .fn()
      .mockResolvedValueOnce(new Response('{}', { status: 500 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(precomputed)));
    vi.stubGlobal('fetch', f);
    renderStock();
    expect(await screen.findByTestId('inline-error')).toHaveTextContent('The server answered 500');
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() => expect(screen.getByTestId('stock-table')).toBeInTheDocument());
  });
});
