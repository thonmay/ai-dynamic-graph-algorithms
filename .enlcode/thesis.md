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
- [x] C10/C12: `scripts/execution_record.sh`; record in `campaign/execution_record/` (now f7ba4d1, 32/32 OK, redacted). Found and fixed one flaky test (e527d08).
- [x] Code cleanup and simplification (2026-11-23, b1bab60..71f89e9, pushed in 4af649c): dead code and two stubs removed, comments trimmed, orchestrator agent-call block merged (event traces identical), clear errors for bad config, corrupt runs and an unusable agent backend (`agent_unavailable`), UI shows agent errors and refused access.
- Supervisor audit 2026-11-25 (`Thonmay_Islam_FFR8A9_BSc_{30_Point,Checkpoint_5}_Audit_2026-11-25.md`, repo root, untracked): CP5 Insufficient, 18 points confirmed, 4 lost (C1.1 topic 17, C2.3 tiny figures, C5.2/C5.4 agent boundary + BrokenProcessPool), 8 open (C6.2/C6.3 missing campaign evidence, C7.1-C7.6 demo).
- [x] Agent-doable audit fixes (2026-11-26): code f7ba4d1 (opencode + Lean prover jailed, EVOALGO_SIGNAL reaper, memory-capped workers + serial fallback, /mnt and `..` fixes, prefix-aware host-data test); thesis 7ef4fbd (FR-VER-09 scope: workspace harness is the stated exception, user choice; App. F full-width UI figures; App. G topic-17 subtopics; 2<=n<=5; pins wording; declaration 195/15). Body pp. 6-85 = 79 pp.
- [x] Review zip `thonmay-review.zip` (ac79322): PDF, LaTeX zip, code zip with redacted `campaign/` + cited `runs/` (user decision 2026-11-25 reverses the earlier exclusion), `SUBMISSION_MANIFEST.md` with hashes. Redaction script kept at `evoalgo-scratch/build_evidence.py`.
- [ ] Still open from the audit: signed declaration, accepted exam registration form, supervisor demo D1-D6 (C7), Turnitin, final `THONMAY_FFR8A9_THESIS.zip`.
- [x] Code-verified corrections (engine threads, control.jsonl writers, process-group vs --kill-child, class/sequence diagrams), object + package diagrams, OS/concurrency subtopics.
- [x] Third audit (bsc-thesis, CP5 skill, 2026-10-31) on 6fe503f; its agent-doable fixes applied in 94343c5 (campaign revisions in 6.1/App. A, ADR-01, object diagram attributes, App. A dev extra and listings, AI rows identical in 5.2 and declaration). Remaining per that audit: student-only items below, plus the archive and the site-string placeholders (deferred by user).
- Length: supervisor announced (2026-11) the faculty 80-page maximum applies (excluding cover, TOC, list of figures, appendix and other supplementary sections). Chapters 1-7 are 78 pp (pp. 6-84 less the divider): compliant; 84 pp if the bibliography (85-90) is counted, which is unresolved. Open: confirm with the supervisor that topic 19 replaces the topic 11 he recalled.
- Ch2 is exactly 20 pp (minimum): any rewrite must not shorten it.
- [ ] USER: print, sign and date `thesis-doc/ai-declaration.docx` by hand, scan to PDF, put it in the submission zip (slot in the manifest).
- [ ] USER: rewrite in your own words (supervisor rule: research-heavy text must be the student's own). AI-drafted passages to rewrite: Ch1 Sec 1.1 Motivation and problem (all four paragraphs) and the Sec 1.3 contribution bullets; Ch6 Sec 6.8 interpretation paragraphs (the prose after Tables 6.3, 6.4, 6.5 and Sec 6.8.5 Threats to validity); Ch7 all sections (7.1-7.5). Keep every number and citation; after rewriting, update the "Thesis text drafting" row of Table 5.2 and the declaration to say which parts were rewritten by you.
- [x] Final-exam registration with topics 8/19/17 submitted 2026-10-31 (`docs/final-exam-topics.pdf`, contains personal data: keep out of the submission zip).
- Turnitin (supervisor, 2026-11): AI-writing detection is now in the report; students may self-check in the supervisor's Turnitin class, 3 submissions per 24 h; supervisor grades on content, the committee may weigh the AI score differently. Check with him that the class does not store submissions in the repository (else the Neptun upload may match the draft).
- [ ] USER: self-check in Turnitin, rewrite flagged and research passages in own words, re-check; upload one file `THONMAY_FFR8A9_THESIS.zip` by 1 Dec 2026.
- [ ] USER: student-led debugging session with the supervisor (CP4-C10; he will run the program himself).
- Repo access: GregoryMorse is a collaborator with write permission on the private repo.
