
MAKEINFO = makeinfo
HTML_FLAGS = --html --no-split
TEXI2DVI = texi2dvi
TEXI2DVI_FLAGS = --expand

TEXI_TEMP = *.log *.cp *.fn *.vr *.tp *.aux *~ *.toc *.ky *.pg *.vrs *.cps *.fns

SRC = dibs.texi commands.texi doc_macros.texi installing.texi overview.texi \
	variables.texi using.texi todo.texi

.PHONY: all help clean 

help:
	@echo "Targets:"  
	@echo " "
	@echo "help:          Prints this message."
	@echo "dibs.info:     Creates info documentation."
	@echo "dibs.html:     Creates html documentation."
	@echo "dibs.dvi:      Creates dvi documentation."
	@echo "all:           Creates all documentation."
	@echo "clean:         Removes all generated files."
	@echo " "

all:
	${MAKE} dibs.info dibs.html dibs.dvi dibs-faq.html
	rm -f ${TEXI_TEMP}

clean:
	rm -f dibs.info dibs.html dibs.dvi ${TEXI_TEMP}

dibs.info: ${SRC}
	${MAKEINFO} dibs.texi

dibs.html: ${SRC}
	${MAKEINFO} ${HTML_FLAGS} dibs.texi

dibs.dvi: ${SRC}
	${TEXI2DVI} ${TEXI2DVI_FLAGS} dibs.texi

dibs-faq.html: dibs-faq.texi
	${MAKEINFO} ${HTML_FLAGS} dibs-faq.texi