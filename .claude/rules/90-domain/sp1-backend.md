---
paths:
  - "zk_backend/**"
  - "zk_offline_dqn/backends/sp1/**"
---

# Vùng SP1

Lý do: import Python không được kích hoạt prove; claim SP1 chỉ đúng với vector + provenance đã khóa.

- Rust workspace từng relation: `guest` / `host` / `shared`. SP1 pin `=6.1.0` (`sp1-build`, `sp1-sdk`, `sp1-zkvm`).
- Python `backends/sp1/` mô tả fixture, argv, metric. **Cấm** `subprocess` / prove khi import. `commands.py` chỉ trả `List[List[str]]`.
- Prove: `RUN_SP1_PROVE=1 cargo run --release -p <host> -- --prove`. Không nằm trong `run_full_regression.py`.
- Vector canonical: `zk_backend/test_vectors/*_case_0.json`. Sửa vector = đổi artifact đã khóa — hỏi người.
- Không commit `proof.bin`. Provenance compact nằm dưới `artifacts/reports/provenance/sp1/`.
- Coverage hiện có (README): TD MVP, Merkle membership, Forward-TD MLP, one-step SGD tiny, short trace, training_update (bs=1), fragment k∈{1,4,8}, aggregation proof-manifest T∈{32,64,128}. k∈{16,32,128} chỉ execute/reference, không proof-backed.
- Host precheck phải gọi shared verifier trước prove, trừ `--skip-host-precheck`.
