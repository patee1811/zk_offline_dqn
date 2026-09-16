# Why Native Recursion Runs Out of Memory

Root cause of the `failed_oom` rows Table 2 reported **at the time**, traced to
a cycle count. Those rows are proof-verified today; see the postscript at the
end for what changed and what this document got wrong.

## The measurement that settles it

Native recursive aggregation was profiled on Kaggle (30 GB) and on an EC2
`r6i.2xlarge` (61 GB). Every run died. The peak tracked the machine:

| Case | Peak on 30 GB | Peak on 61 GB | Result |
| --- | --- | --- | --- |
| T=8, 1 child | 30,399 MB | 59,369 MB | killed |
| T=16, 2 children | 29,612 MB | 60,139 MB | killed |
| T=32, 4 children | 29,255 MB | 60,816 MB | killed |

Doubling the memory doubled the consumption. The host exited with `-9`,
SIGKILL from the kernel OOM killer, with no diagnostic — the signature of a
process killed rather than one that failed.

More memory is not the answer. The peak is not converging on a fixed ceiling.

## The cause is the guest cycle count

The host reports `cycle_count` before proving starts, and execute mode
succeeds every time. Those numbers isolate the problem:

| Case | Children | Cycle count |
| --- | --- | --- |
| T=16 | 2 | 309,402,836 |
| T=32 | 4 | 615,462,741 |

Two more children add 306 million cycles, so each child costs about
**153 million cycles**, and the fixed part is only 3.3 million.

For scale, the most expensive relation that does prove is the k=8 training
fragment at 4,839,664 cycles. Recursion at T=32 asks for **127 times** that.
The proof-manifest-chain mode at the same T=32 runs in 785,786 cycles and
proves fine.

The prover has to hold execution state proportional to cycle count. At 615
million cycles it exhausts whatever memory the machine has.

## Where the 153 million goes

`verify_recursive_children` in `zk_backend/training_aggregation/sp1/shared/`
calls `verify_native_child_proof` per child, which calls
`sp1_lib::verify::verify_sp1_proof`. The payload is tiny — 32 bytes of proof
and about 1.8 KB of public values per child — so this is not data handling.
It is the in-circuit proof verification itself.

Succinct's published precompile figures put unaccelerated PlonK verification
at 187,227,852 cycles and Groth16 at 173,953,261, against 8,078,761 and
9,390,640 with precompiles. The 153 million measured here sits in the
unaccelerated band.

## What this implies

If child verification ran at precompiled cost, roughly 9 million cycles per
proof, the totals would be:

| Case | Estimated | Against the k=8 fragment |
| --- | --- | --- |
| T=16 | ~21.3 M | 4.4x |
| T=32 | ~39.3 M | 8.1x |

Still large, but in the range where a proof has succeeded before, rather than
127 times beyond it.

## The sha2 patch does not help

SP1 recommends patching `sha2` to a precompile-backed build, and no workspace
under `zk_backend/` declared one. That made it the leading hypothesis: pure
Rust SHA-256 inside the guest would explain an unaccelerated cost.

Measured A/B on one machine, execute mode, real child proofs from
`--run-child-proves`:

| Arm | Cycle count |
| --- | --- |
| With `patch-sha2-0.10.8-sp1-6.0.0` | 309,399,516 |
| Without, baseline | 309,399,516 |

Identical to the cycle. The patch was reverted; it changes nothing on this
path and would only add an unexplained dependency.

The run also reproduces the earlier 61 GB measurement of 309,402,836 cycles to
within 0.001%, which confirms the number is stable across machines.

So the 153M per child is not SHA-256. It is the recursion verifier itself,
and nothing in the program's own dependencies reaches it.

## What was left, at the time

Two directions, neither of them a bigger machine:

1. Ask Succinct whether `verify_sp1_proof` is expected to cost ~153 M cycles
   per child in 6.1.0, and whether a precompiled path exists that a program
   can opt into. The sha2 patch is now ruled out, so the question is specific.
2. Accept the cost and keep `thm:manifest-aggregation` scoped to proof-manifest
   chain aggregation.

Raw profiles: `artifacts/reports/memory_profile/ec2_64gb/`.

## Postscript: a third direction, and it worked

Neither of the two above is what resolved this. A CUDA prover did.

The diagnosis in this document is correct and its conclusion was wrong, in a
way worth recording. Every measurement here says the cost is proportional to
the cycle count and that the host cannot hold the execution state; each is
true. The inference that did not follow is that no machine could, because the
CPU prover's memory scales with the trace while the CUDA prover's does not.
On an A10G, peak device memory sits at 18.4 GB and is **flat in T** across a
twentyfold range of cycle counts - the same rows that consumed 60 GB of host
memory and were killed.

What the artifact reports now:

| Mode | Status |
| --- | --- |
| flat recursive, T = 16, 32, 64 | proof-verified, CUDA |
| binary tree, T = 16 | proof-verified, CUDA |
| binary tree, T = 1248 (two environments) and T = 4992 | proof-verified, CUDA |
| any recursion on the CPU prover | still does not complete within 61 GB |

The per-child figure in this document also moved, for an unrelated reason:
enabling `overflow-checks` on the guest raised recursion by 36.8%, so the
~153 M measured here is ~211 M in the current table. The structural claim - a
fixed cost per child verified, independent of how many training steps that
child covers - survived the change and is what makes long traces affordable.

The lesson is narrower than "we were wrong". A resource measurement bounds the
machine it was taken on. This one was read as though it bounded the problem.
