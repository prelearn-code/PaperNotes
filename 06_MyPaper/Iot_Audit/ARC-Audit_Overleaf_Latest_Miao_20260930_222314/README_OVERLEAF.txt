Current manuscript revision: 2026-10-09 evening.
Directory cleanup: 2026-10-21. The original directory name is retained.

English manuscript: main.tex / main.pdf.
Chinese manuscript: main_cn.tex / main_cn.pdf.
Supplementary material: supplementary.tex / supplementary.pdf.

Current evidence, tables, plotting scripts, and experiment source snapshot:
evidence/current-secure/.
The full experiment package is ../paper_C1_reduced_C2C3_full_20261009.zip.
C1 uses two 21,600-record windows; C2/C3 use the full train1/train2 segments.

For Overleaf, upload this directory preserving its subdirectories and select
main.tex with pdfLaTeX. latexmkrc builds supplementary.tex first to resolve
external references. For a local English build, run bash build.sh or
latexmk -pdf main.tex. Select supplementary.tex to preview the companion.

main_cn.tex uses fontspec and xeCJK and requires XeLaTeX with the configured
Windows fonts. Its font paths must match the compilation environment.
Build the supplement before the Chinese manuscript to provide its references.

Current PDFs, LaTeX sources, bibliography, class/style files, current figures,
experiment observations and scripts are retained. Historical manuscript and
evidence copies, review records, and generated compilation intermediates were
removed during cleanup. Compilation recreates the auxiliary files.
