# Backend Choice

## v0.12 Decision Update

As of `v0.12-backend-selection-sp1`, the first concrete backend implementation target is:

```text
SP1
```

RISC Zero remains the main alternative backend for later comparison, but the next implementation milestone should focus on SP1 first.

The detailed decision rationale is documented in:

```text
docs/backend_selection_v0_12.md
```

## 1. Purpose

This document records the backend choice for the first zero-knowledge MVP of the ZK-Offline-DQN project.

The current repository already contains a Python artifact/verifier framework for committed-data offline DQN training. The next research milestone is to move one small relation from Python verification into a real proving backend.

The first backend target is:

> Merkle membership + Bellman target + SmoothL1 TD loss over a committed offline DQN transition.

This document explains why a zkVM backend is preferred for the first MVP and why custom arithmetic circuits should be deferred until the relation is more stable.

## 2. Candidate Backends

The candidate backends are:

```text
RISC Zero
SP1
Noir
Circom
Halo2
```

They can be grouped into two broad categories:

```text
zkVM-style backend:
- RISC Zero
- SP1

Circuit-oriented backend:
- Noir
- Circom
- Halo2
```

## 3. Backend Requirements for This Project

The first backend should support the following needs.

### 3.1 Hashing and Merkle verification

The backend must verify that a private transition belongs to a public dataset root.

Required operations:

```text
serialize transition
hash leaf
iterate over Merkle path
compare computed root with public dataset_root
```

### 3.2 Fixed-point integer arithmetic

The backend must avoid floating-point arithmetic.

Required operations:

```text
signed integer addition
signed integer subtraction
signed integer multiplication
integer division or explicit rescaling
absolute value
comparison
conditional branch for SmoothL1
```

### 3.3 Branching logic

The backend must support relation branches such as:

```text
if done:
    target_fp = reward_fp
else:
    target_fp = reward_fp + gamma_fp * q_target_max_fp
```

and:

```text
if abs(td_error_fp) < fp_scale:
    loss_fp = quadratic_region
else:
    loss_fp = linear_region
```

### 3.4 Test-vector compatibility

The backend should be easy to connect to existing Python artifacts.

The project already has:

```text
Merkle artifacts
TD artifacts
one-step update artifacts
short-trace artifacts
negative tests
regression runner
```

The first backend should consume small JSON test vectors generated from the existing Python pipeline.

### 3.5 Fast iteration

The first research goal is not maximum constraint efficiency.

The first goal is:

```text
prove the right relation
record proof cost
reject tampered witnesses
document limitations
```

Therefore, developer speed matters more than proof-size optimality at this stage.

## 4. Option A: RISC Zero

RISC Zero is a zkVM. It allows a guest program to run inside a verifiable virtual machine and produces a cryptographic receipt that can be verified by others.

### Advantages

```text
natural fit for Rust code
good fit for branching and parsing logic
good fit for Merkle verification
easier migration from Python verifier logic
clear host/guest structure
suitable for first research prototype
```

### Disadvantages

```text
proof generation may be heavier than hand-optimized circuits
not ideal for highly optimized arithmetic-only constraints
requires Rust/zkVM project setup
performance may become an issue for larger traces
```

### Fit for this project

RISC Zero is a strong candidate for the first MVP because the MVP relation contains hashing, Merkle paths, conditional logic, and fixed-point arithmetic.

## 5. Option B: SP1

SP1 is also a zkVM for proving execution of programs compiled to RISC-V.

### Advantages

```text
good fit for Rust programs
natural fit for general computation
good fit for backend MVP experimentation
can prove execution of relation-checking code
active zkVM ecosystem
```

### Disadvantages

```text
requires SP1-specific setup
proof performance must be benchmarked on this project
may still be heavier than a custom circuit
```

### Fit for this project

SP1 is also a strong candidate for the first MVP. It is especially attractive if the project wants a Rust-based zkVM workflow and simple proof/verify commands.

## 6. Option C: Noir

Noir is a domain-specific language for writing zero-knowledge programs.

### Advantages

```text
higher-level than Circom/Halo2
more circuit-like than zkVMs
good for small arithmetic relations
good candidate for a later optimized TD circuit
```

### Disadvantages

```text
requires rewriting the relation in Noir
less direct reuse of Python/Rust verifier logic
hashing and serialization details must be carefully matched
branching and signed fixed-point arithmetic need careful design
```

### Fit for this project

Noir is a good second-stage backend after the TD relation stabilizes. It may be useful for a compact TD arithmetic circuit.

## 7. Option D: Circom

Circom is a circuit description language for building zero-knowledge circuits.

### Advantages

```text
mature ecosystem for arithmetic circuits
good for explicit low-level constraints
good for optimized small statements
```

### Disadvantages

```text
requires manual circuit design
more engineering effort for branching and signed arithmetic
hash function choice affects circuit cost
less convenient for rapid prototype iteration
```

### Fit for this project

Circom is not the best first backend for this project. It may become useful later if the project needs a small hand-optimized TD circuit.

## 8. Option E: Halo2

Halo2 is a lower-level proving framework suitable for custom circuit design.

### Advantages

```text
powerful for custom optimized circuits
flexible for advanced proof design
suitable for long-term research if performance matters
```

### Disadvantages

```text
high implementation complexity
slower iteration speed
requires deeper proving-system expertise
not ideal for first MVP
```

### Fit for this project

Halo2 should be treated as a future research direction, not the first backend target.

## 9. Recommendation

The first backend should be:

```text
Selected first backend: SP1
Main alternative backend: RISC Zero
Secondary future option: Noir
Later optimization path: Circom or Halo2
```

The reason is:

```text
The first MVP is not only arithmetic. It includes hashing, Merkle verification, conditional TD logic, fixed-point conventions, and compatibility with existing artifacts. A zkVM backend is the fastest path to a real proof while preserving the current verifier structure.
```

## 10. Initial Backend Plan

The first backend milestone should not prove full DQN training.

It should prove only:

```text
Merkle membership
Bellman target
TD error
SmoothL1 TD loss
claimed target/loss consistency
```

The first backend project should be organized as:

```text
zk_backend/
  td_mvp/
    README.md
    test_vectors/
      td_mvp_case_0.json
    host/
    guest/
```

The first test vector should contain:

```text
public:
  dataset_root
  fp_scale
  gamma_fp
  claimed_target_fp
  claimed_loss_fp
  leaf_index

private:
  transition
  merkle_path
  q_online_action_fp
  q_target_max_fp
  target_fp
  td_error_fp
  loss_fp
```

## 11. Acceptance Criteria

The backend MVP is successful if:

```text
valid witness produces a proof
valid proof verifies successfully
tampered reward is rejected
tampered Merkle path is rejected
tampered q_target_max_fp is rejected
tampered claimed_loss_fp is rejected
proving time is recorded
verification time is recorded
proof size is recorded
limitations are documented
```

## 12. Decision

For the first implementation attempt, use:

```text
SP1
```

This decision is recorded in:

```text
docs/backend_selection_v0_12.md
```

RISC Zero remains the main alternative backend for a later comparison milestone.

The final choice can be made after checking local installation complexity and the smallest working example on the development machine.

This project should not start with Circom or Halo2 because the relation is still evolving and the first milestone prioritizes correctness and research iteration speed over optimal proof size.