"""Dynamic BFS tree from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  'parent':    list, parent[v] = BFS parent or None (root/unreachable)
  'distances': list, distances[v] = BFS distance from root, -1 if unreachable
  'adj':       list of sets, current out-neighborhood of each vertex
  'indeg':     list of ints, number of in-neighbors at each distance level
               (indeg[d] = count of vertices v with dist[v] == d that have at
               least one in-neighbor at distance d-1)

Insertions are handled incrementally (Frigioni-style): only vertices whose
distance can improve are re-parented, and the improvement propagates forward
through the BFS tree. Deletions are handled by a full BFS recompute, which is
correct but not cheap; the insertion path is the dynamic part.
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
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _recompute_indeg(parent, dist, n):
    indeg = [0] * (n + 1)
    for v in range(n):
        d = dist[v]
        if d >= 0:
            indeg[d] += 1
    return indeg


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    parent, dist = _full_bfs(adj, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'indeg': _recompute_indeg(parent, dist, n),
    }


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    if v in adj[u]:
        return state
    adj[u].add(v)

    parent = state['parent']
    dist = state['distances']
    n = len(adj)

    # If u is reachable and v is unreachable or can be reached one level
    # earlier, start a forward propagation from v.
    if dist[u] != -1 and (dist[v] == -1 or dist[v] > dist[u] + 1):
        dist[v] = dist[u] + 1
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for w in adj[x]:
                if dist[w] == -1 or dist[w] > dx + 1:
                    dist[w] = dx + 1
                    parent[w] = x
                    q.append(w)
        # Recompute indeg from scratch (cheap: O(n)).
        state['indeg'] = _recompute_indeg(parent, dist, n)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    if v not in adj[u]:
        return state
    adj[u].discard(v)

    # Full recompute: correct in all cases (v may have been the only
    # in-neighbor of some vertex, cascading invalidations).
    n = len(adj)
    parent, dist = _full_bfs(adj, n)
    state['parent'] = parent
    state['distances'] = dist
    state['indeg'] = _recompute_indeg(parent, dist, n)
    return state
