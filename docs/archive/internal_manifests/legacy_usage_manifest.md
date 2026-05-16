# Legacy Usage Manifest

Phase 11C audits compatibility scripts and historical skeleton directories. This
manifest is descriptive only. No legacy scripts are moved or deleted in Phase
11C.

## Classification Keys

- `active_workflow`: current release workflow entrypoint.
- `compatibility_wrapper_keep`: old path retained because tests, regression,
  benchmark scripts, docs, or paper still call it directly.
- `exporter_keep`: artifact/vector exporter retained for reproducibility.
- `proof_helper_keep`: pre-backend Merkle/proof helper retained for historical
  workflow support.
- `move_to_legacy_later`: possible future move after references are migrated.
- `delete_candidate_later`: possible future deletion after a separate usage
  audit proves no users remain.
- `do_not_touch`: source area that must remain in place.
- `needs_manual_review`: unclear retirement path.

## Summary

- `scripts/artifacts_export/` is still part of the compatibility surface.
  Golden tests, regression smoke tests, benchmark scripts, SP1 backend docs,
  and paper setup text still reference old script paths.
- The unified CLI supersedes most verifier wrappers for new user-facing work,
  but the old stdout markers and paths are still regression contracts.
- Export scripts remain reproducibility tools for regenerating fixtures and
  benchmark inputs. They are not deletion candidates in this phase.
- `scripts/zk_proofs/` contains pre-backend Merkle utilities. They are not part
  of full regression, but docs and helper artifact workflows still reference
  their inputs and outputs.
- The old `src/zk_offline_dqn/` skeleton had no active package role. After
  reference review, its only direct users were skeleton-specific tests/docs and
  compile-smoke strings, so it was removed in the one-pass cleanup.

## Verifier Compatibility Wrappers

| Path | Classification | Purpose | Current users | Replacement command | CLI equivalent | Safe action | Delete now? | Move now? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `scripts/artifacts_export/verify_transition_membership_artifact.py` | compatibility_wrapper_keep | Verify canonical transition membership artifact and preserve old success marker. | golden tests, docs, legacy workflow | `python -m zk_offline_dqn.cli.main verify membership --input artifacts/fixtures/membership/sample_transition_membership.json` | yes | Keep in place; consider redirecting docs later. | no | no |
| `scripts/artifacts_export/verify_td_mvp_test_vector.py` | compatibility_wrapper_keep | Verify TD MVP/SP1 input vector with preserved stdout markers. | golden tests, TD MVP negative runner, benchmark scripts, SP1 backend docs, paper setup | `python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json` | yes | Keep in place; high-risk to remove. | no | no |
| `scripts/artifacts_export/verify_forward_td_mlp_test_vector.py` | compatibility_wrapper_keep | Verify forward-TD MLP vectors and re-export helper names used by tests. | golden tests, forward/MountainCar benchmark scripts, docs | `python -m zk_offline_dqn.cli.main verify forward-td-mlp --input ...` | yes | Keep in place. | no | no |
| `scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py` | compatibility_wrapper_keep | Verify one-step SGD tiny vectors and preserve helper import surface. | golden tests, one-step SGD tiny benchmark script, docs | `python -m zk_offline_dqn.cli.main verify one-step-sgd-tiny --input ...` | yes | Keep in place. | no | no |
| `scripts/artifacts_export/verify_minibatch_td_artifact.py` | compatibility_wrapper_keep | Verify canonical minibatch TD artifact with checkpoint commitments. | full regression, golden/negative tests, CLI smoke, negative runner, docs | `python -m zk_offline_dqn.cli.main verify minibatch-td --input artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json` | yes | Keep in place; direct full-regression user. | no | no |
| `scripts/artifacts_export/verify_one_step_update_artifact.py` | compatibility_wrapper_keep | Verify canonical one-step update artifact. | full regression, golden/negative tests, CLI smoke, benchmark/negative runners, docs | `python -m zk_offline_dqn.cli.main verify one-step-update --input artifacts/fixtures/one_step_update/one_step_update_artifact.json` | yes | Keep in place; direct full-regression user. | no | no |
| `scripts/artifacts_export/verify_short_trace_update_artifact.py` | compatibility_wrapper_keep | Verify short-trace artifact and embedded one-step updates. | full regression, golden/negative tests, CLI smoke, short-trace benchmark/negative runner, docs | `python -m zk_offline_dqn.cli.main verify short-trace --input artifacts/fixtures/short_trace/short_trace_update_artifact.json` | yes | Keep in place; direct full-regression user. | no | no |
| `scripts/artifacts_export/verify_forward_td_consistency.py` | compatibility_wrapper_keep | Check forward TD consistency against checkpoint and minibatch artifact. | full regression, docs | no exact single CLI command | partial | Keep in place until a CLI/report equivalent exists. | no | no |
| `scripts/artifacts_export/verify_td_sample_artifact.py` | needs_manual_review | Verify legacy TD sample artifact path. | legacy docs/scripts; not default full regression | `python -m zk_offline_dqn.cli.main verify td-mvp --input ...` for TD MVP vectors only | partial | Keep for compatibility; consider deprecating after docs migrate. | no | no |

