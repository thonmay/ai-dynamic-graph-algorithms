"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy (Yang et al. style, simplified):
- Maintain a valid DFS forest (parent, discover, finish) of the current graph.
- On an update, first check whether the old forest is still a valid DFS
  forest of the new graph (Lemma 1: a spanning tree is a DFS tree iff it has
  no forward-cross edges, plus reachability and tree-edge existence).
  If so, keep it (O(n+m) check, no recompute).
- Otherwise, recompute the DFS forest from scratch. This is always correct
  and is the safe fallback; the check above avoids the recompute in the
  common case where the update does not break the forest.

Correctness: we only ever return a forest that is either (a) certified valid
for the current graph, or (b) freshly computed by a full DFS of the current
graph. Both are valid DFS forests.
"""


def _dfs(graph, n):
    """Iterative DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    if n == 0:
        return parent, discover, finish
    clock = 0
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
    1. discover/finish intervals are properly nested or disjoint, times unique.
    2. Tree edges exist in the graph and respect intervals.
    3. No forward-cross edge: for every edge u->v between reachable vertices
       with discover[u] < discover[v], v must be a descendant of u.
    4. Reachability: every vertex reachable from 0 has discover != -1.
    """
    # Check 1: intervals properly nested or disjoint, discover times unique.
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
        if stack and stack[-1][1] > f:
            return False
        stack.append((d, f, v))
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
        row = graph[u]
        for v in range(n):
            if row[v] and discover[v] != -1:
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
            row = graph[u]
            for v in range(n):
                if row[v] and not reachable[v]:
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


def _update(graph, state):
    n = len(graph)
    if _is_valid_dfs(graph, n, state['parent'], state['discover'], state['finish']):
        return state
    return _make_state(graph)


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    return _update(graph, state)


def delete_edge(graph, edge, state):
    return _update(graph, state)
