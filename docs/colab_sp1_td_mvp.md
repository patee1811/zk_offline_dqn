# Google Colab SP1 TD MVP Runbook

This runbook targets Colab Linux runtimes for reproducing the SP1 TD MVP
single-transition and minibatch proof commands.

SP1 runs natively on Linux/macOS. The official SP1 v6 installation path uses
`sp1up`, then verifies `cargo prove --version` and `cargo +succinct --version`.
This project pins SP1 crates to `6.1.0`, so the commands below install the
matching SP1 toolchain when possible.

## 1. Runtime Setup

Use a High-RAM Colab runtime if available. TD-4 and TD-8 proving may exceed
free-tier memory or disconnect limits.

```bash
!nproc
!free -h
!df -h
```

## 2. Install System Dependencies

```bash
!sudo apt-get update
!sudo apt-get install -y \
  build-essential \
  pkg-config \
  libssl-dev \
  protobuf-compiler \
  curl \
  git \
  clang \
  lld
```

## 3. Install Rust

```bash
!curl https://sh.rustup.rs -sSf | sh -s -- -y
```

For later notebook cells:

```bash
import os
os.environ["PATH"] = f"{os.environ['HOME']}/.cargo/bin:{os.environ['PATH']}"
```

Check Rust:

```bash
!rustc --version
!cargo --version
```

## 4. Install SP1

```bash
!curl -L https://sp1up.succinct.xyz | bash
```

Add SP1 to the notebook PATH:

```bash
import os
home = os.environ["HOME"]
os.environ["PATH"] = f"{home}/.sp1/bin:{home}/.cargo/bin:{os.environ['PATH']}"
```

Install the SP1 toolchain. Use the pinned version first; if that fails because
the installer no longer exposes the exact tag, run plain `sp1up`.

```bash
!sp1up -v 6.1.0 || sp1up
```

Verify:

```bash
!cargo prove --version
!cargo +succinct --version
!protoc --version
```

## 5. Clone Repository

```bash
!git clone --branch cleanup-project-structure https://github.com/patee1811/zk_offline_dqn.git
%cd /content/zk_offline_dqn
```

## 6. Python Semantic Oracle

```bash
!python3 scripts/artifacts_export/verify_td_mvp_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json

!python3 scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```

## 7. Rust/SP1 Build Checks

```bash
%cd /content/zk_offline_dqn/zk_backend/td_mvp/sp1
!cargo fmt --check
!cargo check -p td-mvp-shared -p td-mvp-host
```

## 8. Single-Transition TD-1 Proof

```bash
!cargo run --release -p td-mvp-host -- --execute
!cargo run --release -p td-mvp-host -- --prove
```

## 9. TD-2 Minibatch Proof

```bash
%cd /content/zk_offline_dqn
!python3 scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json \
  --out /tmp/td_mvp_batch_size_2.json \
  --batch-size 2

!python3 scripts/artifacts_export/verify_td_mvp_test_vector.py \
  --input /tmp/td_mvp_batch_size_2.json

%cd /content/zk_offline_dqn/zk_backend/td_mvp/sp1
!cargo run --release -p td-mvp-host -- \
  --input /tmp/td_mvp_batch_size_2.json \
  --execute \
  --prove
```

## 10. TD-4 Proof Attempt

Run TD-4 directly, not through the full benchmark matrix, to reduce memory
pressure.

```bash
%cd /content/zk_offline_dqn
!python3 scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json \
  --out /tmp/td_mvp_batch_size_4.json \
  --batch-size 4

!python3 scripts/artifacts_export/verify_td_mvp_test_vector.py \
  --input /tmp/td_mvp_batch_size_4.json

%cd /content/zk_offline_dqn/zk_backend/td_mvp/sp1
!cargo run --release -p td-mvp-host -- \
  --input /tmp/td_mvp_batch_size_4.json \
  --execute \
  --prove
```

## 11. TD-8 Proof Attempt

Only run TD-8 after TD-4 succeeds. If TD-4 disconnects the runtime, treat TD-8
as requiring a larger VM.

```bash
%cd /content/zk_offline_dqn
!python3 scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json \
  --out /tmp/td_mvp_batch_size_8.json \
  --batch-size 8

!python3 scripts/artifacts_export/verify_td_mvp_test_vector.py \
  --input /tmp/td_mvp_batch_size_8.json

%cd /content/zk_offline_dqn/zk_backend/td_mvp/sp1
!cargo run --release -p td-mvp-host -- \
  --input /tmp/td_mvp_batch_size_8.json \
  --execute \
  --prove
```

## 12. Benchmark Runner

Use the full runner only after the direct proof commands work.

```bash
%cd /content/zk_offline_dqn
!python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-2
!python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-4
!python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-8
```

## 13. Outputs To Save

Copy these values from stdout:

```text
proof_generated = true
proof_verified = true
proving_time_sec = ...
verification_time_sec = ...
proof_size_bytes = ...
cycle_count = ...
```
