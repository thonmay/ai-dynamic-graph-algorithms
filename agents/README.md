# Role agents (opencode)

The three agent roles of the evolutionary loop, plus the researcher agent
used by the harness mode, as opencode agent files (markdown with YAML frontmatter):

- `algorithm-generator.md` - generation role (FR-AGENT-02)
- `algorithm-repairer.md` - repair role (FR-AGENT-03)
- `algorithm-reflector.md` - reflection role (FR-AGENT-04)
- `evoalgo-researcher.md` - one coding agent that runs the whole loop with
  the `evoalgo` skill (harness mode)
- `../skills/dynamic-graph-algorithms/SKILL.md` - shared domain knowledge for
  the role agents (candidate interface, invariants, conventions)

No agent file names a model; the run config chooses it (FR-AGENT-01).

## Install

```bash
./scripts/install-agents.sh                # repo -> ~/.config/opencode
./scripts/install-agents.sh --from-global  # ~/.config/opencode -> repo
```

The orchestrator calls a role with `provider: opencode`, which runs
`opencode run --agent <role> --format json --dir <run> [-m <model>] <task>`
and reads the agent's final report from the JSON event stream.
