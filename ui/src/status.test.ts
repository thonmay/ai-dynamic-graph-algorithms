// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { describe, expect, it } from 'vitest'
import { deriveStatus, initialState, reduce, type RunState } from './state'
import type { RunEvent } from './types'

let seq = 0
const ev = (e: Record<string, unknown>) => ({ seq: seq++, ts: '2026-01-01T00:00:00Z', ...e }) as RunEvent
const events = (s: RunState, ...list: Record<string, unknown>[]) => reduce(s, { kind: 'events', events: list.map(ev) })

function started(): RunState {
  seq = 0
  let s = reduce(initialState(), { kind: 'engine', state: 'alive' })
  s = events(s, { type: 'run_start', run_id: 'r', max_generations: 3 }, { type: 'gen_start', gen: 1 },
    { type: 'agent_call_start', gen: 1, role: 'seed', id: 'gen001_c01' })
  return s
}

describe('deriveStatus', () => {
  it('pause: queued -> pausing until the engine actually waits -> paused', () => {
    let s = started()
    expect(deriveStatus(s, true)).toBe('running')
    expect(s.call?.id).toBe('gen001_c01')
    s = reduce(s, { kind: 'queued', cmd: { id: 'p1', cmd: 'pause' } })
    expect(deriveStatus(s, true)).toBe('pausing')
    s = events(s, { type: 'agent_call_end', gen: 1, role: 'seed', id: 'gen001_c01', ok: true, duration_s: 61.2 },
      { type: 'control_ack', cmd_id: 'p1', gen: 1, cmd: 'pause' })
    expect(s.call).toBeNull()
    expect(deriveStatus(s, true)).toBe('running') // acknowledged, engine not waiting yet
    s = events(s, { type: 'paused', gen: 1, before: { role: 'seed', id: 'gen001_c02' } })
    expect(deriveStatus(s, true)).toBe('paused')
    expect(s.pausedBefore).toEqual({ role: 'seed', id: 'gen001_c02' })
    s = reduce(s, { kind: 'queued', cmd: { id: 'r1', cmd: 'resume' } })
    expect(deriveStatus(s, true)).toBe('resuming')
    s = events(s, { type: 'control_ack', cmd_id: 'r1', gen: 1, cmd: 'resume' }, { type: 'resumed', gen: 1 })
    expect(deriveStatus(s, true)).toBe('running')
    expect(s.log.some((l) => l.text === 'seed gen001_c01 · 61.2 s')).toBe(true)
  })

  it('stop and reject clear pending; pending snapshot replaces local state', () => {
    let s = reduce(started(), { kind: 'queued', cmd: { id: 's1', cmd: 'stop' } })
    expect(deriveStatus(s, true)).toBe('stopping')
    s = reduce(s, { kind: 'queued', cmd: { id: 'x', cmd: 'set', field: 'population_size', value: 0 } })
    s = events(s, { type: 'control_reject', cmd_id: 'x', gen: 1, cmd: 'set', reason: 'bad' })
    expect(Object.keys(s.pending)).toEqual(['s1'])
    s = reduce(s, { kind: 'pending', commands: [] })
    expect(deriveStatus(s, true)).toBe('running')
    s = events(s, { type: 'run_end', stop_reason: 'user_stop', generation: 1, best_candidate_id: null,
      best_fitness: null, best_work_ratio: null, model_calls: 1 })
    expect(deriveStatus(s, false)).toBe('stopped')
  })

  it('an acknowledged command never comes back as pending after reconnect', () => {
    let s = events(started(), { type: 'control_ack', cmd_id: 'p1', gen: 1, cmd: 'pause' })
    s = reduce(s, { kind: 'pending', commands: [{ id: 'p1', cmd: 'pause' }] })
    s = reduce(s, { kind: 'queued', cmd: { id: 'p1', cmd: 'pause' } })
    expect(s.pending).toEqual({})
  })

  it('interrupted, offline, starting', () => {
    const s = started()
    expect(deriveStatus(reduce(s, { kind: 'engine', state: 'gone' }), true)).toBe('interrupted')
    expect(deriveStatus(reduce(s, { kind: 'engine', state: 'none' }), true)).toBe('interrupted')
    expect(deriveStatus(s, false)).toBe('offline')
    expect(deriveStatus(initialState(), false)).toBe('starting')
    expect(deriveStatus(reduce(initialState(), { kind: 'engine', state: 'none' }), true)).toBe('empty')
  })
})
