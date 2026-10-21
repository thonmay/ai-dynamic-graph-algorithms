"""Dynamic BFS tree from fixed root 0 under edge insertions/deletions.

State dict:
  'parent':    list, parent[v] or None (root and unreachable -> None)
  'distances': list, BFS distance from root, -1 for unreachable
  'adj':       list of sets, current out-neighborhoods (kept in sync)
  'inadj':     list of sets, current in-neighborhoods (kept in sync)

Local update strategy:
  - Insertion of (u,v): only vertices whose distance can strictly improve
    are affected.  The affected set is the subtree of v (when
    dist[u]+1 < dist[v]) or the set of vertices reachable from v through
    vertices with dist > dist[u]+1 (when v was unreachable).  The set is
    recomputed by a multi-source BFS seeded from boundary in-edges.
  - Deletion of (u,v): only matters when (u,v) is v's tree edge; then v's
    subtree is recomputed from its boundary in-edges, and vertices not
    reached become unreachable.

Correctness: within the affected set S, every vertex's new distance is the
min over in-edges (x,y) with y in S of dist[x]+1 where x is outside S
(fixed, already optimal) or in S (recomputed by BFS).  Vertices outside S
keep valid distances: on insertion no distance worsens and no vertex
outside S can improve (any improving path would have to enter S through a
vertex whose distance is already <= the new candidate); on deletion only
S's vertices lose their tree edge.
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
    inadj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                inadj[v].add(u)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'inadj': inadj,
    }


def init(graph):
    return _build_state(graph)


def _subtree_of(state, v):
    """Set of vertices in v's tree subtree (including v)."""
    parent = state['parent']
    n = len(parent)
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)
    sub = set()
    stack = [v]
    while stack:
        x = stack.pop()
        sub.add(x)
        for c in children[x]:
            stack.append(c)
    return sub


def _recompute_subtree(state, sub, boundary):
    """Recompute distances/parents for vertices in `sub`.

    boundary: iterable of (u, v) edges with u outside sub, v in sub,
    candidate in-edges (u must be reachable).  Multi-source BFS seeded
    from boundary targets, then internal edges.  Vertices in sub not
    reached become unreachable.
    """
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']

    for x in sub:
        parent[x] = None
        dist[x] = -1

    q = deque()
    for u, v in boundary:
        cand = dist[u] + 1
        if dist[v] == -1 or cand < dist[v]:
            dist[v] = cand
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
    inadj = state['inadj']
    boundary = []
    for x in sub:
        for src in inadj[x]:
            if src not in sub and dist[src] != -1:
                boundary.append((src, x))
    return boundary


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['inadj'][v].add(u)
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
    state['inadj'][v].discard(u)
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
