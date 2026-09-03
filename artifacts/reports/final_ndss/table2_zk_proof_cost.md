# Table 2: ZK Proof Cost

| Relation | Variant | Scale Axis | Status | Prove Time (s) | Verify Time (s) | Proof Size (bytes) | Cycle Count | Peak RSS (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| td_mvp | canonical | relation | proof_verified | 53.948219801 | 0.115671105 | 2783869 | 385048 |  |
| merkle_membership | canonical | merkle_depth | proof_verified | 45.566397837 | 0.114596454 | 2779510 | 103106 |  |
| forward_td_mlp | canonical_tiny | network | proof_verified | 79.264680209 | 0.116442351 | 2797873 | 1547202 |  |
| one_step_sgd_tiny | canonical_tiny | network | proof_verified | 64.081797808 | 0.116264878 | 2790039 | 868731 |  |
| short_trace | canonical | trace_length | proof_verified | 46.339151098 | 0.115517681 | 2779261 | 115363 |  |
| training_update | batch1_tiny | batch_size | proof_verified | 55.049392314 | 0.116141615 | 2785287 | 469426 |  |
| training_fragment_k1 | k1 | trace_length | proof_verified | 64.331851778 | 0.116185595 | 2791471 | 896441 |  |
| training_fragment_k4 | k4 | trace_length | proof_verified | 99.026958486 | 0.117276306 | 2811655 | 2597343 |  |
| training_fragment_k8 | k8 | trace_length | proof_verified | 144.558093004 | 0.118261524 | 2837983 | 4839712 |  |
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 68.763754273 | 0.115337702 | 2795159 | 798918 |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 83.51705198 | 0.115726414 | 2802543 | 1370337 |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 103.969187943 | 0.117525413 | 2816880 | 2507854 |  |
| training_fragment_k16 | k16 | trace_length | execute_only |  |  |  |  |  |
| training_fragment_k32 | k32 | trace_length | execute_only |  |  |  |  |  |
| training_fragment_k128 | k128 | trace_length | execute_only |  |  |  |  |  |
| training_update | batch4 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | batch8 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | batch16 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | network_small | network | not_supported_current_backend |  |  |  |  |  |
| merkle_membership | dataset_1000 | dataset_size | proof_verified | 49.421069829 | 0.114722698 | 2782421 | 305813 | 10242.434 |
| merkle_membership | dataset_10000 | dataset_size | proof_verified | 52.777192307 | 0.114834117 | 2783446 | 400355 | 10413.023 |
| merkle_membership | dataset_100000 | dataset_size | proof_verified | 53.682037903 | 0.115112682 | 2783959 | 470808 | 10579.09 |
| native_flat_recursive_t16 | true_recursive_native | recursive_aggregation | proof_verified | 155.719101158 | 0.05002855 | 1274074 | 309392704 |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | proof_verified | 304.651820184 | 0.050092078 | 1274074 | 615461303 |  |
| native_flat_recursive_t64 | true_recursive_native | recursive_aggregation | proof_verified | 602.295960716 | 0.050056388 | 1274074 | 1230442576 |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | proof_verified | 155.510493487 | 0.050110412 | 1274640 | 308594787 |  |
| groth16_recursive_t16 | groth16_child_proofs | recursive_aggregation | proof_verified | 1592.429129133 | 63.036939158 | 1463617811 | 6162569246 |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
