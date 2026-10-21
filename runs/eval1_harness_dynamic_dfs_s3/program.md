# evoalgo: Dynamic DFS forest maintenance

You are searching for a correct, efficient dynamic graph algorithm.
You edit one file, `candidate.py`, and grade it with `evoalgo check`.

## Problem

- Graph: directed; root: yes, vertex 0.
- Implement `init(graph)`, `insert_edge(graph, edge, state)`, `delete_edge(graph, edge, state)`; each returns the new state.
- `graph` is the 0/1 adjacency matrix (list of lists) after the update; `edge` is `(u, v)`. One update flips one entry.
- No globals, no module-level mutable state, standard library only.

State contract (what the grader reads):

```text
Return a dict with 'parent', 'discover' and 'finish' (lists indexed by vertex, or dicts).
parent[root] = None; for every vertex reachable from the root, parent[v] is a tree
in-neighbor discovered before v. Unreachable vertices are not checked.
discover/finish are DFS entry/exit times from one shared counter (e.g. root
discover 0); for every edge u->v between reachable vertices with
discover[u] < discover[v], v must be a descendant of u:
discover[u] < discover[v] < finish[v] < finish[u]. Any valid DFS order is accepted.
All three fields are required.
Other keys are allowed and ignored.
```

## Goal for this run

Reach full correctness first, then avoid a full recompute after updates.

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

# Research brief: Dynamic DFS forest maintenance

Research question: how can a DFS forest from a fixed root be maintained under
edge insertions and deletions without redoing the whole search?

The graph is directed. The maintained forest must be a genuine DFS forest of
the current graph: Yang et al.'s Lemma 1 characterizes it - a search spanning
tree is a DFS tree iff it has no forward-cross edges. Forward and back edges
are fine; only a forward-cross edge (source discovered before target, no
ancestor relation) invalidates the forest.

The standard approach: decide whether the update affects the forest at all,
identify the affected "candidate interval", and re-search only that portion.

Interface reminder: implement init(graph), insert_edge(graph, edge, state),
delete_edge(graph, edge, state). The state is passed in and returned; keep no
globals. Graphs are 0/1 adjacency matrices, vertex ids 0-based. The verifier
certifies the forest with parent pointers plus discovery/finish times.

This is a calibration problem: solutions exist in the literature (Yang et al.),
so it validates that the agents can reproduce a known dynamic algorithm.
