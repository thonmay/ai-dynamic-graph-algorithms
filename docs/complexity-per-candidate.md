# Per-Candidate Complexity: Dynamic MCS Ordering Maintenance

Thesis documentation for todo item (2) of the parent thesis agent. This file
states, for each candidate algorithm in the `mcs_pressure_e2e` evolutionary
run, the maintained state, the initialization cost, the per-update worst-case
cost (probe and regreedy separately), the overall worst case, the measured
`work_ratio`, and a short complexity-theorem block. Every claim about the code
is grounded in the candidate source; every number is grounded in a generation
JSON or, where noted, in the paper skeleton (subagent-reported).

## Notation and measurement model

- `n = |V|` vertices, `m = |E|` edges, undirected, loop-free.
- `pos[v]` is the position of vertex `v` in the maintained ordering
  `order[0..n-1]`. For a flipped edge `(u, v)` we write `pu = pos[u]`,
  `pv = pos[v]`, and assume `pu < pv` (the later endpoint is `v`).
- `k = pv - pu` is the positional distance between the two endpoints.
- `m_suffix(k0) = |{ (a,b) in E : a or b in order[k0:] }|`, the number of
  edges incident to the suffix starting at `k0`.
- The offline baseline is a from-scratch MCS recomputation. It is
  `DynamicMCS.offline_compute` (`src/evoalgo/problem_definitions.py:537-557`):
  an outer loop of `n` steps, each doing an `O(n)` max over the unchosen plus
  an `O(n)` neighbor update, so `O(n^2)` per recomputation. The declared
  baseline work is `n*n` (`problem_definitions.py:559-561`).
- `work_ratio = candidate_work / offline_work`
  (`src/evoalgo/verifier.py:361`). Both numerators are accumulated measured
  times: `candidate_work` sums the sandbox timing of the candidate's `init`
  plus every update in each sequence (`verifier.py:305-308`, `335-338`), and
  `offline_work` sums the same for the offline baseline. The bench is the
  "random" universe: `n_max = 6`, `n_random = 20`, `seq_len_max = 12`,
  `seq_count = 6`, `seed = 1337` (all `generation_000X.json`, `bound`),
  7524 cases.

The `work_ratio` values below are the latest recorded value for each candidate
id across `generation_0001.json` ... `generation_0005.json`.

| candidate | work_ratio | source file |
|-----------|-----------|-------------|
| gen001_c01 | 0.4830733307043726 | generation_0001.json |
| gen001_c02 | 0.4207250912946305 | generation_0001.json (repeated in 0002) |
| gen001_c03 | 0.3500706620915409 | generation_0001.json (repeated in 0002, 0003) |
| gen002_c01 | 0.18973672457322166 | generation_0002.json (repeated in 0003, 0004, 0005) |
| gen003_c01 | 0.1816654569102273 | generation_0003.json (repeated in 0004, 0005) |
| gen003_c02 | not recorded in any generation JSON | see note below |
| gen004_c01 | 0.2503642969435731 | generation_0004.json |
| gen005_c01 | 0.18732924561548633 | generation_0005.json |

`gen003_c02` was never promoted into a generation JSON, so it has no recorded
`work_ratio` in the run files. The paper skeleton reports subagent-measured
numbers for it (exhaustive universe 0.2420 vs gen003_c01 0.2904; random bench
0.1823 vs gen003_c01 0.1817) at `docs/paper-skeleton.md:133-134`. These are
marked subagent-reported here; I did not run the verifier.

---

## gen001_c01

**State and update strategy.** Maintains `ordering` (list), `pos` (list), and
`adj` (list of neighbor sets) (`gen001_c01.py:54`). On any flip it updates the
two adjacency sets in `O(1)` and then always re-runs bucket greedy MCS on the
suffix starting at `min(pos[u], pos[v]) + 1` (`gen001_c01.py:57-74`). There is
no probe: the repair is unconditional.

**Initialization.** Builds `adj` from the `n x n` matrix in `O(n^2)`
(`gen001_c01.py:46-50`), then runs `_mcs_repair(..., 0)` over the whole order.
`_mcs_repair` seeds each suffix vertex's cardinality by summing over its
neighbors (`gen001_c01.py:21-24`, `O(m_suffix)`) and then runs the bucket
selection loop, moving each neighbor up one bucket on a choice
(`gen001_c01.py:27-41`, `O(n + m_suffix)`). Init is therefore `O(n^2 + n + m)`,
dominated by `O(n^2)`.

