// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { api } from '../api'
import type { AgentOptions, EndpointId, LaunchBody, PackInfo, RunSummary } from '../types'

type Step = 1 | 2 | 3 | 4
const STEPS: { n: Step; label: string }[] = [
  { n: 1, label: 'Problem' }, { n: 2, label: 'Goal' }, { n: 3, label: 'Budget' }, { n: 4, label: 'Review' },
]

interface Preset { id: string; label: string; gens: number; pop: number; budget: number }
const PRESETS: Preset[] = [
  { id: 'smoke', label: 'Smoke', gens: 2, pop: 2, budget: 10 },
  { id: 'standard', label: 'Standard', gens: 10, pop: 4, budget: 200 },
  { id: 'deep', label: 'Deep', gens: 30, pop: 8, budget: 1000 },
]

const TIER_LABEL: Record<string, string> = { calibration: 'calibration', core: 'core', open: 'open problem' }

/** Short, pack-independent starting points; the researcher edits them. */
const GOAL_STARTERS = [
  'Find an update rule that avoids a full recompute after deletions.',
  'Reach full correctness first, then lower the work ratio.',
  'Handle insertions with near-constant work per update.',
]

interface Form {
  pack: string
  goal: string
  preset: string
  gens: number
  pop: number
  budget: number
  model: string
  /** An endpoint id (agent loop runs here, model over that API) or 'opencode' (local harness). */
  agent: EndpointId | 'opencode'
  nMax: number
  stopAtFirst: boolean
  dynamicAgents: boolean
  runId: string
}

const MEMORY_KEY = 'evoalgo.newrun'

function remembered(): Partial<Form> {
  try {
    return JSON.parse(localStorage.getItem(MEMORY_KEY) || '{}')
  } catch {
    return {}
  }
}

const AGENT_IDS: Form['agent'][] = ['openrouter', 'openai', 'opencode']

function initialForm(prefill: Partial<Form>): Form {
  const std = PRESETS[1]
  const mem = remembered()
  const f: Form = {
    pack: '', goal: '', preset: mem.preset ?? std.id, gens: mem.gens ?? std.gens, pop: mem.pop ?? std.pop,
    budget: mem.budget ?? std.budget, model: mem.model ?? '', agent: mem.agent ?? 'openrouter', nMax: 5, stopAtFirst: false, dynamicAgents: false, runId: '',
    ...(mem.pack ? { pack: mem.pack } : {}), ...prefill,
  }
  // A stale localStorage value, or a run from mock / a custom URL, has no menu entry.
  if (!AGENT_IDS.includes(f.agent)) f.agent = 'openrouter'
  return f
}

/** Prefill from "#/new?from=<run_id>" (Run again). */
function useFromRun(): { prefill: Partial<Form> | null; source: string | null } {
  const source = new URLSearchParams(location.hash.split('?')[1] ?? '').get('from')
  const [prefill, setPrefill] = useState<Partial<Form> | null>(source ? null : {})
  useEffect(() => {
    if (!source) return
    api<RunSummary & { config?: Record<string, any> }>(`api/runs/${encodeURIComponent(source)}`)
      .then((r) => {
        const c = r.config ?? {}
        setPrefill({
          // Runs from before packs existed only have `problem`; packs share its name.
          pack: c.pack ?? c.problem ?? '', goal: c.research_goal ?? '', gens: c.max_generations, pop: c.population_size,
          budget: c.model_call_budget, model: c.model ?? '', nMax: c.bound?.n_max ?? 5,
          agent: c.provider === 'api' && ['openrouter', 'openai'].includes(c.api_base_url)
            ? c.api_base_url : c.provider === 'opencode' ? 'opencode' : 'openrouter',
          stopAtFirst: !!c.early_stop_on_success, dynamicAgents: !!c.dynamic_agents, preset: 'custom',
        })
      })
      .catch(() => setPrefill({}))
  }, [source])
  return { prefill, source }
}

const RUN_ID = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$/

