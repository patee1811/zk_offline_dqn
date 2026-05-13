# Paper Draft README

This folder contains the working LaTeX manuscript for the project:

> **ZK-Verifiable Temporal-Difference Computation for Offline DQN over Committed Trajectories**

The manuscript is scoped to the current repository milestone: real SP1 backend
proofs for distinct minibatch TD, model-grounded forward-TD MLP, and a
micro-scale one-step SGD update over committed transition data. It does not
claim a full proof of DQN training.

## Current Paper Status

The paper can currently claim:

- committed offline transition membership through Merkle roots and paths;
- fixed-point DQN TD target, TD error, and SmoothL1 loss verification;
- distinct replay minibatch-average TD loss verification for batch sizes 2, 4, and 8;
- an SP1 host/guest/shared implementation for TD, forward-TD MLP, and tiny
  one-step SGD relations;
- cryptographic proof benchmarks for TD-1, TD-2, TD-4, TD-8, CartPole
  forward-TD, MountainCar forward-TD, and CartPole tiny one-step SGD;
- Python/SP1 agreement on valid controls and tampered witnesses;
- Python short-trace verifiers as future backend targets.

The paper should not claim:

- a full proof of offline DQN training from initialization to final checkpoint;
- full proof of neural-network training across many optimizer updates inside
  SP1;
- proof of model selection, early stopping, replay randomness, or target-network synchronization over a full training run;
- production-scale recursive or aggregated proofs.

The safest current positioning is:

> a scoped ZK-verifiable offline-DQN relation stack, with locked SP1 proof benchmarks and explicit boundaries on what remains outside the proof.

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
- **Results**: reports Python regression, SP1 proof metrics, tamper rejection, and remaining trace-composition context.
- **Discussion**: separates the useful claim from limitations and gives the Q1 positioning.
- **Conclusion**: summarizes the current contribution and immediate next research steps.
- **Appendix**: records relation details, public/private fields, tamper cases, and reproducibility commands.

## Locked Benchmark Snapshot

The final Phase E aggregate was generated at UTC
`2026-05-13T23:40:09.274341+00:00` with:

```bash
python scripts/experiments/run_final_ndss_regression.py
```

Summary:

- Benchmark rows: `29`
- Tamper rows: `21`
- All loaded components passed expected outcomes: `True`

Core proof metrics:

| Case | Batch | Prove sec | Verify sec | Proof bytes | Cycles |
|---|---:|---:|---:|---:|---:|
| TD-1 | 1 | 97.955756 | 0.126565 | 2783869 | 385048 |
| TD-2 | 2 | 120.669043 | 0.127258 | 2788227 | 730778 |
| TD-4 | 4 | 141.309797 | 0.125481 | 2796699 | 1435787 |
| TD-8 | 8 | 202.921645 | 0.126658 | 2812915 | 2845813 |
| CartPole forward-TD | 1 | 148.418458 | 0.127259 | 2797833 | 1543753 |
| MountainCar forward-TD | 1 | 107.926506 | 0.126694 | 2787889 | 683942 |
| CartPole one-step SGD tiny | 1 | 115.494141 | 0.125332 | 2789940 | 862136 |

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
