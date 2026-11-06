import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

type Cached = {
  trace: { lines: { line: string; binding: { instance: string }[] }[] };
  counterfactuals: { instance: string }[];
};
const cached = JSON.parse(readFileSync('../../data/precomputed/default.json', 'utf8')) as Cached;
// A line whose binding rule has a cached euro cost, so the hero flow works without the live solver.
const costed = new Set(cached.counterfactuals.map((c) => c.instance));
const heroLine = cached.trace.lines.find((l) => l.binding.some((b) => costed.has(b.instance)))!.line;

test('hero flow: stock, results, why, what a rule costs, compare', async ({ page }) => {
  await page.goto('/stock');
  await expect(page.getByText('Simulated data').first()).toBeVisible();
  await expect(page.getByTestId('kpi-value-at-risk')).toBeVisible();
  await expect(page.getByTestId('globe-panel')).toBeVisible();

  // A plant filter narrows the stock table.
  await page.getByRole('button', { name: /Filter stock on plant/ }).first().click();
  await expect(page.getByTestId('filter-chips')).toBeVisible();

  await page.getByRole('link', { name: 'Results' }).click();
  await expect(page.getByTestId('lines-table')).toBeVisible();
  await expect(page.getByTestId('kpi-units-destroyed')).toBeVisible();

  await page.getByRole('button', { name: `Why ${heroLine}` }).click();
  await expect(page.getByTestId('why-panel')).toBeVisible();
  await expect(page.getByTestId('rule-trace')).toBeVisible();

  await page.getByTestId('counterfactual-button').first().click();
  await expect(page.getByTestId('counterfactual-result')).toContainText('€');

  await page.getByRole('link', { name: 'Compare' }).click();
  await expect(page.getByText('against the greedy baseline').first()).toBeVisible();
});
