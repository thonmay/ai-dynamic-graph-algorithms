# evoalgo: Dynamic lexicographic BFS ordering

You are searching for a correct, efficient dynamic graph algorithm.
You edit one file, `candidate.py`, and grade it with `evoalgo check`.

## Problem

- Graph: undirected; root: no.
- Implement `init(graph)`, `insert_edge(graph, edge, state)`, `delete_edge(graph, edge, state)`; each returns the new state.
- `graph` is the 0/1 adjacency matrix (list of lists) after the update; `edge` is `(u, v)`. One update flips one entry.
- No globals, no module-level mutable state, standard library only.

State contract (what the grader reads):

```text
Return a dict with 'ordering': a list of all n vertices forming a valid LexBFS
ordering (any start vertex, any tie-break). Other keys are allowed and ignored.
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

# Research brief: Dynamic lexicographic BFS ordering

Research question: can a lexicographic BFS (LexBFS) ordering be maintained
under edge insertions and deletions? No efficient fully dynamic algorithm is
known - this is an open problem.

The graph is undirected. The maintained result is any valid LexBFS ordering
(no fixed tie-break, any start vertex). Validity is certified by the (LB)
4-point property of Corneil and Krueger: for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.

Known territory: the static partition-refinement LexBFS of Habib, McConnell,
Paul and Viennot runs in O(n+m). Maintaining the refinement under updates is
the open part; partition-refinement structures are the natural toolbox.

Interface reminder: implement init(graph), insert_edge(graph, edge, state),
delete_edge(graph, edge, state). The state is passed in and returned; keep no
globals. Graphs are 0/1 adjacency matrices, vertex ids 0-based.

This is the open tier: a correct solution would be a research contribution in
its own right, so favour novel data structures over recomputation.
