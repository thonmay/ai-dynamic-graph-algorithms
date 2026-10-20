# evoalgo: Dynamic BFS tree maintenance

You are searching for a correct, efficient dynamic graph algorithm.
You edit one file, `candidate.py`, and grade it with `evoalgo check`.

## Problem

- Graph: directed; root: yes, vertex 0.
- Implement `init(graph)`, `insert_edge(graph, edge, state)`, `delete_edge(graph, edge, state)`; each returns the new state.
- `graph` is the 0/1 adjacency matrix (list of lists) after the update; `edge` is `(u, v)`. One update flips one entry.
- No globals, no module-level mutable state, standard library only.

State contract (what the grader reads):

```text
Return a dict with 'parent' and 'distances' (lists indexed by vertex, or dicts).
parent[root] = None; parent[v] = None for unreachable v.
distances[v] = BFS distance from the root; -1 or None for unreachable v.
Other keys are allowed and ignored.
```

## Loop

1. Edit `candidate.py`.
2. Run `evoalgo check` (default level `search`: all non-isomorphic graphs
   up to n = 4, seconds). Use `--level examples` for a faster n <= 3 check.
3. Read the JSON verdict. On FAIL, `first_failure` names the graph, the
   operation and what was wrong; fix the cause, not the symptom.
4. Keep a change if it fixes a failure or lowers `work_ratio` without
   breaking correctness; otherwise revert it.
5. Every check is logged to `results.tsv` and the run folder; do not edit them.
6. When the search grade passes and you cannot lower `work_ratio` further,
   run `evoalgo check --final` once (n <= 5, minutes) and report.

Correct first, then cheaper. Prefer the simpler of two equally good versions.
A recompute-from-scratch solution is correct but has `work_ratio` near 1;
the research question is how far below that you can go.

## Research brief

# Research brief: Dynamic BFS tree maintenance

Research question: can a BFS tree from a fixed root be maintained incrementally
under edge insertions and deletions, with work well below full recomputation?

The graph is directed; a fixed root r is given. After every update the state
must contain a valid BFS tree: it spans exactly the vertices reachable from r,
every non-root vertex has one parent that is a true in-neighbor, and the
parent of v sits one BFS distance closer to r than v does.

Known territory: Frigioni et al. give a semi-dynamic BFS algorithm with O(mn)
total work; the fully dynamic case is harder. A structurally different correct
approach is interesting even where a known solution exists.

Interface reminder: implement init(graph), insert_edge(graph, edge, state),
delete_edge(graph, edge, state). The state is passed in and returned; keep no
globals. Graphs are 0/1 adjacency matrices, vertex ids 0-based. Correctness is
checked by the invariant above, not by equality with a specific tree.

This is a calibration problem: the system should solve it without help, and it
validates the pipeline end to end.