## Exporter Scripts

| Path | Classification | Purpose | Current users | Replacement command | CLI equivalent | Safe action | Delete now? | Move now? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `scripts/artifacts_export/export_transition_membership_artifact.py` | exporter_keep | Generate canonical transition membership artifact from leaf hashes. | docs, historical fixture regeneration | none | no | Keep for reproducibility. | no | no |
| `scripts/artifacts_export/export_td_sample_artifact.py` | exporter_keep | Generate legacy TD sample artifact. | docs/legacy workflow | none | no | Keep; review in later deprecation phase. | no | no |
| `scripts/artifacts_export/export_td_sample_artifact_from_dataset.py` | exporter_keep | Generate TD sample artifact from dataset. | legacy workflow | none | no | Keep for reproducibility. | no | no |
| `scripts/artifacts_export/export_td_mvp_test_vector.py` | exporter_keep | Generate TD MVP test vector. | backend docs, historical SP1 workflows | none | no | Keep; backend docs reference it. | no | no |
| `scripts/artifacts_export/export_td_mvp_batch_test_vector.py` | exporter_keep | Generate TD MVP batch test vectors. | SP1 backend negative case script/docs | none | no | Keep; backend scripts reference it. | no | no |
| `scripts/artifacts_export/export_minibatch_td_artifact.py` | exporter_keep | Generate minibatch TD artifact. | legacy workflow | none | no | Keep for reproducibility. | no | no |
| `scripts/artifacts_export/export_minibatch_td_artifact_from_dataset.py` | exporter_keep | Generate minibatch TD fixtures from dataset. | distinct TD benchmark script | none | no | Keep; benchmark script user. | no | no |
| `scripts/artifacts_export/export_forward_td_mlp_test_vector.py` | exporter_keep | Generate forward-TD MLP fixtures. | forward-TD MLP benchmark script | none | no | Keep; benchmark script user. | no | no |
| `scripts/artifacts_export/export_one_step_sgd_tiny_test_vector.py` | exporter_keep | Generate one-step SGD tiny fixture. | one-step SGD tiny benchmark script | none | no | Keep; benchmark script user. | no | no |
| `scripts/artifacts_export/export_one_step_update_artifact.py` | exporter_keep | Generate one-step update artifacts/checkpoints. | one-step update benchmark, short-trace exporter | none | no | Keep; benchmark/exporter user. | no | no |
| `scripts/artifacts_export/export_short_trace_update_artifact.py` | exporter_keep | Generate short-trace artifacts and per-step update artifacts. | short-trace benchmark, docs | none | no | Keep; benchmark user and subprocess contract. | no | no |

## Proof Helper Scripts

| Path | Classification | Purpose | Current users | Replacement command | CLI equivalent | Safe action | Delete now? | Move now? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `scripts/zk_proofs/build_leaf_hashes.py` | proof_helper_keep | Build transition leaf hashes for legacy Merkle workflow. | legacy docs/helper artifact generation | active package Merkle helpers for library calls | no | Keep until Merkle helper workflow is retired. | no | no |
| `scripts/zk_proofs/build_merkle_root.py` | proof_helper_keep | Build Merkle root from leaf hashes. | legacy docs/helper workflow | `zk_offline_dqn.core.merkle` for library calls | no | Keep. | no | no |
| `scripts/zk_proofs/check_merkle_membership.py` | proof_helper_keep | Check Merkle membership for a selected leaf. | legacy docs/helper workflow | `python -m zk_offline_dqn.cli.main verify membership ...` for artifact-level verification | partial | Keep. | no | no |
| `scripts/zk_proofs/check_real_transition.py` | proof_helper_keep | Inspect/check real transition data. | legacy data/proof workflow | no direct CLI equivalent | no | Keep pending data workflow audit. | no | no |

## Active Experiment Scripts

`scripts/experiments/` contains active regression, benchmark, report, Kaggle,
and release-readiness orchestration. These scripts are `active_workflow` and
should not be moved or deleted in Phase 11C.

## Phase 11D Recommendation

Future legacy cleanup should not delete scripts first. It should:

1. Replace documentation examples with unified CLI commands where appropriate.
2. Add equivalent CLI/report commands for remaining gaps such as
   `verify_forward_td_consistency.py`.
3. Re-run full regression and paper checks.
4. Only then consider moving unused legacy scripts into an archived namespace,
   preserving stdout markers or adding thin wrappers at the old paths.
