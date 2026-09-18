# Thesis role agents (enlcode)

The evolutionary code-repair system for dynamic graph algorithms is realized
as three enlcode role agents plus one shared skill, matching the multi-role
design committed in the SRS (FR-AGENT-02 generation, FR-AGENT-03 repair,
FR-AGENT-04 reflection; FR-AGENT-06 plateau specialization is an experiment
and uses the generator with a specialized prompt).

Reference material: the original single-agent prompt and steering live in
`.kiro/` (Kiro format, kept as the research reference). The enlcode agents
below are the working implementation.

## Files

- `agents/algorithm-generator.json` - generation role (FR-AGENT-02)
- `agents/algorithm-repairer.json` - repair role (FR-AGENT-03)
- `agents/algorithm-reflector.json` - reflection role (FR-AGENT-04)
- `skills/dynamic-graph-algorithms/SKILL.md` - shared domain knowledge
  (candidate interface, evaluator contract, invariants per problem, Yang et
  al. DFS insight, data-structure toolbox, nauty pipeline, conventions)

## Install

enlcode discovers agents only from `~/.enlcode/agents/` and skills from
`~/.enlcode/skills/` (project-local `.enlcode/` and `.kiro/` are NOT loaded;
verified 2026-09-18). Install or sync with:

```bash
./scripts/install-agents.sh            # repo -> global (fresh setup)
./scripts/install-agents.sh --from-global  # global -> repo (persist edits)
```

After installing, restart enlcode for changes to take effect.

## Invocation from the Python orchestrator

The orchestrator runs each role headless with `enlcode run`. The role message
carries the problem definition and the relevant context; the agent prompt
defines the protocol and the report format the orchestrator parses.

```bash
# Generation (FR-AGENT-02): problem + optional parent candidate
enlcode run "<problem+parent context, tell it the filename>" \
  --agent algorithm-generator --format json

# Reflection (FR-AGENT-04): failed candidate + failing case
enlcode run "<failed candidate path + failing case, tell it the reflection filename>" \
  --agent algorithm-reflector --format json

# Repair (FR-AGENT-03): failed candidate + its reflection
enlcode run "<failed candidate path + reflection path, tell it the new filename>" \
  --agent algorithm-repairer --format json
```

- Model: omit `-m` to use the default, or pin per run:
  `-m ericai/deepseek-ai/DeepSeek-V4-Flash-0731` (or any configured ericai
  model). The SRS (FR-AGENT-01) requires provider abstraction: no agent file
  hardcodes a model; the orchestrator decides per run.
- Automation: add `--dangerously-skip-permissions` for unattended runs. The
  real security boundary is the OS-level sandbox described in the design doc
  (candidate code never runs with agent privileges); the enlcode permission
  prompts are convenience, not the isolation mechanism.
- Output: `--format json` emits machine-parseable events; the final `text`
  part carries the agent's report (CANDIDATE/VERDICT/WORK_RATIO for the
  generator, REPAIRED/VERDICT for the repairer, REFLECTION/ROOT_CAUSE for the
  reflector).

## Editing workflow

Edit the files; run `./scripts/install-agents.sh --from-global` before
committing so the repo copy matches what enlcode loads. Then commit.