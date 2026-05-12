# Week 5 Artifact Package

This file locks the implementation, benchmark, and artifact status at the end
of Week 5. After this point, avoid adding large backend features before the
paper rewrite. Week 6 should write from the results below.

## Final Backend Scope

Locked backend scope:

- SP1 single-transition TD proof: implemented and proof result recorded.
- SP1 minibatch TD proof for TD-2, TD-4, and TD-8: implemented and proof
  results recorded.
- Python one-step and short-trace verifiers: retained as pre-ZK extensions.
- Full DQN proof-of-training, neural-network forward proofs, gradients,
  optimizer proofs, recursive aggregation, and long-trace SP1 proofs remain
  out of scope.

Strongest defensible claim:

```text
ZK-backed offline DQN TD and minibatch-TD verification over committed
trajectory data, with Python pre-ZK extensions for one-step update and
short-trace verification.
```

This should not be phrased as a full proof-of-training result.

## Canonical Artifact Commands

Run the Python regression from the repository root:

```bash
python scripts/experiments/run_full_regression.py
```

Expected outputs:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
artifacts/full_regression/*.stdout.txt
artifacts/full_regression/*.stderr.txt
```

Run a single SP1 execution/proof from Linux, macOS, or WSL2 Ubuntu:

```bash
cd zk_backend/td_mvp/sp1
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
```

Run the SP1 negative suite:

```bash
cd zk_backend/td_mvp/sp1
bash run_negative_cases.sh
```

Run the full SP1 benchmark/reproducibility runner:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

If proving all accepted cases in one run is unstable, prove one accepted case
at a time:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-8
```

On machines without SP1, run only the Python semantic-oracle smoke path and
write it to a separate directory:

```bash
python scripts/experiments/benchmark_sp1_td_mvp.py \
  --skip-sp1 \
  --out-dir artifacts/benchmarks/sp1_td_mvp_python_smoke
```

## Canonical Test Vector

The canonical committed TD MVP test vector is:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

The Python semantic oracle is:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
```

The SP1 backend workspace is:

```text
zk_backend/td_mvp/sp1/
```

## Regression Snapshot

Latest local Week 5 Python regression run:

```text
date = 2026-05-12
platform = native Windows PowerShell
command = python scripts/experiments/run_full_regression.py
num_checks = 10
num_passed = 10
num_failed = 0
all_regression_passed = True
```

Covered checks:

| Check | Status |
| --- | --- |
| Python compile checks | pass |
| TD/minibatch artifact verifier | pass |
| forward TD consistency verifier | pass |
| one-step verifier | pass |
| short-trace contiguous verifier | pass |
| short-trace seeded verifier | pass |
| one-step negative tests | pass |
| short-trace negative tests | pass |
| minibatch TD negative tests | pass |
| TD MVP test-vector negative tests | pass |

## Locked SP1 Proof Snapshot

These proof metrics are the current locked SP1 benchmark values. They were
recorded from a full Kaggle run generated at
`2026-05-12T12:37:34.964280+00:00`.

| Case | Relation | Batch size | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TD-1 | Merkle + TD + SmoothL1 | 1 | 142.324547 | 0.157464 | 2782625 | 382915 |
| TD-2 | Merkle + TD + SmoothL1 + average loss | 2 | 154.923089 | 0.157712 | 2787687 | 725309 |
| TD-4 | Merkle + TD + SmoothL1 + average loss | 4 | 188.501940 | 0.155969 | 2795631 | 1425790 |
| TD-8 | Merkle + TD + SmoothL1 + average loss | 8 | 275.077262 | 0.157424 | 2812327 | 2834727 |

Kaggle full-run status:

```text
prove_requested = True
prove_cases = TD-1, TD-2, TD-4, TD-8
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_sp1_negative_cases_passed = true
```

Native Windows PowerShell was used only for the local Week 5 Python regression
and Python semantic-oracle smoke run. Full SP1 proving remains a
WSL2/Linux/macOS/Kaggle workflow.

Local WSL availability check on 2026-05-12:

```text
wsl -e bash -lc "..."
result = failed
reason = Windows Subsystem for Linux has no installed distributions
```

Because of that environment limitation, the Week 5 turn did not rerun the full
SP1 proof suite on the local Windows machine. The SP1 proof status is locked
from the full Kaggle run recorded above.

## Tamper Rejection Table

Single-transition cases:

| Case | Expected result | Guard |
| --- | --- | --- |
| valid_control | accept | baseline vector |
| tamper_schema_version | reject | schema compatibility |
| tamper_reward | reject | transition serialization, Merkle root, TD target |
| tamper_fixed_point_rounding | reject | fixed-point conversion consistency |
| tamper_done | reject | transition serialization and done branch |
| tamper_done_branch | reject | terminal/non-terminal target semantics |
| tamper_transition_obs | reject | transition serialization and Merkle root |
| tamper_leaf_encoding | reject | serialized leaf equality |
| tamper_merkle_path | reject | Merkle root recomputation |
| tamper_leaf_index | reject | public index/path direction consistency |
| tamper_path_order | reject | Merkle path ordering |
| tamper_q_target_max_fp | reject | Bellman target recomputation |
| tamper_target_network_value | reject | target-value witness consistency |
| tamper_claimed_target_fp | reject | public target consistency |
| tamper_claimed_loss_fp | reject | public loss consistency |
| tamper_leaf_hash | reject | canonical leaf hash consistency |
| tamper_td_error_fp | reject | TD error recomputation |

Batch cases:

| Case | Expected result | Guard |
| --- | --- | --- |
| valid_batch_size_2 | accept | baseline batch vector |
| tamper_batch_claimed_loss_fp | reject | public average loss consistency |
| tamper_batch_size | reject | public batch size consistency |
| tamper_batch_item_loss_fp | reject | per-item loss recomputation |
| tamper_batch_item_index | reject | per-item Merkle index consistency |
| tamper_batch_path_order | reject | per-item Merkle path ordering |
| tamper_batch_target_network_value | reject | per-item target-value witness consistency |
| tamper_batch_fixed_point_rounding | reject | per-item fixed-point conversion consistency |

## Locked Short-Trace Snapshot

The current locked pre-ZK short-trace benchmark remains the contiguous
deterministic 8-step benchmark in `docs/current_benchmark_snapshot.md`.

Representative settings:

```text
num_steps = 8
target_sync_every = 2
batch_size = 4 or 8
verification_passed = True
```

This is a pre-ZK extension result and should not be described as an SP1 trace
proof.

## Limitations for Paper

Required limitations:

- The backend proves TD and minibatch-TD relations, not full DQN training.
- Neural-network forward pass, argmax action selection, gradients,
  optimizer semantics, and checkpoint-to-checkpoint updates are not proven in
  SP1.
- One-step and short-trace checks are Python verifiers, not ZK proofs.
- TD-2/4/8 benchmark fixtures repeat the canonical TD item to exercise
  minibatch aggregation and multiple memberships; they are not a diverse
  sampled replay batch benchmark.
- SP1 proving is currently expensive and should be reported as prototype-scale.
- Results are still CartPole-focused.
- Dataset commitment proves membership in a committed dataset, not honesty of
  data collection or reward assignment before commitment.

## Submission Target Recommendation

Current recommendation:

```text
Q1 journal or strong workshop/preprint first; A*/top security only if Week 6
writing is very sharp and reproducing SP1 benchmarks on the target machine is
clean.
```

Reason:

- The implementation has a real SP1 backend and meaningful negative tests.
- The claim remains intentionally scoped to TD/minibatch TD, not full
  proof-of-training.
- The paper needs careful positioning around proof-of-learning, zkML,
  verifiable RL, and ZK+RL systems to avoid overclaiming.
