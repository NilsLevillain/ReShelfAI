import type { components } from './api/schema';

/** Plain words for everything a supply planner sees. One place, so a word means the same thing on every page. */

type Solve = components['schemas']['SolveOut'];
type Channel = components['schemas']['GeoChannel'];

export const CHANNEL_TYPES: Record<string, { name: string; text: string }> = {
  outlet: { name: 'Outlet store', text: 'Discount stores that sell brand products at reduced prices.' },
  friends_family: { name: 'Friends and family sale', text: 'Closed sales for staff and partners at reduced prices.' },
  clearance_web: { name: 'Clearance website', text: 'Online clearance sales, open to consumers.' },
  ngo_donation: { name: 'Donation', text: 'Stock given to charity partners. Little value comes back, but the stock is not destroyed.' },
  liquidation: { name: 'Liquidation', text: 'Bulk sale to a liquidator at a deep discount. Fast, with the lowest price.' },
};

export function countryName(code: string): string {
  try {
    return new Intl.DisplayNames(['en'], { type: 'region' }).of(code) ?? code;
  } catch {
    return code;
  }
}

export type ChannelInfo = { code: string; name: string; text: string };

export function channelInfo(code: string, channels: Channel[]): ChannelInfo {
  const c = channels.find((x) => x.channel === code);
  if (!c) return { code, name: code, text: '' };
  const t = CHANNEL_TYPES[c.type];
  return { code, name: `${t?.name ?? c.type}, ${countryName(c.country)}`, text: t?.text ?? '' };
}

export type LotInfo = { code: string; name: string };

/** A lot shown by its product name, with the code kept as a small tag. Unknown lots fall back to the code. */
export function lotInfo(code: string, lots: Pick<components['schemas']['StockLot'], 'lot' | 'description'>[]): LotInfo {
  const l = lots.find((x) => x.lot === code);
  return { code, name: l?.description || code };
}

/** What each rule means, in a sentence a planner can check against their own practice. */
export const RULE_HELP: Record<string, { name: string; text: string }> = {
  supply: { name: 'Lot stock', text: 'A lot cannot send out more units than it holds.' },
  cap: { name: 'Channel capacity', text: 'A channel can only take so many units in total.' },
  sku: { name: 'Channel limit on SKUs', text: 'A channel can only handle so many different products.' },
  asrt: { name: 'Assortment limit', text: 'A channel can only carry so many products of one brand and category.' },
  asrt_units: { name: 'Unit limit by brand and category', text: 'A channel can only take so many units of one brand and category.' },
  cov_hi: { name: 'Coverage ceiling', text: 'A channel should not receive more than it can sell in the coverage period.' },
  cov_lo: { name: 'Coverage floor', text: 'A product that a channel receives must be worth sending: enough for a share of its need.' },
  push: { name: 'Push quantity for new products', text: 'A new product in a channel gets at least a set quantity, so it can start to sell.' },
};

export const REASON_HELP: Record<string, string> = {
  RSL: 'Too little shelf life left when the stock would arrive.',
  TIER: 'The brand level is not allowed in this channel, to protect the brand.',
  NO_PUSH: 'A new product in this channel needs a push quantity, and none fits.',
};

export const STOCK_REASON_HELP: Record<string, string> = {
  near_expiry: 'Close to its expiry date.',
  excess: 'More than the main channels can sell.',
  obsolete: 'No longer wanted, for example an old pack.',
  discontinued: 'The product is no longer made or sold.',
  overproduction: 'Made in a larger quantity than ordered.',
};

/** Solver status in one sentence for a planner. The raw status stays in the details. */
export function solverSentence(solve: Solve): string {
  switch (solve.status) {
    case 'optimal':
      return 'The plan is the best one the model can find.';
    case 'feasible':
      return 'The plan follows every rule. The model ran out of time, so a better plan may exist.';
    case 'infeasible':
      return 'No plan can follow every rule. Relax a rule and run again.';
    default:
      return solve.message || 'The model did not finish. Run again with a longer time limit.';
  }
}

export function solverDetails(solve: Solve): string {
  const gap = solve.mip_gap === null ? 'no gap reported' : `gap ${(solve.mip_gap * 100).toFixed(3)}%`;
  return `Solver status: ${solve.status}, ${gap}, ${solve.time_s.toFixed(1)} s of ${solve.time_limit_s} s`;
}

const PARAM_LABELS: Record<string, string> = {
  coverage_days: 'Coverage days',
  coverage_alpha: 'Coverage floor share',
  score_rank_weight: 'Rank bonus',
  epsilon: 'Score give up (epsilon)',
  score_base: 'Score for class',
  push_quantity_units: 'Push quantity for',
  planner_rules: 'Rules the greedy baseline applies by hand',
};

export type ParamChange = { label: string; from: string; to: string };

const show = (v: unknown): string => (Array.isArray(v) ? (v.length ? v.join(', ') : 'none') : String(v ?? 'not set'));

/** Changed values against the defaults, one plain line each. Nested values (class scores, push quantities) get one line per entry. */
export function describeEdits(edits: Record<string, unknown>, defaults: Record<string, unknown> | null): ParamChange[] {
  const out: ParamChange[] = [];
  for (const [key, value] of Object.entries(edits)) {
    const base = PARAM_LABELS[key] ?? key;
    const before = defaults?.[key];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const old = (before ?? {}) as Record<string, unknown>;
      for (const [sub, v] of Object.entries(value as Record<string, unknown>)) {
        if (JSON.stringify(v) !== JSON.stringify(old[sub])) out.push({ label: `${base} ${sub}`, from: show(old[sub]), to: show(v) });
      }
    } else out.push({ label: base, from: show(before), to: show(value) });
  }
  return out;
}

/** "sku[LIQ_AE]" becomes "Channel limit on SKUs, Liquidation, United Arab Emirates". Unknown parts stay as they are. */
export function ruleLabel(instance: string, channels: Channel[]): string {
  const m = /^(\w+)\[(.*)\]$/.exec(instance);
  if (!m) return instance;
  const name = RULE_HELP[m[1]]?.name ?? m[1];
  const args = m[2]
    .split(',')
    .map((a) => a.trim())
    .filter(Boolean)
    .map((a) => (channels.some((c) => c.channel === a) ? channelInfo(a, channels).name : /^\d+$/.test(a) ? `SKU ${a}` : a));
  return args.length ? `${name}, ${args.join(', ')}` : name;
}