/** Inline validation for the review step: blocking errors stop Launch, notes only inform. */
export function reviewIssues(f: Form, pack: PackInfo | undefined,
                             agents?: AgentOptions | null): { blocking: string[]; notes: string[] } {
  const blocking: string[] = []
  const notes: string[] = []
  const inRange = (v: number, lo: number, hi: number) => Number.isInteger(v) && v >= lo && v <= hi
  if (!pack) blocking.push('Choose a problem')
  if (!inRange(f.gens, 1, 1000)) blocking.push('Generations must be 1 to 1000')
  if (!inRange(f.pop, 1, 50)) blocking.push('Population must be 1 to 50')
  if (!inRange(f.budget, 1, 100000)) blocking.push('Call budget must be 1 to 100000')
  if (!inRange(f.nMax, 2, 8)) blocking.push('Verifier n max must be 2 to 8')
  if (f.runId.trim() && !RUN_ID.test(f.runId.trim())) blocking.push('Run id: letters, digits, . _ - only')
  if (f.agent !== 'opencode') {
    const ep = agents?.endpoints.find((e) => e.id === f.agent)
    if (!f.model.trim()) blocking.push('Choose a model for the API endpoint')
    if (ep && !ep.key_set) blocking.push(`Key not set: export ${ep.key_env} before starting evoalgo ui`)
  } else if (agents && !agents.harness.available) {
    blocking.push('opencode not found on this machine')
  }
  if (!f.goal.trim()) notes.push('No goal set')
  // One generate call per slot, plus reflection on failures: a rough floor.
  if (blocking.length === 0 && f.budget < f.gens * f.pop) notes.push('Call budget may stop the run early')
  return { blocking, notes }
}

function Tags({ p }: { p: PackInfo }) {
  return (
    <span className="tags">
      <span className={`tag tier-${p.tier}`}>{TIER_LABEL[p.tier] ?? p.tier}</span>
      <span className="tag">{p.directed ? 'directed' : 'undirected'}</span>
      {p.needs_root && <span className="tag">rooted</span>}
    </span>
  )
}

