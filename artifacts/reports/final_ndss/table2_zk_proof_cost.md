# Table 2: ZK Proof Cost

| Relation | Variant | Scale Axis | Status | Prove Time (s) | Verify Time (s) | Proof Size (bytes) | Cycle Count | Prover | Peak RSS (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| td_mvp | canonical | relation | proof_verified | 60.49624495 | 0.124127551 | 2783869 | 434785 | cpu |  |
| merkle_membership | canonical | merkle_depth | proof_verified | 50.203970284 | 0.122552381 | 2779510 | 116750 | cpu |  |
| forward_td_mlp | canonical_tiny | network | proof_verified | 90.389507192 | 0.125129811 | 2798897 | 1628852 | cpu |  |
| one_step_sgd_tiny | canonical_tiny | network | proof_verified | 71.527741481 | 0.124751534 | 2790551 | 928948 | cpu |  |
| short_trace | canonical | trace_length | proof_verified | 51.787273056 | 0.123439925 | 2779989 | 122067 | cpu |  |
| training_update | batch1_tiny | batch_size | proof_verified | 61.319989572 | 0.124674041 | 2785799 | 494177 | cpu |  |
| training_fragment_k1 | k1 | trace_length | proof_verified | 1.619504343 | 0.127261229 | 2791999 | 935015 | cuda |  |
| training_fragment_k4 | k4 | trace_length | proof_verified | 2.094624044 | 0.127717316 | 2808599 | 2367608 | cuda |  |
| training_fragment_k8 | k8 | trace_length | proof_verified | 3.293015934 | 0.128721639 | 2830831 | 4258262 | cuda |  |
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 1.424242661 | 0.125206401 | 2795671 | 879949 | cuda |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 1.8180899369999999 | 0.125173453 | 2804079 | 1507947 | cuda |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 2.570160927 | 0.126414505 | 2819656 | 2758625 | cuda |  |
| training_fragment | cartpole_expert | committed_dataset | proof_verified | 3.099297747 | 0.128705393 | 2829015 | 4042983 | cuda |  |
| training_fragment | lunarlander_expert | committed_dataset | proof_verified | 4.18296746 | 0.12961467 | 2849714 | 5745368 | cuda |  |
| training_fragment_k16 | k16 | trace_length | execute_only |  |  |  |  |  |  |
| training_fragment_k32 | k32 | trace_length | execute_only |  |  |  |  |  |  |
| training_fragment_k128 | k128 | trace_length | execute_only |  |  |  |  |  |  |
| training_update | batch4 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | batch8 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | batch16 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | network_small | network | not_supported_current_backend |  |  |  |  |  |  |
| merkle_membership | dataset_1000 | dataset_size | proof_verified | 57.741494579 | 0.123351378 | 2782933 | 357965 | cpu | 10308.496 |
| merkle_membership | dataset_10000 | dataset_size | proof_verified | 59.349334546 | 0.123584692 | 2783958 | 470318 | cpu | 10680.688 |
| merkle_membership | dataset_50000 | dataset_size | proof_verified | 60.343401029 | 0.123304088 | 2784470 | 526578 | cpu | 10680.688 |
| merkle_membership | dataset_100000 | dataset_size | proof_verified | 60.826582997 | 0.123102936 | 2784983 | 554100 | cpu | 10729.043 |
| native_flat_recursive_t16 | true_recursive_native | recursive_aggregation | proof_verified | 189.716878495 | 0.053988435 | 1274074 | 422706047 | cuda |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | proof_verified | 392.116108613 | 0.059485475 | 1274074 | 842030244 | cuda |  |
| native_flat_recursive_t64 | true_recursive_native | recursive_aggregation | proof_verified | 770.648105341 | 0.053907619 | 1274074 | 1683536040 | cuda |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | proof_verified | 181.695961217 | 0.05394932 | 1274640 | 421922727 | cuda |  |
| groth16_recursive_t16 | groth16_child_proofs | recursive_aggregation | proof_verified | 1590.207291902 | 67.978753114 | 1469721875 | 6189380355 | cuda |  |
| binary_tree_native_t1248_cartpole | whole_run_cartpole | recursive_aggregation | proof_verified | 191.782642624 | 0.054242549 | 1274654 | 422411631 | cuda |  |
| binary_tree_native_t1248_lunarlander | whole_run_lunarlander | recursive_aggregation | proof_verified | 192.747734871 | 0.053971765 | 1274654 | 422387142 | cuda |  |
| binary_tree_native_t4992_lunarlander_random | whole_run_lunarlander_random | recursive_aggregation | proof_verified | 193.05798728 | 0.053897183 | 1274654 | 422401017 | cuda |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
