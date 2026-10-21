"""Dynamic DFS forest maintenance (list-indexed state).

Maintains a DFS forest from root 0 under edge insertions/deletions.

Correctness rests on Yang et al.'s Lemma 1: a search spanning tree is a DFS
tree iff it has no forward-cross edge. A forward-cross edge is an edge u->v
with discover[u] < discover[v] where v is NOT a strict descendant of u.
Back edges (discover[u] > discover[v]) and forward edges (v a descendant of u)
are always legal.

The state is a valid certificate (parent + discover + finish) for the current
graph. An update is a no-op (return the state unchanged) exactly when it
cannot create a forward-cross edge and cannot change the reachable set:

  insert u->v: no-op iff u is unreachable, or (both reachable and the new
      edge is a back edge or a forward edge). Otherwise the edge either makes
      v newly reachable or creates a forward-cross edge -> recompute.
  delete u->v: no-op iff u->v is not a tree edge (parent[v] != u). Removing a
      non-tree edge neither creates a forward-cross edge nor disconnects the
      tree. Otherwise the tree is broken -> recompute.

Only when the forest is actually invalidated do we recompute from scratch.
State is list-indexed (faster than dicts) for the recompute.
"""


def _full_dfs(graph, n):
    """Standard DFS from root 0 with a shared counter. Returns (parent,
    discover, finish) as lists indexed by vertex."""
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    visited = [False] * n
    timer = [0]

    def dfs(u):
        visited[u] = True
        discover[u] = timer[0]
        timer[0] += 1
        row = graph[u]
        for v in range(n):
            if row[v] == 1 and not visited[v]:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1

    dfs(0)
    return parent, discover, finish


def _rebuild(graph, n):
    parent, discover, finish = _full_dfs(graph, n)
    return {"parent": parent, "discover": discover, "finish": finish, "n": n}


def init(graph):
    n = len(graph)
    return _rebuild(graph, n)


def insert_edge(graph, edge, state):
    u, v = edge
    discover = state["discover"]
    finish = state["finish"]
    du = discover[u]
    # u unreachable: the new edge cannot reach v (no root->...->u path), so
    # the reachable set and the forest are unchanged.
    if du is None:
        return state
    # v not yet reachable: it becomes reachable now -> recompute.
    if discover[v] is None:
        return _rebuild(graph, state["n"])
    # Both reachable: the new edge is legal (no forward-cross) iff it is a
    # back edge (u discovered after v) or a forward edge (v a descendant of u).
    dv = discover[v]
    if du > dv:
        return state
    if du < dv < finish[v] < finish[u]:
        return state
    # discover[u] < discover[v] and v not a descendant: forward-cross edge
    # created -> recompute.
    return _rebuild(graph, state["n"])


def delete_edge(graph, edge, state):
    u, v = edge
    # u->v is not a tree edge: removing it cannot create a forward-cross edge
    # nor disconnect the tree (v keeps its tree path to the root).
    if state["parent"][v] != u:
        return state
    # u->v is a tree edge: the tree is broken -> recompute.
    return _rebuild(graph, state["n"])
