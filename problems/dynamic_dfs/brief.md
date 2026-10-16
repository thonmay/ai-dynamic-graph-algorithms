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
