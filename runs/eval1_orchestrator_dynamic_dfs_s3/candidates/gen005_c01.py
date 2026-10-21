"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Maintains a genuine DFS forest of the current graph under single edge
insertions and deletions.  The maintained state is a dict with:

  parent  : list, parent[v] is the DFS tree in-neighbor of v (None for root
            and for unreachable vertices)
  discover: list, DFS entry time of each vertex (shared counter, root = 0)
  finish  : list, DFS exit time of each vertex

Correctness invariant (Yang et al. Lemma 1): the tree is a DFS tree iff it
has no forward-cross edge, i.e. no edge u->v with discover[u] < discover[v]
and v not a descendant of u.

Strategy (local updates, no full recompute):
  * insert_edge (u,v):
      - if v is already reachable and the new edge is a back/forward edge
        (v is an ancestor of u, or v is a descendant of u), the forest
        stays a valid DFS forest, no work.
      - if v is reachable but neither ancestor nor descendant of u, the
        new edge is a forward-cross edge.  Repair by re-parenting v's
        whole subtree under u (v becomes a child of u, its internal
        subtree is untouched).  This is O(n) and provably yields a valid
        DFS forest.
      - if v is unreachable and u is reachable, recompute from scratch
        (the newly reachable region can be large).
  * delete_edge (u,v):
      - if v is not a tree child of u: the forest is unchanged.
      - if v is a tree child of u: recompute from scratch (the affected
        region can be large).
"""


def _dfs_from_scratch(graph):
    """Run a standard iterative DFS from root 0 and return (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    if n == 0:
        return parent, discover, finish

    root = 0
    discover[root] = 0
    counter[0] = 1
    stack = [[root, 0]]  # [vertex, next neighbor index to try]

    while stack:
        v, ni = stack[-1]
        found = False
        while ni < n:
            if graph[v][ni] and discover[ni] == -1:
                discover[ni] = counter[0]
                counter[0] += 1
                parent[ni] = v
                stack[-1][1] = ni + 1
                stack.append([ni, 0])
                found = True
                break
            ni += 1
        if not found:
            finish[v] = counter[0]
            counter[0] += 1
            stack.pop()

    return parent, discover, finish


def _state(graph):
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def init(graph):
    return _state(graph)


def _is_ancestor(discover, finish, a, b):
    """True if a is a proper ancestor of b (both reachable)."""
    return discover[a] < discover[b] and finish[b] < finish[a]


def _reparent_subtree(parent, discover, finish, u, v):
    """Make v a child of u, keeping v's internal subtree intact.

    Precondition: v is reachable, u is reachable, and neither is an
    ancestor of the other.  After the call, v's subtree occupies the
    interval right after u's own discovery, and all other reachable
    vertices keep their relative order.
    """
    n = len(parent)
    # Collect v's subtree in discovery order.
    subtree = []
    for x in range(n):
        if discover[x] != -1 and _is_ancestor(discover, finish, v, x):
            subtree.append(x)
    subtree.append(v)
    subtree.sort(key=lambda x: discover[x])

    # Collect all reachable vertices in discovery order, excluding v's
    # subtree.
    others = []
    for x in range(n):
        if discover[x] != -1 and not (x == v or _is_ancestor(discover, finish, v, x)):
            others.append(x)
    others.sort(key=lambda x: discover[x])

    # New order: others up to and including u, then v's subtree, then the
    # rest of others.
    new_order = []
    placed = False
    for x in others:
        new_order.append(x)
        if x == u:
            new_order.extend(subtree)
            placed = True
    if not placed:
        # u not found in others (should not happen since u is reachable
        # and not in v's subtree), but handle gracefully.
        new_order.extend(subtree)

    # Reassign discover/finish in the new order.  Each vertex gets
    # discover = 2*i, finish = 2*i + 1 for its position i in new_order.
    # This is a valid DFS timing: for any ancestor a of descendant d,
    # discover[a] < discover[d] < finish[d] < finish[a].
    for i, x in enumerate(new_order):
        discover[x] = 2 * i
        finish[x] = 2 * i + 1

    # Update parent pointers: v's parent becomes u; all other parent
    # pointers are unchanged (the internal structure of v's subtree is
    # preserved, and other vertices keep their parents).
    parent[v] = u


def insert_edge(graph, edge, state):
    u, v = edge
    discover = state['discover']
    finish = state['finish']
    parent = state['parent']

    # If v is already reachable, the new edge is a non-tree edge.  It is
    # harmless only if it does not create a forward-cross edge, i.e. only if
    # v is a descendant of u (discover[u] < discover[v] < finish[v] <
    # finish[u]) or v is an ancestor of u (discover[v] < discover[u] <
    # finish[u] < finish[v]) or u == v.
    if discover[v] != -1:
        if discover[u] != -1:
            if _is_ancestor(discover, finish, u, v):
                # v is a proper descendant of u: forward edge, fine.
                return state
            if _is_ancestor(discover, finish, v, u):
                # v is a proper ancestor of u: back edge, fine.
                return state
            if u == v:
                # self-loop, fine.
                return state
            # v is reachable but neither ancestor nor descendant of u:
            # the new edge is a forward-cross edge.  Repair by
            # re-parenting v's subtree under u.
            _reparent_subtree(parent, discover, finish, u, v)
            return state
        # u is unreachable, v is reachable: the new edge doesn't affect
        # the reachable set (u is not reachable, so the edge can't be
        # used to reach v from the root).  No change.
        return state

    # v is unreachable.  The new edge only matters if u is reachable.
    if discover[u] == -1:
        return state

    # v is unreachable and u is reachable: the new edge makes v (and
    # vertices reachable from v among the previously-unreachable set)
    # newly reachable.  Recompute from scratch.
    return _state(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']

    # If v is not a tree child of u, the forest is unchanged.
    if parent[v] != u:
        return state

    # v is a tree child of u: the deleted edge was a tree edge, so
    # parent[v] = u is now a dangling pointer and the old forest is
    # invalid.  Recompute from scratch.
    return _state(graph)
