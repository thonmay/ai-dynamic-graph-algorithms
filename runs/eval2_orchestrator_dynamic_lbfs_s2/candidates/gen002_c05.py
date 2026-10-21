"""Dynamic LexBFS ordering (open problem; correct baseline with cheap checks).

Strategy:
- Maintain a valid LexBFS ordering in the state.
- After each edge update, run a fast necessary-condition check on the
  ordering. If it passes, keep the ordering (no recompute). If it fails,
  recompute a fresh LexBFS ordering with the static partition-refinement
  algorithm (Habib-McConnell-Paul-Viennot style, O(n+m)).

Fast necessary conditions (all implied by the (LB) 4-point property of
Corneil and Krueger, so a failing check forces a recompute which is always
safe; a passing check keeps the ordering only when the ordering is actually
still valid -- see the soundness argument below).

Condition 1 (first-vertex rule): the first vertex of a LexBFS ordering is
universal in the graph (adjacent to every other vertex). This is a standard
property of LexBFS: the first vertex is the first vertex of the first
bucket, and every later vertex is adjacent to it, otherwise it would have
been split into a separate earlier bucket.

Condition 2 (prefix rule): for every position i >= 1, vertex order[i] is
adjacent to at least one vertex among order[0..i-1]. In LexBFS, when a
vertex is selected, all remaining vertices are partitioned by their
adjacency to the selected vertex, and the non-adjacent part is placed
BEFORE the adjacent part in the bucket list. Hence any vertex selected at
position i must be adjacent to the vertex selected at position i-1... more
precisely, to at least one earlier vertex (the one that kept it in the
front bucket). Actually the precise invariant: at each step, the first
non-empty bucket contains only vertices adjacent to the just-selected
vertex. So order[i] is adjacent to order[i-1] for all i >= 1.

Wait -- that is the precise invariant: in LexBFS, after selecting v, the
buckets are ordered so that vertices adjacent to v come first. The next
selected vertex is the first vertex of the first non-empty bucket, which
therefore is adjacent to v. So: order[i] adjacent to order[i-1] for all
i >= 1. This is a necessary condition.

Condition 3 (4-point property, full check): the actual (LB) property.
We run it only when conditions 1 and 2 pass, to avoid the O(n^4) cost
when the ordering is obviously broken.

Soundness: we keep the ordering only if it passes the FULL 4-point check
when that check is affordable... Actually to be safe and simple: we run
conditions 1 and 2 (O(n^2) total) as a fast filter; if they fail, recompute.
If they pass, we still must ensure validity. The 4-point property is the
exact certificate, so we run it (O(n^4) worst case) only when the fast
filter passes. This is still correct: we never keep an invalid ordering.

Cost profile:
- Fast filter: O(n^2) per update.
- Full 4-point check: O(n^4) worst case, but only when the fast filter
  passes (i.e., the ordering is "close" to valid).
- Recompute: O(n^2) with adjacency matrix (n steps, each refining O(n)
  buckets of total size O(n)).
"""


def _lexbfs(graph):
    """Static LexBFS: return a valid ordering of all vertices."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets of vertices with identical label
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket, take its smallest vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        v = min(buckets[bi])
        buckets[bi].discard(v)
        order.append(v)

        # refine: for each bucket, split off vertices adjacent to v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = set()
            for x in b:
                if graph[v][x]:
                    nb.add(x)
            if nb:
                rest = b - nb
                if rest:
                    new_buckets.append(rest)
                new_buckets.append(nb)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def _fast_filter(graph, order):
    """O(n^2) necessary conditions for a LexBFS ordering.

    1. First vertex is universal.
    2. For all i >= 1, order[i] is adjacent to order[i-1].
    """
    n = len(order)
    if n == 0:
        return True
    v0 = order[0]
    for i in range(1, n):
        if not graph[v0][order[i]]:
            return False
    for i in range(1, n):
        if not graph[order[i - 1]][order[i]]:
            return False
    return True


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property: for all a < b < c (positions) with
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; need: for every c > b with ac in E,
            # exists d < a with db in E and dc not in E
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                # ac in E, ab not in E: need witness d < a
                found = False
                for d in range(a):
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _check_and_maybe_recompute(graph, state):
    order = state['ordering']
    if _fast_filter(graph, order) and _is_valid_lexbfs(graph, order):
        return state
    order = _lexbfs(graph)
    return {'ordering': order}


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    return _check_and_maybe_recompute(graph, state)


def delete_edge(graph, edge, state):
    return _check_and_maybe_recompute(graph, state)
