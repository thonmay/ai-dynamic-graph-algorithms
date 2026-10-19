import { describe, expect, it } from 'vitest'
import { reviewIssues } from './components/NewRunPage'

const pack = { name: 'dynamic_bfs', title: 't', tier: 'calibration', directed: true, needs_root: true,
  checker: 'dynamic_bfs', update_mode: 'mixed', lean: false, question: 'q', brief: 'b' } as const

const form = { pack: 'dynamic_bfs', goal: '', preset: 'standard', gens: 10, pop: 4, budget: 200,
  model: 'Qwen/Qwen3.8-27B-FP8', agent: 'ericai' as const, nMax: 5, stopAtFirst: false, runId: '' }

const agents = {
  endpoints: [
    { id: 'ericai' as const, label: 'EricAI', key_env: 'ERICAI_ACCESS_TOKEN', key_set: true, model: 'Qwen/Qwen3.8-27B-FP8' },
    { id: 'openrouter' as const, label: 'OpenRouter', key_env: 'OPENROUTER_API_KEY', key_set: false, model: null },
  ],
  harness: { id: 'enlcode' as const, available: false },
}

describe('reviewIssues', () => {
  it('a default form can launch, with only a soft note for the empty goal', () => {
    const r = reviewIssues(form, pack)
    expect(r.blocking).toEqual([])
    expect(r.notes).toEqual(['No goal set'])
  })

  it('blocks out-of-range numbers, bad run ids and a missing pack', () => {
    const r = reviewIssues({ ...form, gens: 0, pop: 51, budget: 0, nMax: 9, runId: '../x' }, pack)
    expect(r.blocking).toEqual([
      'Generations must be 1 to 1000', 'Population must be 1 to 50', 'Call budget must be 1 to 100000',
      'Verifier n max must be 2 to 8', 'Run id: letters, digits, . _ - only',
    ])
    expect(reviewIssues(form, undefined).blocking).toEqual(['Choose a problem'])
  })

  it('warns when the call budget cannot cover the planned calls', () => {
    expect(reviewIssues({ ...form, gens: 10, pop: 4, budget: 12, goal: 'g' }, pack).notes)
      .toEqual(['Call budget may stop the run early'])
  })

  it('an API endpoint needs a model and a key; the harness needs its binary', () => {
    expect(reviewIssues(form, pack, agents).blocking).toEqual([])
    expect(reviewIssues({ ...form, model: ' ' }, pack, agents).blocking)
      .toEqual(['Choose a model for the API endpoint'])
    expect(reviewIssues({ ...form, agent: 'openrouter' }, pack, agents).blocking)
      .toEqual(['Key not set: export OPENROUTER_API_KEY before starting evoalgo ui'])
    expect(reviewIssues({ ...form, agent: 'enlcode', model: '' }, pack, agents).blocking)
      .toEqual(['enlcode not found on this machine'])
  })
})
