# ZK-Offline-DQN

> **Pre-ZK Verification Prototype for Offline Deep Q-Network Training from Committed Trajectories**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/Framework-PyTorch-EE4C2C.svg)](https://pytorch.org/)
[![Regression](https://github.com/patee1811/zk_offline_dqn/actions/workflows/regression.yml/badge.svg?branch=master)](https://github.com/patee1811/zk_offline_dqn/actions/workflows/regression.yml)

---

## Overview

This repository contains research code for combining **offline reinforcement learning** with **verification-oriented proof design** for trustworthy training from committed data.

The repository is **not yet a full zero-knowledge proof-of-training system**. It currently implements a **pre-ZK artifact/verifier prototype** for concrete offline DQN-style statements over committed trajectories.

The core idea is:

1. collect a fixed offline trajectory/transition dataset;
2. commit the dataset using a **Merkle tree**;
3. train offline value-learning models on the fixed dataset;
4. export verification-friendly artifacts;
5. verify RL-specific computations such as membership, Bellman targets, TD losses, update consistency, and short update traces.

At the current stage, the repository verifies:

1. **Dataset membership** — a sampled transition genuinely belongs to the committed dataset.
2. **Bellman target correctness** — the Double-DQN-style Bellman backup is computed correctly.
3. **TD loss correctness** — the per-sample **SmoothL1** temporal-difference loss is computed correctly.
4. **Batch-level loss integrity** — the reported minibatch average loss matches the recomputed value.
5. **Checkpoint and model-state anchoring** — checkpoint files are tied to public file SHA-256 hashes, and online/target network state dictionaries are tied to canonical tensor-content SHA-256 commitments.
6. **Forward TD consistency** — TD witness values are checked against actual neural-network forward semantics from the checkpoint.
7. **One-step SGD update consistency** — for a fixed committed minibatch, the verifier checks TD forward semantics, gradient recomputation, parameter-delta consistency, and the SGD update rule.
8. **One-step Double-DQN action/value selection** — one-step TD witnesses include `next_action_online`, and the verifier recomputes both `argmax_a Q_online(s')` and `Q_target(s')[next_action_online]` from the pre-update checkpoint.
9. **Short verified training traces** — multiple verified one-step updates can be chained into short traces with checkpoint chaining and explicit target-network synchronization semantics.
10. **Short-trace boundary anchoring** — initial/final trace checkpoints are anchored by both file SHA-256 hashes and canonical model-state commitments.
11. **Deterministic short-trace sampling-rule enforcement** — the short-trace verifier supports both contiguous deterministic sampling and seeded-permutation sampling with public replay metadata.
12. **Artifact schema-version checks** — main artifacts include explicit `schema_version` fields, and verifiers reject stale or incompatible artifacts before reading statement fields.
13. **Negative verification tests** — the repository includes tamper tests showing that invalid artifacts are rejected.
14. **Regression CI** — GitHub Actions runs the full verification and negative-test suite on pull requests, master pushes, and version tags.

All TD-artifact arithmetic is represented in **fixed-point integer form** to make verification deterministic and more compatible with future proof-system backends.

---

## Current Status

The project is beyond the proposal stage and currently includes:

- an offline RL experimental pipeline on **CartPole-v1**;
- baselines for:
  - offline Double DQN;
  - Conservative Q-Learning, implemented as CQL-lite;
  - Behavior Cloning;
- committed-data artifacts based on **Merkle-style membership proofs**;
- artifact schema-version checks for stale-artifact rejection;
- canonical model-state commitments based on sorted tensor-content SHA-256 hashes;
- a **pre-ZK TD artifact/verifier prototype** for:
  - committed transition membership;
  - Double-DQN-style Bellman target correctness;
  - SmoothL1 TD loss correctness;
  - minibatch-average TD loss correctness;
  - checkpoint anchoring through SHA-256;
  - canonical online/target state-dict commitment checking;
  - forward consistency between TD witness values and checkpoint networks;
- a stronger **pre-ZK one-step update prototype** for:
  - one offline DQN SGD update step from a committed minibatch;
  - pre-update and post-update checkpoint anchoring;
  - canonical pre/post online-network state-dict commitment checking;
  - canonical pre/post target-network state-dict commitment checking;
  - one-step TD witness checking for `next_action_online`;
  - one-step checking of `argmax_a Q_online(s')`;
  - one-step checking of `Q_target(s')[next_action_online]`;
  - gradient recomputation consistency;
  - parameter-delta consistency;
  - SGD update consistency;
  - target-network invariance;
- a stronger **pre-ZK short-trace prototype** for:
  - multi-step checkpoint chaining;
  - nested one-step verifier calls;
  - initial/final trace-boundary checkpoint anchoring;
  - initial/final trace-boundary canonical model-state commitment checking;
  - explicit target-network synchronization semantics;
  - deterministic contiguous sampling-rule enforcement;
  - seeded-permutation sampling-rule enforcement;
  - rejection under sampling-rule mismatch;
- negative verification tests for:
  - tampered TD loss;
  - tampered reward;
  - tampered checkpoint hash;
  - tampered online state-dict commitment;
  - tampered leaf hash;
  - tampered Merkle path;
  - tampered one-step next-action witness;
  - tampered one-step target value witness;
  - tampered one-step loss witness;
  - tampered one-step gradient tensor;
  - tampered one-step delta tensor;
  - tampered one-step learning rate;
  - tampered one-step batch indices;
  - tampered contiguous trace batches;
  - tampered seeded trace batches;
  - tampered sampling seed;
  - tampered dataset size;
  - tampered final checkpoint hash;
  - tampered final online state-dict commitment;
- GitHub Actions regression CI for:
  - Python compile checks;
  - artifact verifier checks;
  - forward TD consistency;
  - one-step verification;
  - short-trace verification;
  - minibatch, one-step, and short-trace negative tests;
  - regression summary report upload.

This repository should currently be described as:

> **a pre-ZK artifact/verifier prototype for committed-data membership, TD-arithmetic correctness, canonical model-state anchoring, forward TD consistency, one-step update consistency, one-step Double-DQN action/value-selection checking, short verified training traces, trace-boundary commitment checking, deterministic short-trace sampling-rule enforcement, artifact schema-version checks, negative tamper tests, and regression CI**

It should **not** yet be described as a full zero-knowledge proof-of-training system.

---

## What Is Verified Right Now

### 1. Verified TD MVP

The current verified MVP is:

> verify committed-sample membership + Double DQN Bellman target + SmoothL1 TD loss + batch-average loss + checkpoint/model-state anchoring.

Concretely, the TD artifact pipeline verifies:

- transition membership against a public Merkle root;
- Double DQN target semantics:
  - next action selected by the **online network**;
  - target value evaluated by the **target network**;
- fixed-point Bellman target arithmetic;
- fixed-point SmoothL1 TD loss arithmetic;
- minibatch average loss;
- public checkpoint identity through `checkpoint_sha256`;
- canonical online/target model-state identity through:
  - `online_state_dict_sha256`;
  - `target_state_dict_sha256`;
- artifact schema compatibility through `schema_version`.

---

### 2. Forward TD Consistency

The repository includes an additional verifier:

```text
scripts/artifacts_export/verify_forward_td_consistency.py
```

This verifier checks that exported TD witness values are not merely arbitrary declared numbers. For every item in a minibatch TD artifact, it recomputes:

```text
Q_online(s)[a]
argmax_a Q_online(s')
Q_target(s')[argmax_a Q_online(s')]
```

from the checkpoint and checks that these values match the artifact's TD witness fields:

```text
q_online_fp
next_action_online
q_target_max_fp
```

This makes the TD artifact verification stronger because it connects the TD arithmetic to the actual checkpoint forward-pass semantics.

---

### 3. One-Step SGD Update Prototype

The repository includes a stronger pre-ZK prototype for:

> **one offline DQN SGD update step from a committed minibatch**

For a fixed minibatch drawn from the committed dataset, the one-step artifact/verifier checks:

- transition membership via Merkle proofs;
- Double-DQN Bellman target correctness;
- SmoothL1 TD loss correctness;
- batch-average loss consistency;
- consistency of the pre-update checkpoint hash;
- consistency of the post-update checkpoint hash;
- consistency of canonical pre/post online-network state-dict commitments;
- consistency of canonical pre/post target-network state-dict commitments;
- consistency of the pre-update and post-update online-network states;
- one-step TD witness consistency for:
  - `next_action_online`;
  - `q_target_max_fp`;
- recomputation of:

```text
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
```

from the pre-update checkpoint;
- invariance of the target network during the one-step statement;
- gradient recomputation consistency;
- parameter-delta consistency;
- SGD update consistency:

```text
w' = w - lr * g
```

The one-step artifact no longer stores local runtime paths in `notes`. Checkpoint paths are provided to the verifier as runtime inputs through environment variables or default local benchmark paths:

```text
ONE_STEP_ARTIFACT_PATH
ONE_STEP_MERKLE_PATH
ONE_STEP_CHECKPOINT_PATH
ONE_STEP_POST_CHECKPOINT_PATH
```

This keeps the persistent artifact contract separate from local filesystem execution details.

Expected one-step verifier output includes:

```text
next_action_match=True
q_target_max_match=True
one_step_canonical_commitments_ok = True
verification_passed = True
```

Important limitation:

> The one-step update verifier currently checks a simplified **SGD** update statement. The main offline DQN baseline trainer may use Adam and additional training-loop details. Therefore, the one-step verifier should be described as a simplified backend-oriented update statement, not as a full proof of the original baseline trainer.

---

### 4. Short Verified Training Traces

The repository also includes a stronger pre-ZK prototype for:

> **short verified offline DQN update traces**

For a sequence of committed minibatches, the short-trace pipeline checks:

- that each step satisfies the one-step update relation;
- checkpoint chaining across steps;
- nested one-step verification;
- declared target-network synchronization semantics;
- initial/final checkpoint anchoring;
- initial/final canonical model-state commitment checking;
- deterministic contiguous sampling-rule consistency;
- seeded-permutation sampling-rule consistency.

The current short-trace benchmark has been run successfully for:

- **2-step traces**
- **4-step traces**
- **8-step traces**

Because the short-trace verifier calls the one-step verifier internally, strengthening the one-step verifier also strengthens each nested update relation in the short trace.

---

### 5. Deterministic Sampling-Rule Enforcement

The current short-trace verifier supports two deterministic sampling rules.

#### Contiguous deterministic sampling

```text
sampling_rule_type = contiguous_deterministic
```

For step index `t`, batch size `k`, and start offset `s`, the expected batch is:

```text
B_t = [s + t*k, s + t*k + 1, ..., s + t*k + (k-1)]
```

#### Seeded permutation sampling

```text
sampling_rule_type = seeded_permutation
```

For seeded permutation sampling, the public sampling metadata includes:

```text
sampling_seed
dataset_size
batch_size
num_steps
```

The verifier reconstructs the same pseudorandom permutation from `sampling_seed`, slices it into minibatches, and checks that:

```text
trace_batch_indices == expected_batches_from_seed
```

This strengthens the statement from:

> “the provided minibatch is valid and the update trace is correct”

to:

> “the provided minibatch is valid, was chosen according to a declared reproducible sampling rule, and the update trace is correct.”

---

### 6. Negative Verification Tests

The verifier does not only accept valid artifacts. It also rejects tampered artifacts.

The repository includes a minibatch TD negative-test runner:

```text
scripts/experiments/run_negative_verification_tests.py
```

It starts from a valid minibatch TD artifact and checks that the verifier accepts the valid artifact while rejecting tampered variants.

| Case | Expected Result | Reason |
|---|---:|---|
| `valid_control` | accept | unchanged valid minibatch TD artifact |
| `tamper_loss_fp` | reject | recomputed SmoothL1 TD loss no longer matches the witness |
| `tamper_reward` | reject | Bellman target and TD loss no longer match the transition |
| `tamper_checkpoint_sha256` | reject | public checkpoint hash no longer matches the checkpoint file |
| `tamper_online_state_dict_sha256` | reject | public online-network state-dict commitment no longer matches the canonical checkpoint tensor contents |
| `tamper_leaf_hash` | reject | serialized transition leaf no longer matches the claimed leaf hash |
| `tamper_merkle_path` | reject | Merkle membership proof no longer reconstructs the public dataset root |

The repository also includes a one-step negative-test runner:

```text
scripts/experiments/run_one_step_negative_tests.py
```

It checks that the verifier accepts a valid one-step artifact and rejects tampered variants.

| Case | Expected Result | Reason |
|---|---:|---|
| `valid_one_step` | accept | unchanged valid one-step update artifact |
| `tamper_next_action_online` | reject | claimed Double-DQN online argmax action no longer matches the pre-update online network |
| `tamper_q_target_max_fp` | reject | claimed target-network value no longer matches `Q_target(s')[next_action_online]` |
| `tamper_loss_fp` | reject | per-item SmoothL1 TD loss no longer matches the recomputed value |
| `tamper_gradient_tensor` | reject | claimed gradient tensor no longer matches recomputed gradients |
| `tamper_delta_tensor` | reject | claimed parameter delta no longer matches the pre/post online-network difference |
| `tamper_post_checkpoint_sha256` | reject | public post-update checkpoint hash no longer matches the post checkpoint file |
| `tamper_post_online_state_dict_sha256` | reject | public post-update online state-dict commitment no longer matches canonical checkpoint tensor contents |
| `tamper_learning_rate_fp` | reject | public learning-rate field no longer matches the expected update relation |
| `tamper_batch_indices` | reject | public minibatch indices no longer match the embedded one-step item indices |

The repository also includes a short-trace negative-test runner:

```text
scripts/experiments/run_short_trace_negative_tests.py
```

It checks both valid and tampered short-trace artifacts.

| Case | Expected Result | Reason |
|---|---:|---|
| `valid_contiguous` | accept | unchanged valid contiguous short-trace artifact |
| `valid_seeded` | accept | unchanged valid seeded-permutation short-trace artifact |
| `tamper_contiguous_public_batch` | reject | public contiguous trace batch no longer matches the declared contiguous rule |
| `tamper_seeded_public_batch` | reject | public seeded trace batch no longer matches the seeded permutation |
| `tamper_sampling_seed` | reject | public seed no longer reconstructs the declared trace batches |
| `tamper_dataset_size` | reject | public dataset size no longer reconstructs the declared seeded batches |
| `tamper_final_checkpoint_sha256` | reject | public final checkpoint file hash no longer matches the final checkpoint |
| `tamper_final_online_state_dict_sha256` | reject | final online-network state-dict commitment no longer matches the final checkpoint tensor contents |

These tests are important because they show that the verifier rejects:

- arithmetic tampering;
- one-step TD/update witness tampering;
- checkpoint/model-state anchoring tampering;
- committed-data membership tampering;
- short-trace sampling-rule tampering;
- short-trace boundary-commitment tampering.

---

## Regression and CI

This repository includes a GitHub Actions regression workflow:

```text
.github/workflows/regression.yml
```

The workflow runs on:

```text
pull_request -> master
push -> master
push -> v* tags
```

The workflow calls the full regression runner:

```bash
python scripts/experiments/run_full_regression.py
```

The full regression runner performs 9 checks:

1. Python compile check;
2. minibatch TD artifact verification;
3. forward TD consistency verification;
4. one-step update artifact verification;
5. short-trace contiguous verification;
6. short-trace seeded verification;
7. one-step negative tests;
8. short-trace negative tests;
9. minibatch TD negative tests.

Expected final output:

```text
all_regression_passed = True
```

The runner writes summary reports to:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
```

It also writes per-check stdout/stderr logs to:

```text
artifacts/full_regression/*.stdout.txt
artifacts/full_regression/*.stderr.txt
```

In GitHub Actions, these files are uploaded as workflow artifacts under:

```text
regression-reports
```

To run the same regression locally:

```powershell
$env:PYTHONPATH="."

python scripts/experiments/run_full_regression.py
```

Expected local output includes:

```text
num_checks = 9
all_regression_passed = True
summary_json_path = artifacts/regression_summary.json
summary_md_path = artifacts/regression_summary.md
```

The current CI uses committed regression fixtures under:

```text
data/
models/
artifacts/
```

These fixtures are intentionally small enough for CI regression and are separate from larger experimental datasets or long-run benchmark outputs.

---

## Artifact Schema Versions

Newly exported artifacts include a top-level `schema_version` field.

Current schema versions:

| Artifact Type | Schema Version |
|---|---|
| Minibatch TD artifact | `minibatch_td_v1` |
| One-step update artifact | `one_step_update_v1` |
| Short-trace update artifact | `short_trace_update_v2` |

Verifiers reject artifacts if:

- `schema_version` is missing;
- `schema_version` does not match the expected schema.

This prevents stale or incompatible artifacts from being silently accepted.

---

### Canonical Model-State Commitments

For `minibatch_td_v1`, `one_step_update_v1`, and `short_trace_update_v2`, artifacts include both file-level and tensor-content-level checkpoint commitments.

```text
# Minibatch TD
checkpoint_sha256
checkpoint_commitment_type
online_state_dict_key
online_state_dict_sha256
target_state_dict_sha256

# One-step update
pre_checkpoint_sha256
post_checkpoint_sha256
checkpoint_commitment_type
pre_online_state_dict_key
pre_online_state_dict_sha256
pre_target_state_dict_sha256
post_online_state_dict_key
post_online_state_dict_sha256
post_target_state_dict_sha256

# Short-trace update
initial_checkpoint_sha256
final_checkpoint_sha256
checkpoint_commitment_type
initial_online_state_dict_key
initial_online_state_dict_sha256
initial_target_state_dict_sha256
final_online_state_dict_key
final_online_state_dict_sha256
final_target_state_dict_sha256
```

For minibatch TD artifacts:

```text
checkpoint_sha256
```

anchors the checkpoint file, while:

```text
online_state_dict_sha256
target_state_dict_sha256
```

anchor the canonical sorted tensor contents of the online and target networks.

For one-step update artifacts:

```text
pre_checkpoint_sha256
post_checkpoint_sha256
```

anchor the pre/post checkpoint files, while:

```text
pre_online_state_dict_sha256
pre_target_state_dict_sha256
post_online_state_dict_sha256
post_target_state_dict_sha256
```

anchor the exact model-state transition checked by the verifier.

For short-trace artifacts:

```text
initial_checkpoint_sha256
final_checkpoint_sha256
```

anchor the trace-boundary checkpoint files, while:

```text
initial_online_state_dict_sha256
initial_target_state_dict_sha256
final_online_state_dict_sha256
final_target_state_dict_sha256
```

anchor the canonical tensor contents of the online and target networks at the start and end of the trace.

This is stronger than relying only on the raw `.pt` file hash because it separates the model-state commitment from PyTorch checkpoint serialization details.

The canonical model-state commitment helper is implemented in:

```text
zk_offline_dqn/commitments.py
```

---

## Locked Benchmark Snapshot

The current repository-level benchmark milestone is the locked 8-step short-trace benchmark with deterministic sampling-rule enforcement.

Snapshot refreshed on 2026-05-02 from:

```text
artifacts/benchmarks/short_trace_update/summary.json
```

### Run 0

| Field | Value |
|---|---:|
| `start_offset` | `0` |
| `batch_size` | `4` |
| `export_time_sec` | `21.9907` |
| `verify_time_sec` | `13.4818` |
| `verification_passed` | `True` |

### Run 1

| Field | Value |
|---|---:|
| `start_offset` | `32` |
| `batch_size` | `4` |
| `export_time_sec` | `23.2580` |
| `verify_time_sec` | `13.6440` |
| `verification_passed` | `True` |

### Run 2

| Field | Value |
|---|---:|
| `start_offset` | `0` |
| `batch_size` | `8` |
| `export_time_sec` | `22.4650` |
| `verify_time_sec` | `14.0169` |
| `verification_passed` | `True` |

The full locked snapshot is documented in:

```text
docs/current_benchmark_snapshot.md
```

---

## What Is Not Yet Verified

The current repository still does **not** verify:

- that the final published checkpoint came from a full correct training trace from initialization;
- general replay-sampling correctness across a long run;
- prioritized replay correctness;
- stochastic replay with full RNG-state modeling;
- long-horizon target-network synchronization guarantees;
- model selection;
- early stopping;
- best-checkpoint selection;
- recursive proof composition;
- a full end-to-end proof of training;
- a production zero-knowledge backend.

More precisely:

- **already enforced now:** deterministic contiguous sampling and seeded-permutation sampling for short traces;
- **not yet enforced generally:** prioritized replay, stochastic replay with full RNG-state modeling, or replay correctness over a full long training run;
- **already checked in Python:** TD arithmetic, canonical model-state anchoring, forward TD consistency, one-step SGD update consistency, one-step next-action/value-selection checking, short-trace boundary commitment checking, and short-trace chaining;
- **not yet proven in ZK:** the same relations inside a zkVM, SNARK, or custom circuit.

---

## ZK Backend MVP Roadmap

The current repository is a pre-ZK artifact/verifier framework. It verifies committed-data offline DQN training artifacts in Python, but it is not yet a full zero-knowledge proof-of-training system.

The next research milestone is to move the smallest backend-ready relation into a real proving backend:

> Merkle membership + Bellman target + SmoothL1 TD loss over a committed offline DQN transition.

The documentation for this milestone is split into:

- [`docs/zk_backend_mvp.md`](docs/zk_backend_mvp.md): defines the smallest ZK backend statement, public inputs, private witness, relation, fixed-point arithmetic, and non-goals.
- [`docs/threat_model.md`](docs/threat_model.md): defines prover/verifier roles, adversarial tampering cases, security goals, privacy goals, and out-of-scope claims.
- [`docs/backend_choice.md`](docs/backend_choice.md): compares RISC Zero, SP1, Noir, Circom, and Halo2, and explains why the first MVP should start with a zkVM backend.

The first backend-facing test vector is now available under:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

It can be regenerated from the existing minibatch TD artifact with:

```bash
python scripts/artifacts_export/export_td_mvp_test_vector.py
```

The test vector is exported from:

```text
artifacts/minibatch_td_from_dataset.json
```

and contains a single-transition statement for:

```text
Merkle membership
+ Bellman target
+ TD error
+ SmoothL1 TD loss
+ claimed target/loss consistency
```
The first concrete backend implementation target selected in v0.12 is:

```text
SP1
```

RISC Zero remains the main alternative backend for a later comparison milestone. The decision rationale is documented in:

```text
docs/backend_selection_v0_12.md
```

The intended progression is:

```text
Python artifact verification
→ backend-ready TD relation
→ real ZK proof for TD arithmetic
→ verified one-step update
→ short-trace proof
→ chunked or recursive full-training certificate
```

The first backend MVP intentionally does not prove full DQN training, full neural-network forward passes, backpropagation, Adam optimizer semantics, long traces, or recursive proof aggregation.

---

## Repository Structure

```text
zk_offline_dqn/
├── .github/
│   └── workflows/
│       └── regression.yml
│
├── zk_offline_dqn/
│   ├── __init__.py
│   ├── zk_specs.py
│   ├── artifact_export_utils.py
│   ├── artifact_schema_versions.py
│   ├── commitments.py
│   └── sampling_rules.py
│
├── scripts/
│   ├── training/
│   │   ├── train_cartpole_dqn.py
│   │   ├── train_offline_dqn.py
│   │   ├── train_cql.py
│   │   └── train_bc.py
│   │
│   ├── data_gen/
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
│   │   ├── verify_forward_td_consistency.py
│   │   ├── verify_one_step_update_artifact.py
│   │   └── verify_short_trace_update_artifact.py
│   │
│   ├── experiments/
│   │   ├── benchmark_one_step_update.py
│   │   ├── benchmark_short_trace_update.py
│   │   ├── run_full_regression.py
│   │   ├── run_negative_verification_tests.py
│   │   ├── run_one_step_negative_tests.py
│   │   └── run_short_trace_negative_tests.py
│   │
│   └── zk_proofs/
│       ├── build_leaf_hashes.py
│       ├── build_merkle_root.py
│       ├── check_merkle_membership.py
│       └── check_real_transition.py
│
├── docs/
│   ├── artifact_schema.md
│   ├── current_benchmark_snapshot.md
│   └── one_step_field_classification.md
│
├── paper/
├── data/
├── models/
├── logs/
├── artifacts/
├── plots/
│
├── proof_statement_design.md
├── setup.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Installation

```bash
git clone https://github.com/patee1811/zk_offline_dqn.git
cd zk_offline_dqn

python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

All commands below should be run from the project root.

---

## Usage

### Stage 1: Train a Behavior Policy

```bash
python scripts/training/train_cartpole_dqn.py
```

---

### Stage 2: Generate an Offline Dataset

```bash
python scripts/data_gen/generate_cartpole_dataset_from_dqn.py \
    --model models/dqn_cartpole_behavior \
    --epsilon 0.10
```

```bash
python scripts/data_gen/flatten_episode_dataset.py \
    --infile data/cartpole_dqn_eps010_episodes.pkl \
    --out data/cartpole_dqn_eps010_transitions.pkl
```

---

### Stage 3: Train Offline Baselines

```bash
python scripts/training/train_offline_dqn.py \
    --data data/cartpole_dqn_eps010_transitions.pkl
```

```bash
python scripts/training/train_cql.py \
    --data data/cartpole_dqn_eps010_transitions.pkl
```

```bash
python scripts/training/train_bc.py \
    --data data/cartpole_dqn_eps010_transitions.pkl
```

---

### Stage 4: Build Dataset Commitments

```bash
python scripts/zk_proofs/build_leaf_hashes.py
```

```bash
python scripts/zk_proofs/build_merkle_root.py
```

```bash
python scripts/artifacts_export/export_transition_membership_artifact.py
python scripts/artifacts_export/verify_transition_membership_artifact.py
```

---

### Stage 5: Export and Verify TD Artifacts

#### Single-Sample TD Artifact

```bash
python scripts/artifacts_export/export_td_sample_artifact.py
python scripts/artifacts_export/verify_td_sample_artifact.py
```

#### Minibatch TD Artifact

```bash
python scripts/artifacts_export/export_minibatch_td_artifact.py
python scripts/artifacts_export/verify_minibatch_td_artifact.py
```

---

### Stage 6: Export TD Artifacts from Real Dataset + Merkle Root + Checkpoint

#### Single Sample

```bash
python scripts/artifacts_export/export_td_sample_artifact_from_dataset.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --index 0 \
    --out artifacts/td_sample_from_dataset.json
```

```bash
python scripts/artifacts_export/verify_td_sample_artifact.py
```

#### Minibatch

```bash
python scripts/artifacts_export/export_minibatch_td_artifact_from_dataset.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --indices 0,1,2,3 \
    --out artifacts/minibatch_td_from_dataset.json
```

```bash
python scripts/artifacts_export/verify_minibatch_td_artifact.py
```

---

### Stage 7: Verify Forward TD Consistency

After exporting a minibatch TD artifact, run:

```bash
python scripts/artifacts_export/verify_forward_td_consistency.py \
    --artifact artifacts/minibatch_td_from_dataset.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt
```

Expected output includes:

```text
all_forward_ok = True
verification_passed = True
```

This checks that:

```text
q_online_fp
next_action_online
q_target_max_fp
```

match the actual forward-pass results from the checkpoint.

---

### Stage 8: Export and Verify One Offline DQN SGD Update Step

```bash
python scripts/artifacts_export/export_one_step_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --indices 0,1,2,3 \
    --lr 0.001 \
    --post-checkpoint-out artifacts/one_step_post_checkpoint.pt \
    --out artifacts/one_step_update_artifact.json
```

```bash
python scripts/artifacts_export/verify_one_step_update_artifact.py
```

Expected output includes:

```text
next_action_match=True
q_target_max_match=True
one_step_canonical_commitments_ok = True
verification_passed = True
```

---

### Stage 9: Export and Verify Short Training Traces

The short-trace exporter currently supports two deterministic sampling rules:

```text
contiguous_deterministic
seeded_permutation
```

#### Option A: Contiguous deterministic sampling

```bash
python scripts/artifacts_export/export_short_trace_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --trace-batches-json "[[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]]" \
    --lr 0.001 \
    --target-sync-every 2 \
    --sampling-rule-type contiguous_deterministic \
    --start-offset 0 \
    --work-dir artifacts/short_trace_work \
    --out artifacts/short_trace_artifact.json
```

#### Option B: Seeded-permutation sampling

```bash
python scripts/artifacts_export/export_short_trace_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --trace-batches-json "[[19,5,14,4],[9,13,15,18]]" \
    --lr 0.001 \
    --target-sync-every 2 \
    --sampling-rule-type seeded_permutation \
    --sampling-seed 42 \
    --dataset-size 20 \
    --work-dir artifacts/short_trace_seeded_work \
    --out artifacts/short_trace_seeded_artifact.json
```

For `seeded_permutation`, the verifier reconstructs the deterministic permutation from:

```text
sampling_seed
dataset_size
batch_size
num_steps
```

and checks that the public `trace_batch_indices` match the expected batches.

---

#### Verify the exported short trace

The exporter prints a `final_checkpoint_path`. Use that path in the verifier.

For Linux/macOS:

```bash
export SHORT_TRACE_ARTIFACT_PATH=artifacts/short_trace_artifact.json
export SHORT_TRACE_MERKLE_PATH=artifacts/cartpole_dqn_eps010_merkle.json
export SHORT_TRACE_INITIAL_CHECKPOINT_PATH=models/offline_dqn_with_target_seed42_best.pt
export SHORT_TRACE_FINAL_CHECKPOINT_PATH=artifacts/short_trace_work/<printed-final-checkpoint>.pt
export SHORT_TRACE_WORK_DIR=artifacts/short_trace_work

python scripts/artifacts_export/verify_short_trace_update_artifact.py
```

For PowerShell:

```powershell
$env:SHORT_TRACE_ARTIFACT_PATH="artifacts/short_trace_artifact.json"
$env:SHORT_TRACE_MERKLE_PATH="artifacts/cartpole_dqn_eps010_merkle.json"
$env:SHORT_TRACE_INITIAL_CHECKPOINT_PATH="models/offline_dqn_with_target_seed42_best.pt"
$env:SHORT_TRACE_FINAL_CHECKPOINT_PATH="artifacts/short_trace_work/<printed-final-checkpoint>.pt"
$env:SHORT_TRACE_WORK_DIR="artifacts/short_trace_work"

python scripts/artifacts_export/verify_short_trace_update_artifact.py
```

For the seeded example, use the seeded artifact and its printed final checkpoint path:

```powershell
$env:SHORT_TRACE_ARTIFACT_PATH="artifacts/short_trace_seeded_artifact.json"
$env:SHORT_TRACE_MERKLE_PATH="artifacts/cartpole_dqn_eps010_merkle.json"
$env:SHORT_TRACE_INITIAL_CHECKPOINT_PATH="models/offline_dqn_with_target_seed42_best.pt"
$env:SHORT_TRACE_FINAL_CHECKPOINT_PATH="artifacts/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt"
$env:SHORT_TRACE_WORK_DIR="artifacts/short_trace_seeded_work"

python scripts/artifacts_export/verify_short_trace_update_artifact.py
```

Expected output includes:

```text
all_sampling_rule_ok = True
short_trace_canonical_boundary_commitments_ok = True
verification_passed = True
```

---

### Stage 10: Run the Short-Trace Benchmark

```bash
python scripts/experiments/benchmark_short_trace_update.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --lr 0.001 \
    --target-sync-every 2
```

The benchmark runner automatically:

- exports short-trace artifacts;
- parses the printed final checkpoint path;
- sets verifier environment variables;
- runs the verifier;
- records benchmark metadata.

---

### Stage 11: Run Minibatch TD Negative Tests

```bash
python scripts/experiments/run_negative_verification_tests.py
```

Expected output includes:

```text
valid_control_accept = True
tamper_loss_fp_accept = False
tamper_reward_accept = False
tamper_checkpoint_sha256_accept = False
tamper_online_state_dict_sha256_accept = False
tamper_leaf_hash_accept = False
tamper_merkle_path_accept = False
all_tests_passed = True
```

The summary is written to:

```text
artifacts/negative_tests/summary.csv
```

Example summary:

```csv
case_name,expected_accept,actual_accept,passed,artifact_path,returncode
valid_control,True,True,True,artifacts/negative_tests/valid_control.json,0
tamper_loss_fp,False,False,True,artifacts/negative_tests/tamper_loss_fp.json,0
tamper_reward,False,False,True,artifacts/negative_tests/tamper_reward.json,0
tamper_checkpoint_sha256,False,False,True,artifacts/negative_tests/tamper_checkpoint_sha256.json,0
tamper_online_state_dict_sha256,False,False,True,artifacts/negative_tests/tamper_online_state_dict_sha256.json,0
tamper_leaf_hash,False,False,True,artifacts/negative_tests/tamper_leaf_hash.json,0
tamper_merkle_path,False,False,True,artifacts/negative_tests/tamper_merkle_path.json,0
```

---

### Stage 12: Run One-Step Negative Tests

```bash
python scripts/experiments/run_one_step_negative_tests.py
```

Expected output includes:

```text
valid_one_step_accept = True
tamper_next_action_online_accept = False
tamper_q_target_max_fp_accept = False
tamper_loss_fp_accept = False
tamper_gradient_tensor_accept = False
tamper_delta_tensor_accept = False
tamper_post_checkpoint_sha256_accept = False
tamper_post_online_state_dict_sha256_accept = False
tamper_learning_rate_fp_accept = False
tamper_batch_indices_accept = False
all_tests_passed = True
```

The summary is written to:

```text
artifacts/one_step_negative_tests/summary.csv
```

The one-step negative-test runner checks that the verifier accepts a valid one-step artifact and rejects tampered variants.

| Case | Expected Result | Reason |
|---|---:|---|
| `valid_one_step` | accept | unchanged valid one-step update artifact |
| `tamper_next_action_online` | reject | claimed Double-DQN online argmax action no longer matches the pre-update online network |
| `tamper_q_target_max_fp` | reject | claimed target-network value no longer matches `Q_target(s')[next_action_online]` |
| `tamper_loss_fp` | reject | per-item SmoothL1 TD loss no longer matches the recomputed value |
| `tamper_gradient_tensor` | reject | claimed gradient tensor no longer matches recomputed gradients |
| `tamper_delta_tensor` | reject | claimed parameter delta no longer matches the pre/post online-network difference |
| `tamper_post_checkpoint_sha256` | reject | public post-update checkpoint hash no longer matches the post checkpoint file |
| `tamper_post_online_state_dict_sha256` | reject | public post-update online state-dict commitment no longer matches canonical checkpoint tensor contents |
| `tamper_learning_rate_fp` | reject | public learning-rate field no longer matches the expected update relation |
| `tamper_batch_indices` | reject | public minibatch indices no longer match the embedded one-step item indices |

---

### Stage 13: Run Short-Trace Negative Tests

```bash
python scripts/experiments/run_short_trace_negative_tests.py
```

Expected output includes:

```text
valid_contiguous_accept = True
valid_seeded_accept = True
tamper_contiguous_public_batch_accept = False
tamper_seeded_public_batch_accept = False
tamper_sampling_seed_accept = False
tamper_dataset_size_accept = False
tamper_final_checkpoint_sha256_accept = False
tamper_final_online_state_dict_sha256_accept = False
all_tests_passed = True
```

The summary is written to:

```text
artifacts/short_trace_negative_tests/summary.csv
```

---

### Stage 14: Full Regression Summary

```bash
python scripts/experiments/run_full_regression.py
```

Expected output includes:

```text
num_checks = 9
all_regression_passed = True
summary_json_path = artifacts/regression_summary.json
summary_md_path = artifacts/regression_summary.md
```

Generated outputs:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
artifacts/full_regression/*.stdout.txt
artifacts/full_regression/*.stderr.txt
```

This is the same regression runner used by GitHub Actions.

---

### Stage 15: Manual Short-Trace Sampling-Rule Tamper Check

Export a valid short-trace artifact:

```bash
python scripts/artifacts_export/export_short_trace_update_artifact.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --merkle artifacts/cartpole_dqn_eps010_merkle.json \
    --checkpoint models/offline_dqn_with_target_seed42_best.pt \
    --trace-batches-json "[[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]]" \
    --lr 0.001 \
    --target-sync-every 2 \
    --sampling-rule-type contiguous_deterministic \
    --start-offset 0 \
    --work-dir artifacts/short_trace_negative_test_work \
    --out artifacts/short_trace_negative_test_valid.json
```

Create a tampered copy with incorrect public batch indices:

```bash
python -c "import json; p='artifacts/short_trace_negative_test_valid.json'; q='artifacts/short_trace_negative_test_tampered.json'; data=json.load(open(p,'r',encoding='utf-8')); data['public']['trace_batch_indices'][1]=[5,6,7,8]; json.dump(data, open(q,'w',encoding='utf-8'), indent=2)"
```

Verify the tampered artifact:

```bash
export SHORT_TRACE_ARTIFACT_PATH=artifacts/short_trace_negative_test_tampered.json
export SHORT_TRACE_MERKLE_PATH=artifacts/cartpole_dqn_eps010_merkle.json
export SHORT_TRACE_INITIAL_CHECKPOINT_PATH=models/offline_dqn_with_target_seed42_best.pt
export SHORT_TRACE_FINAL_CHECKPOINT_PATH=artifacts/short_trace_negative_test_work/<printed-final-checkpoint>.pt
export SHORT_TRACE_WORK_DIR=artifacts/short_trace_negative_test_work

python scripts/artifacts_export/verify_short_trace_update_artifact.py
```

Expected outcome:

```text
verification_passed = False
```

---

### Stage 16: Analyze Results

```bash
python scripts/analysis/analyze_offline_log.py \
    --log logs/offline_dqn_cartpole_log_seed42.csv
```

```bash
python scripts/analysis/analyze_cql_log.py \
    --log logs/cql_cartpole_log_seed42.csv
```

---

### Stage 17: Regression Checklist

```powershell
$env:PYTHONPATH="."

python -m compileall zk_offline_dqn scripts

python scripts/artifacts_export/verify_minibatch_td_artifact.py

python scripts/artifacts_export/verify_forward_td_consistency.py `
  --artifact artifacts/minibatch_td_from_dataset.json `
  --checkpoint models/offline_dqn_with_target_seed42_best.pt

python scripts/artifacts_export/verify_one_step_update_artifact.py

$env:SHORT_TRACE_ARTIFACT_PATH="artifacts/short_trace_update_artifact.json"
$env:SHORT_TRACE_MERKLE_PATH="artifacts/cartpole_dqn_eps010_merkle.json"
$env:SHORT_TRACE_INITIAL_CHECKPOINT_PATH="models/offline_dqn_with_target_seed42_best.pt"
$env:SHORT_TRACE_FINAL_CHECKPOINT_PATH="artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt"
$env:SHORT_TRACE_WORK_DIR="artifacts/short_trace_work"

python scripts/artifacts_export/verify_short_trace_update_artifact.py

$env:SHORT_TRACE_ARTIFACT_PATH="artifacts/short_trace_seeded_artifact.json"
$env:SHORT_TRACE_FINAL_CHECKPOINT_PATH="artifacts/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt"
$env:SHORT_TRACE_WORK_DIR="artifacts/short_trace_seeded_work"

python scripts/artifacts_export/verify_short_trace_update_artifact.py

python scripts/experiments/run_negative_verification_tests.py
python scripts/experiments/run_one_step_negative_tests.py
python scripts/experiments/run_short_trace_negative_tests.py
python scripts/experiments/run_full_regression.py
```

Expected key outputs:

```text
verification_passed = True
all_forward_ok = True
next_action_match=True
q_target_max_match=True
one_step_canonical_commitments_ok = True
short_trace_canonical_boundary_commitments_ok = True
all_sampling_rule_ok = True
all_tests_passed = True
all_regression_passed = True
```

---

## Verification Semantics

The TD-artifact pipeline uses:

- **committed transition membership** through Merkle proofs;
- **Double DQN target semantics**:
  - `argmax` action selected from the online network on `next_obs`;
  - target value taken from the target network at the selected action;
- **SmoothL1 loss** in fixed-point arithmetic;
- **checkpoint anchoring** through `checkpoint_sha256`;
- **canonical model-state anchoring** through sorted tensor-content SHA-256 commitments;
- **schema-version checks** for artifact compatibility;
- **forward consistency checks** between TD witness values and checkpoint network outputs.

The one-step update prototype additionally checks:

- consistency between the committed minibatch and the recomputed training loss;
- consistency between pre/post checkpoint file hashes and checkpoint files;
- consistency between pre/post canonical model-state commitments and checkpoint tensor contents;
- one-step TD forward consistency:
  - `next_action_online` matches `argmax_a Q_online(s')`;
  - `q_target_max_fp` matches `Q_target(s')[next_action_online]`;
- consistency between recomputed gradients and stored gradient tensors;
- consistency between parameter deltas and actual pre/post online-network states;
- consistency of the SGD rule:

```text
w' = w - lr * g
```

- invariance of the target network during the one-step statement.

The short-trace prototype additionally checks:

- step-by-step checkpoint chaining;
- nested one-step update verification;
- initial/final checkpoint file-hash anchoring;
- initial/final canonical model-state commitment checking;
- explicit target-network synchronization behavior;
- deterministic contiguous sampling-rule enforcement with public `sampling_rule_type`, `start_offset`, and `batch_size`;
- seeded-permutation sampling-rule enforcement with public `sampling_seed`, `dataset_size`, `batch_size`, and `num_steps`;
- final checkpoint consistency across the full short trace.

The current implementation is a Python-level pre-ZK verifier. In a future true ZK backend, the same public inputs and private witness relations would be represented inside a zkVM, SNARK, or custom circuit.

---

## ZK-Friendly Fixed-Point Specifications

The fixed-point arithmetic used in the project is defined in:

```text
zk_offline_dqn/zk_specs.py
```

| Parameter | Value | Description |
|---|---:|---|
| `FP_SCALE` | `1000` | Fixed-point scaling factor |
| `OBS_DIM` | `4` | CartPole observation dimension |
| `ACTION_DIM` | `2` | CartPole action dimension |
| `GAMMA_FP` | `990` | Discount factor `gamma = 0.99` in fixed-point |
| `LOSS_TYPE` | `smooth_l1` | SmoothL1 TD loss |
| `SMOOTH_L1_BETA_FP` | `1000` | SmoothL1 beta `= 1.0` in fixed-point |

---

## Proof Statement Design

The current proof statements are documented in:

```text
proof_statement_design.md
```

The repository currently contains five connected statement layers.

### 1. MVP TD-Arithmetic Statement

This layer verifies:

- committed transition membership;
- Double-DQN Bellman target correctness;
- SmoothL1 TD loss correctness;
- minibatch-average loss correctness;
- checkpoint and model-state anchoring.

### 2. Forward TD Consistency Statement

This layer verifies:

- `q_online_fp` matches `Q_online(s)[a]`;
- `next_action_online` matches `argmax_a Q_online(s')`;
- `q_target_max_fp` matches `Q_target(s')[next_action_online]`.

### 3. One-Step Update Statement

This layer verifies:

- one offline DQN SGD update step from a committed minibatch;
- pre/post checkpoint consistency;
- pre/post canonical model-state commitment consistency;
- one-step `next_action_online` consistency;
- one-step `q_target_max_fp` consistency;
- gradient recomputation consistency;
- parameter-delta consistency;
- SGD update consistency.

### 4. Short Verified Training Trace

This layer verifies:

- chaining of consecutive one-step statements;
- checkpoint chaining;
- trace-boundary canonical model-state commitment consistency;
- target-network synchronization semantics.

### 5. Deterministic Short-Trace Sampling Rule

This layer verifies:

- a declared contiguous deterministic batch schedule;
- a declared seeded-permutation batch schedule;
- public `sampling_rule_type`, `start_offset`, `sampling_seed`, `dataset_size`, and `batch_size`;
- rejection of tampered public trace batches or sampling metadata.

---

## Data

The repository includes a small set of committed regression fixtures required by GitHub Actions:

```text
data/cartpole_dqn_eps010_transitions.pkl
models/offline_dqn_with_target_seed42_best.pt
artifacts/cartpole_dqn_eps010_merkle.json
artifacts/minibatch_td_from_dataset.json
artifacts/one_step_update_artifact.json
artifacts/one_step_post_checkpoint.pt
artifacts/short_trace_update_artifact.json
artifacts/short_trace_seeded_artifact.json
artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt
artifacts/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt
```

These are lightweight fixtures for regression verification.

Larger generated datasets, long-run benchmark outputs, logs, checkpoints, and plots should still be treated as generated artifacts and may be excluded from version control depending on size and reproducibility needs.

Typical generated files include:

- episode-level datasets, e.g. `cartpole_dqn_eps010_episodes.pkl`;
- transition-level datasets, e.g. `cartpole_dqn_eps010_transitions.pkl`;
- dataset summary JSON files;
- Merkle artifacts;
- exported verification artifacts;
- checkpoints;
- benchmark logs.

To reproduce the experiments, run the dataset generation and training scripts above.

---

## Recommended Next Technical Milestones

The strongest next milestones are:

### 1. Branch Protection for Master

Enable branch protection on GitHub:

```text
Settings -> Branches -> Add branch protection rule
```

Recommended rule:

```text
Branch name pattern: master
Require a pull request before merging
Require status checks to pass before merging
Require branches to be up to date before merging
Required status check: Regression
```

This ensures that future PRs cannot be merged unless the regression CI passes.

### 2. True ZK Backend

The most important future research step is to instantiate a real proving backend, such as:

- zkVM;
- custom SNARK circuit;
- hybrid backend.

The recommended first ZK target is not the full DQN update. A more feasible first target is:

> committed transition membership + Bellman target + SmoothL1 TD loss over a tiny quantized TD statement.

### 3. ZK Backend MVP Statement

A realistic first ZK backend could prove:

```text
Public inputs:
- Merkle root
- checkpoint/model commitment
- gamma_fp
- fp_scale
- claimed target_fp
- claimed loss_fp

Private witness:
- transition
- Merkle path
- q_online_fp
- next_action_online
- q_target_max_fp

Relation:
- transition belongs to committed dataset
- next_action_online is selected by the online network
- target value is selected from the target network using next_action_online
- Bellman target is computed correctly
- SmoothL1 TD loss is computed correctly
```

This would move the project from **pre-ZK artifact verification** toward a true **ZK proof component**.

---

## Research Positioning

This project should be positioned as:

> **Toward Zero-Knowledge Verifiable Offline DQN Training from Committed Trajectories**

The current contribution is not a full proof of training. The current contribution is a concrete, executable, pre-ZK framework that formalizes and checks the core relations needed before moving to a real proving backend.

The strongest current claims are:

1. committed offline RL data verification;
2. RL-specific Bellman/TD verification;
3. checkpoint and canonical model-state anchoring;
4. forward consistency between artifacts and neural-network checkpoints;
5. one-step SGD update consistency;
6. one-step Double-DQN action/value-selection consistency;
7. short verified update traces;
8. trace-boundary commitment verification;
9. deterministic sampling-rule enforcement;
10. systematic rejection of tampered artifacts;
11. automated regression CI and regression report generation.

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