"""Known-good reference candidates for the verifier self-test.

Two honest references per rooted problem (BFS, DFS), each a self-contained
candidate module (``init`` / ``insert_edge`` / ``delete_edge``) that the
sandbox can exec:

- **known-good** -- a *validate-or-rebuild* dynamic algorithm. On each update
  it checks whether the maintained certificate stays valid; if not, it rebuilds
  from scratch (offline BFS/DFS). For DFS the validity decision is informed by
  Yang et al. Lemma 1 (a search spanning tree is a DFS tree iff it has no
  forward-cross edge): a forward-cross insert or a tree-edge delete forces a
  rebuild, everything else is kept. This is genuinely dynamic (recompute rate
  ~40% over the small universe, well below the recompute-always baseline), not
  a recompute-always wrapper. It is labelled "Yang Lemma-1 informed
  validate-or-rebuild", NOT "Yang's algorithm" -- Yang's contribution is the
  Lemma-1 characterization plus the interval machinery that makes the *check*
  cheap; this reference uses that characterization for the keep/rebuild
  decision but falls back to a full rebuild instead of Yang's ConstrainedDFS
  partial repair.
- **control** -- an *equivalent* valid variant: the same validate-or-rebuild
  structure but with a different tie-break (descending neighbour order in the
  offline rebuild). It produces a different (but valid) tree/forest than the
  known-good. The verifier must accept it -- this proves the checker is
  invariant-based and not biased to one tie-break.

The references are assembled from named code blocks so the fault corpus
(:mod:`evoalgo.selftest.faults`) can inject a one-line mutation by overriding a
single block, keeping each fault a clean, reviewable diff against the
known-good.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# DFS blocks (root = 0; certificate = parent + discover + finish)
# ---------------------------------------------------------------------------

_DFS_BLOCKS: dict[str, str] = {
    "recompute": '''
def _recompute(graph):
    """Offline DFS from root 0, ascending neighbour order."""
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
    return {"parent": parent, "discover": discover, "finish": finish}
''',
    "is_desc": '''
def _is_desc(state, a, b):
    """b is a strict descendant of a iff discover[a] < discover[b] < finish[b] < finish[a]."""
    d, f = state["discover"], state["finish"]
    if a not in d or b not in d:
        return False
    return d[a] < d[b] < f[b] < f[a]
''',
    "is_tree": '''
def _is_tree(state, s, t):
    return state["parent"].get(t) == s
''',
    "init": '''
def init(graph):
    return _recompute(graph)
''',
    "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    d = state["discover"]
    # t newly reachable (was unreachable, s reachable) -> rebuild
    if t not in d and s in d:
        return _recompute(graph)
    # (s, t) is a forward-cross edge -> rebuild (Yang Lemma 1)
    if t in d and s in d and d[s] < d[t] and not _is_desc(state, s, t):
        return _recompute(graph)
    # back edge / forward edge / s unreachable -> forest stays valid
    return state
''',
    "delete": '''
def delete_edge(graph, edge, state):
    s, t = edge
    # deleting a tree edge breaks the spanning structure -> rebuild
    if _is_tree(state, s, t):
        return _recompute(graph)
    # non-tree edge deletion cannot create a forward-cross edge
    return state
''',
    # D5 helper: rebuild parent but keep the OLD discover/finish (stale times)
    "recompute_stale": '''
def _recompute_stale(graph, old):
    fresh = _recompute(graph)
    fresh["discover"] = old["discover"]
    fresh["finish"] = old["finish"]
    return fresh
''',
}

_DFS_BLOCK_ORDER = ["recompute", "is_desc", "is_tree", "init", "insert", "delete"]

# ---------------------------------------------------------------------------
# BFS blocks (root = 0; certificate = parent + distances)
# ---------------------------------------------------------------------------

_BFS_BLOCKS: dict[str, str] = {
    "recompute": '''
def _recompute(graph):
    """Offline BFS from root 0, ascending neighbour order."""
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
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
''',
    "init": '''
def init(graph):
    return _recompute(graph)
''',
    "insert": '''
def insert_edge(graph, edge, state):
    s, t = edge
    dist = state["distances"]
    if t in dist:
        # new edge can only shorten t's distance
        if s in dist and dist[s] + 1 < dist[t]:
            return _recompute(graph)
        return state
    else:
        # t was unreachable; if s reachable, t becomes reachable
        if s in dist:
            return _recompute(graph)
        return state
''',
    "delete": '''
def delete_edge(graph, edge, state):
    s, t = edge
    # (s, t) is a tree edge -> t's distance may increase -> rebuild
    if state["parent"].get(t) == s:
        return _recompute(graph)
    # non-tree edge deletion cannot increase BFS distances
    return state
''',
}

_BFS_BLOCK_ORDER = ["recompute", "init", "insert", "delete"]

# ---------------------------------------------------------------------------
# Equivalent controls (different tie-break, same validate-or-rebuild shape)
# ---------------------------------------------------------------------------

# DFS control: descending neighbour order in the offline rebuild. Produces a
# different (but valid) DFS forest than the ascending known-good.
_DFS_CONTROL_OVERRIDES = {
    "recompute": '''
def _recompute(graph):
    """Offline DFS from root 0, DESCENDING neighbour order (equivalent control)."""
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
}

# BFS control: descending neighbour order in the offline rebuild. Produces a
# different (but valid) BFS tree than the ascending known-good.
_BFS_CONTROL_OVERRIDES = {
    "recompute": '''
def _recompute(graph):
    """Offline BFS from root 0, DESCENDING neighbour order (equivalent control)."""
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
}


def _assemble(blocks: dict[str, str], order: list[str],
              overrides: dict[str, str] | None = None) -> str:
    """Concatenate blocks in order, applying overrides, with a header."""
    overrides = overrides or {}
    merged = dict(blocks)
    merged.update(overrides)
    parts = [merged[name] for name in order if name in merged]
    # include any override-only blocks (e.g. helpers) not in the base order
    for name in overrides:
        if name not in order:
            parts.append(merged[name])
    return "\n".join(parts).strip() + "\n"


def reference_code(problem_name: str, control: bool = False) -> str:
    """Return the self-contained candidate source for a reference.

    ``problem_name`` is ``dynamic_bfs`` or ``dynamic_dfs``. ``control=True``
    returns the equivalent (different tie-break) variant; ``False`` returns the
    known-good.
    """
    if problem_name == "dynamic_dfs":
        overrides = _DFS_CONTROL_OVERRIDES if control else None
        return _assemble(_DFS_BLOCKS, _DFS_BLOCK_ORDER, overrides)
    if problem_name == "dynamic_bfs":
        overrides = _BFS_CONTROL_OVERRIDES if control else None
        return _assemble(_BFS_BLOCKS, _BFS_BLOCK_ORDER, overrides)
    raise ValueError(f"No reference for problem: {problem_name}")


def reference_blocks(problem_name: str) -> tuple[dict[str, str], list[str]]:
    """Return (blocks, order) for a rooted problem, for fault composition."""
    if problem_name == "dynamic_dfs":
        return _DFS_BLOCKS, _DFS_BLOCK_ORDER
    if problem_name == "dynamic_bfs":
        return _BFS_BLOCKS, _BFS_BLOCK_ORDER
    raise ValueError(f"No reference blocks for problem: {problem_name}")


def reference_functions(problem_name: str) -> tuple:
    """Return the in-process (init, insert_edge, delete_edge) of the known-good.

    Used by tests to exercise the reference without the sandbox. The functions
    operate on plain list-of-lists graphs (as the sandbox passes them).
    """
    ns: dict = {}
    exec(compile(reference_code(problem_name), "<reference>", "exec"), ns)
    return ns["init"], ns["insert_edge"], ns["delete_edge"]


# Convenience: the known-good source for each rooted problem.
REFERENCE_CODE = {
    "dynamic_bfs": reference_code("dynamic_bfs"),
    "dynamic_dfs": reference_code("dynamic_dfs"),
}
