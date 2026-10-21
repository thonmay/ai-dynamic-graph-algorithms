"""Dynamic BFS tree from fixed root 0 under edge insertions/deletions.

State dict:
  'parent':    list, parent[v] or None (root and unreachable -> None)
  'distances': list, BFS distance from root, -1 for unreachable
  'adj':       list of sets, current out-neighborhoods (kept in sync)
  'inadj':     list of sets, current in-neighborhoods (kept in sync)

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
    candidate in-edges (u must be reachable).  BFS from boundary targets
    using only edges into sub.  Vertices in sub not reached become
    unreachable.
    """
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    inadj = state['inadj']

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
    # Second pass: a vertex reached via an internal edge may still have a
    # shorter path through a boundary edge discovered later, and a vertex
    # whose parent changed may now offer a shorter path to its in-subtree
    # children (including ones not yet reached).  Relax both directions
    # until stable; each improvement strictly decreases a distance, so
    # this terminates.
    changed = True
    while changed:
        changed = False
        for x in sub:
            if parent[x] is None:
                continue
            best = dist[parent[x]] + 1
            for src in inadj[x]:
                if src not in sub and dist[src] != -1:
                    cand = dist[src] + 1
                    if cand < best:
                        best = cand
                        parent[x] = src
            if best < dist[x]:
                dist[x] = best
                changed = True
            d = dist[x]
            for y in adj[x]:
                if y in sub and (dist[y] == -1 or d + 1 < dist[y]):
                    dist[y] = d + 1
                    parent[y] = x
                    changed = True
    # Third pass: a vertex whose parent changed to a boundary source may
    # now offer a shorter path to in-subtree vertices that were not yet
    # reached.  Propagate until stable.
    changed = True
    while changed:
        changed = False
        for x in sub:
            if parent[x] is None:
                continue
            d = dist[x]
            for y in adj[x]:
                if y in sub and dist[y] == -1:
                    dist[y] = d + 1
                    parent[y] = x
                    changed = True
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



