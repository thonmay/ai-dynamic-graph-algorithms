---
name: dynamic-graph-algorithms
description: Domain knowledge for the thesis evolutionary code-repair system on dynamic graph algorithms: candidate interface, evaluator contract, correctness invariants per problem, Yang et al. dynamic-DFS insight and interval method, data-structure toolbox, nauty enumeration pipeline, difficulty tiers, code conventions. Load when generating, repairing, or reflecting on candidate dynamic graph algorithms.
---

# Dynamic Graph Algorithms - Discovery Domain Knowledge

Shared knowledge for the evolutionary code-repair system. Used by the
generator, repairer, and reflector roles. If instructions here conflict with
the problem definition in the task message, the task message wins.

## Candidate interface (must implement exactly)

The evaluator imports the candidate as a Python module and expects three
pure functions. State is passed in and returned, never stored in globals or
module-level variables.

- `init(graph)` - build and return the initial state from the starting
  adjacency matrix.
- `insert_edge(graph, edge, state)` - update and return the new state after
  inserting edge (u, v).
- `delete_edge(graph, edge, state)` - update and return the new state after
  deleting edge (u, v).

There is no `get_result()` method. The maintained result (tree, ordering,
partition, set) is part of the returned state; the evaluator extracts it.

Graphs are simple, loop-free 0/1 adjacency matrices (directed or undirected
per the problem). A legal update flips exactly one matrix entry (insert or
delete of one edge); there is no structural mutation. Vertex ids are
0-based integers.

## Evaluator contract

For each base graph in the bounded test universe:
1. Build the offline result on the base graph.
2. For each operation sequence (bounded length, interleaved insert/delete):
   a. Run the candidate's dynamic update.
   b. Run the offline algorithm from scratch on the modified graph.
   c. Check the problem's invariant after EVERY operation against the oracle.
   d. If correct, count instrumented work (vertices visited, edges scanned).

Verdicts:
- PASS - invariant holds on every tested graph and operation.
- FAIL - invariant violated on some tested case (the failing case is
  recorded), or the per-candidate wall-clock timeout is exceeded (recorded
  with a `timeout=true` flag).
- CRASH - invalid Python, missing method, runtime exception, or sandbox
  resource violation.

There is no separate TIMEOUT verdict; timeout maps to FAIL with a flag.

Efficiency: work_ratio = candidate_work / offline_work, aggregated (median)
across operations and graphs. An improvement requires work_ratio < 1.
Wall-clock is separate from instrumented work.

Bounded, not proof: the evaluator outputs "no counterexample within the
stated bound" (graph size, sequence length, sample count, seed recorded in
the run config). It does not claim correctness for arbitrary size.

## Correctness invariants per problem

Judgment is by invariant, NOT by reference equality: two valid algorithms on
the same graph may produce different trees/orders. A candidate passes if the
maintained result satisfies the invariant, not if it equals a specific oracle
output.

- Dynamic BFS (directed): the maintained tree is a valid BFS tree of the
  current graph from a stated root. It (1) is connected and spans every
  vertex reachable from the root r; (2) gives every non-root vertex exactly
  one parent p; (3) satisfies delta(p) = delta(v) - 1, where delta(v) is
  the BFS distance from r.
- Dynamic DFS (directed): the maintained forest is a valid DFS forest of
  the current graph. Yang et al. Lemma 1: a search spanning tree is a DFS
  tree iff it has no forward-cross edges. A forward edge (ancestor to
  descendant) is permitted; a back edge (descendant to ancestor) is
  permitted; a forward-cross edge (no ancestor relation, source discovered
  before target) is the defect that invalidates the forest. Validity is
  verified operationally via a DFS-forest certificate (parent pointers plus
  discovery and finish times): the certificate test reconstructs whether
  the forest could have been produced by a DFS of the current graph.
- Dynamic MCS (undirected, primary target): the output is a vertex ordering
  that is a valid MCS ordering of the current graph: each vertex is chosen
  when its cardinality (number of already-chosen neighbors) is maximal
  among the unchosen vertices, for the stated tie-breaking. For chordal
  inputs the ordering is a perfect elimination ordering (PEO). Oracle:
  replay the ordering and confirm each chosen vertex had maximum
  cardinality; for chordal inputs, additionally run the classic O(n+m) PEO
  check (later neighbors of each vertex form a clique).
- Dynamic SCC (directed): the output partitions vertices into sets C1..Ck
  such that within each Ci every vertex reaches every other via edges inside
  Ci; the sets are disjoint and cover all vertices; each Ci is maximal.
