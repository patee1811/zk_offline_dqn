# One-Step SGD Tiny Result

This document records what the `one_step_sgd_tiny_v1` relation verifies and the
benchmark outcome that is used by the paper.

## Verified Relation

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

## Implemented Spec

```text
environment = CartPole-v1
network = 4-8-2
fp_scale = 1000
learning_rate_fp = 100
optimizer_type = sgd
loss_type = smooth_l1
batch_size = 1
```

## Proof Metrics

| Case | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: |
| `one-step-SGD-tiny-1` | accepted proof | 115.494141 | 0.125332 | 2789940 | 862136 |

Tamper rejection covers gradient tensor, delta tensor, learning rate, post
model weight, post model commitment, and SmoothL1 derivative branch.

## Reproduction Commands

```bash
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
```

## Scope

This relation is a micro proof of update evidence, not a full
proof-of-training. It does not prove Adam, target synchronization, recursive
proof aggregation, or a long DQN training trace.
