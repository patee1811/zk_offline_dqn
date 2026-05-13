# Current Benchmark Snapshot

This file records the current benchmark state used by the repository outside
`paper/`. The authoritative final package is
`artifacts/benchmarks/final_ndss/`.

## Python Regression

Latest local regression refresh:

```text
date = 2026-05-13
platform = native Windows PowerShell
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
| distinct TD-1/2/4/8 Python-only benchmark smoke | pass |
| forward-TD MLP Python-only benchmark smoke | pass |
| one-step SGD tiny Python-only benchmark smoke | pass |
| MountainCar forward-TD Python-only benchmark smoke | pass |
| TD MVP test-vector negative tests | pass |
| paper/final-NDSS number consistency check | pass |

## Phase E Final Aggregate

Latest Kaggle SP1 benchmark refresh:

```text
generated_at_utc = 2026-05-13T23:40:09.274341+00:00
platform = Kaggle Linux SP1
components_loaded = 4
benchmark_rows = 29
tamper_rows = 21
all_components_passed = True
```

Accepted SP1 proof rows:

| Relation | Environment | Network | Batch | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 1 | 97.955756 | 0.126565 | 2783869 | 385048 |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 2 | 120.669043 | 0.127258 | 2788227 | 730778 |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 4 | 141.309797 | 0.125481 | 2796699 | 1435787 |
| `td_batch_distinct_v1` | CartPole-v1 | witness Q | 8 | 202.921645 | 0.126658 | 2812915 | 2845813 |
| `forward_td_mlp_v1` | CartPole-v1 | 4-16-16-2 | 1 | 148.418458 | 0.127259 | 2797833 | 1543753 |
| `forward_td_mlp_v1` | MountainCar-v0 | 2-8-8-3 | 1 | 107.926506 | 0.126694 | 2787889 | 683942 |
| `one_step_sgd_tiny_v1` | CartPole-v1 | 4-8-2 | 1 | 115.494141 | 0.125332 | 2789940 | 862136 |

Tamper coverage:

| Relation | Count | Result |
| --- | ---: | --- |
| Distinct TD | 6 | Python and SP1 reject |
| CartPole forward-TD MLP | 7 | Python and SP1 reject |
| MountainCar forward-TD MLP | 2 | Python and SP1 reject |
| Tiny one-step SGD | 6 | Python and SP1 reject |

## Phase A Distinct Minibatch TD

Historical Kaggle SP1 benchmark refresh superseded by the Phase E aggregate:

```text
generated_at_utc = 2026-05-13T01:15:29.080668+00:00
platform = Kaggle Linux
command = python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
batch_sizes = TD-1, TD-2, TD-4, TD-8
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

Accepted distinct replay minibatches:

| Case | Relation | Batch size | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TD-1 | `td_batch_distinct_v1` | 1 | 97.955756 | 0.126565 | 2783869 | 385048 |
| TD-2 | `td_batch_distinct_v1` | 2 | 120.669043 | 0.127258 | 2788227 | 730778 |
| TD-4 | `td_batch_distinct_v1` | 4 | 141.309797 | 0.125481 | 2796699 | 1435787 |
| TD-8 | `td_batch_distinct_v1` | 8 | 202.921645 | 0.126658 | 2812915 | 2845813 |

Tamper coverage:

| Case group | Result |
| --- | --- |
| duplicate index | Python and SP1 reject |
| wrong item index | Python and SP1 reject |
| swapped item order against public `leaf_indices` | Python and SP1 reject |
| wrong item loss | Python and SP1 reject |
| wrong claimed batch average | Python and SP1 reject |
| wrong Merkle path order/metadata | Python and SP1 reject |

The older `benchmark_sp1_td_mvp.py` repeated-transition benchmark remains below
as historical backend evidence, not as the main Phase A minibatch result.

## Legacy SP1 TD MVP

Latest full SP1 benchmark refresh:

```text
generated_at_utc = 2026-05-12T12:37:34.964280+00:00
platform = Kaggle Linux
command = python scripts/experiments/benchmark_sp1_td_mvp.py --prove
prove_cases = TD-1, TD-2, TD-4, TD-8
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_sp1_negative_cases_passed = true
```

| Case | Relation | Batch size | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TD-1 | Merkle + TD + SmoothL1 | 1 | 142.324547 | 0.157464 | 2782625 | 382915 |
| TD-2 | Merkle + TD + SmoothL1 + average loss | 2 | 154.923089 | 0.157712 | 2787687 | 725309 |
| TD-4 | Merkle + TD + SmoothL1 + average loss | 4 | 188.501940 | 0.155969 | 2795631 | 1425790 |
| TD-8 | Merkle + TD + SmoothL1 + average loss | 8 | 275.077262 | 0.157424 | 2812327 | 2834727 |

Tamper coverage:

| Group | Result |
| --- | --- |
| single-transition schema/reward/rounding/done/leaf/path/target/loss tampers | Python and SP1 reject |
| minibatch claimed-loss/size/item/path/target/rounding tampers | Python and SP1 reject |

## Short-Trace Pre-ZK Benchmark

The locked short-trace benchmark remains a Python verifier result, not an SP1
trace proof.

Source:

```text
artifacts/benchmarks/short_trace_update/summary.json
artifacts/benchmarks/short_trace_update/summary.csv
```

Representative settings:

```text
sampling_rule_type = contiguous_deterministic
num_steps = 8
target_sync_every = 2
batch_size = 4 or 8
verification_passed = True
```

Representative runs:

| Run | Start offset | Batch size | Export time sec | Verify time sec | Final checkpoint SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 0 | 4 | 21.9907 | 13.4818 | `b759ddbed0b5105e0ffd23f680ddbf577fc42a911d70d1245712610d43f59bb7` |
| 1 | 32 | 4 | 23.2580 | 13.6440 | `82fefb4ba14afdc9b50bb5e2375e9283c4fedebb12d04388106eba77088bb4ec` |
| 2 | 0 | 8 | 22.4650 | 14.0169 | `01d508d753a395f578e041976f8ecdf2bbd1dbfbf8acf11bf197e3e0fefc2e1e` |

## Interpretation

Paper-facing claim:

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
