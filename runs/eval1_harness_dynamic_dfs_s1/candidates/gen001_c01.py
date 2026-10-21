"""Dynamic DFS forest maintenance from a fixed root (vertex 0).

The maintained forest is a valid DFS forest of the current directed graph
iff (Yang et al., Lemma 1) it has no forward-cross edge and its tree spans
every root-reachable vertex. A single edge flip breaks that invariant only
in three cases:

  1. insert u->v with u reachable and v not reachable
       -> v (and possibly more) become reachable;
  2. insert u->v with discover[u] < discover[v] and v not a descendant of u
       -> a forward-cross edge is created;
  3. delete u->v where u->v is a tree edge (parent[v] == u)
       -> the subtree under v may detach.

In every other case the forest stays valid and we return it unchanged in
O(1) (or O(out-degree) for the adjacency update). For the three breaking
cases we re-run the DFS over the adjacency lists we maintain in state, which
is O(n + m) -- cheaper than the O(n^2) full matrix scan of a recompute.
"""


def _full_dfs(n, adj):
    """Iterative DFS from root 0 over adjacency lists ``adj``.

    Returns {'parent': list, 'discover': dict, 'finish': dict} where
    discover/finish only contain reachable vertices and share one counter
    starting at 0 (discover[0] == 0).
    """
    parent = [None] * n
    discover = {}
    finish = {}
    discover[0] = 0
    timer = 1
    stack = [(0, iter(adj[0]))]
    while stack:
        u, it = stack[-1]
        pushed = False
        for v in it:
            if v not in discover:
                parent[v] = u
                discover[v] = timer
                timer += 1
                stack.append((v, iter(adj[v])))
                pushed = True
                break
        if not pushed:
            finish[u] = timer
            timer += 1
            stack.pop()
    return {'parent': parent, 'discover': discover, 'finish': finish}


def _is_descendant(u, v, discover, finish):
    """v is a descendant of u iff discover[u] < discover[v] < finish[v] < finish[u]."""
    return discover[u] < discover[v] < finish[v] < finish[u]


def init(graph):
    n = len(graph)
    adj = [[] for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].append(v)
    st = _full_dfs(n, adj)
    st['adj'] = adj
    return st


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].append(v)
    discover = state['discover']
    finish = state['finish']
    if u not in discover:
        # u not reachable: an edge out of it reaches no new vertex and
        # cannot create a forward-cross edge among reachable vertices.
        return state
    if v not in discover:
        # v (and possibly more) become reachable: re-search.
        st = _full_dfs(len(adj), adj)
        st['adj'] = adj
        return st
    # v reachable: only a forward-cross edge can break validity.
    if discover[u] < discover[v] and not _is_descendant(u, v, discover, finish):
        st = _full_dfs(len(adj), adj)
        st['adj'] = adj
        return st
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].remove(v)
    parent = state['parent']
    discover = state['discover']
    if v in discover and parent[v] == u:
        # tree edge removed: the subtree under v may detach, re-search.
        st = _full_dfs(len(adj), adj)
        st['adj'] = adj
        return st
    # non-tree edge: the tree still spans every reachable vertex, so the
    # forest stays valid.
    return state
