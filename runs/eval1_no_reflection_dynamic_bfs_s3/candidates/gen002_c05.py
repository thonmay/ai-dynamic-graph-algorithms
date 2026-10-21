"""Dynamic BFS tree maintenance (directed graph, fixed root 0).

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  adj:       list of sets, current out-neighborhoods
  in_adj:    list of sets, current in-neighborhoods

Insertions: if the new edge (u,v) can shorten v (or make it reachable),
run a bounded BFS from v: only vertices whose distance can strictly
improve are touched, and the search stops at the old distance of v.

Deletions: if the deleted edge is not the tree edge of its head, nothing
changes. Otherwise the head's subtree may be orphaned; recompute BFS
distances restricted to the orphaned subtree, using the already-correct
distances of the rest of the graph as boundary conditions.
"""

from collections import deque


def _bfs_full(graph):
    n = len(graph)
    dist = [-1] * n
    parent = [None] * n
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


def _build_adj(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    in_adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                in_adj[v].add(u)
    return adj, in_adj


def init(graph):
    parent, dist = _bfs_full(graph)
    adj, in_adj = _build_adj(graph)
    return {'parent': parent, 'distances': dist, 'adj': adj, 'in_adj': in_adj}


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['in_adj'][v].add(u)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    in_adj = state['in_adj']

    du = dist[u]
    if du == -1:
        return state  # u unreachable: edge cannot help anyone

    if dist[v] == -1:
        # v becomes reachable at du+1; re-root its (empty) subtree
        dist[v] = du + 1
        parent[v] = u
        return state

    if du + 1 < dist[v]:
        # v's distance improves. Propagate the improvement with a bounded
        # BFS: only vertices whose old distance is <= old_d(v) can improve
        # (any vertex at old distance d > old_d(v) has an in-neighbor at
        # old distance d-1 >= old_d(v), which is unaffected, so its
        # distance stays d). For each improved vertex, pick the best
        # in-neighbor under the current (partially updated) distances.
        old_dv = dist[v]
        dist[v] = du + 1
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in adj[x]:
                if dist[y] == -1 or (dist[y] <= old_dv and dx + 1 < dist[y]):
                    # y can improve; find its best in-neighbor.
                    best = x
                    best_d = dx + 1
                    for w in in_adj[y]:
                        dw = dist[w]
                        if dw != -1 and dw + 1 < best_d:
                            best_d = dw + 1
                            best = w
                    dist[y] = best_d
                    parent[y] = best
                    q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['in_adj'][v].discard(u)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    in_adj = state['in_adj']

    if parent[v] != u:
        return state  # not a tree edge: distances unchanged

    # v (and possibly its subtree) is orphaned. Collect the subtree of v
    # in the old tree.
    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        for y in adj[x]:
            if parent[y] == x:
                stack.append(y)

    # Mark subtree vertices as unknown.
    for x in subtree:
        dist[x] = -1
        parent[x] = None

    # Re-BFS restricted to the subtree, seeded by in-edges from outside
    # the subtree (whose distances are already final).
    in_sub = set(subtree)
    q = deque()
    for x in subtree:
        for w in in_adj[x]:
            if w not in in_sub and dist[w] != -1:
                # candidate seed
                if dist[x] == -1 or dist[w] + 1 < dist[x]:
                    dist[x] = dist[w] + 1
                    parent[x] = w
        if dist[x] != -1:
            q.append(x)

    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if y in in_sub and (dist[y] == -1 or dx + 1 < dist[y]):
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)

    return state
