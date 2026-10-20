# Start and watch a multi-agent run

evoalgo's own orchestrator runs a population of agent calls (generate,
reflect, repair) over an OpenAI-compatible API. Use this when the user wants
the automated search rather than you doing the loop.

## Start

Ask the user which endpoint and model to use if they have not said. Keys are
read from environment variables (`ERICAI_ACCESS_TOKEN`, `OPENROUTER_API_KEY`,
`OPENAI_API_KEY`); never print or write a key.

Write a config file next to the runs folder, for example `runs/my_bfs.yaml`:

```yaml
pack: dynamic_bfs
problem: dynamic_bfs
research_goal: Reach full correctness first, then avoid a full recompute after insertions.
provider: api
api_base_url: openrouter   # ericai | openrouter | openai
model: qwen/qwen3-coder
population_size: 4
max_generations: 8
elitism_k: 1
model_call_budget: 64
early_stop_on_success: false
agent_max_steps: 16
workdir: runs
```

Then start it in the background from the repo root:

```bash
nohup evoalgo start runs/my_bfs.yaml --run-id my_bfs > runs/my_bfs.log 2>&1 &
```

A run of this size takes 20 to 40 minutes plus up to 12 minutes of final
grading. The web UI also starts and shows runs; it is a server, so start it
in the background (`nohup evoalgo ui --runs runs --port 8765 > runs/ui.log 2>&1 &`)
or leave it to the user. It listens on 127.0.0.1 without authentication.

## Watch and steer

- Progress: `evoalgo status runs/my_bfs --json` (state, generation, best id,
  best work ratio, final grade once done).
- Pause, resume, stop, or send a hint that every later agent call sees:
  `evoalgo control runs/my_bfs pause|resume|stop`,
  `evoalgo control runs/my_bfs hint "try keeping a level structure"`.
- Commands apply before the next agent call, so a pause can take a minute.

Do not poll in a tight loop. Check every few minutes, or tell the user how
to check and stop.
