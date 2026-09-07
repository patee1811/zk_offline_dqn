# Table 2: ZK Proof Cost

| Relation | Variant | Scale Axis | Status | Prove Time (s) | Verify Time (s) | Proof Size (bytes) | Cycle Count | Prover | Peak RSS (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| td_mvp | canonical | relation | proof_verified | 60.49624495 | 0.124127551 | 2783869 | 434785 | cpu |  |
| merkle_membership | canonical | merkle_depth | proof_verified | 50.222203246 | 0.122936872 | 2779510 | 116750 | cpu |  |
| forward_td_mlp | canonical_tiny | network | proof_verified | 89.878761437 | 0.126011008 | 2798897 | 1628694 | cpu |  |
| one_step_sgd_tiny | canonical_tiny | network | proof_verified | 71.968239471 | 0.124821362 | 2790551 | 928712 | cpu |  |
| short_trace | canonical | trace_length | proof_verified | 51.933611835 | 0.124154753 | 2779989 | 122067 | cpu |  |
| training_update | batch1_tiny | batch_size | proof_verified | 61.491167129 | 0.124643438 | 2785799 | 494060 | cpu |  |
| training_fragment_k1 | k1 | trace_length | proof_verified | 1.643311762 | 0.127073246 | 2792511 | 979945 | cuda |  |
| training_fragment_k4 | k4 | trace_length | proof_verified | 2.324603272 | 0.128052902 | 2813719 | 2799333 | cuda |  |
| training_fragment_k8 | k8 | trace_length | proof_verified | 3.810088194 | 0.129283375 | 2841071 | 5193244 | cuda |  |
| training_aggregation_manifest_t32 | proof_manifest_chain | aggregation_t | proof_verified | 1.407443271 | 0.126195207 | 2795671 | 880030 | cuda |  |
| training_aggregation_manifest_t64 | proof_manifest_chain | aggregation_t | proof_verified | 1.793393018 | 0.125687318 | 2804079 | 1508043 | cuda |  |
| training_aggregation_manifest_t128 | proof_manifest_chain | aggregation_t | proof_verified | 2.526163018 | 0.126357782 | 2819656 | 2758670 | cuda |  |
| training_fragment | cartpole_expert | committed_dataset | proof_verified | 3.45632526 | 0.129179424 | 2835671 | 4647221 | cuda |  |
| training_fragment | lunarlander_expert | committed_dataset | proof_verified | 4.655681776 | 0.197148735 | 4308420 | 6745594 | cuda |  |
| training_fragment_k16 | k16 | trace_length | execute_only |  |  |  |  |  |  |
| training_fragment_k32 | k32 | trace_length | execute_only |  |  |  |  |  |  |
| training_fragment_k128 | k128 | trace_length | execute_only |  |  |  |  |  |  |
| training_update | batch4 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | batch8 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | batch16 | batch_size | not_supported_current_backend |  |  |  |  |  |  |
| training_update | network_small | network | not_supported_current_backend |  |  |  |  |  |  |
| merkle_membership | dataset_1000 | dataset_size | proof_verified | 58.169772372 | 0.123456406 | 2782933 | 357965 | cpu | 10356.629 |
| merkle_membership | dataset_10000 | dataset_size | proof_verified | 59.895160144 | 0.12291586 | 2783958 | 470318 | cpu | 10591.734 |
| merkle_membership | dataset_50000 | dataset_size | proof_verified | 60.557828854 | 0.123399241 | 2784470 | 526578 | cpu | 10611.707 |
| merkle_membership | dataset_100000 | dataset_size | proof_verified | 61.128445191 | 0.123058213 | 2784983 | 554100 | cpu | 10856.727 |
| native_flat_recursive_t16 | true_recursive_native | recursive_aggregation | proof_verified | 193.405205111 | 0.054193836 | 1274074 | 422726492 | cuda |  |
| native_flat_recursive_t32 | true_recursive_native | recursive_aggregation | proof_verified | 385.898092375 | 0.054149142 | 1274074 | 842015859 | cuda |  |
| native_flat_recursive_t64 | true_recursive_native | recursive_aggregation | proof_verified | 755.163171017 | 0.05394864 | 1274074 | 1683525837 | cuda |  |
| binary_tree_native_t16 | binary_native_recursive | recursive_aggregation | proof_verified | 189.844131706 | 0.054469242 | 1274640 | 421911268 | cuda |  |
| groth16_recursive_t16 | groth16_child_proofs | recursive_aggregation | proof_verified | 1596.857619595 | 68.024389019 | 1468175345 | 6180861737 | cuda |  |
| binary_tree_native_t1248_cartpole | whole_run_cartpole | recursive_aggregation | proof_verified | 199.668306727 | 0.054002781 | 1274654 | 422415621 | cuda |  |
| binary_tree_native_t1248_lunarlander | whole_run_lunarlander | recursive_aggregation | proof_verified | 198.139813539 | 0.053853344 | 1274654 | 422396109 | cuda |  |

Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.
