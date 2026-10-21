"""Dynamic BFS tree from fixed root 0 under edge insertions/deletions.

State dict:
  'parent':    list, parent[v] or None (root and unreachable -> None)
  'distances': list, BFS distance from root, -1 for unreachable
  'adj':       list of sets, current out-neighborhoods (kept in sync)

Insertion of (u,v):
  - if u unreachable: no effect.
  - if v unreachable: the affected set is the set of vertices reachable
    from v whose distance can improve (dist > dist[u]+1 or unreachable).
    We recompute that set from its boundary.
  - if dist[u]+1 < dist[v]: v's tree subtree can improve; recompute it
    from its boundary.
  - otherwise: no effect.

Deletion of (u,v):
  - only matters if (u,v) is the tree edge of v; then v's subtree may be
    disconnected.  Recompute the subtree from its boundary; vertices not
    reached become unreachable.

Both procedures are local: work is proportional to the affected subtree
plus its boundary, not the whole graph.  Correctness argument: within the
affected set S, every vertex's new distance is min over in-edges (x,y)
with y in S of dist[x]+1 where x is outside S (fixed) or in S (recomputed
by BFS); vertices outside S keep valid distances because no distance can
worsen on insertion and only S's vertices lose their tree edge on
deletion.
"""

from collections import deque


def _bfs_full(graph):
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        row = graph[u]
        for v in range(n):
            if row[v] and dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _build_state(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
    }


def init(graph):
    return _build_state(graph)


def _subtree_of(state, v):
    """Set of vertices in v's tree subtree (including v)."""
    parent = state['parent']
    n = len(parent)
    sub = set()
    stack = [v]
    while stack:
        x = stack.pop()
        if x in sub:
            continue
        sub.add(x)
        for y in range(n):
            if parent[y] == x:
                stack.append(y)
    return sub


def _recompute_subtree(state, sub, boundary):
    """Recompute distances/parents for vertices in `sub`.

    boundary: iterable of (u, v) edges with u outside sub, v in sub,
    candidate in-edges (u must be reachable).  BFS from boundary targets
    using only edges into sub.  Vertices in sub not reached become
    unreachable.
    """
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']

    for x in sub:
        parent[x] = None
        dist[x] = -1

    q = deque()
    for u, v in boundary:
        if dist[v] == -1:
            dist[v] = dist[u] + 1
            parent[v] = u
            q.append(v)

    while q:
        u = q.popleft()
        for v in adj[u]:
            if v in sub and dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return state


def _boundary(state, sub):
    """All edges (src, x) with src outside sub, src reachable, x in sub."""
    dist = state['distances']
    adj = state['adj']
    n = len(dist)
    boundary = []
    for src in range(n):
        if src in sub or dist[src] == -1:
            continue
        for x in adj[src]:
            if x in sub:
                boundary.append((src, x))
    return boundary


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(state['parent'])
    state['adj'][u].add(v)
    dist = state['distances']
    parent = state['parent']

    if dist[u] == -1:
        return state

    if dist[v] == -1:
        # v becomes reachable; affected set = vertices reachable from v
        # whose distance can improve (dist > dist[u]+1 or unreachable).
        # Over-approximation: BFS from v through vertices with
        # dist == -1 or dist > dist[u]+1.  (A vertex with dist <=
        # dist[u]+1 cannot improve, and neither can anything reached
        # through it at a distance >= its own, so cutting there is safe.)
        limit = dist[u] + 1
        sub = set()
        q = deque([v])
        sub.add(v)
        while q:
            x = q.popleft()
            for y in state['adj'][x]:
                if y not in sub and (dist[y] == -1 or dist[y] > limit):
                    sub.add(y)
                    q.append(y)
        boundary = _boundary(state, sub)
        if u not in sub:
            boundary.append((u, v))
        _recompute_subtree(state, sub, boundary)
        return state

    if dist[u] + 1 < dist[v]:
        # v's distance improves to dist[u]+1; every vertex in v's tree
        # subtree may improve by the same amount.  Recompute the subtree
        # from its boundary (which includes the new edge (u,v) if u is
        # outside the subtree).
        sub = _subtree_of(state, v)
        boundary = _boundary(state, sub)
        if u not in sub:
            boundary.append((u, v))
        _recompute_subtree(state, sub, boundary)
        return state

    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    dist = state['distances']
    parent = state['parent']

    if dist[u] == -1:
        return state
    if parent[v] != u:
        # not the tree edge; v keeps a valid parent, and deletions never
        # improve distances, so nothing changes.
        return state

    sub = _subtree_of(state, v)
    boundary = _boundary(state, sub)
    _recompute_subtree(state, sub, boundary)
    return state
