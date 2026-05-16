# One-Step SGD Tiny SP1 Benchmark Snapshot

## Commands

```bash
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
```

## Overall

- Relation: `one_step_sgd_tiny_v1`
- Network spec: `4,8,2`
- Learning rate fp: `100`
- Python expected outcomes passed: `True`
- SP1 expected outcomes passed: `True`
- Python/SP1 agreement: `True`

## Matrix

| Case | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
|---|---|---:|---:|---:|---:|
| `one-step-SGD-tiny-1` | `accepted` | `115.494141` | `0.125332` | `2789940` | `862136` |
| `tamper_gradient_tensor` | `rejected` | `None` | `None` | `None` | `816177` |
| `tamper_delta_tensor` | `rejected` | `None` | `None` | `None` | `818750` |
| `tamper_learning_rate_fp` | `rejected` | `None` | `None` | `None` | `798867` |
| `tamper_post_model_weight` | `rejected` | `None` | `None` | `None` | `312479` |
| `tamper_post_model_commitment` | `rejected` | `None` | `None` | `None` | `312479` |
| `tamper_smooth_l1_grad` | `rejected` | `None` | `None` | `None` | `786499` |
