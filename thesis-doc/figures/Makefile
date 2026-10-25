# Build every standalone figure to PDF: make -C figures
TEX := $(filter-out umlstyle.tex,$(wildcard *.tex))
PDF := $(TEX:.tex=.pdf)
all: $(PDF)
%.pdf: %.tex umlstyle.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error -quiet $<
	latexmk -c $<
clean:
	latexmk -C $(TEX)
.PHONY: all clean
