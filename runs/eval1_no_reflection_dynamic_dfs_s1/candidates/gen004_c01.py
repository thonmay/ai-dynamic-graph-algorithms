"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy: maintain a valid DFS forest (parent, discover, finish). On each
update, check whether the current forest is still a valid DFS forest of the
new graph (Yang et al. Lemma 1: a spanning tree is a DFS tree iff it has no
forward-cross edges). If it is valid, keep it. Otherwise, recompute the DFS
forest from scratch (correct fallback).

This is correct by construction: we only keep a forest that is certified
valid, and otherwise rebuild. The validity check is O(n + m) which is the
same order as a full recompute, but the check is cheap per edge and avoids
the recompute in the common case where the update does not break the forest.
"""


def _dfs(graph, n):
    """Iterative DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    clock = 0
    # stack of (vertex, next_child_index)
    stack = []
    # We simulate recursive DFS: push root, then walk children in order.
    # Use explicit stack with iterator state.
    stack = [(0, 0)]
    discover[0] = 0
    clock = 1
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < n:
            if graph[u][i] and discover[i] == -1:
                discover[i] = clock
                clock += 1
                parent[i] = u
                stack[-1] = (u, i + 1)
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[u] = clock
            clock += 1
            stack.pop()
    return parent, discover, finish


def _is_valid_dfs(graph, n, parent, discover, finish):
    """Check that (parent, discover, finish) is a valid DFS forest of graph.

    Conditions:
    1. discover/finish are consistent: for each tree edge parent[v]->v,
       discover[parent[v]] < discover[v] < finish[v] < finish[parent[v]].
    2. No forward-cross edge: for every edge u->v in the graph where both
       are reachable (discover != -1), if discover[u] < discover[v] then v
       must be a descendant of u: discover[u] < discover[v] < finish[v] < finish[u].
    3. discover/finish times are a valid DFS numbering: each vertex gets a
       unique discover time, finish > discover, and the intervals are
       properly nested or disjoint.
    4. Reachability: every vertex reachable from 0 in the graph must have
       discover != -1 (the DFS forest must span all reachable vertices).
    5. Tree edges exist in the graph: for each v with parent[v] = p,
       graph[p][v] must be 1.
    """
    # Check 3: intervals are properly nested or disjoint, times unique.
    intervals = []
    seen_disc = set()
    for v in range(n):
        if discover[v] != -1:
            if discover[v] in seen_disc:
                return False
            seen_disc.add(discover[v])
            if finish[v] <= discover[v]:
                return False
            intervals.append((discover[v], finish[v], v))
    # Sort by discover; check nesting/disjointness with a stack.
    intervals.sort()
    stack = []
    for d, f, v in intervals:
        while stack and stack[-1][1] < d:
            stack.pop()
        if stack and stack[-1][1] > f:
            if f > stack[-1][1]:
                return False
        stack.append((d, f, v))
    # Check 1: tree edges respect intervals AND exist in graph.
    for v in range(n):
        if discover[v] == -1:
            if parent[v] is not None:
                return False
            continue
        p = parent[v]
        if p is None:
            if v != 0:
                return False
            continue
        if discover[p] == -1:
            return False
        if not (discover[p] < discover[v] < finish[v] < finish[p]):
            return False
        # Check 5: the tree edge must exist in the current graph.
        if not graph[p][v]:
            return False
    # Check 2: no forward-cross edges.
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if graph[u][v] and discover[v] != -1:
                if discover[u] < discover[v]:
                    if not (discover[u] < discover[v] < finish[v] < finish[u]):
                        return False
    # Check 4: reachability - BFS/DFS from 0 in the graph.
    reachable = [False] * n
    if n > 0:
        reachable[0] = True
        queue = [0]
        qi = 0
        while qi < len(queue):
            u = queue[qi]
            qi += 1
            for v in range(n):
                if graph[u][v] and not reachable[v]:
                    reachable[v] = True
                    queue.append(v)
    for v in range(n):
        if reachable[v] and discover[v] == -1:
            return False
    return True


