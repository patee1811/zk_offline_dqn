# Paper Changelog

## Phase E Roadmap Rewrite - 2026-05-14

The manuscript has been updated around the final Phase E artifact package.

- Reframed the paper as a layered relation stack for committed replay
  membership, distinct minibatch TD, model-grounded forward-TD MLP, and tiny
  one-step SGD.
- Added explicit threat model, formal statements, SP1 backend, security
  analysis, limitations, and artifact appendix sections.
- Updated proof metrics from `artifacts/benchmarks/final_ndss/summary.json`:
  TD-1/2/4/8, CartPole forward-TD, MountainCar forward-TD, and CartPole
  one-step SGD tiny.
- Added an automated paper-number consistency check against the final NDSS
  aggregate.
- Clarified that the contribution is relation-level proof evidence, not full
  proof-of-training.

## Week 6 Q1 Rewrite - 2026-05-13

The manuscript was rewritten around the then-current SP1 backend milestone.

- Retitled the paper to **ZK-Verifiable Temporal-Difference Computation for Offline DQN over Committed Trajectories**.
- Repositioned the contribution from broad proof-of-training to a scoped TD/minibatch-TD ZK backend for offline DQN artifacts.
- Added a related-work discussion covering proof-of-learning, proof-of-training, verifiable ML, ZKML inference/training, zkVMs, and verifiable RL.
- Rewrote the problem setup to define the exact public inputs, private witnesses, fixed-point TD arithmetic, and minibatch loss relation.
- Rewrote the system design around the implemented SP1 host/guest/shared architecture.
- Updated results with the locked SP1 proof benchmark:
  - TD-1: 142.324547 s prove, 0.157464 s verify, 2782625-byte proof, 382915 cycles.
  - TD-2: 154.923089 s prove, 0.157712 s verify, 2787687-byte proof, 725309 cycles.
  - TD-4: 188.501940 s prove, 0.155969 s verify, 2795631-byte proof, 1425790 cycles.
  - TD-8: 275.077262 s prove, 0.157424 s verify, 2812327-byte proof, 2834727 cycles.
- Recorded Python/SP1 agreement and the full tamper-rejection matrix.
- Clarified that one-step and short-trace verifiers are Python-only pre-ZK extensions, not current SP1 statements.
- Expanded the bibliography with current ZKML, proof-of-learning, proof-of-training, and SP1 references.

## Historical Sync - 2026-05-02

Earlier manuscript notes described the repository as a Python pre-ZK
artifact/verifier prototype with one-step and short-trace verification. Those
notes are now superseded by the Phase E rewrite. The Python verifiers remain
useful as semantic oracles and regression checks, while the paper's implemented
cryptographic claim is now the SP1 relation stack reported in the final NDSS
aggregate.
