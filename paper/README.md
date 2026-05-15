# Paper Draft README

This folder contains the working LaTeX manuscript for the project:

> **ZK-Verifiable Temporal-Difference Computation for Offline DQN over Committed Trajectories**

The manuscript is scoped to the current repository milestone: relation-level
verification for selected offline-DQN artifacts, with a validated SP1 proof for
the TD MVP canonical vector. It does not claim a full proof of DQN training.

## Current Paper Status

The paper can currently claim:

- committed offline transition membership through Merkle roots and paths;
- fixed-point DQN TD target, TD error, and SmoothL1 loss verification;
- distinct replay minibatch-average TD loss verification for batch sizes 2, 4, and 8;
- an SP1 host/guest/shared implementation validated for the TD MVP canonical
  vector;
- a Kaggle proof result for `zk_backend/test_vectors/td_mvp_case_0.json`;
- Python/SP1 agreement on valid controls and tampered witnesses;
- Python short-trace verifiers as future backend targets.

The paper should not claim:

- a full proof of offline DQN training from initialization to final checkpoint;
- full proof of neural-network training across many optimizer updates inside
  SP1;
- proof of model selection, early stopping, replay randomness, or target-network synchronization over a full training run;
- production-scale recursive or aggregated proofs.

The safest current positioning is:

> a scoped ZK-verifiable offline-DQN relation stack, with a validated TD MVP SP1 proof and explicit boundaries on what remains outside the proof.

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

- **Abstract**: states the scoped relation-stack contribution and TD MVP SP1 proof result.
- **Introduction**: motivates verifiable offline RL and positions the work between proof-of-learning, ZKML, and RL-specific Bellman checks.
- **Related Work**: covers offline RL, proof-of-learning/proof-of-training, verifiable ML/ZKML, proof systems, and verifiable RL.
- **Problem Setup**: defines committed transitions, fixed-point TD arithmetic, and the exact backend statement.
- **System Design**: describes public inputs, private witnesses, canonical serialization, fixed-point arithmetic, minibatch averaging, SP1 modules, and Python oracle roles.
- **Experimental Setup**: records artifact paths, commands, benchmark cases, and evaluation criteria.
- **Results**: reports Python regression, SP1 proof metrics, tamper rejection, and remaining trace-composition context.
- **Discussion**: separates the useful claim from limitations and gives the Q1 positioning.
- **Conclusion**: summarizes the current contribution and immediate next research steps.
- **Appendix**: records relation details, public/private fields, tamper cases, and reproducibility commands.

## Benchmark Snapshot

Paper-facing reports are generated with:

```bash
python scripts/experiments/generate_paper_reports.py
```

Summary:

- Benchmark rows: `29`
- Tamper rows: `21`
- Full Python regression: `15/15`
- TD MVP proof generated: `true`
- TD MVP proof verified: `true`

TD MVP proof metrics:

| Case | Prove sec | Verify sec | Proof bytes | Cycles |
|---|---:|---:|---:|---:|
| TD MVP canonical vector | 167.726006 | 0.190326 | 2783869 | 385048 |

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
