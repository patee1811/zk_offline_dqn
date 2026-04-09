# Paper Draft README

This folder contains the working LaTeX manuscript for the project:

> **Zero-Knowledge Verifiable Offline DQN Training from Committed Trajectories**

The manuscript is intended to stay synchronized with the current technical state of the repository. At the current stage, the paper should describe the project as a **pre-ZK artifact/verifier prototype**, not as a full zero-knowledge proof-of-training system.

---

## Current Paper Status

The manuscript now aligns with the current repository milestone:

- offline RL baselines have been implemented and evaluated on CartPole,
- committed transition membership is verified through Merkle proofs,
- Double-DQN Bellman target correctness is verified,
- SmoothL1 TD loss correctness is verified,
- minibatch-average loss correctness is verified,
- checkpoint anchoring is verified through SHA-256,
- a stronger pre-ZK prototype for **one offline DQN SGD update step** is also implemented and benchmarked.

This means the paper can now safely claim more than only TD-arithmetic verification. In particular, the manuscript may describe the current stronger milestone as:

> a pre-ZK one-step update prototype that checks committed-minibatch membership, TD arithmetic, gradient recomputation consistency, parameter-delta consistency, SGD update consistency, and pre/post checkpoint anchoring.

The paper should still **not** claim:

- a true zero-knowledge proving backend,
- full proof of offline DQN training,
- multi-step proof composition,
- target-network synchronization proofs across a full training trace,
- replay-sampling correctness across the full run,
- proof recursion or production-grade proof aggregation.

---

## Folder Structure

```text
paper/
├── main.tex                 # Main manuscript entry point
├── refs.bib                 # Bibliography
├── README.md                # This file
└── sections/
    ├── abstract.tex
    ├── introduction.tex
    ├── problem_setup.tex
    ├── experimental_setup.tex
    ├── results.tex
    ├── zk_direction.tex
    ├── conclusion.tex
    └── appendix.tex
```

---

## Manuscript Organization

The current manuscript is organized as follows:

- **Abstract**  
  Summarizes the problem, the current pre-ZK scope, and the stronger one-step update milestone.

- **Introduction**  
  Motivates verifiable offline RL from committed data and positions the work relative to RL+ZKP and proof-of-training lines of work.

- **Problem Setup**  
  Defines the committed offline dataset setting, the DQN-style training setting, and the verification-oriented formulation.

- **Experimental Setup**  
  Describes the RL baselines and the verification experiments, including the committed-dataset pipeline and one-step update evaluation.

- **Results**  
  Reports both RL baseline results and preliminary verification results on committed minibatches.

- **ZK Direction**  
  Explains how the current prototype connects to a future ZK backend and identifies what remains to be proved.

- **Conclusion**  
  Summarizes the current milestone and clarifies the next technical steps.

- **Appendix**  
  Can be used for artifact schemas, exact commands, benchmark details, or extra tables.

---

## What the Paper Should Currently Claim

The paper is now in a good position to claim the following:

1. A concrete formulation for verification-oriented offline DQN training from committed trajectories.
2. A pre-ZK artifact/verifier prototype for:
   - committed transition membership,
   - Double-DQN Bellman target correctness,
   - SmoothL1 TD loss correctness,
   - minibatch-average loss correctness,
   - checkpoint anchoring.
3. A stronger pre-ZK one-step update prototype for:
   - one offline DQN SGD update step from a committed minibatch,
   - gradient recomputation consistency,
   - parameter-delta consistency,
   - SGD update consistency,
   - pre/post checkpoint anchoring,
   - target-network invariance during the one-step statement.
4. Preliminary empirical evidence that the one-step verifier remains stable across multiple minibatch sizes.

These claims are strong enough to make the paper feel substantial, while still remaining accurate.

---

## What the Paper Should Avoid Claiming

To avoid overclaiming, the manuscript should not describe the repository as:

