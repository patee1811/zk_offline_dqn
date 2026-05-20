# ZK-Offline-DQN

Relation-level verification utilities for selected offline DQN artifacts over
committed transition data.

This repository is a research artifact. It is not a full zero-knowledge proof
of DQN training from initialization to final checkpoint, and it does not claim
honest data collection, model selection, recursive aggregation, or proof
coverage for every relation.

The supported SP1 proof claims are scoped to backend validation artifacts:

```text
SP1 proof generation and verification passed on Kaggle for the TD MVP SP1
backend using zk_backend/test_vectors/td_mvp_case_0.json.

SP1 proof generation and verification passed on Kaggle for Merkle membership
of a canonical leaf hash against a provenance-bound dataset root using
zk_backend/test_vectors/merkle_membership_case_0.json.

SP1 proof generation and verification passed on Kaggle for canonical tiny
vectors for Forward-TD MLP, one-step SGD tiny, and short trace checkpoint
chaining using the corresponding cases under zk_backend/test_vectors/.

SP1 proof generation and verification passed on Kaggle for a canonical
batch-size-1 one-step Offline-DQN training update using
zk_backend/test_vectors/training_update_case_0.json. The relation includes
replay membership, forward TD computation, SmoothL1 loss, backpropagated
gradient through a tiny Linear-ReLU-Linear MLP, fixed-point SGD, and the
checkpoint transition.
```

Extension relations are checked by Python semantic oracles unless a separate
backend validation artifact is explicitly cited. The Forward-TD MLP,
one-step SGD tiny, short trace, and training-update SP1 claims are
canonical-vector coverage, not full DQN training, Adam, recursive aggregation,
model selection, or all replay batches.

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
- `zk_backend/merkle_membership/sp1/`: Rust SP1 host, guest, and shared crates
  for canonical leaf-hash membership against a provenance-bound dataset root.
- `zk_backend/forward_td_mlp/sp1/`, `zk_backend/one_step_sgd_tiny/sp1/`, and
  `zk_backend/short_trace/sp1/`: Rust SP1 host, guest, and shared crates for
  canonical tiny relation vectors.
- `zk_backend/training_update/sp1/`: Rust SP1 host, guest, and shared crates
  for the canonical batch-size-1 one-step training update vector.
- `scripts/artifacts_export/`: legacy exporters/verifiers retained for
  compatibility and regression reproducibility.
- `scripts/experiments/`: regression, benchmark, Kaggle validation, and report
  orchestration scripts.

See `docs/architecture.md` for a fuller layer-by-layer map. See
`docs/claim_matrix.md` and `docs/backend_coverage.md` for current claim
boundaries and backend coverage.

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

## Dataset Provenance Pipeline

Dataset commitments should flow through collection/import, audit, manifest, and
then Merkle commitment. Generated canonical datasets live under
`artifacts/datasets/<dataset_id>/`; manually downloaded source files live under
`artifacts/data_sources/<dataset_id>/source.jsonl` or `source.npz`. Both
directories are ignored and should not be committed.

The dataset Merkle commitment is provenance-bound: `merkle_tree.json` stores
`dataset_root`, `manifest_hash`, `audit_report_hash`, `raw_trajectory_hash`,
and `collection_log_final_hash` when available. Use
`scripts/data/verify_dataset_commitment.py` to verify that the commitment still
matches the manifest, audit report, raw transitions, collection log, and Merkle
leaves.

Self-collected audited CartPole smoke path:

```text
python scripts/data/collect_audited_dataset.py --env-id CartPole-v1 --dataset-id cartpole-random-v1 --policy random --num-episodes 2 --base-seed 12345 --max-steps-per-episode 200 --out-dir artifacts/datasets/cartpole-random-v1
python scripts/data/audit_replay_dataset.py --dataset-dir artifacts/datasets/cartpole-random-v1
python scripts/data/commit_audited_dataset.py --dataset-dir artifacts/datasets/cartpole-random-v1
python scripts/data/verify_dataset_commitment.py --dataset-dir artifacts/datasets/cartpole-random-v1
```

Self-collected audited MountainCar smoke path:

