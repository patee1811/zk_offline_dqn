# Artifact Reproducibility

This artifact is designed for a reviewer to clone the repository and run the
fast path without regenerating large proofs or raw benchmark datasets.

## Prerequisites

- Python 3.10 or compatible Python 3.9+.
- `make` on Linux, macOS, WSL2, or Kaggle.
- Python dependencies from `requirements.lock` or `requirements.txt`.
- Rust/SP1 only for optional heavy proof reruns.

## Command Table

| Command | Purpose | Expected runtime class | Primary outputs |
| --- | --- | --- | --- |
| `make reproduce-small` | Runs the reviewer fast path | minutes | tiny dataset audit, compact proof provenance check, benchmark/table checks, artifact manifest |
| `make reproduce-data-audit` | Regenerates a tiny CartPole audited commitment | minutes | `artifacts/reproducibility/data_audit/.../replay_audit_report.json`, `merkle_tree.json` |
| `make reproduce-smoke-sources` | Regenerates lightweight regression/report sources | minutes | `artifacts/regression_summary.json`, `artifacts/benchmarks/*_python_smoke/summary.json` |
| `make reproduce-sp1-proofs` | Validates compact SP1 provenance by default | seconds-minutes | report-source check over `artifacts/reports/provenance/sp1/` |
| `make reproduce-benchmarks` | Regenerates paper report snapshots from compact reports | seconds-minutes | `artifacts/reports/final_ndss/paper_numbers.json` and summary CSVs |
| `make reproduce-tamper` | Validates Table 3 by default | seconds-minutes | Table 3 source-check status |
| `make reproduce-paper-tables` | Regenerates paper-facing report snapshots | seconds | `artifacts/reports/final_ndss/` |
| `make artifact-manifest` | Regenerates hash inventories | seconds | `artifact_manifest.json`, `dataset_hashes.json`, `proof_hashes.json` |

Heavy SP1 proof generation is not part of the default reviewer path. Set
`RUN_HEAVY_SP1=1` only after installing the SP1 toolchain. Full benchmark and
tamper refreshes are similarly gated by `RUN_HEAVY_BENCHMARKS=1` and
`RUN_HEAVY_TAMPER=1`.

## Expected Outputs

The fast path produces or validates:

- dataset audit report: `artifacts/reproducibility/data_audit/cartpole-phase10-small/replay_audit_report.json`;
- dataset commitment: `artifacts/reproducibility/data_audit/cartpole-phase10-small/merkle_tree.json`;
- proof provenance checks: compact reports under `artifacts/reports/provenance/sp1/`;
- paper tables: Table 1, Table 2, and Table 3 under `artifacts/reports/final_ndss/`;
- artifact manifest: `artifacts/reports/final_ndss/artifact_manifest.json`.

## Artifact Inventory

Committed compact artifacts include final paper tables, `paper_numbers.json`,
dataset/proof hash inventories, theorem-to-artifact mapping, and SP1 compact
provenance. Raw datasets, proof binaries, receipts, and temporary proof work
directories are intentionally omitted because they are large and regenerable or
because compact public-input/provenance hashes are the paper artifact.

## Verifying Hashes

Run:

```text
make artifact-manifest
```

The manifest records SHA256 hashes for paper tables, source files, compact SP1
provenance, dataset roots, manifest hashes, and audit-report hashes. It does
not include raw dataset contents.

## What Reruns Reproduce Bit-for-Bit

Rerunning an SP1 host reproduces the *relation output* exactly and the *cost
measurements* only approximately. The two are worth separating, because only
the first is a correctness claim.

| Field | Reproducible | Depends on |
| --- | --- | --- |
| `aggregate_root`, public outputs | yes, exactly | test vector + relation code |
| `public_inputs_sha256`, `test_vector_sha256` | yes, exactly | committed inputs |
| `cycle_count` | no | the compiled guest ELF |
| `prove_time_seconds`, `verify_time_seconds` | no | machine, core count, load |
| `proof_size_bytes` | no | the compiled guest ELF |

`cycle_count` is deterministic given a fixed `(guest ELF, input)` pair, but the
guest ELF is not fixed across time. Nothing in the repository pins the
`succinct` Rust toolchain: `sp1up` installs whichever version is current, so the
same guest source compiles to a different ELF as SP1 releases move. The
`sp1_version` field records the crate version and does not capture this.

### What the committed numbers now are

Every proof-backed Table 2 row except the three `dataset_*` rows was re-measured
on the pinned toolchain (`cargo-prove d454975`, `rustc 1.93.0-dev`) from the
committed test vectors, and each carries a `guest_elf_sha256`. The three
`merkle_membership dataset_*` rows keep their earlier measurements: they are
built from `artifacts/datasets/<prefix>-<size>/`, which is generated and not in
the repository, so they cannot be reproduced from a clean clone. Their
provenance has no `guest_elf_sha256`, which is how to tell them apart.

What the re-measurement changed, and why:

| Rows | Change | Cause |
| --- | --- | --- |
| `training_aggregation_t32/t64/t128` | +13148, +20271, +42082 (~1.7%) | the guest program changed |
| `training_update`, `forward_td_mlp`, `one_step_sgd_tiny` | -34, -32, -32 | toolchain |
| `training_fragment_k1/k4/k8` | +44, +53, +48 | toolchain |
| `merkle_membership`, `short_trace` | none | reproduced exactly |

The aggregation rows are the large ones and they are not toolchain drift. Four
commits added recursive-aggregation support to that guest after the numbers were
recorded (`a89ffe7`, `d6b3c01`, `b57df3b`, `4eb519a`), so the guest carries code
the measured program did not have -- visible as the null `child_proof_mode`,
`aggregation_topology`, and `node_id` fields that appear in the newer
`public_inputs.json`. The old numbers described an older program.

The remaining deltas are tens of cycles on programs whose guest and shared
sources have not changed since their recorded commit. They vary in sign, so they
are not a fixed offset that could be corrected by scaling.

Prove and verify times moved much more than cycle counts, because the rerun used
a 16-vCPU machine rather than the original Kaggle instance. Times are machine
measurements; cycle counts are program measurements.

### Pinning the toolchain

The Cargo manifests pin the SP1 crates to `=6.1.0`, but a bare `sp1up`
installs the latest `succinct` toolchain regardless. Pin both halves:

```text
sp1up --version v6.1.0
```

CI does not install the SP1 toolchain at all -- heavy proving is outside the
Python regression -- so this pin matters only when rerunning proofs by hand.

### Detecting the mismatch

Provenance now records `guest_elf_sha256` alongside `test_vector_sha256`, so a
rerun pins both halves of the `(program, input)` pair that determines
`cycle_count`. A reviewer whose `guest_elf_sha256` differs from the committed
one should expect different cycle counts and identical relation outputs. Entries
recorded before this field was added do not carry it.

## Windows, PowerShell, Linux, and Kaggle

On Windows without `make`, run the Python commands listed in the `Makefile` or
use WSL2. On Kaggle/Linux, `make reproduce-small` is the expected reviewer
command. If an SP1 toolchain is unavailable, keep `RUN_HEAVY_SP1` unset; the
fast path still validates compact proof provenance.
