# Refactor Phase 11B Artifact Decision Status

## Scope

Phase 11B classifies remaining untracked artifact and fixture groups for
release-owner decisions. It does not change verifier logic, artifact schemas,
benchmark methodology, paper claims, Rust/SP1 source, legacy scripts, or
artifact contents.

## Files Created

- `docs/artifact_decision_manifest.md`
- `docs/refactor_phase11b_artifact_decision_status.md`
- `tests/regression/test_artifact_decision_manifest.py`

## Files Modified

- `docs/artifact_cleanup_audit.md`
- `docs/artifact_release_manifest.md`
- `docs/release_checklist.md`
- `docs/refactor_phase11a_cleanup_status.md`

## Inspection Summary

- Remaining visible untracked artifact groups include benchmark fixture
  directories, historical benchmark output folders, sample JSON artifacts,
  short-trace helper artifacts, helper Merkle/leaf-hash JSON files, and one
  checkpoint-like artifact.
- Manifest-listed canonical paths include `artifacts/sample_transition_membership.json`,
  benchmark fixtures for forward-TD MLP and one-step SGD tiny, synced
  short-trace checkpoints, the canonical model checkpoint, and
  `zk_backend/test_vectors/td_mvp_case_0.json`.
- Golden tests reference the forward-TD MLP and one-step SGD tiny fixtures, the
  membership sample artifact, and short-trace work checkpoints.
- Report generation reads final NDSS benchmark summaries and Kaggle Phase 6C
  summaries. Final report CSVs cite the benchmark fixture directories as
  provenance.
- Full regression references canonical tracked artifacts and regenerates
  ignored smoke/full-regression outputs.

## Decision Summary

- `commit_canonical_fixture`: manifest-listed/test-used fixtures and the
  canonical model checkpoint.
- `commit_release_provenance`: final report snapshots, final benchmark fixture
  directories cited by reports, and MountainCar helper Merkle/leaf-hash files
  cited by the MountainCar benchmark summary.
- `keep_local_ignore`: Kaggle output summaries and Python-smoke output
  directories used for local report/source regeneration.
- `archive_later`: large historical one-step update, short-trace update, and
  older SP1 TD MVP benchmark output folders.
- `needs_manual_review`: legacy sample TD/minibatch artifacts, helper
  leaf-hash JSONs, negative short-trace examples, and unclear checkpoint-like
  outputs.
- `do_not_touch`: SP1 backend test vectors, Rust/SP1 backend source, local
  data/model stores, and legacy scripts.

## Recommended Git Add Groups

Phase 11B did not run `git add`. Suggested release-owner commands are recorded
in `docs/artifact_decision_manifest.md`.

## Command Status

| Command | Status |
| --- | --- |
| `git status --short` | pass; remaining untracked artifact groups are classified for decision |
| `git ls-files artifacts` | pass; tracked canonical artifacts and final reports listed |
| `git ls-files artifacts/reports/final_ndss` | pass; five final reports tracked |
| `git ls-files artifacts/benchmarks` | pass; tracked summaries listed, fixture directories remain untracked |
| `git status --ignored --short` | pass; ignored generated/local outputs reviewed |
| `git clean -nd` | pass; dry-run only, no deletion |
| `git clean -ndX` | pass; dry-run only, no deletion |
| `python -m compileall zk_offline_dqn scripts src tests` | pass |
| `python -m unittest discover tests` | pass, 117 tests |
| `python -m unittest discover tests/regression` | pass, 37 tests |
| `python scripts/experiments/check_release_readiness.py` | pass |
| `python scripts/experiments/check_report_sources.py` | pass |
| `python scripts/experiments/generate_paper_reports.py` | pass |
| `python scripts/experiments/check_paper_claims.py` | pass |
| `python scripts/experiments/check_paper_numbers_against_final_ndss.py` | pass |
| `python scripts/experiments/run_full_regression.py` | pass, 15/15 |

## Release-Owner Actions

- Commit canonical fixture/provenance groups only after reviewing
  `docs/artifact_decision_manifest.md`.
- Keep Kaggle output trees and Python-smoke outputs ignored and local.
- Do not commit large historical benchmark output folders unless separately
  selected for archival.
- Do not stage artifacts automatically from this phase; review each suggested
  `git add` group first.
