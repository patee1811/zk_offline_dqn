# Paper Draft README

This folder contains the working LaTeX manuscript for the project:

> **ZK-Verifiable Temporal-Difference Computation for Offline DQN over Committed Trajectories**

The manuscript is scoped to the current repository milestone: a real SP1 backend for single-transition TD and minibatch-TD verification over committed transition data, plus Python semantic verifiers and pre-ZK extension checks for one-step and short-trace statements.

## Current Paper Status

The paper can currently claim:

- committed offline transition membership through Merkle roots and paths;
- fixed-point DQN TD target, TD error, and SmoothL1 loss verification;
- minibatch-average TD loss verification for batch sizes 2, 4, and 8;
- an SP1 host/guest/shared implementation for the TD MVP relation;
- cryptographic proof benchmarks for TD-1, TD-2, TD-4, and TD-8;
- Python/SP1 agreement on valid controls and tampered witnesses;
- Python-only one-step and short-trace verifiers as future backend targets.

The paper should not claim:

- a full proof of offline DQN training from initialization to final checkpoint;
- proof of neural-network forward passes, argmax computation, gradients, or optimizer updates inside SP1;
- proof of model selection, early stopping, replay randomness, or target-network synchronization over a full training run;
- production-scale recursive or aggregated proofs.

The safest current positioning is:

> a scoped ZK-verifiable TD-computation backend for offline DQN artifacts, with locked SP1 proof benchmarks and explicit boundaries on what remains outside the proof.

## Folder Structure

```text
paper/
|-- main.tex
|-- refs.bib
|-- README.md
`-- sections/
    |-- abstract.tex
    |-- introduction.tex
    |-- related_work.tex
    |-- problem_setup.tex
    |-- zk_direction.tex
    |-- experimental_setup.tex
    |-- results.tex
    |-- discussion.tex
    |-- conclusion.tex
    `-- appendix.tex
```

## Manuscript Organization

- **Abstract**: states the scoped SP1 TD/minibatch-TD contribution and locked benchmark results.
- **Introduction**: motivates verifiable offline RL and positions the work between proof-of-learning, ZKML, and RL-specific Bellman checks.
- **Related Work**: covers offline RL, proof-of-learning/proof-of-training, verifiable ML/ZKML, proof systems, and verifiable RL.
- **Problem Setup**: defines committed transitions, fixed-point TD arithmetic, and the exact backend statement.
- **System Design**: describes public inputs, private witnesses, canonical serialization, fixed-point arithmetic, minibatch averaging, SP1 modules, and Python oracle roles.
- **Experimental Setup**: records artifact paths, commands, benchmark cases, and evaluation criteria.
- **Results**: reports Python regression, SP1 proof metrics, tamper rejection, and pre-ZK extension context.
- **Discussion**: separates the useful claim from limitations and gives the Q1 positioning.
- **Conclusion**: summarizes the current contribution and immediate next research steps.
- **Appendix**: records relation details, public/private fields, tamper cases, and reproducibility commands.

## Locked Benchmark Snapshot

The SP1 proof benchmark was generated at UTC `2026-05-12T12:37:34.964280+00:00` with:

```bash
python scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

Summary:

- Python expected outcomes passed: `True`
- SP1 expected outcomes passed: `True`
- Python/SP1 agreement: `True`
- SP1 negative cases passed: `True`

Core proof metrics:

| Case | Batch | Prove sec | Verify sec | Proof bytes | Cycles |
|---|---:|---:|---:|---:|---:|
| TD-1 | 1 | 142.324547 | 0.157464 | 2782625 | 382915 |
| TD-2 | 2 | 154.923089 | 0.157712 | 2787687 | 725309 |
| TD-4 | 4 | 188.501940 | 0.155969 | 2795631 | 1425790 |
| TD-8 | 8 | 275.077262 | 0.157424 | 2812327 | 2834727 |

## Build Notes

Compile from the `paper/` directory:

```bash
latexmk -pdf main.tex
```

or:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

On Windows, MiKTeX must complete first-run setup before `latexmk` or `pdflatex` can build the manuscript.
