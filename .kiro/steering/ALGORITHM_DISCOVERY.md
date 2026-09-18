# Algorithm Discovery Project — Steering

## What This Project Is

A thesis investigating whether a single LLM, through iterative generate-evaluate-reflect loops, can discover correct and efficient dynamic (incremental/decremental) graph algorithms — starting from known offline algorithms.

The agent generates candidate algorithms, tests them exhaustively, reflects on failures, and iterates. An outer Python orchestrator manages an evolutionary population of candidates across generations.

## Architecture

Two-layer design:

- **Outer loop (Python orchestrator)**: manages population of candidates, selection, mutation, crossover. Calls Kiro non-interactively per generation. Scores candidates, maintains evolutionary state.
- **Inner loop (Kiro agent `algorithm-discoverer`)**: receives a problem + context, generates a candidate, runs the evaluator, reflects on failures, iterates. Fully autonomous, no human interaction.

Invocation:
```bash
kiro-cli chat --no-interactive --trust-all-tools --agent algorithm-discoverer --model claude-opus-4-6 "<prompt>"
```

Parallel variants via subagents (island model, up to 4 parallel). Each subagent gets the same agent config but a different mutation of the parent candidate. All relevant context (parent code, failing tests, reflections) must be serialized into each subagent's prompt — subagents don't share state.

## Directory Structure

```
candidates/       — generated algorithm implementations (.py)
evaluator/        — test harness code (pre-built, trusted infrastructure)
reflections/      — structured failure analyses
results/          — evaluation outputs, scores, summaries
```

## Critical Rule: The Evaluator Is Trusted Infrastructure

The evaluator must be pre-built and human-verified. It is the scientific instrument of this thesis — it determines correctness. The agent must NEVER write or modify the evaluator. If the evaluator has a bug, the agent will "discover" wrong algorithms that pass broken tests, invalidating results.

The evaluator should be tested against the supervisor's hand-written reference implementations before any agent runs.

### What the Evaluator Does

For each non-isomorphic digraph G up to size n (via nauty `geng | directg`):
1. Build the offline result (e.g., BFS tree) on G
2. For each possible edge operation (insertion or deletion):
   a. Run the candidate's dynamic update
   b. Run the offline algorithm from scratch on the modified graph
   c. Compare results — mismatch = failure, record the failing case
   d. If correct: count operations (vertices visited, edges scanned) for efficiency measurement

Exhaustive testing is practical up to n=5 or 6. For larger sizes, use random sampling.

## Problem Difficulty Tiers

**Tier 1 — Calibration** (solutions likely in training data):
- Dynamic DFS: Yang et al. VLDB 2020
- Dynamic BFS: Frigioni et al. 2000
- Purpose: validate the system works. If the agent can't solve these, the system has issues.

**Tier 2 — Harder** (less likely in training data):
- Dynamic SCC using Union-Find or novel structures
- Dynamic reachability, dominator trees

**Tier 3 — Open problem** (genuine discovery):
- Dynamic LBFS with partition refinement maintenance under edge updates
- No published solution exists. Progress here is a genuine contribution.

## Mitigating Training Data Recall

For Tier 1 problems, the agent may reproduce known solutions from training data. To distinguish reasoning from recall:
- Use non-standard problem formulations (e.g., specific root vertex, specific tie-breaking rules) that don't match published pseudocode
- Compare agent output structure against known papers to detect verbatim reproduction vs. novel derivation
- A structurally different correct approach is interesting even if a known solution exists
- The real test is Tier 2-3 problems where no published solution exists

## Efficiency Measurement

Candidate algorithms must be instrumented to count:
- Number of vertices visited
- Number of edges scanned

Compare against O(|V| + |E|) full recomputation. The orchestrator/evaluator should collect these metrics automatically.

## Code Conventions

- Python 3, clean and readable
- Core algorithm logic should be short (7-15 lines is typical for good dynamic graph algorithms)
- Clear variable names, no clever tricks
- Algorithm description as comments at the top of each candidate file
- Naming: `candidates/{problem}_{attempt_number}.py` (e.g., `candidates/dfs_insert_001.py`)

## Key Domain References

- **Yang et al. VLDB 2020** — Fully dynamic DFS in directed graphs. Gold-standard benchmark. Core insight: valid DFS-Tree ↔ no forward-cross edges. Both insertion and deletion reduce to eliminating forward-cross edges. Three algorithm levels: basic (Alg 4/5), optimized candidate intervals, hybrid graph/tree search.
- **Frigioni et al. 2000** — Semi-dynamic BFS in digraphs. O(mn) total time.
- **Baswana et al. 2017** — Incremental DFS. O(n) worst-case per insertion for undirected graphs.
- **Bernstein et al. 2023** — Almost-linear time incremental SCC, cycle detection.

## Nauty Tooling

Non-isomorphic digraph generation:
- `geng n` — all non-isomorphic undirected graphs on n vertices
- `directg` — orients edges into all non-isomorphic directed versions
- Pipeline: `geng n | directg` → all non-isomorphic digraphs on n vertices

Counts by vertex count: n=3: 16, n=4: 218, n=5: 9608, n=6: ~1.5M, n=7: ~1B (infeasible).

Parse digraph6 output into NetworkX DiGraph objects. Use nauty CLI directly, not SageMath.
