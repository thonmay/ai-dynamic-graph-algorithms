# Research brief: Dynamic maximal cardinality search ordering

Research question: can a maximal cardinality search (MCS) ordering be
maintained under edge insertions and deletions, with per-update work far
below recomputing the ordering from scratch?

The graph is undirected. The maintained result is a vertex ordering in which
each vertex, when chosen, has cardinality (number of already-chosen neighbors)
maximal among the unchosen vertices, under a stated deterministic tie-break.
For chordal inputs such an ordering is a perfect elimination ordering (PEO).

Known territory: the static MCS algorithm is classic (Rose, Tarjan, Lueker);
the dynamic variant is the primary research target of this project.
Maintaining the running maximum cardinality under updates is the crux.

Interface reminder: implement init(graph), insert_edge(graph, edge, state),
delete_edge(graph, edge, state). The state is passed in and returned; keep no
globals. Graphs are 0/1 adjacency matrices, vertex ids 0-based. The verifier
replays the ordering and certifies the cardinality property directly.

This is a core-tier problem and the main discovery target: expect the
interesting algorithms to appear here.
