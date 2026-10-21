"""Dynamic BFS tree from fixed root 0 under edge insertions/deletions.

State dict:
  parent:    list, parent[v] or None
  distances: list, dist from root, -1 if unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync)
  inadj:     list of sets, current in-neighborhoods (kept in sync)

Insertion: if the new edge (u,v) can shorten v (dist[u]+1 < dist[v]),
recompute BFS from v's subtree (the vertices whose tree path goes through v),
which is the only region that can change.

Deletion: if the deleted edge is not the tree edge of v, nothing changes.
Otherwise v's subtree may be orphaned; run a bounded BFS from the subtree
boundary (vertices at depth d = dist[v]) to find new parents at depth d,
reparenting the subtree.  If any vertex cannot be reached, fall back to a
full BFS (rare, and only when reachability actually changed).
"""

from collections import deque


def _full_bfs(adj, n):
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        for w in adj[u]:
            if dist[w] == -1:
                dist[w] = du + 1
                parent[w] = u
                q.append(w)
    return parent, dist


def _sync(graph):
    """Rebuild adj/inadj from the matrix (used only in init)."""
    n = len(graph)
    adj = [set() for _ in range(n)]
    inadj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                inadj[v].add(u)
    return adj, inadj


def init(graph):
    # `graph` is the matrix AFTER the first update.  The initial graph is
    # unknown, so we cannot know which entry was flipped.  We therefore
    # treat `graph` as the current graph and compute the BFS tree from it.
    n = len(graph)
    adj, inadj = _sync(graph)
    parent, dist = _full_bfs(adj, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'inadj': inadj,
    }


def _subtree_of(state, v):
    """Vertices whose tree path goes through v (including v)."""
    parent = state['parent']
    n = len(parent)
    children = [[] for _ in range(n)]
    for w in range(n):
        p = parent[w]
        if p is not None:
            children[p].append(w)
    out = []
    stack = [v]
    while stack:
        u = stack.pop()
        out.append(u)
        stack.extend(children[u])
    return out


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['inadj'][v].add(u)
    dist = state['distances']
    parent = state['parent']
    if dist[u] != -1 and dist[u] + 1 < dist[v]:
        # v (and possibly its subtree) can be shortened; recompute from v.
        sub = _subtree_of(state, v)
        # detach subtree
        for w in sub:
            parent[w] = None
            dist[w] = -1
        # BFS from v using current graph, but only allowing vertices in sub
        # to be (re)assigned; v gets its new parent u.
        dist[v] = dist[u] + 1
        parent[v] = u
        subset = set(sub)
        q = deque([v])
        while q:
            x = q.popleft()
            for y in state['adj'][x]:
                if y in subset and dist[y] == -1:
                    dist[y] = dist[x] + 1
                    parent[y] = x
                    q.append(y)
        # any vertex in sub still -1 is unreachable (shouldn't happen since
        # the old tree edges are still present), but be safe:
        for w in sub:
            if dist[w] == -1:
                # fall back to full recompute
                p2, d2 = _full_bfs(state['adj'], len(parent))
                state['parent'] = p2
                state['distances'] = d2
                break
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['inadj'][v].discard(u)
    parent = state['parent']
    dist = state['distances']
    if parent[v] != u:
        return state
    # v's tree edge was deleted; v's subtree may be orphaned.
    sub = _subtree_of(state, v)
    subset = set(sub)
    d = dist[v]
    # detach
    for w in sub:
        parent[w] = None
        dist[w] = -1
    # try to find new parents at depth d for vertices in sub, BFS outward
    # from the boundary: any vertex in sub with an in-neighbor at depth d
    # (outside sub, or v itself via another in-neighbor) can be reattached.
    # We do a BFS over sub in tree order, but parents must come from
    # inadj at depth d.  Standard approach: process sub vertices in
    # increasing old depth; a vertex w can be reattached if it has an
    # in-neighbor x with dist[x] == d (x outside sub) -- then dist[w] = d+1
    # and its children may follow.  But children need depth d+1 parents,
    # which are the reattached vertices themselves.  So: BFS where the
    # frontier starts at sub vertices having an external in-neighbor at
    # depth d.
    q = deque()
    for w in sub:
        for x in state['inadj'][w]:
            if x not in subset and dist[x] == d:
                dist[w] = d + 1
                parent[w] = x
                q.append(w)
                break
    while q:
        x = q.popleft()
        for y in state['adj'][x]:
            if y in subset and dist[y] == -1:
                dist[y] = dist[x] + 1
                parent[y] = x
                q.append(y)
    for w in sub:
        if dist[w] == -1:
            # reachability changed; full recompute
            p2, d2 = _full_bfs(state['adj'], len(parent))
            state['parent'] = p2
            state['distances'] = d2
            break
    return state
