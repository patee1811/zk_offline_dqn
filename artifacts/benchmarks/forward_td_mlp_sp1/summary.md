# Forward-TD MLP SP1 Benchmark Snapshot

## Commands

```bash
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
```

## Overall

- Relation: `forward_td_mlp_v1`
- Network spec: `4,16,16,2`
- Batch sizes: `[1, 2]`
- Python expected outcomes passed: `True`
- SP1 expected outcomes passed: `True`
- Python/SP1 agreement: `True`

## Matrix

| Case | Batch | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
|---|---:|---|---:|---:|---:|---:|
| `forward-TD-1` | `1` | `accepted` | `148.418458` | `0.127259` | `2797833` | `1543753` |
| `forward-TD-2` | `2` | `accepted` | `None` | `None` | `None` | `1957958` |
| `tamper_online_model_weight` | `1` | `rejected` | `None` | `None` | `None` | `633034` |
| `tamper_target_model_weight` | `1` | `rejected` | `None` | `None` | `None` | `1119666` |
| `tamper_activation` | `1` | `rejected` | `None` | `None` | `None` | `1498908` |
| `tamper_relu_mask` | `1` | `rejected` | `None` | `None` | `None` | `1498210` |
| `tamper_argmax` | `1` | `rejected` | `None` | `None` | `None` | `1481808` |
| `tamper_selected_target_value` | `1` | `rejected` | `None` | `None` | `None` | `1481943` |
| `tamper_claimed_batch_loss` | `1` | `rejected` | `None` | `None` | `None` | `1488117` |
