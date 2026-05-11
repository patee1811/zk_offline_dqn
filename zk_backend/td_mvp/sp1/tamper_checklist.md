# SP1 TD MVP Tamper Checklist

Use this checklist when porting `scripts/experiments/run_td_mvp_test_vector_negative_tests.py`
to SP1 host tests.

## Required Cases

| Case | Expected result | Relation guard |
| --- | --- | --- |
| `valid_control` | accept | baseline vector proves and verifies |
| `tamper_reward` | reject | transition serialization, Bellman target, Merkle root |
| `tamper_done` | reject | transition serialization and terminal/non-terminal Bellman branch |
| `tamper_transition_obs` | reject | transition serialization and Merkle root |
| `tamper_leaf_encoding` | reject | `leaf == SerializeTransition(transition)` |
| `tamper_merkle_path` | reject | Merkle root recomputation |
| `tamper_q_target_max_fp` | reject | Bellman target recomputation |
| `tamper_claimed_target_fp` | reject | public target consistency |
| `tamper_claimed_loss_fp` | reject | public loss consistency |
| `tamper_leaf_hash` | reject | canonical leaf hash consistency |
| `tamper_td_error_fp` | reject | TD error recomputation |

## SP1 Acceptance Rule

The SP1 host test should treat a case as rejected if proof generation fails,
guest execution panics, or proof verification fails. A tampered case must not
produce a verified proof for the public inputs supplied by that case.
