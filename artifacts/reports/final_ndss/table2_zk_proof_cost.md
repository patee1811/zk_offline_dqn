# Table 2: ZK Proof Cost

| Relation | Variant | Scale Axis | Status | Prove Time (s) | Verify Time (s) | Proof Size (bytes) | Cycle Count | Peak RSS (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| td_mvp | canonical | relation | proof_verified | 167.726006 | 0.190326 | 2783869 | 385048 |  |
| merkle_membership | canonical | merkle_depth | proof_verified | 121.703486901 | 0.148949679 | 2779510 | 103106 |  |
| forward_td_mlp | canonical_tiny | network | proof_verified | 142.746280097 | 0.123545696 | 2797873 | 1547234 |  |
| one_step_sgd_tiny | canonical_tiny | network | proof_verified | 122.726966833 | 0.124717015 | 2790039 | 868763 |  |
| short_trace | canonical | trace_length | proof_verified | 82.303272706 | 0.122530074 | 2779261 | 115363 |  |
| training_update | batch1_tiny | batch_size | proof_verified | 104.785579262 | 0.125128546 | 2785287 | 469460 |  |
| training_fragment_k1 | k1 | trace_length | proof_verified | 163.091462145 | 0.15497829 | 2791463 | 896397 |  |
| training_fragment_k4 | k4 | trace_length | proof_verified | 254.133800348 | 0.154101191 | 2811647 | 2597290 |  |
| training_fragment_k8 | k8 | trace_length | proof_verified | 440.619541167 | 0.20885854 | 2837975 | 4839664 |  |
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 159.549469094 | 0.155103988 | 2789805 | 785786 |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 198.514597771 | 0.164456533 | 2797701 | 1350040 |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 253.231674938 | 0.154249751 | 2812038 | 2465680 |  |
| training_fragment_k16 | k16 | trace_length | execute_only |  |  |  |  |  |
| training_fragment_k32 | k32 | trace_length | execute_only |  |  |  |  |  |
| training_fragment_k128 | k128 | trace_length | execute_only |  |  |  |  |  |
| training_update | batch4 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | batch8 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | batch16 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | network_small | network | not_supported_current_backend |  |  |  |  |  |
| merkle_membership | dataset_1000 | dataset_size | proof_verified | 121.703486901 | 0.148949679 | 2779510 | 103106 |  |
| merkle_membership | dataset_10000 | dataset_size | reference_only |  |  |  |  |  |
| merkle_membership | dataset_100000 | dataset_size | reference_only |  |  |  |  |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | failed_oom |  |  |  |  |  |
| groth16_plonk_recursive_t16 | snark_export | recursive_aggregation | failed_environment |  |  |  |  |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | failed_oom |  |  |  |  |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
