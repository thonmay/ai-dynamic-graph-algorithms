// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { describe, expect, it } from 'vitest'
import { applyEvents, bestPath, failKind, failurePatterns, genAt, initialState } from './state'
import type { RunEvent } from './types'

function stream(): RunEvent[] {
  let seq = 0
  const ev = (e: Record<string, unknown>) =>
    ({ seq: seq, ts: `2026-01-01T00:00:${String(seq++).padStart(2, '0')}Z`, ...e }) as RunEvent
  const pop1 = [
    { id: 'gen001_c01', parent_ids: [], state: 'PASS', fitness: 1, work_ratio: 0.5 },
    { id: 'gen001_c02', parent_ids: [], state: 'FAIL', fitness: 0.5, work_ratio: null },
  ]
  return [
    ev({ type: 'run_start', run_id: 'r', problem: 'dynamic_bfs', max_generations: 2, model_call_budget: 9 }),
    ev({ type: 'gen_start', gen: 1 }),
    ev({ type: 'candidate_generated', id: 'gen001_c01', gen: 1, parent_ids: [], role: 'seed' }),
    ev({ type: 'candidate_verified', id: 'gen001_c01', gen: 1, state: 'PASS', fitness: 1, work_ratio: 0.5 }),
    ev({ type: 'candidate_generated', id: 'gen001_c02', gen: 1, parent_ids: [], role: 'seed' }),
    ev({ type: 'candidate_verified', id: 'gen001_c02', gen: 1, state: 'FAIL', fitness: 0.5,
         failing_case: { expected: '[0]', result: '[1]' } }),
    ev({ type: 'gen_committed', gen: 1, population: pop1, best_id: 'gen001_c01', best_fitness: 1,
         best_work_ratio: 0.5, model_calls: 2, stop_reason: null }),
    ev({ type: 'control_ack', cmd_id: 'a', gen: 1, cmd: 'hint', text: ' go lazy ' }),
    ev({ type: 'control_ack', cmd_id: 'b', gen: 1, cmd: 'pause' }),
    ev({ type: 'paused', gen: 2, before: null }),
    ev({ type: 'control_reject', cmd_id: 'c', gen: 1, cmd: 'set', reason: 'too small' }),
    ev({ type: 'control_ack', cmd_id: 'd', gen: 1, cmd: 'resume' }),
    ev({ type: 'resumed', gen: 2 }),
    ev({ type: 'gen_start', gen: 2 }),
    ev({ type: 'candidate_generated', id: 'gen002_c01', gen: 2, parent_ids: ['gen001_c01'], role: 'mutate' }),
    ev({ type: 'candidate_verified', id: 'gen002_c01', gen: 2, state: 'PASS', fitness: 1, work_ratio: 0.2 }),
    ev({ type: 'candidates_discarded', gen: 2, ids: ['gen001_c02'] }),
    ev({ type: 'gen_committed', gen: 2,
         population: [{ id: 'gen002_c01', parent_ids: ['gen001_c01'], state: 'PASS', fitness: 1, work_ratio: 0.2 }, pop1[0]],
         best_id: 'gen002_c01', best_fitness: 1, best_work_ratio: 0.2, model_calls: 3, stop_reason: 'max_generations' }),
    ev({ type: 'run_end', stop_reason: 'max_generations', generation: 2, best_candidate_id: 'gen002_c01',
         best_fitness: 1, best_work_ratio: 0.2, model_calls: 3 }),
  ]
}

describe('applyEvents', () => {
  it('builds generations, candidates and status', () => {
    const s = applyEvents(initialState(), stream())
    expect(s.status).toBe('done')
    expect(s.gens.map((g) => g.gen)).toEqual([1, 2])
    expect(genAt(s, 1)?.meanWorkRatio).toBe(0.5)
    expect(genAt(s, 1)?.passRate).toBe(0.5)
    expect(s.cands['gen001_c02'].failingCase?.expected).toBe('[0]')
    expect(s.cands['gen001_c02'].discarded).toBe(true)
    expect(s.modelCalls).toBe(3)
    expect(s.order).toEqual(['gen001_c01', 'gen001_c02', 'gen002_c01'])
  })

  it('tracks pause/resume and maps hints to later generations', () => {
    const events = stream()
    const paused = applyEvents(initialState(), events.slice(0, 10))
    expect(paused.status).toBe('paused')
    const s = applyEvents(initialState(), events)
    expect(s.genHints).toEqual({ 2: 'go lazy' })
    expect(s.log.find((l) => l.kind === 'control' && l.tone === 'fail')?.text).toContain('too small')
  })

  it('ignores duplicate events and is batch independent', () => {
    const events = stream()
    const once = applyEvents(initialState(), events)
    const twice = applyEvents(once, events)
    expect(twice.log.length).toBe(once.log.length)
    const split = applyEvents(applyEvents(initialState(), events.slice(0, 7)), events.slice(7))
    expect(split.log).toEqual(once.log)
    expect(split.gens).toEqual(once.gens)
  })

  it('follows the best lineage and reports user stops', () => {
    const s = applyEvents(initialState(), stream())
    expect(bestPath(s, 2)).toEqual(['gen002_c01', 'gen001_c01'])
    const stop = applyEvents(s, [{ seq: 99, ts: 'x', type: 'run_end', stop_reason: 'user_stop', generation: 2,
      best_candidate_id: null, best_fitness: null, best_work_ratio: null, model_calls: null }])
    expect(stop.status).toBe('stopped')
  })
})

