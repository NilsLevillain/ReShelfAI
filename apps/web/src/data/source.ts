import type { components } from '../api/schema';

export type ScenarioResult = components['schemas']['ScenarioResult'];
export type StoredResult = components['schemas']['StoredResult'];
export type SourceKind = 'cached' | 'live';

const precomputed = import.meta.glob('@data/precomputed/*.json', {
  query: '?url',
  import: 'default',
  eager: true,
}) as Record<string, string>;

export const SCENARIOS = ['default', 'luxury_protection'] as const;
export type ScenarioName = (typeof SCENARIOS)[number];

export class RequestError extends Error {
  constructor(
    readonly endpoint: string,
    message: string,
  ) {
    super(message);
  }
}

export function apiUrl(): string {
  return (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '';
}

/** Live when VITE_API_URL is set and answers /health, cached otherwise. The banner states which. */
export async function detectSource(fetchFn: typeof fetch = fetch): Promise<SourceKind> {
  const base = apiUrl();
  if (!base) return 'cached';
  try {
    const res = await fetchFn(`${base}/health`);
    return res.ok ? 'live' : 'cached';
  } catch {
    return 'cached';
  }
}

async function getJson<T>(endpoint: string, init?: RequestInit, fetchFn: typeof fetch = fetch): Promise<T> {
  let res: Response;
  try {
    res = await fetchFn(endpoint, init);
  } catch (e) {
    throw new RequestError(endpoint, `The request did not reach the server (${(e as Error).message}). Check the connection and retry.`);
  }
  if (!res.ok) {
    let detail = '';
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === 'string') detail = ` ${body.detail}`;
    } catch {
      /* body is not JSON, the status line below still says what failed */
    }
    throw new RequestError(endpoint, `The server answered ${res.status}.${detail}`);
  }
  return (await res.json()) as T;
}

export async function fetchScenarioResult(
  source: SourceKind,
  name: ScenarioName,
  fetchFn: typeof fetch = fetch,
): Promise<ScenarioResult> {
  if (source === 'cached') {
    const key = Object.keys(precomputed).find((k) => k.endsWith(`/${name}.json`));
    if (!key) throw new RequestError(`precomputed/${name}.json`, `No precomputed file for scenario ${name}. Run make precompute.`);
    return getJson<ScenarioResult>(precomputed[key], undefined, fetchFn);
  }
  const base = apiUrl();
  const json = { 'Content-Type': 'application/json' };
  const created = await getJson<components['schemas']['ScenarioOut']>(
    `${base}/scenarios`,
    { method: 'POST', headers: json, body: JSON.stringify({ name, base: name }) },
    fetchFn,
  );
  const stored = await getJson<StoredResult>(`${base}/scenarios/${created.id}/solve`, { method: 'POST' }, fetchFn);
  return stored.result;
}
