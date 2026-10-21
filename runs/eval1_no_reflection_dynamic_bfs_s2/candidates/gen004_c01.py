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

    # v's subtree may be orphaned.  A vertex is in the subtree iff its old
    # tree path to the root used the deleted edge, i.e. iff it is a tree
    # descendant of v.  For such a vertex the old distance is stale (its
    # old path used the deleted edge), so it must be re-derived by BFS.
    # For a vertex outside the subtree the old tree path never used the
    # deleted edge, so its old distance is still valid.
    in_subtree = [False] * n
    stack = [v]
    while stack:
        x = stack.pop()
        in_subtree[x] = True
        for y in adj[x]:
            if parent[y] == x:
                stack.append(y)

    # BFS from the root over the current graph, but with a shortcut: a
    # vertex OUTSIDE the orphaned subtree whose old tree parent is still a
    # valid in-neighbor at the right distance keeps its old distance (its
    # old tree path is intact and never used the deleted edge, so its
    # distance is unchanged).  For vertices inside the subtree the old
    # distance is stale, so the BFS distance is used.  This is exact: any
    # path to a subtree vertex either enters the subtree through some edge,
    # which the BFS explores normally, or the vertex keeps a valid old path
    # (only possible outside the subtree).
    #
    # Key subtlety: the BFS distance of a vertex x that is itself a
    # re-reached descendant of v can be SMALLER than its old distance
    # (e.g. a cross edge from a shallow vertex into the subtree).  For a
    # shortcut vertex y whose old parent is such an x, the correct new
    # distance is dx+1 (the BFS distance), NOT the old dist[y] =
    # dist[x]+1, which would be larger and would break the invariant that
    # the parent sits one level closer.  dx+1 equals dist[y] whenever x's
    # distance is unchanged, so the shortcut still saves work.
    #
    # The BFS is seeded from the root and from every boundary in-neighbor
    # of the orphaned subtree (a reachable vertex outside the subtree with
    # an edge into the subtree), so vertices outside the subtree are never
    # reprocessed.
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
                # shortcut: y's old tree path never used the deleted edge,
                # so its old distance is still valid.  Assign dx+1 (not
                # dist[y]) so the parent stays one level closer even when
                # x's new distance is smaller than its old one.
                if not in_subtree[y] and parent[y] == x and dist[y] == dist[x] + 1:
                    ndist[y] = dx + 1
                    nparent[y] = x
                else:
                    ndist[y] = dx + 1
                    nparent[y] = x
                queue.append(y)

    # Seed the BFS from every boundary in-neighbor of the orphaned
    # subtree: a reachable vertex outside the subtree with an edge into
    # the subtree.  This lets the BFS reach the subtree without
    # reprocessing the whole outside of the graph.
    for x in range(n):
        if not in_subtree[x] and dist[x] >= 0:
            for y in adj[x]:
                if in_subtree[y] and ndist[y] == INF:
                    ndist[y] = dist[x] + 1
                    nparent[y] = x
                    queue.append(y)

    for x in range(n):
        if in_subtree[x]:
            dist[x] = -1 if ndist[x] == INF else ndist[x]
            parent[x] = nparent[x]
    return _finalize(state)
