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
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 68.755191731 | 0.115348308 | 2795159 | 800951 |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 83.345884299 | 0.115835967 | 2802543 | 1372345 |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 104.776237644 | 0.116995328 | 2817392 | 2509826 |  |
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
| native_flat_recursive_t16 | true_recursive_native | recursive_aggregation | proof_verified | 155.15525695 | 0.049904298 | 1274074 | 309405410 |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | proof_verified | 277.941845291 | 0.050032673 | 1274074 | 615476672 |  |
| native_flat_recursive_t64 | true_recursive_native | recursive_aggregation | proof_verified | 587.587212785 | 0.050739636 | 1274074 | 1230467546 |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | proof_verified | 141.45632495 | 0.05056926 | 1274640 | 308600772 |  |
| groth16_recursive_t16 | groth16_child_proofs | recursive_aggregation | proof_verified | 1589.110760237 | 63.406733869 | 1463618323 | 6162638640 |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
