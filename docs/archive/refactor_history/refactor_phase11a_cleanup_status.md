# Refactor Phase 11A Cleanup Status

## Scope

Phase 11A performs safe generated-output cleanup and artifact classification.
It does not change verifier logic, artifact schemas, benchmark methodology,
paper claims, Rust/SP1 source code, or legacy scripts.

## Files Created

- `docs/artifact_cleanup_audit.md`
- `docs/refactor_phase11a_cleanup_status.md`
- `tests/regression/test_artifact_cleanup_policy.py`

## Files Modified

- `.gitignore`

## Initial Git/Audit Result

- Tracked Kaggle local outputs: none.
- Tracked final reports: all five files under `artifacts/reports/final_ndss/`.
- Tracked generated smoke/Kaggle/tmp/cache artifacts under `artifacts/`: none
  found by the requested `git ls-files artifacts | findstr` check.
- Ignored generated local outputs: Kaggle folders, Python smoke benchmark
  directories, full-regression logs, caches, local data/model output, and LaTeX
  build products.
- Untracked not-ignored artifacts remain and are classified in
  `docs/artifact_cleanup_audit.md` for human release decision.

## Cleanup Actions

- Removed ignored pulled Kaggle kernel work folders:
  - `kaggle_phase6_zkp_drl/`
  - `kaggle_phase6_zkp_drl_backup/`
  - `kaggle_phase6_zkp_drl_backup_*/`
- Removed ignored `artifacts/full_regression/`; the full regression recreates
  it as local output.
- Removed Python `__pycache__/` directories under source, script, and test
  trees.
- Did not remove `kaggle_phase6_outputs/` because Phase 7 report generation can
  use the Phase 6C summary JSON files as provenance.
- Did not remove `artifacts/benchmarks/*_python_smoke/` because current report
  source checks expect those smoke summaries unless they are regenerated.
- Did not remove untracked benchmark fixtures, sample artifacts, short-trace
  artifacts, model/data files, paper build products, or SP1 backend outputs.

## Gitignore Changes

- Kept Kaggle work/output folders, Python smoke outputs, full-regression logs,
  caches, and local Kaggle archive zips ignored.
- Kept `artifacts/reports/final_ndss/` explicitly unignored so final report
  snapshots remain trackable.
- Replaced the broad `models/` directory ignore with `models/*` plus an
  explicit unignore for the manifest-listed canonical checkpoint
  `models/offline_dqn_with_target_seed42_best.pt`.

## Command Status

| Command | Status |
| --- | --- |
| `git status --short` | pass; untracked artifact groups remain for human decision |
| `git ls-files kaggle_phase6_outputs kaggle_phase6_zkp_drl kaggle_phase6_zkp_drl_backup` | pass; no tracked Kaggle local outputs |
| `git ls-files artifacts/reports/final_ndss` | pass; five final reports tracked |
| `git ls-files artifacts/benchmarks` | pass; tracked benchmark summaries listed, fixture directories remain untracked |
| `git status --ignored --short` | pass; ignored generated/local outputs documented |
| `git clean -nd` | pass; dry-run only, no deletion |
| `git clean -ndX` | pass; dry-run only, no deletion |
| `python -m compileall zk_offline_dqn scripts src tests` | pass |
| `python -m unittest discover tests` | pass, 112 tests |
| `python -m unittest discover tests/regression` | pass, 32 tests |
| `python scripts/experiments/check_release_readiness.py` | pass |
| `python scripts/experiments/check_report_sources.py` | pass |
| `python scripts/experiments/generate_paper_reports.py` | pass |
| `python scripts/experiments/check_paper_claims.py` | pass |
| `python scripts/experiments/check_paper_numbers_against_final_ndss.py` | pass |
| `python scripts/experiments/run_full_regression.py` | pass, 15/15 |

## Remaining Human Decisions

The following visible untracked groups remain intentionally untouched:

- benchmark fixture directories under `artifacts/benchmarks/*/fixtures/`
- historical benchmark output folders including `artifacts/benchmarks/one_step_update/`,
  `artifacts/benchmarks/short_trace_update/`, and
  `artifacts/benchmarks/sp1_td_mvp/`
- sample and helper artifacts under `artifacts/sample_*.json`,
  `artifacts/*leaf_hashes.json`, `artifacts/*merkle.json`, and
  `artifacts/td_sample_from_dataset.json`
- short-trace generated artifacts under `artifacts/short_trace_*` and
  `artifacts/short_trace_*_work/`
- Phase 10 release docs/scripts/tests that are still untracked in this local
  worktree

Phase 11B adds `docs/artifact_decision_manifest.md` to classify these groups as
commit candidates, local ignored provenance, archive-later outputs, or manual
review items.

No canonical artifacts, final reports, paper files, SP1/Rust source files, or
legacy scripts were deleted.
