# Paper Draft README

This folder contains the working LaTeX manuscript for the project:

> **Zero-Knowledge Verifiable Offline DQN Training from Committed Trajectories**

The manuscript should stay synchronized with the current technical state of the repository. At this stage, the paper should describe the project as a **pre-ZK artifact/verifier prototype**, not as a full zero-knowledge proof-of-training system.

---

## Current Paper Status

The manuscript now aligns with the current repository milestone:

- offline RL baselines have been implemented and evaluated on CartPole,
- committed transition membership is verified through Merkle proofs,
- Double-DQN Bellman target correctness is verified,
- SmoothL1 TD loss correctness is verified,
- minibatch-average loss correctness is verified,
- checkpoint anchoring is verified through SHA-256,
- a stronger pre-ZK one-step offline DQN SGD update verifier is implemented and benchmarked,
- short verified training traces are implemented for 2-step, 4-step, and 8-step traces,
- the locked 8-step benchmark enforces deterministic contiguous sampling with public `batch_size` and `start_offset`,
- a negative sanity check shows rejection when public batch indices no longer match the declared sampling rule,
- the B3 short-trace artifact cleanup removes operational path metadata from persistent `notes`.

The paper can currently claim:

> a pre-ZK artifact/verifier prototype that checks committed-data membership, TD-arithmetic correctness, one-step SGD update consistency, short training-trace consistency, deterministic short-trace sampling-rule enforcement, and a cleaner short-trace artifact contract.

The paper should still **not** claim:

- a true zero-knowledge proving backend,
- full proof of offline DQN training from initialization to final selected checkpoint,
- general replay-sampling correctness across a full run,
- long-horizon target-network synchronization guarantees,
- model-selection or early-stopping verification,
- proof recursion or production-grade proof aggregation.

---

## Folder Structure

```text
paper/
|-- main.tex                 # Main manuscript entry point
|-- refs.bib                 # Bibliography
|-- README.md                # This file
`-- sections/
    |-- abstract.tex
    |-- introduction.tex
    |-- problem_setup.tex
    |-- experimental_setup.tex
    |-- results.tex
    |-- zk_direction.tex
    |-- conclusion.tex
    `-- appendix.tex
```

---

## Manuscript Organization

- **Abstract**: summarizes the pre-ZK scope, one-step update milestone, short-trace verification, and deterministic sampling-rule enforcement.
- **Introduction**: motivates verifiable offline RL from committed data and lists the current contributions.
- **Problem Setup**: defines the committed offline dataset, DQN-style training, and verification-oriented formulation.
- **Experimental Setup**: describes RL baselines plus the TD, one-step, and short-trace verification experiments.
- **Results**: reports RL baseline results, one-step verification, short-trace verification, the locked 8-step snapshot, and the negative sanity check.
- **ZK Direction**: explains how the artifact/verifier prototype maps to future public inputs, private witnesses, and proving backends.
- **Discussion**: separates current evidence from limitations and avoids treating Python verifier timings as proof timings.
- **Conclusion**: summarizes the current milestone and identifies backend-ready next steps.
- **Appendix**: records hyperparameters, dataset summaries, fixed-point constants, artifact schema notes, and reporting conventions.

---

## What the Paper Should Currently Claim

The paper is in a good position to claim:

1. A concrete formulation for verification-oriented offline DQN training from committed trajectories.
2. A pre-ZK artifact/verifier prototype for committed transition membership, Double-DQN target correctness, SmoothL1 TD loss correctness, minibatch-average loss correctness, and checkpoint anchoring.
3. A stronger one-step update verifier for committed minibatches, gradient recomputation, parameter-delta consistency, SGD update consistency, target-network invariance, and pre/post checkpoint anchoring.
4. A short-trace verifier that composes consecutive one-step updates with checkpoint chaining and explicit target-network synchronization semantics.
5. Deterministic contiguous sampling-rule enforcement for the locked short-trace benchmark, with public `sampling_rule_type`, `batch_size`, and `start_offset`.
6. A negative sanity check where tampering public trace batches causes rejection.
7. A cleaned B3 short-trace artifact contract where operational paths are supplied by the runtime/benchmark rather than stored in persistent `notes`.

---

## What the Paper Should Avoid Claiming

To avoid overclaiming, the manuscript should not describe the repository as:

- a full zero-knowledge proof-of-training system,
- a complete proof of offline DQN training,
- a system that verifies every training step from initialization to the final selected checkpoint,
- a system that proves general replay-sampling correctness for random, seeded pseudorandom, or prioritized replay,
- a system that verifies model selection, early stopping, or best-checkpoint selection.

