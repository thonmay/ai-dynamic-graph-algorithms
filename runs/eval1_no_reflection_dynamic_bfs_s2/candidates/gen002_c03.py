"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] or None (root / unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync)
  radj:      list of sets, current in-neighborhoods (kept in sync)

Insert: if the new edge (u,v) can shorten v (dist[u]+1 < dist[v]), run a
localized BFS from v over edges that strictly decrease distance.  On an
insertion no distance can increase, so every vertex reached gets its true
new distance.

Delete: if the deleted edge was not v's tree edge, nothing changes
(deletions never shorten distances).  Otherwise v's tree subtree may be
orphaned.  We recompute distances for exactly that subtree with a BFS that
reuses the old tree edges as shortcuts: a vertex whose old tree parent is
still a valid in-neighbor at the right distance keeps its old distance, so
the search is pruned.  This is exact: any path to a subtree vertex either
uses its old tree edge (shortcut applies) or enters the subtree through
some other edge, which the BFS explores normally.
"""


def _bfs_from(root, adj, n):
    INF = float('inf')
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
        'distances': [-1 if d == float('inf') else d for d in dist],
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


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    radj = state['radj']
    dist = state['distances']
    parent = state['parent']

    adj[u].add(v)
    radj[v].add(u)

    # Only useful if u is reachable and the edge strictly improves v.
    if dist[u] >= 0 and dist[u] + 1 < dist[v]:
        # Localized BFS: only relax edges that strictly decrease distance.
        # dist[u] is already optimal (u's distance cannot change on an
        # insertion), so every vertex reached here gets its true new distance.
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

    # BFS from the root over the current graph, but with a shortcut: a
    # vertex whose old tree parent is still a valid in-neighbor at the
    # right distance keeps its old distance (its old tree path is intact).
    # This is exact: any path to x either uses the old tree edge (then the
    # shortcut applies) or enters the subtree through some other edge,
    # which the BFS explores normally.
    INF = float('inf')
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
