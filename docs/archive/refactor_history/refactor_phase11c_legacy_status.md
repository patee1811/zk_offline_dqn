# Refactor Phase 11C Legacy Status

## Scope

Phase 11C audits legacy script usage and records a retirement plan. It does not
change verifier logic, artifact schemas, benchmark methodology, paper claims,
Rust/SP1 source code, or legacy script behavior.

## Files Created

- `docs/legacy_usage_manifest.md`
- `docs/refactor_phase11c_legacy_status.md`
- `scripts/artifacts_export/README.md`
- `scripts/zk_proofs/README.md`
- `src/README.md`
- `tests/regression/test_legacy_usage_manifest.py`

## Files Modified

- `docs/legacy_status.md`
- `docs/refactor_final_summary.md`
- `docs/release_checklist.md`

## Audit Summary

- `scripts/artifacts_export/` contains 20 exporter/verifier scripts.
- Core verifier wrappers are still called by golden tests, regression smoke
  tests, benchmark scripts, negative-test runners, full regression, backend
  docs, and paper setup text.
- Exporter scripts are still used by benchmark scripts, backend docs, or legacy
  fixture regeneration workflows.
- `scripts/zk_proofs/` contains four pre-backend Merkle/data helper scripts;
  they are not part of default full regression but remain documented helper
  workflows.
- `scripts/experiments/` remains the active workflow folder for regression,
  benchmark, report, Kaggle, and release-readiness commands.
- `src/zk_offline_dqn/` remains a future package skeleton, not the active
  package import surface.

## Retirement Recommendation

- Keep all legacy scripts in place for Phase 11C.
- Prefer unified CLI commands for new user-facing verification examples.
- Do not remove old paths until their direct test, regression, benchmark, docs,
  backend, and paper users are migrated.
- If a later phase moves scripts, leave thin compatibility wrappers at old
  paths to preserve stdout markers.

## Command Status

| Command | Status |
| --- | --- |
| legacy directory listing for `scripts/artifacts_export/` | pass; 20 scripts found |
| legacy directory listing for `scripts/zk_proofs/` | pass; 4 scripts found |
| reference search for `scripts/artifacts_export` | pass; direct users found in tests, regression, benchmarks, docs, backend docs, and paper setup |
| reference search for `scripts/zk_proofs` | pass; docs/helper workflow references found |
| reference search for `verify_`, `subprocess`, and `src/zk_offline_dqn` | pass; usage recorded in manifest |
| `python -m compileall zk_offline_dqn scripts src tests` | pass |
| `python -m unittest discover tests` | pass, 122 tests |
| `python -m unittest discover tests/regression` | pass, 42 tests |
| `python scripts/experiments/check_release_readiness.py` | pass |
| `python scripts/experiments/check_report_sources.py` | pass |
| `python scripts/experiments/generate_paper_reports.py` | pass |
| `python scripts/experiments/check_paper_claims.py` | pass |
| `python scripts/experiments/check_paper_numbers_against_final_ndss.py` | pass |
| `python scripts/experiments/run_full_regression.py` | pass, 15/15 |
