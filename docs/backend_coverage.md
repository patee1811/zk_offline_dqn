# Backend Coverage

| Relation / component | Python semantic oracle | SP1 proof-backed | Current safe claim | Notes |
| --- | --- | --- | --- | --- |
| Dataset membership / Merkle membership | yes | yes for canonical leaf-hash membership vector | SP1 proof-backed Merkle membership for canonical leaf hash against provenance-bound dataset root | Does not prove honest collection; Python computes the canonical transition hash before the SP1 leaf-hash membership proof. |
| Provenance-bound dataset commitment | yes | no | artifact-level binding from dataset root to manifest, audit report, raw trajectory, and collection-log hashes when available | Self-collected data can be replay/reward audited before commitment; public benchmark data remains source-integrity-only. |
| TD MVP canonical vector | yes | yes | SP1 proof generation and verification for the TD MVP canonical vector | Baseline fixture: `zk_backend/test_vectors/td_mvp_case_0.json`. |
| Distinct minibatch TD | yes | no current paper-level claim | checked by Python semantic oracles/report matrices | Do not describe as proof-backed without separate backend validation provenance. |
| Forward-TD MLP | yes | no current paper-level claim | checked by Python semantic oracles/report matrices | Do not describe as proof-backed without separate backend validation provenance. |
| One-step SGD tiny | yes | no current paper-level claim | checked by Python semantic oracles/report matrices | Simple SGD update fragment, not Adam or optimizer-state correctness. |
| Short trace / checkpoint chaining | yes | no | Python semantic-oracle checked training fragment | Not an end-to-end trace from initialization to final checkpoint. |
| Backpropagation | partial / relation-local | no | future work | No full backend proof for a small MLP backpropagation path. |
| Adam / optimizer-state proof | no | no | unsupported / future work | Current tiny update scope is simple SGD only. |
| Self-collected replay/reward audit | yes | no | replay/reward audit before Merkle commitment | This is dataset provenance support, not SP1 proof coverage. |
| Public benchmark source integrity | yes | no | source-integrity commitment only | Minari/D4RL imports do not prove original honest collection. |
| Honest data collection | partial replay audit for self-collected data only | no | unsupported as a cryptographic honest-collection proof | The verifier checks membership after replay commitment. |
| Recursive aggregation | no | no | unsupported / future work | No recursive proof artifacts are part of the current claim. |
