# Paper Alignment Audit

Phase 9 audits the manuscript and reviewer-facing docs against the implemented
artifact. The goal is claim hardening, not new methodology or new benchmark
numbers.

## Claim Inventory

| Claim | Support level | Provenance | Safe wording |
| --- | --- | --- | --- |
| Relation-level verification over committed offline-DQN artifacts | supported | `zk_offline_dqn/relations/`, `zk_offline_dqn/verifiers/`, tests | "relation-level verification for selected offline-DQN artifacts" |
| Full DQN training proof | unsupported | no full trace backend, docs non-goals | "not a full proof of DQN training" |
| Honest replay data collection | unsupported | threat model excludes pre-commitment honesty | "membership relative to a committed replay set" |
| TD MVP SP1 proof generation and verification | supported | `artifacts/reports/final_ndss/paper_numbers.json`, Kaggle summaries | "SP1 proof generation and verification passed for the TD MVP canonical vector" |
| SP1 proof coverage for all relations | unsupported | Phase 6C validates TD MVP only | "Python semantic oracles cover extension relations; SP1 proof claim is TD MVP only" |
| Python semantic checks for distinct TD, forward-TD MLP, tiny SGD | supported | tests, benchmark smoke summaries, report matrices | "checked by Python semantic oracles" |
| Recursive aggregation or long training trace proof | unsupported | no recursive proof artifacts | "future work" |
| Final report benchmark/tamper row counts | supported | `paper_numbers.json`, `artifacts/benchmarks/final_ndss/summary.json` | "29 benchmark rows and 21 tamper rows with provenance" |

## Supported Numbers

All paper-facing numbers below are sourced from
`artifacts/reports/final_ndss/paper_numbers.json`:

- regression checks: `15/15`
- benchmark rows: `29`
- tamper rows: `21`
- TD MVP proof generated: `true`
- TD MVP proof verified: `true`
- TD MVP proving time: `167.726006` seconds
- TD MVP verification time: `0.190326` seconds
- TD MVP proof size: `2783869` bytes
- TD MVP cycle count: `385048`
- cargo-prove version:
  `cargo-prove sp1 (d454975 2026-04-11T01:54:01.305546215Z)`

Each value has a source path and field-level provenance in `paper_numbers.json`.

## Risky Claims Found

The pre-Phase 9 manuscript used broad wording such as:

- "proves selected relations in an SP1 zkVM backend"
- "SP1 proofs are recorded for CartPole distinct TD..."
- "model-grounded forward-TD MLP proofs"
- "tiny CartPole one-step SGD proof"
- table backend labels that marked distinct TD, forward-TD MLP, and tiny SGD
  as `SP1`
- reproduction language for "full SP1 proof runs"

Those phrases were too broad for the current accepted support level because the
validated SP1 proof claim is TD MVP canonical vector only.

## Replacements Applied

- Broad SP1 proof wording was replaced with TD MVP canonical-vector wording.
- Non-TD relations are described as Python semantic-oracle/report-backed checks.
- The results proof table now reports only the validated TD MVP SP1 proof row.
- Reproduction commands now separate report generation from TD MVP SP1
  validation.
- The existing paper-number check now reads `paper_numbers.json` instead of
  requiring the old seven-row SP1 proof table.

## Table And Figure Provenance

- Results proof table: supported by `paper_numbers.json`.
- Benchmark/tamper counts: supported by `paper_numbers.json` and
  `artifacts/benchmarks/final_ndss/summary.json`.
- Formal statements table: qualitative support, with backend labels hardened to
  distinguish TD MVP SP1 proof validation from Python-oracle extension checks.
- Architecture figure: qualitative support, with caption hardened to the
  validated TD MVP SP1 proof and Python semantic-oracle extension checks.

## Reviewer-Risk Notes

- Do not reintroduce claims that distinct TD, forward-TD MLP, or tiny SGD have
  validated SP1 proofs unless separate proof summaries are produced and
  recorded with provenance.
- Do not claim full training, honest data collection, recursive aggregation, or
  optimizer-state proof.
- Keep `paper_numbers.json` regenerated after any accepted benchmark/proof
  refresh, and update the paper-number checker before changing tables.
