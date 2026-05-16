# Refactor Phase 11D Layout Plan Status

## Scope

Phase 11D creates a final layout design and migration matrix. It does not move,
rename, or delete files and does not change verifier logic, artifact schemas,
benchmark methodology, Rust/SP1 source code, or paper claims.

## Files Created

- `docs/final_layout_plan.md`
- `docs/path_migration_matrix.md`
- `docs/refactor_phase11d_layout_plan_status.md`
- `artifacts/README.md`
- `scripts/README.md`
- `zk_offline_dqn/artifacts/README.md`
- `zk_offline_dqn/experiments/README.md`
- `zk_offline_dqn/backends/sp1/README.md`
- `tests/regression/test_layout_documentation.py`

## Files Modified

- `docs/refactor_final_summary.md`
- `docs/legacy_status.md`
- `docs/release_checklist.md`

## Layout Findings

- `zk_offline_dqn/artifacts/` and root `artifacts/` overlap by name but not by
  role: one is code, the other is data/output.
- `zk_offline_dqn/experiments/` and `scripts/experiments/` overlap by name but
  not by role: one is report-library code, the other is executable workflows.
- `zk_offline_dqn/backends/sp1/` and `zk_backend/td_mvp/sp1/` overlap by topic
  but not by role: one is Python-side support, the other is Rust/SP1 backend.
- `src/zk_offline_dqn/` is a future skeleton and is not the active package.

## Recommendation

Use Option A from `docs/final_layout_plan.md` for submission: keep current
paths, add README notes, and do not perform structural migrations before the
artifact is reviewed.

Option B should be a post-submission cleanup with wrappers, import
compatibility, path migration tests, report regeneration, and full regression.

## Command Status

| Command | Status |
| --- | --- |
| reference search for `zk_offline_dqn.experiments` | pass; report library users identified |
| reference search for `zk_offline_dqn.artifacts` | pass; schema/IO users identified |
| reference search for `scripts/experiments` | pass; workflow users identified |
| reference search for `scripts/artifacts_export` | pass; compatibility users identified |
| reference search for `scripts/zk_proofs` | pass; legacy helper users identified |
| reference search for `artifacts/` | pass; broad direct path use confirms high migration risk |
| reference search for `src/zk_offline_dqn` | pass; skeleton users identified |
| reference search for `zk_backend` | pass; backend/test-vector users identified |
| `python -m compileall zk_offline_dqn scripts src tests` | pass |
| `python -m unittest discover tests` | pass, 126 tests |
| `python -m unittest discover tests/regression` | pass, 46 tests |
| `python scripts/experiments/check_release_readiness.py` | pass |
| `python scripts/experiments/check_report_sources.py` | pass |
| `python scripts/experiments/generate_paper_reports.py` | pass |
| `python scripts/experiments/check_paper_claims.py` | pass |
| `python scripts/experiments/check_paper_numbers_against_final_ndss.py` | pass |
| `python scripts/experiments/run_full_regression.py` | pass, 15/15 |

No files were moved, renamed, or deleted.
