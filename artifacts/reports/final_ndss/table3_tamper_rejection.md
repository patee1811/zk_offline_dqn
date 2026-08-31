# Table 3: Tamper Rejection

| Tamper | Component | Expected Layer | Observed Layer | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| reward | forward_td_mlp | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| next_state | training_fragment_k1 | python_semantic_oracle | python_semantic_oracle | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| done | forward_td_mlp | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| action | forward_td_mlp | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| merkle_path | training_fragment_k1 | python_semantic_oracle | python_semantic_oracle | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| minibatch_index | training_aggregation_manifest_t128 | python_semantic_oracle | rust_execute | rejected_as_expected | proof-manifest-chain mode; child proofs are bound by hash, not verified in-guest (see the recursive rows for in-guest verification); reused existing SP1 provenance tamper_report.json |
| q_value | forward_td_mlp | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| td_target | forward_td_mlp | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| gradient | one_step_sgd_tiny | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| checkpoint_hash | one_step_sgd_tiny | python_semantic_oracle | rust_execute | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| target_network_sync | training_aggregation_manifest_t128 | python_semantic_oracle | rust_execute | rejected_as_expected | proof-manifest-chain mode; child proofs are bound by hash, not verified in-guest (see the recursive rows for in-guest verification); reused existing SP1 provenance tamper_report.json |
| proof_public_input | forward_td_mlp | public_input_binding | public_input_binding | rejected_as_expected | reused existing SP1 provenance tamper_report.json |
| action | dataset_provenance, forward_td_mlp, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 6/6 rejected | 0 not_applicable |
| audit_report_hash | dataset_commitment | summary | summary | 1/1 rejected | 0 not_applicable |
| checkpoint_hash | one_step_sgd_tiny, training_aggregation_binary_native_t16, training_aggregation_groth16_t16, training_aggregation_manifest_t128, training_aggregation_manifest_t32, training_aggregation_manifest_t64, training_aggregation_recursive_t16, training_aggregation_recursive_t32, training_aggregation_recursive_t64, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 30/30 rejected | 0 not_applicable |
| collection_log_final_hash | dataset_commitment, public_dataset_commitment | summary | summary | 1/2 rejected | 1 not_applicable |
| dataset_root | dataset_commitment, merkle_membership, training_aggregation_binary_native_t16, training_aggregation_groth16_t16, training_aggregation_manifest_t128, training_aggregation_manifest_t32, training_aggregation_manifest_t64, training_aggregation_recursive_t16, training_aggregation_recursive_t32, training_aggregation_recursive_t64, training_update | summary | summary | 14/14 rejected | 0 not_applicable |
| done | dataset_provenance, forward_td_mlp, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 6/6 rejected | 0 not_applicable |
| gradient | one_step_sgd_tiny, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 7/7 rejected | 0 not_applicable |
| loss | forward_td_mlp | summary | summary | 1/1 rejected | 0 not_applicable |
| manifest_hash | dataset_commitment, training_aggregation_binary_native_t16, training_aggregation_groth16_t16, training_aggregation_manifest_t128, training_aggregation_manifest_t32, training_aggregation_manifest_t64, training_aggregation_recursive_t16, training_aggregation_recursive_t32, training_aggregation_recursive_t64, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 13/13 rejected | 0 not_applicable |
| merkle_leaf | merkle_membership | summary | summary | 4/4 rejected | 0 not_applicable |
| merkle_path | dataset_commitment, merkle_membership, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 17/17 rejected | 0 not_applicable |
| minibatch_index | merkle_membership, training_aggregation_binary_native_t16, training_aggregation_groth16_t16, training_aggregation_manifest_t128, training_aggregation_manifest_t32, training_aggregation_manifest_t64, training_aggregation_recursive_t16, training_aggregation_recursive_t32, training_aggregation_recursive_t64, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 43/43 rejected | 0 not_applicable |
| next_state | dataset_provenance, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 5/5 rejected | 0 not_applicable |
| proof_public_input | forward_td_mlp, merkle_membership, one_step_sgd_tiny, proof_artifact_policy, td_mvp, training_aggregation_binary_native_t16, training_aggregation_groth16_t16, training_aggregation_manifest_t128, training_aggregation_manifest_t32, training_aggregation_manifest_t64, training_aggregation_recursive_t16, training_aggregation_recursive_t32, training_aggregation_recursive_t64, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 57/59 rejected | 2 not_applicable |
| q_value | forward_td_mlp, training_update | summary | summary | 5/5 rejected | 0 not_applicable |
| raw_trajectory_hash | dataset_commitment | summary | summary | 2/2 rejected | 0 not_applicable |
| reward | dataset_provenance, forward_td_mlp, training_fragment_k1, training_fragment_k4, training_fragment_k8, training_update | summary | summary | 6/6 rejected | 0 not_applicable |
| target_network_sync | training_aggregation_binary_native_t16, training_aggregation_groth16_t16, training_aggregation_manifest_t128, training_aggregation_manifest_t32, training_aggregation_manifest_t64, training_aggregation_recursive_t16, training_aggregation_recursive_t32, training_aggregation_recursive_t64, training_fragment_k1, training_fragment_k4, training_fragment_k8 | summary | summary | 11/11 rejected | 0 not_applicable |
| td_target | forward_td_mlp, training_update | summary | summary | 4/4 rejected | 0 not_applicable |

Table 3 reports tamper rejection only. Proof-manifest aggregation rows do not claim true recursive child-proof verification.
