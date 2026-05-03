# ZK-Offline-DQN

> **Pre-ZK Verification Prototype for Offline Deep Q-Network Training from Committed Trajectories**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/Framework-PyTorch-EE4C2C.svg)](https://pytorch.org/)

---

## Overview

This repository contains source code for research on combining **Offline Reinforcement Learning** with **verification-oriented proof design** for trustworthy training from committed data.

The current repository is **not yet a full zero-knowledge proof-of-training system**. Instead, it implements a **pre-ZK artifact/verifier prototype** for concrete offline DQN-style statements over committed trajectories.

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
6. **One-step SGD update consistency** — for a fixed committed minibatch, the repository can check gradient recomputation, parameter-delta consistency, and SGD-update consistency for one offline DQN update step.
7. **Short verified training traces** — the repository can chain multiple verified one-step updates into short traces with checkpoint chaining and explicit target-network synchronization semantics.
8. **Deterministic short-trace sampling-rule enforcement** — for the current short-trace benchmark, the exporter and verifier both enforce a declared contiguous deterministic sampling rule with public `batch_size` and `start_offset`.

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
- a **pre-ZK artifact/verifier prototype** for:
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
  - SGD update consistency,
  - target-network invariance,
- a stronger **pre-ZK short-trace prototype** for:
  - multi-step checkpoint chaining,
  - explicit target-network synchronization semantics,
  - deterministic contiguous sampling-rule enforcement,
  - negative rejection under sampling-rule mismatch.
- the B3 short-trace artifact cleanup milestone:
  - persistent `notes` no longer stores local operational paths,
  - the verifier receives Merkle/checkpoint paths from the benchmark/runtime environment,
  - benchmark-only metadata is kept separate from the artifact schema.

This repository should currently be described as:

> **a pre-ZK artifact/verifier prototype for committed-data membership, TD-arithmetic correctness, one-step update consistency, short verified training traces, deterministic short-trace sampling-rule enforcement, and backend-oriented short-trace artifact cleanup**

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

### Stronger One-Step Prototype

The repository also includes a stronger pre-ZK prototype for:

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

### Stronger Short-Trace Prototype

The repository now also includes a stronger pre-ZK prototype for:

> **short verified offline DQN update traces**

For a sequence of committed minibatches, the current short-trace pipeline checks:

- that each step satisfies the one-step update relation,
- checkpoint chaining across steps,
- declared target-network synchronization semantics,
- final checkpoint anchoring,
- deterministic contiguous sampling-rule consistency for the current benchmark setting.

The current short-trace benchmark has been run successfully for:

- **2-step traces**
- **4-step traces**
- **8-step traces**

### Deterministic Sampling-Rule Enforcement

The current short-trace benchmark additionally enforces:

> **deterministic contiguous sampling with public `batch_size` and `start_offset`**

For step index `t`, batch size `k`, and start offset `s`, the expected batch is:

```text
B_t = [s + t*k, s + t*k + 1, ..., s + t*k + (k-1)]
```

This strengthens the statement from:

> “the provided minibatch is valid and the update trace is correct”

to:

> “the provided minibatch is valid, was chosen according to a declared public rule, and the update trace is correct.”

### Negative Sanity Check

The current verifier does not only accept valid artifacts; it also rejects tampered ones.

In particular, starting from a valid short-trace artifact, manually changing the public batch indices so that they no longer match the declared deterministic schedule causes the verifier to reject the artifact even when one-step verification, checkpoint chaining, and target-sync state checks still pass.

This negative sanity check is important because it shows that the verifier independently enforces the declared sampling rule rather than merely trusting the exported artifact structure.

---

## Locked Benchmark Snapshot

The current repository-level benchmark milestone is the locked 8-step short-trace benchmark with deterministic sampling-rule enforcement.

Snapshot refreshed on 2026-05-02 from `artifacts/benchmarks/short_trace_update/summary.json`.

### Run 0
- `start_offset = 0`
- `batch_size = 4`
- `export_time_sec = 21.9907`
- `verify_time_sec = 13.4818`
- `verification_passed = True`

### Run 1
- `start_offset = 32`
- `batch_size = 4`
- `export_time_sec = 23.2580`
- `verify_time_sec = 13.6440`
- `verification_passed = True`

### Run 2
- `start_offset = 0`
- `batch_size = 8`
- `export_time_sec = 22.4650`
- `verify_time_sec = 14.0169`
- `verification_passed = True`

The full locked snapshot is documented in:

```text
docs/current_benchmark_snapshot.md
```

---

## What Is Not Yet Verified

The current repository still does **not** verify:

- that the final published checkpoint came from a full correct training trace from initialization,
- general replay-sampling correctness across a long run,
- seeded pseudorandom replay correctness,
- prioritized replay correctness,
- long-horizon target-network synchronization guarantees,
- model selection / early stopping / best-checkpoint selection,
- recursive proof composition,
- a full end-to-end proof of training,
- a production zero-knowledge backend.

More precisely:

- **already enforced now:** deterministic contiguous sampling for the current short-trace benchmark;
- **not yet enforced generally:** replay-sampling correctness for richer or more realistic sampling rules over a full training run.

---

## Repository Structure

```text
zk_offline_dqn/
├── zk_offline_dqn/                      # Core Python package
│   ├── __init__.py
│   ├── zk_specs.py                      # Fixed-point encoding, TD arithmetic, ZK-friendly constants
│   └── artifact_export_utils.py         # Shared helpers for artifact export / verification
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
│   │   ├── export_short_trace_update_artifact.py
│   │   ├── verify_transition_membership_artifact.py
│   │   ├── verify_td_sample_artifact.py
│   │   ├── verify_minibatch_td_artifact.py
│   │   ├── verify_one_step_update_artifact.py
│   │   └── verify_short_trace_update_artifact.py
│   │
│   ├── experiments/
│   │   ├── benchmark_one_step_update.py
│   │   └── benchmark_short_trace_update.py
│   │
│   └── zk_proofs/
│       ├── build_leaf_hashes.py
│       ├── build_merkle_root.py
│       ├── check_merkle_membership.py
│       └── check_real_transition.py
│
├── docs/
│   ├── artifact_schema.md               # Current artifact field classification and B3 cleanup notes
│   ├── current_benchmark_snapshot.md    # Locked short-trace benchmark milestone
│   └── one_step_field_classification.md # One-step artifact field classification
│
├── paper/                               # LaTeX draft
├── data/                                # Datasets (git-ignored)
├── models/                              # Checkpoints (git-ignored)
├── logs/                                # Training logs (git-ignored)
├── artifacts/                           # Exported artifacts (git-ignored)
├── plots/                               # Plots (git-ignored)
│
├── proof_statement_design.md            # MVP, one-step, and short-trace statement design
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
    --model models/dqn_cartpole_behavior \
    --epsilon 0.10

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

# Behavior Cloning
python scripts/training/train_bc.py \
    --data data/cartpole_dqn_eps010_transitions.pkl
```

### Stage 4: Build committed-data artifacts

```bash
# Build leaf hashes from the dataset
python scripts/zk_proofs/build_leaf_hashes.py

# Build Merkle tree / root
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

### Stage 8: Export and verify short training traces

```bash
python scripts/artifacts_export/export_short_trace_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --trace-batches-json "[[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]]" \
    --lr 0.001 \
    --target-sync-every 2 \
    --start-offset 0 \
    --work-dir artifacts/short_trace_work \
    --out artifacts/short_trace_artifact.json
```

```bash
# Current B3 short-trace artifacts do not store local paths in notes.
# Use the final_checkpoint_path printed by the exporter.
export SHORT_TRACE_ARTIFACT_PATH=artifacts/short_trace_artifact.json
export SHORT_TRACE_MERKLE_PATH=artifacts/cartpole_dqn_eps010_merkle.json
export SHORT_TRACE_INITIAL_CHECKPOINT_PATH=models/offline_dqn_with_target_seed42_best.pt
export SHORT_TRACE_FINAL_CHECKPOINT_PATH=artifacts/short_trace_work/<printed-final-checkpoint>.pt
python scripts/artifacts_export/verify_short_trace_update_artifact.py
```

The benchmark runner performs this wiring automatically: it parses the exporter output, sets the verifier environment variables, and records the final checkpoint path in benchmark metadata rather than inside the artifact.

### Stage 9: Run the locked short-trace benchmark

```bash
python scripts/experiments/benchmark_short_trace_update.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --lr 0.001 \
    --target-sync-every 2
```

This benchmark currently covers:

- 8-step trace, `batch_size = 4`, `start_offset = 0`
- 8-step trace, `batch_size = 4`, `start_offset = 32`
- 8-step trace, `batch_size = 8`, `start_offset = 0`

The benchmark summary includes `final_checkpoint_path` for reproducibility. That field is benchmark metadata only; the short-trace artifact itself keeps `notes` empty after B3 cleanup.

### Stage 10: Negative sanity check for sampling-rule rejection

```bash
# Export a valid 4-step short-trace artifact
python scripts/artifacts_export/export_short_trace_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --trace-batches-json "[[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]]" \
    --lr 0.001 \
    --target-sync-every 2 \
    --start-offset 0 \
    --work-dir artifacts/short_trace_negative_test_work \
    --out artifacts/short_trace_negative_test_valid.json
```

```bash
# Create a tampered copy with incorrect public batch indices
python -c "import json; p='artifacts/short_trace_negative_test_valid.json'; q='artifacts/short_trace_negative_test_tampered.json'; data=json.load(open(p,'r',encoding='utf-8')); data['public']['trace_batch_indices'][1]=[5,6,7,8]; json.dump(data, open(q,'w',encoding='utf-8'), indent=2)"
```

```bash
# Verify the tampered artifact; expected outcome: verification_passed = False
export SHORT_TRACE_ARTIFACT_PATH=artifacts/short_trace_negative_test_tampered.json
export SHORT_TRACE_MERKLE_PATH=artifacts/cartpole_dqn_eps010_merkle.json
export SHORT_TRACE_INITIAL_CHECKPOINT_PATH=models/offline_dqn_with_target_seed42_best.pt
export SHORT_TRACE_FINAL_CHECKPOINT_PATH=artifacts/short_trace_negative_test_work/<printed-final-checkpoint>.pt
python scripts/artifacts_export/verify_short_trace_update_artifact.py
```

### Stage 11: Analyze results

```bash
python scripts/analysis/analyze_offline_log.py \
    --log logs/offline_dqn_cartpole_log_seed42.csv

python scripts/analysis/analyze_cql_log.py \
    --log logs/cql_cartpole_log_seed42.csv
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

The stronger short-trace prototype additionally checks:

- step-by-step checkpoint chaining,
- explicit target-network synchronization behavior,
- deterministic contiguous sampling-rule enforcement with public `sampling_rule_type`, `start_offset`, and `batch_size`,
- final checkpoint consistency across the full short trace.

After B3 cleanup, the short-trace artifact no longer stores operational paths such as the Merkle file path, initial checkpoint path, or final checkpoint path in `notes`. The Python verifier receives those paths through environment variables, while the persistent artifact keeps only the statement data and witness structure.

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

In short, the repository currently contains four connected statement layers:

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

3. **Short verified training trace**
   - chain consecutive one-step statements,
   - enforce checkpoint chaining,
   - enforce target-network synchronization semantics.

4. **Deterministic short-trace sampling-rule enforcement**
   - enforce a declared contiguous deterministic batch schedule,
   - expose `sampling_rule_type`, `start_offset`, and `batch_size` as public trace parameters,
   - reject tampered public trace batches that do not match the declared schedule.

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

The next milestone after the current locked short-trace sampling-rule and B3 cleanup milestones is:

> **one-step schema cleanup plus backend-ready statement design**

The most natural directions are:

1. **Finish artifact schema cleanup**
   - apply the same cleanup discipline to the one-step artifact,
   - separate mandatory public inputs from optional debug fields,
   - separate private witness fields from audit convenience fields,
   - keep benchmark metadata distinct from persistent artifact metadata,
   - reduce statement ambiguity before moving to a proving backend.

2. **Strengthen sampling rules**
   - move beyond deterministic contiguous scheduling,
   - study seeded deterministic replay-style schedules,
   - approach stronger replay-sampling guarantees in a controlled way.

3. **Make the statement more backend-ready**
   - compress or quantize witness data more aggressively,
   - reduce floating-point dependence in update-side checks,
   - move toward circuit-compatible witness representations.

4. **Eventually move to a true proving backend**
   - zkVM or custom circuit/SNARK backend,
   - real proving time / verification time / proof size measurements.

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
