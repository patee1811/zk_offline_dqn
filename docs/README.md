# Project Documentation Index

This directory is the canonical documentation entry point for implementation
and reproducibility notes. The `paper/` directory is intentionally separate and
is not edited by cleanup phases unless explicitly approved.

## Start Here

- `architecture.md` - current code and workflow architecture.
- `reproducibility.md` - regression, SP1 validation, and report regeneration.
- `sp1_python_alignment.md` - Python/SP1 field and command alignment.
- `dev_commands.md` - developer command reference.
- `legacy_status.md` - active vs compatibility entrypoints.
- `reporting_policy.md` - generated report commit policy.
- `refactor_final_summary.md` - completed phases and remaining limitations.

## Scope

This project verifies selected offline-DQN relations over committed artifacts.
It does not claim a full proof of DQN training. The validated SP1 proof claim is
scoped to the TD MVP backend and
`zk_backend/test_vectors/td_mvp_case_0.json`.

## Artifact Contracts

- `artifact_schema.md` - schema notes for TD, one-step, and short-trace
  artifacts.
- `one_step_field_classification.md` - older one-step field audit retained as
  background.

## Backend And Threat Model

- `zk_backend_mvp.md` - TD MVP statement and public/private field split.
- `backend_selection_v0_12.md` - historical SP1 selection decision.
- `backend_choice.md` - backend comparison notes and deferred alternatives.
- `threat_model.md` - prover/verifier assumptions, non-goals, and boundaries.

## Migration Logs

`refactor_phase*.md` files are internal migration logs. They are useful for
auditing how the repository reached its current layout, but reviewer-facing
workflows should start with the docs listed above.

## Core Commands

Run the full Python regression:

```text
python scripts/experiments/run_full_regression.py
```

Generate paper-facing report snapshots:

```text
python scripts/experiments/generate_paper_reports.py
```

Use the unified CLI:

```text
python -m zk_offline_dqn.cli.main --help
```
