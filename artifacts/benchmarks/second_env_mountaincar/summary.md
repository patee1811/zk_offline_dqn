# Phase D MountainCar Forward-TD SP1 Snapshot

Generated at UTC: `2026-05-13T12:43:08.154515+00:00`

## Commands

```bash
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
```

## Overall

- Environment: `MountainCar-v0`
- Relation: `forward_td_mlp_v1`
- Network spec: `2,8,8,3`
- Merkle root: `e6b5cd64f0a687b67334403b2aacff84fb8dd604cc39e19f1e116354fb1ae133`
- Python expected outcomes passed: `True`
- SP1 expected outcomes passed: `True`
- Python/SP1 agreement: `True`

## Matrix

| Case | Batch | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
|---|---:|---|---:|---:|---:|---:|
| `mountaincar-forward-TD-1` | `1` | `accepted` | `107.926506` | `0.126694` | `2787889` | `683942` |
| `tamper_selected_target_value` | `1` | `rejected` | `None` | `None` | `None` | `630657` |
| `tamper_argmax` | `1` | `rejected` | `None` | `None` | `None` | `630523` |
