# SP1 Toolchain Notes

## 1. Purpose

This document records the planned SP1 toolchain setup for the TD MVP backend.

The current milestone is documentation-only. It does not install SP1 into the repository, add Rust dependencies, or generate a proof yet.

The next implementation milestones should use this document as the setup checklist before creating a buildable SP1 workspace.

## 2. Backend Context

The selected first backend is:

```text
SP1
```

The first target relation is the TD MVP relation:

```text
Merkle membership
Bellman target
TD error
SmoothL1 TD loss
claimed target/loss consistency
```

The current compatibility target is:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

The current Python reference verifier is:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
```

## 3. Platform Recommendation

SP1 should be set up first on:

```text
Linux or macOS
```

For Windows development, the recommended path is:

```text
WSL2 Ubuntu
```

Reason:

```text
The official SP1 installation documentation states that SP1 currently runs natively on Linux and macOS.
```

Therefore, this project should avoid relying on native Windows PowerShell for the first SP1 proof milestone.

## 4. Required Tools

Before installing SP1, the development environment should have:

```text
Git
Rust
Docker
Protocol Buffers compiler (protoc)
```

These are listed as SP1 installation requirements in the official SP1 documentation.

## 5. Installation Path

The preferred installation path is the official SP1 installer:

```text
sp1up
```

The SP1 documentation describes two installation options:

```text
1. prebuilt binaries through sp1up
2. build the Succinct Rust toolchain and SP1 CLI from source
```

For this project, use the prebuilt `sp1up` path first unless there is a specific reason to build from source.

## 6. Quickstart Reference

The official SP1 quickstart creates a new project with:

```bash
cargo prove new --bare <name>
```

For this repository, the future SP1 workspace should be created under:

```text
zk_backend/td_mvp/sp1/
```

The exact command should be tested in a clean temporary directory first before modifying the repository layout.

## 7. Proposed Local Setup Flow

On WSL2 Ubuntu or Linux/macOS:

```bash
# 1. Check basic tools
git --version
rustc --version
cargo --version
docker --version
protoc --version

# 2. Install SP1 using the official installer
# Follow the current official SP1 installation page.

# 3. Check SP1 CLI
cargo prove --help

# 4. Create a temporary hello-world project outside this repo
mkdir -p ~/tmp/sp1-smoke
cd ~/tmp/sp1-smoke
cargo prove new --bare hello_sp1

# 5. Build/run the generated example according to the SP1 quickstart
cd hello_sp1
```

The first successful local smoke test should confirm:

```text
cargo prove CLI is installed
a generated SP1 project builds
a generated SP1 example can prove and verify
```

## 8. Current Local Setup Check

Checked on 2026-05-11 from the repository's native Windows PowerShell
environment.

```text
OS: Microsoft Windows 10.0.26200.8246
Shell: Windows PowerShell 5.1.26100.8115
CPU: Intel64 Family 6 Model 183 Stepping 1, GenuineIntel
Logical processors: 20
Git: git version 2.49.0.windows.1
Rust: rustc 1.94.0, cargo 1.94.0
SP1 CLI: cargo prove is not installed
Docker: not found on PATH
protoc: not found on PATH
WSL: WSL2 is the default version, but no Linux distribution is installed
```

Additional access note:

```text
The developer's interactive Windows account reports an Ubuntu WSL2 distro:
Ubuntu, Stopped, Version 2.

The Codex process runs as desktop-eonddfu\codexsandboxoffline. WSL distro
registrations are per Windows user, so this process cannot see or enter the
developer account's Ubuntu distro. `wsl -d Ubuntu` from Codex returns
WSL_E_DISTRO_NOT_FOUND.

An attempt to register a separate `Ubuntu-Codex` distro for the Codex account
was not approved, so Codex cannot directly enter WSL from this session.
```

Manual WSL Ubuntu smoke test:

```text
Run date: 2026-05-11
Runner: user `duy` inside WSL2 Ubuntu
Project path: /home/duy/tmp/sp1-smoke/hello_sp1

OS: Ubuntu 26.04 LTS (resolute)
CPU: 13th Gen Intel(R) Core(TM) i7-13650HX
Memory: 11 GiB total, 10 GiB available at check time
Swap: 3.0 GiB total
rustc: rustc 1.95.0 (59807616e 2026-04-14)
cargo: cargo 1.95.0 (f2d3ce0bd 2026-03-21)
Docker: Docker version 29.1.3, build 29.1.3-0ubuntu4.1
protoc: libprotoc 3.21.12
SP1 CLI: cargo-prove sp1 (d454975 2026-04-11T01:54:01.305546215Z)
```

Command:

```bash
cd "$HOME/tmp/sp1-smoke/hello_sp1"
cargo run --release -- --prove
```

Result:

```text
Finished `release` profile [optimized] target(s) in 1.31s
Running `target/release/fibonacci --prove`
n: 20
Successfully generated proof!
Successfully verified proof!
```

Conclusion:

```text
SP1 hello-world proof gate passed in the developer's WSL2 Ubuntu environment.
Codex cannot directly access that distro because it runs under a separate
Windows sandbox account, so future SP1 commands either need to be run manually
inside the developer distro or through a Codex-visible distro.
```

## 9. Repository Integration Plan

After the external smoke test works, the next milestone should create a buildable workspace under:

```text
zk_backend/td_mvp/sp1/
```

Expected future layout:

```text
zk_backend/td_mvp/sp1/
  Cargo.toml
  host/
    Cargo.toml
    src/main.rs
  guest/
    Cargo.toml
    src/main.rs
  shared/
    Cargo.toml
    src/lib.rs
```

This layout may be adjusted to match the current SP1 template.

## 10. First SP1 Implementation Goal

The first real SP1 implementation should not attempt full DQN training.

It should only prove:

```text
leaf == SerializeTransition(transition)
leaf_hash == SHA256(CanonicalLeafEncoding(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## 11. First SP1 Non-Goals

The first SP1 implementation should not prove:

```text
full DQN training
neural-network forward pass
argmax action selection
gradient computation
optimizer update
short trace chaining
recursive proof aggregation
```

## 12. Smoke-Test Acceptance Criteria

The next SP1 workspace milestone should be considered successful if:

```text
SP1 CLI is installed
a minimal SP1 project builds
a minimal SP1 proof is generated
a minimal SP1 proof verifies
the setup steps are documented
```

## 13. TD MVP Acceptance Criteria

The later TD MVP proof milestone should be considered successful if:

```text
host loads or embeds td_mvp_case_0.json
guest verifies the TD MVP relation
valid test vector produces a proof
proof verifies successfully
tampered input is rejected or fails proving
proving time is recorded
verification time is recorded
proof size is recorded
```

Current TD MVP smoke result, recorded on 2026-05-11 in WSL2 Ubuntu:

```text
valid proof generated and verified
proving_time_sec = 69.608704
verification_time_sec = 0.088708
proof_size_bytes = 2782588
initial negative cases passed:
  tamper_reward
  tamper_done
  tamper_merkle_path
  tamper_claimed_target_fp
  tamper_claimed_loss_fp
```

## 14. References

```text
SP1 official installation documentation
SP1 official quickstart documentation
docs/backend_selection_v0_12.md
docs/backend_choice.md
zk_backend/td_mvp/sp1/README.md
zk_backend/td_mvp/sp1/tamper_checklist.md
scripts/artifacts_export/verify_td_mvp_test_vector.py
```