- Dynamic LBFS (directed): the output is a total ordering pi that is a
  valid lexicographic BFS ordering. Validity is verified against the LexBFS
  cone / interval characterization of Rose (1976) using a reference LexBFS
  implementation as oracle, not an ad-hoc neighbor-consecutiveness
  predicate (which fails on valid orderings like a four-cycle).
- Reachability (directed): for a fixed source s, the maintained set R of
  vertices reachable from s equals the true reachability set of the current
  graph.

## Yang et al. dynamic-DFS (gold-standard reference)

Full dynamic DFS in directed graphs. Lemma 1 (Yang et al.): a search
spanning tree is a valid DFS tree iff it contains no forward-cross edges.
Forward edges (ancestor to descendant) and back edges (descendant to
ancestor) are permitted; only forward-cross edges (no ancestor relation,
source discovered before target) invalidate the forest. The certificate
test (parent pointers plus discovery and finish times) is the operational
form of this check.

The general approach when an edge is inserted or deleted:
1. Check whether the forest needs updating (only certain insertions and
   tree-edge deletions require updates).
2. Identify the affected portion of the forest (the "candidate interval").
3. Reconstruct only that portion via a constrained DFS.
4. Update time intervals for affected vertices.

Key domain references: Yang et al. (fully dynamic DFS, directed; Lemma 1
no-forward-cross-edge characterization above), Frigioni et al.
(semi-dynamic BFS, O(mn) total), Baswana et al. (incremental DFS),
Bernstein et al. (almost-linear decremental SCC), Morse & Kozsik (fully
dynamic loop nesting forests on reducible flow graphs, built on the
Yang et al. dynamic-DFS backend; the canonical example of a novel
dynamic abstraction discovered by extending dynamic DFS), Shinn et al.
(Reflexion: verbal reinforcement learning with structured self-reflection;
the pattern the reflector role follows).

## Data structure toolbox

May use or reinvent any of these:

- Union-Find (disjoint set): near-O(1) amortized union/find via union by
  rank + path compression. Useful for connectivity, SCC maintenance.
- Even-Shiloach (ES) trees: maintain a BFS tree under edge deletions,
  O(mn) total time. The standard decremental shortest-path structure.
- Link-cut trees (Sleator-Tarjan): maintain a forest under link (add edge),
  cut (remove tree edge), and path queries in O(log n) amortized. The
  standard fully dynamic tree structure.
- Euler tour trees: represent a tree as a sequence; support link, cut, and
  subtree queries in O(log n). Alternative to link-cut trees for
  connectivity and tree maintenance.
- Dynamic connectivity (Holm-de Lichtenberg-Thorup, HLT): maintain
  connected components under edge insertions and deletions in O(log^2 n)
  amortized per operation. The gold standard for fully dynamic graph
  connectivity.
- Partition refinement: maintain a partition supporting split, O(n log n).
  Used in LBFS, DFA minimization, modular decomposition. Key for dynamic
  LBFS, an open problem.

If an existing structure is insufficient, propose a novel one: describe the
operations it must support and design it.

## Difficulty tiers

- Tier 1 calibration (solutions likely in training data): dynamic DFS,
  dynamic BFS (directed). Purpose: validate the system works.
- Tier 2 primary target: dynamic MCS (undirected). MCS produces PEOs for
  chordal graphs and is the main discovery target. Known solutions exist
  for the static case; the dynamic variant is the research target.
- Tier 3 harder (directed): dynamic SCC, dynamic reachability.
- Tier 4 open (directed): dynamic LBFS with partition refinement under
  edge updates.

Mitigating training-data recall on Tier 1: prefer non-standard problem
formulations (specific root, specific tie-breaking) that don't match
published pseudocode. A structurally different correct approach is
interesting even if a known solution exists.

## Nauty enumeration pipeline

Non-isomorphic graph generation:
- `geng n` - all non-isomorphic undirected graphs on n vertices
- `directg` - converts each undirected edge into one direction, the other,
  or both (2-cycle), producing all non-isomorphic directed versions
- Pipeline for directed problems: `geng n | directg` -> all non-isomorphic
  digraphs on n vertices
- For undirected problems (MCS): `geng n` alone (no directg)

Counts (directed): n=3: 16, n=4: 218, n=5: 9608, n=6: ~1.5M, n=7: ~1B
(infeasible). Exhaustive testing is practical up to n=5 or 6; beyond that,
random sampling with a stated seed and distribution.

## Code conventions

- Python 3.11+, clean and readable.
- Candidate files are named gen{N}_c{M}.py (e.g. gen001_c01.py).
- Core algorithm logic should be short (7-15 lines is typical for good
  dynamic graph algorithms).
- Clear variable names, no clever tricks.
- One-line problem description + short approach note as comments at the top
  of each candidate file.
- The evaluator is trusted infrastructure. Never modify it.