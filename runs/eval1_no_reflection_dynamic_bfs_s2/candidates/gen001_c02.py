"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync with graph)
  in_adj:    list of sets, current in-neighborhoods
"""

from collections import deque


def _bfs(n, adj):
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
    n = len(graph)
    adj, in_adj = _build_adj(graph)
    parent, dist = _bfs(n, adj)
    return {'parent': parent, 'distances': dist, 'adj': adj, 'in_adj': in_adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']
    n = len(graph)

    if v in adj[u]:
        return state

    adj[u].add(v)
    in_adj[v].add(u)

    du = dist[u]
    if du == -1:
        # u unreachable, edge cannot help
        return state

    if dist[v] == -1:
        # v becomes reachable at distance du+1
        dist[v] = du + 1
        parent[v] = u
        # BFS from v to fix descendants that may now be closer
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in adj[x]:
                if dist[y] == -1:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)
                elif dist[y] > dx + 1:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)
        return state

    if dist[v] > du + 1:
        # v and possibly its subtree get closer
        dist[v] = du + 1
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in adj[x]:
                if dist[y] > dx + 1:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)
        return state

    # dist[v] <= du+1: no change needed
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']
    n = len(graph)

    if v not in adj[u]:
        return state

    adj[u].discard(v)
    in_adj[v].discard(u)

    if parent[v] != u:
        # deleted edge was not a tree edge; distances unchanged
        return state

    # v lost its tree parent. Find the best alternative in-neighbor.
    best = -1
    best_d = -1
    for w in in_adj[v]:
        dw = dist[w]
        if dw != -1 and (best_d == -1 or dw < best_d):
            best_d = dw
            best = w

    if best != -1:
        # v stays at distance best_d+1 (which equals old dist[v])
        parent[v] = best
        return state

    # v and possibly its subtree become unreachable or need re-parenting.
    # Collect the affected subtree (vertices whose parent chain goes through v).
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)

    affected = []
    stack = [v]
    while stack:
        x = stack.pop()
        affected.append(x)
        for c in children[x]:
            stack.append(c)

    affected_set = set(affected)

    # For each affected vertex, find the best in-neighbor outside the
    # affected set with known distance.
    INF = float('inf')
    new_dist = {}
    new_parent = {}
    for x in affected:
        best_w = -1
        best_d = INF
        for w in in_adj[x]:
            if w in affected_set:
                continue
            dw = dist[w]
            if dw != -1 and dw < best_d:
                best_d = dw
                best_w = w
        if best_w != -1:
            new_dist[x] = best_d + 1
            new_parent[x] = best_w

    # Propagate within affected set (BFS by distance)
    q = deque()
    for x in affected:
        if x in new_dist:
            q.append(x)
    while q:
        x = q.popleft()
        dx = new_dist[x]
        for y in adj[x]:
            if y not in affected_set:
                continue
            nd = dx + 1
            if y not in new_dist or nd < new_dist[y]:
                new_dist[y] = nd
                new_parent[y] = x
                q.append(y)

    # Apply
    for x in affected:
        if x in new_dist:
            dist[x] = new_dist[x]
            parent[x] = new_parent[x]
        else:
            dist[x] = -1
            parent[x] = None

    return state
