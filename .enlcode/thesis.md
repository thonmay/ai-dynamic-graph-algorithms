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

## Status (2026-10-26, commit 8b6b656)
- [x] All chapters written (Ch1-Ch7, Appendices A reproducibility, B FR catalogue + use-case narratives, C design decision record, D checklist); 156 pp PDF, body pp 6-100 (95 pp), 55 bib entries all cited, 0 undefined refs, no overfull box > 3.5 pt.
- [x] Two bsc-thesis 30-point audits applied; latest provisional 21-27/30 (21 awarded, 3 lost, 6 pending demo). Exam topics 8/19/17 all "Strong now" (7/2/0, 13/1/0, 14/3/12).
- [x] Committed evidence: self-test logs BFS/DFS/LBFS (+ DFS relabels 2), DFS certificate cross-check (274,942), Yang random-update check (1.44 M), chunk memory (618 MB DFS).
- [x] AI disclosure (commit 42c5667): Section 5.3 overview table, point-of-use footnotes on generated figures, filled ELTE declaration `thesis-doc/ai-declaration.docx` (official template; models only, no harness/provider names, per user). Supervisor explicitly permitted AI use; logs available on request.
- [x] Template guidance off (`\showtemplateguidancefalse`); 157 pp, 0 undefined refs.
- [ ] User: print, sign and date the declaration; add it to the submission zip as a separate file.
- [ ] Third bsc-thesis audit on the final build.
- Length: user chose to keep 95 pp body.
- [ ] Demo (C7.x) with the supervisor on revision 7895107.