**Per-update worst case.** No probe. The regreedy `_mcs_repair` at
`k0 = min(pu, pv) + 1` costs `O(n + m_suffix(k0))`: the `in_prefix` build is
`O(k0) <= O(n)`, the seeding is `O(m_suffix)`, and the selection loop is
`O(n + m_suffix)` (`gen001_c01.py:12-41`). Worst case `k0 = 1` gives
`O(n + m)`.

**Overall worst case.** `O(n + m)` per update, i.e. no better than
recomputation; space `O(n + m)`.

**Measured work_ratio.** 0.4830733307043726 (generation_0001.json).

**Complexity theorem.**

> Theorem (gen001_c01). Maintaining a deterministic MCS ordering under
> single-edge insertions and deletions by unconditionally regreedy-ing the
> suffix from `min(pu, pv) + 1` costs `O(n + m_suffix)` per update, with
> `m_suffix` the number of edges incident to that suffix. The worst case over
> all updates is `O(n + m)`, equal to from-scratch recomputation. Space is
> `O(n + m)`.

---

## gen001_c02

**State and update strategy.** Same state as gen001_c01: `ordering`, `pos`,
`adj` sets (`gen001_c02.py:58`). The difference is an asymmetric restart point
(`gen001_c02.py:61-77`): insertion regreeds from `min(pu, pv) + 1`, deletion
regreeds from `max(pu, pv)`. Still no probe; the regreedy is unconditional, and
the tie-break is an arbitrary `set.pop()` rather than `min`
(`gen001_c02.py:35`).

**Initialization.** Builds `adj` in `O(n^2)` (`gen001_c02.py:50-54`), then
`_mcs_regreedy(..., 0)` over the whole order, `O(n + m)`. Init is `O(n^2 + n + m)`.

**Per-update worst case.** No probe. `_mcs_regreedy` at `k0` costs
`O(n + m_suffix(k0))` (`gen001_c02.py:17-45`): `in_prefix` build `O(k0)`,
seeding `O(m_suffix)`, selection loop `O(n + m_suffix)`. Worst case `O(n + m)`.

**Overall worst case.** `O(n + m)` per update; space `O(n + m)`.

**Measured work_ratio.** 0.4207250912946305 (generation_0001.json).

**Complexity theorem.**

> Theorem (gen001_c02). Maintaining a deterministic MCS ordering by
> unconditionally regreedy-ing the suffix from an asymmetric restart point
> (`min(pu, pv) + 1` on insertion, `max(pu, pv)` on deletion) costs
> `O(n + m_suffix)` per update. The worst case over all updates is
> `O(n + m)`, equal to from-scratch recomputation. Space is `O(n + m)`.

---

## gen001_c03

**State and update strategy.** Maintains `n`, `adj` (sets), `order`, `pos`
(`gen001_c03.py:51`). On a flip it updates the adjacency sets in `O(1)`, keeps
the prefix through `min(pu, pv)` (provably still a valid MCS prefix), recomputes
each unchosen vertex's cardinality against that prefix, and regreeds the suffix
with `_bucket_mcs` (`gen001_c03.py:67-96`). No probe; the regreedy is
unconditional.

**Initialization.** Builds `adj` in `O(n^2)` (`gen001_c03.py:56-61`), then a
from-scratch `_bucket_mcs` over all `n` vertices, `O(n + m)`
(`gen001_c03.py:18-44`). Init is `O(n^2 + n + m)`.

**Per-update worst case.** No probe. `_update` builds `chosen` in `O(n)`,
recomputes `cards` by summing each unchosen vertex's neighbors in `O(n + m)`
(`gen001_c03.py:83-93`), then runs `_bucket_mcs` on the suffix in
`O(n + m_suffix)`, then rebuilds the state in `O(n)` (`gen001_c03.py:95-96`).
Total per update `O(n + m)`.

**Overall worst case.** `O(n + m)` per update; space `O(n + m)`.

**Measured work_ratio.** 0.3500706620915409 (generation_0001.json).

**Complexity theorem.**

> Theorem (gen001_c03). Maintaining a deterministic MCS ordering by keeping the
> prefix through `min(pu, pv)`, recomputing suffix cardinalities against that
> prefix, and regreedy-ing the suffix costs `O(n + m)` per update (the
> cardinality recomputation alone is `O(n + m)`). The worst case over all
> updates is `O(n + m)`, equal to from-scratch recomputation. Space is
> `O(n + m)`.

