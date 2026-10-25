# Thesis project notes (evoalgo)

ELTE IK BSc thesis "AI-Assisted Discovery of Dynamic Graph Algorithms via
Evolutionary Code Repair" (Thonmay Md Thoriqul Islam, FFR8A9; supervisor
Gregory Reynolds Morse). Status, decisions and the chapter plan are in
`.enlcode/thesis.md`; read it before working on the thesis text.

## Repo rules
- Commit and push to `main` (GitHub `thonmay/ai-dynamic-graph-algorithms`) without asking; stage files explicitly.
- Never commit: `papers/`, `docs/`, `logs/`, `review_*`, `review-manuscript.txt`, `round2_checks.zip`, `stab.c`, `supervisor-review.txt`, stray `runs/` dirs, and the pending deletions of `docs/mcs-thesis.html` and `scripts/pdf2md_mineru.py`.
- Scratch goes in `/proj/MPS/MPS_DEV_REPO/ethomdt/evoalgo-scratch/`, never `/tmp` or `/home`; clean up after each task.
- The code is frozen except for fixes; the remaining work is the thesis documentation.

## Build and test
- Python: `.venv/bin/pytest -q -m "not slow" --basetemp=<scratch>/pt -p no:cacheprovider` (slow corpus: `-m slow`, about 20 min).
- UI: `export PATH=/app/vbuild/SLED15-x86_64/nodejs/24.19.0/bin:$PATH; cd ui && npx vitest run && npx tsc --noEmit -p . && npm run build` (writes `src/evoalgo/ui_dist`, tracked).
- Thesis PDF: `export PATH=/app/vbuild/SLED15-x86_64/texlive/2026/bin/x86_64-linux:$PATH; cd thesis-doc && latexmk -pdf main.tex` (`module add texlive/2024` adds no binaries on SLED15).
