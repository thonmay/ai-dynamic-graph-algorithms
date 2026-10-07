---
name: arxiv-submission-auditor
description: Rigorously audit a LaTeX manuscript and final arXiv upload ZIP; verify every citation and cited claim, field-audited `.bib`/matching `.bbl`, novelty/frontier claims, public GitHub artifacts and formal certificates, exact arXiv/MSC/ACM classifications, authorship, rights, and model-specific AI disclosure; embed ASCII-safe metadata in a self-contained TeX `\iffalse` block; exclude code and administration from the upload; and produce a verified archive and readiness report. Use for arXiv preflight, metadata, bibliography, categories, artifact checks, packaging, or final submission audits; do not substitute for scientific peer review or submit without author confirmation.
---

# arXiv Submission Auditor

Produce an evidence-backed audit and a clean upload bundle. Make the main TeX file the canonical, self-contained submission record. Never label a manuscript `SUBMISSION-READY` while a citation, novelty claim, external artifact, disclosure fact, source dependency, metadata value, archive fact, right, or author confirmation remains unresolved.

Label every rule and finding as `ARXIV POLICY`, `STRICT PUBLICATION DEFAULT`, or `GREGORY PREFERENCE`. Never attribute a stricter local convention to arXiv. Audit the extracted final upload archive itself, not merely the working tree that produced it.

Keep edits narrow. Do not silently change results, proofs, experiments, author order, affiliations, AI-use facts, publication status, categories, or license choices. Record every substantive edit and obtain author confirmation.

## Load the audit rules

Read [references/arxiv-policy.md](references/arxiv-policy.md) before every audit and open its official links live. Record the access date because submission rules, TeX environments, and taxonomies change.

Read [references/audit-protocol.md](references/audit-protocol.md) for citation, classification, metadata, source, PDF, and deliverable requirements. Read [references/packaging-and-bibliography.md](references/packaging-and-bibliography.md) for every source audit, archive build, or bibliography. Read [references/artifacts-and-ai.md](references/artifacts-and-ai.md) whenever the paper mentions or relies on software, data, certificates, formal proofs, supplements, or generative AI; inventory both topics even when the paper appears silent. Read [references/novelty-and-frontier.md](references/novelty-and-frontier.md) whenever the paper claims a first result, resolution, open problem, exact frontier, or best-known bound.

## Audit workflow

1. Inventory the complete work.
   - Locate the main TeX file, recursive inputs, bibliography, `.bbl`/index/glossary outputs, figures, custom classes/styles/fonts, ancillary files, linked repositories, proof assistants, certificate generators/checkers, datasets, logs, notebooks, and supplements.
   - Work in a staging copy and preserve the author's source and unrelated files.
   - Resolve this skill's directory and run `python3 <skill-dir>/scripts/audit_tex.py <staged-source-or-final.zip> --main <main.tex> --json <report.json>`. Run it again on the final ZIP. Treat static findings as leads, not proof of citation validity, repository availability, bibliography freshness, or successful arXiv compilation.

2. Establish manuscript and submission facts.
   - Read the title, author block, affiliations, abstract, introduction, contributions, conclusions, acknowledgments, artifact statements, and bibliography.
   - Confirm author order/consent, current affiliation, submitter status, publication/report/DOI status, license choice, artifact scope, and the exact AI models, modes, and roles actually used.
   - For Gregory Morse, propose `Gregory Morse (E\"otv\"os Lor\'and University)` as ASCII-safe author metadata, but reconfirm that ELTE remains current at submission time.

3. Verify every citation and occurrence.
   - Resolve each work through the primary paper, publisher/DOI record, arXiv record, standards body, or official book/catalog record.
   - Verify identity, full metadata, version/publication relationship, corrections/retractions, and support for the nearby claim. Record theorem/section/page/equation evidence when available.
   - Treat inaccessible, ambiguous, mismatched, or unsupported citations as blockers. Never invent or silently substitute a reference.
   - Prefer a field-audited `.bib` plus a freshly generated matching main-stem `.bbl`. This is a strict reliability default, not an arXiv requirement; arXiv currently accepts `.bib` processing or a supplied `.bbl`.

