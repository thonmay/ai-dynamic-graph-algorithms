// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import {
  FAIL_KINDS, rank, type AgentInfo, type Cand, type FailKind, type FailurePatterns, type GenInfo,
  type LogEntry, type LogKind,
} from '../state'
import { clock, f3, isNum, stagger } from '../format'

export type LogFilter = LogKind | 'all'
const FILTERS: LogFilter[] = ['all', 'agent', 'verify', 'control']

export function EventLog({ entries, filter, setFilter, maxGen, onPick }: {
  entries: LogEntry[]
  filter: LogFilter
  setFilter: (f: LogFilter) => void
  maxGen: number
  onPick: (id: string) => void
}) {
  const rows = entries
    .filter((e) => (filter === 'all' || e.kind === filter) && e.gen <= maxGen)
    .slice(-300)
    .reverse()
  return (
    <>
      <div className="ph">
        <h3>Events</h3>
        <div className="pills" role="group" aria-label="Filter events">
          {FILTERS.map((f) => (
            <button key={f} aria-pressed={filter === f} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>
      </div>
      <div className="log" aria-live="polite">
        {rows.length === 0 && <div className="empty small">no events yet</div>}
        {rows.map((e) => (
          <div key={e.seq} className={`row ${e.tone}${e.candidate ? ' link' : ''}`}
               onClick={e.candidate ? () => onPick(e.candidate!) : undefined}>
            <span className="t">{clock(e.ts)}</span>
            <span className="g">{e.gen ? `g${e.gen}` : ''}</span>
            <span className="msg">{e.tone === 'pass' && <i className="dot pass" />}{e.tone === 'fail' && <i className="dot fail" />}{e.text}</span>
          </div>
        ))}
      </div>
    </>
  )
}

export function Population({ gen, cands, selected, onSelect }: {
  gen: GenInfo | undefined
  cands: Record<string, Cand>
  selected: string | null
  onSelect: (id: string) => void
}) {
  if (!gen) {
    return (
      <table className="pop"><tbody>
        {[0, 1, 2].map((i) => <tr key={i} className="skeleton"><td colSpan={5}><span /></td></tr>)}
      </tbody></table>
    )
  }
  const rows = [...gen.population].sort(rank)
  const maxWr = Math.max(1e-9, ...rows.map((r) => r.work_ratio).filter(isNum))
  return (
    <table className="pop">
      <thead><tr><th>candidate</th><th>parent</th><th>role</th><th className="r">fitness</th><th>work ratio</th></tr></thead>
      <tbody>
        {rows.map((p, i) => (
          <tr key={`${gen.gen}-${p.id}`} className={p.id === selected ? 'sel' : ''} onClick={() => onSelect(p.id)}
              style={stagger(i)}>
            <td className="mono"><i className={`dot ${p.state === 'PASS' ? 'pass' : 'fail'}`} />{p.id}</td>
            <td className="mono muted">{p.parent_ids[0] ?? 'seed'}</td>
            <td className="muted">{cands[p.id]?.agent ?? cands[p.id]?.role ?? ''}</td>
            <td className="r num">{f3(p.fitness)}</td>
            <td>
              <div className="wr">
                <span className="num">{f3(p.work_ratio)}</span>
                <span className={`bar${i === 0 ? ' best' : ''}`}>
                  <i style={{ width: `${isNum(p.work_ratio) ? (p.work_ratio / maxWr) * 100 : 0}%` }} />
                </span>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

const FAIL_LABEL: Record<FailKind, string> = {
  init: 'wrong after init', insert: 'wrong after insert', delete: 'wrong after delete',
  crash: 'crash or no verdict', timeout: 'timeout',
}

/** Failure patterns: how the verified candidates of each generation failed. */
export function Failures({ fp, onSelect }: { fp: FailurePatterns; onSelect: (id: string) => void }) {
  if (!fp.byGen.length) return <div className="empty small">no verified candidates yet</div>
  const sizes = Object.entries(fp.bySize).sort((a, b) => Number(a[0]) - Number(b[0]))
  return (
    <>
      <ul className="fail-legend" aria-label="Failures by kind">
        {FAIL_KINDS.map((k) => (
          <li key={k}><i className={`fk ${k}`} />{FAIL_LABEL[k]} <span className="num">{fp.totals[k] ?? 0}</span></li>
        ))}
        {sizes.length > 0 && (
          <li className="muted">first failing graph: {sizes.map(([n, c]) => `n = ${n} (${c})`).join(', ')}</li>
        )}
      </ul>
      <table className="pop fails">
        <thead><tr><th>gen</th><th className="r">failed</th><th>kinds</th></tr></thead>
        <tbody>
          {fp.byGen.map((g, i) => (
            <tr key={g.gen} style={stagger(i)}>
              <td className="num">g{g.gen}</td>
              <td className="r num">{g.failed}/{g.verified}</td>
              <td>
                <div className="fbar" role="group"
                     aria-label={FAIL_KINDS.filter((k) => g.counts[k]).map((k) => `${g.counts[k]} ${FAIL_LABEL[k]}`).join(', ') || 'none failed'}>
                  {FAIL_KINDS.filter((k) => g.counts[k]).map((k) => (
                    <button key={k} className={`fk ${k}`} style={{ flexGrow: g.counts[k] }}
                            title={`${g.counts[k]} ${FAIL_LABEL[k]} · e.g. ${g.example[k]}`}
                            aria-label={`${FAIL_LABEL[k]}: open ${g.example[k]}`}
                            onClick={() => onSelect(g.example[k]!)} />
                  ))}
                  {g.verified > g.failed && <span className="fk pass" style={{ flexGrow: g.verified - g.failed }} />}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

/** Specialists spawned on a plateau (dynamic agent generation). */
export function Agents({ agents, viewGen }: { agents: AgentInfo[]; viewGen: number }) {
  const shown = agents.filter((a) => a.spawnedGen <= viewGen)
  return (
    <table className="pop">
      <thead><tr><th>agent</th><th>focus</th><th className="r">spawned</th><th>status</th></tr></thead>
      <tbody>
        {shown.map((a, i) => {
          const retired = a.retiredGen !== null && a.retiredGen <= viewGen
          return (
            <tr key={a.name} style={stagger(i)} title={a.signature}>
              <td className="mono"><i className={`dot ${retired ? '' : 'pass'}`} />{a.name}</td>
              <td className="muted">{a.kind}</td>
              <td className="r num">g{a.spawnedGen}</td>
              <td className="muted">{retired ? `retired g${a.retiredGen} · ${(a.retireReason ?? '').replace('_', ' ')}` : 'active'}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
