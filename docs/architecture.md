# Architecture

This repository separates relation semantics from artifact loading, command-line
entrypoints, experiments, and backend validation. The goal is to keep the
research artifact understandable while preserving compatibility with older
scripts.

## Relation Layer

`zk_offline_dqn/relations/` contains pure relation checks:

- `membership.py`
- `td_mvp.py`
- `forward_td_mlp.py`
- `one_step_sgd_tiny.py`
- `minibatch_td.py`
- `one_step_update.py`
- `short_trace.py`

These modules implement the Python semantic oracle for committed-data
membership, TD arithmetic, forward-model checks, tiny SGD updates, minibatch
constraints, and short trace chaining. They should remain free of CLI and file
layout assumptions.

## Verifier Adapter Layer

`zk_offline_dqn/verifiers/` loads artifacts, checks schema versions, and calls
the relation layer. This layer is the stable Python verification API used by
tests and the unified CLI.

## Artifact Schema And IO Layer

`zk_offline_dqn/artifacts/` centralizes:

- schema version constants,
- JSON loading/writing helpers,
- artifact manifest metadata,
- public/private/debug field role classification.

Schema strings and required artifact fields must remain backward compatible
unless a deliberate migration is approved.

## CLI Layer

The unified CLI is:

```text
python -m zk_offline_dqn.cli.main
```

Current namespaces include:

- `verify`
- `benchmark`
- `report`

The CLI should call library modules and report scripts without changing
relation semantics.

## Experiment And Report Layer

`scripts/experiments/` contains regression, benchmark, Kaggle validation, and
report orchestration scripts.

`zk_offline_dqn/experiments/` contains descriptive manifests and report table
builders that read existing outputs and write deterministic summaries under
`artifacts/reports/final_ndss/`.

Report generation does not rerun heavy benchmarks or SP1 proof generation.

## SP1 Backend Layer

`zk_backend/td_mvp/sp1/` contains the Rust SP1 workspace:

- host package: `td-mvp-host`
- guest package: `td-mvp-guest`
- shared package: `td-mvp-shared`

Python-side SP1 helpers live under `zk_offline_dqn/backends/sp1/` and describe
fixtures, command templates, and metric loading. They do not execute commands
on import.

The validated SP1 proof claim is scoped to the TD MVP backend and
`zk_backend/test_vectors/td_mvp_case_0.json`.

## Compatibility Wrappers

Legacy exporters and verifier scripts under `scripts/artifacts_export/` remain
available because regression, documentation, and older workflows still refer to
them. Prefer the unified CLI for new verification workflows, but keep wrappers
until their users are fully retired.
