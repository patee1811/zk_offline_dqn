# Refactor Phase 2E Minibatch TD Status

## Files Created

- `zk_offline_dqn/relations/minibatch_td.py`
- `zk_offline_dqn/verifiers/minibatch_td.py`
- `tests/golden/test_minibatch_td_verifier.py`
- `tests/negative/__init__.py`
- `tests/negative/test_minibatch_td_tamper.py`

## Files Modified

- `scripts/artifacts_export/verify_minibatch_td_artifact.py`

## Old Script to New Module Mapping

- Pure minibatch TD relation checks:
  - old: inline item, batch, distinctness, TD, and Merkle checks in `scripts/artifacts_export/verify_minibatch_td_artifact.py`
  - new: `zk_offline_dqn.relations.minibatch_td`
- JSON loading, checkpoint SHA-256, canonical checkpoint commitments, and report formatting:
  - old: inline in the script
  - new: `zk_offline_dqn.verifiers.minibatch_td`
- CLI/environment wrapper:
  - old script path remains `scripts/artifacts_export/verify_minibatch_td_artifact.py`
  - the script now delegates to `zk_offline_dqn.verifiers.minibatch_td`

## Current CLI Behavior Preserved

- The script still takes no CLI flags.
- The artifact path is still read from `MINIBATCH_TD_ARTIFACT_PATH`.
- The default artifact path remains `artifacts/minibatch_td_from_dataset.json`.
- The checkpoint path is still read from `MINIBATCH_TD_CHECKPOINT_PATH`.
- The default checkpoint path remains `models/offline_dqn_with_target_seed42_best.pt`.
- Relation failures still print `verification_passed = False` and exit 0.
- Missing files, malformed artifacts, unsupported schema versions, and invalid
  loss types still raise normally.

## Stdout Markers

- Preserved success/failure marker:
  - `verification_passed = True`
  - `verification_passed = False`
- Report labels and ordering are preserved for valid artifacts.

## Artifact Fields Used

- `schema_version`
- `public.dataset_root`
- `public.batch_size`
- `public.batch_mode`
- `public.leaf_indices`
- `public.loss_type`
- `public.batch_loss_fp`
- `public.checkpoint_sha256`
- `public.checkpoint_commitment_type`
- `public.online_state_dict_key`
- `public.online_state_dict_sha256`
- `public.target_state_dict_sha256`
- `items[].index`
- `items[].transition`
- `items[].leaf` or `items[].serialized_leaf`
- `items[].leaf_hash`
- `items[].merkle_path`
- `items[].td_witness.q_online_fp`
- `items[].td_witness.q_target_max_fp`
- `items[].td_witness.target_fp`
- `items[].td_witness.loss_fp`

## Schema Version Handling

- The verifier still requires `schema_version == "minibatch_td_v1"` through
  `require_schema_version`.
- No schema strings were changed.

## Fixed-Point, TD, and Merkle Helpers Used

- `zk_offline_dqn.zk_specs.serialize_transition_leaf`
- `zk_offline_dqn.zk_specs.compute_td_target_fp`
- `zk_offline_dqn.zk_specs.compute_smooth_l1_loss_fp`
- `zk_offline_dqn.core.merkle.hash_leaf`
- `zk_offline_dqn.core.merkle.verify_merkle_path`
- `zk_offline_dqn.io_utils.file_sha256`
- `zk_offline_dqn.commitments.canonical_checkpoint_state_commitments`

These helpers were reused without changing arithmetic, rounding, SmoothL1
semantics, TD target semantics, or Merkle membership semantics.

## Distinctness Semantics

- `batch_size_ok` remains `batch_size == len(items) and batch_size > 0`.
- `leaf_indices_match` remains true when `public.leaf_indices` is absent;
  otherwise it requires the public indices to match the item order.
- Distinct indices are required when `batch_mode == "distinct"` or
  `public.leaf_indices` is present.
- Distinctness is checked with `len(set(item_indices)) == len(item_indices)`.

## Negative Cases Tested

- Golden/negative tests:
  - duplicate batch indices
  - wrong claimed batch loss
  - wrong item loss
  - wrong TD target
  - wrong Merkle path
- Existing negative runner:
  - reward tamper
  - loss tamper
  - checkpoint SHA tamper
  - canonical online state commitment tamper
  - leaf hash tamper
  - Merkle path tamper
  - duplicate index
  - wrong item index
  - swapped item order
  - claimed batch average tamper
  - path order tamper

## Inspection Summary

- Current CLI arguments and defaults: no CLI flags; environment variables
  `MINIBATCH_TD_ARTIFACT_PATH` and `MINIBATCH_TD_CHECKPOINT_PATH` with existing
  defaults.
- Current stdout marker: `verification_passed = True` or
  `verification_passed = False`.
- Current failure behavior and exit codes: relation rejection exits 0 with a
  false marker; malformed input or schema/loss errors raise.
- Full regression inclusion: `run_full_regression.py` directly runs
  `verify_minibatch_td_artifact.py` and also runs
  `run_negative_verification_tests.py`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.minibatch_td; import zk_offline_dqn.verifiers.minibatch_td"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/artifacts_export/verify_minibatch_td_artifact.py`
- `python scripts/experiments/run_negative_verification_tests.py`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.minibatch_td; import zk_offline_dqn.verifiers.minibatch_td"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 43 tests, including minibatch TD golden and negative tests. |
| `python scripts/artifacts_export/verify_minibatch_td_artifact.py` | PASS | Printed preserved `verification_passed = True` marker for the canonical artifact. |
| `python scripts/experiments/run_negative_verification_tests.py` | PASS | Valid control accepted and all minibatch tamper cases rejected. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Negative-Test Result

- `run_negative_verification_tests.py` completed successfully.
- The runner reported:
  - `valid_control_accept = True`
  - `tamper_loss_fp_accept = False`
  - `tamper_reward_accept = False`
  - `tamper_checkpoint_sha256_accept = False`
  - `tamper_online_state_dict_sha256_accept = False`
  - `tamper_leaf_hash_accept = False`
  - `tamper_merkle_path_accept = False`
  - `tamper_duplicate_index_accept = False`
  - `tamper_wrong_item_index_accept = False`
  - `tamper_swapped_item_order_accept = False`
  - `tamper_claimed_batch_average_accept = False`
  - `tamper_path_order_accept = False`
  - `all_tests_passed = True`

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 2F should extract exactly one additional verifier family, preserving its
current CLI, stdout markers, schema handling, and regression behavior.
