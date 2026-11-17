import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { clearScenarioCache } from '../data/source';

// Tests must not depend on the developer's apps/web/.env.local. A test that needs an API URL stubs it itself.
beforeEach(() => {
  vi.stubEnv('VITE_API_URL', '');
});

afterEach(() => {
  vi.unstubAllEnvs();
  cleanup();
  clearScenarioCache();
  localStorage.clear();
  document.documentElement.removeAttribute('data-theme');
});

// jsdom has no canvas. Return null so the WebGL check says "no WebGL" without printing a warning.
HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;

// jsdom does not implement scrolling. Pages that scroll a field into view only need the call to exist.
Element.prototype.scrollIntoView = () => undefined;
