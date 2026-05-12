# Project Documentation Index

This directory is the canonical documentation entry point for the project.
`paper/` is intentionally separate and should be updated only during the paper
writing phase.

## Current Locked State

Start here for the implementation state that Week 6 should write from:

- `week5_artifact_package.md` - locked backend scope, reproduction commands,
  SP1 benchmark table, tamper table, limitations, and submission recommendation.
- `current_benchmark_snapshot.md` - historical and current benchmark snapshots.

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
- `q1_astar_roadmap_4_6_weeks.md` - planning roadmap. Treat it as historical
  planning unless it conflicts with the locked Week 5 package.

## Canonical Commands

Run the full Python regression from the repository root:

```bash
python scripts/experiments/run_full_regression.py
```

Run the Phase A distinct minibatch SP1 benchmark on Linux, WSL2 Ubuntu, macOS,
or Kaggle:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
```

Run the SP1 negative suite from the SP1 workspace:

```bash
cd zk_backend/td_mvp/sp1
bash run_negative_cases.sh
```
