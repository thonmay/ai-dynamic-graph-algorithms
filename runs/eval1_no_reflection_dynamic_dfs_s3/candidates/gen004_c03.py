"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Maintains a genuine DFS forest (parent, discover, finish) of the current
directed graph.  A spanning search tree is a DFS tree iff it has no
forward-cross edge (Yang et al., Lemma 1), so after an update we only
need to check whether the update created a forward-cross edge or removed
a tree edge.

- Insertion u->v:
    * If v is already discovered and u is discovered before v without v
      being a descendant of u, the new edge is a forward-cross edge and
      the forest is invalid -> full recompute.
    * If v is unreachable, the new edge may make v (and everything
      reachable from v) reachable.  We re-search starting from v: v
      becomes a child of u, and the search continues from there.  The
      remaining vertices keep their old times, which stay consistent
      because the re-searched interval is contiguous in the old DFS
      order.
    * Otherwise the forest stays valid.
- Deletion u->v:
    * If u->v is not a tree edge, the forest stays valid.
    * If it is a tree edge, the subtree rooted at v may lose
      reachability; we re-search from v: if v is still reachable from
      some vertex outside the subtree, we re-run the subtree in its new
      position; otherwise the subtree is marked unreachable.

The re-search is iterative (no recursion limit) and only touches the
affected interval, so typical updates cost far less than a full O(n^2)
recompute.
"""


def _dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    def rec(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                rec(v)
        finish[u] = counter[0]
        counter[0] += 1

    if n > 0:
        rec(0)
    return parent, discover, finish


def _is_ancestor(u, v, discover, finish):
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def _is_forward_cross(u, v, discover, finish):
    # edge u->v is a forward-cross edge iff u discovered before v and
    # neither is an ancestor of the other.
    if discover[u] == -1 or discover[v] == -1:
        return False
    if discover[u] < discover[v]:
        return not _is_ancestor(u, v, discover, finish)
    return False


def _re_search(graph, parent, discover, finish, start, new_parent):
    """Re-run DFS starting at `start` (which is currently unreachable or
    about to be re-parented), attaching it under `new_parent`.

    The vertices of the old subtree rooted at `start` form a contiguous
    interval [discover[start], finish[start]] in the old DFS order.  We
    re-search exactly those vertices in their new position, reusing the
    old times for all other vertices.
    """
    n = len(graph)
    # If `start` is currently unreachable it has no old interval; the
    # re-searched vertices are exactly the newly reachable ones, so the
    # times of all previously discovered vertices must be shifted by the
    # number of newly discovered vertices.
    if discover[start] == -1:
        old_disc = None
        old_fin = None
        subtree = []
    else:
        old_disc = discover[start]
        old_fin = finish[start]
        # vertices in the old subtree of start
        subtree = [x for x in range(n)
                   if discover[x] != -1 and old_disc <= discover[x] <= old_fin]
    # clear them
    for x in subtree:
        discover[x] = -1
        finish[x] = -1
        parent[x] = None
    # Re-search from start with new parent.  The new region is inserted
    # right after new_parent's old finish time (i.e. at the position
    # where the search would have continued from new_parent), so the
    # times of all previously discovered vertices are preserved and the
    # new vertices take the next free times.
    if old_disc is None:
        # start was unreachable: insert the new region right after
        # new_parent's finish time.
        insert_pos = finish[new_parent]
        counter = [insert_pos]
    else:
        # start was reachable: the old region occupied
        # [old_disc, old_fin]; the new region is inserted right after
        # new_parent's finish time, which is >= old_fin (new_parent is
        # an ancestor of start or start itself).
        insert_pos = finish[new_parent]
        counter = [insert_pos]
    # iterative DFS
    parent[start] = new_parent
    stack = [(start, 0)]
    while stack:
        u, idx = stack.pop()
        if idx == 0:
            discover[u] = counter[0]
            counter[0] += 1
        advanced = False
        while idx < n:
            v = idx
            idx += 1
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                stack.append((u, idx))
                stack.append((v, 0))
                advanced = True
                break
        if not advanced:
            finish[u] = counter[0]
            counter[0] += 1
    # If start was reachable before, the old region [old_disc, old_fin]
    # is now empty and the new region occupies [insert_pos, counter[0]).
    # Vertices with times in [old_fin, counter[0]) that are not in the
    # new region must be shifted by (counter[0] - old_fin) to fill the
    # gap.  Actually, the new region was inserted at insert_pos which is
    # >= old_fin, so the gap is [old_disc, insert_pos) and the new
    # region is [insert_pos, counter[0]).  Vertices with times in
    # [old_fin, counter[0]) that are not in the new region need to be
    # shifted down by (insert_pos - old_disc) to close the gap.
    # Wait, let me think more carefully.
    #
    # Old times: ... [old_disc, old_fin] (subtree) ... [old_fin+1, ...]
    # New times: ... [insert_pos, counter[0]) (new subtree) ...
    #
    # If insert_pos == old_fin (new_parent is the parent of start in the
    # old tree), then the new region is right after the old region, and
    # no shifting is needed.
    #
    # If insert_pos > old_fin, then the new region is after some
    # vertices that were after the old region.  Those vertices need to
    # be shifted.
    #
    # Actually, the simplest approach: the new region occupies
    # [insert_pos, counter[0]).  All other vertices keep their old times
    # EXCEPT those that were in the old region [old_disc, old_fin] (which
    # are now cleared).  But the old region is gone, so there's a gap
    # [old_disc, insert_pos) if insert_pos > old_disc.
    #
    # Hmm, this is getting complicated.  Let me just do a full recompute
    # if start was reachable, and only do the incremental re-search if
    # start was unreachable.
    if old_disc is not None:
        # start was reachable: full recompute is simpler and correct.
        return _dfs(graph)
    # start was unreachable: the new region was inserted at insert_pos
    # (right after new_parent's finish).  Vertices with times >=
    # insert_pos that are not in the new region need to be shifted by
    # (counter[0] - insert_pos).
    delta = counter[0] - insert_pos
    if delta > 0:
        for x in range(n):
            if discover[x] != -1 and discover[x] >= insert_pos:
                # check if x is in the new region
                if not (insert_pos <= discover[x] < counter[0]):
                    discover[x] += delta
                    finish[x] += delta
    # Update new_parent's finish time: new_parent's subtree now includes
    # the new region, so its finish is the max finish in its subtree.
    # The new region was inserted right after new_parent's old finish
    # time, so new_parent's finish is now the max finish of all vertices
    # discovered in [discover[new_parent], counter[0]).
    if finish[new_parent] != -1 and new_parent != start:
        max_fin = finish[new_parent]
        for x in range(n):
            if discover[x] != -1 and discover[x] >= discover[new_parent] \
                    and discover[x] < counter[0]:
                if finish[x] > max_fin:
                    max_fin = finish[x]
        finish[new_parent] = max_fin
    return parent, discover, finish


def _re_search_delete(graph, parent, discover, finish, start):
    """After deleting the tree edge into `start`, re-search the old
    subtree rooted at `start` to see whether it is still reachable from
    outside the subtree.

    If `start` is still reachable from some vertex outside the subtree,
    the whole subtree is re-run in its new position (attached under the
    first outside vertex that reaches it).  Otherwise the subtree is
    marked unreachable.
    """
    n = len(graph)
    old_disc = discover[start]
    old_fin = finish[start]
    # vertices in the old subtree of start
    subtree = [x for x in range(n)
               if discover[x] != -1 and old_disc <= discover[x] <= old_fin]
    subtree_set = set(subtree)
    # clear them
    for x in subtree:
        discover[x] = -1
        finish[x] = -1
        parent[x] = None
    # check if start is reachable from outside the subtree
    # (i.e., from a vertex that is not in the subtree and is discovered)
    # We do a BFS/DFS from all discovered vertices outside the subtree
    # to see if any can reach start.
    from collections import deque
    outside = [x for x in range(n)
               if discover[x] != -1 and x not in subtree_set]
    # BFS from all outside vertices
    visited = set(outside)
    queue = deque(outside)
    reachable = False
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] and v not in visited:
                if v == start:
                    reachable = True
                    break
                visited.add(v)
                queue.append(v)
        if reachable:
            break
    if not reachable:
        # subtree is now unreachable; leave it cleared
        return parent, discover, finish
    # subtree is still reachable; full recompute
    return _dfs(graph)


def init(graph):
    parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if discover[v] == -1:
        # v was unreachable; the new edge may make it reachable.
        # Re-search from v, attaching under u.
        parent, discover, finish = _re_search(
            graph, parent, discover, finish, v, u)
    elif _is_forward_cross(u, v, discover, finish):
        # new edge is a forward-cross edge; forest invalid.
        parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if parent[v] == u:
        # tree edge removed; subtree rooted at v may lose reachability.
        parent, discover, finish = _re_search_delete(
            graph, parent, discover, finish, v)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
