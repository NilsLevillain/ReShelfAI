import type { components } from './api/schema';
import type { ScenarioName } from './data/source';

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
  coverage_days: 'Days of sales a channel should hold',
  coverage_alpha: 'Smallest shipment, as a share of the need',
  score_rank_weight: 'Bonus for top sellers',
  epsilon: 'Score the plan may give up for value',
  score_base: 'Score for class',
  push_quantity_units: 'Push quantity for',
  planner_rules: 'Rules the plan made by hand applies',
  channel_sku_limit_scale: 'Channel limit on products',
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

/** The scenarios a planner can open, each with the one line story that tells it apart from the others. */
export const SCENARIO_INFO: Record<ScenarioName, { name: string; story: string }> = {
  default: { name: 'Default', story: 'The starting rules. Each channel holds 90 days of sales.' },
  luxury_protection: {
    name: 'Luxury protection',
    story: 'Luxury is never discounted: it is banned from the outlet, friends and family and clearance channels.',
  },
  max_recovery: {
    name: 'Max recovery',
    story: 'Each channel holds 180 days of sales and new products get twice the push quantity.',
  },
  shelf_life_strict: {
    name: 'Strict shelf life',
    story: 'Every channel asks for 30 more points of remaining shelf life, so more stock is refused at the door.',
  },
};

/** Help for one parameter of the rules page. `raise` and `lower` say what happens to the plan, `how` how to pick a value. */
export type ParamHelp = { name: string; text: string; raise: string; lower: string; range: string; how: string };

export const PARAM_HELP: Record<string, ParamHelp> = {
  coverage_days: {
    name: 'Days of sales a channel should hold',
    text: 'Each channel is asked to hold this many days of sales of a product. It sets the most a channel can receive of that product.',
    raise: 'Channels take more units, so more stock is placed and less is destroyed. A channel may then hold stock that sells slowly.',
    lower: 'Channels take fewer units and more stock is destroyed.',
    range: 'Default 90 days. Allowed 1 to 365.',
    how: 'Choose the number of days a channel can really sell through before the stock goes stale. In the demo, 180 days places about three times as many units as 90.',
  },
  coverage_alpha: {
    name: 'Smallest shipment, as a share of the need',
    text: 'When a channel carries a product, it must receive at least this share of what it needs. It avoids tiny shipments that are not worth sending.',
    raise: 'Fewer products enter a channel, each with a bigger shipment.',
    lower: 'More products can enter a channel, with smaller shipments.',
    range: 'Default 0.5, which is half of the need. Allowed 0 to 1.',
    how: 'Keep 0.5 so a shipment covers at least half of the need. Go lower only if small shipments are acceptable for you.',
  },
  score_rank_weight: {
    name: 'Bonus for top sellers',
    text: 'Every product in a channel has a score, which is what the plan protects first. Products with a better sales rank get this bonus on top of the score of their class.',
    raise: 'Top sellers win more often when a channel has to choose between products.',
    lower: 'Rank matters less and only the class counts. At 0 rank is ignored.',
    range: 'Default 0.25. Allowed 0 to 1.',
    how: 'Compare it with the gaps between classes (A 1.0, B 0.7, C 0.4). A bonus of 0.25 lets a top B product come close to a low ranked A product.',
  },
  epsilon: {
    name: 'Score the plan may give up for value',
    text: 'The plan first keeps the best possible product score. Then it looks for more euros. This is the share of that score it may give up in exchange for value.',
    raise: 'More euros come back, with a less balanced range of products.',
    lower: 'The range of products comes first and fewer euros come back. At 0 the score is never given up.',
    range: 'Default 0.01, which is 1 percent. Allowed 0 to 0.1.',
    how: 'Keep 0.01 for a balanced plan. Try 0.05 if value matters more than keeping every product selling.',
  },
  score_base: {
    name: 'Score by product class',
    text: 'The class says how important a product is in a channel: A sells the most, then B, then C. NEW products have no sales in that channel yet. A higher score makes the plan work harder to keep that class in the channel.',
    raise: 'The plan favors that class when a channel limit forces a choice.',
    lower: 'That class is the first to lose out when a channel limit forces a choice.',
    range: 'Defaults A 1.0, B 0.7, C 0.4, NEW 0.55. Allowed 0 to 2.',
    how: 'Keep the order A, then B, then C. Only the gaps between classes matter, not the numbers. Put NEW higher if launches must get shelf space, lower if proven sellers come first.',
  },
  push_quantity_units: {
    name: 'Push quantity for new products',
    text: 'A new product has no sales history, so nothing says how much a channel needs. Each channel gets a fixed number of units, set by product category, to test the market. It is also the most a new product can receive.',
    raise: 'More units of new products are placed, with the risk that they do not sell.',
    lower: 'Fewer units of new products are placed and more are destroyed. At 0 the category is not pushed.',
    range: 'Whole number from 0 to 10,000 units.',
    how: 'Use the size of a normal first shipment for the category. Fragrance is small, haircare is larger.',
  },
  planner_rules: {
    name: 'Rules the plan made by hand applies',
    text: 'The plan made by hand (the greedy baseline) only checks the rules ticked here. The other rules are found afterwards in an audit. This changes the baseline you are compared with, not your optimized plan.',
    raise: 'The plan made by hand breaks fewer rules, so it is a stronger baseline.',
    lower: 'The plan made by hand breaks more rules, so the gap with the optimized plan grows.',
    range: 'Shelf life, brand tier and channel capacity.',
    how: 'Leave all three ticked for a fair comparison.',
  },
  channel_sku_limit_scale: {
    name: 'Channel limit on products',
    text: 'Each channel can only carry so many different products. This number multiplies that limit for every channel.',
    raise: 'More products can enter each channel. It helps when "Channel limit on products" shows up under Why is stock destroyed.',
    lower: 'Fewer products can enter each channel and more stock is destroyed.',
    range: 'Default 1, which is the limit of the base scenario. Allowed 0.1 to 10.',
    how: 'Raise it to 2 if channels could widen their range. It only matters where the limit is reached, see the Plan page.',
  },
};

