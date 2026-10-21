"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

State dict:
  parent:  list, parent[v] or None (root / unreachable)
  disc:    list, discovery time (None if unreachable)
  fin:     list, finish time (None if unreachable)
  order:   list of reachable vertices in discovery order
  counter: next discovery time
  adj:     list of sorted adjacency lists (kept in sync with the matrix)

Correctness invariant: (parent, disc, fin) is a valid DFS search of the
current graph from root 0, produced by one shared counter.  We maintain it
by re-running the search only over the affected "candidate interval"
(Yang et al. style):

- Insert u->v: if v is already reachable, the forest stays valid (a new
  edge can only be a tree/forward/back edge relative to the old order).
  If v is unreachable, v and everything reachable from v become reachable;
  we re-open u's DFS frame and re-search from u, so the new vertices are
  numbered inside u's (and its ancestors') intervals.
- Delete u->v: if v is not a tree child of u, nothing changes.  Otherwise
  the subtree rooted at v is cut; we re-open u's DFS frame and re-search
  from u, keeping the prefix of the old order up to just before u with its
  old numbers and renumbering the rest.  Vertices that were reachable only
  through the deleted edge become unreachable.

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


def _re_search_from(u, adj, n, parent, disc, fin, order):
    """Re-open u's DFS frame and re-search from u.

    The prefix of `order` before u keeps its old discovery/finish numbers
    (those intervals are fully closed and unaffected).  Everything from u
    onward is cleared and renumbered, so u's (and its ancestors') finish
    times are recomputed to enclose the renumbered descendants.  Returns
    (order, counter)."""
    pos_u = order.index(u)
    prefix = order[:pos_u]
    u_parent = parent[u]
    # Reset everything from u onward (u itself, its descendants, the tail).
    for w in order[pos_u:]:
        parent[w] = None
        disc[w] = None
        fin[w] = None
    # Renumber: prefix keeps old disc/fin; counter resumes after the
    # prefix's last finish time.
    counter = max((fin[w] for w in prefix), default=0)
    # Restore u's parent and re-search from u, treating prefix vertices
    # as already visited.
    parent[u] = u_parent
    disc[u] = counter
    counter += 1
    order = list(prefix)
    order, counter = _dfs_from(u, adj, n, parent, disc, fin, order, counter)
    return order, counter


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
        # v already reachable.  If disc[u] < disc[v] the new edge is a
        # tree/forward/back edge relative to the old order and the forest
        # stays valid.  If disc[u] > disc[v] the new edge is a
        # forward-cross edge (u discovered after v, v not a descendant of
        # u), which invalidates the forest: re-search from the root.
        if disc[u] is not None and disc[u] < disc[v]:
            return _state_fields(state)
        order, counter = _full_search(adj, n)
        state['parent'] = parent
        state['disc'] = disc
        state['fin'] = fin
        state['order'] = order
        state['counter'] = counter
        return _state_fields(state)

    # v unreachable: it and everything reachable from v become reachable.
    # Re-open u's DFS frame and re-search from u so the new vertices are
    # numbered inside u's interval (fin[u] must exceed fin[v]).
    if disc[u] is None:
        # u itself was unreachable: the whole reachable set changes, so
        # re-search from the root.
        order, counter = _full_search(adj, n)
        state['parent'] = parent
        state['disc'] = disc
        state['fin'] = fin
        state['order'] = order
        state['counter'] = counter
        return _state_fields(state)
    order, counter = _re_search_from(u, adj, n, parent, disc, fin, order)
    state['order'] = order
    state['counter'] = counter
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

    # v was a tree child of u: the subtree rooted at v is cut.  Re-open
    # u's DFS frame and re-search from u: the prefix before u keeps its
    # old numbers, u and everything after it is renumbered, and u's
    # ancestors' finish times are recomputed to enclose the new subtree.
    # Vertices reachable only through the deleted edge become unreachable.
    order, counter = _re_search_from(u, adj, n, parent, disc, fin, order)
    state['order'] = order
    state['counter'] = counter
    return _state_fields(state)
