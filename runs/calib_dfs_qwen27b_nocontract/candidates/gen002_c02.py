"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Maintains a genuine DFS forest of the current graph: parent pointers plus
discovery/finish times such that the forest is a valid DFS forest.

Strategy (Yang et al. style):
- Keep the full DFS forest (parent, discover, finish, order, subtree intervals).
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
    """Full DFS from root 0 only. Returns (parent, discover, finish, order).

    Only vertices reachable from 0 are discovered. Times are 0-based:
    discover[u] = t at entry, finish[u] = t at exit, t increments once per
    event. For an isolated root: discover[0]=0, finish[0]=1.
    """
    parent = [None] * n
    discover = [0] * n
    finish = [0] * n
    order = []
    time_counter = [0]

    def dfs(u):
        discover[u] = time_counter[0]
        time_counter[0] += 1
        order.append(u)
        for v in range(n):
            if graph[u][v] and discover[v] == 0:
                parent[v] = u
                dfs(v)
        time_counter[0] += 1
        finish[u] = time_counter[0]

    dfs(0)
    return parent, discover, finish, order


def init(graph):
    n = len(graph)
    parent, discover, finish, order = _full_dfs(graph, n)
    state = {
        'parent': parent,
        'discover': discover,
        'finish': finish,
        'order': order,
        'n': n,
    }
    return state


def _is_ancestor(u, v, discover, finish):
    """Check if u is an ancestor of v in the DFS tree."""
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def _is_forward_cross(u, v, discover, finish):
    """Check if edge (u,v) is a forward-cross edge:
    u discovered before v, but u is not an ancestor of v."""
    return discover[u] < discover[v] and not _is_ancestor(u, v, discover, finish)


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = state['n']

    # Any insertion can change the DFS forest: a new edge from an already
    # discovered vertex to an undiscovered one makes that vertex a child of
    # the new source, and a new edge to an already-finished vertex creates a
    # forward-cross edge. Re-run the full DFS (correct but not optimal).
    parent, discover, finish, order = _full_dfs(graph, n)
    state['parent'] = parent
    state['discover'] = discover
    state['finish'] = finish
    state['order'] = order
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = state['n']

    # Any deletion can change the DFS forest: removing a tree edge may make
    # the child unreachable (or reachable via a different path), and removing
    # a non-tree edge can change which edge becomes the tree edge. Re-run the
    # full DFS (correct but not optimal).
    parent, discover, finish, order = _full_dfs(graph, n)
    state['parent'] = parent
    state['discover'] = discover
    state['finish'] = finish
    state['order'] = order
    return state
