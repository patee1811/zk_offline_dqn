# Artifact Decision Manifest

Phase 11B classifies remaining untracked artifact and fixture groups for a
release-owner decision. This document is descriptive only: no artifacts are
staged, moved, or deleted by this phase.

## Decision Classes

- `commit_canonical_fixture`: required by the artifact manifest, tests, or
  regression-critical entrypoints.
- `commit_release_provenance`: needed to make committed report numbers or
  benchmark summaries inspectable.
- `keep_local_ignore`: useful local provenance or generated output that should
  not be committed.
- `delete_local_safe`: generated local output that can be removed after explicit
  path review.
- `archive_later`: large historical output that may be worth external archival
  but should not be committed automatically.
- `needs_manual_review`: ambiguous artifact; release owner should inspect
  content, size, and paper relevance before adding or ignoring.
- `do_not_touch`: source, canonical backend files, or local data/model stores
  that should not be changed in this cleanup phase.

## Artifact Decisions

| Path pattern | Classification | Reason | Referenced by | Recommended action | Commit? |
| --- | --- | --- | --- | --- | --- |
| `artifacts/reports/final_ndss/` | commit_release_provenance | Final paper-facing report snapshot with provenance. | report generation, release readiness, paper-number checks | Keep tracked and commit with report code/docs. | yes |
| `artifacts/fixtures/minibatch_td/distinct_td_sp1/` | commit_release_provenance | Final benchmark and tamper summaries cite these accepted/tamper fixtures. | `artifacts/reports/final_ndss/*.csv`, `artifacts/benchmarks/final_ndss/source_summaries/distinct_td_sp1/summary.json` | Commit if final benchmark report provenance is part of release. | yes |
| `artifacts/fixtures/forward_td_mlp/` | commit_canonical_fixture | Valid fixtures are manifest-listed and golden tests use batch size 1; tamper fixtures support report provenance. | artifact manifest, golden tests, final reports | Commit the fixture directory with final benchmark reports. | yes |
| `artifacts/fixtures/one_step_sgd_tiny/` | commit_canonical_fixture | Valid fixture is manifest-listed and golden tests use it; tamper fixtures support report provenance. | artifact manifest, golden tests, final reports | Commit the fixture directory with final benchmark reports. | yes |
| `artifacts/fixtures/forward_td_mlp/mountaincar/` | commit_release_provenance | MountainCar final benchmark rows cite these fixtures. | final reports, `benchmark_mountaincar_forward_td_sp1.py` | Commit if MountainCar rows remain in final reports. | yes |
| `artifacts/benchmarks/one_step_update/` | archive_later | Large historical benchmark output with checkpoints and JSON artifacts; not consumed by current final reports. | `benchmark_one_step_update.py` output convention | Keep out of the release commit unless separately selected. Archive externally if needed. | no |
| `artifacts/benchmarks/short_trace_update/` | archive_later | Large historical trace benchmark output, including very long path names; not consumed by current final reports. | `benchmark_short_trace_update.py` output convention | Do not commit automatically. Archive externally or regenerate on demand. | no |
| `artifacts/benchmarks/sp1_td_mvp/` | archive_later | Older SP1 TD MVP benchmark output; current validated proof provenance is Phase 6C Kaggle summary and final reports. | `benchmark_sp1_td_mvp.py` output convention | Keep local or archive externally; do not commit by default. | no |
| `artifacts/fixtures/membership/sample_transition_membership.json` | commit_canonical_fixture | Manifest-listed canonical fixture and default membership verifier artifact. | artifact manifest, golden tests, membership verifier docs | Commit with canonical artifacts. | yes |
| `artifacts/fixtures/minibatch_td/sample_minibatch_td_artifact.json` | needs_manual_review | Legacy exporter template/output, not current manifest-listed canonical fixture. | `export_minibatch_td_artifact.py` | Inspect before committing; prefer current `artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json` for regression. | no |
| `artifacts/fixtures/td_mvp/sample_td_artifact.json` | needs_manual_review | Legacy TD sample output, not used by current regression. | `export_td_sample_artifact.py` output convention | Keep for manual compatibility review. | no |
| `artifacts/fixtures/td_mvp/td_sample_from_dataset.json` | needs_manual_review | Legacy verifier default, but not manifest-listed or used by full regression. | `verify_td_sample_artifact.py` | Commit only if legacy TD sample verification remains a release-supported entrypoint. | no |
| `artifacts/fixtures/membership/cartpole_dqn_eps010_leaf_hashes.json` | needs_manual_review | Helper leaf-hash file used by legacy Merkle/export scripts. | `scripts/zk_proofs/*`, `export_transition_membership_artifact.py` | Keep for manual compatibility review; do not delete. | no |
| `artifacts/fixtures/forward_td_mlp/mountaincar/mountaincar_random_seed42_leaf_hashes.json` | commit_release_provenance | MountainCar benchmark summary records this path as source provenance. | `artifacts/benchmarks/final_ndss/source_summaries/second_env_mountaincar/summary.json`, benchmark script | Commit if MountainCar final report rows are committed. | yes |
| `artifacts/fixtures/forward_td_mlp/mountaincar/mountaincar_random_seed42_merkle.json` | commit_release_provenance | MountainCar benchmark summary records this path as source provenance. | `artifacts/benchmarks/final_ndss/source_summaries/second_env_mountaincar/summary.json`, benchmark script | Commit if MountainCar final report rows are committed. | yes |
| `artifacts/one_step_update_c1_test.pt` | needs_manual_review | Checkpoint-like artifact with unclear current references. | no current code reference found | Keep local until owner decides; do not commit automatically. | no |
| `artifacts/short_trace_negative_test_*.json` | needs_manual_review | Negative-test helper artifacts; generated negative outputs are otherwise ignored. | historical/manual negative test inspection | Keep local unless release owner wants visible negative examples. | no |
| `artifacts/short_trace_seeded_*.json` | needs_manual_review | Seeded short-trace helper/tamper artifacts, not current manifest-listed canonical artifact except tracked `short_trace_seeded_artifact.json`. | historical/manual short-trace checks | Keep local for review; do not commit automatically. | no |
| `artifacts/fixtures/short_trace/short_trace_work/` | commit_canonical_fixture | Manifest lists synced checkpoint under this folder; untracked step artifact JSONs are intermediate helpers. | artifact manifest, full regression, short-trace negative runner | Commit only manifest-listed checkpoint files; review untracked JSON helpers separately. | partial |
| `artifacts/fixtures/short_trace/short_trace_seeded_work/` | commit_canonical_fixture | Manifest lists synced checkpoint under this folder; untracked step artifact JSONs are intermediate helpers. | artifact manifest, full regression, short-trace negative runner | Commit only manifest-listed checkpoint files; review untracked JSON helpers separately. | partial |
| `models/offline_dqn_with_target_seed42_best.pt` | commit_canonical_fixture | Manifest-listed checkpoint used by full regression and short-trace checks. | artifact manifest, full regression | Keep tracked/trackable; do not ignore. | yes |
| `kaggle_phase6_outputs/` | delete_local_safe | Local downloaded Kaggle output tree; SP1 summaries are now snapshotted under `artifacts/reports/provenance/sp1/`. | Kaggle validation launcher output only | Delete locally after report checks pass. Do not commit. | no |
| `artifacts/benchmarks/*_python_smoke/` | keep_local_ignore | Generated Python smoke outputs used by source checks; regenerated by full regression. | benchmark manifest, report source check | Keep local or regenerate; do not commit. | no |
| `artifacts/full_regression/` | delete_local_safe | Generated stdout/stderr logs regenerated by full regression. | full regression output only | Safe to remove after explicit path review. | no |
| `zk_backend/test_vectors/` | do_not_touch | Canonical SP1 backend test vectors. | artifact manifest, SP1 backend, CLI smoke | Do not move, ignore, or delete. | already tracked |

