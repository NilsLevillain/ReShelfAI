import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { InlineError } from '../components/InlineError';
import { useSource } from '../data/DataSource';
import { liveApi, type ScenarioSpec, type ScenarioSummary } from '../data/live';
import { useRun } from '../data/run';

type Params = Record<string, unknown>;
const BASES = ['default', 'luxury_protection'] as const;
type Base = (typeof BASES)[number];
const CLASSES = ['A', 'B', 'C', 'NEW'] as const;
const RULES = [
  ['rsl', 'Shelf life'],
  ['tier', 'Brand tier'],
  ['capacity', 'Channel capacity'],
] as const;
const SCALARS: { key: string; label: string; hint: string; step: number }[] = [
  { key: 'coverage_days', label: 'Coverage days', hint: 'Days of sales a channel should hold', step: 1 },
  { key: 'coverage_alpha', label: 'Coverage floor share', hint: 'Share of the need a selected SKU must get', step: 0.05 },
  { key: 'score_rank_weight', label: 'Rank bonus', hint: 'Score bonus for a better sales rank', step: 0.05 },
  { key: 'epsilon', label: 'Score give up (epsilon)', hint: 'Score the second phase may give up for value', step: 0.005 },
];

const asRecord = (v: unknown): Record<string, number> => (v ?? {}) as Record<string, number>;
const num = (e: React.ChangeEvent<HTMLInputElement>) => Number(e.target.value);

export function Parameters() {
  const source = useSource();
  if (source === null) return <p role="status">Checking the data source</p>;
  if (source === 'cached')
    return (
      <>
        <section className="rs-page-head">
          <h2>Parameters</h2>
          <p>Edit the rules, run the solver and save the scenario.</p>
        </section>
        <div className="rs-callout rs-callout--info" data-testid="editor-needs-live" role="status">
          Editing and running need the live solver. This build shows cached results only. Start the API and set VITE_API_URL
          to edit parameters. The Results page still shows both precomputed scenarios.
        </div>
      </>
    );
  return <Editor />;
}

