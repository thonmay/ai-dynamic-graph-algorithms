"""Dynamic BFS tree from fixed root 0 under directed edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync with graph)
  rad:       list, radius[v] = max distance of any vertex in v's BFS subtree
  children:  list of sets, tree children
  n:         number of vertices

Insertion of (u,v): if dist[u]+1 < dist[v], the subtree of v is cut and
re-discovered by a BFS seeded at v's new level; vertices that end up with a
parent outside the subtree are re-rooted there, and a second pass propagates
the improved parents downward.  Radius values are then fixed by a bounded
propagation (radii only decrease on insertions).

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
    adj[u].add(v)
    parent = state['parent']
    dist = state['distances']
    children = state['children']

    if dist[u] == -1:
        return state
    newd = dist[u] + 1
    if dist[v] != -1 and newd >= dist[v]:
        return state
    # v gets a shorter distance: cut the subtree of v and re-discover it.
    # The whole subtree drops by the same delta, but descendants may also
    # change parent (to a vertex at their new level that was previously too
    # far), so re-run a BFS seeded at v's new level over the subtree.
    oldp = parent[v]
    if oldp is not None:
        children[oldp].discard(v)
    parent[v] = u
    children[u].add(v)
    dist[v] = newd
    # collect the subtree (tree edges still valid as a set of vertices)
    subtree = []
    q = deque([v])
    while q:
        x = q.popleft()
        subtree.append(x)
        for c in children[x]:
            q.append(c)
    in_sub = set(subtree)
    # reset the subtree (except v, already set)
    for x in subtree:
        if x != v:
            parent[x] = None
            dist[x] = -1
            children[x].clear()
    # BFS from v over the subtree; edges to outside the subtree are ignored
    # because outside vertices keep their (unchanged) distances and cannot
    # become parents of a subtree vertex at a smaller distance.
    q = deque([v])
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if y in in_sub and dist[y] == -1:
                dist[y] = dx + 1
                parent[y] = x
                children[x].add(y)
                q.append(y)
            elif y not in in_sub and dist[y] != -1 and dist[y] + 1 < dist[x]:
                # x's parent can be improved to y (y is at the new level of x
                # minus one); re-parent x and continue the BFS from x
                oldpx = parent[x]
                if oldpx is not None:
                    children[oldpx].discard(x)
                parent[x] = y
                children[y].add(x)
                dist[x] = dist[y] + 1
                q.append(x)
    # second pass: vertices whose parent changed may now offer better parents
    # to their subtree children (the first pass only improved parents of
    # vertices discovered in that pass)
    q = deque(x for x in subtree if x != v and parent[x] not in in_sub)
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if y in in_sub and dist[y] != -1 and dx + 1 < dist[y]:
                oldpy = parent[y]
                if oldpy is not None:
                    children[oldpy].discard(y)
                parent[y] = x
                children[x].add(y)
                dist[y] = dx + 1
                q.append(y)
    _fix_radii_after_insert(state, set(subtree))
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