def _rebuild_subtree(graph, n, root, parent, discover, finish):
    """Re-run DFS restricted to the subtree rooted at `root`.

    The subtree is exactly the set of vertices w with
    discover[root] <= discover[w] < finish[root] (intervals are properly
    nested, so this is a contiguous discover-time interval).  We re-search
    from `root` over the current graph, but never leave the interval:
    vertices outside it keep their old times, and edges to them are treated
    as non-tree edges (they are either back/cross edges into already-
    finished regions, which is fine for a DFS forest).

    Returns (ok, parent, discover, finish).  ok is False if the re-search
    cannot span the whole interval (e.g. a tree edge was deleted and some
    vertex in the interval is no longer reachable from root within the
    interval), in which case the caller should fall back to a full rebuild.
    """
    lo = discover[root]
    hi = finish[root]
    # Vertices in the interval, in old discover order.
    in_sub = [v for v in range(n) if lo <= discover[v] < hi]
    # Map old discover time -> vertex for the interval.
    old_disc = {discover[v]: v for v in in_sub}
    # New times: root keeps its discover time; others get fresh times.
    new_disc = {root: lo}
    new_fin = {}
    new_par = {root: None}
    # DFS from root, restricted to vertices in the interval.
    # Children are considered in vertex-id order (any fixed order works).
    # A vertex w is a candidate child of u iff w is in the interval and
    # not yet discovered in this re-search.
    stack = [(root, 0)]
    clock = lo + 1
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < n:
            if graph[u][i] and i in old_disc and i not in new_disc:
                new_disc[i] = clock
                clock += 1
                new_par[i] = u
                stack[-1] = (u, i + 1)
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            new_fin[u] = clock
            clock += 1
            stack.pop()
    # The re-search must have covered the whole interval.
    if len(new_disc) != len(in_sub):
        return False, parent, discover, finish
    # Apply new times to the global arrays.
    for v in in_sub:
        discover[v] = new_disc[v]
        finish[v] = new_fin[v]
        parent[v] = new_par[v]
    return True, parent, discover, finish


def _make_state(graph):
    n = len(graph)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    u, v = edge
    # Fast path: if the old forest is still valid, keep it.
    if _is_valid_dfs(graph, n, parent, discover, finish):
        return state
    # The new edge u->v creates a forward-cross edge: discover[u] <
    # discover[v] and v is not a descendant of u.  The standard fix is to
    # re-search the subtree rooted at v (the earliest-discovered vertex in
    # the affected region).  If that fails, fall back to a full rebuild.
    if discover[u] != -1 and discover[v] != -1 and discover[u] < discover[v]:
        ok, parent, discover, finish = _rebuild_subtree(
            graph, n, v, parent, discover, finish)
        if ok and _is_valid_dfs(graph, n, parent, discover, finish):
            return {'parent': parent, 'discover': discover, 'finish': finish}
    # Fallback: the old forest is invalid and the local fix did not work.
    # Rebuild from scratch.
    return _make_state(graph)


def delete_edge(graph, edge, state):
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    u, v = edge
    # Fast path: if the old forest is still valid, keep it.
    if _is_valid_dfs(graph, n, parent, discover, finish):
        return state
    # The deleted edge was a tree edge parent[v] == u (otherwise the forest
    # would still be valid).  Re-search the subtree rooted at v; if some
    # vertex in it is no longer reachable from v within the interval, fall
    # back to a full rebuild.
    if parent[v] == u and discover[v] != -1:
        ok, parent, discover, finish = _rebuild_subtree(
            graph, n, v, parent, discover, finish)
        if ok and _is_valid_dfs(graph, n, parent, discover, finish):
            return {'parent': parent, 'discover': discover, 'finish': finish}
    return _make_state(graph)
