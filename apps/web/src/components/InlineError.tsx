import { RequestError } from '../data/source';
import { Icon } from './Icon';

export function InlineError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="rs-error" role="alert" data-testid="inline-error">
      <p>
        <Icon name="alert" /> {error.message}
      </p>
      {error instanceof RequestError && <code className="rs-error__endpoint">{error.endpoint}</code>}
      <button type="button" className="rs-btn" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
