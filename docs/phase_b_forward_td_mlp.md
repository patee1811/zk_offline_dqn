# Phase B Forward-TD MLP Result

This document records the Phase B `forward_td_mlp_v1` implementation and the
Kaggle SP1 benchmark snapshot.

## Relation

`forward_td_mlp_v1` proves, inside the SP1 TD backend path:

- committed replay transition membership;
- quantized online model commitment;
- quantized target model commitment;
- fixed-point online MLP forward on `s`;
- fixed-point online MLP forward on `s'`;
- fixed-point target MLP forward on `s'`;
- Double-DQN first-argmax action selection;
- selected target-network value;
- terminal/non-terminal Bellman target;
- SmoothL1 TD loss;
- claimed per-item and batch loss.

The main network spec is:

```text
CartPole 4-16-16-2
fp_scale = 1000
loss_type = smooth_l1
```

## Implementation Paths

```text
zk_offline_dqn/forward_td_mlp.py
scripts/artifacts_export/export_forward_td_mlp_test_vector.py
scripts/artifacts_export/verify_forward_td_mlp_test_vector.py
scripts/experiments/benchmark_forward_td_mlp_sp1.py
zk_backend/td_mvp/sp1/shared/src/lib.rs
zk_backend/td_mvp/sp1/host/src/main.rs
```

## Reproduction Commands

Python-only oracle and tamper matrix:

```bash
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1
```

SP1 execute for valid and tamper cases:

```bash
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py
```

SP1 proof for batch 1:

```bash
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
```

## Kaggle SP1 Snapshot

Run metadata:

```text
generated_at_utc = 2026-05-13T05:30:53.407570+00:00
git_commit = 8be99d788de6fc08002fa10a48d2e63e38073992
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

Benchmark matrix:

| Case | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `forward-TD-1` | 1 | accepted | 218.364941 | 0.154355 | 2797833 | 1542507 |
| `forward-TD-2` | 2 | accepted | n/a | n/a | n/a | 1956254 |
| `tamper_online_model_weight` | 1 | rejected | n/a | n/a | n/a | 632270 |
| `tamper_target_model_weight` | 1 | rejected | n/a | n/a | n/a | 1118902 |
| `tamper_activation` | 1 | rejected | n/a | n/a | n/a | 1497792 |
| `tamper_relu_mask` | 1 | rejected | n/a | n/a | n/a | 1497090 |
| `tamper_argmax` | 1 | rejected | n/a | n/a | n/a | 1480722 |
| `tamper_selected_target_value` | 1 | rejected | n/a | n/a | n/a | 1480857 |
| `tamper_claimed_batch_loss` | 1 | rejected | n/a | n/a | n/a | 1486939 |

## Acceptance Status

Phase B acceptance criteria are met:

- Python fixed-point oracle and SP1 relation agree.
- SP1 execute passes for batch 1 and batch 2.
- SP1 proof is generated and verified for batch 1.
- Model-weight, activation, ReLU-mask, argmax, selected-target-value, and
  claimed-loss tamper cases reject.

Batch 2 proof remains optional and was not generated in this snapshot.

## Scope Limitations

This relation does not prove gradient computation, optimizer updates, target
network synchronization over a long trace, or full DQN training. It proves that
the TD values for the checked batch are anchored to committed fixed-point MLP
weights rather than accepted as standalone Q-value witnesses.
