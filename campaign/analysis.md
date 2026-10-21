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
| single agent (harness) | 9/9 | 0.69 / 0.32 / 0.21 | 35-60 | 1.93 M |

- 26 of 27 cells reach final-grade PASS. The miss is no-reflection BFS seed 3:
  all three graded candidates fail 1 of 51,465 cases at n = 5, which the
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

## eval2: dynamic agent generation (Qwen, LBFS, 3 seeds)

Source: `eval2/results.csv`, `runs/eval2_*`. Config `eval2.yaml`: plateau
window 2 generations, epsilon 0.01, at most 1 active specialist, 3 candidates
per specialist.

| seed | dynamic agents: vs recompute | orchestrator: vs recompute | plateaus / specialists / specialist candidates |
|---|---|---|---|
| 1 | 0.43 | 0.71 | 2 / 2 / 4 |
| 2 | 1.30 | 0.31 | 1 / 1 / 3 |
| 3 | 0.56 | 0.36 | 1 / 1 / 2 |

- **The mechanism works as designed.** All three runs detect an efficiency
  plateau (correct candidates, best work ratio flat for 2 generations),
  spawn a specialist with a focus written from it, and retire it after its
  budget or a window without gain.
- **Specialists rarely help.** Of 9 specialist candidates, 1 became the
  population best (seed 2, gen006_c02, search work ratio 0.683 -> 0.657);
  the others were slower or failed correctness. None was the final graded
  candidate.
- The final results differ between the arms (one better, two worse), but
  the arms also differ in how many model calls the rest of the search made
  (26-28 vs 26-49), and with 3 seeds the spread between seeds is larger than
  the difference between arms. **No effect can be claimed in either
  direction** from this sample.
- Seed 2 shows the LBFS small-graph problem again: its best search candidate
  (0.654) grades at 1.061 on n <= 5.

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

Source: `selftest_dfs_n5.log`, `tests/test_verifier_iso.py`.

- **Self-test:** `evoalgo verify --problem dynamic_dfs --n-max 5` passes
  (ALL PASS).
  - The validate-or-rebuild reference and Yang et al.'s fully dynamic DFS
    (Algorithms 2-5, implemented in `selftest/references.py`) are accepted.
  - The equivalent control (different tie-break) is accepted.
  - All 21 real faults are rejected: 14 seeded faults and 7 one-line
    mutations of the Yang implementation. **Zero false negatives at n <= 5.**
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

## Threats to validity

- Three seeds per cell (one in eval3); medians only, no significance claims.
- Two models from one provider; no closed frontier model and no Claude Code
  or Codex sessions (no keys).
- Calibration problems are solved quickly; differences between modes show
  in cost, not in whether a correct algorithm is found.
- The work-ratio baseline is biased (see Setup); "vs recompute" corrects for
  it, but only on the n <= 5 graphs. Large-graph speedups come from the
  separate benchmark.
- LLM sampling is not seeded; only parent selection is.
