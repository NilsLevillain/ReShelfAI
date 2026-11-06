import type { components } from '../api/schema';

type Solve = components['schemas']['SolveOut'];

export function SolverStatus({ solve }: { solve: Solve }) {
  const gap = solve.mip_gap === null ? 'no gap reported' : `gap ${(solve.mip_gap * 100).toFixed(3)}%`;
  return (
    <span className="rs-badge" data-testid="solver-status" title={solve.message || undefined}>
      Solver: {solve.status}, {gap}, {solve.time_s.toFixed(1)} s of {solve.time_limit_s} s
    </span>
  );
}
