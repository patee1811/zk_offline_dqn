# Paper Alignment Audit

This audit records the manuscript scope against the implemented artifact. The
goal is claim hardening: every paper-facing claim should map to code, tests, and
committed provenance without implying full offline-DQN training soundness.

> **Table naming.** In this repository "Table 1", "Table 2" and "Table 3"
> name the generated artifact tables
> (`artifacts/reports/final_ndss/table{1,2,3}_*`), not the numbering in the
> manuscript. In `paper/main.pdf` those three appear as Table 4 (RL
> performance), Table 5 (proof cost) and Table 7 (tamper rejection).

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
| Training fragments | supported for `k={1,4,8,156}` plus two vectors bound to committed datasets | `zk_backend/training_fragment/sp1/`, Table 2 | "SP1 proof-backed multi-step fragments; `k=156` is the leaf of the whole-run trees" |
| Proof-manifest aggregation | supported for `T={32,64,128}` manifest-chain mode | `zk_backend/training_aggregation/sp1/`, Table 2 | "proof-manifest chunk-chain aggregation; this mode does not verify child proofs in-guest" |
| Recursive aggregation (child proofs verified in-guest) | supported, CUDA prover only | flat `T={16,32,64}`, binary trees to `T=4992`; Table 2, `artifacts/reports/provenance/sp1/training_aggregation_binary_native_*` | "the aggregate guest verifies each child proof cryptographically; measured under a CUDA prover" |
| Whole-run proof | supported for `T={1248,1248,4992}` | three root proofs with `step_start=0`, each leaf bound to the committed dataset | "one root proof covering an entire run, not a fragment of one" |
| Proof on a CPU prover | unsupported for recursion | the CPU prover did not complete recursion rows within 61 GB | "recursion rows require a CUDA prover" |
| Tamper rejection benchmark | supported over current coverage | `artifacts/reports/final_ndss/table3_tamper_rejection.*` | "236 adversarial cases across 19 categories, with zero unexpectedly accepted rows" |

## Supported Numbers

Paper-facing numbers are sourced from committed artifacts:

- RL rows: `artifacts/reports/final_ndss/table1_rl_performance.json`
- SP1 proof costs: `artifacts/reports/final_ndss/table2_zk_proof_cost.json`
- Final relation benchmark matrix: `artifacts/benchmarks/final_ndss/benchmark_matrix.csv`
- Tamper summary: `artifacts/reports/final_ndss/table3_tamper_rejection.json`
- Regression summary and legacy compact numbers: `artifacts/reports/final_ndss/paper_numbers.json`

Current manuscript-level summary:

- Python regression: 15 checks, 0 failures.
- Proof verification: 25 of the 26 proof-verified Table 2 rows verify in
  0.054-0.130 seconds. The Groth16 child-proof row is the exception at 68.0
  seconds and is reported as such.
- Proof size: the same 25 rows are 1.27-2.85 MB; the Groth16 row is 1.47 GB.
- Prover: all 26 proof-verified rows were produced on the CUDA prover, and each
  row records which prover produced it.
- Tamper rejection: 236 adversarial test cases across 19 categories; 233
  rejected as expected, zero unexpectedly accepted.

## Risky Claims To Avoid

- Do not claim a full DQN training proof from initialization to final deployed
  checkpoint.
- Do not claim Adam optimizer soundness, model-selection soundness,
  all-replay-batches soundness, or arbitrary network-size soundness.
- Do not call proof-manifest chunk-chain aggregation recursive aggregation.
  In that mode child proofs are verified outside the guest and represented by
  manifest/public-input hashes. The recursive mode is a separate set of rows and
  a separate claim, and it is the one that verifies child proofs in-guest.
- Do not quote a prove time without the prover that produced it, and do not
  compare prove times across provers. Cycles are the hardware-independent unit;
  ten rows changed prover with cycle counts identical to the digit.
- Do not claim honest public dataset collection for Minari/D4RL imports.
- Do not imply that execute-only `k={16,32,128}` fragment rows are
  proof-backed.

## Checks

The claim scanner in `scripts/experiments/check_paper_claims.py` now checks
both legacy `paper_numbers.json` provenance and current Table 2 proof coverage.
Regression coverage is in `tests/regression/test_paper_claims.py`.