export function NewRunPage() {
  const { prefill, source } = useFromRun()
  const [packs, setPacks] = useState<PackInfo[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<Form | null>(null)
  const [step, setStep] = useState<Step>(1)
  const [busy, setBusy] = useState(false)
  const [briefOpen, setBriefOpen] = useState(false)
  const [agents, setAgents] = useState<AgentOptions | null>(null)
  const goalRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    api<PackInfo[]>('api/packs').then(setPacks).catch((e) => setError(e.message))
    api<AgentOptions>('api/agents').then(setAgents).catch(() => setAgents(null))
  }, [])

  useEffect(() => {
    if (!packs || !prefill || form) return
    const f = initialForm(prefill)
    if (!packs.some((p) => p.name === f.pack)) f.pack = packs.find((p) => p.name === 'dynamic_mcs')?.name ?? packs[0]?.name ?? ''
    setForm(f)
    if (source) setStep(4)
  }, [packs, prefill, form, source])

  useEffect(() => { if (step === 2) goalRef.current?.focus() }, [step])

  const pack = useMemo(() => packs?.find((p) => p.name === form?.pack), [packs, form?.pack])
  const set = (patch: Partial<Form>) => setForm((f) => (f ? { ...f, ...patch } : f))
  const custom = (patch: Partial<Form>) => set({ ...patch, preset: 'custom' })
  const endpoint = agents?.endpoints.find((e) => e.id === form?.agent)
  const suggestedModel = (agent: Form['agent']) => agents?.endpoints.find((e) => e.id === agent)?.model ?? ''
  const chooseAgent = (agent: Form['agent']) => {
    // Swap the model only if it is empty or still the previous suggestion.
    if (!form) return
    const keep = form.model.trim() && form.model !== suggestedModel(form.agent)
    set({ agent, ...(keep ? {} : { model: suggestedModel(agent) }) })
  }
  // First load: an empty model takes the endpoint's suggestion.
  useEffect(() => {
    if (agents && form && !form.model.trim()) {
      const m = agents.endpoints.find((e) => e.id === form.agent)?.model
      if (m) set({ model: m })
    }
  }, [agents, form === null]) // once both have loaded; later edits are the user's

  const launch = async () => {
    if (!form || !pack) return
    setBusy(true)
    setError(null)
    const body: LaunchBody = {
      pack: pack.name, research_goal: form.goal.trim() || undefined, max_generations: form.gens,
      population_size: form.pop, model_call_budget: form.budget, model: form.model.trim() || undefined,
      ...(form.agent === 'opencode' ? { provider: 'opencode' } : { provider: 'api', endpoint: form.agent }),
      n_max: form.nMax, early_stop_on_success: form.stopAtFirst, dynamic_agents: form.dynamicAgents,
      run_id: form.runId.trim() || undefined,
    }
    try {
      const r = await api<{ run_id: string }>('api/runs', { method: 'POST', body: JSON.stringify(body) })
      localStorage.setItem(MEMORY_KEY, JSON.stringify({
        pack: form.pack, preset: form.preset, gens: form.gens, pop: form.pop, budget: form.budget, model: form.model,
        agent: form.agent,
      }))
      location.hash = `#/run/${encodeURIComponent(r.run_id)}`
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setBusy(false)
    }
  }

  const canNext = step !== 1 || !!pack
  const issues = form ? reviewIssues(form, pack, agents) : { blocking: [], notes: [] }

  return (
    <>
      <nav className="top"><div className="bar">
        <a className="word" href="#/">evoalgo</a>
        <span className="crumb">New run</span>
        <span className="sp" />
        <a className="btn" href="#/">Cancel</a>
      </div></nav>

      <main className="wrap narrow">
        <header className="newrun-head">
          <h1 className="title">{source ? 'Run again' : 'New run'}</h1>
          <ol className="stepper" aria-label="Steps">
            {STEPS.map((s) => (
              <li key={s.n}>
                <button className={`stp${s.n === step ? ' on' : ''}${s.n < step ? ' done' : ''}`}
                        aria-current={s.n === step ? 'step' : undefined}
                        disabled={!form || (s.n > 1 && !pack)} onClick={() => setStep(s.n)}>
                  <i>{s.n < step ? '✓' : s.n}</i>{s.label}
                </button>
              </li>
            ))}
          </ol>
        </header>

        {error && <div className="panel form-error-panel" role="alert">{error}</div>}
        {!form && !error && (
          <section className="packs">{[0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="pack skeleton"><span /></div>)}</section>
        )}

        {form && packs && (
          <div key={step} className="step-body">
            {step === 1 && (
              <section className="packs" aria-label="Problem packs">
                {packs.map((p, i) => (
                  <button key={p.name} className="pack" aria-pressed={p.name === form.pack}
                          style={{ ['--i' as string]: i } as CSSProperties}
                          onClick={() => set({ pack: p.name })} onDoubleClick={() => { set({ pack: p.name }); setStep(2) }}>
                    <span className="pk-title">{p.title}</span>
                    <span className="pk-q">{p.question ?? p.name}</span>
                    <Tags p={p} />
                  </button>
                ))}
              </section>
            )}

            {step === 2 && pack && (
              <section className="panel goal-panel">
                <div className="ph"><h3>{pack.title}</h3><Tags p={pack} /></div>
                <label className="field">
                  <span>What do you want to find out in this run?</span>
                  <textarea ref={goalRef} value={form.goal} maxLength={2000} rows={5}
                            placeholder="Optional. The brief alone is enough to start."
                            onChange={(e) => set({ goal: e.target.value })} />
                </label>
                <div className="goal-foot">
                  <div className="chips">
                    {GOAL_STARTERS.map((g) => (
                      <button key={g} className="chip" onClick={() => set({ goal: g })}>{g}</button>
                    ))}
                  </div>
                  <span className="num muted small">{form.goal.length}/2000</span>
                </div>
                <button className="link" onClick={() => setBriefOpen((o) => !o)} aria-expanded={briefOpen}>
                  {briefOpen ? 'Hide brief' : 'Read brief'}
                </button>
                <div className={`brief-wrap${briefOpen ? ' on' : ''}`}><pre className="brief">{pack.brief.trim()}</pre></div>
              </section>
            )}

            {step === 3 && (
              <section className="panel">
                <div className="presets" role="radiogroup" aria-label="Budget preset">
                  {PRESETS.map((p) => (
                    <button key={p.id} role="radio" aria-checked={form.preset === p.id} className="preset"
                            onClick={() => set({ preset: p.id, gens: p.gens, pop: p.pop, budget: p.budget })}>
                      <b>{p.label}</b>
                      <span className="num">{p.gens} gens · pop {p.pop}</span>
                      <span className="num muted">{p.budget} calls</span>
                    </button>
                  ))}
                </div>
                <div className="grid3">
                  <label className="field"><span>Generations</span>
                    <input type="number" min={1} max={1000} value={form.gens}
                           onChange={(e) => custom({ gens: Number(e.target.value) })} /></label>
                  <label className="field"><span>Population</span>
                    <input type="number" min={1} max={50} value={form.pop}
                           onChange={(e) => custom({ pop: Number(e.target.value) })} /></label>
                  <label className="field"><span>Call budget</span>
                    <input type="number" min={1} max={100000} value={form.budget}
                           onChange={(e) => custom({ budget: Number(e.target.value) })} /></label>
                </div>
                <div className="grid3 agents-row">
                  <label className="field"><span>Agents</span>
                    <select value={form.agent} onChange={(e) => chooseAgent(e.target.value as Form['agent'])}>
                      {(agents?.endpoints ?? [{ id: 'openrouter', label: 'OpenRouter', key_set: true }]).map((e) => (
                        <option key={e.id} value={e.id}>{e.label} API{e.key_set ? '' : ' (no key)'}</option>
                      ))}
                      <option value="opencode">opencode harness{agents && !agents.harness.available ? ' (not found)' : ''}</option>
                    </select></label>
                  <label className="field span2"><span>Model</span>
                    <input value={form.model} spellCheck={false}
                           placeholder={form.agent === 'opencode' ? 'harness default' : endpoint?.model ?? 'model id'}
                           onChange={(e) => set({ model: e.target.value })} /></label>
                </div>
                <details className="adv">
                  <summary>Advanced</summary>
                  <div className="grid3">
                    <label className="field"><span>Verifier n max</span>
                      <input type="number" min={2} max={8} value={form.nMax} onChange={(e) => set({ nMax: Number(e.target.value) })} /></label>
                    <label className="field"><span>Run id</span>
                      <input value={form.runId} placeholder="automatic" pattern="[A-Za-z0-9][A-Za-z0-9_.\-]*"
                             onChange={(e) => set({ runId: e.target.value })} /></label>
                  </div>
                  <label className="toggle">
                    <input type="checkbox" checked={form.stopAtFirst} onChange={(e) => set({ stopAtFirst: e.target.checked })} />
                    <i />Stop at the first fully correct candidate
                  </label>
                  <label className="toggle">
                    <input type="checkbox" checked={form.dynamicAgents} onChange={(e) => set({ dynamicAgents: e.target.checked })} />
                    <i />Spawn a specialist agent when the search plateaus
                  </label>
                </details>
              </section>
            )}

            {step === 4 && pack && (
              <section className="panel review">
                <div className="rv-row" onClick={() => setStep(1)}>
                  <span className="rv-k">Problem</span>
                  <span className="rv-v"><b>{pack.title}</b><Tags p={pack} /></span>
                  <span className="rv-edit">Edit</span>
                </div>
                <div className="rv-row" onClick={() => setStep(2)}>
                  <span className="rv-k">Goal</span>
                  <span className="rv-v">{form.goal.trim()
                    ? <span className="rv-goal">{form.goal.trim()}</span>
                    : <span className="warn-text">None set · agents follow the brief</span>}</span>
                  <span className="rv-edit">Edit</span>
                </div>
                <div className="rv-row" onClick={() => setStep(3)}>
                  <span className="rv-k">Budget</span>
                  <span className="rv-v num">{form.gens} generations · population {form.pop} · {form.budget} calls</span>
                  <span className="rv-edit">Edit</span>
                </div>
                <div className="rv-row" onClick={() => setStep(3)}>
                  <span className="rv-k">Verifier</span>
                  <span className="rv-v num">all non-isomorphic graphs, n ≤ {form.nMax} · {pack.update_mode.replace('_', ' ')} updates
                    {form.stopAtFirst ? ' · stop at first correct' : ''}
                    {form.dynamicAgents ? ' · dynamic agents' : ''}</span>
                  <span className="rv-edit">Edit</span>
                </div>
                <div className="rv-row" onClick={() => setStep(3)}>
                  <span className="rv-k">Agents</span>
                  <span className="rv-v"><span className="mono">{form.model.trim() || 'harness default'}</span>
                    <span className="muted"> · {form.agent === 'opencode' ? 'opencode harness' : `${endpoint?.label ?? form.agent} API`}</span></span>
                  <span className="rv-edit">Edit</span>
                </div>
                {(issues.blocking.length > 0 || issues.notes.some((n) => n !== 'No goal set')) && (
                  <div className="rv-issues" role="alert">
                    {issues.blocking.map((m) => <span key={m} className="issue bad">{m}</span>)}
                    {issues.notes.filter((n) => n !== 'No goal set').map((m) => <span key={m} className="issue">{m}</span>)}
                  </div>
                )}
                {pack.lean && (
                  <div className="rv-row static">
                    <span className="rv-k">Lean</span>
                    <span className="rv-v">Proof attempt for the best correct candidate after the run</span>
                    <span />
                  </div>
                )}
              </section>
            )}
          </div>
        )}

        {form && (
          <footer className="step-actions">
            {step > 1 && <button className="btn lg" onClick={() => setStep((step - 1) as Step)}>Back</button>}
            <span className="sp" />
            {step < 4 && step > 1 && <button className="btn lg ghost" onClick={() => setStep(4)}>Skip to review</button>}
            {step < 4
              ? <button className="btn lg primary" disabled={!canNext} onClick={() => setStep((step + 1) as Step)}>Continue</button>
              : <button className="btn lg primary" disabled={busy || issues.blocking.length > 0} onClick={launch}>
                  {busy ? <><span className="spinner xs" />Starting</> : 'Launch run'}
                </button>}
          </footer>
        )}
      </main>
    </>
  )
}
