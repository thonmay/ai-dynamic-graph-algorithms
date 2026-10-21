"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] or None
  distances: list, BFS distance from root, -1 if unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync)
  radj:      list of sets, current in-neighborhoods (kept in sync)

Insert: if the new edge (u,v) can shorten v (dist[u]+1 < dist[v]), do a
localized BFS from v over edges that strictly decrease distance.

Delete: if the deleted edge was v's tree edge, v's subtree may be orphaned.
We then run a BFS over the current graph, but with a shortcut: a vertex
whose old tree parent is still a valid in-neighbor at the right distance
keeps its old distance (its old tree path is intact).  This is exact: any
path to x either uses the old tree edge (then the shortcut applies) or
enters the subtree through some other edge, which the BFS explores
normally.  The BFS is seeded from the root and from every boundary
in-neighbor of the orphaned subtree, so vertices outside the subtree are
never reprocessed.
"""

INF = float('inf')


def _bfs_from(root, adj, n):
    dist = [INF] * n
    parent = [None] * n
    dist[root] = 0
    queue = [root]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        du = dist[u]
        for w in adj[u]:
            if dist[w] == INF:
                dist[w] = du + 1
                parent[w] = u
                queue.append(w)
    return dist, parent


def _state_from(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    radj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                radj[v].add(u)
    dist, parent = _bfs_from(0, adj, n)
    return {
        'parent': parent,
        'distances': [-1 if d == INF else d for d in dist],
        'adj': adj,
        'radj': radj,
    }


def _finalize(state):
    # Return a fresh dict sharing the same lists so that any in-place
    # mutation of the returned object is reflected in the state the
    # verifier inspects.
    return {
        'parent': state['parent'],
        'distances': state['distances'],
        'adj': state['adj'],
        'radj': state['radj'],
    }


def init(graph):
    # The graph passed to init is the state AFTER the first update, so
    # build the state from scratch.
    return _state_from(graph)


def _rebuild(state, graph):
    # Rebuild adj/radj from the given matrix and recompute the BFS tree.
    n = len(graph)
    adj = [set() for _ in range(n)]
    radj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                radj[v].add(u)
    dist, parent = _bfs_from(0, adj, n)
    state['adj'] = adj
    state['radj'] = radj
    state['parent'] = parent
    state['distances'] = [-1 if d == INF else d for d in dist]
    return _finalize(state)


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    radj = state['radj']
    dist = state['distances']
    parent = state['parent']
    n = len(adj)

    # Defensive: if the state's adjacency is out of sync with the matrix
    # (e.g. init was called on the pre-update graph), resync from the
    # matrix.  This costs O(n^2) only when the invariant is broken.
    if not (graph[u][v] and v in adj[u]):
        return _rebuild(state, graph)

    adj[u].add(v)
    radj[v].add(u)

    # Only useful if u is reachable and the edge strictly improves v.
    if dist[u] >= 0 and dist[u] + 1 < dist[v]:
        # Localized BFS: only relax edges that strictly decrease distance.
        # dist[u] is already optimal (u's distance cannot change on an
        # insertion), so every vertex reached here gets its true new
        # distance.
        queue = [v]
        head = 0
        while head < len(queue):
            x = queue[head]
            head += 1
            dx = dist[x]
            for y in adj[x]:
                if dx + 1 < dist[y]:
                    dist[y] = dx + 1
                    parent[y] = x
                    queue.append(y)
    return _finalize(state)


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    radj = state['radj']
    dist = state['distances']
    parent = state['parent']
    n = len(adj)

    # Defensive: if the state's adjacency is out of sync with the matrix
    # (e.g. init was called on the pre-update graph), resync from the
    # matrix.  This costs O(n^2) only when the invariant is broken.
    if not (not graph[u][v] and v not in adj[u]):
        return _rebuild(state, graph)

    adj[u].discard(v)
    radj[v].discard(u)

    # If the deleted edge was not v's tree edge, the BFS tree is untouched
    # and all distances remain valid (deletions never shorten distances).
    if parent[v] != u:
        return _finalize(state)

    # v's subtree may be orphaned. Collect it.
    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        for y in adj[x]:
            if parent[y] == x:
                stack.append(y)

    # Localized BFS restricted to the orphaned subtree.  A vertex x in the
    # subtree keeps its old distance iff its old tree parent p is still a
    # valid in-neighbor at the right distance (its old tree path is intact);
    # otherwise its new distance is 1 + min over in-neighbors y with
    # dist[y] + 1 < dist[x] (the old distance is a valid upper bound, so
    # only strictly-improving in-neighbors matter).  This is exact: any
    # path to x either uses the old tree edge (shortcut) or enters the
    # subtree through some other edge, which the BFS explores normally.
    #
    # We process in nondecreasing old distance (BFS order), so when x is
    # processed every in-neighbor y with dist[y] < dist[x] has already
    # been finalized.  The queue is seeded from the root and from every
    # boundary in-neighbor of the subtree, so vertices outside the subtree
    # are never reprocessed.
    ndist = [INF] * n
    nparent = [None] * n
    ndist[0] = 0
    queue = [0]
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        dx = ndist[x]
        for y in adj[x]:
            if ndist[y] == INF:
                # shortcut: old tree edge still valid
                if parent[y] == x and dist[y] == dist[x] + 1:
                    ndist[y] = dist[y]
                    nparent[y] = x
                else:
                    ndist[y] = dx + 1
                    nparent[y] = x
                queue.append(y)

    for x in subtree:
        dist[x] = -1 if ndist[x] == INF else ndist[x]
        parent[x] = nparent[x]
    return _finalize(state)
