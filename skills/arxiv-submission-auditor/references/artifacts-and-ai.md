# External artifacts and AI disclosure

## Contents

1. Artifact discovery
2. Public GitHub hard gate
3. Artifact verification ledger
4. AI-use inventory
5. Disclosure placement and wording

## 1. Artifact discovery

Search the full manuscript, appendices, footnotes, captions, bibliography notes, source comments, and supplied archives for claims involving:

- code, implementations, scripts, libraries, executables, notebooks, or containers;
- generated certificates, checker programs, SAT/SMT/ILP instances, solver logs, or computational enumerations;
- Lean, Coq, Isabelle, Agda, HOL, or other formalizations;
- datasets, benchmarks, raw results, generated tables/figures, or reproduction packages;
- supplementary/ancillary files, companion websites, repositories, or material promised for later release.

Create one inventory row per mention with the exact paper location, claimed artifact, whether the result depends on it, intended public location, and verification state. A phrase such as `available in the artifact`, `verified computationally`, or `see the accompanying code` without an exact accessible location is a blocker.

## 2. Public GitHub hard gate

For every externally mentioned or relied-upon artifact, require all of the following before `SUBMISSION-READY`:

- a public GitHub repository accessible without authentication;
- the exact repository URL in the visible paper, not only in a hidden metadata block;
- a concise repository URL in arXiv `Comments` when the artifact is material to the work;
- a pinned release/tag and commit hash corresponding to the submitted paper;
- every promised certificate, proof source, checker, dataset, log, and generation script present at the documented path;
- a README mapping paper claims, theorems, tables, algorithms, and appendices to exact files and reproduction/check commands;
- dependency/toolchain versions and a license; no credentials, private data, or machine-local paths;
- a successful clean verification run where feasible.

Classify each artifact as `logically required`, `supporting`, or `regression-only`. The visible manuscript should normally contain one concise reproducibility paragraph with the exact public repository URL, paper release/tag, and this role distinction. Put the file-by-file inventory, commands, expected outputs, toolchain versions, and checksums in the repository README rather than expanding the paper into an operational manual.

For Lean or another proof assistant, additionally require the project manifest/toolchain lock, exact compiler/prover version, imported dependencies, build command, and a clean build from the pinned revision. For large/generated artifacts, require checksums or a release asset manifest. Recommend an immutable archival DOI in addition to GitHub, but do not treat a mutable branch alone as pinned evidence.

If the repository is absent, private, empty, incomplete, unpinned, unreachable, inconsistent with the manuscript, or says that materials will arrive later, mark a blocker. Do not create or publish a repository unless the user explicitly authorizes that external action.

Keep artifacts out of the arXiv upload under the strict default. arXiv ancillary files are an explicit author opt-in, not an automatic consequence of their being permitted. Keep manuscript/audit administration out of the public repository. Prefer a reusable repository name, versioned result directories such as `n4/`, `n5/`, and `general/`, and namespaced release tags such as `n4-arxiv-v1` when that structure fits the project.

Audit licenses separately: arXiv manuscript license, repository software license, data license, and all third-party dependency/asset licenses are different decisions.

## 3. Artifact verification ledger

Record for each artifact:

| Field | Required value |
| --- | --- |
| Paper mentions | Every file/line or page/section occurrence |
| Role | Supporting, reproducibility-only, or logically required |
| Public URL | Exact GitHub repository and relevant subpath/release URL |
| Pin | Release/tag and full commit hash |
| Contents | Promised files present and mapped to paper claims |
| Verification | Commands run, environment/version, result, logs/checksums |
| Paper linkage | Exact URL appears visibly in paper and, when material, Comments |
| Result | `VERIFIED` or `BLOCKER` with reason |

## 4. AI-use inventory

Do not accept `AI tools were used`, `LLM assistance`, or a vendor name alone. Obtain and verify:

- provider and exact model/product name;
- exact thinking/reasoning mode or comparable runtime setting;
- role in research, proof exploration/development/checking, literature search, citation generation/verification, code, experiments, figures/data, manuscript drafting/revision, and referee critique;
- whether outputs entered the paper or artifacts and what the human author actually checked;
- dates/build identifiers when relevant and known;
- any stricter target-venue or institutional requirement.

The metadata region must record the visible section and exact disclosure text. The disclosure itself must appear in the rendered manuscript. If AI materially formed part of the research method, also describe it in the relevant Methods/Computational methodology/Artifact section rather than hiding it only in Acknowledgments.

## 5. Disclosure placement and wording

Use a dedicated unnumbered `AI assistance disclosure` section or Acknowledgments for significant research and drafting use; use a Methods/Artifact section as well when AI is part of the reported method. Never list an AI system as an author or imply it accepts responsibility.

Personal default for Gregory Morse, only after he confirms every fact and the final responsibility clause:

```text
OpenAI GPT-5.6 Sol in extra-high thinking mode was used for research and manuscript drafting. Anthropic Opus 5 in high thinking mode was used as a referee. The author reviewed the resulting mathematical claims, proofs, computations, citations, and manuscript text and assumes full responsibility for the final work.
```

Expand the role sentence if either model also performed proof development/checking, code generation, experiments, literature search, or citation generation/verification. Do not claim review or independent verification that did not occur. Treat a generic disclosure, an incorrect model/mode, a role omission, a hidden-only disclosure, or an unconfirmed responsibility statement as a blocker.
