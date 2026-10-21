"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

Maintains a genuine DFS forest of the current directed graph:
  - parent[v]: tree in-neighbor (None for root and unreachable vertices)
  - discover[v], finish[v]: DFS entry/exit times from one shared counter

Correctness invariant (Yang et al. Lemma 1): a spanning search tree is a DFS
tree iff it has no forward-cross edge, i.e. no edge u->v with
discover[u] < discover[v] and v not a descendant of u.

Strategy:
  - insert: if the new edge is a forward-cross edge (or makes an unreachable
    vertex reachable), re-run DFS from the source u.  u's subtree is
    renumbered; everything else keeps its times.
  - delete: if the deleted edge is a tree edge, re-run DFS from the child.
  - otherwise the forest is unchanged.
"""


def _dfs_from(graph, start, parent, discover, finish):
    """Iterative DFS from `start` over the current graph.

    Renumber only the vertices visited (the subtree of `start` under the
    current forest); all other vertices keep their existing times.
    """
    n = len(graph)
    d0, f0 = discover[start], finish[start]
    # collect the old subtree of `start` (vertices whose times will be
    # renumbered) and clear their parent pointers
    old_sub = set()
    for x in range(n):
        if discover[x] >= d0 and discover[x] <= f0:
            old_sub.add(x)
    for x in old_sub:
        parent[x] = None

    counter = [d0]
    # iterative DFS with explicit stack of (vertex, next-neighbor-index)
    stack = [(start, 0)]
    discover[start] = d0
    parent[start] = None
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < n:
            if graph[u][i]:
                if discover[i] >= f0 or discover[i] < d0:
                    # unvisited (or outside the renumbered interval)
                    discover[i] = counter[0] + 1
                    counter[0] += 1
                    parent[i] = u
                    stack[-1] = (u, i + 1)
                    stack.append((i, 0))
                    advanced = True
                    break
                # else: already visited (tree/forward/back edge) - skip
            i += 1
        if not advanced:
            stack.pop()
            finish[u] = counter[0] + 1
            counter[0] += 1
    return parent, discover, finish


def _full_dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]
    # iterative DFS from root 0
    stack = [(0, 0)]
    discover[0] = 0
    counter[0] = 1
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < n:
            if graph[u][i] and discover[i] == -1:
                discover[i] = counter[0]
                counter[0] += 1
                parent[i] = u
                stack[-1] = (u, i + 1)
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            stack.pop()
            finish[u] = counter[0]
            counter[0] += 1
    return parent, discover, finish


def _is_descendant(discover, finish, anc, desc):
    return discover[anc] < discover[desc] < finish[desc] < finish[anc]


def init(graph):
    parent, discover, finish = _full_dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    # if v is already reachable and u is reachable, check for forward-cross
    if discover[u] != -1 and discover[v] != -1:
        if discover[u] < discover[v] and not _is_descendant(discover, finish, u, v):
            # forward-cross edge: re-search from u
            parent, discover, finish = _dfs_from(graph, u, parent, discover, finish)
    # if v was unreachable, it may become reachable: re-search from u
    elif discover[u] != -1 and discover[v] == -1:
        parent, discover, finish = _dfs_from(graph, u, parent, discover, finish)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    # if the deleted edge is a tree edge, re-search from v
    if parent[v] == u and discover[v] != -1:
        parent, discover, finish = _dfs_from(graph, v, parent, discover, finish)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
