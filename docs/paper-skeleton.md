# Dynamic MCS Ordering Maintenance — Lean-Verified — Paper Skeleton

Status: research draft, 2026-09-21. Formalization still in flight (5 real sorries).
Theorems/proof structure below reflects the current Lean module state.

## Working title
Machine-Checked Correctness of a Fully Dynamic Maximum Cardinality Search
Ordering under Edge Updates

## Abstract (draft)
We consider the problem of maintaining a maximum cardinality search (MCS)
ordering of an undirected graph under fully dynamic single-edge updates
(insertions and deletions). MCS orderings are the canonical tool for chordal
graph recognition and perfect elimination orderings (Rose-Tarjan-Lueker;
Tarjan-Yannakakis). We give a deterministic algorithm -- ties broken by smallest
vertex id -- that maintains the ordering under edge flips by (1) a tight local
probe over an affected window (insertion: first break can only occur in steps
pos[u]+1..pos[v]; deletion: only step pos[v] can be the first break), and (2) a
bucket-MCS regreedy of the suffix from the first breaking step when a break is
found. When the probe finds no break the update costs O(k), k = positional
distance between the edge endpoints; worst case is O(n + m_s) on the regreedy
suffix, no better than recomputation. We verify the full correctness of the
update invariant in the Lean 4 theorem prover. On an exhaustive test bench of
7,524 graph/update-sequence cases (random-rate + adversarial rates) the
candidate matches the offline MCS recomputation on every case and its
measured work is ~18% of the offline baseline. To the best of our knowledge
this is the first fully dynamic maintenance of a graph-search ordering, and the
first machine-checked correctness proof of a fully dynamic graph-ordering
update.

## 1. Introduction
- MCS background, chordal graphs, PEOs, classic references.
- Why dynamic: streaming/changing graphs, incremental chordality, sparse matrix
  reordering, ET-series decompositions, causal inference (MCS-style orderings
  appear in graphical model structure learning).
- Contribution list (4 axes of novelty from related-work doc).
- One honest positioning paragraph: the algorithm is not asymptotically
  worst-case-optimal (worst case = recompute); the contribution is
  amortized/practical efficiency + machine-checked correctness.

## 2. Preliminaries and model
- Undirected graph G=(V,E), n=|V|, m=|E|; Vert n; UGraph with symm+loopless.
- MCS: at each step choose the unchosen vertex with max number of chosen
  neighbors; deterministic tie-break = smallest id.
- IsMCSNext / IsMCSOrdering definitions (as in Lean base).
- Dynamic update model: FlipOf G G' u v (single-edge flip); insert/delete.

## 3. The window characterization (main lemma)
- Insertion: for a flip inserting edge (u,v) with pos[u] < pos[v], only the
  later endpoint's selection-time cardinality changes; it rises for every
  prefix containing u. First break can only occur in steps pos[u]+1..pos[v].
  [Lean: legal_after_laterPos proved; legal_middle_delete proved; before-side
  via base prefix_preserved; probe iff insert_break_iff / deletionBreaks_true_iff
  still sorry.]
- Deletion: only step pos[v] can be the first break.
- Statement of the three main theorems (from the Lean module):
  - init_valid (H) : ValidState H (initOrder H)
  - insert_update_valid (hflip) (hvalid) : ValidState G' (insertUpdate G' order u v)
  - delete_update_valid (hflip) (hvalid) : ValidState G' (deleteUpdate G' order u v)
- The probe functions (firstBreak / deletionBreaks) and their exact firing
  conditions.

## 4. Algorithm and complexity
- initOrder = greedySuffix []; update = probe then regreedy suffix.
- Complexity: probe O(k) (insert) / O(suffix-to-first-break) (delete);
  regreedy O(n + m_s); worst case O(n+m) = recompute; space O(n+m).
- Work-ratio measurement methodology (candidate_work / offline_work,
  verifier.py:361), bench description (7,524 cases, rates), result 0.18.
- Honest open problem: sublinear worst case for MCS-ordering maintenance.
  Related lower bounds: Omega(n) dynamic DFS (Baswana 2016), Omega(log n)
  cell-probe dynamic chordality (Banerjee 2018), BMM/OMv hardness for dynamic
  BFS (Abboud-Williams 2014; Henzinger 2015). No MCS-specific lower bound.

