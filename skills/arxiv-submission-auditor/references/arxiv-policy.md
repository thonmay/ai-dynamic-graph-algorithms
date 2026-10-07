# Current arXiv policy sources and hard checks

Open the official pages below during each audit and record the access date. This is a verified 2026-08-30 baseline, not a substitute for live policy.

## Official sources

- Submission overview and filename/source rules: https://info.arxiv.org/help/submit/index.html
- TeX submission and bibliography rules: https://info.arxiv.org/help/submit_tex.html
- Metadata fields and exact syntax: https://info.arxiv.org/help/prep.html
- Format and public-repository requirements: https://info.arxiv.org/help/policies/format_requirements.html
- Moderation and generative-AI policy: https://info.arxiv.org/help/moderation/index.html
- Current category taxonomy: https://arxiv.org/category_taxonomy
- Official MSC2020 search: https://mathscinet.ams.org/msc/msc2020.html
- ACM 1998 classification index: https://www.acm.org/publications/computing-classification-system/1998
- Current ACM Computing Classification System: https://dl.acm.org/ccs
- Citation formatting for arXiv works: https://info.arxiv.org/help/faq/references.html
- Common TeX failures: https://info.arxiv.org/help/faq/mistakes.html
- Current arXiv TeX Live environment: https://info.arxiv.org/help/faq/texlive.html
- Licenses: https://info.arxiv.org/help/license/index.html
- Cross-listing: https://info.arxiv.org/help/cross.html
- Ancillary files: https://info.arxiv.org/help/ancillary_files.html

## Official metadata baseline

- arXiv metadata accepts ASCII input. Convert Unicode to supported TeX/MathJax forms.
- Title, Authors, and Abstract are required. Author identities, consent, ordering, and current affiliations must be accurate.
- The Abstract value omits the heading, expands opaque macros, avoids presentation-only TeX, and is no more than 1,920 characters.
- Comments is optional but recommended. It should state the page count and may list figures, tables, algorithms, submission/publication status, and public related-material URLs. Separate a URL from following punctuation with whitespace.
- Category supplies one primary subject and optional cross-lists. In the self-contained TeX block, render this as the public-facing `Subjects:` line with exact official labels and codes, primary first.
- For a math submission, use arXiv's syntax: `MSC classes: 68Q25 (Primary) 68N20, 05C85 (Secondary)`. Put `(Primary)` and `(Secondary)` exactly as shown and comma-separate multiple codes within a group.
- For a cs submission, use legacy-style codes accepted by arXiv and semicolon-space separators: `ACM classes: F.2.2; D.3.4; F.3.2`. Verify every code and label; do not paste a CCS 2012 prose path into this field.
- In the TeX record, `MSC classes` maps to arXiv's `MSC-class` web field and `ACM classes` maps to `ACM-class`; paste only the value, not the TeX record label.
- Report number is only an institutionally assigned report number. Journal reference is only complete publication information. DOI is only a DOI for another version of the article, not the arXiv-assigned DOI.
- Links to code or datasets must resolve to a publicly available repository. This skill applies the same hard standard to certificates, proof-assistant sources, supplements, and other externally claimed artifacts.
- Significant text-to-text generative-AI use must be reported in the work. AI tools are not authors; human authors remain responsible for all contents.
- Submit TeX source when the PDF was made from TeX. Include every local dependency and figure; follow current `.bib`/`.bbl`, index, glossary, processor, filename, and TeX Live rules.
- arXiv currently processes required `.bib` files automatically. If a `.bbl` is supplied, arXiv uses it and requires its basename to match the main `.tex`; BibLaTeX `.bbl` backend/format compatibility must match the selected arXiv environment.
- arXiv currently offers TeX Live 2023 and 2025, with 2025 as the default. Verify this live and record the selected tree.
- arXiv permits supporting code/data/images in a root `anc/` directory for TeX submissions; this permission is distinct from the stricter default of keeping reproducibility artifacts in a public pinned repository outside the upload.
- The manuscript must be machine-readable, single-spaced, 10–14 point, and have at least 1-inch margins. Remove line numbers, highlights, margin/referee notes, obstructive watermarks, advertisements, and incompatible copyright language.

## Stricter audit conventions

The following are deliberately stricter than arXiv's minimum wording:

- Make the main TeX file self-contained with a raw `\iffalse` metadata region.
- Require a public GitHub repository, an exact paper URL, and a pinned tag/release/commit for every external artifact on which the paper relies.
- Require provider, exact model, thinking/reasoning mode, and role for significant AI use.
- Prefer an audited `.bib` plus a freshly regenerated matching `.bbl`, include both, and verify full-source and extracted-archive build paths.
- Build the upload ZIP from an explicit compilation allowlist and exclude code, certificates, proof-assistant sources, logs, datasets, audit/administrative files, and old archives unless Gregory explicitly opts into arXiv ancillary files.
- Recompute metadata, manifests, checksums, blockers, and readiness after the final archive change.
- Treat the absence of evidence as unresolved, never as a pass.

## Gregory-specific preferences

- Keep the main TeX file as the canonical self-contained metadata record and derive any metadata text file from it.
- Keep publication administration out of the public code repository.
- Prefer a reusable general repository with versioned result directories and namespaced paper-release tags.
- Use the model-specific AI wording and author/affiliation defaults only after Gregory confirms the facts for the exact submission.

When a live official source conflicts with this baseline, follow the live source, document the change, and propose updating the skill.
