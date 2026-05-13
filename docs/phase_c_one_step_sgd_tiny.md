# Phase C One-Step SGD Tiny Result

This document records the Phase C `one_step_sgd_tiny_v1` implementation and the
Kaggle SP1 benchmark snapshot.

## Relation

`one_step_sgd_tiny_v1` proves a micro-scale SGD update for a one-hidden-layer
fixed-point Q-network:

- committed replay transition membership;
- fixed-point forward-TD over a pre-update online model and target model;
- Double-DQN first-argmax target selection;
- SmoothL1 TD loss;
- SmoothL1 derivative branch;
- one-hidden-layer backpropagation gradients;
- SGD parameter deltas;
- post-update model equality;
- pre/target/post model commitments.

The network spec is intentionally small:

```text
CartPole 4-8-2
fp_scale = 1000
learning_rate_fp = 100
optimizer_type = sgd
loss_type = smooth_l1
batch_size = 1
```

## Implementation Paths

```text
zk_offline_dqn/forward_td_mlp.py
scripts/artifacts_export/export_one_step_sgd_tiny_test_vector.py
scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py
scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py
zk_backend/td_mvp/sp1/shared/src/lib.rs
```

## Reproduction Commands

Python-only oracle and tamper matrix:

```bash
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1
```

SP1 execute for valid and tamper cases:

```bash
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py
```

SP1 proof for batch 1:

```bash
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
```

## Kaggle SP1 Snapshot

Run metadata:

```text
generated_at_utc = 2026-05-13T07:06:05.105838+00:00
git_commit = 3ef14fe5baac8dc8f2b6369fb7229ef0266fac10
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

Benchmark matrix:

| Case | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: |
| `one-step-SGD-tiny-1` | accepted | 168.844574 | 0.152385 | 2789940 | 861913 |
| `tamper_gradient_tensor` | rejected | n/a | n/a | n/a | 815954 |
| `tamper_delta_tensor` | rejected | n/a | n/a | n/a | 818527 |
| `tamper_learning_rate_fp` | rejected | n/a | n/a | n/a | 798644 |
| `tamper_post_model_weight` | rejected | n/a | n/a | n/a | 312479 |
| `tamper_post_model_commitment` | rejected | n/a | n/a | n/a | 312479 |
| `tamper_smooth_l1_grad` | rejected | n/a | n/a | n/a | 786276 |

## Acceptance Status

Phase C acceptance criteria are met:

- Python fixed-point oracle and SP1 relation agree.
- SP1 execute passes for batch 1.
- SP1 proof is generated and verified for batch 1.
- Gradient, delta, learning-rate, post-model, post-commitment, and SmoothL1
  derivative tamper cases reject.

## Scope Limitations

This relation is a micro proof of update evidence, not a full
proof-of-training. It does not prove Adam, target synchronization, recursive
proof aggregation, or a long DQN training trace.
