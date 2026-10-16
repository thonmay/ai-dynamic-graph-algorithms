# Research brief: Dynamic strongly connected components

Research question: can the SCC partition of a directed graph be maintained
under edge insertions and deletions, with per-update work far below
recomputing the whole decomposition?

The maintained result is a partition of the vertices into sets C1..Ck such
that within each Ci every vertex reaches every other via edges inside Ci, the
sets are disjoint and cover all vertices, and each Ci is maximal.

Known territory: Bernstein et al. give an almost-linear decremental SCC
algorithm; the fully dynamic case is substantially harder. Union-find based
connectivity structures and partition refinement are the standard toolbox.

Interface reminder: implement init(graph), insert_edge(graph, edge, state),
delete_edge(graph, edge, state). The state is passed in and returned; keep no
globals. Graphs are 0/1 adjacency matrices, vertex ids 0-based.

This is a core-tier problem: harder than the calibration pair, and a real
research target rather than a known-solution reproduction.
