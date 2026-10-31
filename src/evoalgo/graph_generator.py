# AI-assisted code: generated and revised with Qwen3.8-Flash-Next, GLM-5.2 and Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Graph generation for the bounded test universe.

Directed problems (BFS, DFS, SCC, reachability) default to an
exhaustive-up-to-isomorphism universe built from the nauty data files in
``data/nauty/`` (``directed_n<n>.d6`` = all non-isomorphic loop-free digraphs
on n vertices, OEIS A000273; ``rooted_n<n>.d6`` = one representative per
(digraph, root-orbit) class with the root relabeled to vertex 0, OEIS A353996).
For each class we also apply k deterministic random relabelings (vertex
permutations) to catch label-dependent bugs such as id tie-breaks. For
rooted problems the base classes are the rooted files (one case per root
orbit); for unrooted problems they are the unrooted files.

Undirected problems (MCS) keep the previous behaviour: all labeled graphs for
n <= exhaustive_cap (5), then non-isomorphic ``geng`` representatives from
``undirected_n<n>.g6`` for larger n, then seeded random samples when no data
file exists.

``universe="labeled"`` reproduces the old directed behaviour (all labeled
digraphs for n <= 4, random samples beyond) and is kept only for comparison.

nauty data provenance, counts, and generation commands: see
``data/nauty/README.md``.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterator

import numpy as np

NAUTY_DATA_DIR = Path(__file__).parent / "data" / "nauty"


# ---------------------------------------------------------------------------
# Labeled enumeration (old mode, kept for comparison)
# ---------------------------------------------------------------------------

def enumerate_digraphs(n: int) -> Iterator[np.ndarray]:
    """Yield all labeled loop-free digraphs on n vertices as adjacency matrices.

    For directed graphs: each off-diagonal entry is 0 or 1 independently.
    Count: 2^(n*(n-1)).
    """
    pairs = n * (n - 1)  # directed: n*(n-1) possible edges
    for bits in range(2**pairs):
        mat = np.zeros((n, n), dtype=int)
        idx = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    mat[i, j] = (bits >> idx) & 1
                    idx += 1
        yield mat


def enumerate_undirected_graphs(n: int) -> Iterator[np.ndarray]:
    """Yield all labeled loop-free undirected graphs on n vertices.

    For undirected: only upper triangle entries are free.
    Count: 2^(n*(n-1)/2).
    """
    pairs = n * (n - 1) // 2
    for bits in range(2**pairs):
        mat = np.zeros((n, n), dtype=int)
        idx = 0
        for i in range(n):
            for j in range(i + 1, n):
                val = (bits >> idx) & 1
                mat[i, j] = val
                mat[j, i] = val
                idx += 1
        yield mat


def sample_digraphs(n: int, count: int, seed: int, p: float = 0.3) -> list[np.ndarray]:
    """Sample random loop-free digraphs with edge probability p."""
    rng = random.Random(seed)
    graphs = []
    for _ in range(count):
        mat = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(n):
                if i != j and rng.random() < p:
                    mat[i, j] = 1
        graphs.append(mat)
    return graphs


def sample_undirected_graphs(n: int, count: int, seed: int, p: float = 0.3) -> list[np.ndarray]:
    """Sample random loop-free undirected graphs with edge probability p."""
    rng = random.Random(seed)
    graphs = []
    for _ in range(count):
        mat = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    mat[i, j] = 1
                    mat[j, i] = 1
        graphs.append(mat)
    return graphs


# ---------------------------------------------------------------------------
# nauty encodings
# ---------------------------------------------------------------------------

def decode_graph6(line: str) -> tuple[int, np.ndarray]:
    """Decode one graph6 string (nauty format) into (n, adjacency matrix).

    graph6 packs the upper triangle of the adjacency matrix into 6-bit
    characters (offset 63). The first 1-3 chars encode n.
    """
    vals = [ord(c) - 63 for c in line.strip()]
    if not vals or any(v < 0 or v > 63 for v in vals):
        raise ValueError(f"invalid graph6 line: {line!r}")
    if vals[0] <= 62:
        n, k = vals[0], 1
    elif vals[0] == 63:
        if len(vals) < 4:
            raise ValueError(f"truncated graph6 long header: {line!r}")
        n = (vals[1] << 12) | (vals[2] << 6) | vals[3]
        k = 4
    else:
        raise ValueError(f"invalid graph6 header: {line!r}")
    bits = []
    for v in vals[k:]:
        bits.extend((v >> b) & 1 for b in range(5, -1, -1))
    if len(bits) < n * (n - 1) // 2:
        raise ValueError(f"truncated graph6 line: {line!r}")
    mat = np.zeros((n, n), dtype=int)
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            if bits[idx]:
                mat[i, j] = mat[j, i] = 1
            idx += 1
    return n, mat


