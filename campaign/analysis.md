# Evaluation results (eval1-eval3)

Factual summary of the experiments, as input for the thesis chapters. All
numbers come from the committed files named in each section; nothing here is
estimated.

## Setup

- **Problems:** dynamic BFS and DFS (calibration tier), dynamic LBFS (open
  tier), directed except LBFS.
- **Grades:** search grade during a run (all non-isomorphic graphs up to
  n = 4, every single update, 3 short sequences); final grade on the best
  candidates (n <= 5, 4,187,856 test sequences for BFS/DFS, 21,630 for LBFS).
- **Modes:**
  - `orchestrator`: generator, reflector and repairer agents, population 4,
    8 generations, 64 model-call budget.
  - `no_reflection`: the same without the reflection role.
  - `harness`: a single coding agent (enlcode with the `evoalgo` skill) that
    runs the edit-check loop itself; at most 8 checks, the final grade
    re-run by us.
  - `dynamic_agents`: orchestrator plus specialist agents spawned on a
    plateau (eval2 only).
- **Models:** Qwen3.8-27B-FP8 (eval1, eval2), Gemma-4-31B-it (eval3), both on
  EricAI. Thinking off.
- **Work ratio:** candidate time / offline baseline time on the final-grade
  graphs. The baseline runs on a numpy array, about 2x slower than the same
  algorithm on lists, so a recompute-from-scratch candidate scores 0.479
  (BFS), 0.847 (DFS), 0.818 (LBFS) rather than 1 (`eval1/reference.json`).
  **"vs recompute"** = work ratio / that reference; 1.0 = no better than
  recomputing. This is the metric to report.

## eval1: three modes x three problems x three seeds (Qwen)

Source: `eval1/results.csv`, `eval1/summary.md`, `eval1/bench.csv`.

| mode | final PASS | median vs recompute (BFS / DFS / LBFS) | median LLM turns | median tokens |
|---|---|---|---|---|
| orchestrator | 9/9 | 0.65 / 0.22 / 0.45 | 204-250 | 1.76 M |
| no reflection | 8/9 | 1.38 / 0.25 / 0.58 | 147-206 | 1.52 M |
| single agent (harness) | 9/9 | 0.69 / 0.32 / 0.21 | 35-60 | 1.93 M (2.22 M incl. the retried attempt) |

- 26 of 27 cells reach final-grade PASS. The miss is no-reflection BFS seed 3:
  all three graded candidates pass all 51,456 sequences up to n = 4 and fail
  the ninth at n = 5 (the grade stops at the first counterexample), which the
  n <= 4 search grade cannot see. This is the case the two-tier grade exists
  for.
- Every cell has a search-grade PASS by generation 3 (most in generation 1):
  correctness is reached quickly on these problems; the runs then spend their
  budget on cost.
- Reflection matters for efficiency more than for correctness: without it,
  BFS seed 2 passes with work ratio 1.10 (slower than recomputing).
- The single agent needs about 5x fewer LLM turns but uses similar or more
  tokens (long contexts). One harness cell needed a second attempt (the
  model ended a turn with an empty reply; retried by the campaign runner).

### Beyond the exhaustive bound

`eval1/bench.csv`: each passing final candidate against the recompute
candidate (same list representation) on random graphs n = 16, 64, 128, 10
graphs x 200 balanced insert/delete updates, invariant checked on every 10th
update, each cell in the sandbox jail with a 600 s budget.

| problem | orchestrator | no reflection | single agent |
|---|---|---|---|
| BFS, n = 128 | 66x | 18x | 37x |
| DFS, n = 128 | 2.6x | 1.1x | 4.0x |
| LBFS, n = 128 | 0.21x | 0.15x | 2.55x |

(median speedup over recomputing; > 1 is faster)

- No invariant violation on any graph beyond n = 5.
- Three LBFS cells time out (slow, not wrong).
- **Small-graph efficiency does not predict large-graph efficiency for LBFS:**
  orchestrator LBFS candidates are about 2x cheaper than recomputing at
  n <= 5 (vs recompute 0.45) but about 5x slower at n = 128. The single
  agent's LBFS candidates stay faster at every size.

## eval2: dynamic agent generation (Qwen, LBFS, 8 seeds)

Source: `eval2/results.csv`, `runs/eval2_*`. Config `eval2.yaml`: plateau
window 2 generations, epsilon 0.01, at most 1 active specialist, 3 candidates
per specialist, the same 64-call budget as the orchestrator arm. Seeds 1-3
ran first; seeds 4-8 were added because 3 seeds showed no clear effect.

