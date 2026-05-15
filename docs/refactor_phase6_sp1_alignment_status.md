# Refactor Phase 6 SP1 Alignment Status

## Files Created

- `zk_offline_dqn/backends/sp1/fixtures.py`
- `zk_offline_dqn/backends/sp1/commands.py`
- `zk_offline_dqn/backends/sp1/metrics.py`
- `scripts/experiments/check_sp1_environment.py`
- `scripts/experiments/kaggle_sp1_validation.py`
- `scripts/experiments/setup_sp1_on_kaggle.sh`
- `scripts/experiments/run_phase6_kaggle_validation.py`
- `tests/regression/test_sp1_python_schema_alignment.py`
- `docs/sp1_python_alignment.md`
- `docs/refactor_phase6_sp1_alignment_status.md`

## Files Modified

- `docs/dev_commands.md`

## Backend Discovery

- SP1 workspace: `zk_backend/td_mvp/sp1/`
- Host package: `td-mvp-host`
- Guest package: `td-mvp-guest`
- Shared package: `td-mvp-shared`
- Canonical input: `zk_backend/test_vectors/td_mvp_case_0.json`
- Host execute command: `cargo run --release -p td-mvp-host -- --execute`
- Host prove command: `cargo run --release -p td-mvp-host -- --prove`

## Kaggle Kernel

- Matching `zkp-drl` kernel: `nypate9999/zkp-drl`.
- Kernel folder used locally: `kaggle_phase6_zkp_drl/`.
- Backup folder: `kaggle_phase6_zkp_drl_backup/`.
- Pushed kernel version: version 5.

## Kaggle Commands Run

```text
kaggle kernels list --mine
kaggle kernels list --mine --search zkp-drl
kaggle kernels pull nypate9999/zkp-drl -p kaggle_phase6_zkp_drl -m
kaggle kernels push -p kaggle_phase6_zkp_drl
kaggle kernels status nypate9999/zkp-drl
kaggle kernels output nypate9999/zkp-drl -p kaggle_phase6_outputs
```

The Kaggle executable used by the launcher was:

```text
C:\Users\Ngoc Duy\AppData\Roaming\Python\Python310\Scripts\kaggle.exe
```

## Kaggle Output Summary

Kaggle completed version 5 and produced:

```text
kaggle_phase6_outputs/zk_offline_dqn/artifacts/reports/kaggle_sp1_validation_summary.json
```

The output download timed out while copying the full cloned repository output
tree, but the JSON validation summary was retrieved.

Summary:

- Repo discovery: cloned `https://github.com/patee1811/zk_offline_dqn.git`,
  branch `cleanup-project-structure`, into `/kaggle/working/zk_offline_dqn`.
- Compile smoke: pass.
- `python -m unittest discover tests/regression`: fail because the cloned
  branch did not expose an importable `tests/regression` package.
- Unified CLI TD MVP command: fail because the cloned branch did not expose
  `zk_offline_dqn.cli`.
- Distinct TD Python smoke: pass, `all_passed = True`.
- Forward-TD MLP Python smoke: pass, `all_passed = True`.
- One-step SGD tiny Python smoke: pass, `all_passed = True`.
- Environment diagnostic: pass as a diagnostic, but Rust/Cargo/SP1 tools were
  not present in this executed Kaggle kernel.

## Rust/SP1 Status

- Local Windows diagnostic found `rustc` and `cargo`.
- Local Windows diagnostic did not find `cargo prove` or `sp1up`.
- Kaggle version 5 diagnostic reported `cargo_available = false`.
- Kaggle `cargo test`, SP1 execute, and SP1 prove were skipped because Cargo
  was unavailable in the executed kernel.
- SP1 prove was not requested because `RUN_SP1_PROVE=1` was not set.

## Python Smoke Status

- `python -m compileall zk_offline_dqn scripts src tests`: pass.
- `python -m unittest discover tests`: pass, 94 tests.
- `python -m unittest discover tests/regression`: pass, 14 tests.
- `python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json`: pass.
- `python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke`: pass.
- `python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke`: pass.
- `python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke`: pass.
- `python scripts/experiments/check_sp1_environment.py`: pass as a diagnostic.

## Full Regression Status

`python scripts/experiments/run_full_regression.py` passed all 15 checks:

```text
all_regression_passed = True
```

## Remaining Backend Risks

- Python regression pass does not imply SP1 proof generation works.
- The Kaggle API path validated the Python benchmark smoke checks, but it did
  not validate Rust/SP1 execute or prove because Cargo was unavailable in the
  executed kernel.
- The Kaggle validation cloned the existing remote branch referenced by the
  user's notebook, not the uncommitted local Phase 6 workspace.
- Proof mode remains opt-in through `RUN_SP1_PROVE=1`.
- Future schema or commitment changes must keep Python fixtures and Rust shared
  structs aligned.
