"""Dynamic BFS tree from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance or -1 (unreachable)
  in_edges:  list of sets, in_edges[v] = set of in-neighbors of v

Insertion: if the new edge (u,v) improves v's distance (dist[u]+1 < dist[v]),
propagate the improvement to v's descendants via a BFS over the tree.
Deletion: if the deleted edge was v's parent, recompute v's distance from its
other in-neighbors; if unreachable, detach the subtree and reattach it via
other in-neighbors.
"""

from collections import deque


def _bfs(graph, root):
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    dist[root] = 0
    q = deque([root])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _in_edges(graph):
    n = len(graph)
    ie = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                ie[v].add(u)
    return ie


def init(graph):
    parent, dist = _bfs(graph, 0)
    return {
        'parent': parent,
        'distances': dist,
        'in_edges': _in_edges(graph),
    }


def insert_edge(graph, edge, state):
    u, v = edge
    state['in_edges'][v].add(u)
    parent = state['parent']
    dist = state['distances']
    if dist[u] == -1:
        return state
    if dist[v] == -1 or dist[u] + 1 < dist[v]:
        # v becomes reachable or gets a shorter distance; attach it to u and
        # propagate to its descendants.
        dist[v] = dist[u] + 1
        parent[v] = u
        q = deque()
        for w in range(len(graph)):
            if parent[w] == v:
                q.append(w)
        while q:
            x = q.popleft()
            for y in range(len(graph)):
                if parent[y] == x:
                    dist[y] = dist[x] + 1
                    q.append(y)
    # The new edge may also make previously unreachable vertices reachable
    # (e.g. v was unreachable but has an outgoing edge to an unreachable w).
    # BFS from v over the current graph, restricted to unreachable vertices.
    if dist[v] != -1:
        q = deque([v])
        while q:
            x = q.popleft()
            for y in range(len(graph)):
                if graph[x][y] and dist[y] == -1:
                    dist[y] = dist[x] + 1
                    parent[y] = x
                    q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['in_edges'][v].discard(u)
    parent = state['parent']
    dist = state['distances']
    if parent[v] != u:
        return state
    # v lost its parent; find a new one among remaining in-neighbors.
    n = len(graph)
    # Mark v's subtree in the current tree: any in-neighbor of v that lies in
    # this subtree is not a valid new parent (its reachability goes through v),
    # and picking it would create a parent cycle.
    subtree = set()
    q = deque()
    for x in range(n):
        if parent[x] == v:
            subtree.add(x)
            q.append(x)
    while q:
        x = q.popleft()
        for y in range(n):
            if parent[y] == x:
                subtree.add(y)
                q.append(y)
    best = -1
    for w in state['in_edges'][v]:
        if w not in subtree and dist[w] != -1 and (best == -1 or dist[w] < dist[best]):
            best = w
    if best != -1:
        dist[v] = dist[best] + 1
        parent[v] = best
        # v's distance may have increased; propagate to descendants.
        q = deque()
        for x in range(n):
            if parent[x] == v:
                q.append(x)
        while q:
            x = q.popleft()
            for y in range(n):
                if parent[y] == x:
                    dist[y] = dist[x] + 1
                    q.append(y)
    else:
        # v and its whole subtree lose their parent edge; detach, then try to
        # reattach each detached vertex to a still-reachable in-neighbor.
        detached = [v]
        q = deque([v])
        while q:
            x = q.popleft()
            for y in range(n):
                if parent[y] == x:
                    detached.append(y)
                    q.append(y)
        for x in detached:
            parent[x] = None
            dist[x] = -1
        # Reattach in increasing distance order (BFS order of the old tree).
        for x in detached:
            for w in state['in_edges'][x]:
                if dist[w] != -1:
                    parent[x] = w
                    dist[x] = dist[w] + 1
                    break
    return state
