"""Dynamic DFS forest maintenance.

Maintains a DFS forest (parent / discover / finish) from a fixed root (0)
under single edge insertions and deletions.

A directed spanning forest is a genuine DFS forest iff it has no
forward-cross edge (Yang et al. Lemma 1): for every edge u->v between
reachable vertices with discover[u] < discover[v], v must be a descendant
of u (discover[u] < discover[v] < finish[v] < finish[u]).

Strategy:
  * Most updates are no-ops for the forest:
      - insert (u,v): only invalidates if it creates a forward-cross edge,
        i.e. u and v reachable, discover[u] < discover[v], and v not a
        descendant of u.  A back edge (discover[v] < discover[u]) or a
        forward edge (v a descendant of u) keeps the forest valid.
      - delete (u,v): only invalidates if it was a tree edge
        (parent[v] == u).  Deleting a non-tree edge never creates a
        forward-cross edge, so the forest stays valid.
  * On the rare invalidating update we recompute the whole forest with a
    single iterative DFS (O(n^2) on the adjacency matrix).
"""


def _recompute(graph):
    """Full iterative DFS from root 0; returns (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    timer = 0
    stack = [(0, 0)]
    discover[0] = 0
    timer = 1
    while stack:
        u, i = stack[-1]
        row = graph[u]
        advanced = False
        while i < n:
            if row[i] == 1 and discover[i] is None:
                parent[i] = u
                discover[i] = timer
                timer += 1
                stack[-1] = (u, i + 1)
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            stack.pop()
            finish[u] = timer
            timer += 1
    return parent, discover, finish


def init(graph):
    parent, discover, finish = _recompute(graph)
    return {"parent": parent, "discover": discover, "finish": finish}


def _state(parent, discover, finish):
    return {"parent": parent, "discover": discover, "finish": finish}


def insert_edge(graph, edge, state):
    u, v = edge
    discover = state["discover"]
    finish = state["finish"]
    du = discover[u]
    dv = discover[v]
    if du is None:
        # u unreachable: u->v cannot make anything newly reachable (u is the
        # source) and cannot be a forward-cross edge between reachable verts.
        return state
    # u is reachable.
    if dv is None:
        # v was unreachable; u->v makes v (and possibly more) newly reachable.
        parent, discover, finish = _recompute(graph)
        return _state(parent, discover, finish)
    # Both reachable. A back edge (du >= dv) is fine; a forward edge is fine
    # only if v is a descendant of u. Otherwise it is a forward-cross edge.
    if du < dv and not (dv < finish[v] < finish[u]):
        parent, discover, finish = _recompute(graph)
        return _state(parent, discover, finish)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    # Only a tree edge removal invalidates the forest.
    if state["parent"][v] == u:
        parent, discover, finish = _recompute(graph)
        return _state(parent, discover, finish)
    return state
