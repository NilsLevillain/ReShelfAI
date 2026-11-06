import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { App } from './App';
import { DataSourceProvider } from './data/DataSource';
import type { SourceKind } from './data/source';

const DEFAULTS = {
  coverage_days: 90,
  coverage_alpha: 0.5,
  score_rank_weight: 0.25,
  epsilon: 0.01,
  score_base: { A: 1, B: 0.7, C: 0.4, NEW: 0.55 },
  push_quantity_units: { Fragrance: 5, Skincare: 30 },
  planner_rules: ['rsl', 'tier', 'capacity'],
};

type Saved = { id: number; name: string; base: string; created: string; solved: boolean };

function mockApi(opts: { saved?: Saved[]; failParams?: boolean } = {}) {
  const calls: { url: string; method: string; body?: unknown }[] = [];
  let saved = opts.saved ?? [];
  let failParams = opts.failParams ?? false;
  const reply = (body: unknown, status = 200) => Promise.resolve(new Response(status === 204 ? null : JSON.stringify(body), { status }));
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    calls.push({ url, method, body: init?.body ? JSON.parse(init.body as string) : undefined });
    if (url.endsWith('/params')) {
      if (failParams) {
        failParams = false;
        return reply({ detail: 'The base scenario is missing.' }, 404);
      }
      return reply({ base: 'default', n_skus: 30, n_channels: 5, params: DEFAULTS });
    }
    if (url.endsWith('/solve')) return reply({ result_id: 1, scenario_id: 7, result: precomputed });
    if (method === 'POST' && url.endsWith('/scenarios')) {
      const spec = JSON.parse(init!.body as string);
      saved = [{ id: 7, name: spec.name, base: spec.base, created: '2026-11-06', solved: false }, ...saved];
      return reply({ id: 7, spec }, 201);
    }
    if (method === 'DELETE') {
      saved = saved.filter((s) => !url.endsWith(`/${s.id}`));
      return reply(null, 204);
    }
    if (url.endsWith('/scenarios')) return reply(saved);
    if (/\/scenarios\/\d+$/.test(url))
      return reply({ id: 3, spec: { name: 'Tight', base: 'default', n_skus: 12, n_channels: 3, time_limit_s: 20, params: { coverage_days: 30 } } });
    return reply({ detail: 'unexpected' }, 500);
  });
  vi.stubGlobal('fetch', fetchMock);
  return calls;
}

function renderAt(path: string, source: SourceKind) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <DataSourceProvider initial={source}>
        <App />
      </DataSourceProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('parameter editor', () => {
  it('says editing needs the live solver in cached mode', async () => {
    renderAt('/parameters', 'cached');
    expect(await screen.findByTestId('editor-needs-live')).toHaveTextContent('live solver');
    expect(screen.queryByTestId('parameter-form')).toBeNull();
  });

  it('runs only the edited parameters and lands on the results of the run', async () => {
    const calls = mockApi();
    renderAt('/parameters', 'live');
    const days = await screen.findByLabelText('Coverage days');
    expect(screen.getByTestId('changed-count')).toHaveTextContent('0 parameter(s)');
    await userEvent.clear(days);
    await userEvent.type(days, '45');
    expect(screen.getByTestId('changed-count')).toHaveTextContent('1 parameter(s)');
    await userEvent.click(screen.getByTestId('run-solver'));
    expect(await screen.findByTestId('solver-status')).toHaveTextContent('optimal');
    const post = calls.find((c) => c.method === 'POST' && c.url.endsWith('/scenarios'));
    expect(post?.body).toMatchObject({ name: 'My scenario', params: { coverage_days: 45 } });
    expect(calls.some((c) => c.url === '/scenarios/7/solve')).toBe(true);
    expect(screen.getByTestId('switch-run')).toHaveTextContent('My scenario');
    expect(screen.getByTestId('export-xlsx')).toHaveAttribute('href', '/scenarios/7/export.xlsx');
  });

  it('shows a failed request inline and retries', async () => {
    mockApi({ failParams: true });
    renderAt('/parameters', 'live');
    expect(await screen.findByTestId('inline-error')).toHaveTextContent('base scenario is missing');
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByTestId('parameter-form')).toBeInTheDocument();
    expect(screen.queryByTestId('inline-error')).toBeNull();
  });

  it('saves, lists, loads and deletes scenarios', async () => {
    const calls = mockApi({ saved: [{ id: 3, name: 'Tight', base: 'default', created: '2026-11-05', solved: true }] });
    renderAt('/parameters', 'live');
    const list = await screen.findByTestId('saved-list');
    await userEvent.click(within(list).getByRole('button', { name: 'Load Tight' }));
    await waitFor(() => expect(screen.getByLabelText('Coverage days')).toHaveValue(30));
    expect(screen.getByTestId('editor-notice')).toHaveTextContent('Loaded "Tight"');
    await userEvent.click(screen.getByTestId('save-scenario'));
    expect(await screen.findByTestId('editor-notice')).toHaveTextContent('Saved "Tight" as scenario 7');
    expect(calls.find((c) => c.method === 'POST')?.body).toMatchObject({ n_skus: 12, n_channels: 3, time_limit_s: 20 });
    const deletes = await screen.findAllByRole('button', { name: 'Delete Tight' });
    await userEvent.click(deletes[0]);
    await waitFor(() => expect(calls.some((c) => c.method === 'DELETE' && c.url === '/scenarios/7')).toBe(true));
  });
});

describe('results charts and export', () => {
  it('draws the three charts from the result and disables export without a run', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(precomputed)))));
    renderAt('/results', 'cached');
    expect(await screen.findByTestId('chart-value')).toBeInTheDocument();
    expect(screen.getByTestId('chart-fill')).toBeInTheDocument();
    expect(screen.getByTestId('chart-skus')).toBeInTheDocument();
    expect(screen.getByTestId('charts')).toHaveTextContent('against the greedy baseline');
    expect(screen.getByTestId('export-xlsx')).toBeDisabled();
  });
});
