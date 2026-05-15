# SP1 Python Alignment

## Scope

This alignment note covers relation-level verification only. It does not claim
to verify full DQN training, replay collection, model selection, long traces,
target-network synchronization over a full run, Adam state, or recursive proof
aggregation.

The Python checks remain the semantic oracle for existing artifacts. The SP1
workspace mirrors those checks for backend validation.

## Python Relation Mapping

- TD MVP: `zk_offline_dqn.relations.td_mvp` checks single-transition Merkle
  membership, fixed-point Bellman target, TD error, and SmoothL1 loss.
- Distinct/minibatch TD: the same TD MVP relation supports `private.items[]`,
  public `batch_size`, ordered `leaf_indices`, distinct-index checks, and
  integer average batch loss.
- Forward-TD MLP: `zk_offline_dqn.relations.forward_td_mlp` checks membership,
  quantized MLP forward traces for online and target networks, action selection,
  target/loss recomputation, and model commitments.
- One-step SGD tiny: `zk_offline_dqn.relations.one_step_sgd_tiny` adds one
  tiny SGD update check over a batch of one, including gradient tensors, delta
  tensors, pre/post commitments, and SmoothL1 gradient.

## SP1 Backend Mapping

- Workspace: `zk_backend/td_mvp/sp1/`
- Host package: `td-mvp-host`
- Guest package: `td-mvp-guest`
- Shared package: `td-mvp-shared`
- Input JSON: `zk_backend/test_vectors/td_mvp_case_0.json` for the canonical
  TD MVP control vector, plus benchmark-generated forward-TD MLP and one-step
  SGD tiny fixtures.
- Host command: `cargo run --release -p td-mvp-host -- --execute`
- Proof command: `cargo run --release -p td-mvp-host -- --prove`
- Public output: the guest commits the shared `PublicOutput` containing
  schema version, dataset root, claimed single or batch outputs, item outputs,
  and model/network commitments where applicable.

## Field Mapping

Top-level fields match between Python JSON and Rust shared structs:

| JSON field | Python relation use | SP1 shared struct |
| --- | --- | --- |
| `schema_version` | dispatches relation version | `TdMvpInput.schema_version` |
| `public.dataset_root` | expected Merkle root | `PublicInputs.dataset_root` |
| `public.fp_scale` | fixed-point scale | `PublicInputs.fp_scale` |
| `public.gamma_fp` | Bellman discount | `PublicInputs.gamma_fp` |
| `public.loss_type` | must be `smooth_l1` | `PublicInputs.loss_type` |
| `public.claimed_target_fp` | single TD public target | `PublicInputs.claimed_target_fp` |
| `public.claimed_loss_fp` | single TD public loss | `PublicInputs.claimed_loss_fp` |
| `public.leaf_index` | single TD membership index | `PublicInputs.leaf_index` |
| `public.batch_size` | minibatch count | `PublicInputs.batch_size` |
| `public.leaf_indices` | ordered public batch indices | `PublicInputs.leaf_indices` |
| `public.claimed_batch_loss_fp` | integer average loss | `PublicInputs.claimed_batch_loss_fp` |
| `public.network_spec_hash` | MLP shape/scale commitment | `PublicInputs.network_spec_hash` |
| `public.online_model_commitment` | online model commitment | `PublicInputs.online_model_commitment` |
| `public.target_model_commitment` | target model commitment | `PublicInputs.target_model_commitment` |
| `public.pre_model_commitment` | pre-update model commitment | `PublicInputs.pre_model_commitment` |
| `public.post_model_commitment` | post-update model commitment | `PublicInputs.post_model_commitment` |
| `private.transition` | single TD transition witness | `PrivateWitness.transition` |
| `private.leaf` | serialized transition leaf | `PrivateWitness.leaf` |
| `private.leaf_hash` | canonical SHA-256 leaf hash | `PrivateWitness.leaf_hash` |
| `private.merkle_path` | Merkle authentication path | `PrivateWitness.merkle_path` |
| `private.td_witness` | q values, target, error, loss | `PrivateWitness.td_witness` |
| `private.items[]` | batch item witnesses | `PrivateWitness.items` |
| `private.online_model` | quantized online/pre model | `PrivateWitness.online_model` |
| `private.target_model` | quantized target model | `PrivateWitness.target_model` |
| `private.post_online_model` | post-update model | `PrivateWitness.post_online_model` |
| `private.update_witness` | SGD gradients/deltas | `PrivateWitness.update_witness` |

Known schema strings are centralized in `zk_offline_dqn/artifacts/schemas.py`:
`td_mvp_test_vector_v1`, `td_mvp_batch_test_vector_v1`,
`forward_td_mlp_v1`, and `one_step_sgd_tiny_v1`.

## Mismatch Risks

- Fixed-point arithmetic: Python and Rust must both use integer truncation for
  fixed-point multiplication and identical rounding for transition encoding.
- JSON serialization: field aliases, optional fields, and commitment payload
  ordering must stay stable.
- Merkle path order: `current_is_left`, level metadata, and sibling order must
  match exactly.
- SmoothL1/loss: threshold, integer division, and gradient conventions must
  remain aligned.
- Public/private boundary: public claims and committed guest outputs must match
  the intended relation statement.
- Schema drift: new required fields or renamed schema strings would break old
  fixtures and backend inputs.
- Model commitment drift: network spec and quantized model JSON ordering must
  remain identical.
- Integer overflow/rounding: Rust `i64` and Python arbitrary precision can
  diverge if future fixtures exceed current safe ranges.

## Execution Checklist

Local Python checks:

```text
python -m compileall zk_offline_dqn scripts src tests
python -m unittest discover tests/regression
python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json
python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke
python scripts/experiments/check_sp1_environment.py
```

Kaggle validation:

```text
python scripts/experiments/run_phase6_kaggle_validation.py
python scripts/experiments/kaggle_sp1_validation.py
bash scripts/experiments/setup_sp1_on_kaggle.sh
```

WSL2/Linux SP1 commands:

```text
cd zk_backend/td_mvp/sp1
cargo test
cargo run --release -p td-mvp-host -- --execute
RUN_SP1_PROVE=1 cargo run --release -p td-mvp-host -- --prove
```

## Known Limitations

A passing Python regression does not by itself prove that SP1 proof generation
works. It only confirms the Python-side semantic oracle and fixture/schema
alignment.

For this project, Kaggle validation is accepted if the user's `zkp-drl`
environment successfully runs Rust/SP1 execute and, when explicitly enabled,
prove. A final paper or release package should still record the exact Kaggle
kernel, OS image, Rust toolchain, SP1 version, command lines, and proof metrics.