def decode_digraph6(line: str) -> tuple[int, list[int]]:
    """Decode one digraph6 line (nauty format) into (n, rows).

    digraph6 packs the full n x n adjacency matrix (row by row, arc i->j is
    bit j of row i) into 6-bit characters (offset 63). The first character is
    ``&`` (38); the next encodes n (n<=62: single byte n+63). ``rows[i]`` is
    the out-arc bitmask of vertex i (bit j set iff arc i->j exists).

    Long headers (``~``) for n>62 are not needed for the committed data
    (n<=5) and raise if encountered.
    """
    s = line.strip()
    if not s or s[0] != "&":
        raise ValueError(f"not digraph6: {line!r}")
    rest = s[1:]
    if not rest or rest[0] == "~":
        raise ValueError(f"digraph6 long header (n>62) not supported: {line!r}")
    n = ord(rest[0]) - 63
    if n < 1:
        raise ValueError(f"invalid digraph6 header: {line!r}")
    bits = []
    for c in rest[1:]:
        v = ord(c) - 63
        if v < 0 or v > 63:
            raise ValueError(f"invalid digraph6 body: {line!r}")
        for b in range(5, -1, -1):  # big-endian: first bit of group is MSB
            bits.append((v >> b) & 1)
    if len(bits) < n * n:
        raise ValueError(f"truncated digraph6 line: {line!r}")
    rows = []
    for i in range(n):
        row = 0
        for j in range(n):
            if bits[i * n + j]:
                row |= (1 << j)
        rows.append(row)
    return n, rows


def encode_digraph6(n: int, rows: list[int]) -> str:
    """Inverse of :func:`decode_digraph6`: (n, rows) -> digraph6 string.

    Used only for round-trip self-tests.
    """
    bits = []
    for i in range(n):
        for j in range(n):
            bits.append((rows[i] >> j) & 1)
    while len(bits) % 6:
        bits.append(0)
    out = ["&", chr(n + 63)]
    for g in range(0, len(bits), 6):
        v = 0
        for b in range(5, -1, -1):
            v = (v << 1) | bits[g + (5 - b)]
        out.append(chr(v + 63))
    return "".join(out)


def digraph_rows_to_matrix(n: int, rows: list[int]) -> np.ndarray:
    """Convert digraph6 out-arc bitmasks to an n x n 0/1 adjacency matrix."""
    return np.array([[(rows[i] >> j) & 1 for j in range(n)] for i in range(n)], dtype=int)


def relabel_digraph(graph: np.ndarray, perm: tuple[int, ...]) -> np.ndarray:
    """Apply a vertex permutation to a digraph adjacency matrix.

    ``perm[i]`` is the new label of old vertex i. Arc i->j becomes
    perm[i]->perm[j]. The result is isomorphic to ``graph``; when ``perm`` is
    the identity it is unchanged. Used to produce deterministic label
    variants of a nauty representative so the verifier also exercises
    label-dependent behaviour (e.g. id tie-breaks).
    """
    n = graph.shape[0]
    out = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if graph[i, j]:
                out[perm[i], perm[j]] = 1
    return out


def _relabel_permutations(n: int, seed: int, k: int) -> list[tuple[int, ...]]:
    """Return up to k distinct non-identity vertex permutations of range(n).

    Deterministic in (seed, n, k): the same call always yields the same
    permutations, so the test universe is reproducible across runs.
    """
    if k <= 0:
        return []
    rng = random.Random(seed * 1_000_003 + n)
    identity = tuple(range(n))
    perms: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0
    while len(perms) < k and attempts < 1000:
        attempts += 1
        p = list(range(n))
        rng.shuffle(p)
        p = tuple(p)
        if p == identity or p in seen:
            continue
        seen.add(p)
        perms.append(p)
    return perms


# ---------------------------------------------------------------------------
# nauty loaders
# ---------------------------------------------------------------------------

def load_nauty_graphs(n: int) -> list[np.ndarray] | None:
    """Load non-isomorphic undirected graphs of size n from the nauty data file.

    Returns None if no data file exists for that size (caller falls back to
    random sampling). Files are graph6, one graph per line, produced by
    `geng n` (see data/nauty/README.md).
    """
    path = NAUTY_DATA_DIR / f"undirected_n{n}.g6"
    if not path.exists():
        return None
    graphs = []
    for line in path.read_text().splitlines():
        if line.strip():
            gn, mat = decode_graph6(line)
            if gn != n:
                raise ValueError(f"{path.name}: expected n={n}, got n={gn}")
            graphs.append(mat)
    if not graphs:
        raise ValueError(f"{path} exists but contains no graphs")
    return graphs


