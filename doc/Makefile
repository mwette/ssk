# Makefile

docs: ssk_impl.pdf ssk_mdrw.pdf ssk_spec.pdf

%.pdf: %.tex
	latex $<
	dvipdf $*.dvi

#ssk_impl.pdf: ssk_impl.tex
