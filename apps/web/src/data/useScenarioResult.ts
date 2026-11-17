import { useCallback, useEffect, useState } from 'react';
import { useSource } from './DataSource';
import { useRun } from './run';
import { fetchScenarioResult, loadedScenarioResult, type ScenarioName, type ScenarioResult } from './source';

type State =
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'ready'; result: ScenarioResult };

export function useScenarioResult(name: ScenarioName): State & { retry: () => void } {
  const source = useSource();
  const loaded = source ? loadedScenarioResult(source, name) : undefined;
  const [state, setState] = useState<State>(loaded ? { status: 'ready', result: loaded } : { status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const retry = useCallback(() => setAttempt((a) => a + 1), []);

  useEffect(() => {
    if (!source) return;
    let live = true;
    const again = loadedScenarioResult(source, name);
    setState(again ? { status: 'ready', result: again } : { status: 'loading' });
    fetchScenarioResult(source, name).then(
      (result) => live && setState({ status: 'ready', result }),
      (error: Error) => live && setState({ status: 'error', error }),
    );
    return () => {
      live = false;
    };
  }, [source, name, attempt]);

  return { ...state, retry };
}

/** A precomputed scenario, or the latest live run of the planner when the choice is `run`. */
export function useChoiceResult(choice: ScenarioName | 'run') {
  const { run } = useRun();
  const cached = useScenarioResult(choice === 'run' ? 'default' : choice);
  if (choice === 'run' && run) return { status: 'ready' as const, result: run.result, retry: cached.retry };
  return cached;
}
