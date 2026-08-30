# Memory Profiling on Kaggle

How to fill the empty Peak RSS column in Table 2 and turn `failed_oom` into a
number that names a stage.

## Why this exists

Table 2 reports prove time, verify time, proof size, and cycle count. Peak RSS
is blank on almost every row because the Rust hosts never measured memory:
`metrics.json` carries no memory field at all. Three rows fail with
`failed_oom` or `failed_environment`, and without a per-stage peak there is no
way to tell whether the wrap stage, the recursion, or the core proof exhausted
the machine.

`scripts/experiments/profile_sp1_memory.py` wraps a host command and samples
RSS of the process tree, splitting samples at the stage markers the hosts
already print (`cycle_count`, `proving_time_sec`, `verification_time_sec`).
`scripts/experiments/run_memory_profile_campaign.py` drives it across every
relation and writes one `summary.json`.

Wrapping instead of patching the hosts is deliberate: an in-process counter is
lost when the process is killed, which is exactly the run worth measuring.

## Known ceilings

SP1's published requirements, for judging what a result means:

| Resource | SP1 requirement |
| --- | --- |
| GPU VRAM | 24 GB minimum |
| CUDA compute capability | 8.0 or higher |
| GPU proving OS | Linux x86_64 |
| CPU RAM, core/compress | 16 GB and up |
| CPU RAM, Groth16 wrap | about 14 GB |
| CPU RAM, PLONK wrap | about 60 GB |

The PLONK figure is the leading hypothesis for the `failed_environment` row:
that path needs roughly four times what Groth16 does. Nothing in the current
claim set requires PLONK.

For scale, SUMMER (EuroS&P 2026) reports a 324 GB peak on a 1.5 TB server for
a 12M-parameter RNN. Matching that is not the goal; knowing where this artifact
sits relative to it is.

## Running it on Kaggle

The existing Kaggle path applies unchanged. Enable GPU and internet on the
notebook, then:

```bash
git clone https://github.com/patee1811/zk_offline_dqn.git
cd zk_offline_dqn
bash scripts/experiments/setup_sp1_on_kaggle.sh
pip install psutil
```

`setup_sp1_on_kaggle.sh` installs the build prerequisites, rustup, and SP1
6.1.0, then writes `artifacts/reports/kaggle_sp1_setup_summary.json`. Check
`cargo_prove_version` in that file before going further.

Then run the campaign:

```bash
RUN_SP1_PROVE=1 python scripts/experiments/run_memory_profile_campaign.py \
    --out-dir artifacts/reports/memory_profile
```

Cases run cheapest-first, from `short_trace` at 82 seconds up to
`training_fragment_k8` at 441 seconds, with the two recursion cases last.
`summary.json` is rewritten after every case, so a session killed by its time
limit keeps everything that finished.

To profile a single case:

```bash
RUN_SP1_PROVE=1 python scripts/experiments/run_memory_profile_campaign.py \
    --only training_fragment_k8 --out-dir artifacts/reports/memory_profile
```

`--list` prints the cases in run order. `--execute-only` measures execute-mode
memory without proving, which is a cheap way to confirm the harness works
before spending a proving session.

## Reading the output

Each case writes `<label>.json` with a peak and a mean per stage:

```json
{
  "memory": {
    "peak_rss_mb": 2850.793,
    "peak_stage": "prove",
    "stages": {
      "setup":  {"peak_rss_mb": 412.1, "mean_rss_mb": 180.4, "samples": 44},
      "prove":  {"peak_rss_mb": 2850.8, "mean_rss_mb": 1902.7, "samples": 210}
    }
  }
}
```

`peak_stage` is the answer the campaign exists to produce. On a failed run it
names the stage that was resident when the process died.

Note that `setup` includes `cargo build`. A first run on a clean machine
attributes gigabytes of compilation to that stage; build once before profiling,
or read `setup` as build cost rather than proving cost.

## Results, 2026-08-27

Ten cases across two Kaggle sessions under SP1 6.1.0. Every proof-backed row
reported `proof_generated = true` and `proof_verified = true`.

| Case | Peak RSS | Peak stage | Cycles measured | Result |
| --- | --- | --- | --- | --- |
| short_trace | 9853 MB | prove | 115,363 | proved |
| td_mvp | 10,520 MB | setup | — | proved, build in window |
| training_update batch1 | 10,791 MB | prove | 469,460 | proved |
| one_step_sgd_tiny | 11,595 MB | prove | 868,763 | proved |
| training_aggregation (t32) | 12,109 MB | prove | 798,934 | proved |
| forward_td_mlp | 14,790 MB | prove | 1,547,234 | proved |
| training_fragment (k4) | 16,175 MB | prove | 2,597,494 | proved |
| merkle_membership | 9915 MB | setup | — | proved, build in window |
| **recursive_native_t32** | **29,140 MB** | setup | — | **failed** |
| **recursive_binary_tree_t32** | **28,383 MB** | setup | — | **failed** |

