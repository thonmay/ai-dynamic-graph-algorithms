# Build the thesis PDFs from LaTeX sources.
# Usage: make          (build all PDFs)
#        make design   (build just the design doc)
#        make spec     (build just the requirements spec)
#        make clean    (remove build artifacts)

TEXLIVE ?= texlive/2026

D := docs
DESIGN_TEX := $(D)/design.tex
SPEC_TEX := $(D)/planning-spec-short.tex
DESIGN_PDF := $(D)/design.pdf
SPEC_PDF := $(D)/planning-spec-short.pdf

PDFLATEX := pdflatex -interaction=nonstopmode -halt-on-error -file-line-error
BIBTEX := bibtex

# Load the texlive module in a fresh shell
define run_tex
	@bash -c 'source /etc/home/bashrc 2>/dev/null; module add $(TEXLIVE) 2>/dev/null; cd $(dir $@) && $(1)'
endef

all: $(DESIGN_PDF) $(SPEC_PDF)

$(DESIGN_PDF): $(DESIGN_TEX) $(wildcard $(D)/diagrams/*.png) $(wildcard $(D)/references.bib)
	$(call run_tex,$(PDFLATEX) design && $(BIBTEX) design && $(PDFLATEX) design && $(PDFLATEX) design)

$(SPEC_PDF): $(SPEC_TEX)
	$(call run_tex,$(PDFLATEX) planning-spec-short)

clean:
	rm -f $(D)/*.aux $(D)/*.bbl $(D)/*.blg $(D)/*.log $(D)/*.out $(D)/*.toc $(D)/*.synctex.gz

.PHONY: all clean