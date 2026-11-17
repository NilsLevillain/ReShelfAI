import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { InlineError } from '../components/InlineError';
import { NumberField } from '../components/NumberField';
import { useSource } from '../data/DataSource';
import { SCENARIOS } from '../data/source';
import { liveApi, type ScenarioSpec, type ScenarioSummary } from '../data/live';
import { useRun } from '../data/run';
import { ParamHint, RuleHint } from '../components/Hint';
import { describeEdits, PARAM_HELP, SCENARIO_INFO } from '../glossary';

type Params = Record<string, unknown>;
const BASES = SCENARIOS;
type Base = (typeof BASES)[number];
const CLASSES = ['A', 'B', 'C', 'NEW'] as const;
const RULES = [
  ['rsl', 'Shelf life'],
  ['tier', 'Brand tier'],
  ['capacity', 'Channel capacity'],
] as const;
type Scalar = { key: string; step: number; min?: number; fallback?: number };
const COVERAGE: Scalar[] = [
  { key: 'coverage_days', step: 1, min: 1 },
  { key: 'coverage_alpha', step: 0.05, min: 0 },
  { key: 'channel_sku_limit_scale', step: 0.1, min: 0.1, fallback: 1 },
];
const CHOICE: Scalar[] = [
  { key: 'score_rank_weight', step: 0.05, min: 0 },
  { key: 'epsilon', step: 0.005, min: 0 },
];

/** One number of the rules page: plain name, an explanation on the info button, the allowed values underneath. */
function ScalarField({ spec, value, onValue }: { spec: Scalar; value: number; onValue: (n: number) => void }) {
  const help = PARAM_HELP[spec.key];
  return (
    <label className="rs-field" id={`field-${spec.key}`}>
      <span className="rs-field__label">
        {help.name}
        <ParamHint k={spec.key} />
      </span>
      <NumberField step={spec.step} min={spec.min} aria-label={help.name} value={value} onValue={onValue} />
      <span className="rs-field__hint">{help.range}</span>
    </label>
  );
}

const asRecord = (v: unknown): Record<string, number> => (v ?? {}) as Record<string, number>;

/** Same value for the editor, whatever the order of a list (ticking a rule off and on again is not a change). */
const canon = (v: unknown): string => JSON.stringify(Array.isArray(v) ? [...v].sort() : v);

