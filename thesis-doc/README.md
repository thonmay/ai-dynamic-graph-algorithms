# Thesis source

LaTeX source of the BSc thesis "AI-Assisted Discovery of Dynamic Graph
Algorithms via Evolutionary Code Repair" (Thonmay Md Thoriqul Islam, FFR8A9,
ELTE IK). It uses the `elteikthesis` class by Máté Cserép and Bálint Bognár
(MIT, see `LICENSE`).

## Build

pdfLaTeX with BibTeX, no shell escape:

    latexmk -pdf main.tex      # or: make

The result is `main.pdf` (153 pages at the reviewed revision). In the source
archive the files are inside one folder, `thesis-latex/`; build from there.

## Layout

- `main.tex`: document root; `config.tex`: title page metadata.
- `chapters/`: Chapters 1 to 7 and Appendices A to G.
- `figures/`: UML and process diagrams as TikZ source with their PDFs
  (`figures/Makefile` rebuilds them); `images/ui/`: interface screenshots.
- `references.bib`: the bibliography (every entry is cited).
- `approved-topic-registration.pdf`: the approved topic form, inserted after the
  cover.
- `ai-declaration.docx`: the separate Declaration on the Use of AI Tools, to be
  signed by hand.
- `template-guidance.tex`: the template's guidance switch (off in this thesis).
