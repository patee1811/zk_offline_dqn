# Claim Matrix

| Component | Current support | Evidence / provenance | Safe wording | Target state |
| --- | --- | --- | --- | --- |
| Relation-level verification over selected offline-DQN artifacts | supported | `zk_offline_dqn/relations/`, `zk_offline_dqn/verifiers/`, tests | "relation-level verification for selected offline-DQN artifacts over committed transition data" | keep as current paper-level framing |
| TD MVP SP1 proof | supported | `zk_backend/td_mvp/sp1/`, `zk_backend/test_vectors/td_mvp_case_0.json`, SP1 provenance under `artifacts/reports/provenance/sp1/` if present | "SP1 proof generation and verification for the TD MVP canonical vector" | keep as backend baseline |
| Forward-TD MLP | Python semantic-oracle checked | `zk_offline_dqn/relations/forward_td_mlp.py`, `zk_offline_dqn/verifiers/forward_td_mlp.py`, tests and report rows if present | "checked by Python semantic oracles" | future SP1-backed relation |
| One-step SGD / tiny SGD | Python semantic-oracle checked | `zk_offline_dqn/relations/one_step_sgd_tiny.py`, `zk_offline_dqn/verifiers/one_step_sgd_tiny.py`, tests and report rows if present | "checked by Python semantic oracles" | future SP1-backed one-step update |
| Backpropagation | not fully supported | no full backend proof | "future work" | prove for a small MLP |
| Multi-step training | not full training proof | no end-to-end backend trace from initialization to final checkpoint | "future work / training-fragment target" | prove `W_t -> W_{t+k}` |
| Self-collected replay/reward audit | supported | `zk_offline_dqn/data_pipeline.py`, `scripts/data/collect_audited_dataset.py`, `scripts/data/audit_replay_dataset.py`, tests | "self-collected replay-audit pipeline before commitment; not a ZK proof of original collection" | use before dataset Merkle commitment |
| Public benchmark import | supported | `scripts/data/import_public_dataset.py`, `scripts/data/audit_replay_dataset.py`, tests | "trusted-source benchmark import with source-integrity commitment only" | commit Minari/D4RL subsets without claiming honest collection |
| Honest data collection | not cryptographically proved; self-collected replay/reward audit supported | public benchmark imports are source-integrity only; commitment begins after collection | "membership relative to a committed replay set; self-collected data can carry replay/reward audit evidence" | stronger manifest + replay audit |
| Recursive aggregation | unsupported | no recursive proof artifacts | "future work" | chunk proof aggregation |
