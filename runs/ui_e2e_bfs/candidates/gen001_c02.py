"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State: dict with
  'parent':    list, parent[v] = p or None (root/unreachable)
  'distances': list, BFS distance from root, -1 if unreachable
  'in':        list of sets, in-neighbors of each vertex (maintained)
  'out':       list of sets, out-neighbors of each vertex (maintained)

Insert: if the new edge can shorten some reachable vertex, run a bounded
BFS from the affected vertex (only vertices whose distance can improve).
Delete: if the deleted edge was the parent edge of its head, recompute the
distances of the affected subtree with a bounded BFS that only touches
vertices whose distance may have increased.
"""

from collections import deque


def _bfs_full(graph, n):
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _build_adj(graph, n):
    out = [set() for _ in range(n)]
    inn = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                out[u].add(v)
                inn[v].add(u)
    return inn, out


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph, n)
    inn, out = _build_adj(graph, n)
    return {'parent': parent, 'distances': dist, 'in': inn, 'out': out}


def insert_edge(graph, edge, state):
    u, v = edge
    state['out'][u].add(v)
    state['in'][v].add(u)
    parent = state['parent']
    dist = state['distances']
    n = len(dist)

    # Only useful if u is reachable and the edge can shorten v.
    if dist[u] == -1 or (dist[v] != -1 and dist[u] + 1 >= dist[v]):
        return state

    # v's distance improves to dist[u]+1; propagate the improvement.
    # Also, vertices that were unreachable may now become reachable.
    new_d = dist[u] + 1
    dist[v] = new_d
    parent[v] = u
    q = deque([v])
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in state['out'][x]:
            if dist[y] == -1 or dist[y] > dx + 1:
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['out'][u].discard(v)
    state['in'][v].discard(u)
    parent = state['parent']
    dist = state['distances']
    n = len(dist)

    # If the deleted edge was not v's parent edge, the BFS tree is intact.
    if parent[v] != u:
        return state

    # v (and possibly its subtree) may have lost its shortest path.
    # Recompute distances for the affected region: start from v, and any
    # vertex whose parent chain went through v. We do a bounded BFS:
    # collect the subtree of v in the current tree, then recompute their
    # distances using only edges from vertices whose distance is stable.
    subtree = []
    # children map: build on the fly by scanning parents of subtree members
    # is O(n) per member; instead do a BFS over the tree using a children
    # index rebuilt lazily. Simpler: mark subtree by walking from v using
    # a children list built once per delete (O(n)).
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)

    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        for c in children[x]:
            stack.append(c)

    # Vertices in the subtree may need new distances. Vertices outside are
    # unaffected (their parent chain does not go through v).
    # Recompute: for each subtree vertex, its new distance is 1 + min
    # distance of its in-neighbors, where in-neighbors outside the subtree
    # keep their old distance and in-neighbors inside the subtree are
    # recomputed. This is a shortest-path problem on the subgraph induced
    # by the subtree with boundary sources.
    in_sub = [False] * n
    for x in subtree:
        in_sub[x] = True

    # Dijkstra-like (all weights 1) BFS: initialize each subtree vertex with
    # 1 + min dist of its in-neighbors outside the subtree (or -1 if none),
    # then propagate within the subtree.
    ndist = {}
    q = deque()
    for x in subtree:
        best = None
        for p in state['in'][x]:
            if not in_sub[p]:
                d = dist[p]
                if d != -1 and (best is None or d + 1 < best):
                    best = d + 1
        if best is not None:
            ndist[x] = best
            q.append(x)

    while q:
        x = q.popleft()
        dx = ndist[x]
        for y in state['out'][x]:
            if in_sub[y]:
                cand = dx + 1
                if y not in ndist or cand < ndist[y]:
                    ndist[y] = cand
                    q.append(y)

    # Apply results: vertices not in ndist become unreachable.
    for x in subtree:
        if x in ndist:
            dist[x] = ndist[x]
        else:
            dist[x] = -1
            parent[x] = None

    # Rebuild parent pointers for the subtree: parent of x is an in-neighbor
    # p (outside or inside subtree) with dist[p] == dist[x] - 1.
    # Process in increasing distance order so that in-subtree parents are
    # already assigned when needed.
    for x in sorted(subtree, key=lambda z: dist[z] if dist[z] != -1 else 1 << 30):
        if dist[x] == -1:
            continue
        newp = None
        for p in state['in'][x]:
            if dist[p] == dist[x] - 1:
                newp = p
                break
        parent[x] = newp
    return state
