# Table 2: ZK Proof Cost

| Relation | Variant | Scale Axis | Status | Prove Time (s) | Verify Time (s) | Proof Size (bytes) | Cycle Count | Peak RSS (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| td_mvp | canonical | relation | proof_verified | 167.726006 | 0.190326 | 2783869 | 385048 |  |
| merkle_membership | canonical | merkle_depth | proof_verified | 22.785337436 | 0.086338611 | 2779510 | 103106 |  |
| forward_td_mlp | canonical_tiny | network | proof_verified | 38.199231461 | 0.085754065 | 2797873 | 1547202 |  |
| one_step_sgd_tiny | canonical_tiny | network | proof_verified | 31.490491452 | 0.086747461 | 2790039 | 868731 |  |
| short_trace | canonical | trace_length | proof_verified | 23.366843571 | 0.086860989 | 2779261 | 115363 |  |
| training_update | batch1_tiny | batch_size | proof_verified | 27.07648813 | 0.086269964 | 2785287 | 469426 |  |
| training_fragment_k1 | k1 | trace_length | proof_verified | 31.485706142 | 0.087077918 | 2791471 | 896441 |  |
| training_fragment_k4 | k4 | trace_length | proof_verified | 46.931900136 | 0.087250954 | 2811655 | 2597343 |  |
| training_fragment_k8 | k8 | trace_length | proof_verified | 66.827780725 | 0.088758991 | 2837983 | 4839712 |  |
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 32.527659745 | 0.086539079 | 2795159 | 798934 |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 39.215078766 | 0.086923859 | 2802543 | 1370311 |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 47.811965974 | 0.087003947 | 2816880 | 2507762 |  |
| training_fragment_k16 | k16 | trace_length | execute_only |  |  |  |  |  |
| training_fragment_k32 | k32 | trace_length | execute_only |  |  |  |  |  |
| training_fragment_k128 | k128 | trace_length | execute_only |  |  |  |  |  |
| training_update | batch4 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | batch8 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | batch16 | batch_size | not_supported_current_backend |  |  |  |  |  |
| training_update | network_small | network | not_supported_current_backend |  |  |  |  |  |
| merkle_membership | dataset_1000 | dataset_size | proof_verified | 156.107731501 | 0.191457503 | 2782421 | 305813 | 10197.246 |
| merkle_membership | dataset_10000 | dataset_size | proof_verified | 179.624867853 | 0.194838999 | 2783446 | 400355 | 10511.125 |
| merkle_membership | dataset_100000 | dataset_size | proof_verified | 168.670838206 | 0.195268144 | 2783959 | 470808 | 10552.805 |
| native_flat_recursive_t16 | true_recursive_native | recursive_aggregation | proof_verified | 141.768684256 | 0.050294035 | 1274074 | 309406040 |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | proof_verified | 300.803338259 | 0.050045529 | 1274074 | 615456629 |  |
| native_flat_recursive_t64 | true_recursive_native | recursive_aggregation | proof_verified | 580.393456991 | 0.050349188 | 1274074 | 1230443488 |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | proof_verified | 153.550414155 | 0.050195607 | 1274640 | 308585812 |  |
| groth16_recursive_t16 | groth16_child_proofs | recursive_aggregation | proof_verified | 1589.694720276 | 63.126057846 | 1463614739 | 6162312409 |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