export function Parameters() {
  const source = useSource();
  if (source === null) return <p role="status">Checking the data source</p>;
  if (source === 'cached')
    return (
      <>
        <section className="rs-page-head">
          <h2>Set the rules and run the plan</h2>
          <p className="rs-section__sub">
            Here you change the business rules, run the plan and save it as a scenario you can compare and export.
          </p>
        </section>
        <div className="rs-card" data-testid="editor-needs-live" role="status">
          <h3>Running a plan needs the live solver</h3>
          <p>
            You are looking at cached results: plans that were prepared in advance. They cannot be edited. To change a rule and run
            your own plan, start the live solver:
          </p>
          <ol className="rs-list">
            <li>
              <span>
                In a terminal, in the folder <code>apps/api</code>, run <code>uv run uvicorn main:app --port 8000</code>.
              </span>
            </li>
            <li>
              <span>
                In <code>apps/web/.env.local</code>, add <code>VITE_API_URL=/api</code> (plain UTF-8, one line) and restart the web app.
              </span>
            </li>
            <li>
              <span>Reload this page. The banner at the top will say Live solver.</span>
            </li>
          </ol>
          <div className="rs-actions">
            <Link className="rs-btn rs-btn--primary" to="/results">
              Meanwhile, open the ready plan
            </Link>
            <Link className="rs-btn" to="/compare">
              Compare the two ready scenarios
            </Link>
          </div>
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
  const [reviewing, setReviewing] = useState(false);

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

  // A button on the Plan page can open this page at one field: ?lever=coverage_days
  const [query] = useSearchParams();
  const lever = query.get('lever');
  useEffect(() => {
    if (!lever || !defaults) return;
    const box = document.getElementById(`field-${lever}`);
    box?.scrollIntoView({ block: 'center' });
    box?.querySelector<HTMLInputElement>('input')?.focus();
  }, [lever, defaults]);

  const edits = (): Params =>
    Object.fromEntries(Object.entries(params).filter(([k, v]) => canon(v) !== canon(defaults?.[k])));
  const changes = describeEdits(edits(), defaults);
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
        <h2>Set the rules and run the plan</h2>
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
              <span className="rs-field__label">Start from the scenario</span>
              <select className="rs-input" value={base} onChange={(e) => setBase(e.target.value as Base)}>
                {BASES.map((b) => (
                  <option key={b} value={b}>
                    {SCENARIO_INFO[b].name}
                  </option>
                ))}
              </select>
              <span className="rs-field__hint">{SCENARIO_INFO[base].story}</span>
            </label>
            <label className="rs-field">
              <span className="rs-field__label">SKUs</span>
              <NumberField min={1} max={2000} value={nSkus} onValue={setNSkus} aria-label="SKUs" />
              <span className="rs-field__hint">Bigger worlds solve slower</span>
            </label>
            <label className="rs-field">
              <span className="rs-field__label">Channels</span>
              <NumberField min={1} max={20} value={nChannels} onValue={setNChannels} aria-label="Channels" />
            </label>
            <label className="rs-field">
              <span className="rs-field__label">Solver time limit (s)</span>
              <NumberField min={1} max={600} value={timeLimit} onValue={setTimeLimit} aria-label="Solver time limit" />
            </label>
          </fieldset>

          <fieldset className="rs-fieldset">
            <legend>How much stock a channel takes</legend>
            {COVERAGE.map((s) => (
              <ScalarField key={s.key} spec={s} value={Number(params[s.key] ?? s.fallback ?? 0)} onValue={(n) => set(s.key, n)} />
            ))}
          </fieldset>

          <fieldset className="rs-fieldset" id="field-push_quantity_units">
            <legend>
              Push quantity for new products (units)
              <ParamHint k="push_quantity_units" />
            </legend>
            {Object.keys(asRecord(defaults.push_quantity_units)).map((c) => (
              <label key={c} className="rs-field">
                <span className="rs-field__label">{c}</span>
                <NumberField
                  min={0}
                  aria-label={`Push ${c}`}
                  value={asRecord(params.push_quantity_units)[c] ?? 0}
                  onValue={(n) => setIn('push_quantity_units', c, n)}
                />
              </label>
            ))}
            <span className="rs-field__hint">{PARAM_HELP.push_quantity_units.range}</span>
          </fieldset>

          <fieldset className="rs-fieldset">
            <legend>How the plan chooses between products</legend>
            {CHOICE.map((s) => (
              <ScalarField key={s.key} spec={s} value={Number(params[s.key] ?? 0)} onValue={(n) => set(s.key, n)} />
            ))}
          </fieldset>

          <fieldset className="rs-fieldset" id="field-score_base">
            <legend>
              Score by product class
              <ParamHint k="score_base" />
            </legend>
            {CLASSES.map((c) => (
              <label key={c} className="rs-field">
                <span className="rs-field__label">Class {c}</span>
                <NumberField
                  step={0.05}
                  aria-label={`Score class ${c}`}
                  value={asRecord(params.score_base)[c] ?? 0}
                  onValue={(n) => setIn('score_base', c, n)}
                />
              </label>
            ))}
            <span className="rs-field__hint">{PARAM_HELP.score_base.range}</span>
          </fieldset>

          <fieldset className="rs-fieldset" id="field-planner_rules">
            <legend>
              Rules the plan made by hand applies
              <ParamHint k="planner_rules" />
            </legend>
            {RULES.map(([key, label]) => (
              <div key={key} className="rs-hintrow">
                <label className="rs-check">
                  <input
                    type="checkbox"
                    checked={rules.includes(key)}
                    onChange={(e) => set('planner_rules', e.target.checked ? [...rules, key] : rules.filter((r) => r !== key))}
                  />
                  {label}
                </label>
                <RuleHint k={key} />
              </div>
            ))}
          </fieldset>

          {reviewing && (
            <section className="rs-card rs-review" data-testid="review-step" aria-label="Review before you run">
              <h3>Review before you run</h3>
              {changes.length === 0 ? (
                <p>You are using the default rules.</p>
              ) : (
                <>
                  <p>These values differ from the defaults:</p>
                  <div className="rs-review__rows">
                    {changes.map((c) => (
                      <div key={c.label} className="rs-review__row">
                        <strong>{c.label}</strong>
                        <span>
                          {c.from} to {c.to}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}
              <p className="rs-section__sub">
                Scenario "{name}": {nSkus} SKUs, {nChannels} channels, up to {timeLimit} s of solving.
              </p>
              <div className="rs-actions">
                <button type="button" className="rs-btn rs-btn--primary" disabled={busy !== null} onClick={() => void onRun()} data-testid="confirm-run">
                  {busy === 'run' ? 'Solving' : 'Confirm and run'}
                </button>
                <button type="button" className="rs-btn" disabled={busy !== null} onClick={() => setReviewing(false)} data-testid="back-to-edit">
                  Back to edit
                </button>
              </div>
            </section>
          )}

          <div className="rs-actions">
            <button type="button" className="rs-btn rs-btn--primary" disabled={busy !== null} onClick={() => setReviewing(true)} data-testid="run-solver">
              Review and run the plan
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
