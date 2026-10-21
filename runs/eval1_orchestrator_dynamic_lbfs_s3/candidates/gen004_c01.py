"""Dynamic LexBFS ordering (candidate gen004_c01).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  - init: static partition-refinement LexBFS, O(n^2) with sets.
  - insert_edge / delete_edge:
      1. Verify the current ordering against the LB 4-point property
         (O(n^3) worst case, early exit). If still valid, do nothing.
      2. Try a local repair: move one of the two affected vertices to a
         different position (all positions tried), verify.
      3. Suffix recompute: keep the prefix up to the first affected
         vertex (a valid LexBFS prefix remains a valid prefix of some
         LexBFS of the updated graph) and recompute the rest with
         partition refinement seeded by the prefix. O(n^2).
      4. Fall back to a full recompute.

The LB 4-point property (Corneil-Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.
"""


# ---------------------------------------------------------------------------
# Static LexBFS (partition refinement)
# ---------------------------------------------------------------------------

def _static_lexbfs(n, adj):
    """Return a valid LexBFS ordering of the graph."""
    if n == 0:
        return []
    if n == 1:
        return [0]

    adj_sets = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                adj_sets[u].add(v)
                adj_sets[v].add(u)

    # Partition refinement: one bucket initially.
    # Repeatedly take the first vertex of the first bucket, append to
    # ordering, refine all buckets by adjacency to that vertex.
    buckets = [list(range(n))]
    ordering = []

    for _ in range(n):
        x = buckets[0][0]
        buckets[0] = buckets[0][1:]
        ordering.append(x)

        new_buckets = []
        for C in buckets:
            if not C:
                continue
            C_in = [v for v in C if v in adj_sets[x]]
            C_out = [v for v in C if v not in adj_sets[x]]
            if C_in:
                new_buckets.append(C_in)
            if C_out:
                new_buckets.append(C_out)
        buckets = new_buckets

    return ordering


# ---------------------------------------------------------------------------
# Suffix recompute: keep a valid prefix, refine the rest
# ---------------------------------------------------------------------------

def _suffix_recompute(n, adj, prefix):
    """Given a valid LexBFS prefix of the current graph, complete it to a
    full valid LexBFS ordering by partition-refining the remaining
    vertices, seeded by the prefix.

    Correctness: the prefix is a valid LexBFS prefix of the current graph
    (its own 4-point property is unaffected by the update, and the
    refinement process only ever appends vertices consistent with the
    prefix's labels). Completing it by the standard refinement yields a
    full valid LexBFS ordering.
    """
    if len(prefix) == n:
        return list(prefix)

    adj_sets = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                adj_sets[u].add(v)
                adj_sets[v].add(u)

    used = set(prefix)
    remaining = [v for v in range(n) if v not in used]

    # Seed buckets: refine the remaining set by adjacency to each prefix
    # vertex, in prefix order. This mirrors the labels the prefix would
    # have produced.
    buckets = [remaining]
    for x in prefix:
        new_buckets = []
        for C in buckets:
            if not C:
                continue
            C_in = [v for v in C if v in adj_sets[x]]
            C_out = [v for v in C if v not in adj_sets[x]]
            if C_in:
                new_buckets.append(C_in)
            if C_out:
                new_buckets.append(C_out)
        buckets = new_buckets

    ordering = list(prefix)
    for _ in range(len(remaining)):
        x = buckets[0][0]
        buckets[0] = buckets[0][1:]
        ordering.append(x)

        new_buckets = []
        for C in buckets:
            if not C:
                continue
            C_in = [v for v in C if v in adj_sets[x]]
            C_out = [v for v in C if v not in adj_sets[x]]
            if C_in:
                new_buckets.append(C_in)
            if C_out:
                new_buckets.append(C_out)
        buckets = new_buckets

    return ordering


# ---------------------------------------------------------------------------
# LB 4-point property verification
# ---------------------------------------------------------------------------

