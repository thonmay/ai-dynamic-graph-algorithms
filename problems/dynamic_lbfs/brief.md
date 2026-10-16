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
