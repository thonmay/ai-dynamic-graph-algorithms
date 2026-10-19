"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

State: (parent, disc, fin, order)
  parent[v]: tree parent of v, or -1 if v is undiscovered (or is the root).
  disc[v]: 0-based discovery time (index in `order`), 0 if undiscovered.
  fin[v]:  0-based finish time (one past the last discovery time in the
           subtree), 0 if undiscovered.
  order:   list of discovered vertices in discovery order.

On an update, only the affected subtree is re-searched (Yang et al. style):
  - insertion: only matters if the target was undiscovered, or the target is
    not a descendant of the source (a forward-cross edge would appear);
  - deletion: only matters if the deleted edge was a tree edge.
"""


def _dfs_from(graph, start, parent, disc, fin, order, n):
    """Iterative DFS from `start` over the current graph.

    `parent[start]` must already be set (or -1 for the root).  Disc/fin are
    assigned for every vertex reached; `order` is appended in discovery order.
    """
    disc[start] = len(order)
    order.append(start)
    stack = [(start, 0)]
    while stack:
        v, i = stack[-1]
        advanced = False
        while i < n:
            if graph[v][i] and parent[i] == -1:
                parent[i] = v
                disc[i] = len(order)
                order.append(i)
                stack[-1] = (v, i + 1)
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            fin[v] = len(order)
            stack.pop()


def init(graph):
    n = len(graph)
    parent = [-1] * n
    disc = [0] * n
    fin = [0] * n
    order = []
    if n > 0:
        _dfs_from(graph, 0, parent, disc, fin, order, n)
    return (parent, disc, fin, order)


def _is_ancestor(u, v, disc, fin):
    return disc[u] <= disc[v] and fin[v] <= fin[u]


def _clear_subtree(root, parent, disc, fin, order):
    """Remove the subtree rooted at `root` from the forest."""
    lo, hi = disc[root], fin[root]
    # vertices in the subtree are exactly those with disc in [lo, hi]
    # (contiguous in discovery order)
    for v in order[lo:hi]:
        parent[v] = -1
        disc[v] = 0
        fin[v] = 0
    # rebuild order: keep vertices outside the interval, in original order
    new_order = order[:lo] + order[hi:]
    return new_order


def insert_edge(graph, edge, state):
    parent, disc, fin, order = state
    n = len(graph)
    u, v = edge
    if parent[v] != -1 and _is_ancestor(u, v, disc, fin):
        # v already discovered and is a descendant of u: edge is a forward
        # or back edge, forest stays a valid DFS forest.
        return state
    if parent[v] != -1:
        # v discovered but not a descendant of u: a forward-cross edge would
        # appear.  Re-search the subtree of v so that u's adjacency is
        # respected (v's subtree is re-explored; u's scan will now find v
        # already discovered, so the cross edge simply becomes a forward
        # edge from u's perspective only if v is discovered before u scans
        # it -- which it is, since disc[v] < ... hmm, actually we must
        # re-search from the point where the cross edge matters).
        # Safe approach: re-search v's subtree.
        new_order = _clear_subtree(v, parent, disc, fin, order)
        _dfs_from(graph, v, parent, disc, fin, new_order, n)
        return (parent, disc, fin, new_order)
    # v undiscovered: it becomes reachable from u (u is discovered since
    # the edge exists in the graph and u is in the forest... unless u is
    # undiscovered too, in which case the edge is irrelevant).
    if parent[u] == -1:
        return state
    # v is now reachable; attach it as a child of u by re-searching from v
    # with parent[v] = u.  But we must ensure the DFS order is valid: v is
    # discovered when u's scan reaches it.  Since u is already finished or
    # active, the cleanest correct move is to re-search u's subtree.
    new_order = _clear_subtree(u, parent, disc, fin, order)
    _dfs_from(graph, u, parent, disc, fin, new_order, n)
    return (parent, disc, fin, new_order)


def delete_edge(graph, edge, state):
    parent, disc, fin, order = state
    n = len(graph)
    u, v = edge
    if parent[v] != u:
        # not a tree edge: forest stays valid (the edge was forward/back/cross
        # and removing it cannot create a forward-cross edge).
        return state
    # tree edge removed: v's subtree is no longer reachable via the tree.
    # Re-search from u's subtree: clear u's subtree and re-run DFS from u.
    new_order = _clear_subtree(u, parent, disc, fin, order)
    _dfs_from(graph, u, parent, disc, fin, new_order, n)
    return (parent, disc, fin, new_order)
