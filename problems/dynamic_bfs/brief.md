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
