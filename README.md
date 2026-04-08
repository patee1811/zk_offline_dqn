# ZK-Offline-DQN

> **Pre-ZK Verification Prototype for Offline Deep Q-Network Training from Committed Data**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/Framework-PyTorch-EE4C2C.svg)](https://pytorch.org/)

---

## Overview

This repository contains the source code for our research on combining **Offline Reinforcement Learning** with **verification-oriented proof design** for trustworthy training from committed data.

The current repository is **not yet a full zero-knowledge proof-of-training system**. Instead, it implements a **pre-ZK artifact-verifier prototype** for concrete offline DQN-style statements over committed data.

The core idea is:

1. collect a fixed offline dataset,
2. commit that dataset using a **Merkle tree**,
3. train offline value-learning models on the fixed dataset,
4. export **ZK-friendly artifacts** that verify key RL-specific computations.

At the current stage, the repository can verify:

1. **Dataset membership** — a sampled transition genuinely belongs to the committed dataset.
2. **Bellman target correctness** — the Double-DQN-style Bellman backup arithmetic is computed correctly.
3. **TD loss correctness** — the per-sample **SmoothL1** temporal-difference loss is computed correctly.
4. **Batch-level loss integrity** — the reported minibatch average loss matches the actual computation.
5. **Checkpoint anchoring** — the audited model checkpoint is publicly tied by **SHA-256**.
6. **One-step SGD update consistency** — for a fixed committed minibatch, the repository can also check gradient recomputation, parameter-delta consistency, and SGD-update consistency for one offline DQN update step.

All arithmetic used for TD-artifact verification is represented in **fixed-point integer form** to make verification deterministic and compatible with future proof-system backends.

---

## Current Status

The project is beyond the proposal stage and currently includes:

- an offline RL experimental pipeline on **CartPole-v1**,
- baselines for:
  - offline Double DQN,
  - Conservative Q-Learning (CQL-lite),
  - Behavior Cloning (BC),
- committed-data artifacts based on **Merkle-style membership proofs**,
- a **pre-ZK artifact-verifier prototype** for:
  - committed transition membership,
  - Double-DQN-style Bellman target correctness,
  - SmoothL1 TD loss correctness,
  - minibatch-average TD loss correctness,
  - checkpoint anchoring via SHA-256,
- a stronger **pre-ZK one-step update prototype** for:
  - one offline DQN SGD update step from a committed minibatch,
  - pre-update and post-update checkpoint anchoring,
  - gradient recomputation consistency,
  - parameter-delta consistency,
  - SGD update consistency.

This repository should currently be described as:

> **a pre-ZK artifact-verification prototype for committed-data membership, TD-arithmetic correctness, and one-step update consistency**

—not yet as a full proof-of-training system.

---

## What Is Verified Right Now

### Verified MVP

The current verified MVP is:

> verify committed-sample membership + Double DQN Bellman target + SmoothL1 TD loss + batch-average loss + checkpoint hash anchoring.

Concretely, the current artifact pipeline verifies:

- transition membership against a public Merkle root,
- Double DQN target semantics:
  - next action selected by the **online network**,
  - target value evaluated by the **target network**,
- fixed-point Bellman target arithmetic,
- fixed-point SmoothL1 TD loss arithmetic,
- minibatch average loss,
- public checkpoint identity through `checkpoint_sha256`.

### Stronger Current Prototype Milestone

The repository now also includes a stronger pre-ZK prototype for:

> **one offline DQN SGD update step from a committed minibatch**

For a fixed minibatch drawn from the committed dataset, the current one-step artifact/verifier pipeline checks:

- transition membership via Merkle proofs,
- Double-DQN Bellman target correctness,
- SmoothL1 TD loss correctness,
- batch-average loss consistency,
- consistency of the pre-update checkpoint hash,
- consistency of the post-update checkpoint hash,
- consistency of the pre-update and post-update online-network states,
- invariance of the target network during the one-step statement,
- gradient recomputation consistency,
- parameter-delta consistency,
- SGD update consistency `w' = w - lr * g`.

This stronger milestone is still a **Python pre-ZK artifact/verifier prototype**, not yet a true zero-knowledge proving backend.

### Not Yet Verified

The current repository does **not yet** verify:

- that the checkpoint itself was produced by a full correct training trace,
- optimizer updates across many steps,
- target-network synchronization across all training steps,
- sampling-rule correctness across the full training trace,
- model selection / early stopping / best-checkpoint selection,
- a full end-to-end proof of training,
- recursive proof composition or a production ZK backend.

---

## Repository Structure

```text
zk_offline_dqn/
├── zk_offline_dqn/                      # Core Python package
│   ├── __init__.py
│   ├── zk_specs.py                      # Fixed-point encoding, TD arithmetic, ZK-friendly constants
│   └── artifact_export_utils.py         # Shared helpers for artifact export / one-step verification
│
├── scripts/
│   ├── training/                        # Model training scripts
│   │   ├── train_cartpole_dqn.py
│   │   ├── train_offline_dqn.py
│   │   ├── train_cql.py
│   │   └── train_bc.py
│   │
│   ├── data_gen/                        # Dataset generation & preprocessing
│   │   ├── generate_cartpole_dataset.py
│   │   ├── generate_cartpole_dataset_from_dqn.py
│   │   ├── generate_dataset_from_dqn_until_transitions.py
│   │   ├── generate_random_dataset_until_transitions.py
│   │   ├── flatten_episode_dataset.py
│   │   └── mix_transition_datasets.py
│   │
│   ├── evaluation/
│   │   ├── evaluate_checkpoint.py
│   │   ├── evaluate_bc_checkpoint.py
│   │   ├── test_trained_dqn.py
│   │   └── smoke_test_env.py
│   │
│   ├── analysis/
│   │   ├── analyze_offline_log.py
│   │   ├── analyze_cql_log.py
│   │   ├── analyze_transition_dataset.py
│   │   ├── inspect_dataset.py
│   │   ├── inspect_transition_dataset.py
│   │   └── inspect_all_leaves.py
│   │
│   ├── artifacts_export/
│   │   ├── export_transition_membership_artifact.py
│   │   ├── export_td_sample_artifact.py
│   │   ├── export_minibatch_td_artifact.py
│   │   ├── export_td_sample_artifact_from_dataset.py
│   │   ├── export_minibatch_td_artifact_from_dataset.py
│   │   ├── export_one_step_update_artifact.py
│   │   ├── verify_transition_membership_artifact.py
│   │   ├── verify_td_sample_artifact.py
│   │   ├── verify_minibatch_td_artifact.py
│   │   └── verify_one_step_update_artifact.py
│   │
│   └── zk_proofs/
│       ├── build_leaf_hashes.py
│       ├── build_merkle_root.py
│       ├── check_merkle_membership.py
│       └── check_real_transition.py
│
├── paper/                               # LaTeX draft
├── data/                                # Datasets (git-ignored)
├── models/                              # Checkpoints (git-ignored)
├── logs/                                # Training logs (git-ignored)
├── artifacts/                           # Exported artifacts (git-ignored)
├── plots/                               # Plots (git-ignored)
│
├── proof_statement_design.md            # MVP and stronger one-step statement design
├── setup.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/patee1811/zk_offline_dqn.git
cd zk_offline_dqn

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the project package in editable mode
pip install -e .
```

---

## Usage

All commands should be run from the **project root directory**.

### Stage 1: Train a behavior policy

```bash
python scripts/training/train_cartpole_dqn.py
```

### Stage 2: Generate an offline dataset

```bash
# Generate ε-greedy dataset from the trained DQN
python scripts/data_gen/generate_cartpole_dataset_from_dqn.py \
    --model models/dqn_cartpole_behavior --epsilon 0.10

# Flatten episodes into a transition-level dataset
python scripts/data_gen/flatten_episode_dataset.py \
    --infile data/cartpole_dqn_eps010_episodes.pkl \
    --out data/cartpole_dqn_eps010_transitions.pkl
```

### Stage 3: Train offline baselines

```bash
# Offline DQN
python scripts/training/train_offline_dqn.py \
    --data data/cartpole_dqn_eps010_transitions.pkl

# Conservative Q-Learning (CQL-lite)
python scripts/training/train_cql.py \
    --data data/cartpole_dqn_eps010_transitions.pkl

# Behavioral Cloning
python scripts/training/train_bc.py \
    --data data/cartpole_dqn_eps010_transitions.pkl
```

### Stage 4: Build committed-data artifacts

```bash
# Build leaf hashes from the dataset
python scripts/zk_proofs/build_leaf_hashes.py

# Build Merkle tree
python scripts/zk_proofs/build_merkle_root.py

# Export and verify transition membership artifact
python scripts/artifacts_export/export_transition_membership_artifact.py
python scripts/artifacts_export/verify_transition_membership_artifact.py
```

### Stage 5: Verify TD arithmetic artifacts

```bash
# Single-sample TD artifact
python scripts/artifacts_export/export_td_sample_artifact.py
python scripts/artifacts_export/verify_td_sample_artifact.py

# Minibatch TD artifact
python scripts/artifacts_export/export_minibatch_td_artifact.py
python scripts/artifacts_export/verify_minibatch_td_artifact.py
```

### Stage 6: Export artifacts directly from dataset + Merkle + checkpoint

```bash
# Single-sample artifact built directly from real dataset + real Merkle tree + real checkpoint
python scripts/artifacts_export/export_td_sample_artifact_from_dataset.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --index 0 \
    --out artifacts/td_sample_from_dataset.json

python scripts/artifacts_export/verify_td_sample_artifact.py
```

```bash
# Minibatch artifact built directly from real dataset + real Merkle tree + real checkpoint
python scripts/artifacts_export/export_minibatch_td_artifact_from_dataset.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --indices 0,1,2,3 \
    --out artifacts/minibatch_td_from_dataset.json

python scripts/artifacts_export/verify_minibatch_td_artifact.py
```

### Stage 7: Export and verify one offline DQN SGD update step

```bash
python scripts/artifacts_export/export_one_step_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --indices 0,1,2,3 \
    --lr 0.001 \
    --post-checkpoint-out models/offline_dqn_one_step_sgd.pt \
    --out artifacts/one_step_update_artifact.json
```

```bash
python scripts/artifacts_export/verify_one_step_update_artifact.py
```

The current one-step verifier checks:

- committed-minibatch membership,
- Double-DQN target correctness,
- SmoothL1 TD loss correctness,
- batch-loss consistency,
- pre/post checkpoint anchoring,
- target-network invariance,
- gradient recomputation consistency,
- delta-tensor consistency,
- SGD update consistency.

### Stage 8: Analyze results

```bash
python scripts/analysis/analyze_offline_log.py --log logs/offline_dqn_cartpole_log_seed42.csv
python scripts/analysis/analyze_cql_log.py --log logs/cql_cartpole_log_seed42.csv
```

---

## Verification Semantics

The current TD-artifact pipeline uses:

- **committed transition membership** through Merkle proofs,
- **Double DQN target semantics**:
  - `argmax` action selected from the online network on `next_obs`,
  - target value taken from the target network at that selected action,
- **SmoothL1 loss** in fixed-point arithmetic,
- **checkpoint anchoring** using `checkpoint_sha256`.

The stronger one-step update prototype additionally checks:

- consistency between the committed minibatch and the recomputed training loss,
- consistency between the recomputed gradients and stored gradient tensors,
- consistency between parameter deltas and the actual pre/post online-network states,
- consistency of the SGD rule `w' = w - lr * g`,
- invariance of the target network during the one-step statement.

This makes the current repository substantially closer to real offline Double DQN training semantics than a purely symbolic arithmetic demo.

---

## ZK-Friendly Fixed-Point Specifications

The fixed-point arithmetic used in the project is defined in [`zk_offline_dqn/zk_specs.py`](zk_offline_dqn/zk_specs.py).

| Parameter | Value | Description |
|---|---:|---|
| `FP_SCALE` | 1000 | Fixed-point scaling factor |
| `OBS_DIM` | 4 | CartPole observation dimension |
| `ACTION_DIM` | 2 | CartPole action dimension |
| `GAMMA_FP` | 990 | Discount factor `γ = 0.99` in fixed-point |
| `LOSS_TYPE` | `smooth_l1` | SmoothL1 TD loss |
| `SMOOTH_L1_BETA_FP` | 1000 | SmoothL1 beta `= 1.0` in fixed-point |

---

## Proof Statement Design

The current proof statements are documented in:

```text
proof_statement_design.md
```

In short, the repository currently contains two levels of statement design:

1. **MVP TD-arithmetic statement**
   - verify committed transition membership,
   - verify Double-DQN Bellman target correctness,
   - verify SmoothL1 TD loss correctness,
   - verify minibatch-average loss correctness,
   - anchor the checkpoint publicly by SHA-256.

2. **Stronger one-step update statement**
   - verify one offline DQN SGD update step from a committed minibatch,
   - check pre/post checkpoint consistency,
   - check gradient recomputation consistency,
   - check parameter-delta consistency,
   - check SGD update consistency.

The current implementation is still **pre-ZK**: it formalizes and verifies the statement structure in Python, but does not yet provide a true zero-knowledge proving backend.

---

## Data

Datasets are **not included** in this repository because of their size. To reproduce the experiments, run the dataset generation scripts above.

Typical generated files include:

- episode-level datasets, e.g. `cartpole_dqn_eps010_episodes.pkl`
- transition-level datasets, e.g. `cartpole_dqn_eps010_transitions.pkl`
- dataset summary JSON files generated alongside them

---

## Recommended Next Technical Milestone

The next milestone after the current stronger pre-ZK prototype is:

> **multi-step verified offline DQN update traces or a more circuit-friendly encoding of the current one-step update statement**

Two natural directions are:

1. **Extend from one verified step to K verified steps**
   - chain pre/post checkpoint hashes across steps,
   - keep target-network synchronization explicit,
   - study proof/verification overhead growth.

2. **Make the one-step statement more ZK-friendly**
   - compress or quantize gradient/delta representations more aggressively,
   - reduce floating-point dependence,
   - move toward circuit-compatible witness representations.

---

## Citation

If you find this work useful, please cite:

```bibtex
@misc{zk_offline_dqn_2026,
  title        = {Zero-Knowledge Verifiable Offline DQN Training from Committed Trajectories},
  author       = {Ngoc Duy},
  year         = {2026},
  howpublished = {\url{https://github.com/patee1811/zk_offline_dqn}}
}
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).