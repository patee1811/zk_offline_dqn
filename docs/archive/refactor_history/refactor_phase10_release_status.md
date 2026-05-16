# Refactor Phase 10 Release Status

## Scope

Phase 10 prepares release/submission documentation and release-readiness
checks. It does not change verifier logic, artifact schemas, benchmark
methodology, paper claims beyond Phase 9 hardening, or Rust/SP1 source code.

## Files Created

- `docs/release_checklist.md`
- `docs/artifact_release_manifest.md`
- `docs/refactor_phase10_release_status.md`
- `scripts/experiments/check_release_readiness.py`
- `tests/regression/test_release_readiness.py`

## Files Modified

- None outside Phase 10 status documentation.

## Git Hygiene Snapshot

Initial Phase 10 inspection found:

- Modified tracked files: Phase 6 Kaggle validation plumbing and status docs.
- Tracked final reports: `artifacts/reports/final_ndss/*`.
- Tracked Kaggle local output directories: none found by `git ls-files`.
- Tracked smoke/Kaggle/tmp/cache artifacts under `artifacts/`: none found by
  the requested `git ls-files artifacts | findstr` check.
- Untracked artifacts: multiple canonical-looking JSON/PT files and benchmark
  fixture folders require human release decision.

## Optional Cleanup

No cleanup was executed. Ignored local outputs can be removed after approval
with the commands listed in `docs/release_checklist.md`.

## Command Status

Phase 10 validation completed:

```text
python -m compileall zk_offline_dqn scripts src tests
python -m unittest discover tests
python -m unittest discover tests/regression
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python scripts/experiments/check_paper_claims.py
python scripts/experiments/check_paper_numbers_against_final_ndss.py
python scripts/experiments/check_release_readiness.py
python scripts/experiments/run_full_regression.py
```

Results:

- Compile smoke: passed.
- Full unittest discovery: passed, 106 tests.
- Regression unittest discovery: passed, 26 tests.
- Report source check: passed.
- Report generation: passed.
- Paper claim check: passed.
- Paper number check: passed.
- Release readiness check: passed.
- Full regression: passed all 15 checks.

No SP1 proof was rerun in Phase 10.

## Release Readiness Result

`scripts/experiments/check_release_readiness.py` reported:

- `release_readiness = passed`
- final reports exist, are tracked, and are not ignored
- tracked Kaggle local outputs: none
- tracked generated smoke/Kaggle/tmp/cache artifacts under `artifacts/`: none
- SP1 claim scope: `td_mvp_canonical_vector_only`

## Remaining Human Decisions

The working tree still contains untracked artifact files and benchmark fixture
folders. Some appear canonical and some are generated. A release owner should
decide which to add before the final release commit.

Recommended decision groups:

- canonical fixture artifacts required by regression/review
- generated final reports under `artifacts/reports/final_ndss/`
- docs and paper claim-hardening changes
- release-readiness tooling and tests
- Phase 6 Kaggle validation plumbing
