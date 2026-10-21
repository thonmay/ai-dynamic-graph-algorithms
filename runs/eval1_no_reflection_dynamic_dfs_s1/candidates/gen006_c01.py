"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy (Yang et al. style):
- Maintain a valid DFS forest (parent, discover, finish) of the current graph.
- On an update, check whether the old forest is still a valid DFS forest of
  the new graph.  If yes, keep it (no recompute).
- If not, recompute the DFS forest from scratch.

The validity check is O(n^2) in the worst case (adjacency matrix), same order
as a full recompute, but it is a single pass and avoids the recompute in the
common case where the update does not break the forest.

Correctness: we only keep a forest that is certified valid for the current
graph, and otherwise rebuild from scratch.  The rebuild is a plain DFS, so
the result is always a valid DFS forest.
"""


def _dfs(graph, n):
    """Iterative DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    if n == 0:
        return parent, discover, finish
    clock = 0
    # stack of [vertex, next_child_index]
    stack = [[0, 0]]
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
                stack[-1][1] = i + 1
                stack.append([i, 0])
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
    1. discover/finish intervals are properly nested or disjoint, times unique.
    2. Tree edges respect intervals AND exist in the graph.
    3. No forward-cross edge: for every edge u->v where both are reachable,
       if discover[u] < discover[v] then v must be a descendant of u.
    4. Reachability: every vertex reachable from 0 in the graph must have
       discover != -1.
    """
    # Check 1: intervals properly nested or disjoint, times unique.
    # A DFS forest's intervals are exactly the intervals of a depth-first
    # traversal: sorted by discover, each interval is either contained in the
    # previous one or starts after it finished.
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
    intervals.sort()
    stack = []
    for d, f, v in intervals:
        while stack and stack[-1][1] < d:
            stack.pop()
        if stack and f > stack[-1][1]:
            return False
        stack.append((d, f, v))
    # Check 1b: times are a single contiguous range 0..2r-1 (r = #reachable),
    # i.e. the counter was shared and every slot is used exactly once.
    r = len(intervals)
    if r > 0:
        if max(f for _, f, _ in intervals) != 2 * r - 1:
            return False
        if len(set(finish)) != r:
            return False
    # Check 1c: the root's interval must contain every other interval.
    if r > 0:
        root = intervals[0]
        if root[2] != 0:
            return False
        if root[0] != 0 or root[1] != 2 * r - 1:
            return False
    # Check 2: tree edges respect intervals AND exist in the graph.
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
        if not graph[p][v]:
            return False
    # Check 3: no forward-cross edges.
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if graph[u][v] and discover[v] != -1:
                if discover[u] < discover[v]:
                    if not (discover[u] < discover[v] < finish[v] < finish[u]):
                        return False
    # Check 4: reachability - BFS from 0 in the graph.
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
    if _is_valid_dfs(graph, n, parent, discover, finish):
        return state
    return _make_state(graph)


def delete_edge(graph, edge, state):
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs(graph, n, parent, discover, finish):
        return state
    return _make_state(graph)
