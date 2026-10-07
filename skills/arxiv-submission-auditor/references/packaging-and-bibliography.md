# Packaging and bibliography protocol

## Contents

1. Requirement provenance
2. Bibliography policy and strict default
3. Two independent build paths
4. Explicit upload allowlist
5. Full handoff versus arXiv upload
6. Final PDF and checksum gates
7. Checker invocations

## 1. Requirement provenance

Label every checklist row and finding with exactly one basis:

- `ARXIV POLICY`: an official current arXiv requirement, prohibition, or documented processor behavior;
- `STRICT PUBLICATION DEFAULT`: a deliberately stronger reliability, scholarly-quality, or reproducibility gate;
- `GREGORY PREFERENCE`: a Gregory-specific convention that is neither an arXiv rule nor a universal publication requirement.

When multiple bases apply, list the strongest direct source first and explain the stricter layer separately. Never write `arXiv requires` for a strict default or preference.

## 2. Bibliography policy and strict default

`ARXIV POLICY`: arXiv currently processes required `.bib` files automatically. A submitter may instead provide a pre-generated `.bbl`; when a `.bbl` is present, arXiv uses it, and its basename must match the main `.tex`. Nonstandard classic-BibTeX processors require a preserved `.bbl`. A BibLaTeX `.bbl` must match the backend and a supported BibLaTeX/Biber format.

`STRICT PUBLICATION DEFAULT`:

- maintain a professional field-audited `.bib` and ship both that `.bib` and a freshly generated matching main-stem `.bbl`;
- regenerate the `.bbl` after every citation or bibliography change;
- prefer `.bib` over manually maintained `thebibliography` unless a documented technical reason justifies the latter;
- compare cited keys, `.bib` keys, and `.bbl` keys independently—never take their union and call it valid;
- require zero missing/duplicate/uncited keys and zero BibTeX/Biber warnings;
- verify every BibTeX field: exact author order/spelling/diacritics, capitalization braces, title, venue, year, volume/issue, pages/article number, DOI, arXiv ID, version relationship, translations, corrections, and retractions;
- visually inspect the final bibliography for ordering, legibility, clipping, capitalization, names, identifiers, and page reflow.

Record document package/style and backend separately. For classic BibTeX/natbib, record BibTeX/BibTeX8/upBibTeX and the `.bst`. For BibLaTeX, record backend, local BibLaTeX/Biber versions, `.bbl` format, chosen arXiv TeX Live tree, and compatibility. Do not assume a locally generated BibLaTeX `.bbl` is portable.

## 3. Two independent build paths

Run both after bibliography/content edits and again after final packaging:

1. **Full-source build:** clean staging copy; LaTeX once; BibTeX/Biber once; LaTeX at least twice. Preserve logs and regenerated `.bbl` outside the upload.
2. **Shipping build:** extract the exact final ZIP into a fresh directory; run LaTeX without invoking BibTeX/Biber, using the shipped `.bbl` and processed index/glossary files.

Hard gates:

- regenerated `.bbl` is byte-identical to the one in the final ZIP;
- both PDFs have equal page count and extracted text;
- citation/reference lists and metadata agree;
- packaging-only changes produce rendered-pixel equality where tools permit;
- any PDF metadata difference is explained;
- zero errors, undefined citations/references, missing files/glyphs, BibTeX/Biber warnings, or overfull boxes;
- every underfull box is reviewed and classified cosmetic or substantive.

## 4. Explicit upload allowlist

Build the final arXiv ZIP from enumerated compilation dependencies, never by zipping a working directory. The allowlist normally includes only:

- main and recursively required `.tex` files;
- required `.bib` and matching `.bbl`;
- required figures in already supported formats;
- required local `.sty`, `.cls`, `.bst`, macro, font, and configuration files whose licenses permit redistribution;
- required processed `.ind`, `.gls`, or `.nls` files;
- an intentional `00README` only when processor control actually requires it.

Reject build debris (`.aux`, `.log`, `.blg`, `.out`, `.fls`, `.fdb_latexmk`, `.bcf`, `.run.xml`, and similar), the locally generated main PDF, audits, metadata sheets, blocker ledgers, checklists, checksum files, backup files, hidden files, credentials, old archives, repository copies, and unrelated files.

`STRICT PUBLICATION DEFAULT`: code, certificates, solver logs, datasets, notebooks, Lean/Coq/Isabelle sources, reproduction scripts, and release packages remain in the public pinned repository and are excluded from the arXiv ZIP. arXiv permits an `anc/` directory, but ancillary inclusion is explicit author opt-in only; permission is not a reason to copy a repository into the upload.

Inspect and list every final ZIP member, reject unsafe/absolute/parent-traversal paths, test archive integrity, extract it, and audit the extraction rather than trusting the archive command.

## 5. Full handoff versus arXiv upload

The full author-side handoff may contain the final upload ZIP, approved PDF, source, `.bib`/`.bbl`, audit, metadata, blocker ledger, checklist, repository release material, and checksums. The arXiv ZIP contains only the compilation closure.

Permit exactly one current upload ZIP in the handoff. Move earlier archives to internal backup storage. Keep publication administration out of the public software repository, including audits, metadata paste sheets, blocker ledgers, submission checklists, and GitHub About copy.

## 6. Final PDF and checksum gates

Derive page/figure/table/algorithm counts from the PDF built from the extracted final ZIP. Then regenerate the TeX metadata block, mechanically compare any `ARXIV_METADATA.txt`, rebuild the ZIP if needed, and repeat until stable.

Inspect every PDF page. Verify embedded fonts, selectable text, bibliography rendering, figures, links, margins, and absence of JavaScript, forms, annotations, suspicious objects, line numbers, highlights, watermarks, and referee material.

After the last modification, generate recursive SHA-256 checksums for the completed handoff, verify every entry, test every nested ZIP, reopen the blocker ledger, and regenerate the archive manifest and readiness report. An earlier clean audit never survives an untested late packaging change.

Search all author-side audits, metadata sheets, checklists, and handoff notes for stale archive names, old file/member counts, old page/object counts, phrases such as `two-file upload`, and inherited `no blockers remain` assertions. Recompute them from the final artifacts rather than editing only the most visible report.

## 7. Checker invocations

After the full-source build, audit staging and compare the regenerated `.bbl`:

```text
python3 <skill-dir>/scripts/audit_tex.py <staging-dir> --main <main.tex> --regenerated-bbl <clean-build.bbl> --metadata-file <ARXIV_METADATA.txt> --json <staging-report.json>
```

Create a one-path-per-line allowlist outside the ZIP. Then audit and LaTeX-only build the exact final archive:

```text
python3 <skill-dir>/scripts/audit_tex.py <final-upload.zip> --main <main.tex> --allowlist <upload-allowlist.txt> --regenerated-bbl <clean-build.bbl> --shipping-build --shipping-pdf <archive-built.pdf> --json <archive-report.json>
```

Add `--allow-ancillary` only after explicit author opt-in. Add `--checksums <SHA256SUMS>` to verify a completed handoff manifest. The shipping build deliberately invokes no BibTeX/Biber; it performs three no-shell-escape LaTeX runs, checks the final log, page count, selectable text, suspicious PDF features, and font embedding. Visual inspection and full-source/shipping-PDF regression comparison remain mandatory human/agent gates.
