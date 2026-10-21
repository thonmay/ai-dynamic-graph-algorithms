"""Dynamic BFS tree from fixed root 0 under directed edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync with graph)
  rad:       list, radius[v] = max distance of any vertex in v's BFS subtree
  children:  list of sets, tree children
  n:         number of vertices

Insertion of (u,v): if dist[u]+1 < dist[v], re-parent v to u and update the
distances of v's whole subtree (they all drop by the same delta, so their
tree edges remain valid).  Radius values of the affected vertices are then
fixed by a bounded propagation (radii only decrease on insertions).

Deletion of (u,v): if the edge is not v's tree edge, nothing changes.
Otherwise the subtree of v is cut off; a BFS seeded with all still-reachable
vertices re-discovers the cut region, and radii of the affected vertices are
recomputed exactly and propagated to ancestors.
"""

from collections import deque


def _bfs_full(graph, n):
    dist = [-1] * n
    parent = [None] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        row = graph[u]
        for v in range(n):
            if row[v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _build_state(parent, dist, n):
    children = [set() for _ in range(n)]
    for v in range(n):
        if parent[v] is not None:
            children[parent[v]].add(v)
    rad = [0] * n
    for v in range(n):
        if dist[v] != -1:
            rad[v] = dist[v]
    order = sorted((v for v in range(n) if dist[v] != -1),
                   key=lambda x: dist[x], reverse=True)
    for v in order:
        for c in children[v]:
            if rad[c] > rad[v]:
                rad[v] = rad[c]
    return {'parent': parent, 'distances': dist, 'rad': rad,
            'children': children, 'n': n}


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph, n)
    state = _build_state(parent, dist, n)
    state['adj'] = [set(j for j in range(n) if graph[i][j]) for i in range(n)]
    return state


def _fix_radii_after_insert(state, changed):
    """changed: set of vertices whose distance/parent changed (their rad may
    have decreased).  Propagate decreases upward until stable."""
    rad = state['rad']
    children = state['children']
    dist = state['distances']
    parent = state['parent']
    q = deque(changed)
    seen = set(changed)
    while q:
        v = q.popleft()
        r = dist[v]
        for c in children[v]:
            if rad[c] > r:
                r = rad[c]
        if r != rad[v]:
            rad[v] = r
            p = parent[v]
            if p is not None and p not in seen:
                seen.add(p)
                q.append(p)


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    was_new = v not in adj[u]
    adj[u].add(v)
    parent = state['parent']
    dist = state['distances']
    children = state['children']

    if not was_new or dist[u] == -1:
        return state
    newd = dist[u] + 1
    if dist[v] != -1 and newd >= dist[v]:
        return state
    # v gets a shorter distance (or becomes reachable): re-parent v to u
    oldp = parent[v]
    if oldp is not None:
        children[oldp].discard(v)
    parent[v] = u
    children[u].add(v)
    dist[v] = newd
    changed = {v}
    if oldp is not None:
        # every descendant of v keeps its tree edge; its distance drops by the
        # same delta, so just update the stored distances
        q = deque([v])
        while q:
            x = q.popleft()
            for c in children[x]:
                dist[c] = dist[x] + 1
                changed.add(c)
                q.append(c)
    else:
        # v was unreachable: its old tree children set is empty, so run a real
        # BFS from v over adj to discover newly-reachable vertices
        q = deque([v])
        while q:
            x = q.popleft()
            for y in adj[x]:
                if dist[y] == -1:
                    dist[y] = dist[x] + 1
                    parent[y] = x
                    children[x].add(y)
                    changed.add(y)
                    q.append(y)
    _fix_radii_after_insert(state, changed)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].discard(v)
    parent = state['parent']
    dist = state['distances']
    children = state['children']

    if parent[v] != u:
        return state
    # tree edge deleted: subtree of v is cut off
    subtree = []
    q = deque([v])
    while q:
        x = q.popleft()
        subtree.append(x)
        for c in children[x]:
            q.append(c)
    in_sub = set(subtree)
    for x in subtree:
        parent[x] = None
        dist[x] = -1
        children[x].clear()
    children[u].discard(v)

    # BFS seeded with all still-reachable vertices; only cut vertices get
    # (re)assigned.  Non-cut vertices keep their (unchanged) distances.
    q = deque(w for w in range(n) if w not in in_sub and dist[w] != -1)
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if y in in_sub and dist[y] == -1:
                dist[y] = dx + 1
                parent[y] = x
                children[x].add(y)
                q.append(y)

    # recompute radii for affected vertices and propagate to ancestors
    rad = state['rad']
    affected = set()
    for x in subtree:
        if dist[x] != -1:
            affected.add(x)
            p = parent[x]
            if p is not None:
                affected.add(p)
    order = sorted(affected, key=lambda x: dist[x], reverse=True)
    for x in order:
        r = dist[x]
        for c in children[x]:
            if rad[c] > r:
                r = rad[c]
        rad[x] = r
    # propagate radius changes upward
    q2 = deque()
    seen = set(affected)
    for x in affected:
        p = parent[x]
        if p is not None and p not in seen:
            seen.add(p)
            q2.append(p)
    while q2:
        x = q2.popleft()
        r = dist[x]
        for c in children[x]:
            if rad[c] > r:
                r = rad[c]
        if r != rad[x]:
            rad[x] = r
            p = parent[x]
            if p is not None and p not in seen:
                seen.add(p)
                q2.append(p)
    return state
