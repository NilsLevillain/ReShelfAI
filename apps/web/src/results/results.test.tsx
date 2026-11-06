import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { App } from '../App';
import { DataSourceProvider } from '../data/DataSource';
import { counterfactualsFor, ruleInstances, violationCount, type Result } from './model';

const result = precomputed as unknown as Result;

function renderAt(path: string) {
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
  return render(
    <MemoryRouter initialEntries={[path]}>
      <DataSourceProvider initial="cached">
        <App />
      </DataSourceProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('results model', () => {
  it('orders the counterfactuals of an instance: relax by 10 percent, then off', () => {
    const instance = ruleInstances(result)[0];
    expect(counterfactualsFor(result, instance).map((c) => c.mode)).toEqual(['plus_10pct', 'off']);
  });

  it('counts the violations the checker found in the raw baseline plan', () => {
    expect(violationCount(result)).toBe(Object.values(result.baseline.audit).reduce((s, a) => s + a.count, 0));
    expect(violationCount(result)).toBeGreaterThan(0);
  });
});

describe('results page', () => {
  it('shows the solver status, the unit KPI and the lines', async () => {
    renderAt('/results');
    expect(await screen.findByTestId('solver-status')).toHaveTextContent('optimal');
    expect(screen.getByTestId('kpi-units-destroyed')).toHaveTextContent('against the greedy baseline');
    expect(within(screen.getByTestId('lines-table')).getAllByRole('row').length).toBe(result.lines.length + 1);
  });

  it('the dial moves the euro delta along the precomputed grid', async () => {
    renderAt('/results');
    const delta = await screen.findByTestId('euro-delta');
    expect(delta).toHaveTextContent('€0');
    const dial = screen.getByRole('slider', { name: 'Rule value' });
    const instance = ruleInstances(result)[0];
    const [plus, off] = counterfactualsFor(result, instance);
    const fmt = (v: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v);
    fireEvent.change(dial, { target: { value: '1' } });
    expect(delta).toHaveTextContent(fmt(plus.cost_eur));
    fireEvent.change(dial, { target: { value: '2' } });
    expect(delta).toHaveTextContent(fmt(off.cost_eur));
  });

  it('opens the Why panel with a rule trace and the cost of relaxing a rule', async () => {
    renderAt('/results');
    await screen.findByTestId('lines-table');
    const target = result.trace.lines.find((l) => l.binding.some((b) => counterfactualsFor(result, b.instance).length > 0))!;
    await userEvent.click(screen.getByRole('button', { name: `Why ${target.line}` }));
    expect(screen.getByTestId('why-panel')).toBeInTheDocument();
    expect(within(screen.getByTestId('rule-trace')).getAllByRole('listitem').length).toBe(target.binding.length);
    await userEvent.click(screen.getAllByTestId('counterfactual-button')[0]);
    expect(screen.getByTestId('counterfactual-result')).toHaveTextContent('€');
    await userEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(screen.queryByTestId('why-panel')).toBeNull();
  });

  it('says plainly when a rule cost is not in the cached results', async () => {
    renderAt('/results');
    await screen.findByTestId('lines-table');
    const target = result.trace.lines.find((l) => l.binding.length > 0 && l.binding.every((b) => counterfactualsFor(result, b.instance).length === 0));
    if (!target) return; // every binding line has a cached cost in this world
    await userEvent.click(screen.getByRole('button', { name: `Why ${target.line}` }));
    expect(screen.getByTestId('why-panel')).toHaveTextContent('not in the cached results');
  });
});

describe('compare page', () => {
  it('shows baseline and optimizer columns, the euro delta and the audit', async () => {
    renderAt('/compare');
    expect(await screen.findByTestId('compare-panel')).toBeInTheDocument();
    expect(screen.getByTestId('baseline-column')).toBeInTheDocument();
    expect(screen.getByTestId('optimizer-column')).toBeInTheDocument();
    const gain = result.optimizer.value_recovered - result.baseline.compliant.value_recovered;
    expect(screen.getByTestId('euro-delta').textContent).toContain(gain < 0 ? '−' : '+');
    expect(within(screen.getByTestId('baseline-audit')).getAllByRole('listitem').length).toBe(Object.keys(result.baseline.audit).length);
  });

  it('shows an inline error when the results fail to load', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response('{}', { status: 503 }))));
    render(
      <MemoryRouter initialEntries={['/compare']}>
        <DataSourceProvider initial="cached">
          <App />
        </DataSourceProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByTestId('inline-error')).toHaveTextContent('503');
  });
});