## 5. Formalization in Lean 4
- Functional modeling: state = order as pure List (Vert n); mask/pos are
  notational sugar derived from adjacency and idxOf (module docstring L61-64);
  no State monad/Ref/Array; no bitmasks (representation-independent).
- 28 lemmas/theorems proved (list from gap analysis); 5 remaining sorries
  (init_valid trivial from base; insert_break_iff; deletionBreaks_true_iff;
  insert_update_valid; delete_update_valid).
- Proof architecture: while the Python probe is a bounded scan over a window,
  the Lean build-out proves firstBreak_some/none (unbounded scan) +
  ordering_of_steps_legal + update_from_prefix + legal_after_laterPos +
  legal_middle_delete; NOTE: the bounded firstBreakWindow characterization
  exists in the sibling module (Formal_gen003c01_ab3ed070.lean L721:
  firstBreakWindow_some) but is NOT in the current target module -- either port
  it in or state the bounded version as a lemma.
- What is NOT formalized: bitmask operations, buckets, complexity/amortization,
  work-ratio. Lean is correctness-only and representation-abstract. State what
  the artifact does and does not prove, explicitly.

## 6. Related work (summary) — full doc in docs/related-work-dynamic-mcs.md
- Static MCS: RTL76, TY84, MCS-M (BHAH04).
- Dynamic chordality: Ibarra08, Mezzini12, BHV06, Banerjee18.
- Dynamic graph search: ES81, Baswana16, Chen18, Nakamura19.
- Verified graph algorithms: Gueneau19 (incremental cycle detection), union-find
  verifications, Isabelle AFP DFS, CLRS-Lean.

## 7. Evaluation
- Test bench design (exhaustive small n + random + adversarial sequences),
  pass rate 7524/7524, work_ratio 0.1817 vs offline.
- Reproducibility: verifier CLI, seed, bounds enumerated.

## 8. Conclusion and future work
- Reduce worst case: segment tree / Fenwick "first broken step" query (O(log n)
  probe), overlapped periodic rebuilding (Baswana16 lemma 6.1), amortized
  potential over ordering drift (Banerjee-style). All are future work, not
  claimed.
- Extend verification: time credits (Chargueraud-Pottier) for amortized
  complexity; bitmask/executable representation.

## Appendix A: Lean module theorem inventory + sorries (from gap analysis)
## Appendix B: Reproduction commands for the verifier and the Lean build

## Repo / artifact pointers
- Lean module: ThesisLean/ThesisLean/Formal_gen003c01_eea71821.lean
  (proof base: Formal_gen001c01_3939115c.lean)
- Candidate: runs/mcs_pressure_e2e/candidates/gen003_c01.py
- Verifier results: runs/mcs_pressure_e2e/generation_0003.json (PASS 7524/7524,
  work_ratio 0.1817)
## 9. Optimization attempt: O(log n) probe is impossible (negative result)
We investigated replacing the linear first-break probe (insertion windows
[pos[u]+1, pos[v]]) with an O(log n) binary search over a monotone predicate
backed by prefix sums / Fenwick. The required monotonicity claim is FALSE:
the predicate P(k) = (d(k) > c(k)) or (d(k) = c(k) and v < order[k]) where
d(k) = |N(v) ∩ prefix|, c(k) = |N(order[k]) ∩ prefix| is NOT a prefix —
6191 windows in the exhaustive universe (n<=6) show P=True followed by
P=False, and 2536 even among interior steps. Because each position's
predicate depends on the running prefix and competitors' cardinalities vary
independently, a sound first-break query needs the O(k) scan; a segment
tree/Fenwick cannot answer it. gen003_c02 keeps the exact O(k) probe and
adds a flag-gated periodic-rebuild lever (bounded worst-case suffix), which
is never slower on the recorded bench (0.1823 vs 0.1817, within noise) and
strictly faster on the exhaustive universe (0.2420 vs 0.2904). This negative
result is itself a contribution: it documents an information-theoretic
obstacle to sublinear probing for MCS-ordering maintenance.
