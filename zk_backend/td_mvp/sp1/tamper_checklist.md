# SP1 TD MVP Tamper Checklist

Use this checklist when porting `scripts/experiments/run_td_mvp_test_vector_negative_tests.py`
to SP1 host tests.

## Required Cases

| Case | Expected result | Relation guard |
| --- | --- | --- |
| `valid_control` | accept | baseline vector proves and verifies |
| `tamper_schema_version` | reject | schema compatibility |
| `tamper_reward` | reject | transition serialization, Bellman target, Merkle root |
| `tamper_fixed_point_rounding` | reject | fixed-point conversion consistency |
| `tamper_done` | reject | transition serialization and terminal/non-terminal Bellman branch |
| `tamper_done_branch` | reject | terminal/non-terminal Bellman target semantics |
| `tamper_transition_obs` | reject | transition serialization and Merkle root |
| `tamper_leaf_encoding` | reject | `leaf == SerializeTransition(transition)` |
| `tamper_merkle_path` | reject | Merkle root recomputation |
| `tamper_leaf_index` | reject | public index and Merkle direction consistency |
| `tamper_path_order` | reject | Merkle path ordering |
| `tamper_q_target_max_fp` | reject | Bellman target recomputation |
| `tamper_target_network_value` | reject | target-value witness consistency |
| `tamper_claimed_target_fp` | reject | public target consistency |
| `tamper_claimed_loss_fp` | reject | public loss consistency |
| `tamper_leaf_hash` | reject | canonical leaf hash consistency |
| `tamper_td_error_fp` | reject | TD error recomputation |

## Batch Cases

| Case | Expected result | Relation guard |
| --- | --- | --- |
| `valid_batch_size_2` | accept | baseline minibatch vector executes |
| `tamper_batch_claimed_loss_fp` | reject | public average loss consistency |
| `tamper_batch_size` | reject | public batch size consistency |
| `tamper_batch_item_loss_fp` | reject | per-item loss recomputation |
| `tamper_batch_item_index` | reject | per-item Merkle index consistency |
| `tamper_batch_path_order` | reject | per-item Merkle path ordering |
| `tamper_batch_target_network_value` | reject | per-item target-value witness consistency |
| `tamper_batch_fixed_point_rounding` | reject | per-item fixed-point conversion consistency |

## SP1 Acceptance Rule

The SP1 host test should treat a case as rejected if proof generation fails,
guest execution panics, or proof verification fails. A tampered case must not
produce a verified proof for the public inputs supplied by that case.
