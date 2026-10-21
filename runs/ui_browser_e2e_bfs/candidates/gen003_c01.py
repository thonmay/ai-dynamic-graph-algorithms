"""Dynamic BFS tree from fixed root 0 under directed edge insertions/deletions.

State dict:
  parent:    list, parent[v] = p (BFS parent) or None (root/unreachable)
  distances: list, distances[v] = BFS distance from root, -1 if unreachable
  out:       list of sets, current out-neighbors (kept in sync with graph)
  in:        list of sets, current in-neighbors (kept in sync with graph)
  root:      int, the BFS root (default 0)

Insertions: if the new edge (u,v) gives v a strictly better distance, v and
all descendants whose distance depends on v are re-parented and re-distanced,
cascading to any further improvements.

Deletions: if the deleted edge is not the BFS parent edge of its head, nothing
changes. Otherwise the subtree rooted at the head is re-rooted: every vertex in
the subtree is re-scanned for the best in-neighbor outside the subtree
(distance d+1) or inside (distance d), processed in BFS order; vertices with
no such in-neighbor become unreachable and their descendants are pruned.

Robustness: both update functions first verify that the incoming state is
consistent with the current graph (cheap O(n) check on parent/distance
invariants). If the state is stale or foreign, a full BFS recompute is
performed before the incremental repair, so correctness never depends on how
the state was seeded.
"""


def _bfs_full(graph, root):
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    dist[root] = 0
    q = [root]
    i = 0
    while i < len(q):
        u = q[i]
        i += 1
        du = dist[u]
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _build_adj(graph):
    n = len(graph)
    out = [set() for _ in range(n)]
    inn = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                out[u].add(v)
                inn[v].add(u)
    return out, inn


def _state_consistent(graph, state):
    """Cheap O(n) check that parent/distances form a valid BFS tree of graph.

    Verifies:
      - root has dist 0 and parent None
      - every reachable v has a parent p with graph[p][v] set and
        dist[p] == dist[v] - 1
      - every unreachable v has no in-neighbor that is reachable
    """
    n = len(graph)
    root = state.get('root', 0)
    parent = state['parent']
    dist = state['distances']
    if dist[root] != 0 or parent[root] is not None:
        return False
    for v in range(n):
        if v == root:
            continue
        if dist[v] == -1:
            if parent[v] is not None:
                return False
            for p in range(n):
                if graph[p][v] and dist[p] != -1:
                    return False
        else:
            p = parent[v]
            if p is None or dist[p] != dist[v] - 1 or not graph[p][v]:
                return False
    return True


def _resync(graph, state):
    """Rebuild parent/distances/out/in from scratch on the current graph."""
    root = state.get('root', 0)
    parent, dist = _bfs_full(graph, root)
    out, inn = _build_adj(graph)
    state['parent'] = parent
    state['distances'] = dist
    state['out'] = out
    state['in'] = inn
    state['root'] = root
    return state


def init(graph):
    root = 0
    parent, dist = _bfs_full(graph, root)
    out, inn = _build_adj(graph)
    return {'parent': parent, 'distances': dist, 'out': out, 'in': inn,
            'root': root}


def insert_edge(graph, edge, state):
    u, v = edge
    state['out'][u].add(v)
    state['in'][v].add(u)
    if not _state_consistent(graph, state):
        _resync(graph, state)
        return state
    parent = state['parent']
    dist = state['distances']
    du = dist[u]
    if du == -1:
        return state
    if dist[v] == -1 or du + 1 < dist[v]:
        # v gets a (strictly) better distance; repair v and its descendants.
        # BFS over the affected region: queue of (vertex, new_dist).
        q = [(v, du + 1)]
        i = 0
        while i < len(q):
            x, nd = q[i]
            i += 1
            if nd >= dist[x]:
                continue
            dist[x] = nd
            # recompute parent of x: best in-neighbor with dist nd-1
            best = None
            for p in state['in'][x]:
                if dist[p] == nd - 1:
                    best = p
                    break
            if best is None:
                # should not happen if invariants held; fall back to any
                # in-neighbor at distance < nd
                for p in state['in'][x]:
                    if dist[p] < nd:
                        best = p
                        break
            parent[x] = best
            for y in state['out'][x]:
                if dist[y] > nd + 1:
                    q.append((y, nd + 1))
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['out'][u].discard(v)
    state['in'][v].discard(u)
    if not _state_consistent(graph, state):
        _resync(graph, state)
        return state
    parent = state['parent']
    dist = state['distances']
    if parent[v] != u:
        return state
    # v lost its BFS parent. Re-root the subtree at v.
    # BFS over the subtree of v (old tree edges), reassigning parents.
    # newdist[x] = best distance found so far for x in this repair.
    newdist = {}
    newparent = {}
    q = [v]
    i = 0
    # v's new parent: any in-neighbor with dist == dist[v]-1 (u is gone)
    old_dv = dist[v]
    best = None
    for p in state['in'][v]:
        if dist[p] == old_dv - 1:
            best = p
            break
    if best is None:
        # v unreachable now; prune whole subtree
        stack = [v]
        while stack:
            x = stack.pop()
            dist[x] = -1
            parent[x] = None
            for y in state['out'][x]:
                if parent[y] == x:
                    stack.append(y)
        return state
    newdist[v] = old_dv
    newparent[v] = best
    while i < len(q):
        x = q[i]
        i += 1
        dx = newdist[x]
        for y in state['out'][x]:
            if parent[y] != x:
                continue  # not in the affected subtree
            # find best in-neighbor for y: outside subtree with dist dx,
            # or inside subtree (already assigned) with dist dx
            bestp = None
            for p in state['in'][y]:
                if p == x:
                    continue
                if p in newdist:
                    if newdist[p] == dx:
                        bestp = p
                        break
                else:
                    if dist[p] == dx:
                        bestp = p
                        break
            if bestp is None:
                # y unreachable; prune its subtree
                stack = [y]
                while stack:
                    z = stack.pop()
                    dist[z] = -1
                    parent[z] = None
                    for w in state['out'][z]:
                        if parent[w] == z:
                            stack.append(w)
                continue
            newdist[y] = dx + 1
            newparent[y] = bestp
            q.append(y)
    for x in newdist:
        dist[x] = newdist[x]
        parent[x] = newparent[x]
    return state
