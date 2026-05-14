# Project Documentation Index

This directory is the canonical documentation entry point for the project.
`paper/` is intentionally separate from implementation notes.

## Current State

Start here for the achieved implementation state:

- `current_benchmark_snapshot.md` - current benchmark snapshot.
- `dev_commands.md` - reproduction commands for Python smoke, SP1 refresh, and
  benchmark aggregation.
- `forward_td_mlp_result.md` - model-grounded forward-TD proof result.
- `one_step_sgd_tiny_result.md` - micro-scale SGD update proof result.
- `second_environment_forward_td_result.md` - MountainCar forward-TD proof
  result.

## Backend And Threat Model

- `zk_backend_mvp.md` - TD MVP statement and public/private field split.
- `backend_selection_v0_12.md` - historical SP1 selection decision.
- `backend_choice.md` - backend comparison notes and deferred alternatives.
- `threat_model.md` - prover/verifier assumptions, non-goals, and security
  boundaries.

## Artifact Contracts

- `artifact_schema.md` - canonical schema notes for TD, one-step, and
  short-trace artifacts.
- `one_step_field_classification.md` - older one-step field audit retained as
  background for update-proof work.

## Operations

- `dev_commands.md` - local commands for regression, SP1 runs, and benchmark
  refreshes.

## Canonical Commands

Run the full Python regression from the repository root:

```bash
python scripts/experiments/run_full_regression.py
```

Run the full SP1 benchmark path on Linux, WSL2 Ubuntu, macOS, or Kaggle:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
python3 scripts/experiments/run_final_ndss_regression.py
```

Run the SP1 negative suite from the SP1 workspace:

```bash
cd zk_backend/td_mvp/sp1
bash run_negative_cases.sh
```
