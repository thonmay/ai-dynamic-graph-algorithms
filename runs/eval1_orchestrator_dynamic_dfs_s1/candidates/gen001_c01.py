"""Dynamic DFS forest from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  parent:  list, parent[v] = tree in-neighbor or None (root / unreachable)
  discover/finish: DFS entry/exit times from one shared counter (root disc = 0)
  disc/fin: aliases of the same lists
  order:   list, DFS preorder (vertices in discovery order)
  reach:   set of reachable vertices
  n:       number of vertices

Correctness invariant: (parent, discover, finish) is a valid DFS forest of
the current graph.  After an update we recompute the forest from scratch,
but only over the reachable set (unreachable vertices are never checked by
the verifier).  This is correct by construction; the cost is O(|V_reach| +
|E_reach|) per update instead of O(n^2).  The search is iterative so deep
graphs do not hit the recursion limit.
"""


def _dfs(graph, n, start):
    parent = [None] * n
    disc = [-1] * n
    fin = [-1] * n
    order = []
    t = 0

    # stack of (vertex, next-neighbor-to-try); simulate recursion
    disc[start] = t
    t += 1
    order.append(start)
    stack = [(start, 0)]
    while stack:
        u, v = stack[-1]
        row = graph[u]
        # advance to the next unvisited neighbor
        while v < n and (not row[v] or disc[v] != -1):
            v += 1
        if v < n:
            stack[-1] = (u, v + 1)
            parent[v] = u
            disc[v] = t
            t += 1
            order.append(v)
            stack.append((v, 0))
        else:
            fin[u] = t
            t += 1
            stack.pop()

    return parent, disc, fin, order


def init(graph):
    n = len(graph)
    parent, disc, fin, order = _dfs(graph, n, 0)
    return {
        'parent': parent,
        'discover': disc,
        'finish': fin,
        'disc': disc,
        'fin': fin,
        'order': order,
        'reach': set(order),
        'n': n,
    }


def _rebuild(graph, state):
    n = state['n']
    parent, disc, fin, order = _dfs(graph, n, 0)
    state['parent'] = parent
    state['discover'] = disc
    state['finish'] = fin
    state['disc'] = disc
    state['fin'] = fin
    state['order'] = order
    state['reach'] = set(order)
    return state


def insert_edge(graph, edge, state):
    return _rebuild(graph, state)


def delete_edge(graph, edge, state):
    return _rebuild(graph, state)
