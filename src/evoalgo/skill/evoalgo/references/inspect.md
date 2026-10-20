# Inspect past runs

Run from the folder that contains `runs/`.

- All runs, newest first: `evoalgo history --json`. Each entry has `run_id`,
  `problem`, `state`, `generation`, `best_id`, `best_fitness`,
  `best_work_ratio`, `harness` (true for agent workspaces) and, when the run
  was final-graded, `final_grade` and `best_candidate_path`.
- One run: `evoalgo status runs/<run_id> --json`.
- The algorithm: read `best_candidate_path`.
- Why a candidate failed: `runs/<run_id>/events.jsonl`, the
  `candidate_verified` line for that id (`failing_case`), and
  `runs/<run_id>/reflections/<id>.md` when present.

How to read the numbers:

- `fitness` is the fraction of graded sequences passed; only 1.0 is correct.
- `work_ratio` is measured candidate time over offline recompute time on the
  graded graphs. These graphs are tiny (n <= 5), so constant overhead
  dominates; treat it as a ranking signal, not an asymptotic claim.
- The final grade (n <= 5, all non-isomorphic graphs, millions of sequences
  on directed problems) is the result to report. A search-grade PASS
  (n <= 4) can still fail it.
