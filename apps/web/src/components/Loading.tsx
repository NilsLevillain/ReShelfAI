import { useEffect, useState } from 'react';
import { useSource } from '../data/DataSource';

/**
 * Loading line. In live mode a scenario that was not opened yet is solved on request, which can take
 * many seconds, so after a short wait the line says what is happening and that the next visit is instant.
 */
export function Loading({ what }: { what: string }) {
  const source = useSource();
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 1500);
    return () => clearTimeout(timer);
  }, []);
  return (
    <div role="status" className="rs-note" data-testid="loading">
      <p>Loading {what}</p>
      <div className="rs-skeleton" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      {slow && source === 'live' && (
        <p data-testid="loading-slow">
          The live solver is working on this scenario. A scenario that was not opened yet can take up to 20 seconds. It is kept
          for this visit, so the next time it opens at once.
        </p>
      )}
    </div>
  );
}
