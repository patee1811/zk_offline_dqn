# Second-Environment Forward-TD Result

This document records the second-environment benchmark for
`forward_td_mlp_v1`.

## Verified Relation

The second-environment benchmark uses `MountainCar-v0` with a small quantized
MLP:

```text
MountainCar-v0 2-8-8-3
```

The fixture checks committed transition membership, model commitments,
fixed-point MLP forward passes, Double-DQN argmax/value selection, Bellman TD,
SmoothL1 loss, and batch loss aggregation.

## Proof Metrics

| Case | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `mountaincar-forward-TD-1` | 1 | accepted proof | 107.926506 | 0.126694 | 2787889 | 683942 |

Tamper rejection covers selected target value and argmax.

## Commands

```bash
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
```

## Scope

This is a second environment/spec benchmark, not a policy-performance claim.
The default dataset is collected with a seeded random policy. The purpose is to
show that the committed-data and forward-TD proof relation is not hard-wired to
CartPole dimensions or two-action control.
