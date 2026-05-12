# Paper Changelog

## Week 6 Q1 Rewrite - 2026-05-13

The manuscript has been rewritten around the locked Week 5 SP1 backend milestone.

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

Earlier manuscript notes described the repository as a Python pre-ZK artifact/verifier prototype with one-step and short-trace verification. Those notes are now superseded by the Week 6 Q1 rewrite. The Python verifiers remain useful as semantic oracles and future backend targets, but the paper's main implemented cryptographic claim is now the SP1 TD/minibatch-TD backend.
