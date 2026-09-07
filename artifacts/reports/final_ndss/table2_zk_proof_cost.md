# Table 2: ZK Proof Cost

| Relation | Variant | Scale Axis | Status | Prove Time (s) | Verify Time (s) | Proof Size (bytes) | Cycle Count | Prover | Peak RSS (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| td_mvp | canonical | relation | proof_verified | 60.339038547 | 0.124389036 | 2783869 | 434785 |  |  |
| merkle_membership | canonical | merkle_depth | proof_verified | 50.202496826 | 0.122690861 | 2779510 | 116750 |  |  |
| forward_td_mlp | canonical_tiny | network | proof_verified | 89.209607327 | 0.125632047 | 2798897 | 1628675 |  |  |
| one_step_sgd_tiny | canonical_tiny | network | proof_verified | 71.771876005 | 0.125643043 | 2790551 | 928693 |  |  |
| short_trace | canonical | trace_length | proof_verified | 51.687464148 | 0.124131554 | 2779989 | 122067 |  |  |
| training_update | batch1_tiny | batch_size | proof_verified | 61.563384568000004 | 0.126607929 | 2785799 | 494060 |  |  |
| training_fragment_k1 | k1 | trace_length | proof_verified | 1.574758662 | 0.126805997 | 2791983 | 960902 | cuda |  |
| training_fragment_k4 | k4 | trace_length | proof_verified | 2.313244575 | 0.128539791 | 2813191 | 2776906 | cuda |  |
| training_fragment_k8 | k8 | trace_length | proof_verified | 3.795511814 | 0.129491568 | 2841055 | 5171660 | cuda |  |
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 1.4320784579999999 | 0.125604204 | 2795671 | 879873 | cuda |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 1.8081874249999998 | 0.126041831 | 2804079 | 1508159 | cuda |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 2.53259536 | 0.126969594 | 2819656 | 2759185 | cuda |  |
| training_fragment | cartpole_expert | committed_dataset | proof_verified | 3.370516392 | 0.129267135 | 2835655 | 4636813 | cuda |  |
| training_fragment | lunarlander_expert | committed_dataset | proof_verified | 4.618301761 | 0.197243475 | 4307380 | 6704450 | cuda |  |
| training_fragment_k16 | k16 | trace_length | execute_only |  |  |  |  |  |  |
| training_fragment_k32 | k32 | trace_length | execute_only |  |  |  |  |  |  |
| training_fragment_k128 | k128 | trace_length | execute_only |  |  |  |  |  |  |
| training_update | batch4 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | batch8 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | batch16 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | network_small | network | not_supported_current_backend |  |  |  |  |  |  |
| merkle_membership | dataset_1000 | dataset_size | proof_verified | 57.870841751 | 0.123056228 | 2782933 | 357965 |  | 10327.723 |
| merkle_membership | dataset_10000 | dataset_size | proof_verified | 59.162392332 | 0.123420754 | 2783958 | 470318 |  | 10599.492 |
| merkle_membership | dataset_50000 | dataset_size | proof_verified | 60.401495551 | 0.123110109 | 2784470 | 526578 |  | 10745.34 |
| merkle_membership | dataset_100000 | dataset_size | proof_verified | 60.632972255 | 0.122992097 | 2784983 | 554100 |  | 10745.34 |
| native_flat_recursive_t16 | true_recursive_native | recursive_aggregation | proof_verified | 197.065386195 | 0.054469867 | 1274074 | 422687963 | cuda |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | proof_verified | 386.983008478 | 0.054370422 | 1274074 | 841967530 | cuda |  |
| native_flat_recursive_t64 | true_recursive_native | recursive_aggregation | proof_verified | 734.843879128 | 0.054046829 | 1274074 | 1683424755 | cuda |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | proof_verified | 198.110268856 | 0.054276106 | 1274640 | 421880109 | cuda |  |
| groth16_recursive_t16 | groth16_child_proofs | recursive_aggregation | proof_verified | 1597.873485446 | 68.244203945 | 1468199625 | 6183021300 | cuda |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
