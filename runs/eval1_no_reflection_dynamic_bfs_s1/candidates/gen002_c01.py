"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       list of sets of out-neighbors (kept in sync with the matrix)
  inadj:     list of sets of in-neighbors
  n:         number of vertices

Correctness strategy:
  - insert: if the new edge can shorten some reachable vertex, run a
    "shortening BFS" restricted to vertices whose distance can actually
    decrease (standard dynamic-BFS trick); otherwise do nothing.
  - delete: if the deleted edge is not the BFS parent edge of its head,
    nothing changes. Otherwise the subtree rooted at the head may lose its
    BFS parent; we recompute distances/parents for exactly the affected
    vertices (the old subtree plus any vertices that can now be reached
    shorter via other in-neighbors), using a BFS seeded from the boundary.
"""

from collections import deque


def _bfs_full(adj, n):
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    inadj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                inadj[v].add(u)
    parent, dist = _bfs_full(adj, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'inadj': inadj,
        'n': n,
    }


def _sync(state, graph, edge, added):
    """Keep adj/inadj consistent with the matrix after one flip."""
    u, v = edge
    adj = state['adj']
    inadj = state['inadj']
    if added:
        adj[u].add(v)
        inadj[v].add(u)
    else:
        adj[u].discard(v)
        inadj[v].discard(u)


def insert_edge(graph, edge, state):
    u, v = edge
    _sync(state, graph, edge, True)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    inadj = state['inadj']
    n = state['n']

    # Only useful if u is reachable and the edge can shorten v.
    if dist[u] == -1 or dist[v] != -1 and dist[u] + 1 >= dist[v]:
        return state

    # Shortening BFS: process vertices whose distance decreases.
    # A vertex w can be re-parented to a neighbor x with dist[x]+1 < dist[w].
    # We propagate: when w's distance drops, its out-neighbors may drop too.
    #
    # Correctness argument: when w's distance drops to dw, every out-neighbor
    # y with old dist[y] > dw+1 gets dist dw+1 (a valid BFS distance, since
    # no shorter path to y can exist: any path through a vertex whose
    # distance did not drop has length >= old dist[y] > dw+1, and any path
    # through a vertex whose distance did drop has length >= dw+1 by the
    # same argument inductively).  Vertices with old dist[y] <= dw+1 keep
    # their distance: they already had a path of that length, and no
    # shorter path can appear because every in-neighbor x of y satisfies
    # new dist[x] >= old dist[x] - 1 >= old dist[y] - 1 >= dw, so
    # new dist[x] + 1 >= dw + 1 >= old dist[y].
    q = deque()
    dist[v] = dist[u] + 1
    parent[v] = u
    q.append(v)

    while q:
        w = q.popleft()
        dw = dist[w]
        for y in adj[w]:
            if dist[y] == -1:
                dist[y] = dw + 1
                parent[y] = w
                q.append(y)
            elif dist[y] > dw + 1:
                dist[y] = dw + 1
                parent[y] = w
                q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    _sync(state, graph, edge, False)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    inadj = state['inadj']
    n = state['n']

    # If v was not a child of u in the BFS tree, the tree is untouched.
    if parent[v] != u:
        return state

    # v (and possibly its subtree) lost its BFS parent.
    # Collect the affected set: v plus all descendants in the BFS tree.
    #
    # Key invariant: for any vertex y NOT in the affected set, its distance
    # is unchanged.  Proof: any path from the root to y either avoids the
    # affected set entirely (length >= old dist[y], and old dist[y] is
    # still achievable via the old parent chain, which stays intact since
    # y's parent is not in affected by induction on the chain) or enters
    # the affected set at some vertex w; but w's new distance is at least
    # old dist[w] (it only loses its parent edge, never gains one), so the
    # path is no shorter than the old one.  Hence only affected vertices
    # need updating, and their new distances are computed by a BFS seeded
    # from the boundary (in-neighbors outside affected, whose distances
    # are final).
    children = [set() for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].add(x)

    affected = set()
    stack = [v]
    while stack:
        w = stack.pop()
        if w in affected:
            continue
        affected.add(w)
        stack.extend(children[w])

    # If v is the root, the whole reachable set is affected; recompute.
    if v == 0:
        parent, dist = _bfs_full(adj, n)
        state['parent'] = parent
        state['distances'] = dist
        return state

    # For each affected vertex, find the best alternative parent:
    # an in-neighbor x (not in affected, or in affected with a settled
    # smaller distance) with dist[x] + 1 minimal.
    # We process in increasing distance order: a vertex's new distance is
    # 1 + min(dist[x] for x in inadj[w] with x not in affected) if any,
    # else it may be reached via another affected vertex that itself got
    # a new parent. So do a Dijkstra-like BFS over affected vertices.

    INF = float('inf')
    newdist = {}
    newparent = {}
    # Seed: for each affected w, look at in-neighbors outside affected.
    q = deque()
    for w in affected:
        best = INF
        bp = None
        for x in inadj[w]:
            if x in affected:
                continue
            if dist[x] != -1 and dist[x] + 1 < best:
                best = dist[x] + 1
                bp = x
        if best < INF:
            newdist[w] = best
            newparent[w] = bp
            q.append(w)

    # Propagate within affected set (edges between affected vertices).
    while q:
        w = q.popleft()
        dw = newdist[w]
        for y in adj[w]:
            if y not in affected:
                continue
            cand = dw + 1
            if cand < newdist.get(y, INF):
                newdist[y] = cand
                newparent[y] = w
                q.append(y)

    # Apply: vertices in affected with no new distance become unreachable.
    for w in affected:
        if w in newdist:
            dist[w] = newdist[w]
            parent[w] = newparent[w]
        else:
            dist[w] = -1
            parent[w] = None

    return state
