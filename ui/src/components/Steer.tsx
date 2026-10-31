// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { useEffect, useRef, useState } from 'react'
import type { Command } from '../types'

export function Steer({ open, onClose, activeHint, send }: {
  open: boolean
  onClose: () => void
  activeHint: string | null
  send: (c: Command) => void
}) {
  const [hint, setHint] = useState('')
  const [budget, setBudget] = useState('')
  const [pop, setPop] = useState('')
  const first = useRef<HTMLInputElement>(null)

  useEffect(() => { if (open) first.current?.focus() }, [open])

  const apply = (e: React.FormEvent) => {
    e.preventDefault()
    if (hint.trim()) send({ cmd: 'hint', text: hint.trim() })
    if (budget) send({ cmd: 'set', field: 'model_call_budget', value: Number(budget) })
    if (pop) send({ cmd: 'set', field: 'population_size', value: Number(pop) })
    setHint('')
    setBudget('')
    setPop('')
    onClose()
  }

  return (
    <form className={`pop-over${open ? ' on' : ''}`} onSubmit={apply} inert={!open} aria-label="Steer the run">
      <label>Hint
        <input ref={first} value={hint} onChange={(e) => setHint(e.target.value)} maxLength={2000}
               placeholder={activeHint ? `now: ${activeHint}` : 'e.g. avoid full recompute on delete'} />
      </label>
      <div className="two">
        <label>Call budget
          <input type="number" min={1} max={100000} value={budget} onChange={(e) => setBudget(e.target.value)} />
        </label>
        <label>Population
          <input type="number" min={1} max={50} value={pop} onChange={(e) => setPop(e.target.value)} />
        </label>
      </div>
      <div className="actions">
        {activeHint && (
          <button type="button" className="btn" onClick={() => { send({ cmd: 'hint', text: '' }); onClose() }}>
            Clear hint
          </button>
        )}
        <button type="submit" className="btn primary" disabled={!hint.trim() && !budget && !pop}>
          Apply at next generation
        </button>
      </div>
    </form>
  )
}
