// Pure reducer: events.jsonl records -> UI state. Live view and replay both
// run through applyEvents, so they cannot disagree.

import type { EngineState, FailingCase, PendingCmd, PopEntry, RunEvent, RunStartEvent } from './types'

export interface Cand {
  id: string
  gen: number
  parents: string[]
  role: string
  state: string | null
  fitness: number | null
  workRatio: number | null
  testsPassed: number | null
  testsTotal: number | null
  timeout: boolean
  failingCase: FailingCase | null
  error: string | null
  reflected: boolean
  discarded: boolean
  /** Specialist agent that wrote it (dynamic agent generation). */
  agent?: string
}

/** A specialist spawned on a plateau (dynamic agent generation). */
export interface AgentInfo {
  name: string
  kind: string
  signature: string
  spawnedGen: number
  retiredGen: number | null
  retireReason: string | null
}

export interface GenInfo {
  gen: number
  ts: string
  population: PopEntry[]
  bestId: string | null
  bestFitness: number | null
  bestWorkRatio: number | null
  meanWorkRatio: number | null
  passRate: number
  modelCalls: number | null
}

export type LogKind = 'run' | 'agent' | 'verify' | 'control'
export type Tone = 'plain' | 'muted' | 'pass' | 'fail' | 'accent'

export interface LogEntry {
  seq: number
  ts: string
  gen: number
  kind: LogKind
  tone: Tone
  text: string
  candidate?: string
}

export type Status = 'connecting' | 'running' | 'paused' | 'done' | 'stopped'

export interface RunState {
  lastSeq: number
  meta: RunStartEvent | null
  status: Status
  currentGen: number
  cands: Record<string, Cand>
  order: string[]
  gens: GenInfo[]
  log: LogEntry[]
  activeHint: string | null
  genHints: Record<number, string>
  modelCalls: number
  stopReason: string | null
  firstTs: string | null
  lastTs: string | null
  /** Commands sent but not yet acknowledged, by command id. */
  pending: Record<string, PendingCmd>
  /** Command ids already acknowledged or rejected. */
  handled: Record<string, true>
  /** The agent call in progress, if any. */
  call: { gen: number; role: string; id: string; ts: string } | null
  pausedBefore: { role: string; id: string } | null
  /** Engine process liveness from the server; null until known. */
  engine: EngineState | null
  /** Specialists in spawn order. */
  agents: AgentInfo[]
}

export const LOG_LIMIT = 1000

export function initialState(): RunState {
  return {
    lastSeq: -1, meta: null, status: 'connecting', currentGen: 0, cands: {}, order: [],
    gens: [], log: [], activeHint: null, genHints: {}, modelCalls: 0, stopReason: null,
    firstTs: null, lastTs: null, pending: {}, handled: {}, call: null, pausedBefore: null,
    engine: null, agents: [],
  }
}

/** Everything the websocket delivers, as reducer actions. */
export type Msg =
  | { kind: 'events'; events: RunEvent[] }
  | { kind: 'pending'; commands: PendingCmd[] }
  | { kind: 'queued'; cmd: PendingCmd }
  | { kind: 'engine'; state: EngineState }

export function reduce(s: RunState, m: Msg): RunState {
  switch (m.kind) {
    case 'events':
      return applyEvents(s, m.events)
    case 'pending': // authoritative snapshot, sent on every (re)connect
      return { ...s, pending: Object.fromEntries(
        m.commands.filter((c) => c.id && !s.handled[c.id]).map((c) => [c.id, c])) }
    case 'queued':
      return s.handled[m.cmd.id] ? s : { ...s, pending: { ...s.pending, [m.cmd.id]: m.cmd } }
    case 'engine':
      return { ...s, engine: m.state }
  }
}

export type Live =
  | 'starting' | 'empty' | 'running' | 'pausing' | 'paused' | 'resuming' | 'stopping'
  | 'stopped' | 'done' | 'interrupted' | 'offline'

