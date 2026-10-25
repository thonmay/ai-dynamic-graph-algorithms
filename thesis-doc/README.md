# ELTE IK BSc thesis template

This project modernizes Máté Cserép and Bálint Bognár's MIT-licensed
`elteikthesis` template for a rigorous ELTE IK BSc thesis workflow. It combines
the current ELTE IK rules with strongly recommended thesis-authoring practices. The
official current university pages always take precedence if requirements change.

## Overleaf quick start

1. Use the distributor's **Open in Overleaf** button when available. For a manual
   import, choose **New project** > **Existing project (.zip)** in Overleaf and
   select this ZIP.
2. Keep `main.tex` as the main document and select pdfLaTeX. The archive is
   intentionally flat: `main.tex` is at the ZIP root, not inside an enclosing
   project folder.
3. Edit metadata in `config.tex` and replace every angle-bracket placeholder.
4. Export the approved topic form as `approved-topic-registration.pdf` and upload it
   beside `main.tex`.
5. Replace the prompts in `chapters/`; add figures to `images/` as vector PDF where
   possible.
6. Add only sources actually used to `references.bib`, then cite them in the text.
7. Before submission, set `\showtemplateguidancefalse` in `config.tex`, rebuild from
   scratch, inspect every page, and complete the checklist in Appendix B.

## Structure and evidence

- Introduction: roughly 3–5 pages; goal, scope, success, and exactly three prominent
  contributions.
- User Documentation: around 20 substantive pages is strongly recommended for a
  strong software thesis when the project scope supports it;
  clean installation, workflows, three complex features, screenshots, troubleshooting.
- Requirements Specification: detailed functional/non-functional requirements with
  stable IDs, measurable acceptance criteria, and end-to-end traceability.
- Solution Design: roughly 10+ pages and 3–4 strong, discussed figures.
- Implementation: roughly 10+ pages, linked to design and repository evidence.
- Testing and Evaluation: roughly 10+ pages with expected *and observed* results.
- Conclusion: roughly 2–4 pages, assessing commitments and contribution evidence.
- Bibliography: at least 30 relevant sources is strongly recommended; approximately
  50 well-used sources is an excellent target when the topic supports it. Relevance
  and correct use beat padding.

Page targets are strong recommendations, not permission to add filler. For non-UI or
research-oriented projects, replace UI-specific evidence with the closest rigorous
equivalent agreed with the supervisor.

## Local build

Run `make`. The Makefile builds `main.tex` by default and accepts a different root with
`make MAIN=other-root`. It uses `latexmk` and does not enable shell escape. Run
`make clean` for generated auxiliary files.

The bibliography backend is BibTeX for broad local and Overleaf compatibility.

## Figure and citation discipline

- Export diagrams as vector PDF when possible; use PNG only for raster screenshots.
- Design figures should expose architecture, data/domain structure, interactions, or
  UI/API decisions. Cite each figure in the prose and explain what it demonstrates.
- Keep labels readable at 100%; never use screenshots of source code or diagrams.
- Cite standards, papers, books, datasets, tools, libraries, APIs, and platforms that
  materially support a claim or implementation decision.
- Every bibliography item should be used; every non-obvious borrowed claim should be
  supported near the claim.

## Source and policy references

- Current ELTE IK thesis rules: <https://www.inf.elte.hu/en/guidelines-thesis-final-examination>
- Current ELTE IK AI policy: <https://www.inf.elte.hu/en/ai-usage-policy>
- Upstream template: <https://github.com/mcserep/elteikthesis>

## License

The LaTeX class remains under its upstream MIT license. See `LICENSE`. Newly authored
guidance text may be adapted for thesis preparation.
