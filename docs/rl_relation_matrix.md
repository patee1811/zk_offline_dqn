# RL Relation Matrix

Which verification obligations exist in offline RL, and which published
proof-of-training systems address them.

This is the positioning argument for the paper. Supervised proof-of-training
proves that a declared optimizer was applied to committed data. Offline RL adds
obligations that have no supervised counterpart, because the replay buffer
substitutes for the environment and the regression target is produced by the
model itself. A supervised zkPoT can be arbitrarily faster and still not
express these relations.

## The obligations

| # | Obligation | Why offline RL creates it | Attack it blocks |
| --- | --- | --- | --- |
| R1 | Replay membership | The buffer stands in for the environment; a transition outside it was never observed | Prover invents transitions that justify a desired policy |
| R2 | Provenance-bound commitment | The dataset is collected before training, so the root must bind to audit and collection records | Prover swaps in a different replay set after the fact |
| R3 | Bellman target correctness | The label comes from the target network, not from ground truth — the condition is self-referential | Prover fabricates targets that make any update look valid |
| R4 | Terminal-flag semantics | `done` decides whether the bootstrap term applies at all | Flipping one bit rewrites the value of a trajectory suffix |
| R5 | Greedy action selection | `argmax` over online Q-values picks the bootstrap action | Prover selects a different action to steer the target |
| R6 | Deterministic minibatch sampling | Which transitions were drawn is itself a claim about the training run | Prover cherry-picks favourable transitions per step |
| R7 | Target-network synchronization | A periodic copy that conditions every subsequent step | Skipping a sync changes the trajectory, invisible in the final checkpoint |
| R8 | Checkpoint chaining | Consecutive steps must link, or a fragment proves nothing about the run | Prover proves isolated steps that never composed |

R1, R3, R4, R5, R6 and R7 have no supervised analogue. R2 and R8 do exist in
supervised zkPoT: dataset commitment is standard, and checkpoint chaining is
what recursive composition provides.

## Coverage

| Obligation | Kaizen | SUMMER | zkDL | VeriLoRA | ZKBoost | This work |
| --- | --- | --- | --- | --- | --- | --- |
| R1 Replay membership | — | — | — | — | — | SP1 |
| R2 Provenance commitment | partial | partial | — | partial | — | verifier |
| R3 Bellman target | — | — | — | — | — | SP1 |
| R4 Terminal flags | — | — | — | — | — | SP1 |
| R5 Greedy action | — | — | — | — | — | SP1 |
| R6 Minibatch sampling | — | — | — | — | — | SP1 |
| R7 Target sync | — | — | — | — | — | SP1 |
| R8 Checkpoint chain | recursive | recursive | — | — | — | manifest chain |

`SP1` means a proof was generated and verified for a canonical vector, with
provenance under `artifacts/reports/provenance/sp1/`. `verifier` means a Python
semantic oracle with tamper tests but no SP1 proof. `partial` means the system
commits to a dataset but does not bind collection or audit records to it.

The comparison systems are not deficient. They target supervised training,
where R1 and R3 through R7 do not arise. The point is that their speed and
scale do not transfer: a faster supervised prover still has no circuit for
"this transition is in the committed buffer" or "this target follows from the
target network at this step".

## Where this work is behind

Stating the gap plainly is part of the argument. Numbers are from each paper.

| Axis | Best published | This work |
| --- | --- | --- |
| Model size | 12M parameters (SUMMER, Kaizen) | tiny MLP, canonical vectors |
| Proof size | 165 KB (SUMMER) | 2.78–2.84 MB |
| Verify time | 20 ms (SUMMER) | 0.12–0.21 s |
| Prove time | 70.1 s/iteration at 12M (SUMMER) | 82–441 s per relation |
| Trace length | 100 iterations, extensible to 160k (SUMMER) | k ≤ 8 proved, T ≤ 128 manifest-chained |
| Aggregation | recursive composition | proof-manifest chain, child proofs verified externally |

SUMMER reports a 324 GB peak on a 1.5 TB server. The scale gap reflects
hardware available for this artifact, not a difference in what the relations
require.

## Sources

- Kaizen — Abbaszadeh et al., *Zero-Knowledge Proofs of Training for Deep
  Neural Networks*, ACM CCS 2024. IACR ePrint 2024/162.
- SUMMER — Li and Fan, *Recursive Zero-Knowledge Proofs for Scalable RNN
  Training*, IEEE EuroS&P 2026. IACR ePrint 2025/1688.
- zkDL — *Efficient Zero-Knowledge Proofs of Deep Learning Training*,
  arXiv 2307.16273.
- VeriLoRA — *Fine-Tuning Large Language Models with Verifiable Security via
  Zero-Knowledge Proofs*, arXiv 2508.21393.
- ZKBoost — *Zero-Knowledge Verifiable Training for XGBoost*, IACR ePrint
  2026/202.

Coverage marks were read from each paper's abstract, contributions, and
evaluation. Before submission, re-check them against the full texts: a system
may support an obligation without naming it the way this table does.
