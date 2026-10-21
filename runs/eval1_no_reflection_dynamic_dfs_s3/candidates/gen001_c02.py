"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

Maintains a genuine DFS forest (parent, discover, finish) of the current
graph.  On each update, only the affected portion of the forest is
re-searched:

- Insert u->v: if v is already reachable, the forest stays valid.  If v
  was unreachable, v and everything reachable from v become reachable; we
  re-search the new region and renumber the tail of the old forest.

- Delete u->v: if the edge is not a tree edge, the forest stays valid.
  If it is a tree edge, the subtree rooted at v may lose reachability; we
  re-search from v's children and from every in-neighbor of the subtree.
"""


def _dfs_from(graph, start, parent, discover, finish, counter, n):
    """Iterative DFS from `start` (already discovered, counter advanced).

    Fills parent/discover/finish for newly reached vertices.
    """
    stack = [[start, 0]]
    while stack:
        u, ci = stack[-1]
        advanced = False
        while ci < n:
            if graph[u][ci] and discover[ci] == -1:
                parent[ci] = u
                discover[ci] = counter[0]
                counter[0] += 1
                stack[-1][1] = ci + 1
                stack.append([ci, 0])
                advanced = True
                break
            ci += 1
        if not advanced:
            finish[u] = counter[0]
            counter[0] += 1
            stack.pop()


def _init_dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    discover[0] = 0
    counter = [1]
    _dfs_from(graph, 0, parent, discover, finish, counter, n)
    return parent, discover, finish


def init(graph):
    parent, discover, finish = _init_dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent'][:]
    discover = state['discover'][:]
    finish = state['finish'][:]

    if discover[v] != -1:
        # v already reachable; new edge cannot invalidate the DFS forest.
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # v was unreachable.  The new edge u->v makes v (and everything
    # reachable from v) reachable.
    old_finish_u = finish[u]

    # Tail: reachable vertices discovered after u finished.
    tail = [w for w in range(n)
            if discover[w] != -1 and discover[w] >= old_finish_u]
    tail_order = sorted(tail, key=lambda w: discover[w])
    tail_parents = {w: parent[w] for w in tail}

    # Clear tail.
    for w in tail:
        discover[w] = -1
        finish[w] = -1
        parent[w] = None

    # Re-search from v (parent = u).
    parent[v] = u
    discover[v] = old_finish_u
    counter = [old_finish_u + 1]
    _dfs_from(graph, v, parent, discover, finish, counter, n)

    # Re-search tail vertices in their original discover order.
    for w in tail_order:
        if discover[w] == -1:
            parent[w] = tail_parents[w]
            discover[w] = counter[0]
            counter[0] += 1
            _dfs_from(graph, w, parent, discover, finish, counter, n)

    # Update u's finish time: u's subtree now includes v's region.
    # u's finish should be the max finish in u's subtree.
    max_fin = old_finish_u
    for w in range(n):
        if discover[w] != -1 and discover[w] >= discover[u] and discover[w] < counter[0]:
            if finish[w] > max_fin:
                max_fin = finish[w]
    finish[u] = max_fin

    return {'parent': parent, 'discover': discover, 'finish': finish}


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent'][:]
    discover = state['discover'][:]
    finish = state['finish'][:]

    if parent[v] != u:
        # Not a tree edge; forest stays valid.
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # u->v is a tree edge.  Identify the subtree rooted at v.
    subtree = set()
    stack = [v]
    while stack:
        w = stack.pop()
        if w in subtree:
            continue
        subtree.add(w)
        for x in range(n):
            if graph[w][x] and parent[x] == w:
                stack.append(x)

    # Save children of v (in discover order) before clearing.
    children = sorted([x for x in subtree if parent[x] == v],
                      key=lambda x: discover[x])

    # Save in-neighbors of the subtree that are outside it.
    in_neighbors = set()
    for w in subtree:
        for x in range(n):
            if x not in subtree and graph[x][w]:
                in_neighbors.add(x)

    # Clear the subtree.
    for w in subtree:
        discover[w] = -1
        finish[w] = -1
        parent[w] = None

    # Re-search from v's children and in-neighbors.
    old_disc_v = state['discover'][v]
    counter = [old_disc_v + 1]

    # Re-search sources: v's children + in-neighbors, in discover order.
    sources = list(set(children) | in_neighbors)
    sources.sort(key=lambda x: state['discover'][x] if state['discover'][x] != -1 else n)

    for w in sources:
        if discover[w] == -1:
            # w is a child of v (in the subtree, now cleared).
            discover[w] = counter[0]
            counter[0] += 1
            parent[w] = None
            _dfs_from(graph, w, parent, discover, finish, counter, n)
        else:
            # w is an in-neighbor (outside subtree, already discovered).
            # Explore w's edges to find undiscovered subtree vertices.
            _dfs_from(graph, w, parent, discover, finish, counter, n)

    # Update u's finish time: u's subtree no longer includes v's region.
    max_fin = discover[u]
    for w in range(n):
        if discover[w] != -1 and discover[w] >= discover[u] and discover[w] < state['finish'][u]:
            if finish[w] > max_fin:
                max_fin = finish[w]
    finish[u] = max_fin

    return {'parent': parent, 'discover': discover, 'finish': finish}
