"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via bucket lists.
- insert_edge(u,v) / delete_edge(u,v): keep the current ordering if it is
  still a valid LexBFS ordering, otherwise recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

To avoid the O(n^3) (LB) check on every update, we first run a cheap
necessary-condition filter: every LexBFS ordering is a BFS ordering from
its first vertex, i.e. for every vertex x,
    dist(s, x) = min{ dist(s, y) + 1 : y in N(x), y != s }.
This is O(n+m) and catches most updates that break the ordering. Only when
the BFS filter passes do we run the full (LB) check.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement (HMPV). Returns ordering list.

    Standard bucket-list formulation:
      - Start with all vertices in one bucket.
      - Repeatedly take the first vertex v of the first non-empty bucket,
        append it to the ordering, then split every bucket by adjacency
        to v (adjacent part first, then non-adjacent part).
    """
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of lists of vertices; bucket i holds vertices with
    # the i-th distinct label in order.
    buckets = [list(range(n))]

    ordering = []

    while len(ordering) < n:
        # find first non-empty bucket
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        v = buckets[bi].pop(0)
        ordering.append(v)

        # split every bucket by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                new_buckets.append([])
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            # nb goes first (adjacent to v), then nnb
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
            if not nb and not nnb:
                new_buckets.append([])
        buckets = new_buckets

    return ordering


def _is_bfs_ordering(graph, ordering):
    """Cheap necessary condition: ordering must be a BFS ordering from
    its first vertex. O(n+m).

    For every vertex x (x != s), dist(s, x) must equal
    min{ dist(s, y) + 1 : y in N(x), y != s }.
    """
    n = len(ordering)
    if n == 0:
        return True
    s = ordering[0]
    # BFS distances from s
    dist = [-1] * n
    dist[s] = 0
    queue = [s]
    head = 0
    while head < len(queue):
        v = queue[head]
        head += 1
        row = graph[v]
        for x in range(n):
            if row[x] and dist[x] == -1:
                dist[x] = dist[v] + 1
                queue.append(x)
    # check the BFS condition
    for x in range(n):
        if x == s:
            continue
        if dist[x] == -1:
            # disconnected from s; no constraint (no neighbor of x is
            # reachable from s either, since x's neighbors would be
            # reachable through x... actually if x is unreachable then
            # none of its neighbors are reachable either, so the min
            # over reachable neighbors is empty; skip)
            continue
        best = dist[x] + 1
        row = graph[x]
        for y in range(n):
            if row[y] and y != s and dist[y] != -1:
                if dist[y] + 1 < best:
                    best = dist[y] + 1
        if best != dist[x]:
            return False
    return True


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    # pos[v] = position of v in ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    INF = n + 1
    min_d_pos = [[INF] * n for _ in range(n)]  # indexed by vertex, not position

    for b in range(n):
        pb = pos[b]
        for c in range(n):
            if pos[c] <= pb:
                continue
            if not graph[b][c]:
                continue
            # bc in E, pos[b] < pos[c]
            # find min pos[d] with db in E, dc not in E, pos[d] < pb
            best = INF
            for d in range(n):
                if pos[d] >= pb:
                    continue
                if graph[b][d] and not graph[c][d]:
                    if pos[d] < best:
                        best = pos[d]
            min_d_pos[b][c] = best

    # Now check all triples a < b < c with ac in E, ab not in E
    for a in range(n):
        pa = pos[a]
        for b in range(n):
            pb = pos[b]
            if pb <= pa:
                continue
            if graph[a][b]:
                continue  # ab in E, skip
            # ab not in E, pa < pb
            for c in range(n):
                pc = pos[c]
                if pc <= pb:
                    continue
                if not graph[a][c]:
                    continue  # ac not in E, skip
                # ac in E, ab not in E, pa < pb < pc
                # need exists d < a: db in E, dc not in E
                # i.e., min_d_pos[b][c] < pa
                if min_d_pos[b][c] >= pa:
                    return False
    return True


def _still_valid(graph, ordering):
    """Two-stage validity test: cheap BFS filter, then full (LB) check."""
    if not _is_bfs_ordering(graph, ordering):
        return False
    return _is_valid_lexbfs(graph, ordering)


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _still_valid(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _still_valid(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
