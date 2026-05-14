# Distinct TD SP1 Benchmark Snapshot

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
| `TD-1` | td_batch_distinct_v1 | `1` | `completed` | `97.955756` | `0.126565` | `2783869` | `385048` | distinct committed replay minibatch |
| `TD-2` | td_batch_distinct_v1 | `2` | `completed` | `120.669043` | `0.127258` | `2788227` | `730778` | distinct committed replay minibatch |
| `TD-4` | td_batch_distinct_v1 | `4` | `completed` | `141.309797` | `0.125481` | `2796699` | `1435787` | distinct committed replay minibatch |
| `TD-8` | td_batch_distinct_v1 | `8` | `completed` | `202.921645` | `0.126658` | `2812915` | `2845813` | distinct committed replay minibatch |
| `tamper_duplicate_index` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `55202` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_item_index` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `55616` | negative test for duplicate/order/index/loss/average/path |
| `tamper_swapped_item_order` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `55616` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_item_loss` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `381602` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_claimed_batch_average` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `709917` | negative test for duplicate/order/index/loss/average/path |
| `tamper_wrong_path_order` | invalid distinct batch witness | `2` | `rejected` | `None` | `None` | `None` | `55629` | negative test for duplicate/order/index/loss/average/path |
