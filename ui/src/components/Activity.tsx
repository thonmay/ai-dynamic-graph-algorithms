// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { useState } from 'react'
import { genAt, type Live, type RunState } from '../state'
import { duration, f3 } from '../format'

const VERB: Record<string, string> = {
  seed: 'Seeding', fresh: 'Generating', mutate: 'Mutating', repair: 'Repairing', reflect: 'Reflecting',
  specialist: 'Specialist on',
}

const REASON: Record<string, string> = {
  max_generations: 'generation limit', success: 'correct candidate found', user_stop: 'stopped by you',
  model_call_budget_exhausted: 'call budget used', consecutive_all_failed: 'no progress',
  agent_unavailable: 'agent backend failed',
}

function Copy({ text }: { text: string }) {
  const [done, setDone] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setDone(true)
      setTimeout(() => setDone(false), 1500)
    } catch {
      window.prompt('Copy', text)
    }
  }
  return <button className="btn" onClick={copy}>{done ? 'Copied' : 'Copy'}</button>
}

/** One line under the nav: what the engine is doing right now. */
export function Activity({ state, status, runId, now }: {
  state: RunState
  status: Live
  runId: string
  now: number
}) {
  const call = state.call
  const lastGen = state.gens.at(-1)?.gen ?? 0
  const since = (ts: string) => duration(now - Date.parse(ts))
  let tone = 'idle'
  let body: React.ReactNode

  if (status === 'interrupted') {
    tone = 'fail'
    const cmd = `evoalgo resume runs/${runId}`
    body = <>Engine stopped<code className="mono">{cmd}</code><Copy text={cmd} /></>
  } else if (status === 'offline') {
    tone = 'warn'
    body = <><span className="spinner sm" />Reconnecting</>
  } else if (status === 'paused') {
    tone = 'warn'
    const b = state.pausedBefore
    body = b ? <>Paused before {b.role}<b className="mono">{b.id}</b></> : <>Paused</>
  } else if (status === 'done' || status === 'stopped') {
    tone = status === 'done' ? 'done' : 'fail'
    const g = genAt(state, lastGen)
    body = <>{status === 'done' ? 'Finished' : 'Stopped'} · {REASON[state.stopReason ?? ''] ?? state.stopReason ?? 'ended'}
      {g?.bestId && <> · best<b className="mono">{g.bestId}</b>wr {f3(g.bestWorkRatio)}</>}</>
  } else if (status === 'starting' || status === 'empty') {
    body = status === 'starting' ? <><span className="spinner sm" />Starting</> : <>No events yet</>
  } else if (call) {
    tone = status === 'running' ? 'busy' : 'warn'
    const lead = status === 'pausing' ? 'Pausing after this call · '
      : status === 'stopping' ? 'Stopping after this call · ' : ''
    body = <>{lead}{VERB[call.role] ?? call.role}<b className="mono">{call.id}</b>
      <span className="num muted">{since(call.ts)}</span></>
  } else if (state.currentGen > lastGen) {
    tone = status === 'running' ? 'busy' : 'warn'
    const lead = status === 'pausing' ? 'Pausing next · ' : status === 'stopping' ? 'Stopping next · ' : ''
    body = <>{lead}Verifying gen {state.currentGen}</>
  } else {
    const g = genAt(state, lastGen)
    body = g ? <>Committed gen {g.gen} · best<b className="mono">{g.bestId ?? '-'}</b>wr {f3(g.bestWorkRatio)}</>
      : <>Waiting</>
  }

  return (
    <div className={`activity ${tone}`} role="status" aria-live="polite">
      <i className="dot" />
      <span className="what">{body}</span>
      {(tone === 'busy' || (tone === 'warn' && status !== 'paused' && status !== 'offline')) && (
        <span className="indeterminate" aria-hidden="true" />
      )}
    </div>
  )
}
