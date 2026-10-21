"""Dynamic LexBFS ordering.

Strategy: maintain a LexBFS ordering. On each edge update, try to repair the
existing ordering locally; if the repair fails, fall back to a full
recomputation (which is always correct).

Repair idea:
- Insertion (u,v): the only way the old ordering can become invalid is that
  some vertex x that was adjacent to u but not to v now has u as its first
  neighbor in the ordering while v comes before u.  We can fix this by moving
  v to just before u (and shifting the vertices in between).  If the move
  keeps the ordering valid, we are done in O(n^2); otherwise recompute.
- Deletion (u,v): the only way the old ordering can become invalid is that
  some vertex x had v as its first neighbor and u was the witness for x
  (i.e. u < v, u-x not in E, v-x in E).  We can fix this by moving u to just
  before v.  If the move keeps the ordering valid, done; otherwise recompute.

Validity is checked with the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static O(n^2) LexBFS on an adjacency matrix. Returns ordering list."""
    n = len(graph)
    # label[v] = list of vertices (in order) that are neighbors of v and
    # already ordered; two vertices are in the same class iff their labels
    # are equal.  We keep classes as lists of vertices in current order.
    # Use the standard partition-refinement with a queue of classes.
    #
    # Simpler correct approach: maintain for each vertex v a list L(v) of
    # ordered neighbors of v (in order).  Classes = groups of unvisited vertices
    # with identical L(v).  We implement with explicit class lists and
    # a queue of classes to refine.

    # label[v] = tuple of ordered neighbors of v (in order)
    label = [[] for _ in range(n)]
    # classes: list of lists of unvisited vertices, in current order
    classes = [[v for v in range(n)]]
    # queue of class indices to process
    from collections import deque
    q = deque([0])
    ordered = []

    while q:
        ci = q.popleft()
        if ci >= len(classes) or not classes[ci]:
            continue
        # take the first vertex of the class
        x = classes[ci].pop(0)
        ordered.append(x)
        # refine: for each class, split off vertices adjacent to x
        new_classes = []
        for cj, cls in enumerate(classes):
            if not cls:
                continue
            adj = [v for v in cls if graph[x][v]]
            non = [v for v in cls if not graph[x][v]]
            if adj:
                new_classes.append(adj)
                q.append(len(new_classes) - 1)
            if non:
                new_classes.append(non)
                q.append(len(new_classes) - 1)
        classes = new_classes
    return ordered


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property. Returns True iff order is a valid
    LexBFS ordering of graph."""
    n = len(order)
    # For each pair (b, c) with pos[b] < pos[c] and b-c not in E:
    #   A = {a : pos[a] < pos[b], a-c in E}
    #   S = {d : pos[d] < pos[c], d-b in E, d-c not in E}
    #   Need: if A nonempty, then S nonempty and min(S) < min(A).
    for bi in range(n):
        b = order[bi]
        for ci in range(bi + 1, n):
            c = order[ci]
            if graph[b][c]:
                continue
            # b before c, non-edge
            min_a = None
            for ai in range(bi):
                a = order[ai]
                if graph[a][c]:
                    min_a = ai
                    break
            if min_a is None:
                continue
            min_s = None
            for di in range(ci):
                d = order[di]
                if graph[d][b] and not graph[d][c]:
                    min_s = di
                    break
            if min_s is None or min_s >= min_a:
                return False
    return True


def _try_move(order, src, dst):
    """Return a new order with the vertex at index src moved to index dst
    (inserted before the vertex currently at dst)."""
    v = order[src]
    rest = order[:src] + order[src + 1:]
    if dst > src:
        dst -= 1
    return rest[:dst] + [v] + rest[dst:]


def _repair_insert(graph, order, u, v):
    """Try to repair after inserting edge (u,v). Returns new order or None."""
    n = len(order)
    pos = {x: i for i, x in enumerate(order)}
    pu, pv = pos[u], pos[v]
    if pu < pv:
        # u before v. Problem: some x with x-u edge, x-v non-edge, and u is
        # the first neighbor of x in the ordering, while v is before u.
        # Fix: move v to just before u.
        new_order = _try_move(order, pv, pu)
        if _is_valid_lexbfs(graph, new_order):
            return new_order
        return None
    else:
        # v before u. Problem: some x with x-v edge, x-u non-edge, v first
        # neighbor of x, u before v. Fix: move u to just before v.
        new_order = _try_move(order, pu, pv)
        if _is_valid_lexbfs(graph, new_order):
            return new_order
        return None


def _repair_delete(graph, order, u, v):
    """Try to repair after deleting edge (u,v). Returns new order or None."""
    n = len(order)
    pos = {x: i for i, x in enumerate(order)}
    pu, pv = pos[u], pos[v]
    if pu < pv:
        # u before v. Problem: some x with x-v edge, x-u non-edge, v first
        # neighbor of x, and u was the witness (u before v, u-x non-edge,
        # v-x edge). Fix: move u to just before v.
        new_order = _try_move(order, pu, pv)
        if _is_valid_lexbfs(graph, new_order):
            return new_order
        return None
    else:
        # v before u. Fix: move v to just before u.
        new_order = _try_move(order, pv, pu)
        if _is_valid_lexbfs(graph, new_order):
            return new_order
        return None


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    new_order = _repair_insert(graph, order, u, v)
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    new_order = _repair_delete(graph, order, u, v)
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order}