| seed | dynamic agents: vs recompute | orchestrator: vs recompute | specialists / their candidates / gains |
|---|---|---|---|
| 1 | 0.43 | 0.71 | 2 / 4 / 0 |
| 2 | 1.30 | 0.31 | 1 / 3 / 1 |
| 3 | 0.56 | 0.36 | 1 / 2 / 0 |
| 4 | 0.44 | 0.45 | 2 / 5 / 2 |
| 5 | 0.28 | 0.57 | 2 / 3 / 0 |
| 6 | 0.33 | 0.45 (final FAIL) | 2 / 4 / 0 |
| 7 | 0.65 | 1.03 | 0 / 0 / 0 |
| 8 | 0.36 | 0.38 | 2 / 4 / 0 |
| **median** | **0.44** | **0.45** | |

- **The mechanism works as designed.** 7 of 8 runs detect an efficiency
  plateau (correct candidates, best work ratio flat for 2 generations),
  spawn a specialist whose focus is written from it, and retire it after its
  budget or a window without gain. In seed 7 the search kept improving, so
  no specialist was needed.
- **Specialists rarely help.** Of 25 specialist candidates, 3 became the
  population best. One of them, seed 4's gen007_c02, became the final answer
  (search work ratio 0.593 -> 0.470).
- **Outcome:** dynamic agents gave the lower final value in 6 of 8 paired
  seeds, but the medians are nearly equal (0.44 vs 0.45). Seed 2 has a large
  loss (+0.99). Exact two-sided Wilcoxon signed-rank test p = 0.46; sign test
  p = 0.29. **No significant effect at 8 seeds.**
- Final-grade correctness: 8/8 with dynamic agents, 7/8 without. In
  orchestrator seed 6, all three final candidates fail at n = 5, after
  1,154 to 1,610 passing sequences. One run is no evidence of a correctness effect.
- Cost: median 30 vs 28 model calls (same budget), with more tokens for
  dynamic agents (the specialists' prompts carry the plateau context).
- **The small-graph problem on LBFS:** seed 2's best search candidate (0.654
  on n <= 4) grades at 1.061 on n <= 5. The engine's final-candidate choice
  is correct: the two grades cover different graphs and update sequences.
- Selection seeding changed between the batches. Seeds 1-3 ran with one RNG
  stream per run; seeds 4-8 also ran on that code. The per-generation
  reseeding fixed afterwards (see the bug hunt) affects only future runs and
  resumed ones.

## eval3: second model (Gemma-4-31B-it, one seed)

Source: `eval3/results.csv`, `eval3/final_regrade.json`.

| mode | BFS | DFS | LBFS | LLM turns | tokens |
|---|---|---|---|---|---|
| orchestrator | PASS, 0.16 | PASS, 0.20 | PASS, 0.64 | 33-37 | 75-90 k |
| no reflection | PASS, 0.16 | PASS, 0.30 | PASS, 0.17 | 33-34 | 66-79 k |
| single agent | PASS*, 0.21 | PASS*, 0.20 | PASS, 0.62 | 16-18 | 358-407 k |

(final-grade verdict and raw work ratio)

- All 9 cells reach a correct, final-grade-passing candidate; every first
  search PASS is in generation 1.
- **\*** The harness agent's own `check --final` was killed by its shell's
  2-5 minute default timeout on BFS and DFS (the grade takes ~10 minutes).
  We re-graded the kept candidates (`final_regrade.json`): both pass all
  4,187,856 cases.
  - **Fix:** the skill and the workspace brief now tell the agent to give
    the command at least 15 minutes. eval1's Qwen sessions had set a 900 s
    timeout on their own.
- **Model comparison:** Gemma used 20-25x fewer tokens per orchestrator run
  than Qwen (66-90 k vs 0.6-4.6 M, medians 1.2-2.4 M per mode and problem) and finished in 1-16 minutes, with lower
  raw work ratios on BFS and DFS. One seed per cell, so this is an
  indication, not a measurement.

## Verifier (contribution 2)

Source: `selftest_dfs_n5.log`, `selftest_lbfs_n5.log`, `tests/test_verifier_iso.py`.

- **Self-test:** `evoalgo verify --problem dynamic_dfs --n-max 5` passes
  (ALL PASS).
  - The validate-or-rebuild reference and Yang et al.'s fully dynamic DFS
    (Algorithms 2-5, implemented in `selftest/references.py`) are accepted.
  - The equivalent control (different tie-break) is accepted.
  - All 22 real faults are rejected: 15 seeded faults and 7 one-line
    mutations of the Yang implementation. **Zero false negatives at n <= 5.**
    (BFS: 14 seeded faults, also all rejected.)
    D16 (wrong parent with valid times) was added after the bug hunt below.
