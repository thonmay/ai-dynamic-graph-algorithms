import { rank, type Cand, type GenInfo, type LogEntry, type LogKind } from '../state'
import { clock, f3, isNum } from '../format'

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
              style={{ ['--i' as string]: i }}>
            <td className="mono"><i className={`dot ${p.state === 'PASS' ? 'pass' : 'fail'}`} />{p.id}</td>
            <td className="mono muted">{p.parent_ids[0] ?? 'seed'}</td>
            <td className="muted">{cands[p.id]?.role ?? ''}</td>
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
