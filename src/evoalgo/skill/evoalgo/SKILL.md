---
name: evoalgo
description: Search for correct, efficient dynamic graph algorithms (incremental BFS, DFS, LexBFS, MCS, SCC, reachability) and grade them with evoalgo's exhaustive isomorphism-aware verifier. Use when the user wants to find or improve a dynamic graph algorithm, run an evoalgo problem pack, start or monitor an evoalgo multi-agent run, or inspect evoalgo run results.
compatibility: Requires the evoalgo Python package (the `evoalgo` command) and a shell.
metadata:
  homepage: https://github.com/thonmay/ai-dynamic-graph-algorithms
---

# evoalgo

evoalgo grades candidate algorithms on every non-isomorphic graph up to a
bound and on every single edge flip, so a PASS is strong evidence, and a
FAIL comes with the exact graph and update that broke it.

First run `evoalgo packs`. If the command is missing, tell the user to
install the package from a clone of the repo (`pip install -e '<repo>[api,ui]'`;
an editable install, because the problem packs live in the repo) and stop.

Pick the task:

| The user wants to | Do |
|---|---|
| find or improve an algorithm yourself | the loop below |
| start the multi-agent search and watch it | [references/orchestrator.md](references/orchestrator.md) |
| know how past runs went | [references/inspect.md](references/inspect.md) |

## The loop (you are the researcher)

1. List problems with `evoalgo packs` (name, tier, title, research question).
   `calibration` packs have known solutions; `open` ones may not. Ask the
   user which one if they have not said.
2. Create a workspace from the evoalgo repo root, so the run shows in the web UI:
   `evoalgo init <pack> --harness <claude|codex|opencode|agy> [--goal "..."]`.
   It prints the workspace path. Work only there.
3. Read `program.md` in the workspace in full. It holds the interface, the
   state contract the grader reads, the research brief and the loop rules.
   Follow it.
4. Edit `candidate.py`, then from the workspace run
   `evoalgo check --note "<what you changed>"`. Stdout is one JSON object.
   Exit 0 = PASS, 3 = FAIL or CRASH, 2 = error (message in `error`).
   On FAIL, `first_failure` has the graph, the operation and the wrong
   values; on CRASH, `error` has the exception and the line. The starter
   `candidate.py` raises NotImplementedError, so the first check is a CRASH.
5. Repeat. Correct first, then a lower `work_ratio`. Revert changes that
   break correctness or do not help.
6. When `search` passes and you stop improving, run `evoalgo check --final`
   once (n <= 5; up to ~12 minutes on directed problems). Give the shell
   command a timeout of at least 15 minutes (900000 ms): most agent shells
   stop a command after 2-5 minutes by default, which kills the grade before
   it reports. Then
   `evoalgo finish`, and report: final verdict, work ratio, the idea in two
   lines, and the workspace path.

Rules:

- Edit only `candidate.py`. Never edit `results.tsv`, `workspace.json`,
  `program.md`, `events.jsonl`, `config.yaml` or `candidates/`; they are the
  record of the session.
- Run one check at a time; a second check waits for the first.
- `--level examples` (n <= 3) is faster for quick iterations; the default
  `search` level (n <= 4) is what to optimise against.
- Do not special-case test graphs. The final grade covers more graphs and
  longer update sequences than the search grade.
- If a check times out, `first_failure.hang` names the graph and the update
  sequence that looped.
