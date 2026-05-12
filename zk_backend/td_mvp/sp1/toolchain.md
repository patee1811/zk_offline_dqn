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
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

If the full benchmark is unstable, run one accepted proof case at a time:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-8
```

## Locked Proof Result

Latest full SP1 benchmark run:

```text
generated_at_utc = 2026-05-12T12:37:34.964280+00:00
platform = Kaggle Linux
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_sp1_negative_cases_passed = true
```

| Case | Batch size | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | ---: | ---: | ---: | ---: |
| TD-1 | 1 | 142.324547 | 0.157464 | 2782625 | 382915 |
| TD-2 | 2 | 154.923089 | 0.157712 | 2787687 | 725309 |
| TD-4 | 4 | 188.501940 | 0.155969 | 2795631 | 1425790 |
| TD-8 | 8 | 275.077262 | 0.157424 | 2812327 | 2834727 |

## Non-Goals

This backend does not prove full DQN training, neural-network forward passes,
argmax action selection, gradients, optimizer updates, short traces, or
recursive aggregation.
