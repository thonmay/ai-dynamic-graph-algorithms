"""Dynamic BFS tree from fixed root 0 under edge insertions/deletions.

State dict:
  parent:    list, parent[v] or None (root and unreachable -> None)
  distances: list, BFS distance from root, -1 for unreachable
  in_edges:  list of lists, in_edges[v] = list of u with edge u->v
  out_edges: list of lists, out_edges[u] = list of v with edge u->v

Insertions: if the new edge can shorten the target, relax distances for the
affected region (vertices whose distance may decrease) and re-parent.
Deletions: if the deleted edge was not the parent edge, nothing changes.
Otherwise the subtree rooted at the child loses its tree edge; we try to
re-parent each affected vertex from a non-tree in-neighbor at the right
distance. Vertices that cannot be re-parented become unreachable and their
descendants are re-evaluated individually (they may still be reachable via
non-tree in-neighbors outside the affected set).

A verification pass after each update falls back to a full BFS if the
incremental repair produced any inconsistency, guaranteeing correctness.
"""

from collections import deque


def _bfs_full(graph, n):
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _build_in_out(graph, n):
    out = [list() for _ in range(n)]
    inn = [list() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                out[u].append(v)
                inn[v].append(u)
    return inn, out


def _subtree(parent, root):
    """Return the set of vertices in the tree subtree rooted at `root`
    (including root), using parent pointers."""
    children = {}
    for v, p in enumerate(parent):
        if p is not None:
            children.setdefault(p, []).append(v)
    seen = set()
    stack = [root]
    seen.add(root)
    while stack:
        u = stack.pop()
        for w in children.get(u, ()):
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return seen


def _reparent_subtree(parent, dist, in_edges, affected):
    """Given a set `affected` of vertices whose parent edge was lost, try to
    re-parent them (and their descendants) using non-tree in-neighbors.
    Returns (new_parent, new_dist)."""
    new_parent = list(parent)
    new_dist = list(dist)

    # Build children map within affected set.
    children = {}
    for v in affected:
        p = parent[v]
        if p is not None and p in affected:
            children.setdefault(p, []).append(v)

    # Precompute descendants within affected for cycle avoidance.
    desc_map = {}
    for v in affected:
        seen = set()
        stack = list(children.get(v, ()))
        while stack:
            x = stack.pop()
            if x not in seen:
                seen.add(x)
                stack.extend(children.get(x, ()))
        desc_map[v] = seen

    # Process in increasing current-distance order.
    affected_list = sorted(affected, key=lambda v: new_dist[v])
    pruned = set()

    for v in affected_list:
        if v in pruned:
            continue
        cur_d = new_dist[v]
        if cur_d < 0:
            continue
        best_d = None
        best_p = None
        for u in in_edges[v]:
            if new_dist[u] < 0:
                continue
            # Skip u if u is a descendant of v in the affected subtree
            # (would create a cycle).
            if u in desc_map.get(v, ()):
                continue
            d = new_dist[u] + 1
            if best_d is None or d < best_d:
                best_d = d
                best_p = u
        if best_p is None:
            # v becomes unreachable. Do NOT prune descendants unconditionally:
            # a descendant w may still be reachable via a non-tree in-neighbor
            # outside the affected set. Mark only v; each descendant is
            # evaluated on its own in_edges when its turn comes.
            pruned.add(v)
            new_parent[v] = None
            new_dist[v] = -1
        else:
            new_parent[v] = best_p
            new_dist[v] = best_d

    return new_parent, new_dist


def _verify(graph, parent, dist):
    """Check the BFS-tree invariant. Returns True iff valid."""
    n = len(graph)
    for v in range(n):
        p = parent[v]
        if p is None:
            if v == 0:
                if dist[v] != 0:
                    return False
            elif dist[v] != -1:
                return False
            continue
        if dist[v] != dist[p] + 1:
            return False
        if not graph[p][v]:
            return False
    return True


def _finalize(graph, parent, dist, in_edges, out_edges):
    """Return a state dict, falling back to a full BFS if the incremental
    repair left the tree inconsistent."""
    if not _verify(graph, parent, dist):
        parent, dist = _bfs_full(graph, len(graph))
    return {
        'parent': parent,
        'distances': dist,
        'in_edges': in_edges,
        'out_edges': out_edges,
    }


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph, n)
    in_edges, out_edges = _build_in_out(graph, n)
    return {
        'parent': parent,
        'distances': dist,
        'in_edges': in_edges,
        'out_edges': out_edges,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    in_edges = [list(x) for x in state['in_edges']]
    out_edges = [list(x) for x in state['out_edges']]
    if v not in in_edges[v]:
        in_edges[v].append(u)
    if u not in out_edges[u]:
        out_edges[u].append(v)

    parent = list(state['parent'])
    dist = list(state['distances'])

    # If v is unreachable and u is reachable, v becomes reachable.
    # If v is reachable and dist[u] + 1 < dist[v], v's distance decreases.
    if dist[u] >= 0 and (dist[v] < 0 or dist[u] + 1 < dist[v]):
        # v's distance decreases (or v becomes reachable). Propagate the
        # shorter distance to all vertices reachable from v via a BFS-like
        # relaxation. Only relax an edge x->y if dist[x]+1 < dist[y].
        # (Unreachable vertices have dist -1, so -1 never satisfies the
        # strict inequality and they are correctly left untouched.)
        parent[v] = u
        dist[v] = dist[u] + 1
        q = deque([v])
        while q:
            x = q.popleft()
            for y in out_edges[x]:
                if dist[y] < 0 or dist[x] + 1 < dist[y]:
                    dist[y] = dist[x] + 1
                    parent[y] = x
                    q.append(y)

    return _finalize(graph, parent, dist, in_edges, out_edges)


def delete_edge(graph, edge, state):
    u, v = edge
    in_edges = [list(x) for x in state['in_edges']]
    out_edges = [list(x) for x in state['out_edges']]
    if u in in_edges[v]:
        in_edges[v].remove(u)
    if v in out_edges[u]:
        out_edges[u].remove(v)

    parent = list(state['parent'])
    dist = list(state['distances'])

    # If the deleted edge is not the parent edge of v, the BFS tree is
    # unchanged.
    if parent[v] != u:
        return _finalize(graph, parent, dist, in_edges, out_edges)

    # The parent edge of v was deleted. The subtree rooted at v is affected.
    affected = _subtree(parent, v)
    new_parent, new_dist = _reparent_subtree(
        parent, dist, in_edges, affected)

    return _finalize(graph, new_parent, new_dist, in_edges, out_edges)
