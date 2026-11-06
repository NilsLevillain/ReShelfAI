import type { components } from '../api/schema';
import { eur } from '../stock/model';

export type Result = components['schemas']['ScenarioResult'];
export type Kpi = components['schemas']['KpiOut'];
export type Line = components['schemas']['AllocationLine'];
export type LineTrace = components['schemas']['LineTraceOut'];
export type Counterfactual = components['schemas']['CounterfactualOut'];

/** Planner words for the named constraints. The raw name stays visible as detail. */
export const RULE_WORDS: Record<string, string> = {
  supply: 'Lot stock',
  cap: 'Channel capacity',
  sku: 'Channel limit on SKUs',
  asrt: 'Assortment limit by brand and category',
  asrt_units: 'Unit limit by brand and category',
  cov_hi: 'Coverage ceiling',
  cov_lo: 'Coverage floor',
  push: 'Push quantity for new products',
};

export const REASON_WORDS: Record<string, string> = {
  RSL: 'Not enough shelf life left at delivery',
  TIER: 'The brand tier is not allowed in this channel',
  NO_PUSH: 'New product in this channel with no push quantity',
};

export const MODE_WORDS: Record<string, string> = {
  plus_10pct: 'Relax by 10%',
  off: 'Switch off',
};

export function ruleName(constraint: string): string {
  return RULE_WORDS[constraint] ?? constraint;
}

/** Counterfactuals of one instance, in dial order: relax by 10 percent first, then off. */
export function counterfactualsFor(result: Result, instance: string): Counterfactual[] {
  const order = ['plus_10pct', 'off'];
  return result.counterfactuals
    .filter((c) => c.instance === instance)
    .sort((a, b) => order.indexOf(a.mode) - order.indexOf(b.mode));
}

export function ruleInstances(result: Result): string[] {
  return [...new Set(result.counterfactuals.map((c) => c.instance))];
}

export function violationCount(result: Result): number {
  return Object.values(result.baseline.audit).reduce((s, a) => s + a.count, 0);
}

export function signedEur(v: number): string {
  return `${v > 0 ? '+' : v < 0 ? '−' : ''}${eur(Math.abs(v))}`;
}

export function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

export function signedInt(v: number): string {
  return `${v > 0 ? '+' : v < 0 ? '−' : ''}${new Intl.NumberFormat('en-GB').format(Math.abs(v))}`;
}
