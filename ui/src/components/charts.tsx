// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { bestPath, type GenInfo, type RunState } from '../state'
import { f3, isNum, short } from '../format'

const W = 560

export function Spark({ values, width = 90, height = 22 }: {
  values: (number | null | undefined)[]
  width?: number
  height?: number
}) {
  const v = values.filter(isNum)
  if (v.length < 2) return <svg className="spark" width={width} height={height} aria-hidden="true" />
  const mn = Math.min(...v)
  const range = Math.max(...v) - mn || 1
  const pts = v
    .map((x, i) => `${((i / (v.length - 1)) * width).toFixed(1)},${(height - 2 - ((x - mn) / range) * (height - 4)).toFixed(1)}`)
    .join(' ')
  return (
    <svg className="spark" width={width} height={height} aria-hidden="true">
      <polyline key={v.length} points={pts} pathLength={1} className="draw" />
    </svg>
  )
}

export function WorkRatioChart({ gens, maxGen, viewGen, onPick }: {
  gens: GenInfo[]
  maxGen: number
  viewGen: number
  onPick: (gen: number) => void
}) {
  const H = 230, L = 44, R = 16, T = 14, B = 30
  const n = Math.max(2, maxGen, gens.at(-1)?.gen ?? 1)
  const X = (g: number) => L + ((g - 1) / (n - 1)) * (W - L - R)
  const values = gens.flatMap((g) => [g.bestWorkRatio, g.meanWorkRatio]).filter(isNum)
  const top = Math.max(0.1, Math.ceil(Math.max(0, ...values) * 10) / 10)
  const Y = (v: number) => T + (1 - v / top) * (H - T - B)
  const line = (key: 'bestWorkRatio' | 'meanWorkRatio') =>
    gens.filter((g) => isNum(g[key])).map((g) => `${X(g.gen).toFixed(1)},${Y(g[key] as number).toFixed(1)}`).join(' ')
  const every = Math.ceil(n / 10)
  const labels = Array.from({ length: n }, (_, i) => i + 1).filter((g) => g === 1 || g === n || g % every === 0)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Work ratio per generation">
      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
        <g key={t}>
          <line x1={L} x2={W - R} y1={Y(t * top)} y2={Y(t * top)} className="grid" />
          <text x={L - 8} y={Y(t * top) + 4} textAnchor="end">{(t * top).toFixed(2)}</text>
        </g>
      ))}
      {labels.map((g) => <text key={g} x={X(g)} y={H - 8} textAnchor="middle">g{g}</text>)}
      {gens.length > 0 && viewGen >= 1 && (
        <rect className="band" x={X(Math.min(viewGen, n)) - 10} y={T} width={20} height={H - T - B} rx={10} />
      )}
      <polyline key={`m${gens.length}`} points={line('meanWorkRatio')} pathLength={1} className="line mean draw" />
      <polyline key={`b${gens.length}`} points={line('bestWorkRatio')} pathLength={1} className="line best draw" />
      {gens.map((g) => (
        <g key={g.gen} className="pt" onClick={() => onPick(g.gen)}>
          <rect x={X(g.gen) - 12} y={T} width={24} height={H - T - B} fill="transparent" />
          {isNum(g.meanWorkRatio) && <circle cx={X(g.gen)} cy={Y(g.meanWorkRatio)} r={3} className="dot-mean" />}
          {isNum(g.bestWorkRatio) && <circle cx={X(g.gen)} cy={Y(g.bestWorkRatio)} r={4.5} className="dot-best" />}
          <title>{`gen ${g.gen} · best ${f3(g.bestWorkRatio)} · mean ${f3(g.meanWorkRatio)}`}</title>
        </g>
      ))}
    </svg>
  )
}

export function Lineage({ state, viewGen, bestGen, selected, onSelect }: {
  state: RunState
  viewGen: number
  bestGen: number
  selected: string | null
  onSelect: (id: string) => void
}) {
  const cols = Math.max(1, viewGen)
  const width = Math.max(W, 80 + cols * 64)
  const X = (g: number) => (cols === 1 ? width / 2 : 40 + ((g - 1) / (cols - 1)) * (width - 80))
  const visible = state.order.map((id) => state.cands[id]).filter((c) => c.gen <= viewGen)
  const rows: Record<number, number> = {}
  const pos: Record<string, [number, number]> = {}
  for (const c of visible) {
    const r = rows[c.gen] ?? 0
    rows[c.gen] = r + 1
    pos[c.id] = [X(c.gen), 40 + r * 52]
  }
  const H = Math.max(230, 40 + Math.max(1, ...Object.values(rows)) * 52 + 20)
  const path = bestPath(state, bestGen)
  const onPath = new Set(path)
  const best = path[0]

  if (!visible.length) {
    return <div className="empty"><span className="spinner" />waiting for the first candidate</div>
  }
  return (
    <div className="scroll-x">
      <svg viewBox={`0 0 ${width} ${H}`} className="lineage" style={{ width: width > W ? `${width}px` : '100%' }}
           role="img" aria-label="Candidate lineage">
        {Array.from({ length: cols }, (_, i) => i + 1).map((g) => (
          <g key={g}>
            <text x={X(g)} y={H - 6} textAnchor="middle">g{g}</text>
            {state.genHints[g] && (
              <text x={X(g)} y={16} textAnchor="middle" className="hint-tag">hint<title>{state.genHints[g]}</title></text>
            )}
          </g>
        ))}
        {visible.flatMap((c) => c.parents.filter((p) => pos[p]).map((p) => {
          const [x1, y1] = pos[p]
          const [x2, y2] = pos[c.id]
          const hot = onPath.has(c.id) && onPath.has(p)
          return (
            <path key={`${p}>${c.id}`} d={`M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`}
                  pathLength={1} className={`edge draw${hot ? ' hot' : ''}`} />
          )
        }))}
        {visible.map((c) => {
          const [x, y] = pos[c.id]
          const cls = ['node',
            c.id === best ? 'best' : '',
            c.state === null ? 'pending' : c.state !== 'PASS' ? 'fail' : '',
            c.discarded ? 'gone' : '',
            c.id === selected ? 'sel' : ''].filter(Boolean).join(' ')
          return (
            <g key={c.id} className={cls} onClick={() => onSelect(c.id)}>
              <circle cx={x} cy={y} r={c.id === best ? 9 : 7} />
              <text x={x} y={y + 22} textAnchor="middle">
                {short(c.id)} · {isNum(c.workRatio) ? c.workRatio.toFixed(2) : c.state ?? '...'}
              </text>
              <title>{`${c.id} · ${c.role}${c.parents.length ? ` ← ${c.parents.join(', ')}` : ''} · ${c.state ?? 'testing'}`}</title>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
