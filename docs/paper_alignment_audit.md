# Paper Alignment Audit

This audit records the manuscript scope against the implemented artifact. The
goal is claim hardening: every paper-facing claim should map to code, tests, and
committed provenance without implying full offline-DQN training soundness.

## Current Claim Inventory

| Claim | Support level | Provenance | Safe wording |
| --- | --- | --- | --- |
| Relation-level verification over committed offline-DQN artifacts | supported | `zk_offline_dqn/relations/`, `zk_offline_dqn/verifiers/`, tests | "relation-level verification for selected offline-DQN artifacts" |
| Full DQN training proof | unsupported | no full trace backend, docs non-goals | "not a full proof of DQN training" |
| Honest replay data collection | unsupported as a cryptographic claim | public imports are source-integrity only; self-collected data has replay/reward audit before commitment | "membership relative to a committed replay set; self-collected data can carry replay/reward audit evidence" |
| SP1 proof-backed relation coverage | supported for Table 2 `proof_verified` rows | `artifacts/reports/final_ndss/table2_zk_proof_cost.json`, `artifacts/reports/provenance/sp1/` | "SP1 proof-backed relation families and configurations reported in Table 2" |
| Distinct minibatch TD | supported for TD-1/2/4/8 proof rows | `artifacts/benchmarks/final_ndss/benchmark_matrix.csv`, `zk_backend/td_mvp/sp1/` | "SP1 proof-backed distinct minibatch TD configurations" |
| Forward-TD MLP | supported for canonical tiny vectors and benchmark rows | `zk_backend/forward_td_mlp/sp1/`, SP1 provenance, final benchmark matrix | "SP1 proof-backed fixed-point Forward-TD MLP for canonical tiny vectors; not full training" |
| One-step SGD / training update | supported for canonical tiny vectors | `zk_backend/one_step_sgd_tiny/sp1/`, `zk_backend/training_update/sp1/` | "SP1 proof-backed tiny fixed-point SGD and batch-size-1 training update" |
| Training fragments | supported for `k={1,4,8}` | `zk_backend/training_fragment/sp1/`, Table 2 | "SP1 proof-backed multi-step fragments for canonical tiny vectors" |
| Proof-manifest aggregation | supported for `T={32,64,128}` manifest-chain mode | `zk_backend/training_aggregation/sp1/`, Table 2 | "proof-manifest chunk-chain aggregation; not recursive child-proof verification" |
| Recursive aggregation or long end-to-end trace proof | unsupported | known-failure rows and non-goals | "future work" |
| Tamper rejection benchmark | supported over current coverage | `artifacts/reports/final_ndss/table3_tamper_rejection.*` | "166 adversarial cases across 19 categories, with zero unexpectedly accepted rows" |

## Supported Numbers

Paper-facing numbers are sourced from committed artifacts:

- RL rows: `artifacts/reports/final_ndss/table1_rl_performance.json`
- SP1 proof costs: `artifacts/reports/final_ndss/table2_zk_proof_cost.json`
- Final relation benchmark matrix: `artifacts/benchmarks/final_ndss/benchmark_matrix.csv`
- Tamper summary: `artifacts/reports/final_ndss/table3_tamper_rejection.json`
- Regression summary and legacy compact numbers: `artifacts/reports/final_ndss/paper_numbers.json`

Current manuscript-level summary:

- Python regression: 15 checks, 0 failures.
- Proof verification: all reported proof-verified Table 2 configurations verify
  in under 0.21 seconds.
- Proof size: all reported proof-verified rows are below 2.84 MB.
- Tamper rejection: 166 adversarial test cases across 19 categories; zero
  unexpectedly accepted rows.

## Risky Claims To Avoid

- Do not claim a full DQN training proof from initialization to final deployed
  checkpoint.
- Do not claim Adam optimizer soundness, model-selection soundness,
  all-replay-batches soundness, or arbitrary network-size soundness.
- Do not call proof-manifest chunk-chain aggregation true recursive
  aggregation; child proofs are externally verified and represented by
  manifest/public-input hashes.
- Do not claim honest public dataset collection for Minari/D4RL imports.
- Do not imply that execute-only `k={16,32,128}` fragment rows are
  proof-backed.

## Checks

The claim scanner in `scripts/experiments/check_paper_claims.py` now checks
both legacy `paper_numbers.json` provenance and current Table 2 proof coverage.
Regression coverage is in `tests/regression/test_paper_claims.py`.
