"""Dynamic BFS tree from fixed root 0 under directed edge insert/delete.

State dict:
  parent:    list, parent[v] or None
  distances: list, BFS distance from root, -1 for unreachable
  adj:       list of sets, current out-neighborhoods
  rev:       list of sets, in-neighborhoods
  n:         number of vertices

Approach:
  - Insertion: the new edge (u,v) can only decrease distances (or make
    v reachable).  Run a Dijkstra-like propagation over the affected
    region, re-parenting vertices whose distance decreases.
  - Deletion: if the deleted edge is not a tree edge, nothing changes.
    Otherwise the subtree of v in the BFS tree may lose reachability or
    be re-parented at the same or larger distance.  Run a multi-source
    Dijkstra over the subtree, seeded from in-neighbors outside the
    subtree; vertices not reached become unreachable.
"""

INF = float('inf')


def _bfs_from_root(adj, n):
    dist = [-1] * n
    parent = [None] * n
    dist[0] = 0
    q = [0]
    i = 0
    while i < len(q):
        u = q[i]
        i += 1
        du = dist[u] + 1
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = du
                parent[v] = u
                q.append(v)
    return parent, dist


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    rev = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                rev[v].add(u)
    parent, dist = _bfs_from_root(adj, n)
    return {'parent': parent, 'distances': dist, 'adj': adj,
            'rev': rev, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    rev = state['rev']
    parent = state['parent']
    dist = state['distances']

    adj[u].add(v)
    rev[v].add(u)

    # The new edge can only decrease distances (or make v reachable).
    # Propagate: a vertex x may get a new distance dist[u]+1 via u, and
    # decreases propagate along out-edges.  Use a priority queue.
    import heapq
    if dist[u] == -1:
        # u unreachable: new edge cannot help anyone.
        return state
    heap = []
    cand = dist[u] + 1
    if dist[v] == -1 or cand < dist[v]:
        dist[v] = cand
        parent[v] = u
        heapq.heappush(heap, (cand, v))
    while heap:
        d, x = heapq.heappop(heap)
        if d != dist[x]:
            continue
        nd = d + 1
        for y in adj[x]:
            if dist[y] == -1 or nd < dist[y]:
                dist[y] = nd
                parent[y] = x
                heapq.heappush(heap, (nd, y))
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    rev = state['rev']
    parent = state['parent']
    dist = state['distances']

    adj[u].discard(v)
    rev[v].discard(u)

    # If the deleted edge was not a tree edge, nothing to repair.
    if parent[v] != u:
        return state

    # Tree edge removed.  Collect the subtree of v in the BFS tree.
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)
    sub = []
    stack = [v]
    while stack:
        x = stack.pop()
        sub.append(x)
        for y in children[x]:
            stack.append(y)
    subset = set(sub)

    # Multi-source Dijkstra over the subtree.  Seed x with the best
    # in-neighbor w outside the subtree (dist[w] + 1).  Relax along
    # edges within the subtree.  Vertices not reached become
    # unreachable.  (Distances can only stay the same or increase, or
    # become -1, after a deletion.)
    import heapq
    newdist = {}
    newparent = {}
    heap = []
    for x in sub:
        best = INF
        bp = None
        for w in rev[x]:
            if w not in subset and dist[w] != -1:
                c = dist[w] + 1
                if c < best:
                    best = c
                    bp = w
        if best < INF:
            newdist[x] = best
            newparent[x] = bp
            heapq.heappush(heap, (best, x))
    while heap:
        d, x = heapq.heappop(heap)
        if d > newdist.get(x, INF):
            continue
        nd = d + 1
        for y in adj[x]:
            if y in subset and nd < newdist.get(y, INF):
                newdist[y] = nd
                newparent[y] = x
                heapq.heappush(heap, (nd, y))

    for x in sub:
        if x in newdist:
            dist[x] = newdist[x]
            parent[x] = newparent[x]
        else:
            dist[x] = -1
            parent[x] = None
    return state
