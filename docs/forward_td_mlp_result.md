# Forward-TD MLP Result

This document records what the `forward_td_mlp_v1` relation verifies and the
benchmark outcome that is used by the paper.

## Verified Relation

`forward_td_mlp_v1` proves, inside the SP1 backend path:

- committed replay transition membership;
- quantized online model commitment;
- quantized target model commitment;
- fixed-point online MLP forward on `s`;
- fixed-point online MLP forward on `s'`;
- fixed-point target MLP forward on `s'`;
- Double-DQN first-argmax action selection;
- selected target-network value;
- terminal/non-terminal Bellman target;
- SmoothL1 TD loss;
- claimed per-item and batch loss.

## Implemented Specs

| Environment | Network | Accepted proof rows | Execute-only accepted rows | Rejected tamper rows |
| --- | --- | ---: | ---: | ---: |
| CartPole-v1 | 4-16-16-2 | 1 | 1 | 7 |
| MountainCar-v0 | 2-8-8-3 | 1 | 0 | 2 |

## CartPole Proof Metrics

| Case | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `forward-TD-1` | 1 | accepted proof | 148.418458 | 0.127259 | 2797833 | 1543753 |
| `forward-TD-2` | 2 | accepted execute | n/a | n/a | n/a | 1957958 |

CartPole tamper rejection covers online model weight, target model weight,
activation, ReLU mask, argmax, selected target value, and claimed batch loss.

## MountainCar Proof Metrics

| Case | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `mountaincar-forward-TD-1` | 1 | accepted proof | 107.926506 | 0.126694 | 2787889 | 683942 |

MountainCar tamper rejection covers selected target value and argmax.

## Reproduction Commands

```bash
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
```

## Scope

This relation proves model-grounded TD values for checked batches. It does not
prove optimizer updates, target-network synchronization over a long trace, or
full DQN training.
