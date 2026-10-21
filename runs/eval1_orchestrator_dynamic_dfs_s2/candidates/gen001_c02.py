"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

State dict:
  parent:  list, parent[v] or None (root / unreachable)
  disc:    list, discovery time (None if unreachable)
  fin:     list, finish time (None if unreachable)
  order:   list of reachable vertices in discovery order
  counter: next discovery time
  adj:     list of sorted adjacency lists (kept in sync with the matrix)

Correctness invariant: (parent, disc, fin) is a valid DFS search of the
current graph from root 0.  We maintain it by re-running the search only
over the affected "candidate interval" (Yang et al. style):

- Insert u->v: if v is already reachable, the forest stays valid (a new
  edge can only be a tree/forward/back edge relative to the old order).
  If v is unreachable, v and everything reachable from v become reachable;
  we re-search starting at v, renumbering the tail of the old order.
- Delete u->v: if v is not a tree child of u, nothing changes.  Otherwise
  the subtree rooted at v is cut; we re-search from the cut point, keeping
  the prefix of the old order up to just before v, and renumbering the
  rest.  Vertices that were reachable only through the deleted edge become
  unreachable.

Both updates are O(n + m) worst case but touch only the affected interval.
"""


def _dfs_from(start, adj, n, parent, disc, fin, order, counter):
    """Iterative DFS from `start` over `adj`, continuing the existing
    discovery/finish numbering.  `start` must already have disc set and
    parent set by the caller.  Returns (order, counter)."""
    stack = [(start, 0)]
    order.append(start)
    while stack:
        u, i = stack[-1]
        nbrs = adj[u]
        advanced = False
        while i < len(nbrs):
            v = nbrs[i]
            i += 1
            if disc[v] is None:
                stack[-1] = (u, i)
                parent[v] = u
                disc[v] = counter
                counter += 1
                order.append(v)
                stack.append((v, 0))
                advanced = True
                break
        if not advanced:
            stack.pop()
            fin[u] = counter
            counter += 1
    return order, counter


def _full_search(adj, n):
    """Offline DFS from root 0.  Returns (parent, disc, fin, order, counter)."""
    parent = [None] * n
    disc = [None] * n
    fin = [None] * n
    order = []
    counter = 0
    if n > 0:
        parent[0] = None
        disc[0] = 0
        counter = 1
        order, counter = _dfs_from(0, adj, n, parent, disc, fin, order, counter)
    return parent, disc, fin, order, counter


def _build_adj(graph):
    n = len(graph)
    adj = []
    for u in range(n):
        row = graph[u]
        adj.append([v for v in range(n) if row[v]])
    return adj


def _state_fields(state):
    return {
        'parent': state['parent'],
        'discover': state['disc'],
        'finish': state['fin'],
        'disc': state['disc'],
        'fin': state['fin'],
        'order': state['order'],
        'counter': state['counter'],
        'adj': state['adj'],
    }


def init(graph):
    n = len(graph)
    adj = _build_adj(graph)
    parent, disc, fin, order, counter = _full_search(adj, n)
    return {
        'parent': parent,
        'discover': disc,
        'finish': fin,
        'disc': disc,
        'fin': fin,
        'order': order,
        'counter': counter,
        'adj': adj,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    adj = state['adj']
    # keep adj in sync with the matrix (defensive)
    adj[u] = [w for w in range(n) if graph[u][w]]
    disc = state['disc']
    fin = state['fin']
    parent = state['parent']
    order = state['order']
    counter = state['counter']

    if disc[v] is not None:
        # v already reachable: new edge is tree/forward/back relative to
        # the old order, so the forest remains a valid DFS forest.
        return _state_fields(state)

    # v unreachable: it and everything reachable from v become reachable.
    # Re-search from v, continuing the numbering after the old counter.
    parent[v] = u
    disc[v] = counter
    counter += 1
    order, counter = _dfs_from(v, adj, n, parent, disc, fin, order, counter)
    return _state_fields(state)


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    adj = state['adj']
    adj[u] = [w for w in range(n) if graph[u][w]]
    disc = state['disc']
    fin = state['fin']
    parent = state['parent']
    order = state['order']
    counter = state['counter']

    if parent[v] != u:
        # deleted edge was not a tree edge: forest unchanged.
        return _state_fields(state)

    # v was a tree child of u: the subtree rooted at v is cut.
    # Find v's position in the discovery order; the subtree is the maximal
    # contiguous block starting at v (DFS property).
    pos = order.index(v)
    end = pos
    while end + 1 < len(order):
        w = order[end + 1]
        if disc[w] > disc[v] and fin[w] < fin[v]:
            end += 1
        else:
            break
    subtree = order[pos:end + 1]

    # Save u's parent before clearing (u is in the prefix, so its parent
    # is also in the prefix or u is the root).
    u_parent = parent[u]

    # Clear the subtree.
    for w in subtree:
        parent[w] = None
        disc[w] = None
        fin[w] = None

    # Re-search from the cut point: continue DFS from u (revisiting its
    # remaining children) and then from any earlier vertex whose subtree
    # was cut off.  The prefix of the old order up to just before v keeps
    # its old numbers; everything from v onward is renumbered.
    #
    # The re-search must start from u (to pick up u's remaining children
    # and any later siblings of v) and from any vertex in the prefix whose
    # subtree contained v (i.e., u's ancestors) -- but those ancestors'
    # subtrees are not cut, only v's subtree is.  So we only need to
    # re-search from u, treating the prefix as already visited.
    #
    # However, u's already-finished descendants (before v in the order)
    # must keep their old numbers.  We therefore re-run DFS from u with
    # the prefix treated as already visited, and renumber everything from
    # u onward.  u's parent is unchanged (it is not in the reset set).
    #
    # Implementation: reset numbering from u's position.  The prefix
    # [0, pos_u) keeps its old numbers.  We re-search starting at u.
    pos_u = order.index(u)
    prefix = order[:pos_u]
    # Reset everything from u onward (u itself, the subtree, and the tail).
    for w in order[pos_u:]:
        parent[w] = None
        disc[w] = None
        fin[w] = None
    # Renumber: prefix keeps old disc/fin; counter resumes after the
    # prefix's last finish time.
    counter = max((fin[w] for w in prefix), default=0)
    # Restore u's parent.
    parent[u] = u_parent
    # Re-search from u, treating prefix vertices as already visited.
    disc[u] = counter
    counter += 1
    order = list(prefix)  # start fresh order with prefix
    order, counter = _dfs_from(u, adj, n, parent, disc, fin, order, counter)
    return _state_fields(state)
