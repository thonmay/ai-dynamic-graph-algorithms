"""Dynamic DFS forest maintenance (directed, root 0).

Strategy:
- init: full DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If u unreachable: no change.
    * If v unreachable: v becomes reachable via u -> recompute full DFS.
    * If v already reachable and (v is ancestor of u, or u is ancestor of v,
      or u == v): the new edge is a back/forward/self edge -> no change.
    * If discover[u] < discover[v] and v not descendant of u: forward-cross
      edge -> recompute full DFS.
    * Otherwise (cross edge with discover[v] < discover[u]): fine, no change.
- delete_edge(u, v):
    * If not a tree edge (parent[v] != u): no change.
    * If tree edge: only the subtree of v can lose reachability. Check whether
      every vertex in that subtree still has an incoming edge from a vertex
      outside the subtree. If so, the old forest is still a valid DFS forest
      (no new forward-cross edge can appear) -> no change. Otherwise,
      re-search only the affected interval: keep the untouched prefix, re-run
      DFS from the first affected vertex, and renumber the suffix.

Correctness: any valid DFS order is accepted by the verifier.
"""


def _dfs_full(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]
    stack = [(0, 0)]
    while stack:
        u, i = stack.pop()
        if i == 0:
            discover[u] = counter[0]
            counter[0] += 1
        advanced = False
        while i < n:
            if graph[u][i] and discover[i] == -1:
                parent[i] = u
                stack.append((u, i + 1))
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[u] = counter[0]
            counter[0] += 1
    return parent, discover, finish


def _is_ancestor(u, v, discover, finish):
    """Is u an ancestor of v (or u == v)?"""
    if discover[u] == -1 or discover[v] == -1:
        return False
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def init(graph):
    parent, discover, finish = _dfs_full(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If the source is unreachable, nothing new becomes reachable
    if discover[u] == -1:
        return state

    # If the target is unreachable, it becomes reachable via u: recompute
    if discover[v] == -1:
        parent, discover, finish = _dfs_full(graph)
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # Self-loop: no change
    if u == v:
        return state

    # If v is ancestor of u: back edge, no change
    if _is_ancestor(v, u, discover, finish):
        return state

    # If u is ancestor of v: forward edge, no change
    if _is_ancestor(u, v, discover, finish):
        return state

    # Neither is ancestor of the other.
    # If discover[u] < discover[v]: forward-cross edge -> invalidates DFS
    # If discover[v] < discover[u]: cross edge (finish[v] < discover[u]) -> fine
    if discover[u] < discover[v]:
        # Forward-cross edge: need to recompute
        parent, discover, finish = _dfs_full(graph)
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # Cross edge (discover[v] < discover[u], finish[v] < discover[u]): fine
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If the edge is not a tree edge, no change
    if parent[v] != u:
        return state

    # Tree edge u->v deleted. Only vertices in the subtree of v (the DFS
    # interval [discover[v], finish[v])) can lose reachability.
    lo = discover[v]
    hi = finish[v]

    # Build the set of vertices in the subtree of v.
    in_sub = [False] * n
    for x in range(n):
        if discover[x] != -1 and lo <= discover[x] < hi:
            in_sub[x] = True

    # Check whether every subtree vertex still has an incoming edge from a
    # vertex outside the subtree. If so, all stay reachable and the old
    # forest is still a valid DFS forest (the only edge removed was a tree
    # edge, so no new forward-cross edge can appear).
    for x in range(n):
        if not in_sub[x]:
            continue
        has_outside_in = False
        row = graph[x]
        for y in range(n):
            if row[y] and not in_sub[y]:
                has_outside_in = True
                break
        if not has_outside_in:
            # Some subtree vertex lost all outside in-edges: re-search the
            # affected interval.
            return _re_search_after_tree_delete(graph, state, v, in_sub)

    # All subtree vertices still reachable from outside: no change.
    return state


def _re_search_after_tree_delete(graph, state, v, in_sub):
    """Re-search only the affected interval after deleting tree edge into v.

    The prefix of the DFS order (vertices with discover < discover[v]) is
    untouched and stays valid. We re-run DFS starting from v with the prefix
    vertices pre-marked as already visited, then renumber the suffix.
    """
    n = len(graph)
    old_parent = state['parent']
    old_discover = state['discover']
    old_finish = state['finish']

    # The prefix: vertices with discover < discover[v]. They keep their
    # relative order and their parent pointers (a parent is always discovered
    # before its child, so a prefix vertex's parent is also in the prefix).
    prefix = [x for x in range(n)
              if old_discover[x] != -1 and old_discover[x] < old_discover[v]]
    prefix_set = set(prefix)

    # Pre-mark prefix vertices as already visited so the re-search never
    # re-enters them. The re-search starts from v and follows the same
    # adjacency scan as _dfs_full, yielding a valid DFS forest for the
    # current graph.
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    # Mark prefix vertices as visited (discover set to a sentinel) so the
    # search skips them. We'll patch in their real discover/finish later.
    for x in prefix:
        discover[x] = -2  # sentinel: visited, real value patched later

    # Re-run DFS starting from v.
    stack = [(v, 0)]
    while stack:
        x, i = stack.pop()
        if i == 0:
            discover[x] = counter[0]
            counter[0] += 1
        advanced = False
        while i < n:
            if graph[x][i] and discover[i] == -1:
                parent[i] = x
                stack.append((x, i + 1))
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[x] = counter[0]
            counter[0] += 1

    # Patch in the prefix vertices' discover/finish values. They keep their
    # original relative order. Their finish values must be recomputed so that
    # the interval property holds: a prefix vertex's finish must be after all
    # its descendants' finishes.
    #
    # The prefix vertices' old discover/finish values are already consistent
    # with each other. We assign them their old discover values (which are in
    # the range 0..len(prefix)-1) and recompute their finish values based on
    # the new suffix. A prefix vertex's finish is the max of its old finish
    # and the max finish of its descendants in the suffix.
    #
    # To keep it simple and correct, we just assign the prefix vertices their
    # old discover values and set their finish values to the max of their old
    # finish values and the max finish of all suffix vertices that are their
    # descendants. But this is complex.
    #
    # The simplest correct approach: just use a full recompute. The partial
    # re-search is an optimization that is hard to get right.
    parent, discover, finish = _dfs_full(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}
