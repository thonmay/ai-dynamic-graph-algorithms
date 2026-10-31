# AI-assisted code: generated and revised with Claude Opus 5.5 and Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Known-good reference candidates for the verifier self-test.

Two honest references per corpus problem (BFS, DFS, LBFS), each a self-contained
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
  offline BFS/DFS rebuild; for LBFS the highest start vertex and maximum-id
  ties). It produces a different (but valid) output than the known-good. The
  verifier must accept it -- this proves the checker is invariant-based and
  not biased to one tie-break.

The LBFS reference keeps the ordering while it still satisfies the (LB)
property and otherwise rebuilds by partition refinement (see the LBFS blocks).

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


# ---------------------------------------------------------------------------
# LBFS blocks (undirected, any start; certificate = the ordering)
# ---------------------------------------------------------------------------
#
# Validate-or-rebuild, like BFS/DFS: an update keeps the ordering while it is
# still a LexBFS ordering of the new graph, else rebuilds by partition
# refinement (Habib et al. 2000). _is_lexbfs is the (LB) 4-point property the
# verifier checks (Corneil & Krueger 2008); it agrees with the verifier's
# check on all 124,469 orderings of the labelled graphs with n <= 5.

_LBFS_BLOCKS: dict[str, str] = {
    "recompute": '''
def _recompute(graph):
    """LexBFS by partition refinement from vertex 0, minimum-id tie-break."""
    n = len(graph)
    cells = [list(range(n))] if n else []
    order = []
    while cells:
        p = cells[0].pop(0)
        order.append(p)
        refined = []
        for cell in cells:
            inside = [u for u in cell if graph[p][u]]
            outside = [u for u in cell if not graph[p][u]]
            refined.extend(c for c in (inside, outside) if c)
        cells = refined
    return order
''',
    "is_lexbfs": '''
def _is_lexbfs(graph, order):
    """(LB) 4-point property: for positions a < b < c with ac an edge and ab
    not, some d before a is adjacent to b and not to c."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                if not any(graph[d][b] and not graph[d][c] for d in order[:i]):
                    return False
    return True
''',
    "init": '''
def init(graph):
    return {"ordering": _recompute(graph)}
''',
    "insert": '''
def insert_edge(graph, edge, state):
    # Keep the ordering while it is still a LexBFS ordering, else rebuild.
    if _is_lexbfs(graph, state["ordering"]):
        return state
    return {"ordering": _recompute(graph)}
''',
    "delete": '''
def delete_edge(graph, edge, state):
    if _is_lexbfs(graph, state["ordering"]):
        return state
    return {"ordering": _recompute(graph)}
''',
}

_LBFS_BLOCK_ORDER = ["recompute", "is_lexbfs", "init", "insert", "delete"]

# LBFS control: start at vertex n-1 with the maximum-id tie-break. A different
# (but valid) LexBFS ordering than the known-good.
_LBFS_CONTROL_OVERRIDES = {
    "recompute": _LBFS_BLOCKS["recompute"]
    .replace("from vertex 0, minimum-id tie-break.", "from vertex n-1, maximum-id tie-break (equivalent control).")
    .replace("cells = [list(range(n))] if n else []", "cells = [list(range(n - 1, -1, -1))] if n else []"),
}

_BLOCK_SETS = {
    "dynamic_dfs": (_DFS_BLOCKS, _DFS_BLOCK_ORDER, _DFS_CONTROL_OVERRIDES),
    "dynamic_bfs": (_BFS_BLOCKS, _BFS_BLOCK_ORDER, _BFS_CONTROL_OVERRIDES),
    "dynamic_lbfs": (_LBFS_BLOCKS, _LBFS_BLOCK_ORDER, _LBFS_CONTROL_OVERRIDES),
}

# Problems with a reference, fault corpus and equivalent control.
CORPUS_PROBLEMS = tuple(_BLOCK_SETS)


