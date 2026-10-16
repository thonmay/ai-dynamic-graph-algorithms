import { useEffect, useState, type CSSProperties } from 'react'
import { api } from '../api'
import type { LaunchBody, RunSummary } from '../types'
import { f3, stamp } from '../format'
import { Spark } from './charts'

function Launch() {
  const [configs, setConfigs] = useState<string[]>([])
  const [body, setBody] = useState<LaunchBody>({ config: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<string[]>('api/configs').then((c) => {
      setConfigs(c)
      setBody((b) => (b.config ? b : { ...b, config: c[0] ?? '' }))
    }).catch((e) => setError(e.message))
  }, [])

  const num = (v: string) => (v === '' ? undefined : Number(v))
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const clean = Object.fromEntries(Object.entries(body).filter(([, v]) => v !== undefined && v !== ''))
      const r = await api<{ run_id: string }>('api/runs', { method: 'POST', body: JSON.stringify(clean) })
      location.hash = `#/run/${encodeURIComponent(r.run_id)}`
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="panel launch" onSubmit={submit} style={{ ['--i' as string]: 0 } as CSSProperties}>
      <label className="grow">Config
        <select value={body.config} onChange={(e) => setBody({ ...body, config: e.target.value })}>
          {configs.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </label>
      <label>Run id
        <input placeholder="auto" value={body.run_id ?? ''} pattern="[A-Za-z0-9][A-Za-z0-9_.\-]*"
               onChange={(e) => setBody({ ...body, run_id: e.target.value || undefined })} />
      </label>
      <label className="narrow">Gens
        <input type="number" min={1} max={1000} value={body.max_generations ?? ''}
               onChange={(e) => setBody({ ...body, max_generations: num(e.target.value) })} />
      </label>
      <label className="narrow">Pop
        <input type="number" min={1} max={50} value={body.population_size ?? ''}
               onChange={(e) => setBody({ ...body, population_size: num(e.target.value) })} />
      </label>
      <label className="grow">Model
        <input placeholder="from config" value={body.model ?? ''}
               onChange={(e) => setBody({ ...body, model: e.target.value || undefined })} />
      </label>
      <button className="btn primary" disabled={busy || !body.config}>{busy ? 'Starting' : 'Launch'}</button>
      {error && <p className="form-error">{error}</p>}
    </form>
  )
}

export function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = () => api<RunSummary[]>('api/runs')
      .then((r) => { if (alive) { setRuns(r); setError(null) } })
      .catch((e) => { if (alive) setError(e.message) })
    load()
    const t = setInterval(load, 4000)
    return () => { alive = false; clearInterval(t) }
  }, [])

  return (
    <>
      <nav className="top"><div className="bar"><a className="word" href="#/">evoalgo</a><span className="sp" /></div></nav>
      <main className="wrap">
        <h1 className="title">Runs</h1>
        <Launch />
        <section className="panel list" style={{ ['--i' as string]: 1 } as CSSProperties}>
          {error && <div className="empty small">{error}</div>}
          {!runs && !error && [0, 1, 2, 3].map((i) => <div key={i} className="run skeleton"><span /></div>)}
          {runs?.length === 0 && <div className="empty">no runs yet · launch one above</div>}
          {runs?.map((r, i) => (
            <a key={r.run_id} className="run" href={`#/run/${encodeURIComponent(r.run_id)}`}
               style={{ ['--i' as string]: i } as CSSProperties}>
              <span className={`status ${r.state}`}><i className="dot" /></span>
              <span className="name">
                <b className="mono">{r.run_id}</b>
                <small>{r.has_events ? `${r.problem ?? ''} · ${stamp(r.updated)}` : 'no event log · evoalgo events backfill'}</small>
              </span>
              <span className="num gen">{r.has_events ? `${r.generation}/${r.max_generations ?? '-'}` : ''}</span>
              <Spark values={r.history ?? []} width={80} />
              <span className="num wr">{r.has_events ? f3(r.best_work_ratio) : ''}</span>
              <span className="chev">›</span>
            </a>
          ))}
        </section>
      </main>
    </>
  )
}
