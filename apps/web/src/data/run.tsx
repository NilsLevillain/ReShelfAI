import { createContext, useContext, useState, type ReactNode } from 'react';
import type { ScenarioResult } from './source';

export type Run = { scenarioId: number; name: string; result: ScenarioResult };
type RunCtx = { run: Run | null; setRun: (r: Run | null) => void };

const Ctx = createContext<RunCtx>({ run: null, setRun: () => undefined });

/** The latest live run of the planner. Results and the export read it, so both show one source. */
export function RunProvider({ children }: { children: ReactNode }) {
  const [run, setRun] = useState<Run | null>(null);
  return <Ctx.Provider value={{ run, setRun }}>{children}</Ctx.Provider>;
}

export function useRun(): RunCtx {
  return useContext(Ctx);
}
