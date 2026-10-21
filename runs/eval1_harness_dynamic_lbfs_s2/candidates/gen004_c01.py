"""Dynamic algorithm candidate. Edit this file; keep the three functions.

Strategy: recompute a valid LexBFS ordering from scratch after every update,
using a bitmask-label LexBFS. label[u] is the bitstring of u's non-adjacencies
to the already-ordered vertices, with position 0 (the first selected vertex)
as the most significant bit, so the numeric minimum of (label, id) is exactly
the lexicographically-smallest LexBFS choice (neighbours preferred, id
tie-break). Each step is O(n) integer bit-ops, so the whole search is O(n^2)
with a small constant and no per-step list allocation.

A keep-if-valid variant was measured to cost more than this recompute (the
(LB) validity check has a larger constant than the recompute), so the fastest
recompute minimises work_ratio.
"""


def _lexbfs(graph):
    """Bitmask-label LexBFS. Returns a valid LexBFS ordering of the undirected
    graph given as a 0/1 adjacency matrix (start 0, min-id tie-break)."""
    n = len(graph)
    label = [0] * n
    unvisited = list(range(n))
    order = []
    for step in range(n):
        best = -1
        best_label = -1
        for u in unvisited:
            lu = label[u]
            if best < 0 or lu < best_label or (lu == best_label and u < best):
                best = u
                best_label = lu
        order.append(best)
        unvisited.remove(best)
        row = graph[best]
        bit = 1 << (n - 1 - step)  # position 0 = MSB -> numeric == lexicographic
        for u in unvisited:
            if not row[u]:
                label[u] |= bit
    return order


def init(graph):
    return {"ordering": _lexbfs(graph)}


def insert_edge(graph, edge, state):
    return {"ordering": _lexbfs(graph)}


def delete_edge(graph, edge, state):
    return {"ordering": _lexbfs(graph)}
