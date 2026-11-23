// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { useEffect, useState } from 'react'
import { useRunStream } from '../api'
import { deriveStatus, failurePatterns, genAt, type Live } from '../state'
import { duration, f3, pct, stagger } from '../format'
import { Activity } from './Activity'
import { Lineage, Spark, WorkRatioChart } from './charts'
import { Agents, EventLog, Failures, Population, type LogFilter } from './panels'
import { Drawer } from './Drawer'
import { Steer } from './Steer'
import { Toast } from './Toast'

const LABEL: Record<Live, string> = {
  starting: 'starting', empty: 'no events', running: 'running', pausing: 'pausing', paused: 'paused',
  resuming: 'resuming', stopping: 'stopping', stopped: 'stopped', done: 'done',
  interrupted: 'interrupted', offline: 'offline',
}
const ACTIVE: Live[] = ['running', 'pausing', 'paused', 'resuming', 'stopping']

export function RunPage({ runId }: { runId: string }) {
  const { state, connected, refused, notice, send } = useRunStream(runId)
  const [mode, setMode] = useState<'live' | 'replay'>('live')
  const [replayGen, setReplayGen] = useState(1)
  const [playing, setPlaying] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [steerOpen, setSteerOpen] = useState(false)
  const [filter, setFilter] = useState<LogFilter>('all')
  const [now, setNow] = useState(Date.now())

  const lastGen = state.gens.at(-1)?.gen ?? 0
  const maxGen = state.meta?.max_generations ?? lastGen
  const live = mode === 'live'
  const popGen = live ? lastGen : Math.min(replayGen, lastGen)
  const viewGen = live ? Math.max(state.currentGen, lastGen) : popGen
  const gen = genAt(state, popGen)
  const fp = failurePatterns(state, live ? Infinity : popGen)
  const shownGens = state.gens.filter((g) => g.gen <= popGen)
  const status = deriveStatus(state, connected)
  const active = ACTIVE.includes(status)
  // A coding agent drives workspace runs; the control channel has no reader.
  const agentRun = state.meta?.provider === 'harness'
  const canControl = active && status !== 'stopping' && !agentRun

  useEffect(() => {
    if (!playing) return
    if (replayGen >= lastGen) { setPlaying(false); return }
    const t = setTimeout(() => setReplayGen((g) => g + 1), 900)
    return () => clearTimeout(t)
  }, [playing, replayGen, lastGen])

  useEffect(() => {
    if (!active) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [active])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      if (steerOpen) setSteerOpen(false)
      else setSelected(null)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [steerOpen])

  const startMs = state.firstTs ? Date.parse(state.firstTs) : NaN
  const endMs = active ? now : state.lastTs ? Date.parse(state.lastTs) : NaN

  const pick = (g: number) => { setMode('replay'); setPlaying(false); setReplayGen(g) }
  const toReplay = () => { setMode('replay'); setPlaying(false); setReplayGen(Math.max(1, lastGen)) }
  const play = () => {
    if (replayGen >= lastGen) setReplayGen(1)
    setPlaying(true)
  }

  const kpis = [
    { label: 'best fitness', value: f3(gen?.bestFitness), series: shownGens.map((g) => g.bestFitness) },
    { label: 'best work ratio', value: f3(gen?.bestWorkRatio), series: shownGens.map((g) => g.bestWorkRatio) },
    { label: 'pass rate', value: gen ? pct(gen.passRate) : '-', series: shownGens.map((g) => g.passRate) },
    { label: 'model calls', value: String(gen?.modelCalls ?? state.modelCalls), series: shownGens.map((g) => g.modelCalls) },
  ]

  return (
    <>
      <nav className="top">
        <div className="bar">
          <a className="word" href="#/">evoalgo</a>
          <span className="runid mono">{runId}</span>
          <div className="seg" role="group" aria-label="View">
            <button aria-pressed={live} onClick={() => { setMode('live'); setPlaying(false) }}>Live</button>
            <button aria-pressed={!live} onClick={toReplay} disabled={!lastGen}>Replay</button>
          </div>
          <span className="sp" />
          <span className={`status ${status}`}>
            <i className="dot" /><span key={status} className="swap">{LABEL[status]}</span>
          </span>
          <span className="meta num">gen {viewGen}/{maxGen || '-'}</span>
          <span className="meta num hide-s">{duration(endMs - startMs)}</span>
          <div className="ctl">
            {agentRun ? (
              <span className="meta">{state.meta?.model ? `${state.meta.model} session` : 'agent session'}</span>
            ) : <>
            {status === 'paused' || status === 'resuming' ? (
              <button className="btn" disabled={status === 'resuming'} onClick={() => send({ cmd: 'resume' })}>
                {status === 'resuming' ? <><span className="spinner xs" />Resuming</> : 'Resume'}
              </button>
            ) : (
              <button className="btn" disabled={status !== 'running'} onClick={() => send({ cmd: 'pause' })}>
                {status === 'pausing' ? <><span className="spinner xs" />Pausing</> : 'Pause'}
              </button>
            )}
            <button className="btn" disabled={!canControl} onClick={() => send({ cmd: 'stop' })}>
              {status === 'stopping' ? <><span className="spinner xs" />Stopping</> : 'Stop'}
            </button>
            {active
              ? <button className="btn primary" disabled={!canControl} aria-expanded={steerOpen}
                        onClick={() => setSteerOpen((o) => !o)}>Steer</button>
              : <a className="btn primary" href={`#/new?from=${encodeURIComponent(runId)}`}>Run again</a>}
            </>}
          </div>
        </div>
      </nav>
      {refused ? (
        <div className="activity fail" role="alert">
          <i className="dot" />
          <span className="what">{refused === 'token'
            ? <>Access refused: open the link printed by <code className="mono">evoalgo ui</code> (a restarted server prints a new one).</>
            : <>This run no longer exists. <a href="#/">Back to runs</a></>}</span>
        </div>
      ) : live && <Activity state={state} status={status} runId={runId} now={now} />}
      <Steer open={steerOpen} onClose={() => setSteerOpen(false)} activeHint={state.activeHint} send={send} />

      <main className="wrap">
        {state.meta && (
          <div className="run-head">
            <p className="caption">
              {state.meta.pack ?? state.meta.problem} · {state.meta.model ?? state.meta.provider ?? 'default model'}
              {state.activeHint && <> · <span className="hint-tag">hint</span> {state.activeHint}</>}
              {state.stopReason && <> · {state.stopReason.replaceAll('_', ' ')}</>}
            </p>
            {state.meta.research_goal && <p className="goal-line"><span>Goal</span>{state.meta.research_goal}</p>}
          </div>
        )}

        <section className="panel kpis" style={stagger(0)}>
          {kpis.map((k) => (
            <div className="kpi" key={k.label}>
              <div key={k.value} className="v num tick">{k.value}</div>
              <div className="l">{k.label}</div>
              <Spark values={k.series} />
            </div>
          ))}
        </section>

        <div className="main">
          <div className="stack">
            <section className="panel" style={stagger(1)}>
              <div className="ph">
                <h3>Work ratio</h3>
                <span className="legend"><span><i className="best" />best</span><span><i className="mean" />mean</span></span>
              </div>
              <WorkRatioChart gens={shownGens} maxGen={maxGen} viewGen={popGen} onPick={pick} />
            </section>
            <section className="panel" style={stagger(2)}>
              <div className="ph"><h3>Lineage</h3><span className="meta">{state.order.length} candidates</span></div>
              <Lineage state={state} viewGen={viewGen} bestGen={popGen} selected={selected} onSelect={setSelected} />
            </section>
          </div>
          <section className="panel events" style={stagger(3)}>
            <EventLog entries={state.log} filter={filter} setFilter={setFilter}
                      maxGen={live ? Infinity : popGen} onPick={setSelected} />
          </section>
        </div>

        <section className="panel" style={stagger(4)}>
          <div className="ph"><h3>Population</h3><span className="meta num">{gen ? `gen ${gen.gen}` : ''}</span></div>
          <Population gen={gen} cands={state.cands} selected={selected} onSelect={setSelected} />
        </section>

        <section className="panel" style={stagger(5)}>
          <div className="ph"><h3>Failure patterns</h3><span className="meta num">{fp.failed} failed</span></div>
          <Failures fp={fp} onSelect={setSelected} />
        </section>

        {state.agents.length > 0 && (
          <section className="panel" style={stagger(6)}>
            <div className="ph"><h3>Specialist agents</h3><span className="meta">spawned on a plateau</span></div>
            <Agents agents={state.agents} viewGen={live ? Infinity : popGen} />
          </section>
        )}
      </main>

      {!live && lastGen > 0 && (
        <div className="scrubber" role="group" aria-label="Replay">
          <button className="btn round" onClick={playing ? () => setPlaying(false) : play}
                  aria-label={playing ? 'Pause replay' : 'Play replay'}>{playing ? '❚❚' : '▶'}</button>
          <input type="range" min={1} max={lastGen} value={popGen}
                 onChange={(e) => { setPlaying(false); setReplayGen(Number(e.target.value)) }} aria-label="Generation" />
          <span className="num mono">g{popGen}</span>
        </div>
      )}

      <Drawer runId={runId} id={selected} cands={state.cands} onClose={() => setSelected(null)} />
      <Toast notice={notice} />
    </>
  )
}
