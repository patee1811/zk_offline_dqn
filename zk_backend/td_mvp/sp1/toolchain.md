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

Native Windows check from 2026-05-12:

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
```

If the full benchmark is unstable, run one accepted proof case at a time:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-8
```

## Locked Proof Result

Latest full SP1 benchmark run:

```text
generated_at_utc = 2026-05-13T01:15:29.080668+00:00
platform = Kaggle Linux
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

| Case | Batch size | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | ---: | ---: | ---: | ---: |
| TD-1 | 1 | 168.311847 | 0.194367 | 2783354 | 383541 |
| TD-2 | 2 | 197.410724 | 0.198335 | 2787712 | 729096 |
| TD-4 | 4 | 265.605205 | 0.198736 | 2796184 | 1434680 |
| TD-8 | 8 | 349.079689 | 0.198359 | 2812912 | 2845827 |

## Phase B Forward-TD MLP Result

The Phase B relation is:

```text
forward_td_mlp_v1
```

It extends the TD backend path with fixed-point MLP forward computation,
Double-DQN argmax/value selection, model commitments, Bellman target checking,
SmoothL1 loss checking, and per-item/batch public loss claims.

Latest Kaggle SP1 benchmark run:

```text
generated_at_utc = 2026-05-13T05:30:53.407570+00:00
git_commit = 8be99d788de6fc08002fa10a48d2e63e38073992
network_spec = CartPole 4-16-16-2
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

| Case | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| forward-TD-1 | 1 | accepted | 218.364941 | 0.154355 | 2797833 | 1542507 |
| forward-TD-2 | 2 | accepted | n/a | n/a | n/a | 1956254 |

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

See `docs/phase_b_forward_td_mlp.md` for the full Phase B result snapshot.

## Non-Goals

The TD-only backend does not prove full DQN training, gradients, optimizer
updates, short traces, or recursive aggregation. Phase B now proves
micro-scale fixed-point MLP forward and argmax anchoring for TD values, but
does not prove optimizer updates or full training.
