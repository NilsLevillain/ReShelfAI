import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from './App';
import { DataSourceProvider } from './data/DataSource';
import { InlineError } from './components/InlineError';
import { Stepper } from './components/Stepper';
import { RequestError } from './data/source';

function renderAt(path: string, source: 'cached' | 'live' = 'cached') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <DataSourceProvider initial={source}>
        <App />
      </DataSourceProvider>
    </MemoryRouter>,
  );
}

describe('shell', () => {
  it('shows the simulated badge and the cached banner', () => {
    renderAt('/');
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Simulated data');
    expect(screen.getByTestId('data-source-banner')).toHaveTextContent('Cached results');
  });

  it('says Live solver when the API answers', () => {
    renderAt('/', 'live');
    expect(screen.getByTestId('data-source-banner')).toHaveTextContent('Live solver');
  });

  it('switches theme and stores it', async () => {
    renderAt('/');
    await userEvent.click(screen.getByRole('button', { name: 'Switch theme' }));
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(localStorage.getItem('reshelf-theme')).toBe('dark');
  });

  it('shows the stepper on process pages only', () => {
    const { unmount } = renderAt('/parameters');
    expect(screen.getByTestId('stepper')).toBeInTheDocument();
    unmount();
    renderAt('/stock');
    expect(screen.queryByTestId('stepper')).toBeNull();
  });
});

describe('stepper', () => {
  it('marks done, current and upcoming', () => {
    render(<Stepper current={1} />);
    const items = screen.getAllByRole('listitem');
    expect(items.map((i) => i.dataset.state)).toEqual(['done', 'current', 'upcoming', 'upcoming']);
    expect(items[1]).toHaveAttribute('aria-current', 'step');
  });
});

describe('inline error', () => {
  it('names the endpoint and retries', async () => {
    const retry = vi.fn();
    render(<InlineError error={new RequestError('/scenarios', 'The server answered 500.')} onRetry={retry} />);
    expect(screen.getByRole('alert')).toHaveTextContent('The server answered 500.');
    expect(screen.getByText('/scenarios')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(retry).toHaveBeenCalledOnce();
  });
});
