import { defineConfig } from '@playwright/test';

// One test of the hero flow on the cached results, so it needs no API. Port 5174 avoids a running dev server.
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  reporter: 'list',
  // PW_CHANNEL=msedge uses the installed Edge when the Chromium download is blocked.
  use: { baseURL: 'http://localhost:5174', headless: true, channel: process.env.PW_CHANNEL || undefined },
  webServer: {
    command: 'pnpm exec vite --port 5174 --strictPort',
    url: 'http://localhost:5174',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
