# Achieved Relation Benchmark Artifact

## Status

- Components loaded: `4`
- Benchmark rows: `29`
- Tamper rows: `21`
- All loaded components passed expected outcomes: `True`

## Accepted SP1 Proof Rows

| Relation | Environment | Network | Batch | Prove (s) | Verify (s) | Proof bytes | Cycles |
|---|---|---|---:|---:|---:|---:|---:|
| `td_batch_distinct_v1` | `CartPole-v1` | `witness_q_values` | 1 | 97.955756 | 0.126565 | 2783869 | 385048 |
| `td_batch_distinct_v1` | `CartPole-v1` | `witness_q_values` | 2 | 120.669043 | 0.127258 | 2788227 | 730778 |
| `td_batch_distinct_v1` | `CartPole-v1` | `witness_q_values` | 4 | 141.309797 | 0.125481 | 2796699 | 1435787 |
| `td_batch_distinct_v1` | `CartPole-v1` | `witness_q_values` | 8 | 202.921645 | 0.126658 | 2812915 | 2845813 |
| `forward_td_mlp_v1` | `CartPole-v1` | `4,16,16,2` | 1 | 148.418458 | 0.127259 | 2797833 | 1543753 |
| `forward_td_mlp_v1` | `MountainCar-v0` | `2,8,8,3` | 1 | 107.926506 | 0.126694 | 2787889 | 683942 |
| `one_step_sgd_tiny_v1` | `CartPole-v1` | `4,8,2` | 1 | 115.494141 | 0.125332 | 2789940 | 862136 |

## Source Files

- `summary.json`: machine-readable aggregate.
- `benchmark_matrix.csv`: normalized benchmark and rejection rows.
- `tamper_matrix.csv`: normalized tamper coverage.
- `reproduction.md`: reviewer commands for Python smoke and SP1/Kaggle paths.
