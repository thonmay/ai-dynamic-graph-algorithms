"""Dynamic BFS tree from fixed root 0 under edge insertions/deletions.

State dict:
  parent:    list, parent[v] or None (root and unreachable -> None)
  distances: list, BFS distance from root, -1 for unreachable
  in_edges:  list of lists, in_edges[v] = list of u with edge u->v
  out_edges: list of lists, out_edges[u] = list of v with edge u->v

Insertions: if the new edge can shorten the target, recompute distances for
the affected subtree (vertices whose distance may decrease) and re-parent.
Deletions: if the deleted edge was not the parent edge, nothing changes.
Otherwise the subtree rooted at the child loses its tree edge; we try to
re-parent each affected vertex from a non-tree in-neighbor at the right
distance. If some vertices cannot be re-parented they become unreachable
and we prune their descendants.
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
    Returns (new_parent, new_dist, pruned)."""
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
            # v becomes unreachable; prune v and all affected descendants
            pruned.add(v)
            for w in desc_map.get(v, ()):
                pruned.add(w)
            new_parent[v] = None
            new_dist[v] = -1
            for w in desc_map.get(v, ()):
                new_parent[w] = None
                new_dist[w] = -1
        else:
            new_parent[v] = best_p
            new_dist[v] = best_d

    return new_parent, new_dist, pruned


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
    if dist[u] >= 0 and dist[u] + 1 < dist[v]:
        # v's distance decreases; re-parent v and all descendants.
        affected = _subtree(parent, v)
        # Set v's new parent and distance.
        parent[v] = u
        dist[v] = dist[u] + 1
        # For each descendant w of v (in original tree), recompute its
        # distance using in-neighbors. Process in increasing old-distance
        # order (valid since new distances <= old distances).
        affected_list = sorted(affected, key=lambda w: state['distances'][w])
        for w in affected_list:
            if w == v:
                continue
            best_d = None
            best_p = None
            for u2 in in_edges[w]:
                if dist[u2] < 0:
                    continue
                d = dist[u2] + 1
                if best_d is None or d < best_d:
                    best_d = d
                    best_p = u2
            if best_p is not None:
                parent[w] = best_p
                dist[w] = best_d
            # else: keep old parent/dist (tree edge still exists)

    return {
        'parent': parent,
        'distances': dist,
        'in_edges': in_edges,
        'out_edges': out_edges,
    }


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
        return {
            'parent': parent,
            'distances': dist,
            'in_edges': in_edges,
            'out_edges': out_edges,
        }

    # The parent edge of v was deleted. The subtree rooted at v is affected.
    affected = _subtree(parent, v)
    new_parent, new_dist, pruned = _reparent_subtree(
        parent, dist, in_edges, affected)

    return {
        'parent': new_parent,
        'distances': new_dist,
        'in_edges': in_edges,
        'out_edges': out_edges,
    }
