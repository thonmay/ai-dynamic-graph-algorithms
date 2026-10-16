import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Cand } from '../state'
import type { CandidateFile } from '../types'
import { f3 } from '../format'

const KEYWORDS = /(\b(?:def|return|if|elif|else|for|while|in|not|and|or|is|import|from|class|None|True|False|break|continue|pass|lambda|with|as|try|except|raise|yield|global|nonlocal)\b)/

function Line({ text }: { text: string }) {
  const hash = text.indexOf('#')
  const code = hash >= 0 ? text.slice(0, hash) : text
  const parts = code.split(KEYWORDS)
  return (
    <>
      {parts.map((p, i) => (i % 2 ? <span key={i} className="kw">{p}</span> : p))}
      {hash >= 0 && <span className="cm">{text.slice(hash)}</span>}
    </>
  )
}

function Code({ text }: { text: string }) {
  return (
    <pre className="code">
      {text.replace(/\n$/, '').split('\n').map((l, i) => (
        <div key={i}><span className="no">{i + 1}</span><Line text={l} /></div>
      ))}
    </pre>
  )
}

export function Drawer({ runId, id, cands, onClose }: {
  runId: string
  id: string | null
  cands: Record<string, Cand>
  onClose: () => void
}) {
  const [shown, setShown] = useState<string | null>(id)
  const [file, setFile] = useState<CandidateFile | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { if (id) setShown(id) }, [id])
  useEffect(() => {
    if (!shown) return
    let alive = true
    setFile(null)
    setError(null)
    api<CandidateFile>(`api/runs/${encodeURIComponent(runId)}/candidates/${encodeURIComponent(shown)}`)
      .then((f) => { if (alive) setFile(f) })
      .catch((e) => { if (alive) setError(e instanceof Error ? e.message : String(e)) })
    return () => { alive = false }
  }, [runId, shown])

  const open = id !== null
  const c = shown ? cands[shown] : undefined
  const fc = c?.failingCase
  const reflection = file?.reflection?.trim().split('\n') ?? []

  return (
    <>
      <div className={`scrim${open ? ' on' : ''}`} onClick={onClose} />
      <aside className={`drawer${open ? ' on' : ''}`} role="dialog" aria-label={`Candidate ${shown ?? ''}`} inert={!open}>
        <header>
          <i className={`dot ${c?.state === 'PASS' ? 'pass' : c?.state ? 'fail' : ''}`} />
          <h2 className="mono">{shown}</h2>
          <span className="chip">{c?.state ?? 'testing'}</span>
          <button className="icon" onClick={onClose} aria-label="Close">×</button>
        </header>
        {c && (
          <div className="metrics">
            <div><b className="num">{f3(c.fitness)}</b><span>fitness</span></div>
            <div><b className="num">{f3(c.workRatio)}</b><span>work ratio</span></div>
            <div><b className="num">{c.testsTotal ? `${c.testsPassed ?? 0}/${c.testsTotal}` : '-'}</b><span>tests</span></div>
            <div><b>{c.role}</b><span>{c.parents[0] ? `← ${c.parents[0]}` : 'no parent'}</span></div>
          </div>
        )}
        {fc && (
          <section className="fail-case">
            <h4>{[fc.operation, fc.graph_n ? `n = ${fc.graph_n}` : ''].filter(Boolean).join(' · ') || 'failing case'}</h4>
            <div className="pair">
              <div><small>expected</small><span className="mono">{String(fc.expected ?? '-')}</span></div>
              <div><small>actual</small><span className="mono">{String(fc.result ?? '-')}</span></div>
            </div>
          </section>
        )}
        {c?.error && !fc && <section className="fail-case"><pre className="mono err">{c.error}</pre></section>}
        {reflection.length > 0 && (
          <details className="reflection">
            <summary>reflection</summary>
            <pre>{reflection.join('\n')}</pre>
          </details>
        )}
        {error && <div className="empty small">{error}</div>}
        {!file && !error && <div className="empty small"><span className="spinner" />loading code</div>}
        {file && <Code text={file.code} />}
      </aside>
    </>
  )
}
