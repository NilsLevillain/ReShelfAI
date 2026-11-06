import type { components } from '../api/schema';

export type StockLot = components['schemas']['StockLot'];
export type StockBucket = components['schemas']['StockBucket'];
export type StockOut = components['schemas']['StockOut'];

export type Filters = { brand?: string; category?: string; reason?: string };
export type GroupKey = 'none' | 'brand' | 'category' | 'reason' | 'plant';

export type Totals = { lots: number; units: number; valueAtRisk: number; allocated: number };

export function applyFilters(lots: StockLot[], f: Filters): StockLot[] {
  return lots.filter(
    (l) =>
      (!f.brand || l.brand === f.brand) && (!f.category || l.category === f.category) && (!f.reason || l.reason === f.reason),
  );
}

export function totalsOf(lots: StockLot[]): Totals {
  return {
    lots: lots.length,
    units: lots.reduce((s, l) => s + l.units, 0),
    valueAtRisk: lots.reduce((s, l) => s + l.value_at_risk, 0),
    allocated: lots.reduce((s, l) => s + l.allocated_units, 0),
  };
}

export type Group = { key: string; lots: StockLot[]; totals: Totals };

/** Groups keep the order of first appearance, lots keep their order inside a group. */
export function groupLots(lots: StockLot[], by: GroupKey): Group[] {
  if (by === 'none') return [{ key: '', lots, totals: totalsOf(lots) }];
  const map = new Map<string, StockLot[]>();
  for (const l of lots) {
    const k = l[by];
    map.set(k, [...(map.get(k) ?? []), l]);
  }
  return [...map].map(([key, rows]) => ({ key, lots: rows, totals: totalsOf(rows) }));
}

/** Share of units sent out, in whole percent, 0 for an empty lot. */
export function sharePct(part: number, whole: number): number {
  return whole > 0 ? Math.round((part / whole) * 100) : 0;
}

export const eur = (v: number) =>
  new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v);
export const int = (v: number) => new Intl.NumberFormat('en-GB').format(v);

export const REASON_LABEL: Record<string, string> = {
  near_expiry: 'Near expiry',
  excess: 'Excess',
  obsolete: 'Obsolete',
  discontinued: 'Discontinued',
  overproduction: 'Overproduction',
};
