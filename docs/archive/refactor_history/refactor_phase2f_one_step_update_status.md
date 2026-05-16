# Refactor Phase 2F One-Step Update Status

## Files Created

- `zk_offline_dqn/relations/one_step_update.py`
- `zk_offline_dqn/verifiers/one_step_update.py`
- `tests/golden/test_one_step_update_verifier.py`
- `tests/negative/test_one_step_update_tamper.py`

## Files Modified

- `scripts/artifacts_export/verify_one_step_update_artifact.py`

## Old Script to New Module Mapping

- Pure one-step update relation checks:
  - old: inline item, batch, checkpoint, metadata, gradient, delta, and SGD update checks in `scripts/artifacts_export/verify_one_step_update_artifact.py`
  - new: `zk_offline_dqn.relations.one_step_update`
- JSON loading, Merkle file validation, checkpoint/model loading, file SHA-256, and report formatting:
  - old: inline in the script
  - new: `zk_offline_dqn.verifiers.one_step_update`
- CLI/environment wrapper:
  - old script path remains `scripts/artifacts_export/verify_one_step_update_artifact.py`
  - the script now delegates to `zk_offline_dqn.verifiers.one_step_update`

## Current CLI Behavior Preserved

- The script still takes no CLI flags.
- The artifact path is still read from `ONE_STEP_ARTIFACT_PATH`.
- The Merkle path is still read from `ONE_STEP_MERKLE_PATH`.
- The pre-checkpoint path is still read from `ONE_STEP_CHECKPOINT_PATH`, with
  artifact `notes.checkpoint_path` fallback when the environment variable is
  absent.
- The post-checkpoint path is still read from `ONE_STEP_POST_CHECKPOINT_PATH`,
  with artifact `notes.post_checkpoint_path` fallback when the environment
  variable is absent.
- Valid artifacts still exit 0.
- Relation failures still print `verification_passed = False`, the explanatory
  note, and exit 0.
- Missing files, malformed artifacts, and unsupported schema versions still
  raise normally.

## Stdout Markers

- Preserved success/failure marker:
  - `verification_passed = True`
  - `verification_passed = False`
- The explanatory failure note is preserved.
- Report labels and ordering are preserved for valid artifacts.

## Artifact Fields Used

- `schema_version`
- `public.dataset_root`
- `public.batch_indices`
- `public.batch_size`
- `public.loss_type`
- `public.optimizer_type`
- `public.learning_rate_fp`
- `public.pre_checkpoint_sha256`
- `public.post_checkpoint_sha256`
- `public.checkpoint_commitment_type`
- `public.pre_online_state_dict_key`
- `public.pre_online_state_dict_sha256`
- `public.pre_target_state_dict_sha256`
- `public.post_online_state_dict_key`
- `public.post_online_state_dict_sha256`
- `public.post_target_state_dict_sha256`
- `items[].index`
- `items[].transition`
- `items[].leaf`
- `items[].leaf_hash`
- `items[].merkle_path`
- `items[].td_witness`
- `update_witness.batch_loss_fp`
- `update_witness.gradient_tensors`
- `update_witness.delta_tensors`
- `notes.checkpoint_path`
- `notes.post_checkpoint_path`

## Schema Version Handling

- The verifier still requires `schema_version == "one_step_update_v1"` through
  `require_schema_version`.
- No schema strings were changed.

## Checkpoint and Model Commitment Helpers Used

- `zk_offline_dqn.artifact_export_utils.load_checkpoint_nets`
- `zk_offline_dqn.artifact_export_utils.file_sha256`
- `zk_offline_dqn.commitments.canonical_checkpoint_state_commitments`
- `torch.load`

## Update Semantics Preserved

- Per-item TD witness recomputation uses `compute_td_witness`.
- Batch loss remains integer average over claimed item losses.
- Pre/post checkpoint SHA-256 checks are unchanged.
- Target network must remain unchanged.
- Online network must change.
- Checkpoint step must increment by one.
- Post checkpoint `source_checkpoint_sha256` must match the pre checkpoint SHA.
- Optimizer metadata must be `sgd`.
- Learning-rate metadata is encoded with `encode_fp`.
- Batch indices in metadata must match public `batch_indices`.
- Gradients are recomputed with `compute_training_loss(...).backward()`.
- Claimed gradients, delta tensors, and SGD update are checked with the same
  `torch.allclose` tolerances.

## Short-Trace Compatibility

- `scripts/artifacts_export/verify_short_trace_update_artifact.py` calls the
  old one-step verifier script via subprocess.
- No short-trace verifier logic was changed.
- The old script path remains runnable with the same environment variables and
  stdout marker, preserving the subprocess contract.

## Negative Cases Tested

- Golden/negative tests:
  - wrong post online state commitment
  - wrong batch loss
  - wrong gradient tensor
  - wrong delta tensor
  - wrong post checkpoint SHA
- Existing negative runner:
  - next action tamper
  - target value tamper
  - loss tamper
  - gradient tensor tamper
  - delta tensor tamper
  - post checkpoint SHA tamper
  - post online state commitment tamper
  - learning-rate tamper
  - batch index tamper

## Inspection Summary

- Current CLI arguments and defaults: no CLI flags; environment variables
  `ONE_STEP_ARTIFACT_PATH`, `ONE_STEP_MERKLE_PATH`, `ONE_STEP_CHECKPOINT_PATH`,
  and `ONE_STEP_POST_CHECKPOINT_PATH` with existing defaults.
- Current stdout marker: `verification_passed = True` or
  `verification_passed = False`.
- Current failure behavior and exit codes: relation rejection exits 0 with a
  false marker and note; malformed input or schema errors raise.
- Full regression inclusion: `run_full_regression.py` directly runs
  `verify_one_step_update_artifact.py` and also runs
  `run_one_step_negative_tests.py`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.one_step_update; import zk_offline_dqn.verifiers.one_step_update"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/artifacts_export/verify_one_step_update_artifact.py`
- `python scripts/experiments/run_one_step_negative_tests.py`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.one_step_update; import zk_offline_dqn.verifiers.one_step_update"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 53 tests, including one-step update golden and negative tests. |
| `python scripts/artifacts_export/verify_one_step_update_artifact.py` | PASS | Printed preserved `verification_passed = True` marker for the canonical artifact. |
| `python scripts/experiments/run_one_step_negative_tests.py` | PASS | Valid control accepted and all one-step update tamper cases rejected. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Negative-Test Result

- `run_one_step_negative_tests.py` completed successfully.
- The runner reported:
  - `valid_one_step_accept = True`
  - `tamper_next_action_online_accept = False`
  - `tamper_q_target_max_fp_accept = False`
  - `tamper_loss_fp_accept = False`
  - `tamper_gradient_tensor_accept = False`
  - `tamper_delta_tensor_accept = False`
  - `tamper_post_checkpoint_sha256_accept = False`
  - `tamper_post_online_state_dict_sha256_accept = False`
  - `tamper_learning_rate_fp_accept = False`
  - `tamper_batch_indices_accept = False`
  - `all_tests_passed = True`

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 2G should extract exactly one additional verifier family, preserving its
current CLI, stdout markers, schema handling, and regression behavior.
