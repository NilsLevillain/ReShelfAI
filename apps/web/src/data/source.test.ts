import { describe, expect, it, vi } from 'vitest';
import { RequestError, detectSource, fetchScenarioResult, loadedScenarioResult } from './source';

const ok = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));

describe('detectSource', () => {
  it('is cached without VITE_API_URL', async () => {
    vi.stubEnv('VITE_API_URL', '');
    expect(await detectSource(vi.fn())).toBe('cached');
  });

  it('is live when /health answers', async () => {
    vi.stubEnv('VITE_API_URL', 'http://api.test');
    const f = vi.fn(() => ok({ status: 'ok' })) as unknown as typeof fetch;
    expect(await detectSource(f)).toBe('live');
    expect(f).toHaveBeenCalledWith('http://api.test/health');
  });

  it('is cached when /health fails', async () => {
    vi.stubEnv('VITE_API_URL', 'http://api.test');
    const f = vi.fn(() => Promise.reject(new Error('down'))) as unknown as typeof fetch;
    expect(await detectSource(f)).toBe('cached');
  });
});

describe('fetchScenarioResult', () => {
  it('reads the precomputed file in cached mode', async () => {
    const f = vi.fn(() => ok({ scenario: 'default' })) as unknown as typeof fetch;
    expect(await fetchScenarioResult('cached', 'default', f)).toEqual({ scenario: 'default' });
  });

  it('raises a RequestError with the endpoint on a failed request', async () => {
    const f = vi.fn(() => Promise.resolve(new Response('{"detail":"boom"}', { status: 500 }))) as unknown as typeof fetch;
    const err = await fetchScenarioResult('cached', 'default', f).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(RequestError);
    expect((err as RequestError).endpoint).toContain('default.json');
    expect((err as RequestError).message).toBe('The server answered 500. boom');
  });

  it('creates then solves in live mode', async () => {
    vi.stubEnv('VITE_API_URL', 'http://api.test');
    const calls: string[] = [];
    const f = vi.fn((url: string) => {
      calls.push(url);
      return url.endsWith('/scenarios')
        ? ok({ id: 7, spec: {} })
        : ok({ result: { scenario: 'default' }, result_id: 1, scenario_id: 7 });
    }) as unknown as typeof fetch;
    expect(await fetchScenarioResult('live', 'default', f)).toEqual({ scenario: 'default' });
    expect(calls).toEqual(['http://api.test/scenarios', 'http://api.test/scenarios/7/solve']);
  });
});

describe('scenario result cache', () => {
  it('loads a scenario once per visit, even when two pages ask at the same time', async () => {
    const f = vi.fn(() => ok({ scenario: 'default' })) as unknown as typeof fetch;
    const [a, b] = await Promise.all([fetchScenarioResult('cached', 'default', f), fetchScenarioResult('cached', 'default', f)]);
    await fetchScenarioResult('cached', 'default', f);
    expect(a).toBe(b);
    expect(f).toHaveBeenCalledTimes(1);
    expect(loadedScenarioResult('cached', 'default')).toEqual({ scenario: 'default' });
  });

  it('keeps live and cached results apart, and one scenario apart from another', async () => {
    const f = vi.fn(() => ok({ scenario: 'x' })) as unknown as typeof fetch;
    await fetchScenarioResult('cached', 'default', f);
    expect(loadedScenarioResult('cached', 'max_recovery')).toBeUndefined();
    expect(loadedScenarioResult('live', 'default')).toBeUndefined();
  });

  it('does not keep a failed load, so Retry asks again', async () => {
    const bad = vi.fn(() => Promise.resolve(new Response('{}', { status: 503 }))) as unknown as typeof fetch;
    await expect(fetchScenarioResult('cached', 'default', bad)).rejects.toBeInstanceOf(RequestError);
    const good = vi.fn(() => ok({ scenario: 'default' })) as unknown as typeof fetch;
    expect(await fetchScenarioResult('cached', 'default', good)).toEqual({ scenario: 'default' });
    expect(good).toHaveBeenCalledTimes(1);
  });
});