- **LBFS corpus:** `evoalgo verify --problem dynamic_lbfs --n-max 5` passes
  (`selftest_lbfs_n5.log`). A validate-or-rebuild LBFS reference and an
  equivalent control (other start vertex and tie-break) are accepted; all 12
  seeded faults (L1-L12: missed updates, wrong refinement or pivot, wrong
  validity check, stale graph, incomplete ordering) are rejected. Each has a
  documented minimal counterexample (n <= 4), re-derived independently by a
  reviewer. For undirected problems the verifier tests every labelled graph,
  so the result does not depend on vertex labels. **Zero false negatives at
  n <= 5 for LBFS too**, which backs the LBFS PASS verdicts in eval1-eval3.
- **Neighbour order:** the Yang reference visits neighbours in old discovery
  order. The paper leaves the order open; vertex order (mutation Y7) breaks
  the tree over update sequences, and the self-test catches it only through
  its multi-step sequences.
- **Independent check:** a reviewer ran 1.44 M random updates (n = 6-30,
  eight densities) against the Yang reference and found no invariant
  violation.

## UI (contribution 1)

Source: `ui_check/*.png`, `runs/ui_browser_e2e_bfs`.

- **Browser run:** a run was launched from the New Run page in headless
  Chrome (dynamic BFS, 6 generations, dynamic agents on), monitored live,
  steered with a hint from the Steer panel (acknowledged by the engine at
  generation 2), and replayed with the generation scrubber after it ended
  (final PASS, n <= 4).
- **Access:** the browser went through the token link and an HttpOnly cookie
  (not visible to page scripts).
- **Failure patterns** (`ui_check/08_failures.png`, `09_failure_drawer.png`):
  a panel counts the failed candidates of each generation by kind (wrong
  after init / insert / delete, crash, timeout) and by size of the first
  failing graph; each bar segment opens an example candidate. On eval2 seed 4
  it shows 5 init and 5 insert failures, all at n = 3 or 4.

## Threats to validity

- Three seeds per cell in eval1, one in eval3, eight in eval2; medians, and an exact paired test only for eval2.
- Two models from one provider; no closed frontier model and no Claude Code
  or Codex sessions (no keys).
- Calibration problems are solved quickly; differences between modes show
  in cost, not in whether a correct algorithm is found.
- The work-ratio baseline is biased (see Setup); "vs recompute" corrects for
  it, but only on the n <= 5 graphs. Large-graph speedups come from the
  separate benchmark.
- LLM sampling is not seeded; only parent selection is.

## Bug hunt and hardening (after the campaigns)

Five read-only review agents and one security agent tried to break the tool.
These are the confirmed findings, each fixed with a regression test:

| area | finding | effect on reported results |
|---|---|---|
| DFS checker | accepted a parent tree no DFS produces (parent = shallower ancestor via a forward edge); NaN times could hang it | none: all 12 DFS finals re-graded PASS with the fixed checker (`dfs_checker_regrade.json`); an exhaustive n <= 4 cross-check over 274,942 certificates (every DFS-producible certificate and its single-field perturbations) gives 0 wrong verdicts (`scripts/dfs_certificate_crosscheck.py`, `dfs_certificate_crosscheck.log`) |
| SCC checker | pairwise maximality missed a cycle through 3+ components | none: no SCC campaign |
| Timing | a candidate could patch the clock, `range`, `json` or stdout, or cache by graph object across repeats | none found: no campaign candidate touches timing or these modules (grep); integrity stays best-effort against frame-walking code |
| Sandbox | world-readable host data (/var/log, /opt, /boot, /etc/ssh) was readable and could reach the LLM via the result | secrets, network and writes were blocked already; now hidden too; /etc stays (interpreter needs it) |
| Harness | agent could grade a file other than candidate.py, edit graded snapshots, exceed max_checks, run --final repeatedly | transcripts show none of this; now enforced, snapshots hashed (`final_intact` column) |
| Engine | resume reseeded selection differently and refunded calls of a crashed generation; duplicate specialist ids | no campaign run was resumed (one run_start per run) |
| UI server | first websocket after launch refused (403); control accepted on ended runs; dashboard HTML injection from LLM text | UI only |
| Sandbox limits | no CPU, memory, process, file or output limits: a candidate could fork, allocate or print without bound on the shared host; SysV shared memory outlived it; a deeply nested result crashed the verifier | none: all campaigns ran correct or failing candidates without such behaviour |

Since the bug hunt the runner limits itself before candidate code runs: 4 GB
address space, CPU time = timeout + 5 s, 4 tasks in its user namespace,
16 MB per file and 64 open files (memory files included), its own IPC
namespace, 256 MB of result output and 64 KB of stderr. A final-grade chunk
(1000 graphs at n = 5) peaks near 620 MB and returns about 50 MB, well
inside them. Negative tests cover fork and thread explosion, memory, memory
files, disk, shared memory, output floods, CPU spinning (also with SIGXCPU
ignored) and raising a limit.
