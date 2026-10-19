import { useEffect, useState, type CSSProperties } from 'react'
import { api } from '../api'
import type { RunSummary } from '../types'
import { f3, stamp } from '../format'
import { Spark } from './charts'

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
      <nav className="top"><div className="bar">
        <a className="word" href="#/">evoalgo</a><span className="sp" />
        <a className="btn primary" href="#/new">New run</a>
      </div></nav>
      <main className="wrap">
        <h1 className="title">Runs</h1>
        <section className="panel list" style={{ ['--i' as string]: 0 } as CSSProperties}>
          {error && <div className="empty small">{error}</div>}
          {!runs && !error && [0, 1, 2, 3].map((i) => <div key={i} className="run skeleton"><span /></div>)}
          {runs?.length === 0 && (
            <div className="empty">No runs yet<a className="btn primary" href="#/new">Start the first run</a></div>
          )}
          {runs?.map((r, i) => (
            <a key={r.run_id} className="run" href={`#/run/${encodeURIComponent(r.run_id)}`}
               style={{ ['--i' as string]: i } as CSSProperties}>
              <span className={`status ${r.state}`}><i className="dot" /></span>
              <span className="name">
                <b className="mono">{r.run_id}</b>
                <small>{r.has_events
                  ? <>{r.pack ?? r.problem ?? ''} · {stamp(r.updated)}{r.research_goal ? <> · <span className="goal-inline">{r.research_goal}</span></> : null}</>
                  : 'no event log · evoalgo events backfill'}</small>
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