describe('dynamic agent generation', () => {
  it('tracks spawned and retired specialists and labels their candidates', () => {
    let seq = 100
    const ev = (e: Record<string, unknown>) => ({ seq: seq++, ts: '2026-01-01T00:01:00Z', ...e }) as RunEvent
    const s = applyEvents(initialState(), [
      ...stream().slice(0, -1),
      ev({ type: 'plateau_detected', gen: 2, window: 2, kind: 'efficiency', signature: 'wr 0.2', best_id: 'gen002_c01' }),
      ev({ type: 'agent_spawned', gen: 2, agent: 'specialist-1', kind: 'efficiency', signature: 'wr 0.2', focus: 'f', generations: 3 }),
      ev({ type: 'candidate_generated', id: 'gen003_c02', gen: 3, parent_ids: ['gen002_c01'], role: 'specialist', agent: 'specialist-1' }),
      ev({ type: 'agent_retired', gen: 3, agent: 'specialist-1', reason: 'no_gain', candidates: 1, gained: false }),
    ])
    expect(s.agents).toEqual([{ name: 'specialist-1', kind: 'efficiency', signature: 'wr 0.2',
                                spawnedGen: 2, retiredGen: 3, retireReason: 'no_gain' }])
    expect(s.cands['gen003_c02'].agent).toBe('specialist-1')
    expect(s.log.some((l) => l.text === 'spawned specialist-1 · efficiency')).toBe(true)
  })
})

describe('failure patterns', () => {
  it('counts failures per generation by kind and graph size, up to the viewed generation', () => {
    let seq = 200
    const ev = (e: Record<string, unknown>) => ({ seq: seq++, ts: '2026-01-01T00:02:00Z', ...e }) as RunEvent
    const s = applyEvents(initialState(), [
      ...stream(),
      ev({ type: 'candidate_verified', id: 'gen002_c02', gen: 2, state: 'FAIL', fitness: 0.9,
           failing_case: { operation: 'delete (0, 2)', graph_n: 3 } }),
      ev({ type: 'candidate_verified', id: 'gen002_c03', gen: 2, state: 'FAIL', timeout: true,
           failing_case: { operation: 'timeout' } }),
      ev({ type: 'candidate_verified', id: 'gen002_c04', gen: 2, state: 'CRASH',
           failing_case: { operation: 'crash', graph_n: 2 }, error: 'KeyError: 0' }),
      ev({ type: 'candidate_verified', id: 'gen002_c05', gen: 2, state: 'FAIL',
           failing_case: { operation: 'insert (1, 0)', graph_n: 3 } }),
    ])
    const fp = failurePatterns(s, Infinity)
    expect(fp.byGen.map((g) => [g.gen, g.failed, g.verified])).toEqual([[1, 1, 2], [2, 4, 5]])
    // gen001_c02 has no operation in its failing case: counted as an unexplained failure
    expect(fp.byGen[0].counts).toEqual({ crash: 1 })
    expect(fp.byGen[1].counts).toEqual({ delete: 1, timeout: 1, crash: 1, insert: 1 })
    expect(fp.byGen[1].example.delete).toBe('gen002_c02')
    expect(fp.totals).toEqual({ crash: 2, delete: 1, timeout: 1, insert: 1 })
    expect(fp.bySize).toEqual({ 2: 1, 3: 2 })
    expect(failurePatterns(s, 1).failed).toBe(1)
    expect(failKind(s.cands['gen002_c01'])).toBeNull()
  })
})
