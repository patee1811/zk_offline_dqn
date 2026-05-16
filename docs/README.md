# Project Documentation Index

This directory is the canonical documentation entry point for implementation
and reproducibility notes. The `paper/` directory is intentionally separate and
is not edited by cleanup phases unless explicitly approved.

## Start Here

- `architecture.md` - current code and workflow architecture.
- `reproducibility.md` - regression, SP1 validation, and report regeneration.
- `sp1_python_alignment.md` - Python/SP1 field and command alignment.
- `release_checklist.md` - final release and validation checklist.
- `paper_alignment_audit.md` - paper claim support and risk notes.

## Scope

This project verifies selected offline-DQN relations over committed artifacts.
It does not claim a full proof of DQN training. The validated SP1 proof claim is
scoped to the TD MVP backend and
`zk_backend/test_vectors/td_mvp_case_0.json`.

## Artifact Contracts

- `archive/internal_manifests/artifact_schema.md` - schema notes for TD,
  one-step, and short-trace
  artifacts.
- `archive/internal_manifests/reporting_policy.md` - generated report commit
  policy.
- `archive/internal_manifests/legacy_usage_manifest.md` - active vs
  compatibility entrypoints.
- `archive/internal_manifests/dev_commands.md` - developer command reference.

## Backend And Threat Model

- `archive/internal_manifests/zk_backend_mvp.md` - TD MVP statement and
  public/private field split.
- `archive/internal_manifests/backend_selection_v0_12.md` - historical SP1
  selection decision.
- `archive/internal_manifests/backend_choice.md` - backend comparison notes and
  deferred alternatives.
- `archive/internal_manifests/threat_model.md` - prover/verifier assumptions,
  non-goals, and boundaries.

## Migration Logs

Internal refactor logs are archived under `docs/archive/refactor_history/`.
They are useful for auditing how the repository reached its current layout, but
reviewer-facing workflows should start with the docs listed above.

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
