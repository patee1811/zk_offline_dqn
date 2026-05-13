# Phase D Second Environment

This document records the Phase D second-environment path for the NDSS/A*
roadmap.

## Relation

`forward_td_mlp_v1`

The second-environment smoke uses `MountainCar-v0` with a small synthetic
quantized MLP:

```text
MountainCar-v0 2-8-8-3
```

The fixture checks committed transition membership, model commitments,
fixed-point MLP forward passes, Double-DQN argmax/value selection, Bellman TD,
SmoothL1 loss, and batch loss aggregation.

## Commands

Python-only smoke:

```bash
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1
```

SP1 execute for valid and tamper cases:

```bash
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py
```

SP1 proof for batch 1:

```bash
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
```

## Output Paths

```text
data/mountaincar_random_seed42_transitions.pkl
data/mountaincar_random_seed42_transitions.summary.json
artifacts/mountaincar_random_seed42_leaf_hashes.json
artifacts/mountaincar_random_seed42_merkle.json
artifacts/benchmarks/second_env_mountaincar/summary.json
artifacts/benchmarks/second_env_mountaincar/benchmark_matrix.csv
artifacts/benchmarks/second_env_mountaincar/summary.md
```

## Scope

This is a second environment/spec benchmark, not a policy-performance claim.
The default dataset is collected with a seeded random policy. The purpose is to
show that the committed-data and forward-TD proof relation is not hard-wired to
CartPole dimensions or two-action control.