# ---------------------------------------------------------------------------
# Yang et al. fully dynamic DFS (VLDB 2019), basic algorithms
# ---------------------------------------------------------------------------
#
# Algorithm 2 (framework) + 3 (ConstrainedDFS) + 4 (DFS-Insert) + 5
# (DFS-Delete), as in Section 4-5 of the paper. A virtual root G (-1) points
# to every vertex, so the tree spans all vertices; vertex 0 is G's first
# child, so the subtree of 0 is exactly the set reachable from 0 (a vertex
# reachable from 0 outside it would give a forward-cross edge, Lemma 1).
# Intervals: L/R are the discovery/finish timestamps of the whole tree, one
# shared counter. ConstrainedDFS iterates neighbours in order of their old
# discovery time, so the unchanged tree path from the search root to
# T[CI.left] is walked first and keeps its timestamps. The paper does not
# state an order (it keeps children lists); this choice is ours, and it is
# needed: mutation Y7 (plain vertex order) breaks the tree over update
# sequences.
# Not included: the Section 6 optimizations (refined candidate intervals).

YANG_DFS_CODE = '''
G = -1  # virtual root, an in-neighbour of every vertex


def _out(graph, u):
    n = len(graph)
    if u == G:
        return range(n)
    return [v for v in range(n) if v != u and graph[u][v] == 1]


def _report(st):
    """The checked certificate: G's children (0 among them) have no parent."""
    n = len(st["_L"]) - 1
    return {"parent": {v: (None if st["_P"][v] == G else st["_P"][v]) for v in range(n)},
            "discover": {v: st["_L"][v] for v in range(n)},
            "finish": {v: st["_R"][v] for v in range(n)},
            "_P": st["_P"], "_L": st["_L"], "_R": st["_R"]}


def init(graph):
    """Static DFS from G, visiting 0 first, then the rest in vertex order."""
    P, L, R, ts = {G: None}, {}, {}, [0]

    def dfs(u):
        L[u] = ts[0]; ts[0] += 1
        for v in ([0] + [w for w in range(1, len(graph))] if u == G else _out(graph, u)):
            if v not in L:
                P[v] = u
                dfs(v)
        R[u] = ts[0]; ts[0] += 1

    dfs(G)
    return _report({"_P": P, "_L": L, "_R": R})


def _constrained_dfs(graph, st, root, cl, cr):
    """Algorithms 2+3: re-run DFS from root over T(CI), CI = [cl, cr]."""
    P, L0, R0 = dict(st["_P"]), st["_L"], st["_R"]
    L, R = dict(L0), dict(R0)
    in_ci = {v for v in L0 if cl <= L0[v] <= cr or cl <= R0[v] <= cr}
    visited, ts = set(), [cl]

    def cdfs(u):
        visited.add(u)
        if L0[u] >= cl:
            L[u] = ts[0]; ts[0] += 1
        for v in sorted((w for w in _out(graph, u) if w in in_ci), key=L0.get):
            if v in visited:
                continue
            if L0[v] >= cl:
                P[v] = u  # v becomes the next child of u
            cdfs(v)
        if R0[u] <= cr:
            R[u] = ts[0]; ts[0] += 1

    cdfs(root)
    return _report({"_P": P, "_L": L, "_R": R})


def _lca(st, a, b):
    P, anc = st["_P"], set()
    while a is not None:
        anc.add(a)
        a = P[a]
    while b not in anc:
        b = P[b]
    return b


def insert_edge(graph, edge, state):
    """Algorithm 4 (DFS-Insert)."""
    s, t = edge
    L, R = state["_L"], state["_R"]
    if s == t or R[s] > L[t]:  # not a forward-cross edge: tree stays valid
        return state
    r = _lca(state, s, t)
    return _constrained_dfs(graph, state, r, R[s], R[r])


def delete_edge(graph, edge, state):
    """Algorithm 5 (DFS-Delete)."""
    s, t = edge
    if state["_P"].get(t) != s:  # non-tree edge: tree stays valid
        return state
    return _constrained_dfs(graph, state, G, state["_L"][t], state["_R"][G])
'''


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

    ``problem_name`` is one of ``CORPUS_PROBLEMS``. ``control=True`` returns
    the equivalent (different tie-break) variant; ``False`` returns the
    known-good.
    """
    if problem_name not in _BLOCK_SETS:
        raise ValueError(f"No reference for problem: {problem_name}")
    blocks, order, control_overrides = _BLOCK_SETS[problem_name]
    return _assemble(blocks, order, control_overrides if control else None)


def reference_blocks(problem_name: str) -> tuple[dict[str, str], list[str]]:
    """Return (blocks, order) for a corpus problem, for fault composition."""
    if problem_name not in _BLOCK_SETS:
        raise ValueError(f"No reference blocks for problem: {problem_name}")
    blocks, order, _ = _BLOCK_SETS[problem_name]
    return blocks, order


def reference_functions(problem_name: str) -> tuple:
    """Return the in-process (init, insert_edge, delete_edge) of the known-good.

    Used by tests to exercise the reference without the sandbox. The functions
    operate on plain list-of-lists graphs (as the sandbox passes them).
    """
    ns: dict = {}
    exec(compile(reference_code(problem_name), "<reference>", "exec"), ns)
    return ns["init"], ns["insert_edge"], ns["delete_edge"]


# Mutations of the Yang reference (one textual change each) with the
# smallest counterexample found by exhaustive search over n <= 5 single
# updates; ``None`` means no single update breaks it and it only shows over
# update sequences (Y7; the n <= 5 self-test catches it through its
# multi-step sequences).
YANG_DFS_MUTATIONS: list[dict] = [
    {"id": "Y1", "description": "insert: candidate interval ends at R[s], not R[LCA]",
     "old": "return _constrained_dfs(graph, state, r, R[s], R[r])",
     "new": "return _constrained_dfs(graph, state, r, R[s], R[s])",
     "counterexample": (2, [], ("insert", (0, 1)))},
    {"id": "Y2", "description": "insert: search root t instead of LCA(s, t)",
     "old": "    r = _lca(state, s, t)\n", "new": "    r = t\n",
     "counterexample": (2, [], ("insert", (0, 1)))},
    {"id": "Y3", "description": "insert: forward-cross test inverted",
     "old": "if s == t or R[s] > L[t]:", "new": "if s == t or R[s] < L[t]:",
     "counterexample": (2, [], ("insert", (0, 1)))},
    {"id": "Y4", "description": "delete: candidate interval starts at R[t], not L[t]",
     "old": 'state["_L"][t], state["_R"][G])', "new": 'state["_R"][t], state["_R"][G])',
     "counterexample": (3, [(0, 1), (0, 2), (2, 1)], ("delete", (0, 1)))},
    {"id": "Y5", "description": "ConstrainedDFS ignores the interval constraint on neighbours",
     "old": "if w in in_ci), key=L0.get)", "new": "), key=L0.get)",
     "counterexample": (5, [(0, 1), (1, 2), (1, 3), (1, 4)], ("insert", (3, 4)))},
    {"id": "Y6", "description": "ConstrainedDFS keeps the old parent (no reassignment)",
     "old": "                P[v] = u  # v becomes the next child of u\n", "new": "                pass\n",
     "counterexample": (2, [], ("insert", (0, 1)))},
    {"id": "Y7", "description": "ConstrainedDFS visits neighbours in vertex order, not old discovery order",
     "old": "key=L0.get)", "new": "key=lambda w: w)",
     "counterexample": None},
]


def yang_mutation_code(mutation: dict) -> str:
    code = YANG_DFS_CODE.replace(mutation["old"], mutation["new"], 1)
    if code == YANG_DFS_CODE:
        raise ValueError(f"mutation {mutation['id']} does not apply")
    return code


# Convenience: the known-good source for each corpus problem.
REFERENCE_CODE = {name: reference_code(name) for name in CORPUS_PROBLEMS}
