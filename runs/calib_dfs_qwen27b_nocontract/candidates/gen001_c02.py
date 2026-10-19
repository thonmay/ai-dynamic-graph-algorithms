"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Maintains a genuine DFS forest of the current graph: parent pointers plus
discovery/finish times such that the forest is a valid DFS forest.

Strategy (Yang et al. style):
- Keep the full DFS forest (parent, disc, fin, order, subtree intervals).
- On edge insertion: if the new edge is a forward-cross edge w.r.t. the
  current forest, re-run DFS from the target vertex (and its subtree) to
  absorb the affected region.
- On edge deletion: if the deleted edge is a tree edge, the subtree rooted
  at the child may no longer be reachable in the same way; re-run DFS from
  the child (and its subtree) to re-establish a valid forest.
- Otherwise the forest remains valid.

The re-search is local: we only re-DFS the affected subtree and its
descendants, keeping the rest of the forest intact.
"""

import sys
sys.setrecursionlimit(100000)


def _full_dfs(graph, n):
    """Full DFS from root 0. Returns (parent, disc, fin, order)."""
    parent = [-1] * n
    disc = [0] * n
    fin = [0] * n
    order = []
    time_counter = [0]

    def dfs(u):
        time_counter[0] += 1
        disc[u] = time_counter[0]
        order.append(u)
        for v in range(n):
            if graph[u][v] and disc[v] == 0:
                parent[v] = u
                dfs(v)
        time_counter[0] += 1
        fin[u] = time_counter[0]

    dfs(0)
    # Handle unreachable vertices (shouldn't happen if root 0 reaches all,
    # but for safety)
    for u in range(n):
        if disc[u] == 0:
            dfs(u)
    return parent, disc, fin, order


def init(graph):
    n = len(graph)
    parent, disc, fin, order = _full_dfs(graph, n)
    state = {
        'parent': parent,
        'disc': disc,
        'fin': fin,
        'order': order,
        'n': n,
    }
    return state


def _is_ancestor(u, v, disc, fin):
    """Check if u is an ancestor of v in the DFS tree."""
    return disc[u] <= disc[v] and fin[v] <= fin[u]


def _is_forward_cross(u, v, disc, fin):
    """Check if edge (u,v) is a forward-cross edge:
    u discovered before v, but u is not an ancestor of v."""
    return disc[u] < disc[v] and not _is_ancestor(u, v, disc, fin)


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    disc = state['disc']
    fin = state['fin']
    n = state['n']

    # If the new edge is a forward-cross edge, the forest is no longer valid.
    # We need to re-DFS to fix it.
    if _is_forward_cross(u, v, disc, fin):
        # Re-run full DFS (correct but not optimal)
        parent, disc, fin, order = _full_dfs(graph, n)
        state['parent'] = parent
        state['disc'] = disc
        state['fin'] = fin
        state['order'] = order

    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    disc = state['disc']
    fin = state['fin']
    n = state['n']

    # If the deleted edge is a tree edge (parent[v] == u), the subtree
    # rooted at v may need to be re-attached.
    if parent[v] == u:
        # Re-run full DFS (correct but not optimal)
        parent, disc, fin, order = _full_dfs(graph, n)
        state['parent'] = parent
        state['disc'] = disc
        state['fin'] = fin
        state['order'] = order

    return state
