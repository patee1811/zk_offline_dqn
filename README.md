# ZK-Offline-DQN

> ZK-backed TD verification prototype for offline Deep Q-Network training from committed trajectories.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/Framework-PyTorch-EE4C2C.svg)](https://pytorch.org/)
[![Regression](https://github.com/patee1811/zk_offline_dqn/actions/workflows/regression.yml/badge.svg?branch=master)](https://github.com/patee1811/zk_offline_dqn/actions/workflows/regression.yml)

## Status

This repository is a research prototype for verification-oriented offline RL. It is **not** a full zero-knowledge proof-of-training system.

Current contribution:

- commit a fixed CartPole offline transition dataset with a Merkle tree;
- export verification-friendly TD, one-step, and short-trace artifacts;
- verify committed-data membership, Bellman targets, SmoothL1 TD losses, checkpoint/model-state commitments, one-step SGD consistency, short trace chaining, target sync semantics, and deterministic sampling rules;
- run negative tamper tests and CI regression over committed fixtures;
- implement SP1 relation proofs for Merkle membership, TD/minibatch arithmetic,
  model-grounded forward-TD MLP checks, and one micro-scale SGD update.

Current backend status:

- Python artifact/verifier layer is implemented and regression-tested.
- SP1 is selected as the first concrete proving backend.
- `zk_backend/td_mvp/sp1/` contains a Rust SP1 workspace with `host`, `guest`, and `shared` crates.
- Kaggle SP1 proofs have been generated and verified for distinct TD-1/2/4/8,
  CartPole forward-TD MLP batch 1, MountainCar forward-TD MLP batch 1, and
  CartPole one-step SGD tiny batch 1. Tamper cases for batch structure, model
  weights, activations, argmax/value selection, and update tensors are
  rejected.
- The final benchmark package is under `artifacts/benchmarks/final_ndss/`.

## What Is Verified

The current Python verifiers check these relations over committed fixtures:

- **Membership:** transition leaves match serialized transition data and authenticate to the public Merkle root.
- **TD arithmetic:** Double-DQN target, TD error, and fixed-point SmoothL1 loss match the artifact witness.
- **Distinct batch loss:** minibatch average loss matches recomputed per-item losses, with public ordered `leaf_indices` and duplicate-index rejection for distinct replay batches.
- **Checkpoint anchoring:** checkpoint file SHA-256 and canonical online/target state-dict SHA-256 commitments match supplied checkpoints.
- **Forward TD consistency:** TD witness values match actual checkpoint forward semantics.
- **One-step update:** a simplified SGD update matches recomputed gradients, parameter deltas, learning rate, and pre/post checkpoints.
- **Short traces:** nested one-step updates chain through checkpoints, enforce target sync semantics, and enforce contiguous or seeded-permutation sampling rules.
- **Schema checks:** verifiers reject missing or incompatible `schema_version` values.
- **Negative tests:** tampered artifacts are expected to fail.

Important non-goals:

- no full zero-knowledge proof-of-training is generated yet;
- no full DQN training proof from initialization to final checkpoint;
- no large neural-network training trace inside a proving backend;
- no Adam optimizer proof;
- no claim that data collection or rewards were honest before commitment.

## Repository Map

```text
zk_offline_dqn/
  zk_specs.py                  fixed-point and TD arithmetic conventions
  merkle.py                    shared leaf/Merkle hashing helpers
  commitments.py               canonical PyTorch state-dict commitments
  models.py                    shared DQN QNetwork
  io_utils.py                  small file/JSON/checkpoint helpers
  artifact_export_utils.py     shared artifact export/verifier helpers

scripts/
  data_gen/                    dataset generation utilities
  training/                    offline DQN, CQL-lite, and BC trainers
  artifacts_export/            artifact exporters and verifiers
  experiments/                 regression, negative tests, and benchmarks
  zk_proofs/                   pre-backend Merkle utility scripts
  evaluation/                  checkpoint evaluation utilities
  analysis/                    inspection and plotting helpers

docs/
  artifact_schema.md           canonical artifact schema and cleanup notes
  zk_backend_mvp.md            first ZK backend statement
  backend_choice.md            backend comparison
  backend_selection_v0_12.md   SP1 selection record
  threat_model.md              prover/verifier threat model
  current_benchmark_snapshot.md

zk_backend/
  test_vectors/td_mvp_case_0.json
  td_mvp/sp1/                  SP1 host/guest/shared TD MVP workspace
```

`paper/` contains the manuscript draft and is intentionally separate from this technical cleanup path.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
$env:PYTHONPATH="."
```

The current SP1 milestone should be developed on Linux/macOS or WSL2 Ubuntu, not native Windows PowerShell. See `zk_backend/td_mvp/sp1/toolchain.md`.

## Core Commands

Build Merkle fixtures from a transition dataset:

```powershell
python scripts/zk_proofs/build_leaf_hashes.py
python scripts/zk_proofs/build_merkle_root.py
python scripts/zk_proofs/check_merkle_membership.py
```

Verify the current TD MVP test vector:

```powershell
python scripts/artifacts_export/verify_td_mvp_test_vector.py
python scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```

Run the full Python regression suite:

```powershell
python scripts/experiments/run_full_regression.py
```

Expected summary:

```text
num_checks = 15
all_regression_passed = True
```

Regression reports are written to:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
artifacts/full_regression/*.stdout.txt
artifacts/full_regression/*.stderr.txt
```

## Regression Coverage

The full regression runner currently executes:

1. Python compile checks for `zk_offline_dqn` and `scripts`.
2. Minibatch TD artifact verification.
3. Forward TD consistency verification.
4. One-step update verification.
5. Short-trace contiguous verification.
6. Short-trace seeded-permutation verification.
7. One-step negative tests.
8. Short-trace negative tests.
9. Minibatch TD negative tests.
10. Distinct TD-1/2/4/8 Python-only benchmark smoke.
11. Forward-TD MLP Python-only benchmark smoke.
12. One-step SGD tiny Python-only benchmark smoke.
13. MountainCar forward-TD Python-only benchmark smoke.
14. TD MVP test-vector negative tests.
15. Paper/final-NDSS number consistency check.

CI runs the same regression entrypoint through `.github/workflows/regression.yml`.

## SP1 Backend

The first real SP1 TD MVP proof has been implemented.

Target relation:

```text
leaf == SerializeTransition(transition)
leaf_hash == SHA256(CanonicalLeafEncoding(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + (gamma_fp * q_target_max_fp) // fp_scale
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

Current SP1 proof results:

```text
benchmark_rows = 29
tamper_rows = 21
all_components_passed = True
TD-1 prove_time_sec = 97.955756, verify_time_sec = 0.126565, proof_size_bytes = 2783869, cycle_count = 385048
TD-2 prove_time_sec = 120.669043, verify_time_sec = 0.127258, proof_size_bytes = 2788227, cycle_count = 730778
TD-4 prove_time_sec = 141.309797, verify_time_sec = 0.125481, proof_size_bytes = 2796699, cycle_count = 1435787
TD-8 prove_time_sec = 202.921645, verify_time_sec = 0.126658, proof_size_bytes = 2812915, cycle_count = 2845813
CartPole forward-TD prove_time_sec = 148.418458, verify_time_sec = 0.127259, proof_size_bytes = 2797833, cycle_count = 1543753
MountainCar forward-TD prove_time_sec = 107.926506, verify_time_sec = 0.126694, proof_size_bytes = 2787889, cycle_count = 683942
CartPole one-step SGD tiny prove_time_sec = 115.494141, verify_time_sec = 0.125332, proof_size_bytes = 2789940, cycle_count = 862136
```

Core SP1 commands should be run on Linux/macOS or WSL2 Ubuntu:

```bash
cd zk_backend/td_mvp/sp1
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
bash run_negative_cases.sh
```

Distinct minibatch benchmark/reproducibility command:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
```

It writes `artifacts/benchmarks/distinct_td_sp1/summary.json`, `benchmark_matrix.csv`, and `summary.md`. The Python-only smoke path is `python3 scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1`. The earlier repeated-transition benchmark remains available as `benchmark_sp1_td_mvp.py`, but it is no longer the main paper-facing minibatch result.

Aggregate benchmark and reproduction notes are in
`artifacts/benchmarks/final_ndss/summary.md` and
`artifacts/benchmarks/final_ndss/reproduction.md`.

RISC Zero remains the main later comparison backend. Circuit-oriented backends such as Noir, Circom, and Halo2 are deferred until the relation is stable.

## Canonical Docs

- `docs/README.md`: documentation index and canonical command map.
- `docs/artifact_schema.md`: artifact schema and witness/public/debug field classification.
- `docs/zk_backend_mvp.md`: smallest backend-ready ZK statement.
- `docs/backend_selection_v0_12.md`: SP1 decision.
- `docs/threat_model.md`: threat model and non-goals.
- `docs/current_benchmark_snapshot.md`: current benchmark snapshot.
- `docs/dev_commands.md`: local developer command notes.

## License

MIT. See [LICENSE](LICENSE).