```text
python scripts/data/collect_audited_dataset.py --env-id MountainCar-v0 --dataset-id mountaincar-random-v1 --policy random --num-episodes 2 --base-seed 22345 --max-steps-per-episode 200 --out-dir artifacts/datasets/mountaincar-random-v1
python scripts/data/audit_replay_dataset.py --dataset-dir artifacts/datasets/mountaincar-random-v1
python scripts/data/commit_audited_dataset.py --dataset-dir artifacts/datasets/mountaincar-random-v1
```

Public benchmark imports are source-integrity commitments, not honest-collection
proofs:

```text
python scripts/data/import_public_dataset.py --source-jsonl artifacts/data_sources/public-cartpole-jsonl-v1/source.jsonl --dataset-id public-cartpole-jsonl-v1 --env-id CartPole-v1 --out-dir artifacts/datasets/public-cartpole-jsonl-v1
python scripts/data/import_public_dataset.py --source-npz artifacts/data_sources/public-npz-example-v1/source.npz --dataset-id public-npz-example-v1 --env-id CartPole-v1 --out-dir artifacts/datasets/public-npz-example-v1
python scripts/data/import_public_dataset.py --minari-dataset-id D4RL/pointmaze/umaze-v2 --dataset-id minari-pointmaze-umaze-v2-100 --out-dir artifacts/datasets/minari-pointmaze-umaze-v2-100 --max-transitions 100
```

Recommended later subsets are 10k/50k/100k transitions for Minari/D4RL
PointMaze imports such as `D4RL/pointmaze/umaze-v2`,
`D4RL/pointmaze/umaze-dense-v2`, `D4RL/pointmaze/medium-v2`, and
`D4RL/pointmaze/open-v2`. For self-collected data, use 10k transitions for
`cartpole-random-v1` and `mountaincar-random-v1`; future policy support may add
10k `cartpole-medium-v1`, 10k `cartpole-expert-v1`, 50k
`cartpole-mixed-v1`, 10k `mountaincar-medium-v1`, and 50k
`mountaincar-mixed-v1`.

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

cd zk_backend/merkle_membership/sp1
cargo test
cargo run --release -p merkle-membership-host -- --execute --case ../../test_vectors/merkle_membership_case_0.json
RUN_SP1_PROVE=1 cargo run --release -p merkle-membership-host -- --prove --case ../../test_vectors/merkle_membership_case_0.json --out-dir ../../../artifacts/reports/provenance/sp1/merkle_membership

cd zk_backend/forward_td_mlp/sp1
cargo test
cargo run --release -p forward-td-mlp-host -- --execute --case ../../test_vectors/forward_td_mlp_case_0.json
RUN_SP1_PROVE=1 cargo run --release -p forward-td-mlp-host -- --prove --case ../../test_vectors/forward_td_mlp_case_0.json --out-dir ../../../artifacts/reports/provenance/sp1/forward_td_mlp

cd zk_backend/one_step_sgd_tiny/sp1
cargo test
cargo run --release -p one-step-sgd-tiny-host -- --execute --case ../../test_vectors/one_step_sgd_tiny_case_0.json
RUN_SP1_PROVE=1 cargo run --release -p one-step-sgd-tiny-host -- --prove --case ../../test_vectors/one_step_sgd_tiny_case_0.json --out-dir ../../../artifacts/reports/provenance/sp1/one_step_sgd_tiny

cd zk_backend/short_trace/sp1
cargo test
cargo run --release -p short-trace-host -- --execute --case ../../test_vectors/short_trace_case_0.json
RUN_SP1_PROVE=1 cargo run --release -p short-trace-host -- --prove --case ../../test_vectors/short_trace_case_0.json --out-dir ../../../artifacts/reports/provenance/sp1/short_trace

cd zk_backend/training_update/sp1
cargo test
cargo run --release -p training-update-host -- --execute --case ../../test_vectors/training_update_case_0.json
RUN_SP1_PROVE=1 cargo run --release -p training-update-host -- --prove --case ../../test_vectors/training_update_case_0.json --out-dir ../../../artifacts/reports/provenance/sp1/training_update
```

Proof commands require the Rust/SP1 toolchain and are not part of the default
Python regression.

## Documentation

- `docs/reproducibility.md`: regression, SP1 validation, and report
  regeneration workflow.
- `docs/claim_matrix.md`: supported, oracle-only, and unsupported claim
  boundaries.
- `docs/backend_coverage.md`: relation-by-relation Python oracle and SP1
  coverage.
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
