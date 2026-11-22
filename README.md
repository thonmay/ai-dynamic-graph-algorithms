# AI-Assisted Discovery of Dynamic Graph Algorithms via Evolutionary Code Repair

BSc thesis project at Eotvos Lorand University, Faculty of Informatics.

A research platform combining LLM-driven evolutionary code repair with exhaustive
isomorphism-aware verification to assist algorithm designers in developing correct
and efficient dynamic graph algorithms on directed graphs.

## Thesis

The thesis (LaTeX source and the built PDF) is in [`thesis-doc/`](thesis-doc/).

## Lean Formalization

The dynamic MCS candidate `gen001_c01` is formalized and proved correct in Lean 4 +
mathlib under [`lean/`](lean/). The headline theorem `mcsUpdate_preserves_invariant`
states that the candidate's update preserves a valid MCS ordering under every single
edge flip; `init_valid`, `insert_edge_valid` and `delete_edge_valid` follow.

Verify the proof is honest (builds, no `sorry`, standard axioms only):

```bash
cd lean
lake build ThesisLean.Formal_gen001c01_3939115c   # must end "Build completed successfully"
lake env lean AxiomAudit.lean                      # each theorem: [propext, Classical.choice, Quot.sound]
lake env leanchecker ThesisLean.Formal_gen001c01_3939115c   # kernel replay, exit 0
```

Toolchain: `leanprover/lean4:v4.34.0`, mathlib `v4.34.0` (see `lean/lean-toolchain`).

## Project Overview

The system runs an evolutionary loop in which candidate dynamic graph algorithms
(generated and repaired by cooperative AI agents) are tested exhaustively against
all non-isomorphic digraphs (enumerated via nauty's `geng` + `directg`) and scored
on correctness and efficiency relative to full offline recomputation.

Supported problem tiers:

- Calibration: dynamic BFS, dynamic DFS (known solutions exist)
- Harder: dynamic SCC, reachability
- Open: dynamic Lexicographic BFS (genuine discovery target)

Core principles:

- Correctness by invariant, not by reference equality (dynamic outputs are not unique)
- Verification engine is trusted infrastructure, never exposed to agents
- Sequence-based testing of interleaved edge insertions and deletions
- Exhaustive isomorphism-aware coverage up to n <= 5, random sampling beyond
- LLM-agnostic provider abstraction, CLI-driven, JSON filesystem persistence

## Use with coding agents

The `evoalgo` [Agent Skill](https://agentskills.io) lets Claude Code, Codex or
opencode run the search loop themselves: edit one candidate file, grade it with
the exhaustive verifier, keep or revert. Install the package from a clone
(`pip install -e '.[api,ui]'`), then make the skill available:

- Inside this repo it is picked up automatically (`.agents/skills/`, `.claude/skills/`).
- Elsewhere: `evoalgo skill --install` (copies it to `~/.agents/skills` and `~/.claude/skills`).
- Claude Code plugin: `/plugin install evoalgo --marketplace thonmay/ai-dynamic-graph-algorithms`.

Then ask the agent, for example: "Use the evoalgo skill to find a dynamic BFS
algorithm for pack dynamic_bfs". Each session is a run in `runs/` and shows in
`evoalgo ui`.

## Security

- API keys are read from environment variables (`OPENAI_API_KEY`,
  `OPENROUTER_API_KEY`, or the variable named by `api_key_env`); only the
  variable name is stored in run configs and logs.
- Candidate code is LLM-written and runs in a Linux namespace jail (no
  network, no home directory or token files, read-only file tree, own pid
  namespace, own IPC namespace) with resource limits: 4 GB address space,
  CPU time near the wall-clock timeout, 4 processes, 16 MB per file and 64
  open files, 64 MB scratch, 256 MB result output. It
  needs unprivileged user namespaces; without them the sandbox refuses to
  run unless `EVOALGO_SANDBOX=none` is set.
- Coding-agent harnesses get an allow-listed environment, not your full shell
  environment.
- `evoalgo ui` binds to 127.0.0.1 and needs the access token from the link it
  prints at start-up (or writes to `runs/.ui-link`, mode 600, when output is
  redirected); reach it from another machine through an SSH port-forward.

## Status

Implemented and evaluated: the web UI (`evoalgo ui`), the verifier and its
self-test (`evoalgo verify`), the cooperative and dynamic agents
(`evoalgo start`), and the evaluation campaigns in
[`campaign/analysis.md`](campaign/analysis.md).