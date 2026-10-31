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

## Status (2026-10-31, after the supervisor's checkpoint 4 and 5 audits of 2026-10-30)
- Audits: `Thonmay_Islam_BSc_Checkpoint_4_Implementation_Audit_2026-10-30.md`, `..._Checkpoint_5_Final_Thesis_Audit_2026-10-30.md` (repo root, untracked). Both "Insufficient" on evidence/compliance gates, not on content.
- Session: January 2027 (Neptun upload deadline 1 Dec 2026); cover year 2027. Topics to register, in order: 8 OOM, 19 Concurrent, 17 OS (supervisor recalled 11; student chose 8/19/17). Private coverage map: `.enlcode/exam-topic-coverage.md`.
- [x] C14 length: Ch1-7 = 78 substantive pp + divider (printed 6-84); detailed tables moved to Appendix D; faculty max 80.
- [x] C14 claims: zero-false-negative bounded to the seeded corpus/universe/histories everywhere; eval3 raw 7/9 + 2 regrades explicit.
- [x] C13: AI header comment in every source file (from the recorded edit history; AST/bundle identical, commit e39d4ab); 5.3 table and declaration page refs updated. Supervisor explicitly permitted AI use.
- [x] C10/C12: `scripts/execution_record.sh`; record in `campaign/execution_record/` (e527d08, 31/31 OK, redacted). Found and fixed one flaky test (e527d08).
- [x] Code-verified corrections (engine threads, control.jsonl writers, process-group vs --kill-child, class/sequence diagrams), object + package diagrams, OS/concurrency subtopics.
- [x] Third audit (bsc-thesis, CP5 skill, 2026-10-31) on 6fe503f; its agent-doable fixes applied in 94343c5 (campaign revisions in 6.1/App. A, ADR-01, object diagram attributes, App. A dev extra and listings, AI rows identical in 5.2 and declaration). Remaining per that audit: student-only items below, plus the archive and the site-string placeholders (deferred by user).
- Open question for the supervisor: whether the bibliography (pp. 85-90) counts toward the 80-page limit (if yes: 84 pp); whether topic 19 replacing his recalled 11 is fine; whether the 6 N subtopics of topic 17 are acceptable.
- Ch2 is exactly 20 pp (minimum): any rewrite must not shorten it.
- [ ] USER: print, sign and date `thesis-doc/ai-declaration.docx` by hand, scan to PDF, put it in the submission zip (slot in the manifest).
- [ ] USER: rewrite in your own words (supervisor rule: research-heavy text must be the student's own). AI-drafted passages to rewrite: Ch1 Sec 1.1 Motivation and problem (all four paragraphs) and the Sec 1.3 contribution bullets; Ch6 Sec 6.8 interpretation paragraphs (the prose after Tables 6.3, 6.4, 6.5 and Sec 6.8.5 Threats to validity); Ch7 all sections (7.1-7.5). Keep every number and citation; after rewriting, update the "Thesis text drafting" row of Table 5.2 and the declaration to say which parts were rewritten by you.
- [ ] USER: register the three topics in Neptun; book the supervisor's single Turnitin check (about one week before upload); upload one file `THONMAY_FFR8A9_THESIS.zip` by 1 Dec 2026.
- [ ] USER: student-led debugging session with the supervisor (CP4-C10; he will run the program himself).
- Repo access: GregoryMorse is a collaborator with write permission on the private repo.
