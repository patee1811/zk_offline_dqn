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

## First results, 2026-08-27

Three cases ran on Kaggle under SP1 6.1.0, all with `proof_generated = true`
and `proof_verified = true`. This is the first memory data this artifact has.

| Case | Peak RSS | Peak stage | Prove | Cycles |
| --- | --- | --- | --- | --- |
| short_trace | 9853 MB | prove | 117.1 s | 115,363 |
| training_update batch1 | 10,791 MB | prove | 136.3 s | 469,460 |
| merkle_membership | 9915 MB | setup | 118.7 s | — |

Two checks that the run is comparable to the committed table: cycle counts
match Table 2 exactly (115,363 and 469,460), and merkle_membership proved in
118.7 s against Table 2's 121.7 s, a 2.5% spread.

Three findings.

**Proving needs about 10 GB.** Every case peaked between 9.8 and 10.8 GB. On a
30 GB machine that leaves roughly 19 GB of headroom, so the core proof stage is
not what exhausts memory. Groth16 wrapping at about 14 GB also fits. PLONK at
about 60 GB does not, which makes it the leading explanation for the
`failed_environment` row.

**Peak scales with cycles, weakly.** From 115 k to 469 k cycles — a factor of
four — the peak moved from 9853 MB to 10,791 MB, under 10%. A large fixed cost
dominates. Extrapolating to the k=8 fragment at 4.8 M cycles, ten times more
again, still suggests low tens of GB rather than hundreds. That has to be
measured, not assumed.

**merkle_membership peaked in `setup`, not `prove`.** Its build ran inside the
profiled window: the log shows `Finished release profile in 10m 44s` before the
host started. The warm-up build only covered `short-trace-host`, so the other
two workspaces compiled during profiling. For that row, read 9915 MB as
compilation, and treat the peak stage as unreliable. Build every host before
profiling, or read `setup` as build cost.

Raw output is in `artifacts/reports/memory_profile/`.

## What is still unmeasured

The two rows that motivated the campaign — `recursive_native_groth16` and
`recursive_native_compressed` — have not been profiled yet, nor has
training_fragment_k8 at 4.8 M cycles. Those are the next run.

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
