"""Dynamic BFS tree maintenance from a fixed root (vertex 0).

State dict keys:
  parent:    list, parent[v] = BFS parent of v (None for root / unreachable)
  distances: list, distances[v] = BFS distance from root (-1 if unreachable)
  adj:       list of sets, current out-neighborhoods (kept in sync with graph)

Correctness strategy:
  - insert_edge: if the new edge can improve a vertex's distance, run a
    bounded BFS from that vertex restricted to vertices with dist >= d+1
    (standard dynamic BFS insertion). Otherwise no change.
  - delete_edge: if the deleted edge is not the tree edge of its head, no
    change. Otherwise the subtree rooted at the head may be invalid; we
    recompute BFS restricted to the affected region (the subtree plus any
    vertices whose distance could change), which is far smaller than the
    whole graph in typical cases.
"""

from collections import deque


def _bfs_full(graph, n):
    """Plain BFS from root 0. Returns (parent, distances)."""
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
    return [set(i for i in range(n) if graph[u][i]) for u in range(n)]


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph, n)
    adj = _build_adj(graph, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']

    if dist[u] == -1:
        return state
    if dist[v] != -1 and dist[v] <= dist[u] + 1:
        return state

    # v can be improved to dist[u] + 1; propagate.
    new_d = dist[u] + 1
    dist[v] = new_d
    parent[v] = u
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


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    n = len(parent)

    if parent[v] != u:
        # not a tree edge; distances unchanged
        return state

    # v lost its tree parent. Collect the subtree rooted at v.
    children = [[] for _ in range(n)]
    for x in range(1, n):
        p = parent[x]
        if p is not None:
            children[p].append(x)

    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        for c in children[x]:
            stack.append(c)
    subtree_set = set(subtree)

    # Mark all subtree vertices as tentatively unreachable.
    for x in subtree:
        parent[x] = None
        dist[x] = -1

    # For each x in subtree, find the minimum dist[w] over in-neighbors w
    # outside the subtree (w still reachable). This gives a candidate
    # distance for x.
    candidate = {x: -1 for x in subtree}
    for w in range(n):
        if w in subtree_set or dist[w] == -1:
            continue
        for x in adj[w]:
            if x in subtree_set:
                nd = dist[w] + 1
                if candidate[x] == -1 or nd < candidate[x]:
                    candidate[x] = nd

    # BFS within subtree using candidate distances.
    q = deque()
    for x in subtree:
        if candidate[x] != -1:
            dist[x] = candidate[x]
            # find the in-neighbor w outside subtree with dist[w] == candidate[x]-1
            for w in range(n):
                if w not in subtree_set and dist[w] == candidate[x] - 1 and x in adj[w]:
                    parent[x] = w
                    break
            q.append(x)

    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if y in subtree_set and (dist[y] == -1 or dist[y] > dx + 1):
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)

    # Fix up parents of non-subtree vertices that pointed into the subtree
    # (their old parent is now unreachable or at a different distance).
    for x in range(n):
        if x in subtree_set or x == 0:
            continue
        p = parent[x]
        if p is None:
            continue
        if p in subtree_set:
            # old parent is in the (now possibly unreachable) subtree;
            # find a new parent: an in-neighbor w with dist[w] == dist[x] - 1
            found = False
            for w in range(n):
                if dist[w] == dist[x] - 1 and x in adj[w]:
                    parent[x] = w
                    found = True
                    break
            if not found:
                # x is unreachable (shouldn't happen if x was reachable
                # before and its old parent was the only issue, but handle
                # gracefully)
                parent[x] = None
                dist[x] = -1
    return state
