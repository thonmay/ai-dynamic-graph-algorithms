// Event and API shapes. Mirrors src/evoalgo/events.py and server.py.

export interface FailingCase {
  problem?: string
  result?: string
  expected?: string
  operation?: string
  graph_n?: number
  graph_shape?: number[]
  sequence_idx?: number
  [key: string]: unknown
}

export interface PopEntry {
  id: string
  parent_ids: string[]
  state: string | null
  fitness: number | null
  work_ratio: number | null
}

interface Base {
  seq: number
  ts: string
}

export type RunStartEvent = Base & {
  type: 'run_start'
  run_id?: string
  problem?: string | null
  pack?: string | null
  research_goal?: string | null
  provider?: string | null
  model?: string | null
  population_size?: number | null
  max_generations?: number | null
  model_call_budget?: number | null
  resumed?: boolean
  generation?: number
  backfilled?: boolean
}

export type RunEvent =
  | RunStartEvent
  | (Base & { type: 'gen_start'; gen: number })
  | (Base & { type: 'candidate_generated'; id: string; gen: number; parent_ids?: string[]; role?: string })
  | (Base & {
      type: 'candidate_verified'
      id: string
      gen: number
      state?: string | null
      fitness?: number | null
      work_ratio?: number | null
      timeout?: boolean
      tests_passed?: number | null
      tests_total?: number | null
      failing_case?: FailingCase | null
      error?: string | null
    })
  | (Base & { type: 'candidate_reflected'; id: string; gen: number; reflection_path?: string | null })
  | (Base & { type: 'candidates_discarded'; gen: number; ids: string[] })
  | (Base & { type: 'agent_failed'; gen: number; id: string; role?: string })
  | (Base & { type: 'agent_call_start'; gen: number; role: string; id: string; agent?: string | null; model?: string | null })
  | (Base & { type: 'agent_call_end'; gen: number; role: string; id: string; ok: boolean; duration_s: number })
  | (Base & { type: 'paused'; gen: number; before: { role: string; id: string } | null })
  | (Base & { type: 'resumed'; gen: number })
  | (Base & {
      type: 'gen_committed'
      gen: number
      population: PopEntry[]
      best_id: string | null
      best_fitness: number | null
      best_work_ratio: number | null
      model_calls: number | null
      stop_reason: string | null
    })
  | (Base & { type: 'control_ack'; cmd_id: string; gen: number; cmd: string; text?: string; field?: string; value?: number })
  | (Base & { type: 'control_reject'; cmd_id: string; gen: number; cmd?: string; reason: string })
  | (Base & {
      type: 'run_end'
      stop_reason: string | null
      generation: number
      best_candidate_id: string | null
      best_fitness: number | null
      best_work_ratio: number | null
      model_calls: number | null
    })

export type Command =
  | { cmd: 'pause' }
  | { cmd: 'resume' }
  | { cmd: 'stop' }
  | { cmd: 'hint'; text: string }
  | { cmd: 'set'; field: 'model_call_budget' | 'population_size'; value: number }

/** A control command the engine has not acknowledged yet. */
export interface PendingCmd {
  id: string
  cmd: string
  text?: string
  field?: string
  value?: number
}

export type EngineState = 'alive' | 'gone' | 'none'

export interface RunSummary {
  run_id: string
  has_events: boolean
  engine?: EngineState
  state: 'no_events' | 'empty' | 'running' | 'paused' | 'done' | 'interrupted'
  problem?: string | null
  model?: string | null
  pack?: string | null
  research_goal?: string | null
  max_generations?: number | null
  generation?: number
  best_id?: string | null
  best_fitness?: number | null
  best_work_ratio?: number | null
  model_calls?: number | null
  started?: string | null
  updated?: string | null
  events?: number
  history?: (number | null)[]
}

export interface CandidateFile {
  id: string
  code: string
  reflection: string | null
}

export interface LaunchBody {
  pack?: string
  config?: string
  research_goal?: string
  run_id?: string
  max_generations?: number
  population_size?: number
  model_call_budget?: number
  model?: string
  provider?: 'api' | 'enlcode'
  endpoint?: EndpointId
  n_max?: number
  early_stop_on_success?: boolean
}

export type EndpointId = 'ericai' | 'openrouter' | 'openai'

export interface AgentOptions {
  endpoints: { id: EndpointId; label: string; key_env: string; key_set: boolean; model: string | null }[]
  harness: { id: 'enlcode'; available: boolean }
}

export interface PackInfo {
  name: string
  title: string
  tier: 'calibration' | 'core' | 'open'
  directed: boolean
  needs_root: boolean
  checker: string
  update_mode: string
  lean: boolean
  question: string | null
  brief: string
}
