# LaTeX draft for `Zero-Knowledge Verifiable Offline DQN Training from Committed Trajectories`

This folder is a working LaTeX draft generated from the current experimental state of the project.

## Files
- `main.tex`: main manuscript entry point
- `sections/`: section files
- `refs.bib`: starter bibliography placeholders

## Recommended next writing updates
1. Add citations and refine related work.
2. Export training curves from Python and include them as figures.
3. Add a finalized experimental table for all baselines.
4. Add a dedicated section on commitments, Merkle trees, and proof statements.

The script will:
1. refresh MiKTeX file database/format (when `initexmf` is available),
2. compile with `latexmk` if installed,
3. otherwise fall back to the classic `pdflatex -> bibtex -> pdflatex -> pdflatex` flow.