export const RULE_CHOICE_HELP: Record<string, { name: string; text: string }> = {
  rsl: { name: 'Shelf life', text: 'Channels refuse stock that has too little shelf life left when it arrives.' },
  tier: { name: 'Brand tier', text: 'Some channels refuse some brand levels, for example luxury in a clearance channel, to protect the brand.' },
  capacity: { name: 'Channel capacity', text: 'A channel cannot take more units than its capacity.' },
};

/** Why stock is destroyed. Each cause says what happened to the units and what a planner can change. */
export type CauseHelp = { title: string; text: string; action?: string };

export const CAUSE_HELP: Record<string, CauseHelp> = {
  coverage_ceiling: {
    title: 'Channels already hold enough stock',
    text: 'A channel only takes about the days of sales it is asked to hold. The rest of this stock has nowhere to go.',
    action: 'Raise the days of sales a channel holds',
  },
  push_ceiling: {
    title: 'New products stop at their push quantity',
    text: 'A new product has no sales history, so each channel only takes its push quantity. The rest of the lot is left over.',
    action: 'Change the push quantities',
  },
  blocked: {
    title: 'No channel accepts these lots',
    text: 'The shelf life, brand tier or push rules removed every channel for these lots. The Stock page shows how many channels each lot can still go to.',
  },
  no_demand: {
    title: 'No channel sells these products',
    text: 'The channels that accept these lots do not sell the product, or already hold more than they need.',
  },
  sku_limit: {
    title: 'Channels are full in number of products',
    text: 'There was room for more units, but a channel cannot carry more different products.',
    action: 'Raise the channel limit on products',
  },
  capacity: {
    title: 'Channel capacity is full',
    text: 'There was demand for more units, but a channel reached its total capacity.',
  },
  group_limit: {
    title: 'Limit on one brand and category',
    text: 'There was room for more units, but a channel reached its limit for one brand and category.',
  },
  not_worth: {
    title: 'Not worth sending',
    text: 'There was room and no limit was reached. Sending more would not have paid, for example because the brand cost is larger than the price that comes back.',
  },
};

/** Where on the rules page a lever lives, so a button on the Plan page can take the planner there. */
export const LEVER_FIELD: Record<string, string> = {
  coverage_days: 'Days of sales a channel should hold',
  push_quantity_units: 'Push quantity for new products',
  channel_sku_limit_scale: 'Channel limit on products',
};

/** What a KPI means and which direction is better. Used for tooltips and for the good or bad signal on changes. */
export type KpiHelp = { name: string; text: string; better: 'up' | 'down' };

export const KPI_HELP: Record<string, KpiHelp> = {
  value_recovered: {
    name: 'Value recovered',
    text: 'The money that comes back from the stock that is placed, after the brand cost. It is a simulated figure.',
    better: 'up',
  },
  units_allocated: { name: 'Units given a second life', text: 'Units the plan sends to a channel instead of destroying them.', better: 'up' },
  units_destroyed: { name: 'Units destroyed', text: 'Units the plan does not place. Under Why is stock destroyed you can see why.', better: 'down' },
  brand_risk_index: {
    name: 'Brand risk index',
    text: 'For every euro of stock cost the plan sends out, this is the part that counts as brand image cost, for example a premium product sold in a clearance channel. Lower is better, and 0 percent means nothing brand sensitive was sent. It is a ratio: it can fall when a plan places more low risk stock, even if the total brand cost grows.',
    better: 'down',
  },
};
