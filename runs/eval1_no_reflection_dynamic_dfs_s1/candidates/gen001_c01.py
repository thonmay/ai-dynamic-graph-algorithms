"""Dynamic DFS forest from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  parent:  list, parent[v] or None (root / unreachable)
  disc:    list, discovery times (shared counter, root disc 0)
  finish:  list, finish times
  adj:     list of sets of out-neighbors (kept in sync with the matrix)
  n:       number of vertices

Correctness invariant (Yang et al. Lemma 1): the maintained tree is a DFS tree
iff it has no forward-cross edge, i.e. no edge u->v with disc[u] < disc[v] and
v not a descendant of u.  After each update we check this invariant; if it
holds we keep the forest, otherwise we recompute the DFS from scratch.

Work: O(n) per update for the invariant check (plus O(1) bookkeeping);
O(n^2) only when the forest actually has to change.
"""


def _dfs_full(graph, n):
    parent = [None] * n
    disc = [-1] * n
    finish = [-1] * n
    t = 0
    stack = [(0, 0)]
    disc[0] = 0
    t = 1
    while stack:
        u, i = stack.pop()
        advanced = False
        while i < n:
            if graph[u][i] and disc[i] == -1:
                parent[i] = u
                disc[i] = t
                t += 1
                stack.append((u, i + 1))
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[u] = t
            t += 1
    return parent, disc, finish


def _is_valid_forest(parent, disc, finish, adj, n):
    """Check the no-forward-cross-edge invariant.

    For every edge u->v with disc[u] < disc[v], v must be a descendant of u:
    disc[u] < disc[v] < finish[v] < finish[u].
    """
    for u in range(n):
        du = disc[u]
        if du < 0:
            continue
        fu = finish[u]
        for v in adj[u]:
            dv = disc[v]
            if dv < 0:
                # edge from a reachable vertex to an unreachable one:
                # the target should have been discovered
                return False
            if du < dv:
                if not (dv < finish[v] < fu):
                    return False
            elif dv < du:
                # edge u->v with v discovered before u: v must be an
                # ancestor of u (back edge), i.e. finish[u] < finish[v]
                if not (fu < finish[v]):
                    return False
            else:
                # du == dv: u == v (self-loop), always fine
                pass
    # Tree edges must be consistent with the discovery order: the parent of
    # each reachable non-root vertex must be its in-tree neighbor and must
    # have been discovered before it.
    for v in range(n):
        if disc[v] < 0:
            continue
        p = parent[v]
        if p is None:
            if v != 0:
                return False
        else:
            if p not in adj[v] or disc[p] >= disc[v]:
                return False
    # The parent chain of every reachable vertex must lead back to the root.
    # (The per-vertex disc[p] < disc[v] check above already rules out cycles,
    # so this walk is guaranteed to terminate.)
    for v in range(n):
        if disc[v] < 0:
            continue
        cur = v
        while cur is not None:
            cur = parent[cur]
        if cur != 0:
            return False
    return True


def _make_state(graph):
    n = len(graph)
    parent, disc, finish = _dfs_full(graph, n)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    return {
        'parent': parent,
        'discover': disc,
        'finish': finish,
        'adj': adj,
        'n': n,
    }


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].add(v)
    if _is_valid_forest(state['parent'], state['discover'], state['finish'], adj, state['n']):
        return state
    return _make_state(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].discard(v)
    if _is_valid_forest(state['parent'], state['discover'], state['finish'], adj, state['n']):
        return state
    return _make_state(graph)
