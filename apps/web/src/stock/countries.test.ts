import { describe, expect, it } from 'vitest';
import { activeCountryIds, countryShapes } from './countries';

describe('globe countries', () => {
  it('has an outline for every country that the geo table can place', () => {
    const ids = new Set(countryShapes().map((s) => String(s.id)));
    const placed = ['PL', 'MX', 'CN', 'NL', 'US', 'DE', 'FR', 'GB', 'ES', 'IT', 'BR', 'IN', 'JP', 'AE', 'ZA', 'KE', 'TR', 'AU', 'CA'];
    for (const code of activeCountryIds(placed)) expect(ids.has(code), `no outline for ${code}`).toBe(true);
  });

  it('marks known countries and skips unknown ones', () => {
    expect(activeCountryIds(['DE', 'XX']).size).toBe(1);
    expect(activeCountryIds([]).size).toBe(0);
  });
});
