# Thesis project notes (evoalgo)

ELTE IK BSc thesis "AI-Assisted Discovery of Dynamic Graph Algorithms via
Evolutionary Code Repair" (Thonmay Md Thoriqul Islam, FFR8A9; supervisor
Gregory Reynolds Morse). Read this file before working on the thesis text.
Agent notes and trackers live in this repo root, never in `.enlcode/`.

## Repo rules
- Commit and push to `main` (GitHub `thonmay/ai-dynamic-graph-algorithms`, public since 2026-11-27) without asking; stage files explicitly.
- Never commit: the paths listed in `.gitignore` (personal notes, `docs/`, `papers/`, `logs/`, supervisor skills, third-party Lean skills), `review_*`, `review-manuscript.txt`, `round2_checks.zip`, `stab.c`, `supervisor-review.txt`, the supervisor's `*_Audit_*.md` files, stray `runs/` dirs, and the user's local edit of `runs/mcs_pressure_e2e/formalization/gen003_c01.json`.
- Scratch goes in `/proj/MPS/MPS_DEV_REPO/ethomdt/evoalgo-scratch/`, never `/tmp` or `/home`; clean up after each task.
- The code is frozen except for fixes; the remaining work is the thesis documentation.
- Another agent (agy) pushes `fix/*` branches; review them (code-reviewer agent) before merging. `origin/fix/antigravity-support` holds an unmerged `provider: agy` backend with review notes in `AGY_REVIEW.md`; not before submission.

## Build and test
- Python: `.venv/bin/pytest -q -m "not slow" --basetemp=<scratch>/pt -p no:cacheprovider` (slow corpus: `-m slow`, about 20 min). Set `TMPDIR` under scratch: the agent jail makes `/tmp` private.
- UI: `export PATH=/app/vbuild/SLED15-x86_64/nodejs/24.19.0/bin:$PATH; cd ui && npx vitest run && npx tsc --noEmit -p . && npm run build` (writes `src/evoalgo/ui_dist`, tracked).
- Thesis PDF: `export PATH=/app/vbuild/SLED15-x86_64/texlive/2026/bin/x86_64-linux:$PATH; cd thesis-doc && latexmk -pdf main.tex` (`module add texlive/2024` adds no binaries on SLED15). `thesis-doc/main.pdf` is tracked but ignored: `git add -f`.
- Execution record: `scripts/execution_record.sh <repo> <rev> <out> <python3.11>` (32 steps, about 50 min, Node 22 on PATH, redaction env vars as in its header); the result replaces `campaign/execution_record/`.
- Review archive `thonmay-review.zip`: PDF, LaTeX source zip, code zip with redacted `campaign/` and cited `runs/` (built by `evoalgo-scratch/build_evidence.py`), `SUBMISSION_MANIFEST.md` with hashes. Not the final Neptun zip.
- CI: GitHub Actions `tests.yml` (lint, pytest 3.11/3.12, UI) and `lean.yml`; CI only, no CD.

## Thesis baseline and rules
- Contract: the approved registration form `topic-proposal-registration.pdf` (embedded as `thesis-doc/approved-topic-registration.pdf`). Contributions: C1 research UI, C2 isomorphism-aware verifier (zero false negatives at n <= 5, Yang et al. DFS accepted), C3 cooperative and dynamic agents.
- Cover metadata (`thesis-doc/config.tex`) matches the form; cover year 2027 (January 2027 session).
- Faculty length rule: body (Chapters 1-7) 40-80 pp, bibliography and appendices excluded; currently printed pp. 6-85 minus the divider = 79 pp. Ch2 must stay at least 20 pp.
- Style: no em or en dashes in the text (bibliography page ranges from plainnat are fine), British spelling, `-{}-` inside `\texttt`, no invented facts; every number must trace to `campaign/` or `runs/`.
- Final-exam topics, registered 2026-10-31: 8 OOM (first), 19 Concurrent programming, 17 Operating systems; woven into Design and Implementation, never labelled. Private coverage map: `exam-topic-coverage.md`. `docs/final-exam-topics.pdf` holds personal data: keep it out of every zip.
- Evidence: `campaign/analysis.md` (eval1-eval3, self-tests, UI check, bug hunt), `campaign/execution_record/`, `campaign/eval*/results.csv`.
- Turnitin: AI-writing detection is in the report; students may self-check in the supervisor's class (3 per 24 h).

## Status (2026-11-28)
- Code described: `141f6e2` (agent jail fixes, merged agy fixes, Antigravity skill path); execution record on it: 32/32, 206 pytest. Review zip built on `2ee0f47`.
- Self-audit by the bsc-thesis agent (CP5 and 30-point skills), final on `26fe1e0`: CP5 Sufficient, 24/30 awarded + 6 pending demo, 0 lost, excluding student-only items.
- Supervisor audits of 2026-11-25 (repo root, untracked): CP5 Insufficient, 18 confirmed, 4 lost, 8 open; the repo-fixable findings are resolved.
- Needs the supervisor's agreement: the FR-VER-09 exception for the unconfined workspace harness (eval1 harness agents read `verifier.py` and `problem_definitions.py`; disclosed in 2.5.6 and 6.8.5).
- Student-only, open: sign `thesis-doc/ai-declaration.docx` by hand and scan it; accepted exam-registration form; live demo with the supervisor (C7, 6 points); Turnitin self-check and rewriting research passages in own words (Ch1 1.1 and 1.3 bullets, Ch6 6.8 interpretation, Ch7), then update Table 5.2 and the declaration; upload `THONMAY_FFR8A9_THESIS.zip` to Neptun by 1 Dec 2026.
- Defense deck draft: `defense/draft/index.html` (12 min, S1-S10 + backups); committee profiles in `evoalgo-scratch/defense/guide.md`.
