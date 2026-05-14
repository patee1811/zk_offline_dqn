# Current Benchmark Snapshot

This file records the achieved verification capabilities and their benchmark
results. The machine-readable source is
`artifacts/benchmarks/final_ndss/summary.json`.

## Regression Coverage

```text
command = python scripts/experiments/run_full_regression.py
num_checks = 15
num_passed = 15
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
| distinct TD benchmark smoke | pass |
| forward-TD MLP benchmark smoke | pass |
| one-step SGD tiny benchmark smoke | pass |
| MountainCar forward-TD benchmark smoke | pass |
| TD MVP test-vector negative tests | pass |
| paper/benchmark number consistency check | pass |

## Achieved SP1 Proofs

| Relation | Environment | Network | Batch | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 1 | 97.955756 | 0.126565 | 2783869 | 385048 |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 2 | 120.669043 | 0.127258 | 2788227 | 730778 |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 4 | 141.309797 | 0.125481 | 2796699 | 1435787 |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 8 | 202.921645 | 0.126658 | 2812915 | 2845813 |
| `forward_td_mlp_v1` | CartPole-v1 | 4-16-16-2 | 1 | 148.418458 | 0.127259 | 2797833 | 1543753 |
| `forward_td_mlp_v1` | MountainCar-v0 | 2-8-8-3 | 1 | 107.926506 | 0.126694 | 2787889 | 683942 |
| `one_step_sgd_tiny_v1` | CartPole-v1 | 4-8-2 | 1 | 115.494141 | 0.125332 | 2789940 | 862136 |

## Tamper Coverage

| Relation | Count | Result |
| --- | ---: | --- |
| Distinct TD | 6 | Python and SP1 reject |
| CartPole forward-TD MLP | 7 | Python and SP1 reject |
| MountainCar forward-TD MLP | 2 | Python and SP1 reject |
| Tiny one-step SGD | 6 | Python and SP1 reject |

## Paper-Facing Claim

```text
ZK-backed offline DQN relation proofs over committed trajectory data, covering
distinct minibatch TD, model-grounded forward-TD MLP checks, and one
micro-scale SGD update.
```

Required limitation:

```text
The backend does not prove full optimizer traces, Adam semantics,
checkpoint-to-checkpoint training histories, full training traces, or honest
data collection before commitment.
```