---

## gen002_c01

**State and update strategy.** Maintains `n`, `mask` (one adjacency bitmask per
vertex), `order`, `pos` (`gen002_c01.py:81`). A flip is two integer bit ops
(`gen002_c01.py:87-92`). The regreedy uses bitmask buckets: seed each suffix
vertex's cardinality as `popcount(mask[v] & prefix)`, pick the smallest id in
the top bucket via the lowbit, and move neighbors up one bucket on a choice
(`gen002_c01.py:24-65`). No probe; the regreedy is unconditional, from
`k0 = pu + 1` (insertion) or `k0 = pv` (deletion) (`gen002_c01.py:100-101`).

**Initialization.** Builds `mask` in `O(n^2)` (`gen002_c01.py:71-77`), then
`_regreedy(..., 0)` over the whole order, `O(n + m)`. Init is `O(n^2 + n + m)`.

**Per-update worst case.** No probe. `_regreedy` at `k0` costs
`O(n + m_suffix(k0))`: the `remaining`/`prefix` setup is `O(n - k0)`, the
seeding loop is `O(n - k0)` bit_counts, and the selection loop processes each
suffix edge once (`gen002_c01.py:26-65`). Each `bit_count` on an `n`-bit mask
is one word-popcount; in bit-complexity it is `O(n / w)` for word size `w`,
treated as `O(1)` word ops. Worst case `O(n + m)`.

**Overall worst case.** `O(n + m)` per update; space `O(n + m)`. The drop from
gen001_c03 (0.3501) to 0.1897 is a constant-factor win from replacing Python
set operations with hardware bit counts, not an asymptotic change.

**Measured work_ratio.** 0.18973672457322166 (generation_0002.json).

**Complexity theorem.**

> Theorem (gen002_c01). Maintaining a deterministic MCS ordering with bitmask
> adjacency and bitmask buckets, by unconditionally regreedy-ing the suffix
> from `pu + 1` (insertion) or `pv` (deletion), costs `O(n + m_suffix)` per
> update (word-ops; `O(n^2 / w + m_suffix)` in bit-complexity for the
> popcounts). The worst case over all updates is `O(n + m)`, equal to
> from-scratch recomputation. Space is `O(n + m)`.

---

## gen003_c01

**State and update strategy.** Maintains `n`, `mask` (adjacency bitmasks),
`order`, `pos` (`gen003_c01.py:128`). A flip is two bit ops. The update first
runs a tight local probe to find the first step whose MCS choice breaks, and
only if a break is found does it regreedy the suffix from that step
(`gen003_c01.py:131-155`). This is the first candidate with a probe.

**Initialization.** Builds `mask` in `O(n^2)` (`gen003_c01.py:117-124`), then
`_regreedy(..., 0)` over the whole order, `O(n + m)`. Init is `O(n^2 + n + m)`.

**Per-update worst case.**
- Insertion probe `_first_break(order, mask, pu + 1, pv, v)`
  (`gen003_c01.py:80-96`, called at `:150`): builds the prefix mask
  `_prefix_mask(order, pu + 1)` in `O(pu)`, then scans the window
  `[pu + 1, pv]` in `O(k)` steps, each a `bit_count` plus a constant. Probe
  cost `O(pu + k)`, worst case `O(n)`.
- Deletion probe `_deletion_breaks(order, mask, pv, v)`
  (`gen003_c01.py:99-112`, called at `:152`): builds `_prefix_mask(order, pv)`
  in `O(pv)`, then scans the whole suffix `order[pv+1:]` in `O(n - pv)` steps.
  Probe cost `O(n)` worst case.
- If a break is found at step `k0`, `_regreedy(order, pos, mask, n, k0)`
  (`gen003_c01.py:36-77`) costs `O(n + m_suffix(k0))`, worst case `O(n + m)`.
- If no break, total update cost is just the probe: `O(pu + k)` (insertion) or
  `O(n)` (deletion).

**Overall worst case.** `O(n + m)` per update (probe plus a full regreedy);
space `O(n + m)`.

**Measured work_ratio.** 0.1816654569102273 (generation_003.json). This is the
best random-bench value in the run and the one cited in the paper skeleton
(0.1817).

**Complexity theorem.**

