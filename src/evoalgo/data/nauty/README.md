# Non-isomorphic graph universes (nauty)

Exhaustive-up-to-isomorphism test universes for the verifier. Generated with
the **nauty 2.7r4** binaries (`geng`, `directg`, Apache-2.0 license) on
aiserver. Each file holds one graph per line in the corresponding nauty
format.

## Undirected (graph6) -- used by `dynamic_mcs`

Produced with `geng -q n`. All non-isomorphic undirected graphs on n
vertices (OEIS A001004).

| file | graphs |
|---|---|
| undirected_n5.g6 | 34 |
| undirected_n6.g6 | 156 |
| undirected_n7.g6 | 1044 |

## Directed (digraph6) -- used by `dynamic_bfs`, `dynamic_dfs`

Produced with `geng -q n | directg -q`, which turns each undirected edge into
one direction, the other, or both (2-cycle), yielding all non-isomorphic
loop-free digraphs on n vertices.

`directed_n<n>.d6` -- all non-isomorphic digraphs (OEIS A000273):

| file | digraphs |
|---|---|
| directed_n1.d6 | 1 |
| directed_n2.d6 | 3 |
| directed_n3.d6 | 16 |
| directed_n4.d6 | 218 |
| directed_n5.d6 | 9608 |

`rooted_n<n>.d6` -- one representative per **(digraph, root-orbit)** class,
with the distinguished vertex (root) relabeled to vertex 0 (OEIS A353996).
For a rooted problem (BFS/DFS fix the source at 0) this covers every root
orbit exactly once, so the verifier exercises all non-isomorphic
(digraph, source) pairs. Counts:

| file | (digraph, root) classes |
|---|---|
| rooted_n1.d6 | 1 |
| rooted_n2.d6 | 4 |
| rooted_n3.d6 | 36 |
| rooted_n4.d6 | 752 |
| rooted_n5.d6 | 45960 |

## digraph6 format

A digraph6 line is `&` + header + body. The header is the single byte `n+63`
(for n<=62). The body packs the full n x n adjacency matrix row by row (arc
i->j is bit j of row i) into 6-bit groups, each offset by 63. Decoded by
`graph_generator.decode_digraph6`; the inverse is `encode_digraph6`.

## Loaders

- `graph_generator.load_nauty_digraphs(n)` -- unrooted reps (A000273).
- `graph_generator.load_nauty_rooted_digraphs(n)` -- rooted reps (A353996).
- `graph_generator.load_nauty_graphs(n)` -- undirected reps (A001004).

`graph_generator.generate_test_graphs(...)` assembles the directed universe
from the rooted files (for rooted problems) or unrooted files (for unrooted
problems), plus `relabels_per_class` deterministic random relabelings of each
representative (to catch label-dependent bugs such as id tie-breaks).

## Provenance / regeneration

- nauty 2.7r4, `geng` + `directg`, run on aiserver 2026-10-16.
- Counts cross-checked against OEIS A000273 (directed) and A353996 (rooted),
  and against an independent brute-force canonical-form enumeration
  and a Burnside orbit cross-check (scratch scripts, not kept).
- License: nauty is Apache-2.0; the generated graph data are public
  mathematical objects (no license restriction on the data itself).
