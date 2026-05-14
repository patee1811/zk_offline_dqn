# SP1 Toolchain Notes

SP1 is the concrete backend for the TD MVP. Native Windows PowerShell is useful
for Python regression, but SP1 proof generation should be run on Linux, macOS,
WSL2 Ubuntu, or Kaggle.

## Required Tools

```text
Git
Rust and Cargo
SP1 / cargo-prove toolchain
Docker if required by the installed SP1 flow
Protocol Buffers compiler if required by the installed SP1 flow
```

## Local Environment Notes

Native Windows notes:

```text
SP1 CLI: not available to the Codex Windows session
WSL: no Codex-visible installed distribution
```

The full SP1 proof benchmark was therefore refreshed on Kaggle.

## Canonical Commands

From `zk_backend/td_mvp/sp1/`:

```bash
cargo check -p td-mvp-shared -p td-mvp-host
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
bash run_negative_cases.sh
```

From the repository root:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
python3 scripts/experiments/run_final_ndss_regression.py
```

If the full benchmark is unstable, run one accepted proof case at a time:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-8
```

## Proof Result

Full SP1 benchmark run:

```text
platform = Kaggle Linux SP1
benchmark_rows = 29
tamper_rows = 21
all_components_passed = True
```

| Relation | Case | Batch size | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Distinct TD | TD-1 | 1 | 97.955756 | 0.126565 | 2783869 | 385048 |
| Distinct TD | TD-2 | 2 | 120.669043 | 0.127258 | 2788227 | 730778 |
| Distinct TD | TD-4 | 4 | 141.309797 | 0.125481 | 2796699 | 1435787 |
| Distinct TD | TD-8 | 8 | 202.921645 | 0.126658 | 2812915 | 2845813 |
| CartPole forward-TD | forward-TD-1 | 1 | 148.418458 | 0.127259 | 2797833 | 1543753 |
| MountainCar forward-TD | mountaincar-forward-TD-1 | 1 | 107.926506 | 0.126694 | 2787889 | 683942 |
| CartPole one-step SGD tiny | one-step-SGD-tiny-1 | 1 | 115.494141 | 0.125332 | 2789940 | 862136 |

## Forward-TD MLP Result

The relation is:

```text
forward_td_mlp_v1
```

It extends the TD backend path with fixed-point MLP forward computation,
Double-DQN argmax/value selection, model commitments, Bellman target checking,
SmoothL1 loss checking, and per-item/batch public loss claims.

Kaggle SP1 benchmark run:

```text
network_spec = CartPole 4-16-16-2
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

| Case | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| forward-TD-1 | 1 | accepted | 148.418458 | 0.127259 | 2797833 | 1543753 |
| forward-TD-2 | 2 | accepted | n/a | n/a | n/a | 1957958 |

Tamper cases rejected under SP1 execute:

```text
tamper_online_model_weight
tamper_target_model_weight
tamper_activation
tamper_relu_mask
tamper_argmax
tamper_selected_target_value
tamper_claimed_batch_loss
```

See `docs/forward_td_mlp_result.md` for the full result snapshot.

## One-Step SGD Tiny Result

The relation is:

```text
one_step_sgd_tiny_v1
```

It extends the backend path with a micro-scale fixed-point SGD update over a
one-hidden-layer Q-network. The relation checks committed transition
membership, forward-TD, SmoothL1 derivative, backprop gradients, SGD deltas,
post-update model equality, and pre/target/post model commitments.

Kaggle SP1 benchmark run:

```text
network_spec = CartPole 4-8-2
learning_rate_fp = 100
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

| Case | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | ---: | ---: | ---: |
| one-step-SGD-tiny-1 | accepted | 115.494141 | 0.125332 | 2789940 | 862136 |

Tamper cases rejected under SP1 execute:

```text
tamper_gradient_tensor
tamper_delta_tensor
tamper_learning_rate_fp
tamper_post_model_weight
tamper_post_model_commitment
tamper_smooth_l1_grad
```

See `docs/one_step_sgd_tiny_result.md` for the full result snapshot.

## Non-Goals

The backend does not prove full DQN training, Adam, target synchronization,
recursive aggregation, or a long training trace.
