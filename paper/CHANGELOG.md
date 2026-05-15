# Paper Changelog

## Relation-Stack Rewrite

The manuscript has been updated around the achieved artifact results.

- Reframed the paper as a layered relation stack for committed replay
  membership, distinct minibatch TD, model-grounded forward-TD MLP, and tiny
  one-step SGD.
- Added explicit threat model, formal statements, SP1 backend, security
  analysis, limitations, and artifact appendix sections.
- Updated proof metrics from `artifacts/benchmarks/final_ndss/summary.json`:
  TD-1/2/4/8, CartPole forward-TD, MountainCar forward-TD, and CartPole
  one-step SGD tiny.
- Added an automated paper-number consistency check against the benchmark
  aggregate.
- Clarified that the contribution is relation-level proof evidence, not full
  proof-of-training.

## Phase 9 Claim Hardening

- Scoped the paper's validated SP1 proof claim to the TD MVP backend on
  `zk_backend/test_vectors/td_mvp_case_0.json`.
- Replaced broad SP1 proof wording for distinct TD, forward-TD MLP, and tiny
  SGD with Python-oracle/report-backed wording.
- Updated the results table to use `artifacts/reports/final_ndss/paper_numbers.json`
  provenance for the TD MVP proof metrics.
