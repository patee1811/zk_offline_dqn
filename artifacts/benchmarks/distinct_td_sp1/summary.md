# Distinct TD SP1 Benchmark Snapshot

Generated at UTC: `2026-05-13T01:15:29.080668+00:00`

## Command

```bash
python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1
python scripts/experiments/benchmark_distinct_td_sp1.py --prove
```

## Overall

- Dataset: `data/cartpole_dqn_eps010_transitions.pkl`
- Merkle artifact: `artifacts/cartpole_dqn_eps010_merkle.json`
- Checkpoint: `models/offline_dqn_with_target_seed42_best.pt`
- Batch sizes: `[1, 2, 4, 8]`
- Python expected outcomes passed: `True`
- SP1 expected outcomes passed: `True`
- Python/SP1 agreement: `True`

## Benchmark Matrix

| Case | Relation | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count | Notes |
|---|---|---:|---|---:|---:|---:|---:|---|
| `TD-1` | td_batch_distinct_v1 | `1` | `completed` | `168.311847` | `0.194367` | `2783354` | `383541` | distinct committed replay minibatch |
| `TD-2` | td_batch_distinct_v1 | `2` | `completed` | `197.410724` | `0.198335` | `2787712` | `729096` | distinct committed replay minibatch |
| `TD-4` | td_batch_distinct_v1 | `4` | `completed` | `265.605205` | `0.198736` | `2796184` | `1434680` | distinct committed replay minibatch |
| `TD-8` | td_batch_distinct_v1 | `8` | `completed` | `349.079689` | `0.198359` | `2812912` | `2845827` | distinct committed replay minibatch |
| `tamper_duplicate_index` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `52326` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_item_index` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `52731` | negative test for duplicate/order/index/loss/average/path |
| `tamper_swapped_item_order` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `52731` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_item_loss` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `379578` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_claimed_batch_average` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `708751` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_path_order` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `52757` | negative test for duplicate/order/index/loss/average/path |
