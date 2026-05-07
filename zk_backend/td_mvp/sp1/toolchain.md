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

## 8. Repository Integration Plan

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

## 9. First SP1 Implementation Goal

The first real SP1 implementation should not attempt full DQN training.

It should only prove:

```text
leaf_hash == Hash(Serialize(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## 10. First SP1 Non-Goals

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

## 11. Smoke-Test Acceptance Criteria

The next SP1 workspace milestone should be considered successful if:

```text
SP1 CLI is installed
a minimal SP1 project builds
a minimal SP1 proof is generated
a minimal SP1 proof verifies
the setup steps are documented
```

## 12. TD MVP Acceptance Criteria

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

## 13. References

```text
SP1 official installation documentation
SP1 official quickstart documentation
docs/backend_selection_v0_12.md
docs/backend_choice.md
zk_backend/td_mvp/sp1/README.md
scripts/artifacts_export/verify_td_mvp_test_vector.py
```