/** What the user should see right now, combining events, pending commands and liveness. */
export function deriveStatus(s: RunState, connected: boolean): Live {
  if (s.status === 'done' || s.status === 'stopped') return s.status
  if (!connected) return s.lastSeq < 0 ? 'starting' : 'offline'
  if (s.lastSeq < 0) return s.engine === 'none' || s.engine === 'gone' ? 'empty' : 'starting'
  if (s.engine === 'none' || s.engine === 'gone') return 'interrupted'
  const cmds = Object.values(s.pending).map((c) => c.cmd)
  if (cmds.includes('stop')) return 'stopping'
  if (s.status === 'paused') return cmds.includes('resume') ? 'resuming' : 'paused'
  return cmds.includes('pause') ? 'pausing' : 'running'
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const f3 = (v: number | null | undefined) => (isNum(v) ? v.toFixed(3) : '-')

export function describeCommand(c: { cmd?: string; text?: string; field?: string; value?: number }): string {
  if (c.cmd === 'hint') return c.text?.trim() ? `hint "${c.text.trim()}"` : 'hint cleared'
  if (c.cmd === 'set') return `${c.field} = ${c.value}`
  return c.cmd ?? 'command'
}

function newCand(id: string, gen: number, parents: string[] = [], role = 'mutate'): Cand {
  return {
    id, gen, parents, role, state: null, fitness: null, workRatio: null, testsPassed: null,
    testsTotal: null, timeout: false, failingCase: null, error: null, reflected: false, discarded: false,
  }
}

export function applyEvents(prev: RunState, events: RunEvent[]): RunState {
  const s: RunState = {
    ...prev, cands: { ...prev.cands }, order: [...prev.order], gens: [...prev.gens],
    log: [...prev.log], genHints: { ...prev.genHints }, pending: { ...prev.pending },
    handled: { ...prev.handled },
  }
  const settle = (cmdId: string) => {
    delete s.pending[cmdId]
    s.handled[cmdId] = true
  }
  const upsert = (c: Cand) => {
    if (!(c.id in s.cands)) s.order.push(c.id)
    s.cands[c.id] = c
  }

  for (const e of events) {
    if (e.seq <= s.lastSeq) continue
    s.lastSeq = e.seq
    s.firstTs ??= e.ts
    s.lastTs = e.ts
    const gen = 'gen' in e && isNum(e.gen) ? e.gen : s.currentGen
    const log = (kind: LogKind, tone: Tone, text: string, candidate?: string) =>
      s.log.push({ seq: e.seq, ts: e.ts, gen, kind, tone, text, candidate })

    switch (e.type) {
      case 'run_start':
        s.meta = s.meta ?? e
        s.status = 'running'
        log('run', 'plain', e.resumed ? `resumed at gen ${e.generation ?? 0}` : `start · ${e.problem ?? ''}`)
        break
      case 'gen_start':
        s.currentGen = e.gen
        if (s.activeHint) s.genHints[e.gen] = s.activeHint
        log('run', 'muted', `gen ${e.gen}`)
        break
      case 'candidate_generated': {
        const parents = e.parent_ids ?? []
        const role = e.role ?? 'mutate'
        upsert({ ...(s.cands[e.id] ?? newCand(e.id, e.gen)), parents, role, gen: e.gen,
                 ...(e.agent ? { agent: e.agent } : {}) })
        const who = e.agent ? `${e.agent} ` : ''
        log('agent', 'plain', `${who}${role} ${e.id}${parents.length ? ` ← ${parents.join(', ')}` : ''}`, e.id)
        break
      }
      case 'plateau_detected':
        log('run', 'accent', `plateau over ${e.window} gens (${e.kind})`, e.best_id ?? undefined)
        break
      case 'agent_spawned':
        s.agents = [...s.agents, { name: e.agent, kind: e.kind, signature: e.signature,
                                   spawnedGen: e.gen, retiredGen: null, retireReason: null }]
        log('agent', 'accent', `spawned ${e.agent} · ${e.kind}`)
        break
      case 'agent_retired':
        s.agents = s.agents.map((a) => a.name === e.agent ? { ...a, retiredGen: e.gen, retireReason: e.reason } : a)
        log('agent', 'muted', `retired ${e.agent} · ${e.reason.replace('_', ' ')} · ${e.candidates} candidates${e.gained ? ', improved best' : ''}`)
        break
      case 'candidate_verified': {
        const c = s.cands[e.id] ?? newCand(e.id, e.gen)
        upsert({
          ...c, state: e.state ?? null, fitness: e.fitness ?? null, workRatio: e.work_ratio ?? null,
          testsPassed: e.tests_passed ?? null, testsTotal: e.tests_total ?? null,
          timeout: !!e.timeout, failingCase: e.failing_case ?? null, error: e.error ?? null,
        })
        const tests = isNum(e.tests_total) ? ` · ${e.tests_passed ?? 0}/${e.tests_total}` : ''
        const wr = isNum(e.work_ratio) ? ` wr ${f3(e.work_ratio)}` : ''
        log('verify', e.state === 'PASS' ? 'pass' : 'fail', `${e.state ?? '?'} ${e.id}${wr}${tests}`, e.id)
        break
      }
      case 'candidate_reflected':
        if (s.cands[e.id]) upsert({ ...s.cands[e.id], reflected: true })
        log('agent', 'plain', `reflect ${e.id}`, e.id)
        break
      case 'candidates_discarded':
        for (const id of e.ids) if (s.cands[id]) upsert({ ...s.cands[id], discarded: true })
        log('run', 'muted', `cull ${e.ids.join(', ')}`)
        break
      case 'agent_failed':
        log('agent', 'fail', `${e.role ?? 'agent'} ${e.id}: no candidate written`)
        break
      case 'agent_call_start':
        s.call = { gen: e.gen, role: e.role, id: e.id, ts: e.ts }
        break
      case 'agent_call_end':
        if (s.call?.id === e.id && s.call.role === e.role) s.call = null
        log('agent', e.ok ? 'muted' : 'fail', `${e.role} ${e.id}${isNum(e.duration_s) ? ` · ${e.duration_s.toFixed(1)} s` : ''}`, e.id)
        break
      case 'paused':
        s.status = 'paused'
        s.pausedBefore = e.before
        log('control', 'accent', e.before ? `paused before ${e.before.role} ${e.before.id}` : 'paused')
        break
      case 'resumed':
        s.status = 'running'
        s.pausedBefore = null
        log('control', 'accent', 'resumed')
        break
      case 'gen_committed': {
        const wrs = e.population.map((p) => p.work_ratio).filter(isNum)
        const info: GenInfo = {
          gen: e.gen, ts: e.ts, population: e.population, bestId: e.best_id,
          bestFitness: e.best_fitness, bestWorkRatio: e.best_work_ratio,
          meanWorkRatio: wrs.length ? wrs.reduce((a, b) => a + b, 0) / wrs.length : null,
          passRate: e.population.length
            ? e.population.filter((p) => p.state === 'PASS').length / e.population.length : 0,
          modelCalls: e.model_calls,
        }
        const i = s.gens.findIndex((g) => g.gen === e.gen)
        if (i >= 0) s.gens[i] = info
        else s.gens.push(info)
        s.gens.sort((a, b) => a.gen - b.gen)
        for (const p of e.population) {
          if (!s.cands[p.id]) {
            upsert({ ...newCand(p.id, e.gen, p.parent_ids), state: p.state, fitness: p.fitness, workRatio: p.work_ratio })
          }
        }
        if (isNum(e.model_calls)) s.modelCalls = e.model_calls
        log('run', 'accent', `commit gen ${e.gen} · best ${e.best_id ?? '-'} wr ${f3(e.best_work_ratio)}`, e.best_id ?? undefined)
        break
      }
      case 'control_ack':
        // Paused/running state follows the engine's paused/resumed events,
        // not the acknowledgement, so "pausing" lasts until the engine waits.
        settle(e.cmd_id)
        if (e.cmd === 'hint') s.activeHint = (e.text ?? '').trim() || null
        log('control', 'accent', `${describeCommand(e)} · applied`)
        break
      case 'control_reject':
        settle(e.cmd_id)
        log('control', 'fail', `${e.cmd ?? 'command'} rejected: ${e.reason}`)
        break
      case 'run_end':
        s.call = null
        s.pausedBefore = null
        s.stopReason = e.stop_reason
        s.status = e.stop_reason === 'user_stop' ? 'stopped' : 'done'
        if (isNum(e.model_calls)) s.modelCalls = e.model_calls
        log('run', 'accent', `end · ${e.stop_reason ?? 'unknown'}`)
        break
    }
  }
  if (s.log.length > LOG_LIMIT) s.log = s.log.slice(-LOG_LIMIT)
  return s
}

export function genAt(s: RunState, gen: number): GenInfo | undefined {
  return s.gens.find((g) => g.gen === gen)
}

/** Best candidate of `gen` and its first-parent ancestors, newest first. */
export function bestPath(s: RunState, gen: number): string[] {
  const path: string[] = []
  const seen = new Set<string>()
  let id = genAt(s, gen)?.bestId ?? null
  while (id && !seen.has(id)) {
    seen.add(id)
    path.push(id)
    id = s.cands[id]?.parents[0] ?? null
  }
  return path
}

/** Same order as population._rank_key: passing, higher fitness, lower work ratio. */
export function rank(a: PopEntry, b: PopEntry): number {
  const k = (p: PopEntry) => [p.state === 'PASS' ? 0 : 1, -(p.fitness ?? 0), p.work_ratio ?? Infinity]
  const [x, y] = [k(a), k(b)]
  for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] < y[i] ? -1 : 1
  return 0
}
