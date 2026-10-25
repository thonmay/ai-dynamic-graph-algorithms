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
- [x] Template set up, form embedded, builds (26 pp of placeholders).
- [ ] Figures (vector PDF): use case, component, class, sequence (one generation), state (CandidateState), process/deployment.
- [ ] Ch1 Introduction, Ch2 User doc, Ch3 Requirements, Ch4 Design, Ch5 Implementation, Ch6 Testing, Ch7 Conclusion, appendices.
- [ ] Bibliography >= 30; AI-use disclosures at point of use; AI declaration (separate file).
- [ ] bsc-thesis audits: requirements and architecture checkpoints, then the 30-point audit; re-run the exam-topic scorer.
