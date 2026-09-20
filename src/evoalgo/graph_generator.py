"""Graph generation for the bounded test universe.

For n <= exhaustive_cap: enumerate all labeled simple loop-free graphs on n
  vertices. Labeled enumeration is more thorough than nauty's non-isomorphic
  classes since it tests every possible edge configuration (including
  label-handling bugs). Cost: 2^(n(n-1)/2) undirected, 2^(n(n-1)) directed,
  so exhaustive is capped at n=4 directed and n=5 undirected.

If a nauty data file exists for a size n (src/evoalgo/data/nauty/undirected_n<n>.g6,
  graph6 format, generated offline with geng), those non-isomorphic graphs
  replace random sampling for that size. This gives an exhaustive-up-to-
  isomorphism universe at n=5..7 where labeled enumeration is too costly.

For sizes with no nauty data: seeded random graphs from a stated distribution.
"""

from __future__ import annotations

import itertools
import random
from pathlib import Path
from typing import Iterator

import numpy as np

NAUTY_DATA_DIR = Path(__file__).parent / "data" / "nauty"


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


def load_nauty_graphs(n: int) -> list[np.ndarray] | None:
    """Load non-isomorphic graphs of size n from the nauty data file.

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


def generate_test_graphs(
    n_max: int,
    n_random: int,
    seed: int,
    directed: bool,
    exhaustive_cap: int | None = None,
) -> list[tuple[int, np.ndarray]]:
    """Generate the bounded test universe of base graphs.

    Returns list of (n, adjacency_matrix) pairs.

    For n <= exhaustive_cap (default: 4 directed, 5 undirected): all labeled
    graphs (exhaustive).
    For larger n with a nauty data file: all non-isomorphic graphs.
    For larger n without data: n_random seeded random samples.
    """
    if exhaustive_cap is None:
        exhaustive_cap = 4 if directed else 5
    result: list[tuple[int, np.ndarray]] = []
    rng_seed = seed

    for n in range(2, n_max + 1):
        if directed:
            if n <= exhaustive_cap:
                for g in enumerate_digraphs(n):
                    result.append((n, g))
            else:
                # Sample for larger n
                count = min(n_random, 200)
                for g in sample_digraphs(n, count, rng_seed):
                    result.append((n, g))
                rng_seed += 1
        else:
            if n <= exhaustive_cap:
                for g in enumerate_undirected_graphs(n):
                    result.append((n, g))
            else:
                nauty = load_nauty_graphs(n)
                if nauty is not None:
                    for g in nauty:
                        result.append((n, g))
                else:
                    count = min(n_random, 200)
                    for g in sample_undirected_graphs(n, count, rng_seed):
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
