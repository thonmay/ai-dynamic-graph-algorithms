# Research brief: Dynamic single-source reachability

Research question: can the set of vertices reachable from a fixed source be
maintained under edge insertions and deletions, cheaper than re-running the
search after every update?

The graph is directed and the source s is fixed. After every update the state
must contain exactly the true reachability set from s. This is the simplest
dynamic connectivity-style invariant: a vertex enters the set when an edge
into it from the set appears, and must be tracked out (possibly with a whole
cascade) when the last such edge disappears.

Known territory: Even-Shiloach trees give O(mn) total work for decremental
single-source reachability; the fully dynamic case needs more.

Interface reminder: implement init(graph), insert_edge(graph, edge, state),
delete_edge(graph, edge, state). The state is passed in and returned; keep no
globals. Graphs are 0/1 adjacency matrices, vertex ids 0-based.

This is a core-tier problem: a stepping stone between calibration and the open
order-maintenance problems, and useful for validating the pipeline on a
set-valued (rather than tree-valued) invariant.
