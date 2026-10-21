"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Strategy:
- init: full DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If v is already reachable and (v is an ancestor of u, or v is a
      descendant of u, or discover[v] < discover[u]): the new edge is a
      back/forward edge and the forest stays a valid DFS forest.
    * If v is unreachable and u is reachable: the new edge makes v
      (and possibly more) reachable.  Re-search only the affected
      interval: re-search from u in the new graph, treating vertices
      with old discover < discover[u] as already-discovered.  The
      new times are spliced into the old ones.
    * Otherwise (forward-cross edge, or u unreachable): recompute.
- delete_edge(u, v):
    * If the deleted edge is not a tree edge, the forest is unchanged.
    * If it is a tree edge: recompute the DFS from scratch.

The recompute fallback guarantees correctness in all cases; the fast paths
handle the common cases without touching the forest.
"""


def _dfs(graph, n):
    """Full DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    def visit(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                visit(v)
        finish[u] = counter[0]
        counter[0] += 1

    if n > 0:
        visit(0)
    return parent, discover, finish


def _is_ancestor(discover, finish, a, b):
    """True if a is an ancestor of b (or a == b) in the DFS tree."""
    if discover[a] == -1 or discover[b] == -1:
        return False
    return discover[a] <= discover[b] and finish[b] <= finish[a]


def init(graph):
    n = len(graph)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def _local_insert_research(graph, n, u, v, parent, discover, finish):
    """Re-search the affected interval after inserting edge u->v where
    v was unreachable and u is reachable.

    Re-search from u in the new graph, treating vertices with old
    discover < discover[u] as already-discovered (they keep their old
    times).  The counter starts at discover[u] (u is re-discovered at
    the same time).  All other vertices in the affected set get new
    times.

    Returns (new_parent, new_discover, new_finish).
    """
    # New arrays: start with old values.
    new_discover = list(discover)
    new_finish = list(finish)
    new_parent = list(parent)

    # Vertices with old discover < discover[u] are "pre-discovered":
    # they keep their old times and are treated as already-discovered
    # in the re-search.
    pre_discovered = set(
        x for x in range(n) if discover[x] != -1 and discover[x] < discover[u]
    )

    # Reset the affected vertices (old discover >= discover[u]) so they
    # will be re-discovered.
    for x in range(n):
        if discover[x] != -1 and discover[x] >= discover[u]:
            new_discover[x] = -1
            new_finish[x] = -1
            new_parent[x] = None
    # v was unreachable, so it's already -1.

    # Re-search from u.  The counter starts at discover[u].
    counter = [discover[u]]

    def visit(x):
        new_discover[x] = counter[0]
        counter[0] += 1
        for w in range(n):
            if graph[x][w]:
                if w in pre_discovered:
                    continue
                if new_discover[w] == -1:
                    new_parent[w] = x
                    visit(w)
        new_finish[x] = counter[0]
        counter[0] += 1

    visit(u)

    return new_parent, new_discover, new_finish


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # v already reachable: check whether the new edge is harmless.
    if discover[v] != -1:
        # back edge (v ancestor of u) or forward edge (v descendant of u): fine
        if _is_ancestor(discover, finish, v, u) or _is_ancestor(discover, finish, u, v):
            return state
        # v discovered before u: edge goes "backwards" in time, fine
        if discover[v] < discover[u]:
            return state
        # v discovered after u but not a descendant: forward-cross edge -> recompute
        # fall through

    # v unreachable: try a local re-search of the affected interval.
    if discover[v] == -1:
        # If u is unreachable, the new edge connects two unreachable
        # vertices; the reachable set is unchanged.
        if discover[u] == -1:
            return state
        # If u is the root, the new edge changes the root's adjacency and
        # the whole order may shift; recompute.
        if u == 0:
            parent, discover, finish = _dfs(graph, n)
            return {
                'parent': parent,
                'discover': discover,
                'finish': finish,
            }

        # Local re-search: re-search from u, treating vertices with
        # old discover < discover[u] as already-discovered.
        new_parent, new_discover, new_finish = _local_insert_research(
            graph, n, u, v, parent, discover, finish
        )
        return {
            'parent': new_parent,
            'discover': new_discover,
            'finish': new_finish,
        }

    # forward-cross case: recompute
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']

    # If the deleted edge is not a tree edge, the forest is unchanged.
    if parent[v] != u:
        return state

    # Tree edge deleted: recompute
    n = len(graph)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
