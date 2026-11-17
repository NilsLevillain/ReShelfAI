import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import precomputed from '@data/precomputed/default.json';
import { CurrencyProvider } from '../data/currency';
import { countryName } from '../glossary';
import type { Result } from '../results/model';
import { codeOfCountryId } from './countries';
import { GlobePanel } from './GlobePanel';

const geo = (precomputed as unknown as Result).geo;

function panel(withPlan: boolean) {
  return render(
    <MemoryRouter>
      <CurrencyProvider>
        <GlobePanel geo={geo} onSelect={() => undefined} webgl={false} withPlan={withPlan} />
      </CurrencyProvider>
    </MemoryRouter>,
  );
}

const firstColumn = () =>
  within(screen.getByTestId('country-table'))
    .getAllByRole('rowheader')
    .map((c) => c.textContent);

describe('globe numbers', () => {
  it('has one row per country, biggest value at risk first', () => {
    panel(true);
    const rows = within(screen.getByTestId('country-table')).getAllByRole('row');
    expect(rows).toHaveLength(geo.countries.length + 1);
    const biggest = [...geo.countries].sort((a, b) => b.value_at_risk - a.value_at_risk)[0];
    expect(firstColumn()[0]).toBe(countryName(biggest.country));
  });

  it('sorts on a column when its title is clicked, and again to reverse', async () => {
    panel(true);
    await userEvent.click(within(screen.getByTestId('country-table')).getByRole('button', { name: 'Units destroyed' }));
    const top = [...geo.countries].sort((a, b) => b.destroyed_units - a.destroyed_units)[0];
    expect(firstColumn()[0]).toBe(countryName(top.country));
    await userEvent.click(within(screen.getByTestId('country-table')).getByRole('button', { name: 'Units destroyed' }));
    const last = [...geo.countries].sort((a, b) => a.destroyed_units - b.destroyed_units)[0];
    expect(firstColumn()[0]).toBe(countryName(last.country));
  });

  it('shows what the plan does only when a plan is applied', () => {
    const { unmount } = panel(false);
    expect(screen.queryByRole('button', { name: 'Units destroyed' })).toBeNull();
    expect(within(screen.getByTestId('plant-table')).queryByRole('columnheader', { name: 'Units destroyed' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Value at risk' })).toBeInTheDocument();
    unmount();
    panel(true);
    expect(screen.getByRole('button', { name: 'Units destroyed' })).toBeInTheDocument();
    expect(within(screen.getByTestId('plant-table')).getByRole('columnheader', { name: 'Units destroyed' })).toBeInTheDocument();
  });

  it('maps a map id back to a country code', () => {
    expect(codeOfCountryId('276')).toBe('DE');
    expect(codeOfCountryId('000')).toBeUndefined();
  });
});
