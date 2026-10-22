"""Seeded-fault corpus for the verifier self-test.

Each fault is a one-line mutation of the known-good reference
(:mod:`evoalgo.selftest.references`), expressed as an override of one (or two)
named code block. Every *real* fault is documented with its minimal
counterexample (n, base edge list, single-edge op) at n<=5 -- the smallest
case where the mutated candidate violates the problem invariant. These were
derived and verified against the real ``check_invariant`` (see
``/tmp/enlcode/yang/fault_results.json`` in the research notes; reproduced and
re-checked by ``tests/test_verifier_iso.py``).

Two entries are **equivalent controls** (``is_equivalent=True``): D9 (DFS,
descending neighbour order) and B12 (BFS, descending neighbour order). These
are *valid* algorithm variants, not bugs -- the verifier must ACCEPT them,
which demonstrates the checker is invariant-based and not biased to one
tie-break. They are excluded from the zero-false-negative count.

Zero false negatives := every real fault (``is_equivalent=False``) is
rejected (FAIL or CRASH) by the n<=5 verifier.
"""

from __future__ import annotations

from .references import _assemble, reference_blocks

# ---------------------------------------------------------------------------
# Fault block overrides. Each value is a full replacement for the named block.
# ---------------------------------------------------------------------------

_DFS_FAULT_OVERRIDES: dict[str, dict[str, str]] = {
    # D1: missed update on delete (tree-edge deletion treated as no-op)
    "D1": {
        "delete": '''
def delete_edge(graph, edge, state):
    return state
''',
    },
    # D2: missed update on insert (forward-cross insert treated as no-op)
    "D2": {
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    d = state["discover"]
    if t not in d and s in d:
        return _recompute(graph)
    return state
''',
    },
    # D3: inverted forward-cross test (rebuild when descendant, keep when fwd-cross)
    "D3": {
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    d = state["discover"]
    if t not in d and s in d:
        return _recompute(graph)
    if t in d and s in d and d[s] < d[t] and _is_desc(state, s, t):
        return _recompute(graph)
    return state
''',
    },
    # D4: off-by-one: finish timer not incremented (finish[u]=timer[0] w/o +1)
    "D4": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
    # D5: stale discover/finish on rebuild (rebuild parent, keep old times)
    "D5": {
        "recompute_stale": '''
def _recompute_stale(graph, old):
    fresh = _recompute(graph)
    fresh["discover"] = old["discover"]
    fresh["finish"] = old["finish"]
    return fresh
''',
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    d = state["discover"]
    if t not in d and s in d:
        return _recompute_stale(graph, state)
    if t in d and s in d and d[s] < d[t] and not _is_desc(state, s, t):
        return _recompute_stale(graph, state)
    return state
''',
        "delete": '''
def delete_edge(graph, edge, state):
    s, t = edge
    if _is_tree(state, s, t):
        return _recompute_stale(graph, state)
    return state
''',
    },
    # D6: root gets a parent
    "D6": {
        "init": '''
def init(graph):
    st = _recompute(graph)
    st["parent"][0] = 1 if len(graph) > 1 else None
    return st
''',
    },
    # D7: recompute follows reverse edges (graph[v][u] instead of graph[u][v])
    "D7": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n):
            if graph[v][u] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1
    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
    # D8: insert is a no-op (never rebuild on insert)
    "D8": {
        "insert": '''
def insert_edge(graph, edge, state):
    return state
''',
    },
    # D10: drop one reachable vertex from discover/finish
    "D10": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1
    dfs(0)
    if discover:
        last = max(discover, key=lambda x: discover[x])
        if last != 0:
            del discover[last]
            del finish[last]
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
    # D11: parent points to a non-neighbor
    "D11": {
        "init": '''
def init(graph):
    st = _recompute(graph)
    for v in st["parent"]:
        if v != 0 and st["parent"][v] is not None:
            bad = (v + 1) % len(graph)
            if bad != v and not graph[bad][v]:
                st["parent"][v] = bad
            break
    return st
''',
    },
    # D12: discover time not incremented (duplicate times)
    "D12": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1
    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
    # D13: rebuild from the stale (pre-delete) graph
    "D13": {
        "delete": '''
def delete_edge(graph, edge, state):
    s, t = edge
    if _is_tree(state, s, t):
        g_old = [row[:] for row in graph]
        g_old[s][t] = 1
        return _recompute(g_old)
    return state
''',
    },
    # D14: finish time == discover time (no subtree span)
    "D14": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = discover[u]
    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
    # D15: on insert, rebuild but forget to add the new edge to the graph
    "D15": {
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    d = state["discover"]
    if t not in d and s in d:
        g_old = [row[:] for row in graph]
        g_old[s][t] = 0
        return _recompute(g_old)
    if t in d and s in d and d[s] < d[t] and not _is_desc(state, s, t):
        return _recompute(graph)
    return state
''',
    },
    # D16: parent set to the earliest-discovered in-neighbour on the tree
    # path instead of the vertex that discovered it (times still a real DFS)
    "D16": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    path = []
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        path.append(u)
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = next(a for a in path if graph[a][v] == 1)
                dfs(v)
        path.pop()
        finish[u] = timer[0]
        timer[0] += 1
    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
    # D9: descending neighbour order (EQUIVALENT control)
    "D9": {
        "recompute": '''
def _recompute(graph):
    import sys
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]
    sys.setrecursionlimit(10000)
    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n - 1, -1, -1):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1
    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    },
}

_BFS_FAULT_OVERRIDES: dict[str, dict[str, str]] = {
    # B1: missed update on delete (tree-edge deletion treated as no-op)
    "B1": {
        "delete": '''
def delete_edge(graph, edge, state):
    return state
''',
    },
    # B2: missed update on insert (distance-shortening edge treated as no-op)
    "B2": {
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    dist = state["distances"]
    if t not in dist and s in dist:
        return _recompute(graph)
    return state
''',
    },
    # B3: inverted distance-shortening test
    "B3": {
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    dist = state["distances"]
    if t in dist:
        if s in dist and dist[s] + 1 > dist[t]:
            return _recompute(graph)
        return state
    else:
        if s in dist:
            return _recompute(graph)
        return state
''',
    },
    # B4: off-by-one in distance (dist[v] = dist[u], not +1)
    "B4": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u]
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
    # B5: off-by-one: recompute loop skips last vertex (range(n-1))
    "B5": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n - 1):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
    # B6: root gets a parent
    "B6": {
        "init": '''
def init(graph):
    st = _recompute(graph)
    st["parent"][0] = 1 if len(graph) > 1 else None
    return st
''',
    },
    # B7: recompute follows reverse edges (graph[v][u] instead of graph[u][v])
    "B7": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[v][u] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
    # B8: insert is a no-op (never rebuild on insert)
    "B8": {
        "insert": '''
def insert_edge(graph, edge, state):
    return state
''',
    },
    # B9: parent points to a non-neighbor
    "B9": {
        "init": '''
def init(graph):
    st = _recompute(graph)
    for v in st["parent"]:
        if v != 0 and st["parent"][v] is not None:
            bad = (v + 1) % len(graph)
            if bad != v and not graph[bad][v]:
                st["parent"][v] = bad
            break
    return st
''',
    },
    # B10: forget to add a newly-reachable vertex
    "B10": {
        "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    if t not in state["distances"] and s in state["distances"]:
        return state
    if t in state["distances"] and s in state["distances"] and state["distances"][s] + 1 < state["distances"][t]:
        return _recompute(graph)
    return state
''',
    },
    # B11: wrong root (1 instead of 0)
    "B11": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    r = 1 if n > 1 else 0
    parent = {r: None}
    dist = {r: 0}
    queue = collections.deque([r])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
    # B13: rebuild from the stale (pre-delete) graph
    "B13": {
        "delete": '''
def delete_edge(graph, edge, state):
    s, t = edge
    if state["parent"].get(t) == s:
        g_old = [row[:] for row in graph]
        g_old[s][t] = 1
        return _recompute(g_old)
    return state
''',
    },
    # B14: parent at wrong BFS level (parent[v] = (u+2) % n)
    "B14": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = (u + 2) % n
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
    # B15: recompute treats the graph as undirected
    "B15": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if (graph[u][v] == 1 or graph[v][u] == 1) and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
    # B12: descending neighbour order (EQUIVALENT control)
    "B12": {
        "recompute": '''
def _recompute(graph):
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n - 1, -1, -1):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    },
}

# ---------------------------------------------------------------------------
# Fault metadata table.
# counterexample = (n, edges, op) where op is "init" or (type, (u, v)).
# ---------------------------------------------------------------------------

_FAULTS: list[dict] = [
    # ---- DFS ----
    {"id": "D1", "problem": "dynamic_dfs",
     "description": "missed update on delete (tree-edge deletion treated as no-op)",
     "fault_class": "stale tree after tree-edge delete",
     "counterexample": (3, [(0, 1), (0, 2), (1, 2)], ("delete", (1, 2))),
     "overrides": _DFS_FAULT_OVERRIDES["D1"], "is_equivalent": False},
    {"id": "D2", "problem": "dynamic_dfs",
     "description": "missed update on insert (forward-cross edge ignored)",
     "fault_class": "missed update on insert",
     "counterexample": (3, [(0, 1), (0, 2)], ("insert", (1, 2))),
     "overrides": _DFS_FAULT_OVERRIDES["D2"], "is_equivalent": False},
    {"id": "D3", "problem": "dynamic_dfs",
     "description": "inverted forward-cross test (rebuild when descendant, keep when fwd-cross)",
     "fault_class": "wrong predicate",
     "counterexample": (3, [(0, 1), (0, 2)], ("insert", (1, 2))),
     "overrides": _DFS_FAULT_OVERRIDES["D3"], "is_equivalent": False},
    {"id": "D4", "problem": "dynamic_dfs",
     "description": "off-by-one: finish timer not incremented",
     "fault_class": "off-by-one (timing)",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _DFS_FAULT_OVERRIDES["D4"], "is_equivalent": False},
    {"id": "D5", "problem": "dynamic_dfs",
     "description": "stale discover/finish on rebuild (rebuild parent, keep old times)",
     "fault_class": "stale certificate",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _DFS_FAULT_OVERRIDES["D5"], "is_equivalent": False},
    {"id": "D6", "problem": "dynamic_dfs",
     "description": "root assigned a parent",
     "fault_class": "invalid root",
     "counterexample": (2, [], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D6"], "is_equivalent": False},
    {"id": "D7", "problem": "dynamic_dfs",
     "description": "recompute follows reverse edges",
     "fault_class": "ignores direction",
     "counterexample": (2, [(0, 1)], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D7"], "is_equivalent": False},
    {"id": "D8", "problem": "dynamic_dfs",
     "description": "insert is a no-op (never rebuild on insert)",
     "fault_class": "missed update on insert",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _DFS_FAULT_OVERRIDES["D8"], "is_equivalent": False},
    {"id": "D9", "problem": "dynamic_dfs",
     "description": "descending neighbour order (valid variant, not a bug)",
     "fault_class": "equivalent control",
     "counterexample": None,
     "overrides": _DFS_FAULT_OVERRIDES["D9"], "is_equivalent": True},
    {"id": "D10", "problem": "dynamic_dfs",
     "description": "drop one reachable vertex from discover/finish",
     "fault_class": "incomplete forest",
     "counterexample": (2, [(0, 1)], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D10"], "is_equivalent": False},
    {"id": "D11", "problem": "dynamic_dfs",
     "description": "parent points to a non-neighbor",
     "fault_class": "invalid parent",
     "counterexample": (3, [(0, 1)], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D11"], "is_equivalent": False},
    {"id": "D12", "problem": "dynamic_dfs",
     "description": "discover time not incremented (duplicate times)",
     "fault_class": "off-by-one (timing)",
     "counterexample": (2, [(0, 1)], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D12"], "is_equivalent": False},
    {"id": "D13", "problem": "dynamic_dfs",
     "description": "rebuild from the stale (pre-update) graph",
     "fault_class": "stale state",
     "counterexample": (3, [(0, 1), (0, 2), (1, 2)], ("delete", (1, 2))),
     "overrides": _DFS_FAULT_OVERRIDES["D13"], "is_equivalent": False},
    {"id": "D14", "problem": "dynamic_dfs",
     "description": "finish time == discover time",
     "fault_class": "off-by-one (timing)",
     "counterexample": (2, [(0, 1)], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D14"], "is_equivalent": False},
    {"id": "D15", "problem": "dynamic_dfs",
     "description": "rebuild ignoring the inserted edge",
     "fault_class": "missed update on insert",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _DFS_FAULT_OVERRIDES["D15"], "is_equivalent": False},
    {"id": "D16", "problem": "dynamic_dfs",
     "description": "parent is a shallower tree ancestor, not the discovering vertex",
     "fault_class": "wrong tree (valid times)",
     "counterexample": (3, [(0, 1), (0, 2), (1, 2)], "init"),
     "overrides": _DFS_FAULT_OVERRIDES["D16"], "is_equivalent": False},
    # ---- BFS ----
    {"id": "B1", "problem": "dynamic_bfs",
     "description": "missed update on delete (tree-edge deletion treated as no-op)",
     "fault_class": "stale tree",
     "counterexample": (2, [(0, 1)], ("delete", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B1"], "is_equivalent": False},
    {"id": "B2", "problem": "dynamic_bfs",
     "description": "missed update on insert (distance-shortening edge ignored)",
     "fault_class": "missed update on insert",
     "counterexample": (3, [(0, 1), (1, 2)], ("insert", (0, 2))),
     "overrides": _BFS_FAULT_OVERRIDES["B2"], "is_equivalent": False},
    {"id": "B3", "problem": "dynamic_bfs",
     "description": "inverted distance-shortening test",
     "fault_class": "wrong predicate",
     "counterexample": (3, [(0, 1), (1, 2)], ("insert", (0, 2))),
     "overrides": _BFS_FAULT_OVERRIDES["B3"], "is_equivalent": False},
    {"id": "B4", "problem": "dynamic_bfs",
     "description": "off-by-one in distance (no +1)",
     "fault_class": "off-by-one",
     "counterexample": (3, [(0, 1), (1, 2)], ("insert", (0, 2))),
     "overrides": _BFS_FAULT_OVERRIDES["B4"], "is_equivalent": False},
    {"id": "B5", "problem": "dynamic_bfs",
     "description": "off-by-one: recompute skips last vertex",
     "fault_class": "off-by-one",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B5"], "is_equivalent": False},
    {"id": "B6", "problem": "dynamic_bfs",
     "description": "root assigned a parent",
     "fault_class": "invalid root",
     "counterexample": (2, [], "init"),
     "overrides": _BFS_FAULT_OVERRIDES["B6"], "is_equivalent": False},
    {"id": "B7", "problem": "dynamic_bfs",
     "description": "recompute follows reverse edges",
     "fault_class": "ignores direction",
     "counterexample": (2, [(0, 1)], "init"),
     "overrides": _BFS_FAULT_OVERRIDES["B7"], "is_equivalent": False},
    {"id": "B8", "problem": "dynamic_bfs",
     "description": "insert is a no-op (never rebuild on insert)",
     "fault_class": "missed update on insert",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B8"], "is_equivalent": False},
    {"id": "B9", "problem": "dynamic_bfs",
     "description": "parent points to a non-neighbor",
     "fault_class": "invalid parent",
     "counterexample": (3, [(0, 1)], "init"),
     "overrides": _BFS_FAULT_OVERRIDES["B9"], "is_equivalent": False},
    {"id": "B10", "problem": "dynamic_bfs",
     "description": "forget to add a newly-reachable vertex",
     "fault_class": "missed update on insert",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B10"], "is_equivalent": False},
    {"id": "B11", "problem": "dynamic_bfs",
     "description": "wrong root (1 instead of 0)",
     "fault_class": "wrong root",
     "counterexample": (2, [], ("insert", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B11"], "is_equivalent": False},
    {"id": "B12", "problem": "dynamic_bfs",
     "description": "descending neighbour order (valid variant, not a bug)",
     "fault_class": "equivalent control",
     "counterexample": None,
     "overrides": _BFS_FAULT_OVERRIDES["B12"], "is_equivalent": True},
    {"id": "B13", "problem": "dynamic_bfs",
     "description": "rebuild from the stale (pre-update) graph",
     "fault_class": "stale state",
     "counterexample": (2, [(0, 1)], ("delete", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B13"], "is_equivalent": False},
    {"id": "B14", "problem": "dynamic_bfs",
     "description": "parent at wrong BFS level",
     "fault_class": "invalid parent",
     "counterexample": (3, [(0, 1)], "init"),
     "overrides": _BFS_FAULT_OVERRIDES["B14"], "is_equivalent": False},
    {"id": "B15", "problem": "dynamic_bfs",
     "description": "recompute treats the graph as undirected",
     "fault_class": "ignores direction",
     "counterexample": (2, [(0, 1), (1, 0)], ("delete", (0, 1))),
     "overrides": _BFS_FAULT_OVERRIDES["B15"], "is_equivalent": False},
]

FAULTS: list[dict] = _FAULTS


def faults_for(problem_name: str) -> list[dict]:
    """Return the fault entries for a rooted problem (BFS or DFS)."""
    return [f for f in FAULTS if f["problem"] == problem_name]


def real_faults(problem_name: str) -> list[dict]:
    """Return only the non-equivalent (real) faults for a problem."""
    return [f for f in faults_for(problem_name) if not f["is_equivalent"]]


def equivalent_controls(problem_name: str) -> list[dict]:
    """Return the equivalent-control entries for a problem."""
    return [f for f in faults_for(problem_name) if f["is_equivalent"]]


def compose_fault_code(problem_name: str, fault: dict) -> str:
    """Return the self-contained candidate source for a fault.

    Assembles the known-good reference blocks with the fault's overrides
    applied, so each fault is a clean diff against the known-good.
    """
    blocks, order = reference_blocks(problem_name)
    return _assemble(blocks, order, overrides=fault["overrides"])


def counterexample_graph(fault: dict) -> tuple[int, list[list[int]]]:
    """Return (n, base adjacency list-of-lists) for a fault's counterexample.

    Raises ValueError for equivalent controls (no counterexample).
    """
    ce = fault["counterexample"]
    if ce is None:
        raise ValueError(f"fault {fault['id']} has no counterexample (equivalent control)")
    n, edges, _op = ce
    g = [[0] * n for _ in range(n)]
    for u, v in edges:
        g[u][v] = 1
    return n, g
