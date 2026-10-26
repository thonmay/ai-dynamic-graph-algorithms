# Thesis documentation tracker

## Baseline
- Contract: the approved registration form, `topic-proposal-registration.pdf` (repo root; same text as `docs/topic-proposal.txt`). Three contributions: C1 research UI (launch, monitor, replay), C2 isomorphism-aware verifier (zero false negatives at n <= 5, Yang et al. DFS accepted), C3 cooperative agents with optional dynamic agent generation (correct dynamic BFS within bounded generations).
- Thesis source: `thesis-doc/` (supervisor's enhanced Overleaf template, downloaded from grm.web.elte.hu/supervision; identical to `docs/templates/overleaf/`). The form is embedded as `thesis-doc/approved-topic-registration.pdf`.
- Cover metadata (`thesis-doc/config.tex`) matches the form: Computer Science BSc, Department of Programming Languages and Compilers, supervisor position "Lecturer and MSc in Computer Science".

## Decisions
- Final-exam topics, in order: **8 OOM (first choice), 19 Concurrent programming, 17 Operating systems**. Chosen for exam-preparation load and natural fit (sandbox = OS, verifier pool / pipes / locks = concurrency, UML set = OOM). Rejected: 20/21 Databases (no database in the system, scorer 0 C), 11 OOP (C++-heavy question bank), 9 OOD.
- Exam topics are woven into Design and Implementation, never labelled as such (supervisor rule).
- Supervisor page-count targets: Intro 3-5, User doc 20, Design 10+ with 3-4 strong figures, Implementation 10+, Testing 10+ (every test: steps, expected, observed), Conclusion 2-4; total 60-80; bibliography >= 30 (50 target).
- Old drafts `docs/planning-spec-short.tex` (SRS, FR/NFR IDs) and `docs/design.tex` are source material, not the deliverable; the checkpoint audit `Thonmay_Islam_BSc_SRS_Design_Audit.md` lists what they lacked.

## Evidence sources
- Results: `campaign/analysis.md` (eval1-eval3, verifier self-tests, UI check, bug hunt, sandbox limits); self-test logs `campaign/selftest_{dfs,lbfs}_n5.log`; UI screenshots `campaign/ui_check/`.
- Exam-topic scorer output (supervisor's skill): `/proj/MPS/MPS_DEV_REPO/ethomdt/evoalgo-scratch/examtopic/` (re-run after the chapters are written).
- Supervisor guides (downloaded): study guide, past questions, committee profiles in `/proj/MPS/MPS_DEV_REPO/ethomdt/evoalgo-scratch/guide/`.

## Status
- [x] Template set up, form embedded. Figures: use cases, components, class, state, sequence, processes (all TikZ, figures/).
- [x] First drafts: Ch2 user doc, Ch3 requirements (catalogue in Appendix B), Ch4 design, Ch5 implementation, Ch6 testing. Commit b7ebe04.
- [x] bsc-thesis 30-point draft audit (2026-10-26): 16 awarded, 7 lost, 7 pending; factual fixes applied (crossover/retention invented, test count, relabels, token link, culled files, TC prefixes TC-HAR/TC-SRV, FR summary complete, traceability refs, `--` in texttt, duplicate Rose bib).
- [ ] Length: body ~104 pp -> 75-85 pp. Audit cut list: ADR table to appendix; NFR table 2 columns; use-case narratives to a table; sandbox/concurrency/universe explained once (design in Ch4, code in Ch5, one-line refs elsewhere); Ch2 complex-features section to a table; duplicate screenshots in Ch4; drop "earlier draft/checkpoint audit" mentions.
- [ ] Remaining audit items: hardware requirements (Ch2); event-schema table (Ch4 persistence); ruff/mypy result or coding standard (Ch5); cite >= 30 keys without \nocite; figures legible (class and sequence at full width, split class diagram); UML validity (one class per box); process figure as a UML deployment diagram; copy ui_check PNGs into thesis-doc/figures for Overleaf; commit the chunk RSS measurement; British spelling throughout; object and package diagram for OOM; reader-writer, monitors, semaphore, paging mentions for Concurrency/OS.
- [ ] Ch1 Introduction, Ch7 Conclusion, Appendix A reproducibility, AI-use disclosures + declaration, guidance flag off.
- [ ] Background: DFS self-test with --relabels 2 (campaign/selftest_dfs_n5_relabels2.log) to back the full-universe wording.
