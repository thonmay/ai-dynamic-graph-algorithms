"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Maintains a genuine DFS forest (parent, discover, finish) of the current
directed graph.  Correctness invariant (Yang et al. Lemma 1): a spanning
search tree is a DFS tree iff it has no forward-cross edge, i.e. no edge
u->v with discover[u] < discover[v] and v not a descendant of u.

Strategy:
- Insertion: if the new edge is a forward-cross edge, re-search the
  candidate interval [discover[u], finish[u]] (the subtree rooted at u plus
  everything discovered after u's subtree, up to u's finish time).  This
  interval contains every vertex whose DFS order could change.
- Deletion: if the deleted edge is a tree edge, the subtree rooted at its
  child is detached; re-search that subtree from the child (it may be
  reattached elsewhere via non-tree edges).  If the deleted edge is not a
  tree edge, the forest remains a valid DFS forest (removing a non-tree
  edge cannot create a forward-cross edge), so nothing changes.
"""


def _dfs_from(graph, start, state, counter):
    """Iterative DFS from `start` over the current graph.

    Discovers vertices in adjacency-matrix order (0..n-1).  Returns the
    counter after the search.  Updates state['parent'], state['discover'],
    state['finish'] in place.
    """
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)
    stack = [(start, 0)]
    discover[start] = counter
    counter += 1
    parent[start] = None
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < n:
            if graph[u][i]:
                if discover[i] == -1:
                    discover[i] = counter
                    counter += 1
                    parent[i] = u
                    stack[-1] = (u, i + 1)
                    stack.append((i, 0))
                    advanced = True
                    break
            i += 1
        if not advanced:
            stack.pop()
            finish[u] = counter
            counter += 1
    return counter


def _reset_interval(state, lo, hi):
    """Reset parent/discover/finish for vertices with lo <= discover < hi."""
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    for v in range(len(discover)):
        if lo <= discover[v] < hi:
            discover[v] = -1
            finish[v] = -1
            parent[v] = None


def _retime(state, lo, hi):
    """Reassign discover/finish in [lo, hi) to a fresh contiguous block
    starting at lo, preserving relative order."""
    discover = state['discover']
    finish = state['finish']
    n = len(discover)
    verts = [v for v in range(n) if lo <= discover[v] < hi]
    verts.sort(key=lambda v: (discover[v], finish[v]))
    counter = lo
    for v in verts:
        discover[v] = counter
        counter += 1
    for v in sorted(verts, key=lambda v: finish[v]):
        finish[v] = counter
        counter += 1
    return counter


def init(graph):
    n = len(graph)
    state = {
        'parent': [None] * n,
        'discover': [-1] * n,
        'finish': [-1] * n,
    }
    counter = 0
    if n > 0:
        counter = _dfs_from(graph, 0, state, counter)
    return state


def _is_descendant(state, u, v):
    """True if v is a proper descendant of u in the current DFS forest."""
    d = state['discover']
    f = state['finish']
    return d[u] < d[v] and f[v] < f[u]


def insert_edge(graph, edge, state):
    u, v = edge
    d = state['discover']
    f = state['finish']
    # u unreachable: the new edge cannot make anything reachable from the
    # root (u itself is not), so the forest is unaffected.
    if d[u] == -1:
        return state
    # v unreachable but u reachable: the new edge makes v (and everything
    # reachable from v) newly reachable from the root.  Extend the forest
    # by searching from v with times after all existing ones.  The new
    # u->v edge is a tree edge in the new forest, so the order stays valid.
    if d[v] == -1:
        # Nest v's subtree inside u's interval: u->v is a tree edge, so
        # v must be a descendant of u (discover[u] < discover[v] <
        # finish[v] < finish[u]).  Search from v with times after all
        # existing ones, then re-time u's interval to absorb them.
        counter = max(f) + 1
        _dfs_from(graph, v, state, counter)
        state['parent'][v] = u
        _retime(state, d[u], max(f) + 1)
        return state
    # Back edge (v discovered before u) or tree edge: fine.
    if d[v] < d[u]:
        return state
    # Forward edge (v descendant of u): fine.
    if _is_descendant(state, u, v):
        return state
    # Forward-cross edge: re-search the candidate interval.
    lo = d[u]
    hi = f[u]
    _reset_interval(state, lo, hi)
    counter = lo
    counter = _dfs_from(graph, u, state, counter)
    # Re-time the rest of the interval (vertices discovered after u's
    # subtree, up to the old finish of u) to keep a valid global order.
    _retime(state, counter, hi)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    d = state['discover']
    f = state['finish']
    # Only a tree-edge deletion can break the forest.
    if parent[v] != u:
        return state
    # Detach the subtree rooted at v and re-search it from v.
    lo = d[v]
    hi = f[v]
    _reset_interval(state, lo, hi)
    counter = lo
    counter = _dfs_from(graph, v, state, counter)
    _retime(state, counter, hi)
    return state