> Theorem (gen003_c01). Maintaining a deterministic MCS ordering under
> single-edge insertions and deletions by a tight affected-window probe plus a
> conditional suffix regreedy requires, on insertion of `(u, v)` with
> `pu < pv`, an `O(pu + k)` probe (`k = pv - pu`) and, if a break is detected
> at step `k0`, an `O(n + m_suffix(k0))` regreedy; on deletion, an `O(n)`
> probe and, if step `pv` breaks, an `O(n + m_suffix(pv))` regreedy. If no
> break is found the total update cost is the probe alone. The worst case over
> all updates is `O(n + m)`, i.e. no better than recomputation. Space is
> `O(n + m)`.

---

## gen003_c02

**State and update strategy.** Keeps the linear `O(k)` probe from gen003_c01
verbatim (`gen003_c02.py:122-159`, identical to `gen003_c01.py:80-112`) and the
same conditional `_regreedy` (`gen003_c02.py:78-119`). The only addition is a
flag-gated periodic full rebuild: `USE_PERIODIC_REBUILD = False` and
`REBUILD_PERIOD = 64` (`gen003_c02.py:66-67`). When the flag is enabled, every
`REBUILD_PERIOD`-th update runs a full `_regreedy(..., 0)` and resets a
per-update counter (`gen003_c02.py:209-215`). The docstring records the
negative result that motivated this design: the proposed `O(log n)`
binary-search probe is unsound because the first-break predicate is not
monotone (6191 non-monotone windows in the exhaustive universe)
(`gen003_c02.py:7-59`).

**Initialization.** Builds `mask` in `O(n^2)` (`gen003_c02.py:164-171`), then
`_regreedy(..., 0)`, `O(n + m)`, and initializes
`updates_since_rebuild = 0` (`gen003_c02.py:175-181`). Init is `O(n^2 + n + m)`.

**Per-update worst case.**
- Probe and regreedy are identical to gen003_c01: insertion `O(pu + k)` probe,
  deletion `O(n)` probe, and on a break `O(n + m_suffix(k0))` regreedy.
- Periodic rebuild (only when `USE_PERIODIC_REBUILD` is True): one full
  `_regreedy(..., 0)` of `O(n + m)` every `REBUILD_PERIOD = 64` updates, i.e.
  an amortized `O((n + m) / 64)` per update, which bounds the worst-case
  accumulated suffix a pending break can leave mis-ordered
  (`gen003_c02.py:62-67`, `209-215`).
- With the flag disabled (the default), the update is identical to
  gen003_c01's probe plus conditional regreedy; the worst case over all
  updates is `O(n + m)`.

**Overall worst case.** `O(n + m)` per update; space `O(n + m)`.

**Measured work_ratio.** Not recorded in any generation JSON. Subagent-reported
(from `docs/paper-skeleton.md:133-134`, not reproduced here because the
verifier is broken in this shell): exhaustive universe 0.2420 for gen003_c02
vs 0.2904 for gen003_c01; random bench 0.1823 for gen003_c02 vs 0.1817 for
gen003_c01. The random-bench gen003_c01 figure (0.1817) matches the generation
JSON; the exhaustive-universe figures (0.2904, 0.2420) are a different, larger
universe (all labeled loop-free undirected graphs on `n = 2..6`, every absent
edge as an insertion, per `gen003_c02.py:26-30`) and do not appear in the run
files.

**Complexity theorem.**

> Theorem (gen003_c02). gen003_c02 has the same probe and regreedy costs as
> gen003_c01: insertion `O(pu + k)` probe, deletion `O(n)` probe, and on a
> break `O(n + m_suffix(k0))` regreedy, worst case `O(n + m)` per update,
> space `O(n + m)`. In addition, when `USE_PERIODIC_REBUILD` is enabled with
> `REBUILD_PERIOD = 64`, it performs one full `O(n + m)` rebuild every 64
> updates, adding an amortized `O((n + m) / 64)` per update and bounding the
> worst-case suffix drift left by a pending break. With the flag disabled the
> update is identical to gen003_c01.

---

## gen004_c01

