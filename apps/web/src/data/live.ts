import type { components } from '../api/schema';
import { apiUrl, getJson, type StoredResult } from './source';

export type BaseParams = components['schemas']['BaseParams'];
export type ScenarioSpec = components['schemas']['ScenarioSpec'];
export type ScenarioOut = components['schemas']['ScenarioOut'];
export type ScenarioSummary = components['schemas']['ScenarioSummary'];

const json = { 'Content-Type': 'application/json' };

export const liveApi = {
  baseParams: (base: string) => getJson<BaseParams>(`${apiUrl()}/base-scenarios/${base}/params`),
  list: () => getJson<ScenarioSummary[]>(`${apiUrl()}/scenarios`),
  load: (id: number) => getJson<ScenarioOut>(`${apiUrl()}/scenarios/${id}`),
  save: (spec: ScenarioSpec) =>
    getJson<ScenarioOut>(`${apiUrl()}/scenarios`, { method: 'POST', headers: json, body: JSON.stringify(spec) }),
  solve: (id: number) => getJson<StoredResult>(`${apiUrl()}/scenarios/${id}/solve`, { method: 'POST' }),
  async remove(id: number): Promise<void> {
    const url = `${apiUrl()}/scenarios/${id}`;
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) throw new Error(`The server answered ${res.status} when deleting scenario ${id}.`);
  },
  exportUrl: (id: number) => `${apiUrl()}/scenarios/${id}/export.xlsx`,
};