def _load_nauty_digraphs(n: int, prefix: str) -> list[np.ndarray] | None:
    """Load digraph6 representatives of size n from ``<prefix>_n<n>.d6``.

    ``prefix`` is ``directed`` (unrooted, OEIS A000273) or ``rooted`` (one
    representative per (digraph, root-orbit) class with the root at vertex 0,
    OEIS A353996). Returns None if no data file exists for that size.
    """
    path = NAUTY_DATA_DIR / f"{prefix}_n{n}.d6"
    if not path.exists():
        return None
    graphs = []
    for line in path.read_text().splitlines():
        if line.strip():
            dn, rows = decode_digraph6(line)
            if dn != n:
                raise ValueError(f"{path.name}: expected n={n}, got n={dn}")
            graphs.append(digraph_rows_to_matrix(n, rows))
    if not graphs:
        raise ValueError(f"{path} exists but contains no digraphs")
    return graphs


def load_nauty_digraphs(n: int) -> list[np.ndarray] | None:
    """All non-isomorphic loop-free digraphs of size n (unrooted reps)."""
    return _load_nauty_digraphs(n, "directed")


def load_nauty_rooted_digraphs(n: int) -> list[np.ndarray] | None:
    """One representative per (digraph, root-orbit) class of size n.

    The distinguished vertex (root) is relabeled to vertex 0 in each
    representative, so a rooted problem can fix its source at 0 and still
    cover every root orbit exactly once.
    """
    return _load_nauty_digraphs(n, "rooted")


# ---------------------------------------------------------------------------
# Universe assembly
# ---------------------------------------------------------------------------

def generate_test_graphs(
    n_max: int,
    n_random: int,
    seed: int,
    directed: bool,
    exhaustive_cap: int | None = None,
    universe: str = "nauty",
    rooted: bool = False,
    relabels_per_class: int = 2,
) -> list[tuple[int, np.ndarray]]:
    """Generate the bounded test universe of base graphs.

    Returns a list of (n, adjacency_matrix) pairs.

    Directed, ``universe="nauty"`` (default): for each n with a data file,
    every non-isomorphic representative (rooted files for rooted problems,
    unrooted otherwise) plus ``relabels_per_class`` deterministic random
    relabelings of each representative. For n with no data file, seeded
    random samples. This is the exhaustive-up-to-isomorphism universe.

    Directed, ``universe="labeled"`` (comparison only): all labeled digraphs
    for n <= exhaustive_cap (4), random samples beyond.

    Undirected (any universe): all labeled graphs for n <= exhaustive_cap
    (5), then non-isomorphic ``geng`` representatives from the data files for
    larger n, then seeded random samples when no data file exists. This path
    is unchanged from the original so MCS behaviour is preserved.
    """
    if exhaustive_cap is None:
        exhaustive_cap = 4 if directed else 5
    result: list[tuple[int, np.ndarray]] = []
    rng_seed = seed

    for n in range(2, n_max + 1):
        if directed:
            if universe == "labeled":
                if n <= exhaustive_cap:
                    for g in enumerate_digraphs(n):
                        result.append((n, g))
                else:
                    for g in sample_digraphs(n, min(n_random, 200), rng_seed):
                        result.append((n, g))
                    rng_seed += 1
            else:  # "nauty"
                loader = load_nauty_rooted_digraphs if rooted else load_nauty_digraphs
                reps = loader(n)
                if reps is None:
                    for g in sample_digraphs(n, min(n_random, 200), rng_seed):
                        result.append((n, g))
                    rng_seed += 1
                    continue
                for g in reps:
                    result.append((n, g))
                    for perm in _relabel_permutations(n, seed, relabels_per_class):
                        result.append((n, relabel_digraph(g, perm)))
        else:
            # Undirected: preserve the original labelled/nauty/sampled mix.
            if n <= exhaustive_cap:
                for g in enumerate_undirected_graphs(n):
                    result.append((n, g))
            else:
                nauty = load_nauty_graphs(n)
                if nauty is not None:
                    for g in nauty:
                        result.append((n, g))
                else:
                    for g in sample_undirected_graphs(n, min(n_random, 200), rng_seed):
                        result.append((n, g))
                    rng_seed += 1

    return result


def generate_operation_sequences(
    n: int,
    graph: np.ndarray,
    seq_len_max: int,
    seq_count: int,
    seed: int,
    directed: bool = True,
) -> list[list[tuple[str, tuple[int, int]]]]:
    """Generate bounded sequences of edge insertions and deletions.

    Each operation is ('insert', (u, v)) or ('delete', (u, v)).
    Operations are legal: insert only if edge absent, delete only if present.
    """
    rng = random.Random(seed)
    sequences = []

    for s in range(seq_count):
        seq = []
        current = graph.copy()
        for _ in range(seq_len_max):
            # Pick a random non-diagonal cell
            u = rng.randint(0, n - 1)
            v = rng.randint(0, n - 1)
            while v == u:
                v = rng.randint(0, n - 1)

            if current[u, v] == 0:
                current[u, v] = 1
                if not directed:
                    current[v, u] = 1
                seq.append(("insert", (u, v)))
            else:
                current[u, v] = 0
                if not directed:
                    current[v, u] = 0
                seq.append(("delete", (u, v)))
        sequences.append(seq)

    return sequences
