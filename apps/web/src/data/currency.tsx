import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

/**
 * Display currency. The solver always works in euro. These rates are invented for the demo and only change how a
 * number is shown, never the number the solver returned.
 */
export const CURRENCIES = {
  EUR: { rate: 1, label: 'Euro (EUR)' },
  USD: { rate: 1.08, label: 'US dollar (USD)' },
  GBP: { rate: 0.85, label: 'Pound sterling (GBP)' },
  CNY: { rate: 7.8, label: 'Chinese yuan (CNY)' },
  JPY: { rate: 163, label: 'Japanese yen (JPY)' },
} as const;
export type CurrencyCode = keyof typeof CURRENCIES;

const KEY = 'reshelf-currency';

export type Money = {
  currency: CurrencyCode;
  setCurrency: (c: CurrencyCode) => void;
  /** Full amount, for tables. */
  money: (euros: number) => string;
  /** Short amount for KPI cards, for example 1.2M. */
  compact: (euros: number) => string;
  /** Amount with a plus or minus sign. */
  signed: (euros: number) => string;
};

function build(currency: CurrencyCode, setCurrency: (c: CurrencyCode) => void): Money {
  const rate = CURRENCIES[currency].rate;
  const fmt = (v: number, compact: boolean) =>
    new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency,
      maximumFractionDigits: compact ? 1 : 0,
      notation: compact ? 'compact' : 'standard',
    }).format(v * rate);
  return {
    currency,
    setCurrency,
    money: (v) => fmt(v, false),
    compact: (v) => (Math.abs(v * rate) >= 100_000 ? fmt(v, true) : fmt(v, false)),
    signed: (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${fmt(Math.abs(v), false)}`,
  };
}

const Ctx = createContext<Money>(build('EUR', () => undefined));

function stored(): CurrencyCode {
  try {
    const v = localStorage.getItem(KEY);
    return v && v in CURRENCIES ? (v as CurrencyCode) : 'EUR';
  } catch {
    return 'EUR';
  }
}

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, set] = useState<CurrencyCode>(stored);
  const value = useMemo(
    () =>
      build(currency, (c) => {
        set(c);
        try {
          localStorage.setItem(KEY, c);
        } catch {
          /* storage is off, the choice lasts until reload */
        }
      }),
    [currency],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useMoney(): Money {
  return useContext(Ctx);
}
