"""Dynamic LexBFS ordering (candidate gen003_c03).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m).
- insert_edge(u,v): if the current ordering is still valid (checked via the
  (LB) 4-point property), keep it.  Otherwise, recompute from scratch.
- delete_edge(u,v): deleting an edge can only destroy validity, but the old
  ordering is sometimes still valid; check the (LB) property first and only
  recompute when the check fails.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
A vertex ordering is a LexBFS ordering iff it satisfies (LB).

The validity check uses bitsets: for each vertex v, N[v] is a Python int
whose bit i is 1 iff v is adjacent to order[i].  For a fixed b, S_a (the set
of positions d < a with db in E) is built incrementally as a bitset, and the
violation test "exists c > b with ac in E and S_a subset of N(c)" becomes a
bitwise scan over the candidate c's.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    buckets = [set(range(n))]
    order = []

    for v in range(n):
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        b = buckets[bi]
        x = min(b)
        b.remove(x)
        order.append(x)
        nb = graph[x]
        new_buckets = []
        for bj in buckets:
            if not bj:
                continue
            inside = set(w for w in bj if nb[w])
            outside = bj - inside
            if inside:
                new_buckets.append(inside)
            if outside:
                new_buckets.append(outside)
        buckets = new_buckets
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    if n <= 2:
        return True

    # N[v] = bitset of positions i with order[i] adjacent to v.
    N = [0] * n
    for i, v in enumerate(order):
        row = graph[v]
        bits = 0
        for w in range(n):
            if row[w]:
                bits |= 1 << w
        N[v] = bits

    for b in range(1, n):
        vb = order[b]
        Nvb = N[vb]
        S = 0  # S_a = {d < a : db in E}, as a bitset of positions
        for a in range(b):
            va = order[a]
            if (Nvb >> a) & 1:
                S |= 1 << a
                continue
            # ab not in E; violation iff exists c > b with ac in E and
            # S subset of N(c).
            Nva = N[va]
            if S == 0:
                # any c > b adjacent to va violates
                if Nva & (~((1 << (b + 1)) - 1)):
                    return False
            else:
                # candidates c > b adjacent to va
                cand = Nva & (~((1 << (b + 1)) - 1))
                while cand:
                    lsb = cand & (-cand)
                    c = lsb.bit_length() - 1
                    if (N[order[c]] & S) == S:
                        return False
                    cand ^= lsb
    return True


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    order = _lexbfs(graph)
    return {'ordering': order}
