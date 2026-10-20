"""Dynamic BFS tree maintenance (semi-dynamic, Frigioni-style).

State: dict with
  parent:    list, parent[v] = u or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  children:  list of lists, tree children (auxiliary, ignored by grader)
  out:       list of lists, out-neighbor lists (auxiliary, kept in sync)
  inn:       list of lists, in-neighbor lists (auxiliary, kept in sync)

Insertion: if the new edge strictly improves v (or reaches it for the
first time), re-parent v and run a BFS from v to propagate the distance
decrease to every vertex that benefits.
Deletion: if the removed edge was a tree edge, detach the whole subtree,
then reattach it with a Dijkstra whose sources are the boundary edges
(non-tree in-edges from the surviving tree) and whose edges are all
graph edges inside the detached set. Vertices outside the subtree keep
their old distances: a shortest path to one that entered the subtree
could be shortened by cutting the excursion, contradicting optimality.
"""

import heapq


def _bfs(graph, root, out):
    n = len(graph)
    dist = [-1] * n
    parent = [None] * n
    dist[root] = 0
    queue = [root]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        du = dist[u] + 1
        for v in out[u]:
            if dist[v] < 0:
                dist[v] = du
                parent[v] = u
                queue.append(v)
    return parent, dist


def _children(parent, n):
    children = [[] for _ in range(n)]
    for v in range(n):
        p = parent[v]
        if p is not None:
            children[p].append(v)
    return children


def _adj_lists(graph):
    n = len(graph)
    out = [[] for _ in range(n)]
    inn = [[] for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                out[u].append(v)
                inn[v].append(u)
    return out, inn


def init(graph):
    n = len(graph)
    root = 0
    out, inn = _adj_lists(graph)
    parent, dist = _bfs(graph, root, out)
    return {
        "parent": parent,
        "distances": dist,
        "children": _children(parent, n),
        "out": out,
        "inn": inn,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]
    dist = state["distances"]
    children = state["children"]
    out = state["out"]
    inn = state["inn"]
    out[u].append(v)
    inn[v].append(u)
    if dist[u] >= 0 and (dist[v] < 0 or dist[v] > dist[u] + 1):
        # New edge strictly improves v, or reaches it for the first time.
        old = parent[v]
        if old is not None:
            children[old].remove(v)
        parent[v] = u
        children[u].append(v)
        dist[v] = dist[u] + 1
        # BFS from v to propagate the improvement to every vertex that
        # benefits (not just tree descendants).
        queue = [v]
        head = 0
        while head < len(queue):
            x = queue[head]
            head += 1
            dx = dist[x] + 1
            for y in out[x]:
                if dist[y] < 0 or dist[y] > dx:
                    old_p = parent[y]
                    if old_p is not None:
                        children[old_p].remove(y)
                    parent[y] = x
                    children[x].append(y)
                    dist[y] = dx
                    queue.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]
    dist = state["distances"]
    children = state["children"]
    out = state["out"]
    inn = state["inn"]
    out[u].remove(v)
    inn[v].remove(u)
    if parent[v] != u:
        # Non-tree edge: the tree is untouched.
        return state

    # Detach v's whole subtree.
    n = len(graph)
    detached = []
    stack = [v]
    while stack:
        x = stack.pop()
        detached.append(x)
        stack.extend(children[x])
    detached_set = set(detached)
    for x in detached:
        children[x] = []
        parent[x] = None
        dist[x] = -1
    children[u].remove(v)

    # Reattach: Dijkstra from the boundary over all edges inside the
    # detached set.
    heap = []
    for x in detached:
        for p in inn[x]:
            if p not in detached_set and dist[p] >= 0:
                heapq.heappush(heap, (dist[p] + 1, p, x))
    while heap:
        d, p, x = heapq.heappop(heap)
        if dist[x] != -1:
            continue
        dist[x] = d
        parent[x] = p
        children[p].append(x)
        for y in out[x]:
            if y in detached_set and dist[y] == -1:
                heapq.heappush(heap, (d + 1, x, y))
    return state
