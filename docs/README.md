# Project Documentation Index

This directory is the canonical documentation entry point for the project.
`paper/` is intentionally separate and should be updated only during the paper
writing phase.

## Current Locked State

Start here for the final Phase E implementation state:

- `current_benchmark_snapshot.md` - current benchmark snapshot and historical
  SP1 context.
- `dev_commands.md` - reproduction commands for Python smoke, SP1 refresh, and
  final Phase E aggregation.
- `ndss_astar_3_month_roadmap.md` - roadmap used to drive the final Phase E
  artifact and paper rewrite.

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
- `ndss_astar_3_month_roadmap.md` - planning roadmap. Treat it as historical
  planning unless it conflicts with the final Phase E artifact.

## Canonical Commands

Run the full Python regression from the repository root:

```bash
python scripts/experiments/run_full_regression.py
```

Run the full Phase E SP1 benchmark path on Linux, WSL2 Ubuntu, macOS, or Kaggle:

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
