# Refactor Phase 7 Reports Status

## Scope

Phase 7 adds deterministic report generation from existing regression,
benchmark, and Kaggle SP1 validation outputs. It does not change verifier
semantics, artifact schemas, benchmark methodology, paper text, or Rust/SP1
source code.

## Files Created

- `zk_offline_dqn/experiments/report_tables.py`
- `zk_offline_dqn/experiments/benchmark_manifest.py`
- `zk_offline_dqn/experiments/paper_numbers.py`
- `scripts/experiments/generate_paper_reports.py`
- `scripts/experiments/check_report_sources.py`
- `tests/regression/test_report_generation.py`
- `docs/reproducibility.md`
- `docs/refactor_phase7_reports_status.md`

## Files Modified

- `zk_offline_dqn/cli/report.py`
- `docs/dev_commands.md`
- `docs/sp1_python_alignment.md`

## Report Outputs

Generated report files are written under:

```text
artifacts/reports/final_ndss/
```

Expected files:

- `paper_numbers.json`
- `benchmark_summary.csv`
- `tamper_summary.csv`
- `sp1_status.json`
- `benchmark_snapshot.md`

## Benchmark Manifest Coverage

The Phase 7 manifest records report entries for:

- `td_mvp`
- `distinct_td`
- `forward_td_mlp`
- `one_step_sgd_tiny`
- `minibatch_td`
- `one_step_update`
- `short_trace`
- `sp1_td_mvp_execute`
- `sp1_td_mvp_prove`

Each entry records the command, fixture path, expected output path, status type,
and paper relevance. The manifest is descriptive only and does not move or
rewrite files.

## SP1 Proof Scope

The only SP1 proof validation claim represented by Phase 7 is:

```text
SP1 proof generation and verification passed on Kaggle for the TD MVP SP1
backend using zk_backend/test_vectors/td_mvp_case_0.json.
```

This does not claim proof of full DQN training, proof coverage for every
relation, recursive aggregation, or new benchmark results.

## Command Status

Phase 7 local validation completed:

```text
python -m compileall zk_offline_dqn scripts src tests
python -m unittest discover tests
python -m unittest discover tests/regression
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python -m zk_offline_dqn.cli.main report check-sources
python -m zk_offline_dqn.cli.main report generate
python scripts/experiments/run_full_regression.py
python scripts/experiments/check_sp1_environment.py
```

Results:

- Compile smoke: passed.
- Full unittest discovery: passed, 97 tests.
- Regression unittest discovery: passed, 17 tests.
- Report source check: passed.
- Report generation script: passed.
- CLI report source check: passed.
- CLI report generation: passed.
- Full regression: passed all 15 checks.
- SP1 environment diagnostic: completed; local Windows has `rustc`/`cargo`,
  but does not have `cargo prove` or `sp1up` on PATH.

## Generated Report Summary

`artifacts/reports/final_ndss/paper_numbers.json` records:

- Regression: `15/15` checks passed.
- Existing final NDSS benchmark summary: 29 benchmark rows, 21 tamper rows,
  and all four existing components passed.
- TD MVP Kaggle SP1 proof status: validated.
- Cargo prove version:
  `cargo-prove sp1 (d454975 2026-04-11T01:54:01.305546215Z)`.
- Cargo test status: passed.
- SP1 execute status: passed.
- SP1 prove status: passed.
- `execution_ok = true`.
- `cycle_count = 385048`.
- `proof_generated = true`.
- `proof_verified = true`.
- `proving_time_sec = 167.726006`.
- `verification_time_sec = 0.190326`.
- `proof_size_bytes = 2783869`.

Every paper-facing value in `paper_numbers.json` includes provenance pointing
to the source file and source field.

## Remaining Risks

- Phase 7 reports reuse existing benchmark outputs; they do not rerun heavy
  proof benchmarks or change methodology.
- The Phase 6C proof claim remains scoped to TD MVP on
  `zk_backend/test_vectors/td_mvp_case_0.json`.
- Existing final NDSS benchmark matrices are surfaced with provenance, but this
  phase does not expand paper claims.
