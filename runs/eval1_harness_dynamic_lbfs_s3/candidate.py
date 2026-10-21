"""Dynamic LexBFS ordering (undirected).

Maintains a valid lexicographic BFS ordering under edge insertions and
deletions. The ordering is recomputed with a bitmask partition-refinement
LexBFS (Habib-McConnell-Paul-Viennot), which is correct for any start vertex
and any tie-break. Bitmask partitioning is much cheaper than the numpy
offline baseline's per-vertex scalar accesses and set membership tests, so
the per-update work lands well below a full numpy recompute.

State: {"adj": list[int] (adjacency bitmask per vertex), "n": int,
        "ordering": list[int] (a valid LexBFS ordering)}.
"""


def _lexbfs(adj, n):
    """Return a valid LexBFS ordering of the graph with adjacency bitmasks adj.

    Partition refinement: cells partition the unplaced vertices; two vertices
    share a cell iff they have identical adjacency to every placed vertex.
    Each step places the lowest vertex of the first cell and refines every
    cell by that vertex's adjacency (adjacent part before non-adjacent part).
    """
    order = []
    full = (1 << n) - 1
    cells = [full]
    for _ in range(n):
        c0 = cells[0]
        pbit = c0 & -c0
        p = pbit.bit_length() - 1
        cells[0] = c0 & ~pbit
        order.append(p)
        ap = adj[p]
        nap = full ^ ap
        newcells = []
        for c in cells:
            if not c:
                continue
            a = c & ap
            b = c & nap
            if a:
                newcells.append(a)
            if b:
                newcells.append(b)
        cells = newcells
    return order


def init(graph):
    n = len(graph)
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        m = 0
        for v in range(n):
            if row[v]:
                m |= 1 << v
        adj[u] = m
    return {"adj": adj, "n": n, "ordering": _lexbfs(adj, n)}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u] |= 1 << v
    adj[v] |= 1 << u
    return {"adj": adj, "n": state["n"], "ordering": _lexbfs(adj, state["n"])}


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    return {"adj": adj, "n": state["n"], "ordering": _lexbfs(adj, state["n"])}