When in doubt, the safest phrasing is:

> a pre-ZK artifact/verifier prototype for committed-data membership, TD arithmetic, one-step update consistency, short-trace consistency, and deterministic short-trace sampling-rule enforcement.

---

## Current Experimental Scope Reflected in the Paper

### 1. RL Baseline Layer

This layer evaluates offline RL performance on CartPole using:

- offline Double DQN,
- CQL-lite,
- behavior cloning.

Its purpose is to establish a real RL training setting rather than a purely symbolic verification toy.

### 2. Verification Layer

This layer evaluates whether the artifact pipeline is internally consistent on real committed minibatches and short traces. It includes:

- single-sample TD verification,
- minibatch TD verification,
- one-step offline DQN SGD update verification,
- one-step batch-size benchmarking for batch sizes 1, 2, 4, 8, and 16,
- short-trace verification for 2-step, 4-step, and 8-step traces,
- the locked 8-step deterministic sampling-rule benchmark,
- a negative sanity check for sampling-rule rejection.

These experiments are not cryptographic ZK benchmarks. Export and verifier timings should be described as **Python pre-ZK artifact/verifier timings**, not proving times.

---

## Recommended Writing Focus

The manuscript should emphasize:

1. Offline RL is a natural first target because the dataset is fixed and commit-friendly.
2. DQN is a useful first RL statement because Bellman targets, TD losses, target networks, and SGD updates are nontrivial but still manageable.
3. TD verification is the first RL-specific arithmetic milestone.
4. One-step update verification bridges arithmetic summaries and actual learning updates.
5. Short-trace verification shows that the prototype now checks a small process-level training computation, not only isolated steps.
6. Deterministic contiguous sampling-rule enforcement is meaningful, but it is still narrower than general replay-sampling correctness.
7. The current system remains pre-ZK until a real proving backend is added.

---

## Recommended Next Writing Updates

The highest-value writing updates are:

1. Keep `results.tex` synchronized with `docs/current_benchmark_snapshot.md`.
2. Keep `appendix.tex` synchronized with `docs/artifact_schema.md`, especially the B3 `notes` cleanup.
3. Add exact short-trace benchmark commands and verifier environment variables in the appendix if reproducibility detail is needed.
4. Add one concise note that benchmark metadata such as `final_checkpoint_path` is not part of the persistent artifact schema.
5. Avoid presenting export/verify timings as cryptographic proving or verification times.

---

## Recommended Next Technical Milestone

Now that the repository already supports one-step verification and short verified traces, the next technical milestone is no longer "first verified update step" or "first multi-step trace." Those have been reached in pre-ZK form.

The next milestone should be one of:

### Option A: Backend-Ready Artifact Design

- finish cleanup of the one-step artifact,
- separate public inputs, private witnesses, and audit-only debug fields,
- reduce raw tensor and floating-point dependence,
- define a stable schema version before building a proving backend.

### Option B: Stronger Sampling Rules

- move beyond contiguous deterministic schedules,
- study seeded deterministic replay-style schedules,
- approach replay-sampling guarantees in a controlled way.

### Option C: Longer Trace Composition

- extend beyond the current short-trace scale,
- clarify target-sync semantics over longer horizons,
- study how witness size and verification time scale with trace length.

### Option D: True ZK Backend

- implement a proof backend for a small subrelation first,
- measure true proving time, verification time, and proof size,
- then expand toward one-step and short-trace statements.

For the paper, the cleanest phrasing is:

> The current draft reaches a meaningful pre-ZK milestone: TD arithmetic, one-step update consistency, short-trace consistency, deterministic sampling-rule enforcement, and B3 short-trace schema cleanup. The next stage is backend-ready witness design and migration toward a true zero-knowledge proving backend.

---

## Build Notes

Compile the manuscript from the `paper/` directory or from the project root using your usual LaTeX workflow.

Typical local compilation flow:

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If `latexmk` is available:

```bash
cd paper
latexmk -pdf main.tex
```

---

## Final Positioning

The paper is currently strongest when positioned as:

> a research prototype that formalizes and experimentally validates the statement structure for verifiable offline DQN training from committed data, progressing from TD arithmetic to one-step SGD update consistency and short process-level training-trace verification under a declared public sampling rule.

That framing is technically honest, aligned with the repository, and strong enough for the current draft.
