# ZK-Offline-DQN

Relation-level verification utilities for selected offline DQN artifacts over
committed transition data.

This repository is a research artifact. It is not a full zero-knowledge proof
of DQN training from initialization to final checkpoint, and it does not claim
honest data collection, model selection, recursive aggregation, or proof
coverage for every relation.

The supported SP1 proof claim is scoped to one backend validation result:

```text
SP1 proof generation and verification passed on Kaggle for the TD MVP SP1
backend using zk_backend/test_vectors/td_mvp_case_0.json.
```

## Architecture

- `zk_offline_dqn/relations/`: pure relation checks for membership, TD MVP,
  forward-TD MLP, one-step SGD tiny, minibatch TD, one-step update, and short
  traces.
- `zk_offline_dqn/verifiers/`: artifact-facing adapters that load JSON
  fixtures and call relation modules without changing semantics.
- `zk_offline_dqn/artifacts/`: centralized schema constants, JSON IO helpers,
  manifest metadata, and public/private/debug field roles.
- `zk_offline_dqn/cli/`: unified CLI entrypoint available as
  `python -m zk_offline_dqn.cli.main`.
- `zk_offline_dqn/backends/sp1/`: Python-side SP1 fixture, command, and metric
  helpers.
- `zk_offline_dqn/experiments/`: report manifests and paper-facing report
  generation from existing outputs.
- `zk_backend/td_mvp/sp1/`: Rust SP1 host, guest, and shared crates for the TD
  MVP backend.
- `scripts/artifacts_export/`: legacy exporters/verifiers retained for
  compatibility and regression reproducibility.
- `scripts/experiments/`: regression, benchmark, Kaggle validation, and report
  orchestration scripts.

See `docs/architecture.md` for a fuller layer-by-layer map.

## Quick Start

Install the Python package in editable mode from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
$env:PYTHONPATH="."
```

Run the main local checks:

```text
python -m unittest discover tests
python scripts/experiments/run_full_regression.py
python -m zk_offline_dqn.cli.main --help
```

The full regression currently runs 15 Python-side checks and writes:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
artifacts/full_regression/
```

## Reports

Generate paper-facing report snapshots from existing outputs:

```text
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python -m zk_offline_dqn.cli.main report generate
```

Generated final reports live under:

```text
artifacts/reports/final_ndss/
```

SP1 proof provenance copied from Kaggle lives under:

```text
artifacts/reports/provenance/sp1/
```

The report generator does not rerun heavy benchmarks and does not rerun SP1
prove. Missing optional values are represented explicitly rather than inferred.

Paper-facing claim checks:

```text
python scripts/experiments/check_paper_claims.py
python scripts/experiments/check_paper_numbers_against_final_ndss.py
```

## SP1 Validation

Kaggle validation can run from a pushed branch or from a local workspace
archive. Proof generation is opt-in:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive --run-sp1-setup --run-sp1-execute --run-sp1-prove
```

The WSL2/Linux fallback commands are:

```text
cd zk_backend/td_mvp/sp1
cargo test
cargo run --release -p td-mvp-host -- --execute
RUN_SP1_PROVE=1 cargo run --release -p td-mvp-host -- --prove
```

Proof commands require the Rust/SP1 toolchain and are not part of the default
Python regression.

## Documentation

- `docs/reproducibility.md`: regression, SP1 validation, and report
  regeneration workflow.
- `docs/sp1_python_alignment.md`: Python/SP1 field and command alignment.
- `docs/archive/internal_manifests/dev_commands.md`: developer command reference.
- `docs/archive/internal_manifests/legacy_status.md`: active vs compatibility entrypoints.
- `docs/archive/internal_manifests/reporting_policy.md`: which generated reports should be committed.
- `docs/archive/refactor_history/refactor_final_summary.md`: completed phases and remaining limitations.

Legacy scripts are intentionally kept for compatibility. Prefer the unified CLI
and current scripts for new work, but do not remove legacy exporters or
verifiers without proving they are unused by regression and documentation.

## License

MIT. See `LICENSE`.
