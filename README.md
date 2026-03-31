# ZK-Offline-DQN

> **Verifiable Offline Deep Q-Network Training with Zero-Knowledge Proofs**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/Framework-PyTorch-EE4C2C.svg)](https://pytorch.org/)

---

## Overview

This repository contains the source code for our research on combining **Offline Reinforcement Learning** (Offline DQN, Conservative Q-Learning) with **Zero-Knowledge Proofs** to enable verifiable and trustworthy offline RL training.

The core idea is to cryptographically commit an offline dataset using a **Merkle tree**, then produce **ZK-friendly artifacts** that can prove:

1. **Dataset membership** — a training transition genuinely belongs to the committed dataset.
2. **TD-target correctness** — the Bellman backup arithmetic was computed honestly.
3. **Batch-level loss integrity** — the reported minibatch loss matches the actual computation.

All arithmetic is performed in **fixed-point integer representation** to ensure deterministic, circuit-compatible verification.

## Repository Structure

```
zk_offline_dqn/
├── zk_offline_dqn/              # Core Python package
│   ├── __init__.py
│   └── zk_specs.py              # ZK constants, fixed-point encoding, TD arithmetic
│
├── scripts/                     # Executable scripts (organized by pipeline stage)
│   ├── training/                # Model training scripts
│   │   ├── train_cartpole_dqn.py          # Train behavior DQN policy (online)
│   │   ├── train_offline_dqn.py           # Offline DQN training from static dataset
│   │   ├── train_cql.py                   # Conservative Q-Learning (CQL) training
│   │   └── train_bc.py                    # Behavioral Cloning baseline
│   │
│   ├── data_gen/                # Dataset generation & preprocessing
│   │   ├── generate_cartpole_dataset.py               # Random policy dataset
│   │   ├── generate_cartpole_dataset_from_dqn.py      # ε-greedy DQN dataset
│   │   ├── generate_dataset_from_dqn_until_transitions.py
│   │   ├── generate_random_dataset_until_transitions.py
│   │   ├── flatten_episode_dataset.py                 # Episodes → transitions
│   │   └── mix_transition_datasets.py                 # Mix datasets by ratio
│   │
│   ├── evaluation/              # Model evaluation & testing
│   │   ├── evaluate_checkpoint.py         # Evaluate DQN/CQL checkpoint
│   │   ├── evaluate_bc_checkpoint.py      # Evaluate BC checkpoint
│   │   ├── test_trained_dqn.py            # Quick test of trained DQN
│   │   └── smoke_test_env.py              # Environment sanity check
│   │
│   ├── analysis/                # Data analysis & visualization
│   │   ├── analyze_offline_log.py         # Plot Offline DQN training curves
│   │   ├── analyze_cql_log.py             # Plot CQL training curves
│   │   ├── analyze_transition_dataset.py  # Dataset statistics
│   │   ├── inspect_dataset.py             # Quick dataset inspection
│   │   ├── inspect_transition_dataset.py  # Quick transition inspection
│   │   └── inspect_all_leaves.py          # Serialize & inspect all leaves
│   │
│   ├── artifacts_export/        # ZK artifact generation & verification
│   │   ├── export_transition_membership_artifact.py   # Membership proof artifact
│   │   ├── export_td_sample_artifact.py               # Single-sample TD artifact
│   │   ├── export_minibatch_td_artifact.py            # Minibatch TD artifact
│   │   ├── verify_transition_membership_artifact.py   # Verify membership
│   │   ├── verify_td_sample_artifact.py               # Verify single TD
│   │   └── verify_minibatch_td_artifact.py            # Verify minibatch TD
│   │
│   └── zk_proofs/               # Merkle tree construction & verification
│       ├── build_leaf_hashes.py           # Hash all transitions into leaves
│       ├── build_merkle_root.py           # Build Merkle tree from leaf hashes
│       ├── check_merkle_membership.py     # Verify Merkle membership proof
│       └── check_real_transition.py       # Inspect a real transition's leaf
│
├── paper/                       # LaTeX source for the research paper
├── data/                        # Datasets (git-ignored, see Data section)
├── models/                      # Trained model checkpoints (git-ignored)
├── logs/                        # Training logs (git-ignored)
├── artifacts/                   # ZK proof artifacts (git-ignored)
├── plots/                       # Generated plots (git-ignored)
│
├── setup.py                     # Package installation
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
└── README.md
```

## Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/zk_offline_dqn.git
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

## Usage

The project follows a multi-stage pipeline. All scripts should be run from the **project root directory**.

### Stage 1: Train a Behavior Policy (Online DQN)

```bash
python scripts/training/train_cartpole_dqn.py
```

### Stage 2: Generate an Offline Dataset

```bash
# Generate ε-greedy dataset from the trained DQN
python scripts/data_gen/generate_cartpole_dataset_from_dqn.py \
    --model models/dqn_cartpole_behavior --epsilon 0.10

# Flatten episodes into a transition-level dataset
python scripts/data_gen/flatten_episode_dataset.py \
    --infile data/cartpole_dqn_eps010_episodes.pkl \
    --out data/cartpole_dqn_eps010_transitions.pkl
```

### Stage 3: Train Offline RL Agents

```bash
# Offline DQN
python scripts/training/train_offline_dqn.py \
    --data data/cartpole_dqn_eps010_transitions.pkl

# Conservative Q-Learning (CQL)
python scripts/training/train_cql.py \
    --data data/cartpole_dqn_eps010_transitions.pkl

# Behavioral Cloning (baseline)
python scripts/training/train_bc.py \
    --data data/cartpole_dqn_eps010_transitions.pkl
```

### Stage 4: Build ZK Artifacts

```bash
# Build leaf hashes from the dataset
python scripts/zk_proofs/build_leaf_hashes.py

# Build Merkle tree
python scripts/zk_proofs/build_merkle_root.py

# Export and verify membership proof
python scripts/artifacts_export/export_transition_membership_artifact.py
python scripts/artifacts_export/verify_transition_membership_artifact.py

# Export and verify TD arithmetic proof
python scripts/artifacts_export/export_td_sample_artifact.py
python scripts/artifacts_export/verify_td_sample_artifact.py

# Export and verify minibatch TD proof
python scripts/artifacts_export/export_minibatch_td_artifact.py
python scripts/artifacts_export/verify_minibatch_td_artifact.py
```

### Stage 5: Analyze Results

```bash
python scripts/analysis/analyze_offline_log.py --log logs/offline_dqn_cartpole_log_seed42.csv
python scripts/analysis/analyze_cql_log.py --log logs/cql_cartpole_log_seed42.csv
```

## ZK Specifications

The fixed-point arithmetic used throughout the project is defined in [`zk_offline_dqn/zk_specs.py`](zk_offline_dqn/zk_specs.py):

| Parameter     | Value | Description                          |
|---------------|-------|--------------------------------------|
| `FP_SCALE`    | 1000  | Fixed-point scaling factor           |
| `OBS_DIM`     | 4     | CartPole observation dimensionality  |
| `ACTION_DIM`  | 2     | CartPole action space size           |
| `GAMMA_FP`    | 990   | Discount factor γ=0.99 in fixed-point|
| `LOSS_TYPE`   | `mse` | MSE loss for circuit compatibility   |

## Data

Datasets are **not included** in this repository due to their size. To reproduce the experiments, run the data generation scripts in Stage 1–2 above. Summary JSON files (`.summary.json`) are generated alongside each dataset for reference.

## Citation

If you find this work useful, please cite:

```bibtex
@misc{zk_offline_dqn_2026,
    title   = {Verifiable Offline Deep Q-Network Training with Zero-Knowledge Proofs},
    author  = {Ngoc Duy},
    year    = {2026},
    url     = {https://github.com/<your-username>/zk_offline_dqn}
}
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