Cycle counts match Table 2 exactly where they were measured, and
merkle_membership proved in 118.7 s against Table 2's 121.7 s, a 2.5% spread.

Two rows are labelled for the vector they actually ran, not the one intended.
The fragment and aggregation hosts default to `training_fragment_k4_case_0`
and `training_aggregation_t32_case_0`, and run 2 passed no `--case`, so it
profiled k4 at 2.6 M cycles and t32 at 799 k cycles. The campaign now passes
`--case` explicitly; k8 at 4.8 M and t128 at 2.5 M are still unmeasured.

### Proving fits in 30 GB; recursion does not

Every proof-backed relation peaked between 9.8 and 16.2 GB. The largest
measured, the k4 fragment at 2.6 M cycles, used 16.2 GB — comfortable on a
30 GB machine, and Groth16 wrapping at about 14 GB fits alongside it. The k8
fragment at 4.8 M cycles has not been measured, but the scaling below puts it
well inside the ceiling.

Both recursion cases peaked at 28–29 GB against a 30 GB ceiling, then died.
Neither left an error message: the aggregation host was invoked, printed its
build banner, and the process ended. A child that vanishes without a diagnostic
at 29 GB on a 30 GB box is the signature of the kernel OOM killer, not a logic
fault. The log contains no allocation-failure text, which is consistent —
SIGKILL gives the process no chance to report.

This is the number Table 2's `failed_oom` never carried. The gap is not a
factor of ten; it is a few gigabytes.

### Peak grows with cycles, sublinearly

From 115 k to 2.6 M cycles — a factor of 23 — the peak moved from 9853 MB to
16,175 MB, a factor of 1.6. A large fixed cost dominates and the marginal cost
per cycle is small. On that trend the k8 fragment at 4.8 M cycles lands near
20 GB, still inside a 30 GB ceiling; that remains a projection, not a
measurement.

### Rows to read with care

`td_mvp` and `merkle_membership` both peaked in `setup` because their builds
ran inside the profiled window. Run 2 warmed five hosts but not `td-mvp-host`.
Read those two peaks as compilation cost.

The recursion peaks are also attributed to `setup`, but for a different reason:
those cases run a Python driver that generates the recursive case and proves
child nodes before the aggregate step, so no `proving_time_sec` marker is ever
printed and every sample falls in the first bucket. The peak value is real; the
stage label is not meaningful for driver cases.

Raw output is in `artifacts/reports/memory_profile/`, with `summary.json` for
run 1 and `summary_run2.json` for run 2.

## What this changes

Dropping PLONK was already the first recommendation; these numbers make it
unavoidable. PLONK wrapping needs about 60 GB, and recursion alone reaches 29 GB
before wrapping starts.

The remaining levers, in order:

1. Lower the shard size. SP1 defaults to about 2 M cycles per shard.
2. Widen and flatten the recursion tree. Arity 2 at depth 4 peaked at 28.4 GB;
   SUMMER chose arity 10 at depth 2 explicitly for memory.
3. Rent a machine with 64 GB or more for one T=16 run. Since proving is CPU
   only, that is a RAM instance, not a GPU one, and the shortfall is small
   enough that 64 GB should be ample.

## Harness verification

Exercised end to end on Windows against a real `cargo run --release -p
short-trace-host -- --prove` before the Kaggle run: 273 samples over 88.8
seconds, peak 2850.8 MB. The build then failed because `sp1-jit` does not
compile on Windows, which is why proving runs on Kaggle.

Fault paths tested: psutil missing (reports it and exits cleanly), child
process killed mid-run (still reports `peak_stage`), unknown case label (names
it), missing workspace (skips with a reason).

## If a case still OOMs

In the order worth trying:

1. Drop PLONK, keep Groth16. About 14 GB instead of 60 GB, and no current
   claim needs PLONK.
2. Lower the shard size. SP1 defaults to roughly 2 million cycles per shard;
   smaller shards lower the peak at the cost of more shards. The k=8 fragment
   at 4.8M cycles is the obvious candidate.
3. Widen and flatten the recursion tree. SUMMER uses arity 10 at depth 2 and
   states the choice was made for memory; the failed attempt here was arity 2
   at depth 4. Each level runs a verifier circuit inside a circuit, so fewer
   levels wins over fewer proofs held.
4. Defer commitment openings to the root. SUMMER performs no openings during
   recursion and carries only a counter, a digest, and one aggregated
   evaluation pair between levels.
5. Rent an A100 80 GB or use the Succinct Prover Network for the final run.
   One successful T=16 recursive proof is enough to restate Theorem 7; this
   does not need standing infrastructure.