4. Determine submission classifications.
   - Compare the central contribution with the live arXiv taxonomy and several recent genuinely similar papers.
   - Recommend exactly one primary subject and only justified cross-lists. Format `Subjects`, `MSC classes`, and `ACM classes` exactly as specified in `audit-protocol.md`; use legacy-style ACM codes accepted by arXiv and separate them with `; `.

5. Close artifact and disclosure blockers.
   - For every external code, certificate, Lean/Coq/Isabelle proof, dataset, supplement, or reproducibility claim, require the paper to give the exact public GitHub location and pinned version. Open it without authentication, verify the referenced content exists and matches the paper, and ensure the same URL is present in `Comments` when appropriate.
   - Require a visible, truthful manuscript disclosure for significant AI use. Record exact provider, model, thinking/reasoning mode, and role; generic phrases such as `AI tools assisted` do not pass. The hidden metadata block alone is not disclosure.
   - Keep code, certificates, Lean sources, logs, datasets, and reproduction scripts in the public pinned repository, not the arXiv upload. Treat arXiv ancillary files as explicit author opt-in only.

6. Build and inspect.
   - Record engine, bibliography package/style/backend, local tool versions, and selected arXiv TeX Live tree. Compile the full source through LaTeX + BibTeX/Biber + LaTeX twice, then compile the extracted final archive without invoking BibTeX/Biber. Require the regenerated and shipped `.bbl` files to be byte-identical.
   - Resolve every warning, missing dependency, case mismatch, unresolved citation/reference, overfull box, and source/PDF divergence. Classify every underfull box.
   - Inspect the rendered PDF visually. Verify title, authors, affiliations, abstract, acknowledgments, page/object counts, artifact URLs, references, appendices, and rights text.

7. Embed canonical submission metadata.
   - Insert or replace exactly one raw `\iffalse` / `\fi` region marked `ARXIV-METADATA-BEGIN` and `ARXIV-METADATA-END`; do not prefix its contents with `%`.
   - Use the exact field layout in `audit-protocol.md`. Keep every paste value ASCII-safe and compile-test the region.
   - If the abstract environment is already directly pasteable into arXiv—ASCII-safe, under the live limit, free of opaque/local macros and unsupported formatting—record `Abstract source: copy abstract environment verbatim`. Otherwise include the fully expanded paste-ready `Abstract:` value inside the false region. Never maintain two silently divergent abstracts.
   - Treat the TeX region as canonical. Generate `ARXIV_METADATA.txt` only as an optional convenience derived from it, never as the sole metadata record.

8. Deliver the audit.
   - Build the arXiv archive from an explicit compilation allowlist; never zip a directory blindly. Create `ARXIV_AUDIT.md` outside it. Exclude code/artifacts, audit files, local build debris, credentials, older archives, and unrelated files.
   - Keep the full author handoff bundle distinct from the arXiv upload ZIP. Permit exactly one current upload ZIP in the handoff; generate and verify recursive SHA-256 checksums only after the final change.
   - Extract and audit the final ZIP, rebuild its PDF, recompute metadata from that PDF, resynchronize the TeX block and optional `ARXIV_METADATA.txt`, reopen every blocker, and regenerate the manifest, checksums, and readiness statement.
   - End with only the remaining web actions: upload, select confirmed categories/license, paste metadata, inspect arXiv's generated PDF, and approve submission.

## Final gate

- `SUBMISSION-READY`: zero blockers; citations, novelty, and claims verified; every mentioned external artifact is public, pinned, linked, and checked; the extracted final ZIP passes both build paths; its manifest and checksums are final; TeX metadata is canonical and synchronized; model-specific AI disclosure and rights are settled; author confirmations are recorded.
- `CONDITIONALLY READY`: no known contradiction, but explicit author confirmation or an external check remains.
- `NOT READY`: any technical, metadata, citation, artifact, disclosure, rights, or scientific-support blocker remains.

Never promise moderator acceptance or category approval.
