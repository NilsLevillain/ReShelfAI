import type { components } from '../api/schema';
import { solverDetails, solverSentence } from '../glossary';

type Solve = components['schemas']['SolveOut'];

/** One sentence for the planner. Status, gap and time sit behind Details. */
export function SolverStatus({ solve }: { solve: Solve }) {
  return (
    <div data-testid="solver-status">
      <p className="rs-note">{solverSentence(solve)}</p>
      <details className="rs-more">
        <summary>Details</summary>
        <p title={solve.message || undefined}>{solverDetails(solve)}</p>
      </details>
    </div>
  );
}