**State and update strategy.** Maintains `n`, `mask`, `order`, `pos`, plus
three extra structures (`gen004_c01.py:150-159`): `card_at[k]` (the
cardinality of `order[k]` at its selection step), `buckets[c]` (bitmask of
steps whose `card_at` equals `c`), and `pref[k]` (bitmask of `order[:k]`),
together with `peak` (highest nonempty bucket). A flip changes exactly one
`card_at` entry, `card_at[pv]` (`gen004_c01.py:8-12`). The probes read the old
max in `O(1)` from `card_at` / `pref` instead of recomputing popcounts
(`gen004_c01.py:94-137`).

**Initialization.** Builds `mask` in `O(n^2)` (`gen004_c01.py:143-149`), then
`_regreedy(st, 0)` over the whole order, which also builds `card_at`,
`buckets`, `pref`, `peak` (`gen004_c01.py:29-91`). Init is `O(n^2 + n + m)`.

**Per-update worst case.**
- Insertion probe `_first_break(st, pu, pv, v)` (`gen004_c01.py:94-111`,
  called at `:182`): seeds `d` from `pref[pu + 1]` in `O(1)`, then scans the
  window `[pu + 1, pv)` in `O(k)` steps, each `O(1)` (reads `card_at[k]` and
  one bit test). Probe cost `O(k)`, worst case `O(n)`.
- Deletion probe `_deletion_breaks(st, pv, v)` (`gen004_c01.py:114-137`,
  called at `:184`): reads `c = card_at[pv] - 1` in `O(1)`, unions the bucket
  candidates with `card_at` in `[c, peak]` in `O(peak - c) <= O(n)`, masks out
  steps `<= pv`, then visits only the candidate steps, each an `O(1)`
  popcount. Probe cost `O(n)` worst case (bounded by bucket candidates, not a
  full suffix scan).
- If a break is found at `k0`, `_regreedy(st, k0)` (`gen004_c01.py:29-91`)
  costs `O(n + m_suffix(k0))` and refreshes `card_at`, `buckets`, `pref`,
  `peak` for the rewritten suffix.
- If no break, the update is `O(1)`: it moves the single `card_at[pv]` entry
  between buckets and adjusts `peak` (`gen004_c01.py:187-198`).

**Overall worst case.** `O(n + m)` per update (probe plus a full regreedy);
space `O(n + m)`. The random-bench work_ratio (0.2504) is worse than
gen003_c01 (0.1817): the extra `pref`/`card_at`/`buckets` bookkeeping adds
overhead that outweighs the cheaper probe on this bench.

**Measured work_ratio.** 0.2503642969435731 (generation_004.json).

**Complexity theorem.**

> Theorem (gen004_c01). Maintaining a deterministic MCS ordering with
> incrementally-updated `card_at`, `buckets`, and `pref` structures requires,
> on insertion of `(u, v)` with `pu < pv`, an `O(k)` probe (`k = pv - pu`) and,
> if a break is detected at step `k0`, an `O(n + m_suffix(k0))` regreedy that
> also refreshes the auxiliary structures; on deletion, an `O(n)` probe and,
> if step `pv` breaks, an `O(n + m_suffix(pv))` regreedy. If no break is found
> the total update cost is `O(1)`. The worst case over all updates is
> `O(n + m)`, i.e. no better than recomputation. Space is `O(n + m)`.

---

## gen005_c01

**State and update strategy.** Maintains `n`, `mask`, `order`, `pos`, plus
`sel_card[v]`, the cardinality of `v` at its own selection step
(`gen005_c01.py:128-129`). A flip changes `sel_card` for exactly one vertex,
`v`, by a single `+/-1` (`gen005_c01.py:149-156`). The probes read the old max
in `O(1)` from `sel_card[order[k]]` instead of a per-step popcount
(`gen005_c01.py:77-111`), but still build the prefix mask with `_prefix_mask`
(`gen005_c01.py:86`, `104`).

**Initialization.** Builds `mask` in `O(n^2)` (`gen005_c01.py:117-123`), then
`_regreedy(order, pos, sel_card, mask, n, 0)` over the whole order, which sets
`sel_card[v] = maxc` at each selection (`gen005_c01.py:32-74`, `63`). Init is
`O(n^2 + n + m)`.

**Per-update worst case.**
- Insertion probe `_first_break(order, mask, sel_card, pu + 1, pv, v)`
  (`gen005_c01.py:77-95`, called at `:153`): builds `_prefix_mask(order, pu + 1)`
  in `O(pu)`, seeds `d` with one popcount, then scans the window `[pu + 1, pv]`
  in `O(k)` steps, each `O(1)` (reads `sel_card[order[k]]` and one bit test).
  Probe cost `O(pu + k)`, worst case `O(n)`.