def _is_valid_lexbfs(ordering, adj):
    """Check the LB 4-point property. O(n^3) worst case."""
    n = len(ordering)
    if n <= 2:
        return True

    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if adj[a][b]:
                continue
            for k in range(j + 1, n):
                c = ordering[k]
                if not adj[a][c]:
                    continue
                # ac in E, ab not in E, a < b < c.
                # Need d < a with db in E and dc not in E.
                found = False
                for l in range(i):
                    d = ordering[l]
                    if adj[d][b] and not adj[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


# ---------------------------------------------------------------------------
# Local repair
# ---------------------------------------------------------------------------

def _try_local_repair(ordering, adj, u, v):
    """Try to repair the ordering after an edge update involving u and v.

    Returns a new valid ordering, or None if no repair found.
    """
    n = len(ordering)
    if n <= 2:
        return ordering[:]

    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i

    # Build candidate moves: (vertex, new_position)
    # Try moving u and v to various positions.
    # Heuristic order: positions near the other affected vertex first.

    candidates = []

    # Move later vertex to just after earlier, and earlier to just after later
    if pos[u] < pos[v]:
        candidates.append((v, pos[u] + 1))  # v right after u
        candidates.append((u, pos[v]))       # u right after v
    else:
        candidates.append((u, pos[v] + 1))
        candidates.append((v, pos[u]))

    # Move to front
    candidates.append((u, 0))
    candidates.append((v, 0))
    # Move to back
    candidates.append((u, n - 1))
    candidates.append((v, n - 1))

    # All positions for u
    for p in range(n):
        if p != pos[u]:
            candidates.append((u, p))
    # All positions for v
    for p in range(n):
        if p != pos[v]:
            candidates.append((v, p))

    # Deduplicate, preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    # Stage 1: exhaustive single-vertex moves (O(n^2) verifications).
    # This is cheaper than a full recompute (O(n^3)) and always finds a
    # repair when one exists by moving a single vertex.
    for w, new_pos in unique:
        new_ordering = ordering[:]
        old_pos = pos[w]
        new_ordering.pop(old_pos)
        # Adjust new_pos if we removed an element before it
        if old_pos < new_pos:
            new_pos -= 1
        new_ordering.insert(new_pos, w)
        if _is_valid_lexbfs(new_ordering, adj):
            return new_ordering

    # Stage 2: swaps of u with another vertex, or v with another vertex.
    # Only try swaps that change the relative order of the swapped pair
    # (swapping equal positions is a no-op).
    for w in (u, v):
        j = pos[w]
        for i in range(n):
            if i == j:
                continue
            new_ordering = ordering[:]
            new_ordering[i], new_ordering[j] = new_ordering[j], new_ordering[i]
            if _is_valid_lexbfs(new_ordering, adj):
                return new_ordering

    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def init(graph):
    """Initialize the state from the adjacency matrix."""
    n = len(graph)
    ordering = _static_lexbfs(n, graph)
    return {
        'ordering': ordering,
        'n': n,
    }


def _update(graph, edge, state):
    """Shared update logic for insert/delete."""
    u, v = edge
    n = state['n']
    ordering = state['ordering']

    # Quick check: is the current ordering still valid?
    if _is_valid_lexbfs(ordering, graph):
        return state

    # Try local repair
    repaired = _try_local_repair(ordering, graph, u, v)
    if repaired is not None:
        state['ordering'] = repaired
        return state

    # Suffix recompute: keep the prefix up to the first affected vertex.
    # A valid LexBFS prefix remains a valid LexBFS prefix of some LexBFS of the
    # updated graph, so this always yields a valid full ordering.
    pos_u = ordering.index(u)
    pos_v = ordering.index(v)
    cut = min(pos_u, pos_v)
    prefix = ordering[:cut]
    state['ordering'] = _suffix_recompute(n, graph, prefix)
    return state


def insert_edge(graph, edge, state):
    """Handle insertion of edge (u, v)."""
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    """Handle deletion of edge (u, v)."""
    return _update(graph, edge, state)