- a full zero-knowledge proof-of-training system,
- a complete proof of offline DQN training,
- a system that already proves the full training trace from initialization to final checkpoint,
- a system that already proves multi-step target-network synchronization or replay-sampling correctness over time.

When in doubt, the safest phrasing is:

> a pre-ZK artifact/verifier prototype for committed-data membership, TD-arithmetic correctness, and one-step update consistency.

---

## Current Experimental Scope Reflected in the Paper

The manuscript currently has two experimental layers:

### 1. RL Baseline Layer

This layer evaluates standard offline RL performance on CartPole using methods such as:

- offline Double DQN,
- CQL-lite,
- behavioral cloning.

Its purpose is to establish a real RL training setting rather than a purely symbolic proof toy.

### 2. Verification Layer

This layer evaluates whether the verification-oriented artifact pipeline is internally consistent on real committed minibatches. It now includes:

- single-sample TD verification,
- minibatch TD verification,
- one-step offline DQN SGD update verification,
- preliminary batch-size benchmarking for the one-step verifier.

The verification experiments are not yet cryptographic ZK benchmarks. They should be described as **preliminary pre-ZK consistency results**.

---

## Recommended Writing Focus for the Current Draft

The manuscript should emphasize the following narrative:

1. **Why offline RL is the right setting for committed data**  
   Because the dataset is fixed in advance and naturally compatible with commitment schemes.

2. **Why DQN is the right first target**  
   Because it contains nontrivial RL-specific update structure while still remaining much simpler than PPO or SAC.

3. **Why TD verification is a meaningful first milestone**  
   Because Bellman target and TD loss are the core RL-specific arithmetic relations that distinguish the setting from generic supervised learning.

4. **Why one-step update verification matters**  
   Because it bridges the gap between verifying only arithmetic summaries and verifying an actual learning update.

5. **Why the current system is still pre-ZK**  
   Because the repository currently verifies the intended statement structure in Python, but does not yet implement a real proof backend.

This storyline is both accurate and persuasive for a research draft.

---

## Recommended Next Writing Updates

The next manuscript updates should prioritize the following:

1. Refine the abstract so it explicitly mentions the stronger one-step update prototype.
2. Ensure the introduction contributions list includes the one-step update milestone.
3. Keep the results section balanced:
   - RL baseline performance,
   - verification consistency results,
   - limitations of the current pre-ZK setting.
4. Add one concise discussion paragraph on why the measured export/verify times are **not** yet proving times.
5. Optionally add an appendix table for artifact fields:
   - TD artifact public fields,
   - one-step artifact public fields,
   - update witness contents.
6. Optionally add exact benchmark commands in the appendix for reproducibility.

---

## Recommended Next Technical Milestone After the Current Draft

Now that the manuscript can already describe a one-step pre-ZK update prototype, the next technical milestone should no longer be “first one verified update step.” That milestone has effectively already been reached in pre-ZK form.

The next real milestone should be one of the following:

### Option A: Multi-Step Verified Update Traces

Extend the current one-step statement to a short chain of steps, for example:

- step 1: pre-checkpoint to checkpoint 1,
- step 2: checkpoint 1 to checkpoint 2,
- ...
- explicit handling of target-network synchronization.

### Option B: More ZK-Friendly Witness Design

Keep the one-step scope, but make the update artifact more circuit-friendly by:

- compressing gradient representations,
- reducing raw floating-point dependence,
- introducing more explicit quantization or fixed-point update rules.

### Option C: True ZK Backend

Implement an actual proof backend for a subset of the current statement, beginning with the smallest viable subrelation.

For the paper, the cleanest phrasing is:

> The current draft already reaches a meaningful one-step pre-ZK verification milestone; the next stage is to move from this artifact/verifier prototype toward multi-step composition and a true zero-knowledge backend.

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

> a research prototype that formalizes and experimentally validates the statement structure for verifiable offline DQN training from committed data, including both TD-arithmetic verification and a stronger one-step SGD update-consistency milestone.

That framing is technically honest, aligned with the repository, and strong enough for a serious draft.