- Deletion probe `_deletion_breaks(order, mask, sel_card, pv, v)`
  (`gen005_c01.py:98-111`, called at `:156`): builds `_prefix_mask(order, pv)`
  in `O(pv)`, reads `c = sel_card[v]` in `O(1)`, then scans the whole suffix
  `order[pv+1:]` in `O(n - pv)` steps, each a popcount. Probe cost `O(n)` worst
  case.
- If a break is found at `k0`, `_regreedy(order, pos, sel_card, mask, n, k0)`
  (`gen005_c01.py:32-74`) costs `O(n + m_suffix(k0))` and refreshes `sel_card`
  for the rewritten suffix.

**Overall worst case.** `O(n + m)` per update (probe plus a full regreedy);
space `O(n + m)`.

**Measured work_ratio.** 0.18732924561548633 (generation_0005.json).

**Complexity theorem.**

> Theorem (gen005_c01). Maintaining a deterministic MCS ordering with an
> incrementally-updated `sel_card` array requires, on insertion of `(u, v)`
> with `pu < pv`, an `O(pu + k)` probe (`k = pv - pu`) and, if a break is
> detected at step `k0`, an `O(n + m_suffix(k0))` regreedy that refreshes
> `sel_card`; on deletion, an `O(n)` probe and, if step `pv` breaks, an
> `O(n + m_suffix(pv))` regreedy. If no break is found the total update cost is
> the probe alone. The worst case over all updates is `O(n + m)`, i.e. no
> better than recomputation. Space is `O(n + m)`.

---

## Summary table

| candidate | work_ratio | probe cost | regreedy cost | worst case | note |
|-----------|-----------|-----------|--------------|-----------|------|
| gen001_c01 | 0.4831 | none (always regreedy) | `O(n + m_suffix)` | `O(n + m)` | set buckets, unconditional suffix repair from `min+1` |
| gen001_c02 | 0.4207 | none (always regreedy) | `O(n + m_suffix)` | `O(n + m)` | asymmetric restart (`min+1` ins / `max` del), `set.pop` tie-break |
| gen001_c03 | 0.3501 | none (always regreedy) | `O(n + m)` | `O(n + m)` | recomputes suffix cards against prefix, then `_bucket_mcs` |
| gen002_c01 | 0.1897 | none (always regreedy) | `O(n + m_suffix)` | `O(n + m)` | first bitmask version; constant-factor win, same asymptotics |
| gen003_c01 | 0.1817 | ins `O(pu + k)`, del `O(n)` | `O(n + m_suffix)` | `O(n + m)` | first probe; best random-bench value |
| gen003_c02 | not recorded (subagent: 0.1823 rand / 0.2420 exhaustive) | ins `O(pu + k)`, del `O(n)` | `O(n + m_suffix)` (+ amortized `O((n+m)/64)` if rebuild on) | `O(n + m)` | gen003_c01 probe verbatim + flag-gated periodic rebuild (default off) |
| gen004_c01 | 0.2504 | ins `O(k)`, del `O(n)` | `O(n + m_suffix)` | `O(n + m)` | `card_at`/`buckets`/`pref`; no-break update `O(1)`; slower on bench |
| gen005_c01 | 0.1873 | ins `O(pu + k)`, del `O(n)` | `O(n + m_suffix)` | `O(n + m)` | `sel_card` array read; keeps `O(pu)` prefix-mask build |

`work_ratio` values are the latest recorded per candidate across
`generation_0001.json` ... `generation_0005.json` (see the provenance table at
the top). `gen003_c02` has no recorded value in the run files; its numbers are
subagent-reported from `docs/paper-skeleton.md:133-134`.

## Ungrounded claims

- The `work_ratio` for `gen003_c02` (0.2420 exhaustive, 0.1823 random) and the
  `gen003_c01` exhaustive-universe figure (0.2904) are taken from
  `docs/paper-skeleton.md:133-134` and are subagent-reported. I did not run the
  verifier (it is broken in this shell), so these three numbers are not
  independently reproduced here. The random-bench `gen003_c01` figure (0.1817)
  is grounded in `generation_0003.json`.
- No other number in this file is ungrounded: every `work_ratio` in the
  provenance table appears verbatim in a generation JSON, and every
  complexity claim cites the candidate source by function and line.
