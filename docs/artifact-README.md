# Artifact README (draft) — Dynamic MCS Ordering Maintenance, Lean-verified

Status: draft skeleton; fill in exact commands/DOIs at submission.

## Purpose
Reproduce: (1) the Lean 4 machine-checked correctness proofs for the dynamic
MCS ordering maintenance algorithm; (2) the empirical verifier result
(PASS 7524/7524, work_ratio 0.1817 vs offline recompute).

## Contents
- `ThesisLean/ThesisLean/Formal_gen003c01_eea71821.lean` — the formalization
  (main module; proof base `Formal_gen001c01_3939115c.lean`).
- `lean-toolchain` — pinned Lean version. MUST be pinned; do not upgrade after
  freezing. Record the exact lake version and mathlib manifest.
- `runs/mcs_pressure_e2e/candidates/gen003_c01.py` — the algorithm (Python,
  reference implementation used by the verifier).
- `runs/mcs_pressure_e2e/generation_0003.json` — recorded PASS + work_ratio.
- Verifier harness: `src/evoalgo/verifier.py` (work_ratio =
  candidate_work / offline_work), `problem_definitions.py` (offline_compute +
  DynamicMCS.check_invariant).

## Build
1. Install Lean 4 with the pinned toolchain (elan):
   `curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh`
   then `elan override set <pinned version>` in the project dir.
2. `lake build` in the project root. Expected: clean build, no warnings,
   theorem list as in Appendix A of paper-skeleton.md.
3. Sanity: grep for `sorry|axiom|admit|unsafe` — expected zero (except header
   comment mentions of the word sorry).

## Reproduce the empirical result
Environment: PYTHONPATH=src; Python 3.11+ (bit_count, dataclasses).
Verifier: `python3 -m evoalgo.cli --run runs/mcs_pressure_e2e verify --candidate gen003_c01`
(CLI signature note: verify subcommand is self-test only; per-candidate verify
runs inside the orchestrator `start`/`resume`. For a standalone re-run use the
Verifier API as in the paper's Appendix B.)
Expected: state=PASS, tests=7524/7524, work_ratio=0.1817 (deterministic,
seed 1337).

## Scope of the machine-checked claim (be explicit)
The Lean proof covers:
- Correctness of initOrder / insertUpdate / deleteUpdate: the maintained order
  is a valid deterministic MCS ordering of the updated graph at every step.
- The window characterization (probe soundness directions proved so far;
  bounded-window probe iff still being completed).
The Lean proof does NOT cover:
- Time complexity / amortized analysis (no time credits; no asymptotic claims).
- The bitmask/bucket implementation (representation-abstract).
- The empirical work_ratio number (measured in Python, not proved).

## Zenodo / DOI
Deposit at submission: Lake project + lean-toolchain + README + verifier
sources. License: review target TBD (CC-BY for LIPIcs venues; ACM policy for
CPP). Record the artifact DOI in the paper's artifact appendix.

## Toolchain freeze checklist
- [ ] Record `lean-toolchain` content.
- [ ] Record `lake` version + mathlib toolchain.
- [ ] Capture `lake build` log for the frozen commit.
- [ ] Record Python + numpy versions for the verifier.