## Recommended Git Add Groups

These are recommendations only; Phase 11B does not stage files.

Canonical fixtures:

```text
git add artifacts/fixtures/membership/sample_transition_membership.json
git add artifacts/fixtures/forward_td_mlp/
git add artifacts/fixtures/one_step_sgd_tiny/
git add models/offline_dqn_with_target_seed42_best.pt
```

Final report provenance fixtures, if the release includes the current final
benchmark tables:

```text
git add artifacts/fixtures/minibatch_td/distinct_td_sp1/
git add artifacts/fixtures/forward_td_mlp/mountaincar/
git add artifacts/fixtures/forward_td_mlp/mountaincar/mountaincar_random_seed42_leaf_hashes.json
git add artifacts/fixtures/forward_td_mlp/mountaincar/mountaincar_random_seed42_merkle.json
git add artifacts/reports/final_ndss/
```

Keep local and ignored:

```text
artifacts/archive/manual_review/
kaggle_phase6_outputs/
artifacts/benchmarks/*_python_smoke/
artifacts/full_regression/
```

Manual-review queue:

```text
artifacts/fixtures/minibatch_td/sample_minibatch_td_artifact.json
artifacts/fixtures/td_mvp/sample_td_artifact.json
artifacts/fixtures/td_mvp/td_sample_from_dataset.json
artifacts/fixtures/membership/cartpole_dqn_eps010_leaf_hashes.json
artifacts/one_step_update_c1_test.pt
artifacts/short_trace_negative_test_*.json
artifacts/short_trace_seeded_*.json
artifacts/benchmarks/one_step_update/
artifacts/benchmarks/short_trace_update/
artifacts/benchmarks/sp1_td_mvp/
```
