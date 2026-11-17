import { Link } from 'react-router-dom';

/** End of page guide: what the planner does next, in one sentence and one button. */
export function NextStep({ to, label, text }: { to: string; label: string; text: string }) {
  return (
    <section className="rs-card rs-nextstep" data-testid="next-step" aria-label="Next step">
      <p>
        <strong>Next step.</strong> {text}
      </p>
      <div className="rs-actions">
        <Link className="rs-btn rs-btn--primary" to={to}>
          {label}
        </Link>
      </div>
    </section>
  );
}