function Editor() {
  const navigate = useNavigate();
  const { setRun } = useRun();
  const [base, setBase] = useState<Base>('default');
  const [defaults, setDefaults] = useState<Params | null>(null);
  const [params, setParams] = useState<Params>({});
  const [name, setName] = useState('My scenario');
  const [nSkus, setNSkus] = useState(30);
  const [nChannels, setNChannels] = useState(5);
  const [timeLimit, setTimeLimit] = useState(60);
  const [saved, setSaved] = useState<ScenarioSummary[]>([]);
  const [error, setError] = useState<Error | null>(null);
  const [retry, setRetry] = useState<() => void>(() => () => undefined);
  const [busy, setBusy] = useState<'run' | 'save' | null>(null);
  const [notice, setNotice] = useState('');

  const fail = useCallback((e: unknown, again: () => void) => {
    setError(e as Error);
    setRetry(() => again);
  }, []);

  const loadSaved = useCallback(() => {
    liveApi.list().then(setSaved, (e) => fail(e, loadSaved));
  }, [fail]);

  const loadDefaults = useCallback(
    (b: string, keep?: Params) => {
      liveApi.baseParams(b).then(
        (p) => {
          setDefaults(p.params);
          setParams({ ...p.params, ...keep });
          setError(null);
        },
        (e) => fail(e, () => loadDefaults(b, keep)),
      );
    },
    [fail],
  );

  useEffect(() => {
    loadDefaults(base);
  }, [base, loadDefaults]);
  useEffect(loadSaved, [loadSaved]);

  const edits = (): Params =>
    Object.fromEntries(Object.entries(params).filter(([k, v]) => JSON.stringify(v) !== JSON.stringify(defaults?.[k])));
  const spec = (): ScenarioSpec => ({ name, base, n_skus: nSkus, n_channels: nChannels, time_limit_s: timeLimit, params: edits() });

  const save = async (): Promise<number | null> => {
    try {
      const out = await liveApi.save(spec());
      setError(null);
      loadSaved();
      return out.id;
    } catch (e) {
      fail(e, () => void save());
      return null;
    }
  };

  const onSave = async () => {
    setBusy('save');
    const id = await save();
    if (id !== null) setNotice(`Saved "${name}" as scenario ${id}.`);
    setBusy(null);
  };

  const onRun = async () => {
    setBusy('run');
    setNotice('');
    const id = await save();
    if (id !== null) {
      try {
        const stored = await liveApi.solve(id);
        setRun({ scenarioId: id, resultId: stored.result_id, name, result: stored.result });
        navigate('/results');
      } catch (e) {
        fail(e, () => void onRun());
      }
    }
    setBusy(null);
  };

  const onLoad = async (id: number) => {
    try {
      const s = (await liveApi.load(id)).spec;
      setBase(s.base as Base);
      setName(s.name);
      setNSkus(s.n_skus ?? 30);
      setNChannels(s.n_channels ?? 5);
      setTimeLimit(s.time_limit_s ?? 60);
      loadDefaults(s.base ?? 'default', (s.params ?? {}) as Params);
      setNotice(`Loaded "${s.name}".`);
    } catch (e) {
      fail(e, () => void onLoad(id));
    }
  };

  const onDelete = async (id: number) => {
    try {
      await liveApi.remove(id);
      loadSaved();
    } catch (e) {
      fail(e, () => void onDelete(id));
    }
  };

  const set = (key: string, value: unknown) => setParams((p) => ({ ...p, [key]: value }));
  const setIn = (key: string, sub: string, value: number) => set(key, { ...asRecord(params[key]), [sub]: value });
  const rules = (params.planner_rules as string[] | undefined) ?? [];

  return (
    <>
      <section className="rs-page-head">
        <h2>Parameters</h2>
        <p>Edit the rules, run the solver and save the scenario. Every value is an invented illustrative default.</p>
      </section>
      {error && <InlineError error={error} onRetry={retry} />}
      {notice && (
        <p role="status" data-testid="editor-notice">
          {notice}
        </p>
      )}
      {!defaults ? (
        !error && <p role="status">Loading parameters</p>
      ) : (
        <form className="rs-form" data-testid="parameter-form" onSubmit={(e) => e.preventDefault()}>
          <fieldset className="rs-fieldset">
            <legend>Scenario</legend>
            <label className="rs-field">
              <span className="rs-field__label">Name</span>
              <input className="rs-input" value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="rs-field">
              <span className="rs-field__label">Base world</span>
              <select className="rs-input" value={base} onChange={(e) => setBase(e.target.value as Base)}>
                {BASES.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </label>
            <label className="rs-field">
              <span className="rs-field__label">SKUs</span>
              <input className="rs-input" type="number" min={1} max={2000} value={nSkus} onChange={(e) => setNSkus(num(e))} />
              <span className="rs-field__hint">Bigger worlds solve slower</span>
            </label>
            <label className="rs-field">
              <span className="rs-field__label">Channels</span>
              <input className="rs-input" type="number" min={1} max={20} value={nChannels} onChange={(e) => setNChannels(num(e))} />
            </label>
            <label className="rs-field">
              <span className="rs-field__label">Solver time limit (s)</span>
              <input className="rs-input" type="number" min={1} max={600} value={timeLimit} onChange={(e) => setTimeLimit(num(e))} />
            </label>
          </fieldset>

          <fieldset className="rs-fieldset">
            <legend>Coverage and objective</legend>
            {SCALARS.map((s) => (
              <label key={s.key} className="rs-field">
                <span className="rs-field__label">{s.label}</span>
                <input
                  className="rs-input"
                  type="number"
                  step={s.step}
                  aria-label={s.label}
                  value={Number(params[s.key] ?? 0)}
                  onChange={(e) => set(s.key, num(e))}
                />
                <span className="rs-field__hint">{s.hint}</span>
              </label>
            ))}
          </fieldset>

          <fieldset className="rs-fieldset">
            <legend>Score by class</legend>
            {CLASSES.map((c) => (
              <label key={c} className="rs-field">
                <span className="rs-field__label">Class {c}</span>
                <input
                  className="rs-input"
                  type="number"
                  step={0.05}
                  aria-label={`Score class ${c}`}
                  value={asRecord(params.score_base)[c] ?? 0}
                  onChange={(e) => setIn('score_base', c, num(e))}
                />
              </label>
            ))}
          </fieldset>

          <fieldset className="rs-fieldset">
            <legend>Push quantity for new products (units)</legend>
            {Object.keys(asRecord(defaults.push_quantity_units)).map((c) => (
              <label key={c} className="rs-field">
                <span className="rs-field__label">{c}</span>
                <input
                  className="rs-input"
                  type="number"
                  min={0}
                  aria-label={`Push ${c}`}
                  value={asRecord(params.push_quantity_units)[c] ?? 0}
                  onChange={(e) => setIn('push_quantity_units', c, num(e))}
                />
              </label>
            ))}
          </fieldset>

          <fieldset className="rs-fieldset">
            <legend>Rules the greedy baseline applies by hand</legend>
            {RULES.map(([key, label]) => (
              <label key={key} className="rs-check">
                <input
                  type="checkbox"
                  checked={rules.includes(key)}
                  onChange={(e) => set('planner_rules', e.target.checked ? [...rules, key] : rules.filter((r) => r !== key))}
                />
                {label}
              </label>
            ))}
          </fieldset>

          <div className="rs-actions">
            <button type="button" className="rs-btn rs-btn--primary" disabled={busy !== null} onClick={() => void onRun()} data-testid="run-solver">
              {busy === 'run' ? 'Solving' : 'Run the solver'}
            </button>
            <button type="button" className="rs-btn" disabled={busy !== null} onClick={() => void onSave()} data-testid="save-scenario">
              Save scenario
            </button>
            <button type="button" className="rs-btn" onClick={() => setParams(defaults)}>
              Reset to defaults
            </button>
            <span data-testid="changed-count">{Object.keys(edits()).length} parameter(s) changed from the defaults</span>
          </div>
        </form>
      )}

      <section>
        <h3>Saved scenarios</h3>
        {saved.length === 0 ? (
          <p>No saved scenario yet.</p>
        ) : (
          <ul data-testid="saved-list">
            {saved.map((s) => (
              <li key={s.id} className="rs-actions">
                <strong>{s.name}</strong>
                <span>
                  {s.base}
                  {s.solved ? ', solved' : ''}
                </span>
                <button type="button" className="rs-btn" aria-label={`Load ${s.name}`} onClick={() => void onLoad(s.id)}>
                  Load
                </button>
                <button type="button" className="rs-btn" aria-label={`Delete ${s.name}`} onClick={() => void onDelete(s.id)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
