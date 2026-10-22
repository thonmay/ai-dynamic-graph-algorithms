"""Dynamic LexBFS ordering.

Strategy: recompute the LexBFS ordering from scratch on every update.

- init: run the LexBFS algorithm with a deterministic tie-break.
- insert_edge(u, v): recompute the LexBFS ordering.
- delete_edge(u, v): recompute the LexBFS ordering.

The (LB) 4-point property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """LexBFS with a deterministic tie-break.

    Uses a global 'first' array to track the first bucket containing a neighbor,
    and picks the vertex with the smallest (first[v], v) key.
    """
    n = len(graph)
    if n == 0:
        return []

    buckets = [[v] for v in range(n)]
    bucket_of = list(range(n))
    first = [n] * n
    processed = [False] * n
    ordering = []

    for _step in range(n):
        best = None
        for v in range(n):
            if processed[v]:
                continue
            key = (first[v], v)
            if best is None or key < (first[best], best):
                best = v
        x = best
        processed[x] = True
        ordering.append(x)

        new_buckets = []
        for b in buckets:
            nb = [v for v in b if graph[v][x]]
            nnb = [v for v in b if not graph[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets

        for i, b in enumerate(buckets):
            for v in b:
                bucket_of[v] = i
        for v in range(n):
            if graph[v][x]:
                first[v] = bucket_of[v]
            else:
                first[v] = n

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property. Returns True if ordering is a valid
    LexBFS ordering of graph.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(graph)
    if n <= 2:
        return True

    # Precompute adjacency as sets for fast lookup
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    for c in range(n):
        vc = ordering[c]
        # For each a < c with ac in E
        for a in range(c):
            va = ordering[a]
            if va not in adj[vc]:
                continue
            # ac in E
            # Precompute witness pool: d at position < a with dc not in E
            witness_pool = set()
            for d_pos in range(a):
                vd = ordering[d_pos]
                if vd not in adj[vc]:
                    witness_pool.add(vd)
            # For each b in (a, c) with ab not in E, check if
            # witness_pool intersects adj[b]
            for b in range(a + 1, c):
                vb = ordering[b]
                if vb in adj[va]:
                    continue
                # ab not in E, need witness
                # Check if any d in witness_pool has db in E
                found = False
                for d in witness_pool:
                    if vb in adj[d]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': state['n']}


def delete_edge(graph, edge, state):
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': state['n']}
