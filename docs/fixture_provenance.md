# Fixture Provenance

Where the committed regression fixtures come from.

The CI workflow (`.github/workflows/regression.yml`) refuses to run unless a set
of dataset, checkpoint, and Merkle fixtures already exist in the working tree.
Those fixtures are committed, not generated during CI. This document records the
scripts that produced them, so a reviewer can trace any fixture back to its
source instead of treating it as an unexplained binary.

The scripts named here are **not** invoked by `run_full_regression.py` and have
no callers inside the repository. They are kept as provenance for the committed
artifacts. Do not delete them because a reference search comes back empty.

## Required by CI

| Fixture | Produced by |
| --- | --- |
| `data/cartpole_dqn_eps010_transitions.pkl` | `scripts/data_gen/` chain, below |
| `models/offline_dqn_with_target_seed42_best.pt` | `scripts/training/train_offline_dqn.py` |
| `artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json` | `scripts/zk_proofs/` chain, below |
| `artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json` | `scripts/artifacts_export/export_minibatch_td_artifact_from_dataset.py` |
| `artifacts/fixtures/one_step_update/one_step_update_artifact.json` | `scripts/artifacts_export/export_one_step_update_artifact.py` |
| `artifacts/fixtures/short_trace/short_trace_update_artifact.json` | `scripts/artifacts_export/export_short_trace_update_artifact.py` |

## Dataset chain

The replay set is collected from a trained behavior policy, not from random
actions, which is why the epsilon appears in the filename.

```text
# 1. Behavior policy: stable-baselines3 DQN, seed 42, 20000 timesteps.
#    Hardcoded; writes models/dqn_cartpole_behavior.zip
python scripts/training/train_cartpole_dqn.py

# 2. Roll out that policy with epsilon = 0.10 to get episodes.
python scripts/data_gen/generate_cartpole_dataset_from_dqn.py \
    --model models/dqn_cartpole_behavior \
    --episodes 200 --seed 123 --epsilon 0.10

# 3. Flatten episodes into the flat transition table the relations expect.
python scripts/data_gen/flatten_episode_dataset.py \
    --infile data/cartpole_dqn_eps010_episodes.pkl \
    --out data/cartpole_dqn_eps010_transitions.pkl
```

`data/` is gitignored, so step 3's output is a local prerequisite for
`run_full_regression.py`. The committed Merkle root below is what binds the
paper's claims to a specific version of this dataset.

## Merkle commitment chain

Both scripts hardcode their input and output paths and take no arguments.

```text
# 4. Serialize each transition to a canonical leaf, then SHA256 it.
python scripts/zk_proofs/build_leaf_hashes.py
#    data/cartpole_dqn_eps010_transitions.pkl
#      -> artifacts/fixtures/membership/cartpole_dqn_eps010_leaf_hashes.json

# 5. Build the tree. Odd levels duplicate the last node, Bitcoin-style.
python scripts/zk_proofs/build_merkle_root.py
#    ..._leaf_hashes.json -> ..._cartpole_dqn_eps010_merkle.json
```

The committed tree has 47450 leaves over 17 levels. Rerunning step 5 on a
different dataset produces a different root and invalidates every membership
fixture and every paper number derived from it.

## Offline DQN checkpoint

```text
# 6. Train the offline agent that the one-step and short-trace relations verify.
python scripts/training/train_offline_dqn.py \
    --data data/cartpole_dqn_eps010_transitions.pkl \
    --seed 42 --steps 5000 --batch-size 64 --gamma 0.99 --lr 1e-4 \
    --target-update 200 --out models/offline_dqn_with_target.pt
```

The script appends `seed{N}_best` and `seed{N}_last` to `--out`, which is how
`models/offline_dqn_with_target_seed42_best.pt` gets its name. Only the `_best`
checkpoint is tracked; `.gitignore` excludes `models/*` apart from that one file.

## Unreferenced by design

These directories hold exploratory and evaluation tooling with no callers. They
are not part of the verification path and are not required to reproduce any
paper number. They are kept because deleting working analysis code to satisfy a
reference count is not cleanup.

- `scripts/analysis/` — dataset and training-log inspection.
- `scripts/evaluation/` — checkpoint evaluation and environment smoke tests.
- `scripts/training/train_bc.py`, `train_cql.py` — baseline agents, not proved.
- `scripts/data_gen/generate_random_dataset_until_transitions.py`,
  `mix_transition_datasets.py` — alternate dataset variants.

`scripts/artifacts_export/` is different: `run_full_regression.py` calls five of
its verifiers directly, so it is a live compatibility surface.
