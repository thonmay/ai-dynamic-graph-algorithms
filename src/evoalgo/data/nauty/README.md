# Non-isomorphic graph universes (nauty)

Generated with `geng` (nauty 27r12, lonnen/nauty mirror) on aiserver,
2026-09-20. Each file holds all non-isomorphic undirected graphs on n
vertices in graph6 format, one per line.

| file | graphs |
|---|---|
| undirected_n5.g6 | 34 |
| undirected_n6.g6 | 156 |
| undirected_n7.g6 | 1044 |

`graph_generator.load_nauty_graphs()` loads these when the labeled
exhaustive cap (n<=5) does not already cover a size.
